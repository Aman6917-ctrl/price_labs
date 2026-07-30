"""POST /api/feedback — thumbs up/down on suggested answers."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_feedback_service
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services.feedback_service import FeedbackService

router = APIRouter(tags=["feedback"])


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Submit answer feedback",
    responses={
        400: {"description": "Unknown question_id or invalid payload"},
        503: {"description": "MongoDB unavailable"},
    },
)
async def submit_feedback(
    body: FeedbackCreate,
    service: FeedbackService = Depends(get_feedback_service),
) -> FeedbackResponse:
    """
    Thumbs up / thumbs down (plus optional comment) for a persisted question.

    Emits `FeedbackSubmitted` for analytics + document stats.
    """
    try:
        return await service.submit(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
