"""API schemas for document registry."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.models.enums import DocumentCategory, DocumentHealth
from app.schemas.common import APIModel, TimestampSchema


class DocumentUpsert(APIModel):
    document_id: str
    title: str
    category: DocumentCategory | str
    source: str
    version: str = "0.0.0"
    tags: list[str] = Field(default_factory=list)
    last_updated: datetime | str | None = None
    health: DocumentHealth = DocumentHealth.HEALTHY
    chunk_count: int = 0
    workspace_id: str | None = None


class DocumentResponse(TimestampSchema):
    document_id: str
    title: str
    category: DocumentCategory | str
    source: str
    version: str
    tags: list[str] = Field(default_factory=list)
    last_updated: datetime | str | None = None
    health: DocumentHealth
    retrieval_count: int = 0
    knowledge_gap_count: int = 0
    feedback_count: int = 0
    chunk_count: int = 0
    average_confidence: float | None = None
    average_coverage: float | None = None
    average_quality: float | None = None
    last_retrieved: datetime | None = None


class DocumentStatsResponse(APIModel):
    """Focused stats DTO for a single document."""

    document_id: str
    title: str
    health: DocumentHealth
    retrieval_count: int
    knowledge_gap_count: int
    feedback_count: int
    average_confidence: float | None = None
    average_coverage: float | None = None
    average_quality: float | None = None
    last_retrieved: datetime | None = None
