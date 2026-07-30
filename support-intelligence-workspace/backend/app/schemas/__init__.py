"""API request/response schemas (DTOs). Not used for Mongo persistence."""

from app.schemas.analytics import AnalyticsResponse, AnalyticsUpsert, DashboardSummary
from app.schemas.ask import AskRequest, AskResponse
from app.schemas.common import MessageResponse, PaginationParams
from app.schemas.document import DocumentResponse, DocumentUpsert
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.schemas.knowledge_gap import KnowledgeGapCreate, KnowledgeGapResponse
from app.schemas.question import QuestionCreate, QuestionResponse, QuestionUpdate

__all__ = [
    "AnalyticsResponse",
    "AnalyticsUpsert",
    "AskRequest",
    "AskResponse",
    "DashboardSummary",
    "DocumentResponse",
    "DocumentUpsert",
    "FeedbackCreate",
    "FeedbackResponse",
    "KnowledgeGapCreate",
    "KnowledgeGapResponse",
    "MessageResponse",
    "PaginationParams",
    "QuestionCreate",
    "QuestionResponse",
    "QuestionUpdate",
]
