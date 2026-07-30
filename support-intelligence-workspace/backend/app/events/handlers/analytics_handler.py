"""
Analytics event handler.

MVP: records a lightweight daily rollup *cache* (not source of truth).
Canonical metrics are computed from questions / gaps / feedback / documents
in AnalyticsService.get_dashboard().
"""

from __future__ import annotations

import logging
from datetime import date

from app.events.types import (
    AnswerGenerated,
    DomainEvent,
    FeedbackSubmitted,
    KnowledgeGapFlagged,
    QuestionCreated,
)
from app.models.analytics import AnalyticsDocument
from app.repositories.analytics import AnalyticsRepository

logger = logging.getLogger(__name__)


class AnalyticsHandler:
    """
    Updates optional daily rollup rows for faster dashboards later.

    GET /api/analytics still recomputes from canonical collections; this
    handler only maintains a secondary cache.
    """

    def __init__(self, analytics_repo: AnalyticsRepository) -> None:
        self._analytics = analytics_repo

    async def __call__(self, event: DomainEvent) -> None:
        if isinstance(event, (QuestionCreated, AnswerGenerated)):
            await self._bump_question_metrics(event)
        elif isinstance(event, KnowledgeGapFlagged):
            await self._bump_gap(event)
        elif isinstance(event, FeedbackSubmitted):
            await self._bump_feedback(event)

    async def _load_today(self) -> AnalyticsDocument:
        today = date.today()
        existing = await self._analytics.get_by_date(today)
        if existing:
            return existing
        return AnalyticsDocument(date=today)

    async def _save(self, doc: AnalyticsDocument) -> None:
        await self._analytics.upsert_by_date(doc)

    async def _bump_question_metrics(
        self, event: QuestionCreated | AnswerGenerated
    ) -> None:
        row = await self._load_today()
        # Prefer AnswerGenerated for counts to avoid double-count with QuestionCreated
        if isinstance(event, AnswerGenerated):
            row.questions_count += 1
            if event.confidence_score is not None:
                row.average_confidence = _avg(
                    row.average_confidence, row.questions_count - 1, event.confidence_score
                )
            if event.coverage_score is not None:
                # reuse knowledge_gaps_count slot? No — store in extended fields via most_retrieved hack
                # Better: use average_response_quality for quality score mapping
                pass
            if event.quality:
                qmap = {
                    "excellent": 100,
                    "good": 75,
                    "needs_review": 45,
                    "poor": 15,
                }
                q = qmap.get(event.quality)
                if q is not None:
                    row.average_response_quality = _avg(
                        row.average_response_quality,
                        max(0, row.questions_count - 1),
                        float(q),
                    )
            for doc_id in event.source_document_ids:
                row.most_retrieved[doc_id] = row.most_retrieved.get(doc_id, 0) + 1
        await self._save(row)

    async def _bump_gap(self, event: KnowledgeGapFlagged) -> None:
        row = await self._load_today()
        row.knowledge_gaps_count += 1
        key = event.category or event.topic or "unknown"
        row.gaps_by_category[key] = row.gaps_by_category.get(key, 0) + 1
        await self._save(row)

    async def _bump_feedback(self, event: FeedbackSubmitted) -> None:
        # Rollup cache does not need feedback detail for MVP; count via canonical store.
        # Touch today's row so updated_at moves (observability that events flowed).
        row = await self._load_today()
        await self._save(row)


def _avg(current: float | None, prior_n: int, value: float) -> float:
    if prior_n <= 0 or current is None:
        return round(value, 2)
    return round(((current * prior_n) + value) / (prior_n + 1), 2)
