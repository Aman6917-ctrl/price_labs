"""
Evidence / relevance assessment for Ask scoring.

Vector similarity alone must never produce High confidence. We check whether
retrieved chunks actually mention the requested feature / entities.

Unsupported-topic detection must NOT reject supported products (e.g. Airbnb)
when the matching document is present — only truly missing topics become gaps.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace

from app.rag.retrieval.types import RetrievedChunk

# Allow booking.com / gpt-5, but never trailing punctuation like "failed."
_TOKEN = re.compile(r"[a-z0-9]+(?:[./_+-][a-z0-9]+)*", re.IGNORECASE)
_HTML_TAG = re.compile(r"<[^>]+>")
_MAX_TOKEN_LEN = 40
_NOISE_TOKENS = frozenset(
    {
        "script",
        "alert",
        "onclick",
        "onerror",
        "javascript",
        "ignore",
        "previous",
        "instructions",
        "reveal",
        "system",
        "prompt",
        "assistant",
        "dan",
        "jailbreak",
    }
)

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "do",
        "does",
        "did",
        "can",
        "could",
        "should",
        "would",
        "how",
        "what",
        "when",
        "where",
        "why",
        "who",
        "which",
        "with",
        "from",
        "into",
        "for",
        "and",
        "or",
        "but",
        "to",
        "of",
        "in",
        "on",
        "at",
        "my",
        "our",
        "your",
        "their",
        "i",
        "me",
        "we",
        "you",
        "it",
        "this",
        "that",
        "these",
        "those",
        "about",
        "any",
        "have",
        "has",
        "had",
        "be",
        "been",
        "being",
        "please",
        "help",
        "tell",
        "explain",
        "using",
        "use",
        "get",
        "set",
        "need",
        "want",
        "pricelabs",
        "labs",
        "support",
        "integrate",
        "integration",
        "integrations",
        "feature",
        "features",
        "work",
        "works",
        "working",
        "available",
        "offer",
        "offers",
        "provide",
        "provides",
        "question",
        "customer",
        "issue",
        "problem",
        "error",
        "errors",
        "not",
        "no",
    }
)

# Symptom / status words — useful for ranking, never required for "supported"
_SYMPTOM_TERMS = frozenset(
    {
        "failed",
        "failing",
        "failure",
        "broken",
        "wrong",
        "suspended",
        "updating",
        "update",
        "updated",
        "connectivity",
        "connection",
        "overview",
        "guide",
        "help",
    }
)

# Generic nouns that must not alone prove a feature exists
_WEAK_ALONE = frozenset(
    {
        "policy",
        "account",
        "login",
        "password",
        "guide",
        "overview",
        "sync",
        "data",
        "system",
        "user",
        "team",
        "api",
    }
)

_FEATURE_PATTERNS = (
    re.compile(
        r"\b(?:support|supports|supporting)\s+([a-z0-9][\w+./-]*(?:\s+[a-z0-9][\w+./-]*){0,3})",
        re.I,
    ),
    re.compile(
        r"\bintegrat(?:e|es|ion|ions)?\s+(?:with|to)\s+([a-z0-9][\w+./-]*(?:\s+[a-z0-9][\w+./-]*){0,3})",
        re.I,
    ),
    re.compile(
        r"\bconnect(?:s|ion|ions)?\s+(?:with|to)\s+([a-z0-9][\w+./-]*(?:\s+[a-z0-9][\w+./-]*){0,3})",
        re.I,
    ),
    re.compile(
        r"\b(?:reset|change|update)\s+(?:my\s+)?([a-z0-9][\w+./-]*)\s+(?:password|account|login)",
        re.I,
    ),
    re.compile(
        r"\b([a-z0-9][\w+./-]*)\s+(?:password|integration|webhook|api|pms)\b",
        re.I,
    ),
    re.compile(
        r"\b(?:what\s+is|what's)\s+(?:the\s+)?([a-z0-9][\w+./-]*(?:\s+[a-z0-9][\w+./-]*){0,3}\s+policy)\b",
        re.I,
    ),
    re.compile(
        r"\b([a-z0-9][\w+./-]*)\s+policy\b",
        re.I,
    ),
    re.compile(
        r"\b(?:who\s+is|who's)\s+(?:the\s+)?(ceo|cto|founder|owner)\b",
        re.I,
    ),
    re.compile(
        r"\b(ceo|cto|founder)\s+of\b",
        re.I,
    ),
)

_INSUFFICIENT_MARKERS = (
    "couldn't find enough information",
    "could not find enough information",
    "not enough information",
    "insufficient information",
    "insufficient documentation",
    "documentation is insufficient",
    "no documentation",
    "don't have information",
    "do not have information",
    "unable to find",
    "can't find enough",
    "cannot find enough",
    "doesn't cover",
    "does not cover",
    "not covered in",
    "not mentioned in the documentation",
    "no information in the documentation",
    "outside the documentation",
)

UNSUPPORTED_SCORE_CAP = 30.0


@dataclass(frozen=True)
class EvidenceResult:
    """How well retrieved evidence answers the question."""

    keyword_overlap: float  # 0–1
    entity_overlap: float  # 0–1
    direct_mention: float  # 0–1 (requested feature appears in evidence)
    evidence_quality: float  # 0–1 blended
    semantic_relevance: float  # 0–1 similarity tempered by mention
    unsupported_topic: bool
    focus_terms: tuple[str, ...] = field(default_factory=tuple)
    missing_terms: tuple[str, ...] = field(default_factory=tuple)
    reasons: tuple[str, ...] = field(default_factory=tuple)
    supporting_document_ids: tuple[str, ...] = field(default_factory=tuple)


class EvidenceAssessor:
    def assess(self, question: str, chunks: list[RetrievedChunk]) -> EvidenceResult:
        question = sanitize_question(question)
        focus = extract_focus_terms(question)
        features = extract_feature_phrases(question)
        critical = _critical_terms(features, focus)
        primary = _primary_entities(features, critical, focus)

        if not chunks:
            return EvidenceResult(
                keyword_overlap=0.0,
                entity_overlap=0.0,
                direct_mention=0.0,
                evidence_quality=0.0,
                semantic_relevance=0.0,
                unsupported_topic=True,
                focus_terms=tuple(focus),
                missing_terms=tuple(primary or critical or focus),
                reasons=("No chunks retrieved",),
            )

        corpus = "\n".join(_chunk_text(c) for c in chunks).lower()
        present = [t for t in focus if _term_in_evidence(t, chunks, corpus)]
        missing = [t for t in focus if not _term_in_evidence(t, chunks, corpus)]

        keyword_overlap = len(present) / max(len(focus), 1) if focus else 0.0

        entities = [t for t in focus if len(t) >= 4 and t not in _WEAK_ALONE]
        if not entities:
            entities = [t for t in focus if t not in _WEAK_ALONE] or list(focus)
        ent_present = [t for t in entities if _term_in_evidence(t, chunks, corpus)]
        entity_overlap = (
            len(ent_present) / max(len(entities), 1) if entities else 0.0
        )

        # Primary product/feature entities decide support (Airbnb, Booking.com, …)
        check_terms = primary or critical or [
            t for t in focus if t not in _WEAK_ALONE
        ]
        if check_terms:
            mentioned = sum(
                1 for f in check_terms if _term_in_evidence(f, chunks, corpus)
            )
            direct_mention = mentioned / len(check_terms)
            feature_missing = [
                f for f in check_terms if not _term_in_evidence(f, chunks, corpus)
            ]
        else:
            strong = [t for t in focus if t not in _WEAK_ALONE] or list(focus)
            hit = sum(1 for t in strong if _term_in_evidence(t, chunks, corpus))
            direct_mention = hit / max(len(strong), 1)
            feature_missing = [
                t for t in strong if not _term_in_evidence(t, chunks, corpus)
            ]

        supporting_ids = tuple(
            dict.fromkeys(
                c.document_id
                for c in chunks
                if any(
                    _chunk_mentions_term(c, t)
                    for t in (primary or critical or present or [])
                )
            )
        )

        # Hard guarantee: if a matching product doc is present, never unsupported
        doc_supports = bool(supporting_ids) and (
            not primary
            or all(_term_in_evidence(p, chunks, corpus) for p in primary)
        )
        if doc_supports and primary:
            direct_mention = 1.0
            feature_missing = []

        sims = [c.similarity for c in chunks]
        top_sim = max(sims) if sims else 0.0
        semantic_relevance = top_sim * (
            0.25 + 0.75 * max(entity_overlap, direct_mention)
        )

        evidence_quality = (
            0.40 * direct_mention
            + 0.30 * entity_overlap
            + 0.20 * keyword_overlap
            + 0.10 * min(1.0, top_sim)
        )

        unsupported = _is_unsupported(
            features=features,
            primary=primary,
            critical=critical,
            focus=focus,
            direct_mention=direct_mention,
            entity_overlap=entity_overlap,
            keyword_overlap=keyword_overlap,
            feature_missing=feature_missing,
            doc_supports=doc_supports,
            top_sim=top_sim,
        )

        reasons: list[str] = []
        if unsupported:
            miss = feature_missing or missing or list(primary)
            if miss:
                reasons.append(
                    "Requested topic not mentioned in retrieved docs: "
                    + ", ".join(miss[:6])
                )
            else:
                reasons.append(
                    "Retrieved evidence does not explicitly answer the question"
                )

        return EvidenceResult(
            keyword_overlap=round(keyword_overlap, 4),
            entity_overlap=round(entity_overlap, 4),
            direct_mention=round(direct_mention, 4),
            evidence_quality=round(evidence_quality, 4),
            semantic_relevance=round(semantic_relevance, 4),
            unsupported_topic=unsupported,
            focus_terms=tuple(focus),
            missing_terms=tuple(feature_missing or missing),
            reasons=tuple(reasons),
            supporting_document_ids=supporting_ids,
        )

    def has_direct_doc_support(
        self, question: str, chunks: list[RetrievedChunk]
    ) -> bool:
        """True when a retrieved doc clearly matches the asked product/feature."""
        if not chunks:
            return False
        question = sanitize_question(question)
        features = extract_feature_phrases(question)
        focus = extract_focus_terms(question)
        critical = _critical_terms(features, focus)
        primary = _primary_entities(features, critical, focus)
        if not primary:
            return False
        corpus = "\n".join(_chunk_text(c) for c in chunks).lower()
        return all(_term_in_evidence(p, chunks, corpus) for p in primary)

    def mark_supported(self, evidence: EvidenceResult) -> EvidenceResult:
        """Override a false-unsupported result after doc-support verification."""
        return replace(
            evidence,
            unsupported_topic=False,
            direct_mention=1.0,
            missing_terms=(),
            reasons=(),
            evidence_quality=max(evidence.evidence_quality, 0.85),
        )


def sanitize_question(question: str) -> str:
    """Strip HTML / nulls before evidence matching (does not alter persistence copy)."""
    text = (question or "").replace("\x00", " ")
    text = _HTML_TAG.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_focus_terms(question: str) -> list[str]:
    question = sanitize_question(question)
    tokens = [t.lower().strip(".,!?;:") for t in _TOKEN.findall(question)]
    terms = [
        t
        for t in tokens
        if t
        and t not in _STOPWORDS
        and t not in _SYMPTOM_TERMS
        and t not in _NOISE_TOKENS
        and 2 < len(t) <= _MAX_TOKEN_LEN
    ]
    features = extract_feature_phrases(question)
    ordered: list[str] = []
    seen: set[str] = set()
    for t in features + terms:
        cleaned = t.strip(".,!?;:")
        if (
            cleaned
            and cleaned not in seen
            and cleaned not in _NOISE_TOKENS
            and len(cleaned) <= _MAX_TOKEN_LEN
        ):
            seen.add(cleaned)
            ordered.append(cleaned)
    return ordered


def extract_feature_phrases(question: str) -> list[str]:
    question = sanitize_question(question)
    found: list[str] = []
    for pattern in _FEATURE_PATTERNS:
        for match in pattern.finditer(question):
            phrase = match.group(1).strip().lower()
            phrase = re.sub(r"\s+", " ", phrase)
            parts = [
                p
                for p in phrase.split()
                if p not in _STOPWORDS
                and p not in {"integration", "integrations", "feature"}
            ]
            if not parts:
                raw = phrase.strip()
                if raw and raw not in found:
                    found.append(raw)
                continue
            cleaned = " ".join(parts)
            if cleaned and cleaned not in found:
                found.append(cleaned)
            if parts[0] not in found:
                found.append(parts[0])
    return found


def answer_indicates_insufficient(answer: str | None) -> bool:
    text = (answer or "").strip().lower()
    if not text:
        return True
    from app.rag.prompt_builder import INSUFFICIENT_ANSWER

    if text == INSUFFICIENT_ANSWER.lower():
        return True
    if INSUFFICIENT_ANSWER.lower() in text:
        return True
    return any(marker in text for marker in _INSUFFICIENT_MARKERS)


def _critical_terms(features: list[str], focus: list[str]) -> list[str]:
    """
    Terms that must appear for the topic to count as supported.

    Feature/entity phrases are required. Symptom words are never required.
    """
    if features:
        critical = [
            f.strip(".,!?;:")
            for f in features
            if f.strip(".,!?;:")
            and f.strip(".,!?;:") not in _SYMPTOM_TERMS
            and (" " in f or f not in _WEAK_ALONE)
        ]
        return critical or [f.strip(".,!?;:") for f in features if f.strip(".,!?;:")]
    strong = [
        t for t in focus if t not in _WEAK_ALONE and t not in _SYMPTOM_TERMS
    ]
    return strong


def _primary_entities(
    features: list[str],
    critical: list[str],
    focus: list[str],
) -> list[str]:
    """
    Brand / product entities that decide supported vs gap.

    Prefer feature phrases (Airbnb, WhatsApp, Booking.com). Fall back to
    strong critical nouns — never symptom/weak generics alone.
    """
    if features:
        # Prefer single-token product names; keep multi-word if that's all we have
        singles = [
            f
            for f in features
            if " " not in f and f not in _WEAK_ALONE and f not in _SYMPTOM_TERMS
        ]
        if singles:
            return list(dict.fromkeys(singles))
        return list(dict.fromkeys(features))[:3]
    if critical:
        return list(dict.fromkeys(critical))[:3]
    strong = [t for t in focus if t not in _WEAK_ALONE and t not in _SYMPTOM_TERMS]
    return strong[:3]


def _term_in_corpus(term: str, corpus: str) -> bool:
    term = term.lower().strip().strip(".,!?;:")
    if not term:
        return False
    if " " in term:
        return term in corpus
    return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", corpus) is not None


def _chunk_mentions_term(chunk: RetrievedChunk, term: str) -> bool:
    """Match against title/category/tags/document_id/content — not body alone."""
    term = term.lower().strip().strip(".,!?;:")
    if not term:
        return False
    doc_id = (chunk.document_id or "").lower().replace("_", "-")
    slug = term.replace(" ", "-").replace(".", "-")
    if slug and slug in doc_id:
        return True
    if term.replace(".", "") and term.replace(".", "") in doc_id.replace("-", "").replace(
        ".", ""
    ):
        # booking.com ↔ booking-com-integration
        compact_term = re.sub(r"[^a-z0-9]", "", term)
        compact_id = re.sub(r"[^a-z0-9]", "", doc_id)
        if compact_term and compact_term in compact_id:
            return True
    blob = _chunk_text(chunk).lower()
    return _term_in_corpus(term, blob)


def _term_in_evidence(
    term: str,
    chunks: list[RetrievedChunk],
    corpus: str,
) -> bool:
    if _term_in_corpus(term, corpus):
        return True
    return any(_chunk_mentions_term(c, term) for c in chunks)


def _is_unsupported(
    *,
    features: list[str],
    primary: list[str],
    critical: list[str],
    focus: list[str],
    direct_mention: float,
    entity_overlap: float,
    keyword_overlap: float,
    feature_missing: list[str],
    doc_supports: bool,
    top_sim: float,
) -> bool:
    """
    Knowledge-gap only when:
    - no relevant documents match the asked product/feature, OR
    - retrieved evidence clearly does not answer the question.

    If a matching product document is present (doc_supports), never unsupported.
    """
    if doc_supports and direct_mention >= 1.0:
        return False

    # Named feature / integration asks (WhatsApp, Netflix, CEO, refund policy)
    if features and primary:
        return direct_mention < 1.0 or bool(feature_missing)

    # Non-feature troubleshooting / how-to: need topic overlap, not perfect match
    if critical:
        if direct_mention >= 0.99:
            return False
        if entity_overlap == 0.0 and direct_mention == 0.0:
            return True
        # Weak lexical overlap + low similarity → gap
        if direct_mention < 0.5 and top_sim < 0.35:
            return True
        return False

    if focus and entity_overlap == 0.0 and keyword_overlap == 0.0:
        return True
    if not critical and not features and keyword_overlap < 0.34:
        return True
    return False


def _chunk_text(chunk: RetrievedChunk) -> str:
    tags = " ".join(chunk.tags)
    return f"{chunk.title}\n{chunk.category}\n{tags}\n{chunk.content}"
