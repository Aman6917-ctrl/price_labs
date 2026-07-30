"""KnowledgeGapRepository — CRUD only."""

from __future__ import annotations

from app.models.knowledge_gap import KnowledgeGapDocument
from app.repositories.base import BaseRepository
from app.utils.constants import COLLECTION_KNOWLEDGE_GAPS


class KnowledgeGapRepository(BaseRepository[KnowledgeGapDocument]):
    collection_name = COLLECTION_KNOWLEDGE_GAPS
    model = KnowledgeGapDocument

    async def list_by_category(
        self, category: str, *, limit: int = 50
    ) -> list[KnowledgeGapDocument]:
        return await self.list(filters={"category": category}, limit=limit)

    async def list_by_question(
        self, question_id: str, *, limit: int = 50
    ) -> list[KnowledgeGapDocument]:
        return await self.list(filters={"question_id": question_id}, limit=limit)
