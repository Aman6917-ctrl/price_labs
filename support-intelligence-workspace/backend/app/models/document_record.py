"""Persistence model: knowledge-base document registry (Mongo, not Chroma)."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.models.base import MongoBaseModel
from app.models.enums import DocumentCategory, DocumentHealth


class DocumentRecord(MongoBaseModel):
    """
    Mongo-side registry of ingested docs.

    Chroma holds vectors + chunk metadata; this collection holds
    document-level health, retrieval/gap/feedback stats, and averages.
    """

    document_id: str
    title: str
    category: DocumentCategory | str
    source: str
    version: str = "0.0.0"
    tags: list[str] = Field(default_factory=list)
    last_updated: datetime | str | None = None
    health: DocumentHealth = DocumentHealth.HEALTHY
    retrieval_count: int = 0
    knowledge_gap_count: int = 0
    feedback_count: int = 0
    chunk_count: int = 0
    average_confidence: float | None = None
    average_coverage: float | None = None
    average_quality: float | None = None
    confidence_sample_count: int = 0
    coverage_sample_count: int = 0
    quality_sample_count: int = 0
    last_retrieved: datetime | None = None
