"""
Ask-path observability.

Never log raw customer question text — only aggregate timings and scores.
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator

logger = logging.getLogger("app.ask.observability")


@dataclass
class AskTrace:
    request_id: str = ""
    embedding_ms: float = 0.0
    retrieval_ms: float = 0.0  # vector search only (excludes embedding when split)
    rerank_ms: float = 0.0
    llm_ms: float = 0.0
    persist_ms: float = 0.0
    total_ms: float = 0.0
    retrieved_count: int = 0
    unique_documents: int = 0
    confidence_score: float | None = None
    coverage_score: float | None = None
    confidence_level: str | None = None
    quality: str | None = None
    recommended_action: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost_usd: float | None = None
    error_type: str | None = None
    skipped_llm: bool = False
    metadata: dict[str, str | int | float | bool] = field(default_factory=dict)

    def emit(self) -> None:
        logger.info(
            "ask_complete request_id=%s embedding_ms=%.1f retrieval_ms=%.1f "
            "rerank_ms=%.1f llm_ms=%.1f persist_ms=%.1f total_ms=%.1f "
            "retrieved=%d unique_docs=%d confidence=%s coverage=%s level=%s "
            "quality=%s action=%s tokens=%s cost_usd=%s skipped_llm=%s error=%s",
            self.request_id,
            self.embedding_ms,
            self.retrieval_ms,
            self.rerank_ms,
            self.llm_ms,
            self.persist_ms,
            self.total_ms,
            self.retrieved_count,
            self.unique_documents,
            self.confidence_score,
            self.coverage_score,
            self.confidence_level,
            self.quality,
            self.recommended_action,
            self.total_tokens,
            self.estimated_cost_usd,
            self.skipped_llm,
            self.error_type,
        )


@contextmanager
def timed_section(trace: AskTrace, attr: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        setattr(trace, attr, getattr(trace, attr, 0.0) + elapsed_ms)
