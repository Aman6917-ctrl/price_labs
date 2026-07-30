"""
Embedding generation — local sentence-transformers (no API key).

Default model: sentence-transformers/all-MiniLM-L6-v2
Shared by ingestion and ChromaRetriever so query/document spaces match.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings

from app.config import Settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=2)
def _build_hf_embeddings(model_name: str) -> HuggingFaceEmbeddings:
    logger.info("Loading local embedding model: %s", model_name)
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


class EmbeddingGenerator:
    def __init__(self, settings: Settings) -> None:
        self._embeddings = _build_hf_embeddings(settings.embedding_model)

    @property
    def client(self) -> Embeddings:
        return self._embeddings

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embeddings.embed_query(text)


def get_embeddings(settings: Settings) -> Embeddings:
    """Factory used by ingest + retriever."""
    return EmbeddingGenerator(settings).client
