"""
Document health scoring (MVP mock heuristics).

Future: replace with AI evaluation pipeline without changing AskService.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.models.enums import DocumentHealth
from app.rag.retrieval.types import RetrievedChunk


@dataclass(frozen=True)
class DocumentHealthResult:
    document_id: str
    title: str
    category: str
    health: DocumentHealth
    reason: str
    last_updated: str
    version: str


class DocumentHealthCalculator:
    """
    Priority (worst wins):
    1. Many knowledge gaps for this document → outdated / needs_review
    2. Age from last_updated
    3. Default healthy
    """

    def assess(
        self,
        chunks: list[RetrievedChunk],
        *,
        gap_counts: dict[str, int] | None = None,
    ) -> list[DocumentHealthResult]:
        gap_counts = gap_counts or {}
        seen: set[str] = set()
        results: list[DocumentHealthResult] = []

        for chunk in chunks:
            if chunk.document_id in seen:
                continue
            seen.add(chunk.document_id)
            gaps = gap_counts.get(chunk.document_id, 0)
            health, reason = _score(chunk.last_updated, gaps)
            results.append(
                DocumentHealthResult(
                    document_id=chunk.document_id,
                    title=chunk.title,
                    category=chunk.category,
                    health=health,
                    reason=reason,
                    last_updated=chunk.last_updated,
                    version=chunk.version,
                )
            )
        return results


def _score(last_updated: str, gap_count: int) -> tuple[DocumentHealth, str]:
    if gap_count >= 3:
        return (
            DocumentHealth.OUTDATED,
            f"{gap_count} knowledge-gap reports linked to this document.",
        )
    if gap_count >= 1:
        age_health, age_reason = _from_age(last_updated)
        if age_health == DocumentHealth.HEALTHY:
            return (
                DocumentHealth.NEEDS_REVIEW,
                f"{gap_count} open knowledge-gap report(s).",
            )
        return age_health, age_reason

    return _from_age(last_updated)


def _from_age(last_updated: str) -> tuple[DocumentHealth, str]:
    if not last_updated:
        return DocumentHealth.NEEDS_REVIEW, "Missing last_updated metadata."
    try:
        dt = datetime.strptime(last_updated[:10], "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return DocumentHealth.NEEDS_REVIEW, "Unparseable last_updated metadata."

    age_days = (datetime.now(timezone.utc) - dt).days
    if age_days > 180:
        return (
            DocumentHealth.OUTDATED,
            f"Last updated {age_days} days ago (>180).",
        )
    if age_days > 90:
        return (
            DocumentHealth.NEEDS_REVIEW,
            f"Last updated {age_days} days ago (>90).",
        )
    return DocumentHealth.HEALTHY, f"Updated {age_days} days ago."
