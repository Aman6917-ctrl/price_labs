"""API schemas for analytics — dashboard DTOs computed from canonical stores."""

from __future__ import annotations

from datetime import date

from pydantic import Field

from app.schemas.common import APIModel, TimestampSchema


class AnalyticsUpsert(APIModel):
    """Optional daily rollup cache write (not source of truth)."""

    date: date
    questions_count: int = 0
    knowledge_gaps_count: int = 0
    average_confidence: float | None = None
    average_response_quality: float | None = None
    most_retrieved: dict[str, int] = Field(default_factory=dict)
    gaps_by_category: dict[str, int] = Field(default_factory=dict)
    health_distribution: dict[str, int] = Field(default_factory=dict)
    workspace_id: str | None = None


class AnalyticsResponse(TimestampSchema):
    date: date
    questions_count: int
    knowledge_gaps_count: int
    average_confidence: float | None = None
    average_response_quality: float | None = None
    most_retrieved: dict[str, int] = Field(default_factory=dict)
    gaps_by_category: dict[str, int] = Field(default_factory=dict)
    health_distribution: dict[str, int] = Field(default_factory=dict)


class NamedCount(APIModel):
    key: str
    count: int
    label: str | None = None


class AnalyticsDashboard(APIModel):
    """
    Canonical dashboard metrics for GET /api/analytics.

    Computed from questions, knowledge_gaps, feedback, and documents.
    Daily rollup cache is not required to serve this response.
    """

    questions_today: int = 0
    questions_this_week: int = 0
    knowledge_gaps_total: int = 0
    feedback_count: int = 0
    positive_feedback_pct: float | None = None
    negative_feedback_pct: float | None = None
    average_confidence: float | None = None
    average_coverage: float | None = None
    average_quality: float | None = None
    average_processing_time_ms: float | None = None
    most_retrieved_documents: list[NamedCount] = Field(default_factory=list)
    top_missing_topics: list[NamedCount] = Field(default_factory=list)
    knowledge_gaps_by_category: list[NamedCount] = Field(default_factory=list)
    confidence_distribution: dict[str, int] = Field(default_factory=dict)
    coverage_distribution: dict[str, int] = Field(default_factory=dict)
    document_health_distribution: dict[str, int] = Field(default_factory=dict)
    recommended_action_distribution: dict[str, int] = Field(default_factory=dict)
    recent_knowledge_gaps: int = 0
    # Aggregated from persisted Ask rag_meta (when available)
    total_tokens: int | None = None
    estimated_cost_usd: float | None = None
    questions_total: int = 0


# Back-compat alias used by older imports
DashboardSummary = AnalyticsDashboard
