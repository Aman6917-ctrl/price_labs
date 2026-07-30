"""Persistence model: daily analytics aggregates."""

from __future__ import annotations

from datetime import date

from pydantic import Field

from app.models.base import MongoBaseModel


class AnalyticsDocument(MongoBaseModel):
    """
    One row per calendar day (per workspace when multi-workspace lands).

    Module 5 will upsert counters; Module 3 defines storage + CRUD only.
    """

    date: date
    questions_count: int = 0
    knowledge_gaps_count: int = 0
    average_confidence: float | None = None
    average_response_quality: float | None = None
    # document_id → retrieval count for that day
    most_retrieved: dict[str, int] = Field(default_factory=dict)
    # topic/category → gap count
    gaps_by_category: dict[str, int] = Field(default_factory=dict)
    # health → count
    health_distribution: dict[str, int] = Field(default_factory=dict)
