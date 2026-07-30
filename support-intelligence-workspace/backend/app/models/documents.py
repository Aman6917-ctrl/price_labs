"""
Document domain models for the ingestion / RAG pipeline.

LoadedDocument  — one source file after loading (pre-chunk)
DocumentChunk   — one embeddable unit with full retrieval metadata
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """
    Metadata attached to every ChromaDB chunk.

    Designed so analytics, health scoring, filtering, and citations
    can run without re-reading source files.
    """

    document_id: str
    title: str
    category: str
    source: str
    last_updated: str
    version: str
    tags: list[str] = Field(default_factory=list)
    chunk_index: int | None = None
    total_chunks: int | None = None

    def for_vectorstore(self) -> dict[str, str | int]:
        """
        Chroma metadata values must be str | int | float | bool.
        Lists are serialized as comma-separated strings.
        """
        return {
            "document_id": self.document_id,
            "title": self.title,
            "category": self.category,
            "source": self.source,
            "last_updated": self.last_updated,
            "version": self.version,
            "tags": ",".join(self.tags),
            "chunk_index": self.chunk_index if self.chunk_index is not None else -1,
            "total_chunks": self.total_chunks if self.total_chunks is not None else -1,
        }


class LoadedDocument(BaseModel):
    """Raw document content + metadata before chunking."""

    content: str
    metadata: DocumentMetadata


class DocumentChunk(BaseModel):
    """Single chunk ready for embedding + vector storage."""

    content: str
    metadata: DocumentMetadata


class IngestionResult(BaseModel):
    """Summary returned by CLI and POST /api/ingest."""

    documents_loaded: int
    chunks_created: int
    collection: str
    dry_run: bool = False
    document_ids: list[str] = Field(default_factory=list)
    message: str = ""
