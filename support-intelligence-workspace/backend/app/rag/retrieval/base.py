"""
Retriever abstraction.

AskService depends on this protocol — not Chroma — so hybrid/BM25/query
expansion can replace the implementation without touching AskService.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.rag.retrieval.types import RetrievalResult


@runtime_checkable
class BaseRetriever(Protocol):
    def retrieve(self, query: str, *, top_k: int = 5) -> RetrievalResult:
        """Return chunks + timing, ordered by descending similarity (0–1)."""
