"""API schemas for feedback."""

from __future__ import annotations

from pydantic import Field

from app.models.enums import FeedbackType
from app.schemas.common import APIModel, TimestampSchema


class FeedbackCreate(APIModel):
    question_id: str
    feedback_type: FeedbackType = Field(
        ...,
        description="Use thumbs_up / thumbs_down for primary UX.",
    )
    comment: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    edited_response: str | None = None
    workspace_id: str | None = None


class FeedbackResponse(TimestampSchema):
    question_id: str
    feedback_type: FeedbackType
    comment: str | None = None
    rating: int | None = None
    edited_response: str | None = None
