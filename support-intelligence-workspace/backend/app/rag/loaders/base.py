"""
Document loader contract.

New source types (PDF, HTML, Confluence, Notion, GitHub Docs) plug in by:
1. Implementing BaseDocumentLoader
2. Registering with LoaderRegistry

The IngestionService and RAG retrieve path never change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.models.documents import LoadedDocument


class BaseDocumentLoader(ABC):
    """Abstract loader for a single source type."""

    #: Stable identifier used in registry + future sync configs
    source_type: str

    @abstractmethod
    def can_load(self, path: Path) -> bool:
        """Return True if this loader handles the given path/URI."""

    @abstractmethod
    def load(self, path: Path) -> list[LoadedDocument]:
        """
        Load one or more documents from a path.

        Directory loaders may return many documents;
        file loaders typically return one.
        """


class LoaderNotFoundError(LookupError):
    """Raised when no registered loader can handle a path."""
