"""
Frontmatter helpers for markdown knowledge-base files.

Format:
---
document_id: api-guide
title: API Guide
category: API
last_updated: 2026-06-15
version: 2.1.0
tags: [api, rest, endpoints]
---

Body content...
"""

from __future__ import annotations

import re
from typing import Any


_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split YAML-like frontmatter from body. Returns ({}, full text) if absent."""
    match = _FRONTMATTER_RE.match(text.strip())
    if not match:
        return {}, text

    raw_meta, body = match.group(1), match.group(2)
    meta: dict[str, Any] = {}

    for line in raw_meta.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        meta[key] = _parse_value(value)

    return meta, body.strip()


def _parse_value(value: str) -> Any:
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("'\"") for item in inner.split(",") if item.strip()]
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value
