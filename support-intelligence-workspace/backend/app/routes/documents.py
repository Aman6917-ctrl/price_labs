"""GET /api/documents — document registry + stats."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_document_service
from app.schemas.document import DocumentResponse, DocumentStatsResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get(
    "/",
    response_model=list[DocumentResponse],
    summary="List documents",
)
async def list_documents(
    limit: int = 50,
    service: DocumentService = Depends(get_document_service),
) -> list[DocumentResponse]:
    return await service.list_documents(limit=min(limit, 200))


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document",
    responses={404: {"description": "Document not found"}},
)
async def get_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    doc = await service.get(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get(
    "/{document_id}/stats",
    response_model=DocumentStatsResponse,
    summary="Document statistics",
    responses={404: {"description": "Document not found"}},
)
async def get_document_stats(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
) -> DocumentStatsResponse:
    stats = await service.get_stats(document_id)
    if stats is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return stats
