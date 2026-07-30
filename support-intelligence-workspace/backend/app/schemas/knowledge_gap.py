"""API schemas for knowledge gaps."""

from __future__ import annotations

from pydantic import Field

from app.models.enums import DocumentCategory, KnowledgeGapReason
from app.schemas.common import APIModel, TimestampSchema


class KnowledgeGapCreate(APIModel):
    reason: KnowledgeGapReason
    category: DocumentCategory | str = DocumentCategory.UNCATEGORIZED
    description: str | None = Field(
        default=None,
        description="Additional notes from the support engineer.",
    )
    question_id: str | None = Field(
        default=None,
        description="Reference to the Ask question that surfaced the gap.",
    )
    document_id: str | None = Field(
        default=None,
        description="Primary document (optional if retrieved_document_ids set).",
    )
    retrieved_document_ids: list[str] = Field(
        default_factory=list,
        description="Documents retrieved when the engineer flagged the gap.",
    )
    session_id: str | None = None
    topic: str | None = None
    workspace_id: str | None = None


class KnowledgeGapResponse(TimestampSchema):
    reason: KnowledgeGapReason
    category: DocumentCategory | str
    description: str | None = None
    question_id: str | None = None
    document_id: str | None = None
    retrieved_document_ids: list[str] = Field(default_factory=list)
    session_id: str | None = None
    topic: str | None = None
