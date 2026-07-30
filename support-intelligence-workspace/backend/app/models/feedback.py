"""Persistence model: engineer feedback on suggested answers."""

from __future__ import annotations

from app.models.base import MongoBaseModel
from app.models.enums import FeedbackType


class FeedbackDocument(MongoBaseModel):
    """
    Feedback tied to a persisted question.

    Used for Average Response Quality and regenerate/edit analytics.
    """

    question_id: str
    feedback_type: FeedbackType
    comment: str | None = None
    rating: int | None = None  # optional 1–5 when UI collects it
    edited_response: str | None = None
