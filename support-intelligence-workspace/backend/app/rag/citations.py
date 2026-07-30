"""Citation builder — public-facing sources (no internal chunk IDs)."""

from __future__ import annotations

from app.rag.retrieval.types import RetrievedChunk
from app.schemas.ask import AskCitation


class CitationBuilder:
    def build(self, chunks: list[RetrievedChunk]) -> list[AskCitation]:
        """One citation per document — best similarity wins."""
        best: dict[str, RetrievedChunk] = {}
        for chunk in chunks:
            current = best.get(chunk.document_id)
            if current is None or chunk.similarity > current.similarity:
                best[chunk.document_id] = chunk

        ordered = sorted(best.values(), key=lambda c: c.similarity, reverse=True)
        return [
            AskCitation(
                title=c.title,
                category=c.category,
                version=c.version,
                last_updated=c.last_updated,
                similarity=round(c.similarity, 4),
                document_id=c.document_id,
                excerpt=_excerpt(c.content),
            )
            for c in ordered
        ]


def _excerpt(text: str, limit: int = 180) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1] + "…"
