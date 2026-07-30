"""Shared API schema primitives (not persistence models)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class TimestampSchema(APIModel):
    id: str
    created_at: datetime
    updated_at: datetime
    workspace_id: str | None = None


class MessageResponse(APIModel):
    message: str
    detail: str | None = None


class PaginationParams(APIModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
