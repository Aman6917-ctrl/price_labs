"""
AnalyticsService — dashboard metrics from canonical collections.

Daily analytics rows are an optional cache updated by AnalyticsHandler.
GET /api/analytics always recomputes from questions / gaps / feedback / documents.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from statistics import mean

from app.models.enums import FeedbackType
from app.repositories.analytics import AnalyticsRepository
from app.repositories.document import DocumentRepository
from app.repositories.feedback import FeedbackRepository
from app.repositories.knowledge_gap import KnowledgeGapRepository
from app.repositories.question import QuestionRepository
from app.schemas.analytics import AnalyticsDashboard, NamedCount
from app.utils.datetime import normalize_datetime

_QUALITY_SCORE = {
    "excellent": 100.0,
    "good": 75.0,
    "needs_review": 45.0,
    "poor": 15.0,
}

_POSITIVE = {FeedbackType.THUMBS_UP.value, FeedbackType.POSITIVE.value}
_NEGATIVE = {FeedbackType.THUMBS_DOWN.value, FeedbackType.NEGATIVE.value}


class AnalyticsService:
    def __init__(
        self,
        analytics_repo: AnalyticsRepository,
        question_repo: QuestionRepository,
        gap_repo: KnowledgeGapRepository,
        document_repo: DocumentRepository,
        feedback_repo: FeedbackRepository | None = None,
    ) -> None:
        self._analytics_repo = analytics_repo
        self._question_repo = question_repo
        self._gap_repo = gap_repo
        self._document_repo = document_repo
        self._feedback_repo = feedback_repo

    async def get_dashboard(self) -> AnalyticsDashboard:
        # Boundaries are always timezone-aware UTC
        now = datetime.now(timezone.utc)
        start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_week = start_today - timedelta(days=start_today.weekday())

        questions = await self._question_repo.list(limit=500, sort=[("created_at", -1)])
        gaps = await self._gap_repo.list(limit=500, sort=[("created_at", -1)])
        documents = await self._document_repo.list(limit=500)
        feedback = []
        if self._feedback_repo is not None:
            feedback = await self._feedback_repo.list(limit=500)

        questions_today = sum(
            1 for q in questions if _is_on_or_after(q.created_at, start_today)
        )
        questions_week = sum(
            1 for q in questions if _is_on_or_after(q.created_at, start_week)
        )

        conf_scores = [
            (
                q.confidence_score * 100
                if q.confidence_score is not None and q.confidence_score <= 1
                else q.confidence_score
            )
            for q in questions
            if q.confidence_score is not None
        ]
        coverage_scores: list[float] = []
        quality_scores: list[float] = []
        processing_times: list[float] = []
        token_total = 0
        cost_total = 0.0
        token_samples = 0
        cost_samples = 0
        conf_dist: Counter[str] = Counter()
        cov_dist: Counter[str] = Counter()
        action_dist: Counter[str] = Counter()

        for q in questions:
            level = q.confidence_level.value if q.confidence_level else None
            if level:
                conf_dist[level] += 1
            meta = q.rag_meta or {}
            cov = meta.get("coverage_score")
            if isinstance(cov, (int, float)):
                coverage_scores.append(float(cov))
                cov_dist[_bucket_coverage(float(cov))] += 1
            qual = meta.get("quality")
            if isinstance(qual, str) and qual in _QUALITY_SCORE:
                quality_scores.append(_QUALITY_SCORE[qual])
            action = meta.get("recommended_action")
            if isinstance(action, str):
                action_dist[action] += 1
            # Prefer full pipeline total when persisted
            total_ms = meta.get("processing_time_ms")
            if isinstance(total_ms, (int, float)):
                processing_times.append(float(total_ms))
            else:
                pt = meta.get("retrieval_ms")
                lt = meta.get("llm_ms")
                emb = meta.get("embedding_ms")
                if any(isinstance(x, (int, float)) for x in (pt, lt, emb)):
                    processing_times.append(
                        float(pt or 0) + float(lt or 0) + float(emb or 0)
                    )
            usage = meta.get("token_usage") or {}
            if isinstance(usage, dict):
                tok = usage.get("total_tokens")
                if isinstance(tok, (int, float)):
                    token_total += int(tok)
                    token_samples += 1
                cost = usage.get("estimated_cost_usd")
                if isinstance(cost, (int, float)):
                    cost_total += float(cost)
                    cost_samples += 1

        fb_total = len(feedback)
        pos = sum(1 for f in feedback if f.feedback_type.value in _POSITIVE)
        neg = sum(1 for f in feedback if f.feedback_type.value in _NEGATIVE)
        rated = pos + neg

        gap_topics: Counter[str] = Counter()
        gap_cats: Counter[str] = Counter()
        for g in gaps:
            topic = g.topic or str(g.category)
            gap_topics[topic] += 1
            gap_cats[str(g.category)] += 1

        top_docs = sorted(
            documents, key=lambda d: d.retrieval_count, reverse=True
        )[:10]
        health = await self._document_repo.health_distribution()

        return AnalyticsDashboard(
            questions_today=questions_today,
            questions_this_week=questions_week,
            knowledge_gaps_total=len(gaps),
            feedback_count=fb_total,
            positive_feedback_pct=_pct(pos, rated),
            negative_feedback_pct=_pct(neg, rated),
            average_confidence=_mean_or_none(conf_scores),
            average_coverage=_mean_or_none(coverage_scores),
            average_quality=_mean_or_none(quality_scores),
            average_processing_time_ms=_mean_or_none(processing_times),
            most_retrieved_documents=[
                NamedCount(
                    key=d.document_id,
                    count=d.retrieval_count,
                    label=d.title,
                )
                for d in top_docs
                if d.retrieval_count > 0
            ],
            top_missing_topics=[
                NamedCount(key=k, count=v, label=k)
                for k, v in gap_topics.most_common(10)
            ],
            knowledge_gaps_by_category=[
                NamedCount(key=k, count=v, label=k)
                for k, v in gap_cats.most_common(20)
            ],
            confidence_distribution=dict(conf_dist),
            coverage_distribution=dict(cov_dist),
            document_health_distribution=health,
            recommended_action_distribution=dict(action_dist),
            recent_knowledge_gaps=sum(
                1 for g in gaps if _is_on_or_after(g.created_at, start_today)
            ),
            total_tokens=token_total if token_samples else None,
            estimated_cost_usd=round(cost_total, 6) if cost_samples else None,
            questions_total=len(questions),
        )

    async def dashboard_summary(self) -> AnalyticsDashboard:
        return await self.get_dashboard()


def _is_on_or_after(
    value: datetime | None, boundary: datetime
) -> bool:
    """Compare only after both sides are known to be aware UTC."""
    if value is None:
        return False
    left = normalize_datetime(value)
    right = normalize_datetime(boundary)
    if left is None or right is None:
        return False
    return left >= right


def _mean_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    return round(mean(values), 2)


def _pct(part: int, whole: int) -> float | None:
    if whole <= 0:
        return None
    return round((part / whole) * 100, 1)


def _bucket_coverage(score: float) -> str:
    if score >= 85:
        return "high"
    if score >= 50:
        return "medium"
    return "low"
