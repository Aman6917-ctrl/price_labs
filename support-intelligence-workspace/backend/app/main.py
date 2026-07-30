"""
FastAPI entrypoint.

Lifespan owns MongoDatabase, EventBus + handler registration, and teardown.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.mongodb import MongoDatabase
from app.events.bus import EventBus
from app.events.handlers import register_handlers
from app.repositories.analytics import AnalyticsRepository
from app.repositories.document import DocumentRepository
from app.routes import analytics as analytics_routes
from app.routes import ask as ask_routes
from app.routes import documents as documents_routes
from app.routes import feedback as feedback_routes
from app.routes import gaps as gaps_routes
from app.routes import ingest as ingest_routes

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    bus = EventBus()
    app.state.event_bus = bus

    db = MongoDatabase(settings)
    try:
        await db.connect()
        await db.ensure_indexes()
        app.state.db = db
        app.state.db_available = True
        register_handlers(
            bus,
            document_repo=DocumentRepository(db),
            analytics_repo=AnalyticsRepository(db),
        )
        logger.info(
            "MongoDB ready; event handlers registered (%d)",
            bus.handler_count(),
        )
    except Exception as exc:
        logger.warning("MongoDB unavailable at startup: %s", exc)
        app.state.db = None
        app.state.db_available = False

    app.state.ask_service = None

    yield

    db_obj: MongoDatabase | None = getattr(app.state, "db", None)
    if db_obj is not None:
        await db_obj.close()


app = FastAPI(
    title=settings.app_name,
    description=(
        "Internal workspace for support engineers: RAG-assisted answers, "
        "citations, knowledge-gap feedback, and analytics — not a customer-facing chatbot.\n\n"
        "See docs/API.md for request/response contracts."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str | bool | int]:
    bus: EventBus | None = getattr(app.state, "event_bus", None)
    return {
        "status": "ok",
        "service": settings.app_name,
        "mongodb": bool(getattr(app.state, "db_available", False)),
        "event_handlers": bus.handler_count() if bus else 0,
    }


app.include_router(ingest_routes.router, prefix=settings.api_prefix)
app.include_router(ask_routes.router, prefix=settings.api_prefix)
app.include_router(gaps_routes.router, prefix=settings.api_prefix)
app.include_router(feedback_routes.router, prefix=settings.api_prefix)
app.include_router(analytics_routes.router, prefix=settings.api_prefix)
app.include_router(documents_routes.router, prefix=settings.api_prefix)
