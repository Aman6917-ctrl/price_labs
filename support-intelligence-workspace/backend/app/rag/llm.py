"""
LLMService — sole Anthropic Claude chat entrypoint.

AskService must never import Anthropic / LangChain chat models directly.
Secrets are read only from Settings (backend/.env).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import Settings

logger = logging.getLogger(__name__)

# Approximate list prices (USD / 1M tokens) for demo cost awareness
_MODEL_PRICING: dict[str, tuple[float, float]] = {
    "claude-sonnet-5": (3.0, 15.0),
    "claude-opus-5": (15.0, 75.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-sonnet-4-5-20250929": (3.0, 15.0),
    "claude-haiku-4-5-20251001": (1.0, 5.0),
    "claude-3-5-sonnet-latest": (3.0, 15.0),
    "claude-3-5-sonnet-20241022": (3.0, 15.0),
}


@dataclass(frozen=True)
class LLMResult:
    text: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost_usd: float | None = None


@runtime_checkable
class BaseLLM(Protocol):
    def generate(self, *, system: str, user: str) -> LLMResult: ...


class LLMService:
    def __init__(self, settings: Settings) -> None:
        if not settings.has_usable_anthropic_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required for Claude generation. "
                "Set it in backend/.env (see backend/.env.example)."
            )
        self._model_name = settings.chat_model_name
        # Newer Claude models reject temperature; omit it for compatibility.
        self._llm = ChatAnthropic(
            model=self._model_name,
            api_key=settings.anthropic_api_key,
            timeout=60,
            max_retries=2,
            max_tokens=2048,
        )

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate(self, *, system: str, user: str) -> LLMResult:
        try:
            response = self._llm.invoke(
                [SystemMessage(content=system), HumanMessage(content=user)]
            )
        except Exception:
            logger.exception("llm_generate_failed model=%s", self._model_name)
            raise

        text = _content_to_text(response.content)
        prompt_tokens, completion_tokens, total_tokens = _extract_tokens(response)
        cost = _estimate_cost(
            self._model_name, prompt_tokens, completion_tokens
        )
        return LLMResult(
            text=text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=cost,
        )


def _content_to_text(content: object) -> str:
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            else:
                text = getattr(block, "text", None)
                if text:
                    parts.append(str(text))
        return "\n".join(parts).strip()
    return str(content).strip()


def _extract_tokens(response: object) -> tuple[int | None, int | None, int | None]:
    usage = getattr(response, "usage_metadata", None) or {}
    if isinstance(usage, dict) and usage:
        prompt = usage.get("input_tokens")
        completion = usage.get("output_tokens")
        total = usage.get("total_tokens")
        if total is None and prompt is not None and completion is not None:
            total = int(prompt) + int(completion)
        return (
            int(prompt) if prompt is not None else None,
            int(completion) if completion is not None else None,
            int(total) if total is not None else None,
        )

    meta = getattr(response, "response_metadata", None) or {}
    usage_meta = meta.get("usage") if isinstance(meta, dict) else None
    if isinstance(usage_meta, dict):
        prompt = usage_meta.get("input_tokens")
        completion = usage_meta.get("output_tokens")
        total = None
        if prompt is not None and completion is not None:
            total = int(prompt) + int(completion)
        return (
            int(prompt) if prompt is not None else None,
            int(completion) if completion is not None else None,
            total,
        )
    return None, None, None


def _estimate_cost(
    model: str,
    prompt_tokens: int | None,
    completion_tokens: int | None,
) -> float | None:
    if prompt_tokens is None or completion_tokens is None:
        return None
    rates = _MODEL_PRICING.get(model)
    if rates is None:
        # Default to Sonnet rates when the exact id is unknown
        rates = _MODEL_PRICING["claude-sonnet-5"]
    in_rate, out_rate = rates
    cost = (prompt_tokens / 1_000_000) * in_rate + (
        completion_tokens / 1_000_000
    ) * out_rate
    return round(cost, 6)
