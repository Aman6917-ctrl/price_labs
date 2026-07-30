"""Retrieval package — swappable dense / hybrid / BM25 backends."""

from app.rag.retrieval.base import BaseRetriever
from app.rag.retrieval.chroma_retriever import ChromaRetriever
from app.rag.retrieval.heuristic_reranker import HeuristicReranker, NoOpReranker
from app.rag.retrieval.reranker_base import BaseReranker
from app.rag.retrieval.types import RetrievalResult, RetrievedChunk

__all__ = [
    "BaseRetriever",
    "BaseReranker",
    "ChromaRetriever",
    "HeuristicReranker",
    "NoOpReranker",
    "RetrievalResult",
    "RetrievedChunk",
]
