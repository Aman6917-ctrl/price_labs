#!/usr/bin/env python3
"""
CLI entrypoint for document ingestion.

    cd backend
    source .venv/bin/activate
    python ../scripts/ingest_docs.py
    python ../scripts/ingest_docs.py --dry-run

Calls the same IngestionService as POST /api/ingest.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow `python ../scripts/ingest_docs.py` from backend/ or repo root
BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.rag.ingestion import IngestionService  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest knowledge-base docs into ChromaDB via IngestionService."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load and chunk only; skip embeddings and vector store writes.",
    )
    parser.add_argument(
        "--no-replace",
        action="store_true",
        help="Append to existing collection instead of rebuilding.",
    )
    args = parser.parse_args()

    service = IngestionService()
    result = service.ingest(dry_run=args.dry_run, replace=not args.no_replace)
    print(json.dumps(result.model_dump(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
