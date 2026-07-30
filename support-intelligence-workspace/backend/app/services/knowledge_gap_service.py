"""KnowledgeGapService — validation + persistence + domain events."""

from __future__ import annotations

from app.events.bus import EventBus
from app.events.types import KnowledgeGapFlagged
from app.models.knowledge_gap import KnowledgeGapDocument
from app.repositories.knowledge_gap import KnowledgeGapRepository
from app.repositories.question import QuestionRepository
from app.schemas.knowledge_gap import KnowledgeGapCreate, KnowledgeGapResponse


class KnowledgeGapService:
    def __init__(
        self,
        repo: KnowledgeGapRepository,
        question_repo: QuestionRepository | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._repo = repo
        self._question_repo = question_repo
        self._bus = event_bus

    async def flag_gap(self, payload: KnowledgeGapCreate) -> KnowledgeGapResponse:
        if payload.question_id and self._question_repo is not None:
            question = await self._question_repo.get_by_id(payload.question_id)
            if question is None:
                raise ValueError(f"Question not found: {payload.question_id}")

        doc_ids = list(payload.retrieved_document_ids)
        if payload.document_id and payload.document_id not in doc_ids:
            doc_ids.insert(0, payload.document_id)

        entity = KnowledgeGapDocument(
            reason=payload.reason,
            category=payload.category,
            description=payload.description,
            question_id=payload.question_id,
            document_id=payload.document_id or (doc_ids[0] if doc_ids else None),
            retrieved_document_ids=doc_ids,
            session_id=payload.session_id,
            topic=payload.topic,
            workspace_id=payload.workspace_id,
        )
        created = await self._repo.create(entity)
        response = KnowledgeGapResponse.model_validate(created, from_attributes=True)

        if self._bus is not None and created.id:
            await self._bus.publish(
                KnowledgeGapFlagged(
                    gap_id=created.id,
                    reason=created.reason.value
                    if hasattr(created.reason, "value")
                    else str(created.reason),
                    category=str(created.category),
                    topic=created.topic,
                    question_id=created.question_id,
                    document_ids=tuple(doc_ids),
                )
            )
        return response

    async def list_recent(self, *, limit: int = 20) -> list[KnowledgeGapResponse]:
        rows = await self._repo.list(limit=limit)
        return [
            KnowledgeGapResponse.model_validate(r, from_attributes=True) for r in rows
        ]

    async def count_all(self) -> int:
        return await self._repo.count()
