"""
Local extractive LLM — no external API.

Produces a grounded draft from retrieved chunks so Ask Workspace works
without ANTHROPIC_API_KEY (development / demos only).
"""

from __future__ import annotations

import logging
import re

from app.rag.llm import LLMResult

logger = logging.getLogger(__name__)

_SENTENCE = re.compile(r"(?<=[.!?])\s+")


class LocalExtractiveLLM:
    """Cheap extractive answerer used when Anthropic is not configured."""

    def __init__(self) -> None:
        logger.warning(
            "Using LocalExtractiveLLM — set ANTHROPIC_API_KEY in backend/.env "
            "for Claude generation."
        )

    @property
    def model_name(self) -> str:
        return "local-extractive"

    def generate(self, *, system: str, user: str) -> LLMResult:
        # PromptBuilder puts context + question in the user message.
        context, question = _split_user(user)
        excerpts = _pick_sentences(context, question, limit=4)
        if not excerpts:
            text = (
                "I could not find enough matching documentation to draft an answer. "
                "Please flag this as a knowledge gap or verify the relevant docs."
            )
        else:
            bullets = "\n".join(f"- {s}" for s in excerpts)
            text = (
                "Based on the available PriceLabs documentation:\n\n"
                f"{bullets}\n\n"
                "Please verify against the cited sources before sending to the customer. "
                "(Local extractive mode — configure ANTHROPIC_API_KEY for Claude answers.)"
            )
        return LLMResult(
            text=text,
            prompt_tokens=None,
            completion_tokens=None,
            total_tokens=None,
            estimated_cost_usd=0.0,
        )


def _split_user(user: str) -> tuple[str, str]:
    # Heuristic: last "Question:" / "Customer question:" block
    lower = user.lower()
    for marker in ("customer question:", "question:"):
        idx = lower.rfind(marker)
        if idx >= 0:
            return user[:idx].strip(), user[idx + len(marker) :].strip()
    return user, user


def _pick_sentences(context: str, question: str, *, limit: int) -> list[str]:
    q_tokens = {t.lower() for t in re.findall(r"[a-z0-9]+", question.lower()) if len(t) > 2}
    sentences = [s.strip() for s in _SENTENCE.split(context) if len(s.strip()) > 40]
    ranked: list[tuple[int, str]] = []
    for s in sentences:
        s_tokens = {t.lower() for t in re.findall(r"[a-z0-9]+", s.lower()) if len(t) > 2}
        score = len(q_tokens & s_tokens)
        if score > 0:
            ranked.append((score, s))
    ranked.sort(key=lambda x: x[0], reverse=True)
    out: list[str] = []
    seen: set[str] = set()
    for _, s in ranked:
        key = s[:80]
        if key in seen:
            continue
        seen.add(key)
        # Keep sentence length reasonable for the UI
        cleaned = s if len(s) <= 320 else s[:317] + "…"
        out.append(cleaned)
        if len(out) >= limit:
            break
    return out
