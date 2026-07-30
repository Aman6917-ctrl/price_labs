"""AnalyticsRepository — CRUD only for daily aggregates."""

from __future__ import annotations

from datetime import date

from app.models.analytics import AnalyticsDocument
from app.repositories.base import BaseRepository, utc_now
from app.utils.constants import COLLECTION_ANALYTICS


class AnalyticsRepository(BaseRepository[AnalyticsDocument]):
    collection_name = COLLECTION_ANALYTICS
    model = AnalyticsDocument

    async def get_by_date(self, day: date) -> AnalyticsDocument | None:
        doc = await self.collection.find_one({"date": day.isoformat()})
        return self._to_model(doc)

    async def upsert_by_date(self, entity: AnalyticsDocument) -> AnalyticsDocument:
        payload = self._dump_for_insert(entity)
        payload["date"] = (
            entity.date.isoformat()
            if hasattr(entity.date, "isoformat")
            else str(entity.date)
        )
        now = utc_now()
        existing = await self.collection.find_one({"date": payload["date"]})
        if existing:
            payload["created_at"] = existing.get("created_at", now)
            payload["updated_at"] = now
            await self.collection.update_one({"date": payload["date"]}, {"$set": payload})
        else:
            payload["created_at"] = now
            payload["updated_at"] = now
            await self.collection.insert_one(payload)
        return await self.get_by_date(entity.date)  # type: ignore[return-value]

    async def list_recent(self, *, limit: int = 30) -> list[AnalyticsDocument]:
        return await self.list(limit=limit, sort=[("date", -1)])
