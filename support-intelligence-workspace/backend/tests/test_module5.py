"""Unit tests — KnowledgeGapService, FeedbackService, AnalyticsService, event handlers."""

from __future__ import annotations

import pytest

from app.events.bus import EventBus
from app.events.handlers.analytics_handler import AnalyticsHandler
from app.events.handlers.document_stats import DocumentStatsHandler
from app.events.types import (
    AnswerGenerated,
    DocumentRetrieved,
    FeedbackSubmitted,
    KnowledgeGapFlagged,
)
from app.models.document_record import DocumentRecord
from app.models.enums import (
    DocumentCategory,
    DocumentHealth,
    FeedbackType,
    KnowledgeGapReason,
)
from app.models.question import QuestionDocument
from app.schemas.feedback import FeedbackCreate
from app.schemas.knowledge_gap import KnowledgeGapCreate
from app.services.analytics_service import AnalyticsService
from app.services.feedback_service import FeedbackService
from app.services.knowledge_gap_service import KnowledgeGapService
from tests.fakes import (
    FakeAnalyticsRepo,
    FakeDocumentRepo,
    FakeFeedbackRepo,
    FakeGapRepo,
    FakeQuestionRepo,
)


@pytest.mark.asyncio
async def test_flag_gap_persists_and_emits_event():
    gaps = FakeGapRepo()
    questions = FakeQuestionRepo()
    bus = EventBus()
    seen: list = []

    async def capture(event):
        seen.append(event)

    bus.subscribe(KnowledgeGapFlagged, capture)
    svc = KnowledgeGapService(gaps, questions, event_bus=bus)

    result = await svc.flag_gap(
        KnowledgeGapCreate(
            reason=KnowledgeGapReason.MISSING_DOCUMENTATION,
            category=DocumentCategory.API_GUIDE,
            description="No webhook retry docs",
            topic="webhooks",
            retrieved_document_ids=["webhooks", "api-guide"],
        )
    )
    assert result.id
    assert result.reason == KnowledgeGapReason.MISSING_DOCUMENTATION
    assert len(seen) == 1
    assert seen[0].document_ids == ("webhooks", "api-guide")


@pytest.mark.asyncio
async def test_flag_gap_rejects_unknown_question():
    svc = KnowledgeGapService(FakeGapRepo(), FakeQuestionRepo())
    with pytest.raises(ValueError, match="Question not found"):
        await svc.flag_gap(
            KnowledgeGapCreate(
                reason=KnowledgeGapReason.OUTDATED_DOCUMENTATION,
                category="FAQ",
                question_id="000000000000000000000000",
            )
        )


@pytest.mark.asyncio
async def test_feedback_thumbs_and_event():
    questions = FakeQuestionRepo()
    q = await questions.create(
        QuestionDocument(
            session_id="s1",
            question_text="How do webhooks work?",
            source_document_ids=["webhooks"],
        )
    )
    feedback = FakeFeedbackRepo()
    bus = EventBus()
    seen: list = []

    async def capture(event):
        seen.append(event)

    bus.subscribe(FeedbackSubmitted, capture)
    svc = FeedbackService(feedback, questions, event_bus=bus)

    result = await svc.submit(
        FeedbackCreate(
            question_id=q.id,  # type: ignore[arg-type]
            feedback_type=FeedbackType.THUMBS_UP,
            comment="Helpful",
        )
    )
    assert result.feedback_type == FeedbackType.THUMBS_UP
    assert len(seen) == 1
    assert seen[0].document_ids == ("webhooks",)


@pytest.mark.asyncio
async def test_document_stats_handler_retrieval_and_gaps():
    docs = FakeDocumentRepo()
    await docs.upsert_by_document_id(
        DocumentRecord(
            document_id="webhooks",
            title="Webhooks",
            category="Webhooks",
            source="docs/webhooks.md",
        )
    )
    handler = DocumentStatsHandler(docs)

    await handler(
        DocumentRetrieved(document_ids=("webhooks",), request_id="req_1")
    )
    row = await docs.get_by_document_id("webhooks")
    assert row is not None
    assert row.retrieval_count == 1
    assert row.last_retrieved is not None

    await handler(
        KnowledgeGapFlagged(
            gap_id="g1",
            reason="outdated_documentation",
            category="Webhooks",
            document_ids=("webhooks",),
        )
    )
    row = await docs.get_by_document_id("webhooks")
    assert row is not None
    assert row.knowledge_gap_count == 1
    assert row.health == DocumentHealth.NEEDS_REVIEW


@pytest.mark.asyncio
async def test_analytics_handler_answer_generated():
    analytics = FakeAnalyticsRepo()
    handler = AnalyticsHandler(analytics)
    await handler(
        AnswerGenerated(
            question_id="q1",
            request_id="req_1",
            confidence_score=80,
            coverage_score=70,
            quality="good",
            source_document_ids=("webhooks",),
        )
    )
    from datetime import date

    row = await analytics.get_by_date(date.today())
    assert row is not None
    assert row.questions_count == 1
    assert row.most_retrieved.get("webhooks") == 1


@pytest.mark.asyncio
async def test_analytics_dashboard_from_canonical_stores():
    questions = FakeQuestionRepo()
    gaps = FakeGapRepo()
    docs = FakeDocumentRepo()
    feedback = FakeFeedbackRepo()
    analytics = FakeAnalyticsRepo()

    await questions.create(
        QuestionDocument(
            session_id="s1",
            question_text="Q",
            confidence_score=0.8,
            rag_meta={
                "coverage_score": 70,
                "quality": "good",
                "recommended_action": "send_response",
                "retrieval_ms": 10,
                "llm_ms": 20,
            },
        )
    )
    await gaps.create(
        __import__("app.models.knowledge_gap", fromlist=["KnowledgeGapDocument"]).KnowledgeGapDocument(
            reason=KnowledgeGapReason.MISSING_DOCUMENTATION,
            category=DocumentCategory.WEBHOOKS,
            topic="webhooks retries",
        )
    )
    await docs.upsert_by_document_id(
        DocumentRecord(
            document_id="webhooks",
            title="Webhooks",
            category="Webhooks",
            source="x",
            retrieval_count=5,
            health=DocumentHealth.HEALTHY,
        )
    )

    svc = AnalyticsService(analytics, questions, gaps, docs, feedback)
    dash = await svc.get_dashboard()
    assert dash.questions_today >= 1
    assert dash.knowledge_gaps_total == 1
    assert dash.average_confidence is not None
    assert dash.top_missing_topics
    assert dash.most_retrieved_documents[0].key == "webhooks"
