"""QuestionService — business rules around question persistence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.config import Settings, get_settings
from app.models.enums import ConfidenceLevel
from app.models.question import QuestionDocument, SourceCitation
from app.repositories.question import QuestionRepository
from app.schemas.question import QuestionCreate, QuestionResponse, QuestionUpdate


class QuestionService:
    def __init__(
        self,
        repo: QuestionRepository,
        settings: Settings | None = None,
    ) -> None:
        self._repo = repo
        self._settings = settings or get_settings()

    def resolve_confidence_level(self, score: float | None) -> ConfidenceLevel | None:
        if score is None:
            return None
        if score >= self._settings.confidence_high:
            return ConfidenceLevel.HIGH
        if score >= self._settings.confidence_medium:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW

    async def create_question(self, payload: QuestionCreate) -> QuestionResponse:
        level = payload.confidence_level or self.resolve_confidence_level(
            payload.confidence_score
        )
        entity = QuestionDocument(
            session_id=payload.session_id,
            question_text=payload.question_text,
            suggested_response=payload.suggested_response,
            confidence_score=payload.confidence_score,
            confidence_level=level,
            source_document_ids=payload.source_document_ids,
            citations=[SourceCitation(**c.model_dump()) for c in payload.citations],
            rag_meta=payload.rag_meta,
            workspace_id=payload.workspace_id,
        )
        created = await self._repo.create(entity)
        return QuestionResponse.model_validate(created, from_attributes=True)

    async def get_question(self, question_id: str) -> QuestionResponse | None:
        doc = await self._repo.get_by_id(question_id)
        if not doc:
            return None
        return QuestionResponse.model_validate(doc, from_attributes=True)

    async def update_question(
        self, question_id: str, payload: QuestionUpdate
    ) -> QuestionResponse | None:
        fields = payload.model_dump(exclude_unset=True)
        if "confidence_score" in fields and "confidence_level" not in fields:
            fields["confidence_level"] = self.resolve_confidence_level(
                fields.get("confidence_score")
            )
        updated = await self._repo.update(question_id, fields)
        if not updated:
            return None
        return QuestionResponse.model_validate(updated, from_attributes=True)

    async def list_session(self, session_id: str) -> list[QuestionResponse]:
        rows = await self._repo.list_by_session(session_id)
        return [QuestionResponse.model_validate(r, from_attributes=True) for r in rows]

    async def count_today(self) -> int:
        start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return await self._repo.count({"created_at": {"$gte": start}})

    async def list_recent(self, *, limit: int = 20) -> list[QuestionResponse]:
        since = datetime.now(timezone.utc) - timedelta(days=7)
        rows = await self._repo.list_since(since, limit=limit)
        return [QuestionResponse.model_validate(r, from_attributes=True) for r in rows]
