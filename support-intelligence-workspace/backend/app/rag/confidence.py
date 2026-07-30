"""
Heuristic confidence — NEVER derived from the LLM.

Score is 0–100. Similarity alone cannot produce High confidence; evidence
(entity / keyword / direct feature mention) is required.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev

from app.config import Settings
from app.models.enums import ConfidenceLevel
from app.rag.evidence import UNSUPPORTED_SCORE_CAP, EvidenceResult
from app.rag.retrieval.types import RetrievedChunk


@dataclass(frozen=True)
class ConfidenceResult:
    score: float  # 0–100
    level: ConfidenceLevel
    factors: dict[str, float]


class ConfidenceCalculator:
    """
    Weighted blend:

    - top_similarity       20%
    - avg_similarity       10%
    - semantic_relevance   20%  — similarity tempered by mention
    - evidence_quality     25%  — entity/keyword/direct mention
    - direct_mention       15%
    - supporting_docs       5%
    - agreement             5%
    """

    def __init__(self, settings: Settings) -> None:
        self._high = settings.confidence_high * 100
        self._medium = settings.confidence_medium * 100
        self._top_k = settings.rag_top_k

    def calculate(
        self,
        chunks: list[RetrievedChunk],
        *,
        evidence: EvidenceResult | None = None,
    ) -> ConfidenceResult:
        if not chunks:
            return ConfidenceResult(
                score=0.0,
                level=ConfidenceLevel.LOW,
                factors={
                    "top_similarity": 0.0,
                    "avg_similarity": 0.0,
                    "semantic_relevance": 0.0,
                    "evidence_quality": 0.0,
                    "direct_mention": 0.0,
                    "supporting_docs": 0.0,
                    "agreement": 0.0,
                },
            )

        sims = [c.similarity for c in chunks]
        top_sim = max(sims)
        avg_sim = mean(sims)
        unique_docs = len({c.document_id for c in chunks})
        supporting = min(1.0, unique_docs / 3.0)
        agreement = _agreement(sims)

        ev_quality = evidence.evidence_quality if evidence else 0.0
        direct = evidence.direct_mention if evidence else 0.0
        semantic = (
            evidence.semantic_relevance
            if evidence
            else top_sim * 0.25  # without evidence, heavily discount similarity
        )

        score_0_1 = (
            0.20 * top_sim
            + 0.10 * avg_sim
            + 0.20 * semantic
            + 0.25 * ev_quality
            + 0.15 * direct
            + 0.05 * supporting
            + 0.05 * agreement
        )
        score = round(max(0.0, min(100.0, score_0_1 * 100)), 1)

        # Hard guards — similarity alone must never yield High
        if evidence and evidence.unsupported_topic:
            score = min(score, UNSUPPORTED_SCORE_CAP)
        elif direct < 0.5:
            # No clear feature mention → at most medium band, usually lower
            score = min(score, self._medium - 0.1)
        elif ev_quality < 0.45:
            score = min(score, self._high - 0.1)

        # High requires real evidence + decent similarity
        if score >= self._high and (
            direct < 0.99
            or ev_quality < 0.55
            or top_sim < 0.35
            or (evidence is not None and evidence.unsupported_topic)
        ):
            score = min(score, self._high - 0.1)

        level = self._to_level(score)
        return ConfidenceResult(
            score=score,
            level=level,
            factors={
                "top_similarity": round(top_sim, 4),
                "avg_similarity": round(avg_sim, 4),
                "semantic_relevance": round(semantic, 4),
                "evidence_quality": round(ev_quality, 4),
                "direct_mention": round(direct, 4),
                "supporting_docs": round(supporting, 4),
                "agreement": round(agreement, 4),
            },
        )

    def clamp_unsupported(self, result: ConfidenceResult) -> ConfidenceResult:
        score = min(result.score, UNSUPPORTED_SCORE_CAP)
        return ConfidenceResult(
            score=score,
            level=self._to_level(score),
            factors={**result.factors, "unsupported_cap": UNSUPPORTED_SCORE_CAP},
        )

    def _to_level(self, score: float) -> ConfidenceLevel:
        if score >= self._high:
            return ConfidenceLevel.HIGH
        if score >= self._medium:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW


def _agreement(sims: list[float]) -> float:
    if len(sims) == 1:
        return sims[0]
    spread = pstdev(sims)
    return max(0.0, min(1.0, 1.0 - spread * 2.0))
