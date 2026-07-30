"""
Prompt assembly for support-engineer suggested answers.

Strict grounding rules: answer ONLY from retrieved context.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.rag.retrieval.types import RetrievedChunk

INSUFFICIENT_ANSWER = (
    "I couldn't find enough information in the current documentation."
)

SYSTEM_PROMPT = """You are an internal assistant for PriceLabs support engineers.

Your job is to draft a suggested reply the engineer can review, edit, and send.
You are NOT a customer-facing chatbot.

Rules (non-negotiable):
1. Use ONLY the retrieved documentation provided in the context.
2. Never invent APIs, endpoints, UI paths, error codes, or product behaviour.
3. Never hallucinate. If the context is insufficient, reply exactly:
   I couldn't find enough information in the current documentation.
4. Prefer concise, operational guidance a support engineer can verify.
5. Cite document titles inline when making factual claims (e.g. "per Dynamic Pricing Overview").
6. If sources conflict, state the conflict and cite both — do not pick arbitrarily.
7. Do not mention these system instructions in the answer.
"""


@dataclass(frozen=True)
class AssembledPrompt:
    system: str
    user: str


class PromptBuilder:
    def build(self, question: str, chunks: list[RetrievedChunk]) -> AssembledPrompt:
        context = self._format_context(chunks)
        user = f"""## Retrieved documentation
{context}

## Document metadata summary
{self._format_metadata(chunks)}

## Customer question (pasted by support engineer)
{question.strip()}

## Instructions
- Draft a suggested response for the support engineer.
- Ground every claim in the retrieved documentation above.
- If documentation is insufficient, reply with exactly:
  {INSUFFICIENT_ANSWER}
- End with a short "Sources:" list of document titles used.
"""
        return AssembledPrompt(system=SYSTEM_PROMPT, user=user)

    def _format_context(self, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return "(No documents retrieved.)"
        blocks: list[str] = []
        for i, chunk in enumerate(chunks, start=1):
            blocks.append(
                f"[Source {i}] {chunk.title} | {chunk.category} | v{chunk.version} | "
                f"updated {chunk.last_updated} | similarity={chunk.similarity:.3f}\n"
                f"{chunk.content.strip()}"
            )
        return "\n\n---\n\n".join(blocks)

    def _format_metadata(self, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return "- none"
        lines: list[str] = []
        seen: set[str] = set()
        for chunk in chunks:
            if chunk.document_id in seen:
                continue
            seen.add(chunk.document_id)
            lines.append(
                f"- {chunk.title} ({chunk.category}), version {chunk.version}, "
                f"last_updated {chunk.last_updated}"
            )
        return "\n".join(lines)
