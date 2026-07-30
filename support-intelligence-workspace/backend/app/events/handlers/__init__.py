"""Register MVP event handlers on an EventBus instance."""

from __future__ import annotations

from app.events.bus import EventBus
from app.events.handlers.analytics_handler import AnalyticsHandler
from app.events.handlers.document_stats import DocumentStatsHandler
from app.events.types import (
    AnswerGenerated,
    DocumentIngested,
    DocumentRetrieved,
    FeedbackSubmitted,
    KnowledgeGapFlagged,
    QuestionCreated,
)
from app.repositories.analytics import AnalyticsRepository
from app.repositories.document import DocumentRepository


def register_handlers(
    bus: EventBus,
    *,
    document_repo: DocumentRepository,
    analytics_repo: AnalyticsRepository,
) -> None:
    """
    Wire handlers once at app startup (or when Mongo becomes available).

    Safe to call multiple times only on a fresh bus — callers should clear first.
    """
    doc_handler = DocumentStatsHandler(document_repo)
    analytics_handler = AnalyticsHandler(analytics_repo)

    for event_type in (
        DocumentRetrieved,
        KnowledgeGapFlagged,
        FeedbackSubmitted,
        AnswerGenerated,
        DocumentIngested,
    ):
        bus.subscribe(event_type, doc_handler)

    for event_type in (
        QuestionCreated,
        AnswerGenerated,
        KnowledgeGapFlagged,
        FeedbackSubmitted,
    ):
        bus.subscribe(event_type, analytics_handler)
