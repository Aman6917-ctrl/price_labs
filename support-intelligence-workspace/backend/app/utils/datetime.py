"""
UTC datetime normalization for safe comparisons.

MongoDB BSON Date has no timezone; Motor/PyMongo typically returns
offset-naive datetimes that represent UTC. Application code often writes
aware UTC via datetime.now(timezone.utc). Comparing the two raises TypeError.
"""

from __future__ import annotations

from datetime import date, datetime, timezone


def normalize_datetime(dt: datetime | date | None) -> datetime | None:
    """
    Normalize to timezone-aware UTC.

    - None → None
    - naive datetime → assume UTC and attach timezone.utc
    - aware datetime → convert to UTC
    - date → midnight UTC on that calendar day
    """
    if dt is None:
        return None

    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    # bare date (not datetime)
    if isinstance(dt, date):
        return datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc)

    raise TypeError(f"Expected datetime | date | None, got {type(dt)!r}")
