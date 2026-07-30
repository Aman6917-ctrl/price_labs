"""Ask API DTOs — response contract for the support intelligence workspace."""

from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator

from app.models.enums import (
    AnswerQuality,
    ConfidenceLevel,
    DocumentHealth,
    RecommendedAction,
)
from app.schemas.common import APIModel


class AskRequest(APIModel):
    question: str = Field(..., min_length=3, max_length=4000)
    session_id: str | None = Field(
        default=None,
        description="Optional engineer session id for grouping turns.",
    )
    workspace_id: str | None = None
    top_k: int | None = Field(default=None, ge=1, le=10)

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("Question must be at least 3 characters")
        return cleaned


class AskCitation(APIModel):
    title: str
    category: str
    version: str
    last_updated: str
    similarity: float
    document_id: str
    excerpt: str | None = None


class RetrievedDocumentSchema(APIModel):
    document_id: str
    title: str
    category: str
    version: str
    last_updated: str
    similarity: float
    excerpt: str | None = None


class DocumentHealthSchema(APIModel):
    document_id: str
    title: str
    category: str
    health: DocumentHealth
    reason: str
    last_updated: str
    version: str


class ConfidenceBlock(APIModel):
    level: ConfidenceLevel
    score: float = Field(..., ge=0, le=100)


class CoverageBlock(APIModel):
    score: float = Field(..., ge=0, le=100)
    label: str


class QualityBlock(APIModel):
    label: AnswerQuality
    reasons: list[str] = Field(default_factory=list)


class ProcessingTimings(APIModel):
    embedding_ms: float = 0.0
    retrieval_ms: float = 0.0
    rerank_ms: float = 0.0
    llm_ms: float = 0.0
    total_ms: float = 0.0


class TokenUsage(APIModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost_usd: float | None = None


class AskResponse(APIModel):
    """
    Support-engineer response contract.

    Top-level fields match the product contract; timings/tokens/debug live
    under metadata (debug only when APP_ENV=development).
    """

    request_id: str
    answer: str
    confidence: ConfidenceBlock
    coverage: CoverageBlock
    quality: QualityBlock
    citations: list[AskCitation] = Field(default_factory=list)
    why_this_answer: str
    recommended_action: RecommendedAction
    recommended_action_reason: str | None = None
    retrieved_documents: list[RetrievedDocumentSchema] = Field(default_factory=list)
    document_health: list[DocumentHealthSchema] = Field(default_factory=list)
    question_id: str | None = None
    processing: ProcessingTimings
    metadata: dict[str, Any] = Field(default_factory=dict)
