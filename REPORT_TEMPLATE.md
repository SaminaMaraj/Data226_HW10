# Pinecone Airflow Assignment Report

## GitHub Repository
- Repository Link: `<paste your GitHub repo URL here>`

## Objective
Run a Pinecone workflow as an Airflow job using Docker Compose, Sentence Transformers, and Pinecone.

## 1. Modify `docker-compose.yaml` and install packages
I updated the Airflow Docker setup to build a custom image and added:
- `sentence-transformers==3.1.1`
- `pinecone==5.3.1`

### Screenshot 1
- Dockerfile / requirements.txt / docker-compose.yaml showing package installation and custom build.

## 2. Restart Docker containers
Commands used:
```bash
docker compose down
docker compose up --build
```

### Screenshot 2
- Terminal showing containers restarted successfully.

## 3. Configure Pinecone and Airflow Variables
Created these Airflow Variables:
- `pinecone_api_key`
- `pinecone_index_name`
- `pinecone_cloud`
- `pinecone_region`
- `pinecone_search_query`

### Screenshot 3
- Pinecone console with API key / project setup.

### Screenshot 4
- Airflow Admin > Variables page.

## 4. Download, process, and generate input file
The DAG generates a JSON input file and then processes it into a structured records file for embedding.

### Screenshot 5
- Airflow graph view of DAG.

### Screenshot 6
- Log for `download_and_generate_input_file`.

### Screenshot 7
- Log for `process_input_file`.

## 5. Create Pinecone index
The DAG creates a Pinecone index with dimension 384 and cosine metric.

### Screenshot 8
- Log for `create_pinecone_index`.

### Screenshot 9
- Pinecone index page showing created index.

## 6. Convert input file into embeddings and ingest into Pinecone
The DAG uses `sentence-transformers/all-MiniLM-L6-v2` to generate embeddings and upserts them into Pinecone.

### Screenshot 10
- Log for `embed_and_ingest`.

## 7. Run search against Pinecone
The DAG encodes a query, searches the Pinecone index, and writes results to a JSON file.

### Screenshot 11
- Log for `run_search`.

### Screenshot 12
- Search results in task log or Pinecone query output.

## 8. Conclusion
This project successfully automated a full vector-search workflow in Airflow: generating input data, processing it, creating a Pinecone index, ingesting embeddings, and running semantic search.
