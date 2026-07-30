"""Unit tests for UTC datetime normalization."""

from __future__ import annotations

from datetime import date, datetime, timezone, timedelta

from app.utils.datetime import normalize_datetime


def test_normalize_none():
    assert normalize_datetime(None) is None


def test_normalize_naive_assumes_utc():
    naive = datetime(2026, 7, 30, 12, 0, 0)
    result = normalize_datetime(naive)
    assert result is not None
    assert result.tzinfo is not None
    assert result.utcoffset() == timedelta(0)
    assert result.hour == 12


def test_normalize_aware_converts_to_utc():
    # Fixed offset +05:30
    aware = datetime(2026, 7, 30, 17, 30, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    result = normalize_datetime(aware)
    assert result is not None
    assert result == datetime(2026, 7, 30, 12, 0, tzinfo=timezone.utc)


def test_normalize_date_to_midnight_utc():
    result = normalize_datetime(date(2026, 7, 30))
    assert result == datetime(2026, 7, 30, 0, 0, tzinfo=timezone.utc)


def test_naive_vs_aware_boundary_comparable():
    start_today = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    # Simulates Mongo returning naive UTC
    mongo_created = datetime(2026, 7, 30, 8, 0, 0)
    left = normalize_datetime(mongo_created)
    right = normalize_datetime(start_today)
    assert left is not None and right is not None
    # Must not raise
    _ = left >= right
