"""Persistence models and RAG document shapes."""

from app.models.analytics import AnalyticsDocument
from app.models.base import MongoBaseModel, utc_now
from app.models.document_record import DocumentRecord
from app.models.documents import DocumentChunk, DocumentMetadata, IngestionResult, LoadedDocument
from app.models.enums import (
    AnswerQuality,
    ConfidenceLevel,
    DocumentCategory,
    DocumentHealth,
    FeedbackType,
    KnowledgeGapReason,
    RecommendedAction,
)
from app.models.feedback import FeedbackDocument
from app.models.knowledge_gap import KnowledgeGapDocument
from app.models.question import QuestionDocument, SourceCitation

__all__ = [
    "AnalyticsDocument",
    "AnswerQuality",
    "ConfidenceLevel",
    "DocumentCategory",
    "DocumentChunk",
    "DocumentHealth",
    "DocumentMetadata",
    "DocumentRecord",
    "FeedbackDocument",
    "FeedbackType",
    "IngestionResult",
    "KnowledgeGapDocument",
    "KnowledgeGapReason",
    "LoadedDocument",
    "MongoBaseModel",
    "QuestionDocument",
    "RecommendedAction",
    "SourceCitation",
    "utc_now",
]
