"""
Shared repository helpers — CRUD only, no business rules.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from bson import ObjectId
from pymongo import ReturnDocument
from pydantic import BaseModel

from app.database.mongodb import MongoDatabase

T = TypeVar("T", bound=BaseModel)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise ValueError(f"Invalid ObjectId: {value}")
    return ObjectId(value)


def serialize_id(document: dict[str, Any] | None) -> dict[str, Any] | None:
    if document is None:
        return None
    doc = dict(document)
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


class BaseRepository(Generic[T]):
    """
    Generic Motor CRUD.

    Subclasses set `collection_name` and `model` and may add query helpers
    that still remain free of business logic.
    """

    collection_name: str
    model: type[T]

    def __init__(self, db: MongoDatabase) -> None:
        self._db = db

    @property
    def collection(self):
        return self._db.get_collection(self.collection_name)

    def _to_model(self, document: dict[str, Any] | None) -> T | None:
        serialized = serialize_id(document)
        if serialized is None:
            return None
        return self.model.model_validate(serialized)

    def _dump_for_insert(self, entity: T) -> dict[str, Any]:
        data = entity.model_dump(by_alias=True, exclude_none=False)
        # Never persist a client-supplied id on insert
        data.pop("_id", None)
        data.pop("id", None)
        data["created_at"] = data.get("created_at") or utc_now()
        data["updated_at"] = data.get("updated_at") or utc_now()
        return _normalize(data)

    async def create(self, entity: T) -> T:
        payload = self._dump_for_insert(entity)
        result = await self.collection.insert_one(payload)
        created = await self.collection.find_one({"_id": result.inserted_id})
        model = self._to_model(created)
        assert model is not None
        return model

    async def get_by_id(self, entity_id: str) -> T | None:
        doc = await self.collection.find_one({"_id": to_object_id(entity_id)})
        return self._to_model(doc)

    async def update(self, entity_id: str, fields: dict[str, Any]) -> T | None:
        updates = _normalize({k: v for k, v in fields.items() if v is not None})
        updates["updated_at"] = utc_now()
        doc = await self.collection.find_one_and_update(
            {"_id": to_object_id(entity_id)},
            {"$set": updates},
            return_document=ReturnDocument.AFTER,
        )
        return self._to_model(doc)

    async def delete(self, entity_id: str) -> bool:
        result = await self.collection.delete_one({"_id": to_object_id(entity_id)})
        return result.deleted_count == 1

    async def list(
        self,
        *,
        filters: dict[str, Any] | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: list[tuple[str, int]] | None = None,
    ) -> list[T]:
        query = filters or {}
        cursor = self.collection.find(query)
        if sort:
            cursor = cursor.sort(sort)
        else:
            cursor = cursor.sort([("created_at", -1)])
        cursor = cursor.skip(offset).limit(limit)
        raw = await cursor.to_list(length=limit)
        return [m for m in (self._to_model(d) for d in raw) if m]

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        return await self.collection.count_documents(filters or {})


def _normalize(data: Any) -> Any:
    """Recursively convert enums / dates for Motor."""
    if isinstance(data, dict):
        return {k: _normalize(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_normalize(v) for v in data]
    if hasattr(data, "value") and hasattr(data, "name"):
        return data.value
    if hasattr(data, "isoformat") and not isinstance(data, str):
        from datetime import date, datetime

        if isinstance(data, datetime):
            return data
        if isinstance(data, date):
            return data.isoformat()
    return data
