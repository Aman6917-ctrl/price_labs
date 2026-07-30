"""
Reranker abstraction.

MVP: heuristic diversity + freshness boost.
Future: cross-encoder, Cohere rerank, etc. — swap via DI only.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.rag.retrieval.types import RetrievedChunk


@runtime_checkable
class BaseReranker(Protocol):
    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        *,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """Re-order / trim chunks. Must not invent content."""
