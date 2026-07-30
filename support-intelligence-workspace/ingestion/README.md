"""
Top-level ingestion notes.

Runtime implementation lives in `backend/app/rag/`:
  loaders → chunking → embeddings → vectorstore
  orchestrated by IngestionService

CLI:  scripts/ingest_docs.py
HTTP: POST /api/ingest
"""
