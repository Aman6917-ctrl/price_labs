"""Shared retrieval types used across retrievers, rerankers, and AskService."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RetrievedChunk:
    """
    One retrieved passage with metadata + similarity.

    chunk_index is retained for internal ranking only — never returned in
    public citation DTOs.
    """

    content: str
    document_id: str
    title: str
    category: str
    source: str
    version: str
    last_updated: str
    similarity: float
    tags: tuple[str, ...] = field(default_factory=tuple)
    chunk_index: int | None = None

    @property
    def similarity_pct(self) -> float:
        return round(max(0.0, min(1.0, self.similarity)) * 100, 1)


@dataclass
class RetrievalResult:
    """Retriever output including split embedding vs search timings."""

    chunks: list[RetrievedChunk]
    embedding_ms: float = 0.0
    search_ms: float = 0.0
