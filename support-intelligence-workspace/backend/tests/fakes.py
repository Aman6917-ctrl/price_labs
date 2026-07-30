"""In-memory fakes for unit tests — no Mongo required."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.analytics import AnalyticsDocument
from app.models.document_record import DocumentRecord
from app.models.feedback import FeedbackDocument
from app.models.knowledge_gap import KnowledgeGapDocument
from app.models.question import QuestionDocument


def _now() -> datetime:
    return datetime.now(timezone.utc)


class InMemoryRepo:
    def __init__(self) -> None:
        self.items: dict[str, Any] = {}

    async def create(self, entity: Any) -> Any:
        eid = uuid4().hex[:24]
        data = entity.model_copy(update={"id": eid, "created_at": _now(), "updated_at": _now()})
        self.items[eid] = data
        return data

    async def get_by_id(self, entity_id: str) -> Any | None:
        return self.items.get(entity_id)

    async def update(self, entity_id: str, fields: dict[str, Any]) -> Any | None:
        current = self.items.get(entity_id)
        if not current:
            return None
        updated = current.model_copy(update={**fields, "updated_at": _now()})
        self.items[entity_id] = updated
        return updated

    async def list(self, *, filters=None, limit=50, offset=0, sort=None):
        rows = list(self.items.values())
        return rows[offset : offset + limit]

    async def count(self, filters=None) -> int:
        return len(self.items)


class FakeQuestionRepo(InMemoryRepo):
    model = QuestionDocument

    async def list_by_session(self, session_id: str, *, limit: int = 50):
        return [q for q in self.items.values() if q.session_id == session_id][:limit]


class FakeGapRepo(InMemoryRepo):
    pass


class FakeFeedbackRepo(InMemoryRepo):
    async def list_by_question(self, question_id: str, *, limit: int = 50):
        return [f for f in self.items.values() if f.question_id == question_id][:limit]


class FakeDocumentRepo(InMemoryRepo):
    async def get_by_document_id(self, document_id: str) -> DocumentRecord | None:
        for doc in self.items.values():
            if doc.document_id == document_id:
                return doc
        return None

    async def upsert_by_document_id(self, entity: DocumentRecord) -> DocumentRecord:
        existing = await self.get_by_document_id(entity.document_id)
        if existing and existing.id:
            updated = existing.model_copy(
                update={
                    **entity.model_dump(exclude={"id", "created_at"}),
                    "updated_at": _now(),
                }
            )
            self.items[existing.id] = updated
            return updated
        return await self.create(entity)

    async def health_distribution(self) -> dict[str, int]:
        dist: dict[str, int] = {}
        for doc in self.items.values():
            key = doc.health.value if hasattr(doc.health, "value") else str(doc.health)
            dist[key] = dist.get(key, 0) + 1
        return dist

    async def list_most_retrieved(self, *, limit: int = 10):
        rows = sorted(
            self.items.values(), key=lambda d: d.retrieval_count, reverse=True
        )
        return rows[:limit]


class FakeAnalyticsRepo(InMemoryRepo):
    async def get_by_date(self, day):
        key = day.isoformat() if hasattr(day, "isoformat") else str(day)
        for row in self.items.values():
            d = row.date.isoformat() if hasattr(row.date, "isoformat") else str(row.date)
            if d == key:
                return row
        return None

    async def upsert_by_date(self, entity: AnalyticsDocument) -> AnalyticsDocument:
        existing = await self.get_by_date(entity.date)
        if existing and existing.id:
            updated = existing.model_copy(
                update={
                    **entity.model_dump(exclude={"id", "created_at"}),
                    "updated_at": _now(),
                }
            )
            self.items[existing.id] = updated
            return updated
        return await self.create(entity)
