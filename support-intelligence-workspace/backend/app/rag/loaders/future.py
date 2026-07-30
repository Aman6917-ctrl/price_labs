"""
Future loader stubs.

Registered in the registry map for discoverability, but not enabled
until their dependencies and sync adapters ship. Adding a real
implementation only requires replacing the stub class — IngestionService
and RAG retrieval stay unchanged.
"""

from __future__ import annotations

from pathlib import Path

from app.models.documents import LoadedDocument
from app.rag.loaders.base import BaseDocumentLoader


class _FutureLoader(BaseDocumentLoader):
    """Base for loaders that are intentionally not implemented in MVP."""

    source_type = "future"

    def can_load(self, path: Path) -> bool:
        # Never auto-selected during directory walks in MVP
        return False

    def load(self, path: Path) -> list[LoadedDocument]:
        raise NotImplementedError(
            f"{self.source_type} loader is reserved for future scope. "
            f"Implement BaseDocumentLoader and register it to enable: {path}"
        )


class PDFDocumentLoader(_FutureLoader):
    source_type = "pdf"


class HTMLDocumentLoader(_FutureLoader):
    source_type = "html"


class ConfluenceDocumentLoader(_FutureLoader):
    source_type = "confluence"


class NotionDocumentLoader(_FutureLoader):
    source_type = "notion"


class GitHubDocsLoader(_FutureLoader):
    source_type = "github_docs"
