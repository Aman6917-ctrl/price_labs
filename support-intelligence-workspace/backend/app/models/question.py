"""Persistence model: support questions answered via the Ask flow."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.models.base import MongoBaseModel
from app.models.enums import ConfidenceLevel


class SourceCitation(BaseModel):
    """Embedded citation snapshot stored on a question document."""

    document_id: str
    title: str
    category: str | None = None
    chunk_index: int | None = None
    excerpt: str | None = None
    score: float | None = None


class QuestionDocument(MongoBaseModel):
    """
    One Ask-session turn persisted for analytics and knowledge-gap linkage.

    Module 4 (RAG) writes this after generation; Module 3 only defines shape + CRUD.
    """

    session_id: str
    question_text: str
    suggested_response: str | None = None
    edited_response: str | None = None
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel | None = None
    source_document_ids: list[str] = Field(default_factory=list)
    citations: list[SourceCitation] = Field(default_factory=list)
    # Opaque bag for RAG debug (model name, top_k, etc.) — keeps schema stable
    rag_meta: dict[str, Any] = Field(default_factory=dict)
