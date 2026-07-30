"""
FastAPI dependency injection.

Routes depend on services; services depend on repositories;
repositories depend on MongoDatabase — never the reverse.
EventBus is app-scoped and injected into services that emit events.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends, Request

from app.config import Settings, get_settings
from app.database.mongodb import MongoDatabase
from app.events.bus import EventBus
from app.repositories.analytics import AnalyticsRepository
from app.repositories.document import DocumentRepository
from app.repositories.feedback import FeedbackRepository
from app.repositories.knowledge_gap import KnowledgeGapRepository
from app.repositories.question import QuestionRepository
from app.services.analytics_service import AnalyticsService
from app.services.ask_service import AskService, build_default_ask_service
from app.services.document_service import DocumentService
from app.services.feedback_service import FeedbackService
from app.services.knowledge_gap_service import KnowledgeGapService
from app.services.question_service import QuestionService


def get_db(request: Request) -> MongoDatabase:
    db = getattr(request.app.state, "db", None)
    if db is None:
        raise RuntimeError("Database is not initialized on app.state")
    return db


def get_db_optional(request: Request) -> MongoDatabase | None:
    return getattr(request.app.state, "db", None)


def get_event_bus(request: Request) -> EventBus:
    bus = getattr(request.app.state, "event_bus", None)
    if bus is None:
        bus = EventBus()
        request.app.state.event_bus = bus
    return bus


async def get_database(request: Request) -> AsyncGenerator[MongoDatabase, None]:
    yield get_db(request)


# --- Repositories ------------------------------------------------------------

def get_question_repository(
    db: MongoDatabase = Depends(get_db),
) -> QuestionRepository:
    return QuestionRepository(db)


def get_knowledge_gap_repository(
    db: MongoDatabase = Depends(get_db),
) -> KnowledgeGapRepository:
    return KnowledgeGapRepository(db)


def get_feedback_repository(
    db: MongoDatabase = Depends(get_db),
) -> FeedbackRepository:
    return FeedbackRepository(db)


def get_document_repository(
    db: MongoDatabase = Depends(get_db),
) -> DocumentRepository:
    return DocumentRepository(db)


def get_analytics_repository(
    db: MongoDatabase = Depends(get_db),
) -> AnalyticsRepository:
    return AnalyticsRepository(db)


# --- Services ----------------------------------------------------------------

def get_question_service(
    repo: QuestionRepository = Depends(get_question_repository),
    settings: Settings = Depends(get_settings),
) -> QuestionService:
    return QuestionService(repo, settings)


def get_knowledge_gap_service(
    repo: KnowledgeGapRepository = Depends(get_knowledge_gap_repository),
    question_repo: QuestionRepository = Depends(get_question_repository),
    bus: EventBus = Depends(get_event_bus),
) -> KnowledgeGapService:
    return KnowledgeGapService(repo, question_repo, event_bus=bus)


def get_feedback_service(
    repo: FeedbackRepository = Depends(get_feedback_repository),
    question_repo: QuestionRepository = Depends(get_question_repository),
    bus: EventBus = Depends(get_event_bus),
) -> FeedbackService:
    return FeedbackService(repo, question_repo, event_bus=bus)


def get_document_service(
    repo: DocumentRepository = Depends(get_document_repository),
    bus: EventBus = Depends(get_event_bus),
) -> DocumentService:
    return DocumentService(repo, event_bus=bus)


def get_analytics_service(
    analytics_repo: AnalyticsRepository = Depends(get_analytics_repository),
    question_repo: QuestionRepository = Depends(get_question_repository),
    gap_repo: KnowledgeGapRepository = Depends(get_knowledge_gap_repository),
    document_repo: DocumentRepository = Depends(get_document_repository),
    feedback_repo: FeedbackRepository = Depends(get_feedback_repository),
) -> AnalyticsService:
    return AnalyticsService(
        analytics_repo, question_repo, gap_repo, document_repo, feedback_repo
    )


async def _gap_counts_for_docs(
    document_ids: list[str],
    gap_repo: KnowledgeGapRepository,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for doc_id in document_ids:
        counts[doc_id] = await gap_repo.count({"document_id": doc_id})
    return counts


def get_ask_service(
    request: Request,
    settings: Settings = Depends(get_settings),
    bus: EventBus = Depends(get_event_bus),
) -> AskService:
    """
    Build AskService with optional Mongo-backed persistence + EventBus.
    """
    cached: AskService | None = getattr(request.app.state, "ask_service", None)
    db = get_db_optional(request)

    question_service = None
    document_service = None
    gap_provider = None

    if db is not None:
        q_repo = QuestionRepository(db)
        d_repo = DocumentRepository(db)
        g_repo = KnowledgeGapRepository(db)
        question_service = QuestionService(q_repo, settings)
        document_service = DocumentService(d_repo, event_bus=bus)

        async def gap_provider(doc_ids: list[str]) -> dict[str, int]:
            return await _gap_counts_for_docs(doc_ids, g_repo)

    if cached is not None:
        cached._questions = question_service
        cached._documents = document_service
        cached._gap_count_provider = gap_provider
        cached._bus = bus
        return cached

    service = build_default_ask_service(
        settings,
        question_service=question_service,
        document_service=document_service,
        gap_count_provider=gap_provider,
        event_bus=bus,
    )
    request.app.state.ask_service = service
    return service
