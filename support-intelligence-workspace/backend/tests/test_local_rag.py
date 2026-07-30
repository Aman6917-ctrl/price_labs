"""Unit tests for local extractive LLM (Anthropic fallback)."""

from __future__ import annotations

from app.rag.local_llm import LocalExtractiveLLM


def test_local_llm_generates_text():
    llm = LocalExtractiveLLM()
    out = llm.generate(
        system="You are a support assistant.",
        user=(
            "Context:\nDynamic pricing adjusts nightly rates based on demand.\n\n"
            "Customer question:\nHow does dynamic pricing work?"
        ),
    )
    assert out.text
    assert "documentation" in out.text.lower() or "pricing" in out.text.lower()
