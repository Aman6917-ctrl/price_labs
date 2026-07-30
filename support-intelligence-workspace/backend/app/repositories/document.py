"""DocumentRepository — CRUD only for the Mongo document registry."""

from __future__ import annotations

from typing import Any

from app.models.document_record import DocumentRecord
from app.repositories.base import BaseRepository, utc_now
from app.utils.constants import COLLECTION_DOCUMENTS


class DocumentRepository(BaseRepository[DocumentRecord]):
    collection_name = COLLECTION_DOCUMENTS
    model = DocumentRecord

    async def get_by_document_id(self, document_id: str) -> DocumentRecord | None:
        doc = await self.collection.find_one({"document_id": document_id})
        return self._to_model(doc)

    async def upsert_by_document_id(self, entity: DocumentRecord) -> DocumentRecord:
        """Insert or replace registry row keyed by document_id (not Mongo _id)."""
        payload = self._dump_for_insert(entity)
        now = utc_now()
        existing = await self.collection.find_one({"document_id": entity.document_id})
        if existing:
            payload["created_at"] = existing.get("created_at", now)
            payload["updated_at"] = now
            # Preserve retrieval_count unless caller set a non-zero value intentionally
            if entity.retrieval_count == 0 and "retrieval_count" in existing:
                payload["retrieval_count"] = existing["retrieval_count"]
            await self.collection.update_one(
                {"document_id": entity.document_id},
                {"$set": payload},
            )
        else:
            payload["created_at"] = now
            payload["updated_at"] = now
            await self.collection.insert_one(payload)
        return await self.get_by_document_id(entity.document_id)  # type: ignore[return-value]

    async def increment_retrieval_count(self, document_id: str, by: int = 1) -> None:
        await self.collection.update_one(
            {"document_id": document_id},
            {"$inc": {"retrieval_count": by}, "$set": {"updated_at": utc_now()}},
        )

    async def list_most_retrieved(self, *, limit: int = 10) -> list[DocumentRecord]:
        cursor = (
            self.collection.find({})
            .sort([("retrieval_count", -1)])
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [m for m in (self._to_model(d) for d in docs) if m]

    async def health_distribution(self) -> dict[str, int]:
        pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$health", "count": {"$sum": 1}}},
        ]
        rows = await self.collection.aggregate(pipeline).to_list(length=20)
        return {str(r["_id"]): int(r["count"]) for r in rows}
