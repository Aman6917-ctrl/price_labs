"""POST /api/flag-gap — knowledge gap reports."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_knowledge_gap_service
from app.schemas.knowledge_gap import KnowledgeGapCreate, KnowledgeGapResponse
from app.services.knowledge_gap_service import KnowledgeGapService

router = APIRouter(tags=["knowledge-gaps"])


@router.post(
    "/flag-gap",
    response_model=KnowledgeGapResponse,
    summary="Flag a knowledge gap",
    responses={
        400: {"description": "Invalid payload or unknown question_id"},
        503: {"description": "MongoDB unavailable"},
    },
)
async def flag_gap(
    body: KnowledgeGapCreate,
    service: KnowledgeGapService = Depends(get_knowledge_gap_service),
) -> KnowledgeGapResponse:
    """
    Support engineer reports missing / outdated / incorrect / confusing docs.

    Emits `KnowledgeGapFlagged` for analytics + document stats handlers.
    """
    try:
        return await service.flag_gap(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get(
    "/gaps",
    response_model=list[KnowledgeGapResponse],
    summary="List recent knowledge gaps",
)
async def list_gaps(
    limit: int = 20,
    service: KnowledgeGapService = Depends(get_knowledge_gap_service),
) -> list[KnowledgeGapResponse]:
    return await service.list_recent(limit=min(limit, 100))
