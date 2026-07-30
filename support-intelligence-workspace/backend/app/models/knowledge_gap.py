"""Persistence model: knowledge gap reports from support engineers."""

from __future__ import annotations

from pydantic import Field

from app.models.base import MongoBaseModel
from app.models.enums import DocumentCategory, KnowledgeGapReason


class KnowledgeGapDocument(MongoBaseModel):
    """
    Engineer-flagged documentation issue.

    Links optionally to a question and/or a specific document.
    `category` supports dashboard grouping (Top Missing Topics, gaps by category).
    """

    reason: KnowledgeGapReason
    category: DocumentCategory | str
    description: str | None = None
    question_id: str | None = None
    document_id: str | None = None
    retrieved_document_ids: list[str] = Field(default_factory=list)
    session_id: str | None = None
    # Free-form topic label when docs are missing entirely
    topic: str | None = None
