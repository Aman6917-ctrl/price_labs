"""
MongoDB database service — injectable, not a global singleton import.

Repositories receive MongoDatabase via constructor / FastAPI Depends.
"""

from __future__ import annotations

import logging
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase

from app.config import Settings
from app.database.indexes import INDEX_PLAN

logger = logging.getLogger(__name__)


class MongoDatabase:
    """
    Thin wrapper around Motor.

    Lifecycle is owned by the FastAPI lifespan (connect → ensure_indexes → close).
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: AsyncIOMotorClient | None = None
        self._db: AsyncIOMotorDatabase | None = None

    @property
    def client(self) -> AsyncIOMotorClient:
        if self._client is None:
            raise RuntimeError("MongoDatabase is not connected. Call connect() first.")
        return self._client

    @property
    def db(self) -> AsyncIOMotorDatabase:
        if self._db is None:
            raise RuntimeError("MongoDatabase is not connected. Call connect() first.")
        return self._db

    async def connect(self) -> None:
        self._client = AsyncIOMotorClient(self._settings.mongodb_uri)
        self._db = self._client[self._settings.mongodb_db]
        # Fail fast if Mongo is unreachable
        await self._client.admin.command("ping")
        logger.info(
            "Connected to MongoDB db=%s",
            self._settings.mongodb_db,
        )

    async def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed")

    def get_collection(self, name: str) -> AsyncIOMotorCollection:
        return self.db[name]

    async def ping(self) -> bool:
        try:
            await self.client.admin.command("ping")
            return True
        except Exception:
            return False

    async def ensure_indexes(self) -> None:
        """Create indexes defined in INDEX_PLAN (idempotent)."""
        for plan in INDEX_PLAN:
            collection = self.get_collection(plan.collection)
            for spec in plan.indexes:
                kwargs: dict[str, Any] = {}
                if spec.name:
                    kwargs["name"] = spec.name
                if spec.unique:
                    kwargs["unique"] = True
                if spec.sparse:
                    kwargs["sparse"] = True
                await collection.create_index(spec.keys, **kwargs)
                logger.debug(
                    "Ensured index %s on %s",
                    spec.name or spec.keys,
                    plan.collection,
                )
