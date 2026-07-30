"""POST /api/ask — thin HTTP adapter over AskService."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_ask_service
from app.rag.exceptions import AskError
from app.schemas.ask import AskRequest, AskResponse
from app.services.ask_service import AskService

router = APIRouter(prefix="/ask", tags=["ask"])


@router.post("/", response_model=AskResponse)
async def ask_question(
    body: AskRequest,
    service: AskService = Depends(get_ask_service),
) -> AskResponse:
    """
    Produce a suggested answer for a support engineer.

    Not a customer chatbot — returns confidence, coverage, citations,
    document health, and explainability for human review.
    """
    try:
        return await service.ask(body)
    except AskError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": exc.message},
        ) from exc
