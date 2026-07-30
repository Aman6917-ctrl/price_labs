"""
ChromaDB vector store adapter.

Stores chunks with rich metadata for filtering, citations, and analytics.
Uses the same local Embeddings instance as retrieval.
"""

from __future__ import annotations

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.models.documents import DocumentChunk


class VectorStoreService:
    def __init__(
        self,
        persist_directory: Path,
        collection_name: str,
        embeddings: Embeddings,
    ) -> None:
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self._embeddings = embeddings
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self._store = self._open_store()

    def _open_store(self) -> Chroma:
        return Chroma(
            collection_name=self.collection_name,
            embedding_function=self._embeddings,
            persist_directory=str(self.persist_directory),
        )

    @property
    def store(self) -> Chroma:
        return self._store

    def clear(self) -> None:
        """Remove all vectors so re-ingest is idempotent for MVP demos."""
        existing = self._store.get()
        ids = existing.get("ids") or []
        if ids:
            self._store.delete(ids=ids)

    def upsert_chunks(self, chunks: list[DocumentChunk], replace: bool = True) -> int:
        if replace:
            self.clear()

        documents = [
            Document(
                page_content=chunk.content,
                metadata=chunk.metadata.for_vectorstore(),
            )
            for chunk in chunks
        ]
        ids = [
            f"{chunk.metadata.document_id}::{chunk.metadata.chunk_index}"
            for chunk in chunks
        ]
        self._store.add_documents(documents=documents, ids=ids)
        return len(documents)

    def similarity_search(self, query: str, k: int = 5) -> list[Document]:
        return self._store.similarity_search(query, k=k)

    def similarity_search_with_score(
        self, query: str, k: int = 5
    ) -> list[tuple[Document, float]]:
        return self._store.similarity_search_with_score(query, k=k)
