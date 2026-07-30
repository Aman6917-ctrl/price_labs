"""Answer quality + recommended action heuristics (no second LLM call)."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import (
    AnswerQuality,
    ConfidenceLevel,
    RecommendedAction,
)
from app.rag.evidence import answer_indicates_insufficient
from app.schemas.ask import AskCitation


@dataclass(frozen=True)
class QualityResult:
    label: AnswerQuality
    reasons: list[str]


@dataclass(frozen=True)
class ActionResult:
    action: RecommendedAction
    reason: str


class AnswerQualityEvaluator:
    """
    Lightweight post-generation checks.

    Signals: emptiness, length, citations, coverage, confidence, unsupported topic.
    """

    SHORT_ANSWER_CHARS = 80

    def evaluate(
        self,
        *,
        answer: str,
        citations: list[AskCitation],
        coverage_score: float,
        confidence_level: ConfidenceLevel,
        confidence_score: float,
        skipped_llm: bool,
        unsupported_topic: bool = False,
    ) -> QualityResult:
        reasons: list[str] = []
        text = (answer or "").strip()
        insufficient = (
            skipped_llm
            or answer_indicates_insufficient(text)
            or unsupported_topic
        )

        if not text:
            reasons.append("Answer is empty")
            return QualityResult(AnswerQuality.POOR, reasons)

        if unsupported_topic:
            reasons.append("Requested feature is not mentioned in retrieved documentation")

        if len(text) < self.SHORT_ANSWER_CHARS:
            reasons.append(f"Answer is very short (<{self.SHORT_ANSWER_CHARS} chars)")

        if not citations:
            reasons.append("No citations attached")

        if coverage_score < 40:
            reasons.append(f"Low documentation coverage ({coverage_score:.0f}%)")
        elif coverage_score < 60:
            reasons.append(f"Partial documentation coverage ({coverage_score:.0f}%)")

        if confidence_level == ConfidenceLevel.LOW:
            reasons.append(f"Low confidence ({confidence_score:.0f}/100)")
        elif confidence_level == ConfidenceLevel.MEDIUM:
            reasons.append(f"Medium confidence ({confidence_score:.0f}/100)")

        if answer_indicates_insufficient(text) or skipped_llm:
            reasons.append("Model skipped or returned insufficient-documentation reply")

        # Label selection (worst applicable wins)
        if (
            not text
            or insufficient
            or coverage_score <= 30
            or confidence_score <= 30
            or (
                confidence_level == ConfidenceLevel.LOW and coverage_score < 50
            )
        ):
            if not reasons:
                reasons.append("Weak grounding signals")
            return QualityResult(AnswerQuality.POOR, reasons)

        if (
            confidence_level == ConfidenceLevel.LOW
            or coverage_score < 50
            or not citations
            or len(text) < self.SHORT_ANSWER_CHARS
        ):
            return QualityResult(
                AnswerQuality.NEEDS_REVIEW,
                reasons or ["One or more review signals triggered"],
            )

        if (
            confidence_level == ConfidenceLevel.HIGH
            and coverage_score >= 85
            and citations
            and len(text) >= self.SHORT_ANSWER_CHARS
        ):
            return QualityResult(
                AnswerQuality.EXCELLENT,
                ["Strong confidence, coverage, citations, and answer length"],
            )

        return QualityResult(
            AnswerQuality.GOOD,
            reasons or ["Solid retrieval with acceptable answer length"],
        )


class RecommendedActionResolver:
    """
    Rule-based next step for the support engineer.

    Priority:
      unsupported / insufficient → ESCALATE_TO_HUMAN (knowledge gap)
      coverage < 40              → FLAG_KNOWLEDGE_GAP
      confidence LOW             → VERIFY_DOCUMENTATION
      quality POOR               → ESCALATE_TO_HUMAN
      quality NEEDS_REVIEW       → VERIFY_DOCUMENTATION
      else                       → SEND_RESPONSE
    """

    def resolve(
        self,
        *,
        coverage_score: float,
        confidence_level: ConfidenceLevel,
        quality: AnswerQuality,
        unsupported_topic: bool = False,
        insufficient_answer: bool = False,
    ) -> ActionResult:
        if unsupported_topic or insufficient_answer:
            return ActionResult(
                RecommendedAction.ESCALATE_TO_HUMAN,
                "Unsupported topic / knowledge gap — escalate to a human and flag "
                "missing documentation.",
            )
        if coverage_score < 40:
            return ActionResult(
                RecommendedAction.FLAG_KNOWLEDGE_GAP,
                f"Coverage {coverage_score:.0f}% is below 40% — docs likely missing or thin.",
            )
        if confidence_level == ConfidenceLevel.LOW:
            return ActionResult(
                RecommendedAction.VERIFY_DOCUMENTATION,
                "Confidence is Low — verify sources before sending to the customer.",
            )
        if quality == AnswerQuality.POOR:
            return ActionResult(
                RecommendedAction.ESCALATE_TO_HUMAN,
                "Answer quality is Poor — escalate or rewrite manually.",
            )
        if quality == AnswerQuality.NEEDS_REVIEW:
            return ActionResult(
                RecommendedAction.VERIFY_DOCUMENTATION,
                "Answer needs review — spot-check citations and coverage.",
            )
        return ActionResult(
            RecommendedAction.SEND_RESPONSE,
            "Confidence and coverage look solid — safe to send after a quick skim.",
        )
