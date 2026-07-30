"""
Document stats handler — updates Mongo document registry from events.

Keeps retrieval / gap / feedback counters and rolling averages off AskService.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.events.types import (
    AnswerGenerated,
    DocumentIngested,
    DocumentRetrieved,
    DomainEvent,
    FeedbackSubmitted,
    KnowledgeGapFlagged,
)
from app.models.document_record import DocumentRecord
from app.models.enums import AnswerQuality, DocumentHealth
from app.repositories.document import DocumentRepository

logger = logging.getLogger(__name__)

_QUALITY_SCORE = {
    AnswerQuality.EXCELLENT.value: 100.0,
    AnswerQuality.GOOD.value: 75.0,
    AnswerQuality.NEEDS_REVIEW.value: 45.0,
    AnswerQuality.POOR.value: 15.0,
}


class DocumentStatsHandler:
    def __init__(self, document_repo: DocumentRepository) -> None:
        self._docs = document_repo

    async def __call__(self, event: DomainEvent) -> None:
        if isinstance(event, DocumentRetrieved):
            await self.on_document_retrieved(event)
        elif isinstance(event, KnowledgeGapFlagged):
            await self.on_knowledge_gap_flagged(event)
        elif isinstance(event, FeedbackSubmitted):
            await self.on_feedback_submitted(event)
        elif isinstance(event, AnswerGenerated):
            await self.on_answer_generated(event)
        elif isinstance(event, DocumentIngested):
            await self.on_document_ingested(event)

    async def on_document_retrieved(self, event: DocumentRetrieved) -> None:
        now = datetime.now(timezone.utc)
        for doc_id in dict.fromkeys(event.document_ids):
            existing = await self._docs.get_by_document_id(doc_id)
            if existing and existing.id:
                await self._docs.update(
                    existing.id,
                    {
                        "retrieval_count": existing.retrieval_count + 1,
                        "last_retrieved": now,
                    },
                )
            else:
                # Ensure a stub registry row exists for unknown ids
                await self._docs.upsert_by_document_id(
                    DocumentRecord(
                        document_id=doc_id,
                        title=doc_id,
                        category="uncategorized",
                        source="unknown",
                        retrieval_count=1,
                        last_retrieved=now,
                    )
                )

    async def on_knowledge_gap_flagged(self, event: KnowledgeGapFlagged) -> None:
        for doc_id in dict.fromkeys(event.document_ids):
            existing = await self._docs.get_by_document_id(doc_id)
            if not existing or not existing.id:
                continue
            new_count = existing.knowledge_gap_count + 1
            fields: dict = {"knowledge_gap_count": new_count}
            if new_count >= 3:
                fields["health"] = DocumentHealth.OUTDATED
            elif new_count >= 1 and existing.health == DocumentHealth.HEALTHY:
                fields["health"] = DocumentHealth.NEEDS_REVIEW
            await self._docs.update(existing.id, fields)

    async def on_feedback_submitted(self, event: FeedbackSubmitted) -> None:
        for doc_id in dict.fromkeys(event.document_ids):
            existing = await self._docs.get_by_document_id(doc_id)
            if not existing or not existing.id:
                continue
            await self._docs.update(
                existing.id,
                {"feedback_count": existing.feedback_count + 1},
            )

    async def on_answer_generated(self, event: AnswerGenerated) -> None:
        for doc_id in dict.fromkeys(event.source_document_ids):
            existing = await self._docs.get_by_document_id(doc_id)
            if not existing or not existing.id:
                continue
            fields: dict = {}
            if event.confidence_score is not None:
                avg, n = _rolling_avg(
                    existing.average_confidence,
                    existing.confidence_sample_count,
                    event.confidence_score,
                )
                fields["average_confidence"] = avg
                fields["confidence_sample_count"] = n
            if event.coverage_score is not None:
                avg, n = _rolling_avg(
                    existing.average_coverage,
                    existing.coverage_sample_count,
                    event.coverage_score,
                )
                fields["average_coverage"] = avg
                fields["coverage_sample_count"] = n
            if event.quality:
                qscore = _QUALITY_SCORE.get(event.quality)
                if qscore is not None:
                    avg, n = _rolling_avg(
                        existing.average_quality,
                        existing.quality_sample_count,
                        qscore,
                    )
                    fields["average_quality"] = avg
                    fields["quality_sample_count"] = n
            if fields:
                await self._docs.update(existing.id, fields)

    async def on_document_ingested(self, event: DocumentIngested) -> None:
        await self._docs.upsert_by_document_id(
            DocumentRecord(
                document_id=event.document_id,
                title=event.title or event.document_id,
                category=event.category or "uncategorized",
                source=event.source or "",
                version=event.version or "0.0.0",
                tags=list(event.tags),
                last_updated=event.last_updated,
                chunk_count=event.chunk_count,
                health=DocumentHealth.HEALTHY,
            )
        )


def _rolling_avg(
    current_avg: float | None, sample_count: int, new_value: float
) -> tuple[float, int]:
    n = max(0, sample_count)
    if n == 0 or current_avg is None:
        return round(new_value, 2), 1
    updated = ((current_avg * n) + new_value) / (n + 1)
    return round(updated, 2), n + 1
