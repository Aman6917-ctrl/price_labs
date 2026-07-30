"""
Application configuration.

All runtime knobs live here so services never hardcode secrets or model names.
Primary stack: Anthropic Claude (chat) + local sentence-transformers (embeddings).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ — always load .env from here, regardless of process CWD
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_ROOT / ".env"

_PLACEHOLDER_KEYS = {
    "",
    "sk-your-key-here",
    "sk-ant-your-key-here",
    "your-api-key",
    "changeme",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    app_name: str = "Support Intelligence Workspace"
    app_env: str = "development"
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:5173"

    # --- MongoDB ---
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "support_intelligence"

    # --- LLM (Anthropic Claude) ---
    llm_provider: str = Field(default="anthropic")
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"
    # Kept for backward-compatible env files; unused by the Anthropic path
    openai_api_key: str = ""
    llm_model: str = "claude-sonnet-5"

    # --- Embeddings (local, no API key) ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- RAG / Chroma ---
    chroma_persist_dir: str = "../vectorstore"
    chroma_collection: str = "pricelabs_docs_minilm"
    rag_top_k: int = 5
    docs_path: str = "../docs"
    chunk_size: int = 900
    chunk_overlap: int = 150

    # --- Confidence thresholds ---
    confidence_high: float = 0.75
    confidence_medium: float = 0.45

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def has_usable_anthropic_key(self) -> bool:
        key = (self.anthropic_api_key or "").strip()
        return bool(key) and key.lower() not in _PLACEHOLDER_KEYS

    @property
    def effective_llm_provider(self) -> str:
        """
        anthropic — Claude (default when key present)
        local — extractive fallback (no Anthropic key / LLM_PROVIDER=local)
        """
        requested = (self.llm_provider or "anthropic").strip().lower()
        if requested == "local":
            return "local"
        if requested in {"anthropic", "claude", "auto"}:
            return "anthropic" if self.has_usable_anthropic_key else "local"
        return "anthropic" if self.has_usable_anthropic_key else "local"

    @property
    def chat_model_name(self) -> str:
        return (self.anthropic_model or self.llm_model or "claude-sonnet-5").strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()
