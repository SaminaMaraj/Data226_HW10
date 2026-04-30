# Data226_HW10
# Pinecone Airflow Assignment (DATA 226)

## Overview
This project implements an end-to-end data pipeline using Apache Airflow and Pinecone.

The pipeline:
1. Downloads Medium article data
2. Preprocesses the data
3. Creates a Pinecone index
4. Generates sentence embeddings
5. Ingests embeddings into Pinecone
6. Runs a semantic search query

---

## Technologies Used
- Apache Airflow
- Docker & Docker Compose
- Pinecone (Vector Database)
- Sentence Transformers
- Python

---

## Project Structure

.
├── dags/
│   └── pinecone_airflow_job.py
├── docker-compose.yaml
├── Dockerfile
├── requirements.txt
├── logs/
├── README.md
