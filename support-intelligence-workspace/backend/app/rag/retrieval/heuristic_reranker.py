"""
Heuristic reranker (MVP).

Strategy:
1. Prefer higher similarity.
2. Keyword / entity overlap with the query.
3. Soft diversity boost so multiple documents surface.
4. Prefer Release Notes over Changelog when both match similarly.
5. Mild freshness boost from last_updated when parseable.
6. Deduplicate near-identical chunk content.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

from app.rag.retrieval.types import RetrievedChunk

_TOKEN = re.compile(r"[a-z0-9]+", re.I)
_STOP = frozenset(
    "a an the is are do does how what when why with from for and or to of in on at".split()
)


class HeuristicReranker:
    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        *,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        if not chunks:
            return []

        # Deduplicate by content fingerprint (keep highest similarity)
        unique: list[RetrievedChunk] = []
        seen_fp: set[str] = set()
        for chunk in sorted(chunks, key=lambda c: c.similarity, reverse=True):
            fp = _fingerprint(chunk.content)
            if fp in seen_fp:
                continue
            seen_fp.add(fp)
            unique.append(chunk)

        q_tokens = _tokens(query)
        seen_docs: dict[str, int] = {}
        scored: list[tuple[float, RetrievedChunk]] = []

        for chunk in unique:
            doc_count = seen_docs.get(chunk.document_id, 0)
            diversity = 1.0 if doc_count == 0 else max(0.85, 1.0 - 0.08 * doc_count)
            freshness = _freshness_boost(chunk.last_updated)
            keyword = _keyword_boost(q_tokens, chunk)
            source_pref = _source_preference(chunk)
            score = chunk.similarity * diversity * freshness * keyword * source_pref
            scored.append((score, chunk))
            seen_docs[chunk.document_id] = doc_count + 1

        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]


class NoOpReranker:
    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        *,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        return chunks[:top_k]


def _fingerprint(text: str) -> str:
    normalized = " ".join(text.lower().split())
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:16]


def _tokens(text: str) -> set[str]:
    return {t for t in _TOKEN.findall(text.lower()) if len(t) > 2 and t not in _STOP}


def _keyword_boost(q_tokens: set[str], chunk: RetrievedChunk) -> float:
    if not q_tokens:
        return 1.0
    title = (chunk.title or "").lower()
    category = (chunk.category or "").lower()
    blob = f"{title} {category} {' '.join(chunk.tags)} {chunk.content}".lower()
    c_tokens = _tokens(blob)
    if not c_tokens:
        return 0.92
    overlap = len(q_tokens & c_tokens) / len(q_tokens)
    # Strong boost when the query entity appears in title/category
    title_hit = any(
        t in title or t in category for t in q_tokens if len(t) >= 4
    )
    base = 0.90 + 0.22 * overlap
    return min(1.18, base + (0.10 if title_hit else 0.0))


def _source_preference(chunk: RetrievedChunk) -> float:
    """Prefer Release Notes over Changelog for similar matches."""
    title = (chunk.title or "").lower()
    category = (chunk.category or "").lower()
    doc_id = (chunk.document_id or "").lower()
    hay = f"{title} {category} {doc_id}"
    if "release note" in hay or "release-notes" in hay:
        return 1.04
    if "changelog" in hay:
        return 0.96
    return 1.0


def _freshness_boost(last_updated: str) -> float:
    if not last_updated:
        return 1.0
    try:
        dt = datetime.strptime(last_updated[:10], "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return 1.0
    age_days = (datetime.now(timezone.utc) - dt).days
    if age_days <= 90:
        return 1.03
    if age_days <= 180:
        return 1.0
    return 0.97
