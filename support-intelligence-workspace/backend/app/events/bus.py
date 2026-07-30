"""
Lightweight in-process event bus.

MVP: synchronous (awaited) handlers — no broker.
Future: swap `publish` to enqueue Kafka/SQS without changing emitters.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from app.events.types import DomainEvent

logger = logging.getLogger(__name__)

E = TypeVar("E", bound=DomainEvent)
Handler = Callable[[DomainEvent], Awaitable[None]]


class EventBus:
    """
    Pub/sub for domain events.

    Handlers are registered by exact event type. Publish awaits each handler
    in registration order. Handler failures are logged and do not fail the
    publisher (analytics must not break Ask).
    """

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[Handler]] = defaultdict(list)

    def subscribe(self, event_type: type[E], handler: Handler) -> None:
        self._handlers[event_type].append(handler)

    def clear(self) -> None:
        self._handlers.clear()

    async def publish(self, event: DomainEvent) -> None:
        handlers = list(self._handlers.get(type(event), []))
        for handler in handlers:
            try:
                await handler(event)
            except Exception:
                logger.exception(
                    "event_handler_failed event=%s handler=%s",
                    type(event).__name__,
                    getattr(handler, "__name__", repr(handler)),
                )

    def handler_count(self, event_type: type[DomainEvent] | None = None) -> int:
        if event_type is None:
            return sum(len(v) for v in self._handlers.values())
        return len(self._handlers.get(event_type, []))
