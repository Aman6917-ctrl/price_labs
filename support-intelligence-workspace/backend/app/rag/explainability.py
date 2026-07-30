"""Explainability — help engineers trust (or challenge) the suggestion."""

from __future__ import annotations

from app.models.enums import ConfidenceLevel
from app.rag.confidence import ConfidenceResult
from app.rag.coverage import CoverageResult
from app.rag.retrieval.types import RetrievedChunk


class ExplainabilityBuilder:
    def build(
        self,
        chunks: list[RetrievedChunk],
        confidence: ConfidenceResult,
        coverage: CoverageResult,
        *,
        unsupported_topic: bool = False,
        evidence_reasons: list[str] | None = None,
    ) -> str:
        if unsupported_topic:
            detail = "; ".join(evidence_reasons or []) or (
                "retrieved chunks do not explicitly mention the requested feature"
            )
            return (
                "Knowledge gap detected: the documentation does not appear to cover "
                f"this topic ({detail}). "
                f"Confidence forced Low ({confidence.score:.0f}/100) and coverage "
                f"Low ({coverage.score:.0f}%) — escalate to a human; do not send "
                "this answer to the customer."
            )

        if not chunks:
            return (
                "No supporting documents were retrieved. "
                "Confidence is Low and coverage is insufficient — "
                "do not send this answer without checking the knowledge base manually."
            )

        unique_docs = len({c.document_id for c in chunks})
        top = max(c.similarity for c in chunks)
        level_reason = _level_reason(confidence.level, unique_docs, confidence.factors)

        return (
            f"Retrieved {len(chunks)} supporting chunk(s) across {unique_docs} document(s). "
            f"Highest similarity: {top:.2f}. "
            f"Documentation coverage: {coverage.score:.0f}% ({coverage.label}) "
            f"Confidence: {confidence.level.value.capitalize()} ({confidence.score:.0f}/100) "
            f"because {level_reason}"
        )


def _level_reason(
    level: ConfidenceLevel,
    unique_docs: int,
    factors: dict[str, float],
) -> str:
    if level == ConfidenceLevel.HIGH:
        if unique_docs >= 2:
            return (
                "multiple independent documents agree and the requested feature "
                "is explicitly mentioned."
            )
        return "a strong top match with explicit feature mention in the evidence."
    if level == ConfidenceLevel.MEDIUM:
        return (
            f"moderate retrieval strength "
            f"(top={factors.get('top_similarity', 0):.2f}, "
            f"evidence={factors.get('evidence_quality', 0):.2f}) — verify before sending."
        )
    return (
        "weak evidence or missing feature mention — treat as a draft only and "
        "search docs manually."
    )
