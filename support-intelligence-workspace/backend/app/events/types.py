"""Domain events — payloads only; no Mongo / HTTP imports."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class DomainEvent:
    event_id: str = field(default_factory=lambda: f"evt_{uuid4().hex[:16]}")
    occurred_at: datetime = field(default_factory=_utc_now)


@dataclass(frozen=True)
class QuestionCreated(DomainEvent):
    question_id: str = ""
    session_id: str = ""
    confidence_score: float | None = None  # 0–100
    coverage_score: float | None = None
    quality: str | None = None
    recommended_action: str | None = None
    processing_time_ms: float | None = None
    source_document_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class AnswerGenerated(DomainEvent):
    """Fired after Ask produces an answer (even if persist soft-fails)."""

    question_id: str | None = None
    request_id: str = ""
    confidence_score: float | None = None
    coverage_score: float | None = None
    quality: str | None = None
    recommended_action: str | None = None
    processing_time_ms: float | None = None
    source_document_ids: tuple[str, ...] = ()
    skipped_llm: bool = False


@dataclass(frozen=True)
class KnowledgeGapFlagged(DomainEvent):
    gap_id: str = ""
    reason: str = ""
    category: str = ""
    topic: str | None = None
    question_id: str | None = None
    document_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class FeedbackSubmitted(DomainEvent):
    feedback_id: str = ""
    question_id: str = ""
    feedback_type: str = ""
    document_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class DocumentRetrieved(DomainEvent):
    document_ids: tuple[str, ...] = ()
    question_id: str | None = None
    request_id: str | None = None
    similarities: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentIngested(DomainEvent):
    document_id: str = ""
    title: str = ""
    category: str = ""
    version: str = ""
    chunk_count: int = 0
    source: str = ""
    tags: tuple[str, ...] = ()
    last_updated: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
