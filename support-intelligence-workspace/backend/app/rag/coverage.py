"""
Documentation coverage — distinct from confidence.

Confidence ≈ "how trustworthy is this retrieval for answering?"
Coverage  ≈ "how much documentation exists on this topic?"

If evidence does not mention the requested feature, coverage is Low
regardless of vector similarity.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from app.rag.evidence import UNSUPPORTED_SCORE_CAP, EvidenceResult
from app.rag.retrieval.types import RetrievedChunk


@dataclass(frozen=True)
class CoverageResult:
    score: float  # 0–100
    label: str
    factors: dict[str, float]


class CoverageCalculator:
    """
    Heuristic:

    - direct_mention     35%  — feature explicitly present
    - entity_overlap     25%
    - unique_doc_ratio   15%
    - avg_similarity     15%
    - top_hit_strength   10%
    """

    STRONG_HIT = 0.55

    def calculate(
        self,
        chunks: list[RetrievedChunk],
        *,
        evidence: EvidenceResult | None = None,
    ) -> CoverageResult:
        if not chunks:
            return CoverageResult(
                score=10.0,
                label="Documentation is insufficient.",
                factors={
                    "direct_mention": 0.0,
                    "entity_overlap": 0.0,
                    "unique_doc_ratio": 0.0,
                    "avg_similarity": 0.0,
                    "top_hit_strength": 0.0,
                },
            )

        sims = [c.similarity for c in chunks]
        top_sim = max(sims)
        avg_sim = mean(sims)
        unique_docs = len({c.document_id for c in chunks})
        unique_ratio = min(1.0, unique_docs / 3.0)
        top_hit = (
            1.0
            if top_sim >= self.STRONG_HIT
            else max(0.0, top_sim / self.STRONG_HIT)
        )

        direct = evidence.direct_mention if evidence else 0.0
        entity = evidence.entity_overlap if evidence else 0.0

        score = round(
            max(
                0.0,
                min(
                    100.0,
                    (
                        0.35 * direct
                        + 0.25 * entity
                        + 0.15 * unique_ratio
                        + 0.15 * avg_sim
                        + 0.10 * top_hit
                    )
                    * 100,
                ),
            ),
            1,
        )

        if evidence and evidence.unsupported_topic:
            score = min(score, UNSUPPORTED_SCORE_CAP)
        elif direct < 0.5:
            score = min(score, 45.0)

        return CoverageResult(
            score=score,
            label=_label(score),
            factors={
                "direct_mention": round(direct, 4),
                "entity_overlap": round(entity, 4),
                "unique_doc_ratio": round(unique_ratio, 4),
                "avg_similarity": round(avg_sim, 4),
                "top_hit_strength": round(top_hit, 4),
            },
        )

    def clamp_unsupported(self, result: CoverageResult) -> CoverageResult:
        score = min(result.score, UNSUPPORTED_SCORE_CAP)
        return CoverageResult(
            score=score,
            label=_label(score),
            factors={**result.factors, "unsupported_cap": UNSUPPORTED_SCORE_CAP},
        )


def _label(score: float) -> str:
    if score >= 85:
        return "Documentation fully covers the topic."
    if score >= 50:
        return "Partial documentation exists."
    return "Documentation is insufficient."
