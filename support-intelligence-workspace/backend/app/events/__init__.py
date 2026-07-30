"""In-process domain events (sync handlers; broker-ready later)."""

from app.events.bus import EventBus
from app.events.types import (
    AnswerGenerated,
    DocumentIngested,
    DocumentRetrieved,
    DomainEvent,
    FeedbackSubmitted,
    KnowledgeGapFlagged,
    QuestionCreated,
)

__all__ = [
    "AnswerGenerated",
    "DocumentIngested",
    "DocumentRetrieved",
    "DomainEvent",
    "EventBus",
    "FeedbackSubmitted",
    "KnowledgeGapFlagged",
    "QuestionCreated",
]
