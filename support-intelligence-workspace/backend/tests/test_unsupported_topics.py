"""Tests: unsupported topics must score Low + escalate; supported stay usable."""

from __future__ import annotations

import pytest

from app.config import Settings
from app.models.enums import AnswerQuality, ConfidenceLevel, RecommendedAction
from app.rag.confidence import ConfidenceCalculator
from app.rag.coverage import CoverageCalculator
from app.rag.evidence import (
    EvidenceAssessor,
    answer_indicates_insufficient,
    extract_feature_phrases,
)
from app.rag.quality import AnswerQualityEvaluator, RecommendedActionResolver
from app.rag.retrieval.types import RetrievedChunk


def _chunk(
    *,
    content: str,
    title: str = "Airbnb Integration",
    similarity: float = 0.88,
    document_id: str = "airbnb-integration",
    category: str | None = None,
    tags: tuple[str, ...] = ("airbnb", "pms"),
) -> RetrievedChunk:
    return RetrievedChunk(
        content=content,
        document_id=document_id,
        title=title,
        category=category or title,
        source=f"docs/{document_id}.md",
        version="1.0.0",
        last_updated="2026-01-01",
        similarity=similarity,
        tags=tags,
        chunk_index=0,
    )


AIRBNB_CHUNK = _chunk(
    content=(
        "PriceLabs syncs with Airbnb via the channel manager. "
        "Calendar sync and price push are supported for Airbnb listings."
    )
)

BOOKING_CHUNK = _chunk(
    content=(
        "Booking.com integration pushes rates and availability. "
        "Use the PMS connectors to map Listing IDs. Rate policy applies."
    ),
    title="Booking.com Integration",
    document_id="booking-com-integration",
    similarity=0.86,
    tags=("booking.com", "pms"),
)

DYNAMIC_CHUNK = _chunk(
    content="Dynamic pricing adjusts nightly rates based on occupancy and demand.",
    title="Dynamic Pricing Overview",
    document_id="dynamic-pricing",
    similarity=0.9,
    tags=("pricing", "dynamic"),
)

UNSUPPORTED_QUESTIONS = [
    "Does PriceLabs support WhatsApp integration?",
    "Does PriceLabs integrate with Telegram?",
    "How do I reset my Netflix password?",
    "Does PriceLabs support Expedia integration?",
    "Does PriceLabs integrate with Oracle PMS?",
    "Does PriceLabs support Slack integration?",
    "What is the PriceLabs refund policy?",
    "Who is the CEO of PriceLabs?",
    "Does PriceLabs support GPT-5?",
]

SUPPORTED_QUESTIONS = [
    "Does PriceLabs support Airbnb integration?",
    "How does Booking.com sync work?",
    "Airbnb sync failed.",
    "Why are prices not updating?",
    "Dynamic pricing overview.",
    "Booking.com connectivity suspended.",
]


def _supported_corpus() -> list[RetrievedChunk]:
    return [
        AIRBNB_CHUNK,
        BOOKING_CHUNK,
        DYNAMIC_CHUNK,
        _chunk(
            content=(
                "Why prices are not updating: verify sync and push. "
                "Dynamic pricing overview covers demand signals. "
                "Booking.com connectivity suspended when credentials fail."
            ),
            title="Troubleshooting Guide",
            document_id="troubleshooting",
            similarity=0.8,
            tags=("sync", "prices"),
        ),
    ]


@pytest.mark.parametrize("question", UNSUPPORTED_QUESTIONS)
def test_unsupported_questions_are_detected(question: str):
    assessor = EvidenceAssessor()
    evidence = assessor.assess(question, [AIRBNB_CHUNK, BOOKING_CHUNK])
    assert evidence.unsupported_topic is True
    assert evidence.direct_mention < 1.0


@pytest.mark.parametrize("question", SUPPORTED_QUESTIONS)
def test_supported_questions_not_falsely_unsupported(question: str):
    evidence = EvidenceAssessor().assess(question, _supported_corpus())
    assert evidence.unsupported_topic is False, evidence
    assert evidence.direct_mention == 1.0


@pytest.mark.parametrize(
    "question,chunks",
    [
        ("Does PriceLabs support Airbnb integration?", [AIRBNB_CHUNK]),
        ("Booking.com integration", [BOOKING_CHUNK]),
        ("Dynamic pricing", [DYNAMIC_CHUNK]),
    ],
)
def test_supported_topics_high_confidence(question: str, chunks: list[RetrievedChunk]):
    """Regression: supported product docs → High confidence (not knowledge gap)."""
    settings = Settings()
    evidence = EvidenceAssessor().assess(question, chunks)
    assert evidence.unsupported_topic is False, evidence
    assert evidence.supporting_document_ids, evidence

    confidence = ConfidenceCalculator(settings).calculate(chunks, evidence=evidence)
    coverage = CoverageCalculator().calculate(chunks, evidence=evidence)

    assert confidence.level == ConfidenceLevel.HIGH, confidence
    assert confidence.score >= 75
    assert coverage.score >= 70

    action = RecommendedActionResolver().resolve(
        coverage_score=coverage.score,
        confidence_level=confidence.level,
        quality=AnswerQuality.GOOD,
        unsupported_topic=False,
        insufficient_answer=False,
    )
    assert action.action == RecommendedAction.SEND_RESPONSE


@pytest.mark.parametrize(
    "question",
    [
        "Does PriceLabs support WhatsApp integration?",
        "Does PriceLabs integrate with Telegram?",
        "How do I reset my Netflix password?",
    ],
)
def test_truly_unsupported_stay_low_confidence(question: str):
    settings = Settings()
    chunks = [AIRBNB_CHUNK, BOOKING_CHUNK, DYNAMIC_CHUNK]
    evidence = EvidenceAssessor().assess(question, chunks)
    assert evidence.unsupported_topic is True

    confidence = ConfidenceCalculator(settings).calculate(chunks, evidence=evidence)
    coverage = CoverageCalculator().calculate(chunks, evidence=evidence)
    confidence = ConfidenceCalculator(settings).clamp_unsupported(confidence)
    coverage = CoverageCalculator().clamp_unsupported(coverage)

    assert confidence.level == ConfidenceLevel.LOW
    assert confidence.score <= 30
    assert coverage.score <= 30


def test_airbnb_doc_present_never_unsupported():
    """If an Airbnb Integration document is retrieved, never classify as gap."""
    chunks = [
        _chunk(
            content="Authorize the PriceLabs Airbnb app with the host account.",
            title="Airbnb Integration",
            document_id="airbnb-integration",
            similarity=0.72,
        )
    ]
    evidence = EvidenceAssessor().assess(
        "Does PriceLabs support Airbnb integration?",
        chunks,
    )
    assert evidence.unsupported_topic is False
    assert "airbnb-integration" in evidence.supporting_document_ids
    assert EvidenceAssessor().has_direct_doc_support(
        "Does PriceLabs support Airbnb integration?",
        chunks,
    )


def test_punctuation_does_not_break_topic_match():
    """Trailing punctuation must not create phantom critical terms like 'failed.'."""
    chunks = [
        _chunk(
            content="Airbnb sync failed when the channel token expires.",
            title="Airbnb Integration",
            similarity=0.9,
        )
    ]
    evidence = EvidenceAssessor().assess("Airbnb sync failed.", chunks)
    assert evidence.unsupported_topic is False
    assert "failed." not in evidence.focus_terms
    assert "failed." not in evidence.missing_terms


@pytest.mark.parametrize("question", UNSUPPORTED_QUESTIONS)
def test_unsupported_confidence_and_coverage_capped(question: str):
    settings = Settings()
    assessor = EvidenceAssessor()
    chunks = [AIRBNB_CHUNK, BOOKING_CHUNK]
    evidence = assessor.assess(question, chunks)

    confidence = ConfidenceCalculator(settings).calculate(chunks, evidence=evidence)
    coverage = CoverageCalculator().calculate(chunks, evidence=evidence)
    confidence = ConfidenceCalculator(settings).clamp_unsupported(confidence)
    coverage = CoverageCalculator().clamp_unsupported(coverage)

    assert evidence.unsupported_topic
    assert confidence.score <= 30
    assert confidence.level == ConfidenceLevel.LOW
    assert coverage.score <= 30
    assert "insufficient" in coverage.label.lower()


@pytest.mark.parametrize("question", UNSUPPORTED_QUESTIONS)
def test_unsupported_quality_and_action(question: str):
    settings = Settings()
    chunks = [AIRBNB_CHUNK, BOOKING_CHUNK]
    evidence = EvidenceAssessor().assess(question, chunks)
    confidence = ConfidenceCalculator(settings).calculate(chunks, evidence=evidence)
    coverage = CoverageCalculator().calculate(chunks, evidence=evidence)
    if evidence.unsupported_topic:
        confidence = ConfidenceCalculator(settings).clamp_unsupported(confidence)
        coverage = CoverageCalculator().clamp_unsupported(coverage)

    answer = "I couldn't find enough information in the documentation."
    quality = AnswerQualityEvaluator().evaluate(
        answer=answer,
        citations=[],
        coverage_score=coverage.score,
        confidence_level=confidence.level,
        confidence_score=confidence.score,
        skipped_llm=False,
        unsupported_topic=True,
    )
    action = RecommendedActionResolver().resolve(
        coverage_score=coverage.score,
        confidence_level=confidence.level,
        quality=quality.label,
        unsupported_topic=True,
        insufficient_answer=True,
    )

    assert quality.label == AnswerQuality.POOR
    assert action.action == RecommendedAction.ESCALATE_TO_HUMAN
    assert "knowledge gap" in action.reason.lower()


def test_similarity_alone_cannot_be_high():
    settings = Settings()
    chunks = [
        _chunk(
            content="Dynamic pricing adjusts rates based on market occupancy.",
            title="Dynamic Pricing Overview",
            document_id="dynamic-pricing",
            similarity=0.95,
        )
    ]
    evidence = EvidenceAssessor().assess(
        "Does PriceLabs support WhatsApp?",
        chunks,
    )
    confidence = ConfidenceCalculator(settings).calculate(chunks, evidence=evidence)
    confidence = ConfidenceCalculator(settings).clamp_unsupported(confidence)
    assert confidence.level != ConfidenceLevel.HIGH
    assert confidence.score <= 30


def test_refund_policy_not_fooled_by_generic_policy_word():
    """Booking.com 'rate policy' must not satisfy 'refund policy'."""
    evidence = EvidenceAssessor().assess(
        "What is the PriceLabs refund policy?",
        [BOOKING_CHUNK],
    )
    assert evidence.unsupported_topic is True
    assert "refund" in " ".join(evidence.missing_terms)


def test_feature_phrase_extraction():
    assert "whatsapp" in extract_feature_phrases(
        "Does PriceLabs support WhatsApp integration?"
    )
    assert "telegram" in extract_feature_phrases(
        "Does PriceLabs integrate with Telegram?"
    )
    assert "netflix" in extract_feature_phrases(
        "How do I reset my Netflix password?"
    )
    assert "refund" in extract_feature_phrases(
        "What is the PriceLabs refund policy?"
    )
    assert "ceo" in extract_feature_phrases("Who is the CEO of PriceLabs?")
    assert "airbnb" in extract_feature_phrases(
        "Does PriceLabs support Airbnb integration?"
    )


def test_insufficient_answer_detection():
    assert answer_indicates_insufficient(
        "I couldn't find enough information in the documentation."
    )
    assert answer_indicates_insufficient(
        "I couldn't find enough information in the current documentation."
    )
    assert not answer_indicates_insufficient(
        "Airbnb sync works via the channel manager. Sources: Airbnb Integration"
    )


def test_html_noise_does_not_false_unsupported():
    chunks = [
        _chunk(
            content="PriceLabs syncs with Airbnb via the channel manager.",
            title="Airbnb Integration",
            similarity=0.9,
        )
    ]
    evidence = EvidenceAssessor().assess(
        "<script>alert(1)</script> Airbnb sync failed.",
        chunks,
    )
    assert evidence.unsupported_topic is False
    assert "script" not in evidence.focus_terms
    assert "alert" not in evidence.focus_terms


def test_giant_token_ignored_for_critical_match():
    chunks = [
        _chunk(
            content="Airbnb sync documentation.",
            title="Airbnb Integration",
            similarity=0.9,
        )
    ]
    evidence = EvidenceAssessor().assess("Airbnb " + ("x" * 200), chunks)
    assert evidence.unsupported_topic is False


def test_mark_supported_override():
    evidence = EvidenceAssessor().assess(
        "Does PriceLabs support WhatsApp?",
        [AIRBNB_CHUNK],
    )
    assert evidence.unsupported_topic is True
    fixed = EvidenceAssessor().mark_supported(evidence)
    assert fixed.unsupported_topic is False
    assert fixed.direct_mention == 1.0
