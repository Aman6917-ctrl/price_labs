"""Tests for Anthropic + local MiniLM configuration."""

from __future__ import annotations

from app.config import Settings


def test_effective_provider_anthropic_with_key():
    s = Settings(
        anthropic_api_key="sk-ant-test-key-not-real",
        llm_provider="anthropic",
        anthropic_model="claude-sonnet-5",
    )
    assert s.has_usable_anthropic_key
    assert s.effective_llm_provider == "anthropic"
    assert s.chat_model_name == "claude-sonnet-5"


def test_effective_provider_local_without_key():
    s = Settings(anthropic_api_key="", llm_provider="auto")
    assert s.effective_llm_provider == "local"


def test_placeholder_anthropic_key_rejected():
    s = Settings(anthropic_api_key="sk-ant-your-key-here", llm_provider="anthropic")
    assert not s.has_usable_anthropic_key
    assert s.effective_llm_provider == "local"


def test_embedding_model_is_local_minilm():
    s = Settings()
    assert "MiniLM" in s.embedding_model or "minilm" in s.embedding_model.lower()
