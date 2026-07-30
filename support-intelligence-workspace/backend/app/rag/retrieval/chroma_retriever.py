"""ChromaDB dense retriever — local MiniLM embeddings (no OpenAI key)."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from langchain_chroma import Chroma

from app.config import Settings
from app.rag.embeddings import get_embeddings
from app.rag.retrieval.types import RetrievalResult, RetrievedChunk

logger = logging.getLogger(__name__)


class ChromaRetriever:
    """Dense vector retrieval over the ingested knowledge base."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._embeddings = get_embeddings(settings)
        persist = _resolve_from_backend(settings.chroma_persist_dir)
        self._store = Chroma(
            collection_name=settings.chroma_collection,
            embedding_function=self._embeddings,
            persist_directory=str(persist),
        )

    def retrieve(self, query: str, *, top_k: int = 5) -> RetrievalResult:
        try:
            t_embed = time.perf_counter()
            embedding = self._embeddings.embed_query(query)
            embedding_ms = (time.perf_counter() - t_embed) * 1000

            t_search = time.perf_counter()
            pairs = self._store.similarity_search_by_vector_with_relevance_scores(
                embedding, k=top_k
            )
            search_ms = (time.perf_counter() - t_search) * 1000
        except Exception:
            logger.exception("vector_retrieval_failed")
            raise

        results: list[RetrievedChunk] = []
        for doc, relevance in pairs:
            meta = doc.metadata or {}
            tags_raw = meta.get("tags") or ""
            tags = tuple(
                t.strip() for t in str(tags_raw).split(",") if t.strip()
            )
            chunk_index = meta.get("chunk_index")
            try:
                chunk_index_int = int(chunk_index) if chunk_index is not None else None
                if chunk_index_int is not None and chunk_index_int < 0:
                    chunk_index_int = None
            except (TypeError, ValueError):
                chunk_index_int = None

            similarity = float(relevance)
            if similarity > 1.0:
                similarity = 1.0 / (1.0 + similarity)
            similarity = max(0.0, min(1.0, similarity))

            results.append(
                RetrievedChunk(
                    content=doc.page_content,
                    document_id=str(meta.get("document_id") or "unknown"),
                    title=str(meta.get("title") or "Untitled"),
                    category=str(meta.get("category") or "uncategorized"),
                    source=str(meta.get("source") or ""),
                    version=str(meta.get("version") or "0.0.0"),
                    last_updated=str(meta.get("last_updated") or ""),
                    similarity=similarity,
                    tags=tags,
                    chunk_index=chunk_index_int,
                )
            )

        results.sort(key=lambda c: c.similarity, reverse=True)
        return RetrievalResult(
            chunks=results,
            embedding_ms=embedding_ms,
            search_ms=search_ms,
        )


def _resolve_from_backend(relative_or_absolute: str) -> Path:
    path = Path(relative_or_absolute)
    if path.is_absolute():
        return path
    backend_root = Path(__file__).resolve().parents[3]
    return (backend_root / path).resolve()
