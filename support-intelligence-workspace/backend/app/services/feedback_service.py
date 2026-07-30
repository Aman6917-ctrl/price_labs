"""FeedbackService — thumbs up/down + domain events."""

from __future__ import annotations

from app.events.bus import EventBus
from app.events.types import FeedbackSubmitted
from app.models.enums import FeedbackType
from app.models.feedback import FeedbackDocument
from app.repositories.feedback import FeedbackRepository
from app.repositories.question import QuestionRepository
from app.schemas.feedback import FeedbackCreate, FeedbackResponse

_POSITIVE = {FeedbackType.THUMBS_UP, FeedbackType.POSITIVE}
_NEGATIVE = {FeedbackType.THUMBS_DOWN, FeedbackType.NEGATIVE}


class FeedbackService:
    def __init__(
        self,
        repo: FeedbackRepository,
        question_repo: QuestionRepository,
        event_bus: EventBus | None = None,
    ) -> None:
        self._repo = repo
        self._question_repo = question_repo
        self._bus = event_bus

    async def submit(self, payload: FeedbackCreate) -> FeedbackResponse:
        question = await self._question_repo.get_by_id(payload.question_id)
        if question is None:
            raise ValueError(f"Question not found: {payload.question_id}")

        entity = FeedbackDocument(
            question_id=payload.question_id,
            feedback_type=payload.feedback_type,
            comment=payload.comment,
            rating=payload.rating,
            edited_response=payload.edited_response,
            workspace_id=payload.workspace_id,
        )
        created = await self._repo.create(entity)

        if payload.edited_response:
            await self._question_repo.update(
                payload.question_id,
                {"edited_response": payload.edited_response},
            )

        response = FeedbackResponse.model_validate(created, from_attributes=True)

        if self._bus is not None and created.id:
            doc_ids = tuple(question.source_document_ids or [])
            await self._bus.publish(
                FeedbackSubmitted(
                    feedback_id=created.id,
                    question_id=payload.question_id,
                    feedback_type=payload.feedback_type.value,
                    document_ids=doc_ids,
                )
            )
        return response

    async def list_for_question(self, question_id: str) -> list[FeedbackResponse]:
        rows = await self._repo.list_by_question(question_id)
        return [FeedbackResponse.model_validate(r, from_attributes=True) for r in rows]

    @staticmethod
    def is_positive(feedback_type: FeedbackType) -> bool:
        return feedback_type in _POSITIVE

    @staticmethod
    def is_negative(feedback_type: FeedbackType) -> bool:
        return feedback_type in _NEGATIVE
