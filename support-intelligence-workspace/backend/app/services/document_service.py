"""DocumentService — registry of knowledge-base documents in Mongo."""

from __future__ import annotations

from app.events.bus import EventBus
from app.events.types import DocumentIngested
from app.models.document_record import DocumentRecord
from app.models.enums import DocumentHealth
from app.repositories.document import DocumentRepository
from app.schemas.document import (
    DocumentResponse,
    DocumentStatsResponse,
    DocumentUpsert,
)


class DocumentService:
    def __init__(
        self,
        repo: DocumentRepository,
        event_bus: EventBus | None = None,
    ) -> None:
        self._repo = repo
        self._bus = event_bus

    async def upsert(self, payload: DocumentUpsert) -> DocumentResponse:
        entity = DocumentRecord(
            document_id=payload.document_id,
            title=payload.title,
            category=payload.category,
            source=payload.source,
            version=payload.version,
            tags=payload.tags,
            last_updated=payload.last_updated,
            health=payload.health,
            chunk_count=payload.chunk_count,
            workspace_id=payload.workspace_id,
        )
        saved = await self._repo.upsert_by_document_id(entity)
        response = DocumentResponse.model_validate(saved, from_attributes=True)

        if self._bus is not None:
            await self._bus.publish(
                DocumentIngested(
                    document_id=payload.document_id,
                    title=payload.title,
                    category=str(payload.category),
                    version=payload.version,
                    chunk_count=payload.chunk_count,
                    source=payload.source,
                    tags=tuple(payload.tags),
                    last_updated=str(payload.last_updated)
                    if payload.last_updated
                    else None,
                )
            )
        return response

    async def get(self, document_id: str) -> DocumentResponse | None:
        doc = await self._repo.get_by_document_id(document_id)
        if not doc:
            return None
        return DocumentResponse.model_validate(doc, from_attributes=True)

    async def get_stats(self, document_id: str) -> DocumentStatsResponse | None:
        doc = await self._repo.get_by_document_id(document_id)
        if not doc:
            return None
        return DocumentStatsResponse(
            document_id=doc.document_id,
            title=doc.title,
            health=doc.health,
            retrieval_count=doc.retrieval_count,
            knowledge_gap_count=doc.knowledge_gap_count,
            feedback_count=doc.feedback_count,
            average_confidence=doc.average_confidence,
            average_coverage=doc.average_coverage,
            average_quality=doc.average_quality,
            last_retrieved=doc.last_retrieved,
        )

    async def list_documents(self, *, limit: int = 50) -> list[DocumentResponse]:
        rows = await self._repo.list(limit=limit, sort=[("title", 1)])
        return [DocumentResponse.model_validate(r, from_attributes=True) for r in rows]

    async def health_distribution(self) -> dict[str, int]:
        return await self._repo.health_distribution()

    async def set_health(
        self, document_id: str, health: DocumentHealth
    ) -> DocumentResponse | None:
        existing = await self._repo.get_by_document_id(document_id)
        if not existing or not existing.id:
            return None
        updated = await self._repo.update(existing.id, {"health": health})
        if not updated:
            return None
        return DocumentResponse.model_validate(updated, from_attributes=True)
