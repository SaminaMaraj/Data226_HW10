from airflow import DAG
from airflow.decorators import task
from airflow.models import Variable
from datetime import datetime, timedelta

import ast
import os
import time
import requests
import pandas as pd

from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="Medium_to_Pinecone",
    default_args=default_args,
    description="Build a Medium article search engine using Pinecone",
    schedule=timedelta(days=7),
    start_date=datetime(2025, 4, 1),
    catchup=False,
    tags=["medium", "pinecone", "search-engine"],
) as dag:

    @task
    def download_data():
        """Download Medium dataset CSV"""
        data_dir = "/tmp/medium_data"
        os.makedirs(data_dir, exist_ok=True)

        file_path = os.path.join(data_dir, "medium_data.csv")
        url = "https://s3-geospatial.s3.us-west-2.amazonaws.com/medium_data.csv"

        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            line_count = sum(1 for _ in f)

        print(f"Downloaded file path: {file_path}")
        print(f"Downloaded file has {line_count} lines")

        return file_path

    @task
    def preprocess_data(data_path: str):
        """Clean Medium data and create metadata/id columns"""
        df = pd.read_csv(data_path)

        # Keep only useful fields and handle nulls
        df["title"] = df["title"].fillna("").astype(str)
        df["subtitle"] = df["subtitle"].fillna("").astype(str)

        # Create metadata column exactly like class example
        df["metadata"] = df.apply(
            lambda row: {"title": (row["title"] + " " + row["subtitle"]).strip()},
            axis=1,
        )

        # Create string id
        df["id"] = df.reset_index(drop=True).index.astype(str)

        preprocessed_path = "/tmp/medium_data/medium_preprocessed.csv"
        df.to_csv(preprocessed_path, index=False)

        print(f"Preprocessed data saved to {preprocessed_path}")
        print(f"Total rows after preprocessing: {len(df)}")

        return preprocessed_path

    @task
    def create_pinecone_index():
        """Create Pinecone serverless index"""
        api_key = Variable.get("pinecone_api_key")
        pc = Pinecone(api_key=api_key)

        index_name = "semantic-search-fast"

        spec = ServerlessSpec(
            cloud="aws",
            region="us-east-1",
        )

        # Delete old index if it exists
        existing_indexes = [idx["name"] for idx in pc.list_indexes()]
        if index_name in existing_indexes:
            print(f"Index '{index_name}' already exists. Deleting it first...")
            pc.delete_index(index_name)
            time.sleep(5)

        # Create fresh index
        pc.create_index(
            name=index_name,
            dimension=384,   # all-MiniLM-L6-v2 output dimension
            metric="dotproduct",
            spec=spec,
        )

        # Wait until ready
        while not pc.describe_index(index_name).status["ready"]:
            print("Waiting for Pinecone index to be ready...")
            time.sleep(2)

        print(f"Pinecone index '{index_name}' created successfully")
        return index_name

    @task
    def generate_embeddings_and_upsert(data_path: str, index_name: str):
        """Generate embeddings and upsert to Pinecone"""
        api_key = Variable.get("pinecone_api_key")

        df = pd.read_csv(data_path)

        # metadata is stored as a string in CSV, convert back to dict safely
        df["metadata"] = df["metadata"].apply(ast.literal_eval)

        model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)

        batch_size = 100
        total_rows = len(df)
        total_batches = (total_rows + batch_size - 1) // batch_size

        print(f"Total rows to ingest: {total_rows}")
        print(f"Batch size: {batch_size}")
        print(f"Total batches: {total_batches}")

        for i in range(0, total_rows, batch_size):
            batch_num = i // batch_size + 1
            batch_df = df.iloc[i:i + batch_size].copy()

            texts = batch_df["metadata"].apply(lambda x: x["title"]).tolist()
            embeddings = model.encode(texts)

            vectors = []
            for j, (_, row) in enumerate(batch_df.iterrows()):
                vectors.append(
                    {
                        "id": str(row["id"]),
                        "values": embeddings[j].tolist(),
                        "metadata": row["metadata"],
                    }
                )

            index.upsert(vectors=vectors)
            print(f"Upserted batch {batch_num}/{total_batches} with {len(vectors)} records")

        print(f"Successfully upserted {total_rows} records into Pinecone index '{index_name}'")
        return index_name

    @task
    def test_search_query(index_name: str):
        """Run a sample semantic search against Pinecone"""
        api_key = Variable.get("pinecone_api_key")

        model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)

        query = "what is ethics in AI"
        query_embedding = model.encode(query).tolist()

        results = index.query(
            vector=query_embedding,
            top_k=5,
            include_metadata=True,
        )

        print(f"Search results for query: '{query}'")

        matches = results.get("matches", [])
        for idx, result in enumerate(matches, start=1):
            title = result.get("metadata", {}).get("title", "N/A")
            score = result.get("score", "N/A")
            record_id = result.get("id", "N/A")
            print(f"{idx}. ID: {record_id}, Score: {score}, Title: {title[:120]}")

        return f"Returned {len(matches)} results"

    downloaded_file = download_data()
    preprocessed_file = preprocess_data(downloaded_file)
    pinecone_index = create_pinecone_index()
    upserted_index = generate_embeddings_and_upsert(preprocessed_file, pinecone_index)
    test_search_query(upserted_index)