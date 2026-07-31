"""
IngestionService — single orchestrator for CLI and HTTP.

Flow:
  discover sources
      → Document Loader (registry)
      → Chunking
      → Embedding Generator
      → Vector Store

No duplicate logic between scripts/ingest_docs.py and POST /api/ingest.
"""

from __future__ import annotations

from pathlib import Path

from app.config import Settings, get_settings
from app.models.documents import IngestionResult, LoadedDocument
from app.rag.chunking import DocumentChunker
from app.rag.embeddings import EmbeddingGenerator
from app.rag.loaders import LoaderRegistry, build_default_registry
from app.rag.loaders.base import LoaderNotFoundError
from app.rag.vectorstore import VectorStoreService


class IngestionService:
    def __init__(
        self,
        settings: Settings | None = None,
        registry: LoaderRegistry | None = None,
        chunker: DocumentChunker | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.registry = registry or build_default_registry()
        self.chunker = chunker or DocumentChunker(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )

    @property
    def docs_path(self) -> Path:
        return _resolve_docs_path(self.settings.docs_path)

    @property
    def chroma_path(self) -> Path:
        return _resolve_from_backend(self.settings.chroma_persist_dir)

    def discover_files(self, root: Path | None = None) -> list[Path]:
        """Find ingestible files under docs_path (recursive)."""
        base = root or self.docs_path
        if not base.exists():
            raise FileNotFoundError(f"Docs path not found: {base}")

        files: list[Path] = []
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            if path.name.lower() == "readme.md":
                continue
            try:
                self.registry.resolve(path)
            except LoaderNotFoundError:
                continue
            files.append(path)
        return files

    def load_documents(self, paths: list[Path] | None = None) -> list[LoadedDocument]:
        files = paths if paths is not None else self.discover_files()
        documents: list[LoadedDocument] = []
        for path in files:
            loader = self.registry.resolve(path)
            documents.extend(loader.load(path))
        return documents

    def ingest(
        self,
        *,
        dry_run: bool = False,
        replace: bool = True,
        paths: list[Path] | None = None,
    ) -> IngestionResult:
        """
        Run the full pipeline.

        dry_run=True  → load + chunk only (no embeddings / Chroma writes)
        replace=True  → rebuild collection (default for MVP re-ingest)
        """
        documents = self.load_documents(paths)
        chunks = self.chunker.chunk_many(documents)
        document_ids = [doc.metadata.document_id for doc in documents]

        if dry_run:
            return IngestionResult(
                documents_loaded=len(documents),
                chunks_created=len(chunks),
                collection=self.settings.chroma_collection,
                dry_run=True,
                document_ids=document_ids,
                message="Dry run complete — embeddings and vector store skipped.",
            )

        embedder = EmbeddingGenerator(self.settings)
        vectorstore = VectorStoreService(
            persist_directory=self.chroma_path,
            collection_name=self.settings.chroma_collection,
            embeddings=embedder.client,
        )
        stored = vectorstore.upsert_chunks(chunks, replace=replace)

        return IngestionResult(
            documents_loaded=len(documents),
            chunks_created=stored,
            collection=self.settings.chroma_collection,
            dry_run=False,
            document_ids=document_ids,
            message=f"Ingested {stored} chunks from {len(documents)} documents.",
        )


def _resolve_from_backend(relative_or_absolute: str) -> Path:
    """Resolve paths relative to the backend/ package root."""
    path = Path(relative_or_absolute)
    if path.is_absolute():
        return path
    backend_root = Path(__file__).resolve().parents[2]  # .../backend
    return (backend_root / path).resolve()


def _resolve_docs_path(configured: str) -> Path:
    """
    Resolve knowledge-base docs for local + Railway layouts.

    Tries configured path first, then backend/docs and ../docs.
    Absolute bad env values (e.g. DOCS_PATH=/docs) fall through to bundled docs.
    """
    candidates = [configured, "docs", "../docs"]
    seen: set[Path] = set()
    for raw in candidates:
        if not raw:
            continue
        path = _resolve_from_backend(raw) if not Path(raw).is_absolute() else Path(raw)
        if path in seen:
            continue
        seen.add(path)
        if path.is_dir():
            return path
    # Last resort relative defaults even if configured was a missing absolute path
    for raw in ("docs", "../docs"):
        path = _resolve_from_backend(raw)
        if path.is_dir():
            return path
    return _resolve_from_backend(configured if not Path(configured).is_absolute() else "docs")
