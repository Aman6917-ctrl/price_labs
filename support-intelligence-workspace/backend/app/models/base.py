"""
Persistence base model.

Every MongoDB document inherits these fields so Auth / RBAC / multi-workspace /
audit can layer on later without reshaping collections.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MongoBaseModel(BaseModel):
    """
    Common persistence fields.

    - id: string form of MongoDB ObjectId (set after insert)
    - created_at / updated_at: always UTC
    - workspace_id: reserved for multi-workspace (null = default workspace in MVP)
    - created_by / updated_by: reserved for auth + audit logs
    """

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        extra="ignore",
    )

    id: str | None = Field(default=None, alias="_id")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # --- Future scalability (unused in MVP logic, stored when provided) ---
    workspace_id: str | None = None
    created_by: str | None = None
    updated_by: str | None = None

    def touch(self) -> None:
        """Bump updated_at to now (UTC)."""
        self.updated_at = utc_now()
