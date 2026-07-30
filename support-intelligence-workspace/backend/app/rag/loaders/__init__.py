"""
Loader registry — single place to plug new source types.

Usage:
    registry = build_default_registry()
    loader = registry.resolve(path)
    docs = loader.load(path)
"""

from __future__ import annotations

from pathlib import Path

from app.rag.loaders.base import BaseDocumentLoader, LoaderNotFoundError
from app.rag.loaders.future import (
    ConfluenceDocumentLoader,
    GitHubDocsLoader,
    HTMLDocumentLoader,
    NotionDocumentLoader,
    PDFDocumentLoader,
)
from app.rag.loaders.markdown import MarkdownDocumentLoader


class LoaderRegistry:
    def __init__(self) -> None:
        self._loaders: list[BaseDocumentLoader] = []

    def register(self, loader: BaseDocumentLoader) -> None:
        self._loaders.append(loader)

    def resolve(self, path: Path) -> BaseDocumentLoader:
        for loader in self._loaders:
            if loader.can_load(path):
                return loader
        raise LoaderNotFoundError(f"No loader registered for: {path}")

    def supported_source_types(self) -> list[str]:
        return [loader.source_type for loader in self._loaders]


def build_default_registry() -> LoaderRegistry:
    """
    MVP: Markdown is active.
    Future types are registered for extension visibility but never match can_load.
    """
    registry = LoaderRegistry()
    registry.register(MarkdownDocumentLoader())
    # Extension points — implement load()/can_load() when ready
    registry.register(PDFDocumentLoader())
    registry.register(HTMLDocumentLoader())
    registry.register(ConfluenceDocumentLoader())
    registry.register(NotionDocumentLoader())
    registry.register(GitHubDocsLoader())
    return registry
