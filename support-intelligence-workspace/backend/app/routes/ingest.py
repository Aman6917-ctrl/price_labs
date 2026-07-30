"""Ingestion HTTP adapter — thin wrapper over IngestionService."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.documents import IngestionResult
from app.rag.ingestion import IngestionService

router = APIRouter(prefix="/ingest", tags=["ingestion"])


class IngestRequest(BaseModel):
    dry_run: bool = Field(
        default=False,
        description="If true, load and chunk only — skip embeddings and Chroma writes.",
    )
    replace: bool = Field(
        default=True,
        description="If true, rebuild the collection before writing (idempotent MVP).",
    )


@router.post("/", response_model=IngestionResult)
async def ingest_documents(body: IngestRequest | None = None) -> IngestionResult:
    """
    Trigger the same ingestion pipeline used by `scripts/ingest_docs.py`.

    No duplicate logic — both call IngestionService.ingest().
    """
    request = body or IngestRequest()
    service = IngestionService()
    try:
        return service.ingest(dry_run=request.dry_run, replace=request.replace)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - surface unexpected failures clearly
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc
