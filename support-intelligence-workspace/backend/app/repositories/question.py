"""QuestionRepository — CRUD only."""

from __future__ import annotations

from datetime import datetime

from app.models.question import QuestionDocument
from app.repositories.base import BaseRepository
from app.utils.constants import COLLECTION_QUESTIONS


class QuestionRepository(BaseRepository[QuestionDocument]):
    collection_name = COLLECTION_QUESTIONS
    model = QuestionDocument

    async def list_by_session(self, session_id: str, *, limit: int = 50) -> list[QuestionDocument]:
        return await self.list(filters={"session_id": session_id}, limit=limit)

    async def list_since(
        self, since: datetime, *, limit: int = 100
    ) -> list[QuestionDocument]:
        return await self.list(
            filters={"created_at": {"$gte": since}},
            limit=limit,
            sort=[("created_at", -1)],
        )
