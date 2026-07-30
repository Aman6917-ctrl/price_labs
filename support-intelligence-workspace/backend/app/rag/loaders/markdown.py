"""Markdown knowledge-base loader (MVP source type)."""

from __future__ import annotations

from pathlib import Path

from app.models.documents import DocumentMetadata, LoadedDocument
from app.rag.loaders.base import BaseDocumentLoader
from app.rag.loaders.frontmatter import parse_frontmatter


class MarkdownDocumentLoader(BaseDocumentLoader):
    source_type = "markdown"

    def can_load(self, path: Path) -> bool:
        return path.is_file() and path.suffix.lower() in {".md", ".markdown"}

    def load(self, path: Path) -> list[LoadedDocument]:
        text = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)

        if not body.strip():
            raise ValueError(f"Empty markdown body: {path}")

        document_id = str(meta.get("document_id") or path.stem)
        title = str(meta.get("title") or path.stem.replace("-", " ").title())
        category = str(meta.get("category") or "uncategorized")
        last_updated = str(meta.get("last_updated") or "1970-01-01")
        version = str(meta.get("version") or "0.0.0")
        tags = meta.get("tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]

        metadata = DocumentMetadata(
            document_id=document_id,
            title=title,
            category=category,
            source=str(path.resolve()),
            last_updated=last_updated,
            version=version,
            tags=list(tags),
        )
        return [LoadedDocument(content=body, metadata=metadata)]
