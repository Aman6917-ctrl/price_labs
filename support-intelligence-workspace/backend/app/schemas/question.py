"""API schemas for questions — separate from QuestionDocument."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.models.enums import ConfidenceLevel
from app.schemas.common import APIModel, TimestampSchema


class CitationSchema(APIModel):
    document_id: str
    title: str
    category: str | None = None
    chunk_index: int | None = None
    excerpt: str | None = None
    score: float | None = None


class QuestionCreate(APIModel):
    """Inbound create payload (Module 4 will populate after RAG)."""

    session_id: str
    question_text: str
    suggested_response: str | None = None
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel | None = None
    source_document_ids: list[str] = Field(default_factory=list)
    citations: list[CitationSchema] = Field(default_factory=list)
    rag_meta: dict[str, Any] = Field(default_factory=dict)
    workspace_id: str | None = None


class QuestionUpdate(APIModel):
    edited_response: str | None = None
    suggested_response: str | None = None
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel | None = None


class QuestionResponse(TimestampSchema):
    session_id: str
    question_text: str
    suggested_response: str | None = None
    edited_response: str | None = None
    confidence_score: float | None = None
    confidence_level: ConfidenceLevel | None = None
    source_document_ids: list[str] = Field(default_factory=list)
    citations: list[CitationSchema] = Field(default_factory=list)
    rag_meta: dict[str, Any] = Field(default_factory=dict)
