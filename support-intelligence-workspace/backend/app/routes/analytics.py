"""GET /api/analytics — dashboard metrics from canonical stores."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_analytics_service
from app.schemas.analytics import AnalyticsDashboard
from app.services.analytics_service import AnalyticsService

router = APIRouter(tags=["analytics"])


@router.get(
    "/analytics",
    response_model=AnalyticsDashboard,
    summary="Dashboard analytics",
    responses={503: {"description": "MongoDB unavailable"}},
)
async def get_analytics(
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsDashboard:
    """
    Structured dashboard DTO.

    Computed from questions, knowledge_gaps, feedback, and documents —
    not from the optional daily rollup cache.
    """
    try:
        return await service.get_dashboard()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
