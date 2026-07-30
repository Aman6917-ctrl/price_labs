"""FeedbackRepository — CRUD only."""

from __future__ import annotations

from app.models.feedback import FeedbackDocument
from app.repositories.base import BaseRepository
from app.utils.constants import COLLECTION_FEEDBACK


class FeedbackRepository(BaseRepository[FeedbackDocument]):
    collection_name = COLLECTION_FEEDBACK
    model = FeedbackDocument

    async def list_by_question(
        self, question_id: str, *, limit: int = 50
    ) -> list[FeedbackDocument]:
        return await self.list(filters={"question_id": question_id}, limit=limit)
