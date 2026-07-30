"""Repository layer — MongoDB CRUD adapters."""

from app.repositories.analytics import AnalyticsRepository
from app.repositories.document import DocumentRepository
from app.repositories.feedback import FeedbackRepository
from app.repositories.knowledge_gap import KnowledgeGapRepository
from app.repositories.question import QuestionRepository

__all__ = [
    "AnalyticsRepository",
    "DocumentRepository",
    "FeedbackRepository",
    "KnowledgeGapRepository",
    "QuestionRepository",
]
