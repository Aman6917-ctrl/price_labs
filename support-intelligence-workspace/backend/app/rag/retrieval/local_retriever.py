"""
Local (no-API-key) retrieval for development.

Uses the same docs + chunker as ingestion, scores with keyword overlap.
Keeps Ask usable when OPENAI_API_KEY is not configured.
"""

from __future__ import annotations

import logging
import re
import time
from functools import lru_cache

from app.config import Settings
from app.models.documents import DocumentChunk
from app.rag.chunking import DocumentChunker
from app.rag.ingestion import IngestionService
from app.rag.retrieval.types import RetrievalResult, RetrievedChunk

logger = logging.getLogger(__name__)

_TOKEN = re.compile(r"[a-z0-9]+", re.IGNORECASE)


class LocalKeywordRetriever:
    """In-memory keyword retriever over ingested markdown docs."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._chunks = _load_chunks(settings)
        logger.warning(
            "Using LocalKeywordRetriever (%d chunks) — set OPENAI_API_KEY "
            "in backend/.env for OpenAI embeddings + Chroma.",
            len(self._chunks),
        )

    def retrieve(self, query: str, *, top_k: int = 5) -> RetrievalResult:
        t0 = time.perf_counter()
        q_tokens = _tokenize(query)
        scored: list[tuple[float, DocumentChunk]] = []
        for chunk in self._chunks:
            score = _overlap_score(q_tokens, _tokenize(chunk.content + " " + chunk.metadata.title))
            if score > 0:
                scored.append((score, chunk))
        embedding_ms = (time.perf_counter() - t0) * 1000

        t1 = time.perf_counter()
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[: max(1, top_k)]
        search_ms = (time.perf_counter() - t1) * 1000

        results: list[RetrievedChunk] = []
        for score, chunk in top:
            meta = chunk.metadata
            results.append(
                RetrievedChunk(
                    content=chunk.content,
                    document_id=meta.document_id,
                    title=meta.title,
                    category=meta.category,
                    source=meta.source,
                    version=meta.version,
                    last_updated=str(meta.last_updated or ""),
                    similarity=min(1.0, score),
                    tags=tuple(meta.tags or ()),
                    chunk_index=meta.chunk_index,
                )
            )
        return RetrievalResult(
            chunks=results,
            embedding_ms=embedding_ms,
            search_ms=search_ms,
        )


def _load_chunks(settings: Settings) -> list[DocumentChunk]:
    try:
        return _cached_chunks(
            settings.docs_path,
            settings.chunk_size,
            settings.chunk_overlap,
        )
    except Exception:
        logger.exception("local_retriever_failed_to_load_docs")
        return []


@lru_cache(maxsize=1)
def _cached_chunks(
    docs_path: str, chunk_size: int, chunk_overlap: int
) -> tuple[DocumentChunk, ...]:
    # Build a throwaway settings-like ingest using current config fields
    from app.config import get_settings

    base = get_settings()
    svc = IngestionService(
        settings=base,
        chunker=DocumentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap),
    )
    documents = svc.load_documents()
    chunks = svc.chunker.chunk_many(documents)
    return tuple(chunks)


def _tokenize(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN.findall(text) if len(t) > 2}


def _overlap_score(query: set[str], doc: set[str]) -> float:
    if not query or not doc:
        return 0.0
    inter = len(query & doc)
    if inter == 0:
        return 0.0
    # Jaccard-ish, boosted toward recall for short support queries
    return inter / (len(query) ** 0.5 * len(doc) ** 0.25 + 1e-9)
