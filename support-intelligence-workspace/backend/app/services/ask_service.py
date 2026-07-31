"""
AskService — orchestrates the internal support intelligence RAG path.

Not a chatbot. Produces a reviewable suggested answer with confidence,
coverage, quality, citations, health, and explainability for support engineers.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from statistics import mean
from typing import Any

from app.config import Settings
from app.events.bus import EventBus
from app.events.types import AnswerGenerated, DocumentRetrieved, QuestionCreated
from app.models.enums import AnswerQuality, ConfidenceLevel, RecommendedAction
from app.rag.citations import CitationBuilder
from app.rag.confidence import ConfidenceCalculator
from app.rag.coverage import CoverageCalculator
from app.rag.evidence import (
    EvidenceAssessor,
    answer_indicates_insufficient,
    sanitize_question,
)
from app.rag.exceptions import (
    EmbeddingError,
    LLMError,
    ValidationAskError,
    VectorStoreError,
)
from app.rag.explainability import ExplainabilityBuilder
from app.rag.health import DocumentHealthCalculator
from app.rag.llm import BaseLLM, LLMResult, LLMService
from app.rag.observability import AskTrace, timed_section
from app.rag.prompt_builder import INSUFFICIENT_ANSWER, PromptBuilder
from app.rag.quality import AnswerQualityEvaluator, RecommendedActionResolver
from app.rag.retrieval.base import BaseRetriever
from app.rag.retrieval.reranker_base import BaseReranker
from app.rag.retrieval.types import RetrievedChunk, RetrievalResult
from app.schemas.ask import (
    AskRequest,
    AskResponse,
    ConfidenceBlock,
    CoverageBlock,
    DocumentHealthSchema,
    ProcessingTimings,
    QualityBlock,
    RetrievedDocumentSchema,
    TokenUsage,
)
from app.schemas.question import CitationSchema, QuestionCreate
from app.services.document_service import DocumentService
from app.services.question_service import QuestionService

logger = logging.getLogger(__name__)

MIN_COVERAGE_FOR_LLM = 25.0


class AskService:
    def __init__(
        self,
        *,
        settings: Settings,
        retriever: BaseRetriever,
        reranker: BaseReranker,
        llm: BaseLLM,
        prompt_builder: PromptBuilder,
        confidence_calculator: ConfidenceCalculator,
        coverage_calculator: CoverageCalculator,
        health_calculator: DocumentHealthCalculator,
        citation_builder: CitationBuilder,
        explainability_builder: ExplainabilityBuilder,
        quality_evaluator: AnswerQualityEvaluator | None = None,
        action_resolver: RecommendedActionResolver | None = None,
        evidence_assessor: EvidenceAssessor | None = None,
        question_service: QuestionService | None = None,
        document_service: DocumentService | None = None,
        gap_count_provider: Any | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._settings = settings
        self._retriever = retriever
        self._reranker = reranker
        self._llm = llm
        self._prompts = prompt_builder
        self._confidence = confidence_calculator
        self._coverage = coverage_calculator
        self._evidence = evidence_assessor or EvidenceAssessor()
        self._health = health_calculator
        self._citations = citation_builder
        self._explain = explainability_builder
        self._quality = quality_evaluator or AnswerQualityEvaluator()
        self._actions = action_resolver or RecommendedActionResolver()
        self._questions = question_service
        self._documents = document_service
        self._gap_count_provider = gap_count_provider
        self._bus = event_bus

    async def ask(self, request: AskRequest) -> AskResponse:
        request_id = f"req_{uuid.uuid4().hex[:16]}"
        trace = AskTrace(request_id=request_id)
        t0 = time.perf_counter()
        pre_rerank: list[RetrievedChunk] = []

        try:
            self._validate(request)
            top_k = request.top_k or self._settings.rag_top_k

            try:
                retrieval = await asyncio.to_thread(
                    self._retriever.retrieve,
                    request.question,
                    top_k=top_k * 2,
                )
            except ValueError as exc:
                raise EmbeddingError(str(exc)) from exc
            except Exception as exc:
                raise VectorStoreError(f"Retrieval failed: {exc}") from exc

            if isinstance(retrieval, RetrievalResult):
                pre_rerank = list(retrieval.chunks)
                trace.embedding_ms = retrieval.embedding_ms
                trace.retrieval_ms = retrieval.search_ms
            else:
                # Back-compat if a custom retriever still returns a bare list
                pre_rerank = list(retrieval)  # type: ignore[arg-type]
                trace.retrieval_ms = 0.0

            with timed_section(trace, "rerank_ms"):
                chunks = await asyncio.to_thread(
                    self._reranker.rerank,
                    request.question,
                    pre_rerank,
                    top_k=top_k,
                )

            trace.retrieved_count = len(chunks)
            trace.unique_documents = len({c.document_id for c in chunks})

            evidence = self._evidence.assess(request.question, chunks)

            # Safety net: if a matching product doc was retrieved, never treat
            # the question as an unsupported knowledge gap (false-negative guard).
            if (
                evidence.unsupported_topic
                and chunks
                and self._evidence.has_direct_doc_support(request.question, chunks)
            ):
                evidence = self._evidence.mark_supported(evidence)

            confidence = self._confidence.calculate(chunks, evidence=evidence)
            coverage = self._coverage.calculate(chunks, evidence=evidence)

            # Unsupported topics: clamp scores only AFTER verification above,
            # skip LLM, and do not cite loosely related docs as evidence.
            loosely_related: list[RetrievedChunk] = []
            if evidence.unsupported_topic:
                loosely_related = list(chunks)
                chunks = []
                confidence = self._confidence.clamp_unsupported(confidence)
                coverage = self._coverage.clamp_unsupported(coverage)
                citations = []
                health_rows = []
                answer = INSUFFICIENT_ANSWER
                skipped_llm = True
                llm_result = None
                insufficient_answer = True
            else:
                gap_counts = await self._load_gap_counts(chunks)
                health_rows = self._health.assess(chunks, gap_counts=gap_counts)
                citations = self._citations.build(chunks)

                answer, skipped_llm, llm_result = await self._generate_answer(
                    request.question, chunks, coverage.score, trace
                )

                insufficient_answer = skipped_llm or answer_indicates_insufficient(
                    answer
                )
                if insufficient_answer:
                    confidence = self._confidence.clamp_unsupported(confidence)
                    coverage = self._coverage.clamp_unsupported(coverage)
                    # Insufficient answer must not cite docs that didn't answer
                    citations = []

            why = self._explain.build(
                chunks if chunks else loosely_related,
                confidence,
                coverage,
                unsupported_topic=evidence.unsupported_topic
                or insufficient_answer,
                evidence_reasons=list(evidence.reasons),
            )

            quality = self._quality.evaluate(
                answer=answer,
                citations=citations,
                coverage_score=coverage.score,
                confidence_level=confidence.level,
                confidence_score=confidence.score,
                skipped_llm=skipped_llm,
                unsupported_topic=evidence.unsupported_topic
                or insufficient_answer,
            )
            action = self._actions.resolve(
                coverage_score=coverage.score,
                confidence_level=confidence.level,
                quality=quality.label,
                unsupported_topic=evidence.unsupported_topic,
                insufficient_answer=insufficient_answer,
            )

            trace.skipped_llm = skipped_llm
            trace.confidence_score = confidence.score
            trace.coverage_score = coverage.score
            trace.confidence_level = confidence.level.value
            trace.quality = quality.label.value
            trace.recommended_action = action.action.value
            if llm_result is not None:
                trace.prompt_tokens = llm_result.prompt_tokens
                trace.completion_tokens = llm_result.completion_tokens
                trace.total_tokens = llm_result.total_tokens
                trace.estimated_cost_usd = llm_result.estimated_cost_usd

            trace.total_ms = (time.perf_counter() - t0) * 1000

            question_id = await self._persist(
                request=request,
                answer=answer,
                confidence=confidence,
                chunks=chunks,
                citations=citations,
                coverage_score=coverage.score,
                quality=quality.label,
                action=action.action,
                request_id=request_id,
                processing_time_ms=trace.total_ms,
                trace=trace,
            )

            await self._emit_ask_events(
                request_id=request_id,
                question_id=question_id,
                chunks=chunks,
                confidence_score=confidence.score,
                coverage_score=coverage.score,
                quality=quality.label.value,
                recommended_action=action.action.value,
                processing_time_ms=trace.total_ms,
                skipped_llm=skipped_llm,
                session_id=request.session_id
                or trace.metadata.get("session_id"),
            )

            trace.emit()

            processing = ProcessingTimings(
                embedding_ms=round(trace.embedding_ms, 1),
                retrieval_ms=round(trace.retrieval_ms, 1),
                rerank_ms=round(trace.rerank_ms, 1),
                llm_ms=round(trace.llm_ms, 1),
                total_ms=round(trace.total_ms, 1),
            )
            token_usage = TokenUsage(
                prompt_tokens=trace.prompt_tokens,
                completion_tokens=trace.completion_tokens,
                total_tokens=trace.total_tokens,
                estimated_cost_usd=trace.estimated_cost_usd,
            )

            metadata: dict[str, Any] = {
                "request_id": request_id,
                "model": getattr(self._llm, "model_name", "unknown"),
                "top_k": top_k,
                "skipped_llm": skipped_llm,
                "unsupported_topic": evidence.unsupported_topic,
                "insufficient_answer": insufficient_answer,
                "docs_are_loosely_related": bool(loosely_related),
                "loosely_related_documents": [
                    {
                        "document_id": c.document_id,
                        "title": c.title,
                        "category": c.category,
                        "similarity": round(c.similarity, 4),
                    }
                    for c in _unique_docs(loosely_related)[:5]
                ],
                "evidence": {
                    "keyword_overlap": evidence.keyword_overlap,
                    "entity_overlap": evidence.entity_overlap,
                    "direct_mention": evidence.direct_mention,
                    "evidence_quality": evidence.evidence_quality,
                    "focus_terms": list(evidence.focus_terms),
                    "missing_terms": list(evidence.missing_terms),
                    "reasons": list(evidence.reasons),
                },
                "confidence_factors": confidence.factors,
                "coverage_factors": coverage.factors,
                "quality_reasons": quality.reasons,
                "recommended_action_reason": action.reason,
                "processing": processing.model_dump(),
                "token_usage": token_usage.model_dump(),
                "session_id": request.session_id
                or trace.metadata.get("session_id"),
            }
            if self._is_development():
                metadata["debug"] = self._build_debug(
                    pre_rerank=pre_rerank,
                    reranked=chunks,
                    embedding_ms=trace.embedding_ms,
                    search_ms=trace.retrieval_ms,
                    rerank_ms=trace.rerank_ms,
                )

            return AskResponse(
                request_id=request_id,
                answer=answer,
                confidence=ConfidenceBlock(
                    level=confidence.level, score=confidence.score
                ),
                coverage=CoverageBlock(
                    score=coverage.score, label=coverage.label
                ),
                quality=QualityBlock(label=quality.label, reasons=quality.reasons),
                citations=citations,
                why_this_answer=why,
                recommended_action=action.action,
                recommended_action_reason=action.reason,
                retrieved_documents=[
                    RetrievedDocumentSchema(
                        document_id=c.document_id,
                        title=c.title,
                        category=c.category,
                        version=c.version,
                        last_updated=c.last_updated,
                        similarity=round(c.similarity, 4),
                        excerpt=_excerpt(c.content),
                    )
                    for c in _unique_docs(chunks)
                ],
                document_health=[
                    DocumentHealthSchema(
                        document_id=h.document_id,
                        title=h.title,
                        category=h.category,
                        health=h.health,
                        reason=h.reason,
                        last_updated=h.last_updated,
                        version=h.version,
                    )
                    for h in health_rows
                ],
                question_id=question_id,
                processing=processing,
                metadata=metadata,
            )
        except (ValidationAskError, EmbeddingError, VectorStoreError, LLMError):
            trace.error_type = "known"
            trace.total_ms = (time.perf_counter() - t0) * 1000
            trace.emit()
            raise
        except Exception as exc:
            trace.error_type = type(exc).__name__
            trace.total_ms = (time.perf_counter() - t0) * 1000
            trace.emit()
            logger.exception("ask_unhandled_error request_id=%s", request_id)
            return self._fallback_response(request_id, trace, str(exc))

    def _validate(self, request: AskRequest) -> None:
        cleaned = sanitize_question(request.question or "")
        if len(cleaned) < 3:
            raise ValidationAskError("Question is required")
        if len(request.question) > 4000:
            raise ValidationAskError("Question exceeds maximum length of 4000 characters")

    def _is_development(self) -> bool:
        return self._settings.app_env.lower() in {"development", "dev", "local"}

    def _build_debug(
        self,
        *,
        pre_rerank: list[RetrievedChunk],
        reranked: list[RetrievedChunk],
        embedding_ms: float,
        search_ms: float,
        rerank_ms: float,
    ) -> dict[str, Any]:
        sims = [c.similarity for c in reranked]
        return {
            "retrieved_chunks": [
                {
                    "document_id": c.document_id,
                    "title": c.title,
                    "similarity": round(c.similarity, 4),
                    "excerpt": _excerpt(c.content, 120),
                }
                for c in pre_rerank
            ],
            "retrieved_documents": [
                {"document_id": c.document_id, "title": c.title}
                for c in _unique_docs(pre_rerank)
            ],
            "average_similarity": round(mean(sims), 4) if sims else 0.0,
            "top_similarity": round(max(sims), 4) if sims else 0.0,
            "reranked_order": [
                {"rank": i + 1, "document_id": c.document_id, "title": c.title}
                for i, c in enumerate(reranked)
            ],
            "retrieval_time": {
                "embedding_ms": round(embedding_ms, 1),
                "search_ms": round(search_ms, 1),
                "rerank_ms": round(rerank_ms, 1),
            },
        }

    async def _generate_answer(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        coverage_score: float,
        trace: AskTrace,
    ) -> tuple[str, bool, LLMResult | None]:
        if not chunks or coverage_score < MIN_COVERAGE_FOR_LLM:
            return INSUFFICIENT_ANSWER, True, None

        prompt = self._prompts.build(question, chunks)
        try:
            with timed_section(trace, "llm_ms"):
                result = await asyncio.to_thread(
                    self._llm.generate, system=prompt.system, user=prompt.user
                )
        except Exception as exc:
            raise LLMError(f"LLM generation failed: {exc}") from exc

        if isinstance(result, LLMResult):
            text = result.text
            llm_result = result
        else:
            # Back-compat for string-only fakes
            text = str(result)
            llm_result = LLMResult(text=text)

        if not text:
            return INSUFFICIENT_ANSWER, False, llm_result
        return text, False, llm_result

    async def _emit_ask_events(
        self,
        *,
        request_id: str,
        question_id: str | None,
        chunks: list[RetrievedChunk],
        confidence_score: float,
        coverage_score: float,
        quality: str,
        recommended_action: str,
        processing_time_ms: float,
        skipped_llm: bool,
        session_id: str | None,
    ) -> None:
        if self._bus is None:
            return
        doc_ids = tuple(dict.fromkeys(c.document_id for c in chunks))
        similarities = {
            c.document_id: c.similarity
            for c in _unique_docs(chunks)
        }
        await self._bus.publish(
            DocumentRetrieved(
                document_ids=doc_ids,
                question_id=question_id,
                request_id=request_id,
                similarities=similarities,
            )
        )
        await self._bus.publish(
            AnswerGenerated(
                question_id=question_id,
                request_id=request_id,
                confidence_score=confidence_score,
                coverage_score=coverage_score,
                quality=quality,
                recommended_action=recommended_action,
                processing_time_ms=processing_time_ms,
                source_document_ids=doc_ids,
                skipped_llm=skipped_llm,
            )
        )
        if question_id:
            await self._bus.publish(
                QuestionCreated(
                    question_id=question_id,
                    session_id=str(session_id or ""),
                    confidence_score=confidence_score,
                    coverage_score=coverage_score,
                    quality=quality,
                    recommended_action=recommended_action,
                    processing_time_ms=processing_time_ms,
                    source_document_ids=doc_ids,
                )
            )

    async def _persist(
        self,
        *,
        request: AskRequest,
        answer: str,
        confidence: Any,
        chunks: list[RetrievedChunk],
        citations: list[Any],
        coverage_score: float,
        quality: AnswerQuality,
        action: RecommendedAction,
        request_id: str,
        processing_time_ms: float,
        trace: AskTrace,
    ) -> str | None:
        if self._questions is None:
            return None

        session_id = request.session_id or f"session_{uuid.uuid4().hex[:12]}"
        trace.metadata["session_id"] = session_id

        payload = QuestionCreate(
            session_id=session_id,
            question_text=request.question,
            suggested_response=answer,
            confidence_score=confidence.score / 100.0,
            confidence_level=confidence.level,
            source_document_ids=list({c.document_id for c in chunks}),
            citations=[
                CitationSchema(
                    document_id=c.document_id,
                    title=c.title,
                    category=c.category,
                    excerpt=c.excerpt,
                    score=c.similarity,
                )
                for c in citations
            ],
            rag_meta={
                "request_id": request_id,
                "coverage_score": coverage_score,
                "confidence_score_100": confidence.score,
                "quality": quality.value,
                "recommended_action": action.value,
                "embedding_ms": round(trace.embedding_ms, 1),
                "retrieval_ms": round(trace.retrieval_ms, 1),
                "llm_ms": round(trace.llm_ms, 1),
                "processing_time_ms": processing_time_ms,
                "token_usage": {
                    "prompt_tokens": trace.prompt_tokens,
                    "completion_tokens": trace.completion_tokens,
                    "total_tokens": trace.total_tokens,
                    "estimated_cost_usd": trace.estimated_cost_usd,
                },
            },
            workspace_id=request.workspace_id,
        )
        try:
            with timed_section(trace, "persist_ms"):
                saved = await self._questions.create_question(payload)
            return saved.id
        except Exception:
            logger.exception("ask_persist_failed request_id=%s", request_id)
            trace.error_type = "persist_soft_fail"
            return None

    async def _load_gap_counts(
        self, chunks: list[RetrievedChunk]
    ) -> dict[str, int]:
        if self._gap_count_provider is None or not chunks:
            return {}
        try:
            return await self._gap_count_provider(
                list({c.document_id for c in chunks})
            )
        except Exception:
            logger.exception("ask_gap_counts_failed")
            return {}

    def _fallback_response(
        self, request_id: str, trace: AskTrace, error: str
    ) -> AskResponse:
        processing = ProcessingTimings(total_ms=round(trace.total_ms, 1))
        return AskResponse(
            request_id=request_id,
            answer=(
                "The support intelligence service hit an unexpected error while "
                "preparing a suggested answer. Please search the knowledge base "
                "manually. Engineering has been signaled via logs (no question "
                "text was logged)."
            ),
            confidence=ConfidenceBlock(level=ConfidenceLevel.LOW, score=0),
            coverage=CoverageBlock(
                score=0,
                label="Documentation coverage unavailable due to an internal error.",
            ),
            quality=QualityBlock(
                label=AnswerQuality.POOR,
                reasons=["Pipeline failed before a grounded answer was produced"],
            ),
            citations=[],
            why_this_answer=(
                "Pipeline failed before a grounded answer could be produced. "
                "Error type recorded in metrics only."
            ),
            recommended_action=RecommendedAction.ESCALATE_TO_HUMAN,
            recommended_action_reason="Internal error — escalate and answer manually.",
            retrieved_documents=[],
            document_health=[],
            question_id=None,
            processing=processing,
            metadata={
                "request_id": request_id,
                "degraded": True,
                "error_class": error[:120],
                "processing": processing.model_dump(),
            },
        )


def _unique_docs(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    best: dict[str, RetrievedChunk] = {}
    for chunk in chunks:
        cur = best.get(chunk.document_id)
        if cur is None or chunk.similarity > cur.similarity:
            best[chunk.document_id] = chunk
    return sorted(best.values(), key=lambda c: c.similarity, reverse=True)


def _excerpt(text: str, limit: int = 180) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1] + "…"


def build_default_ask_service(
    settings: Settings,
    *,
    question_service: QuestionService | None = None,
    document_service: DocumentService | None = None,
    gap_count_provider: Any | None = None,
    event_bus: EventBus | None = None,
    retriever: BaseRetriever | None = None,
    reranker: BaseReranker | None = None,
    llm: BaseLLM | None = None,
) -> AskService:
    """Factory used by DI — keeps construction in one place."""
    from app.rag.local_llm import LocalExtractiveLLM
    from app.rag.retrieval.chroma_retriever import ChromaRetriever
    from app.rag.retrieval.heuristic_reranker import HeuristicReranker

    # Retrieval always uses local MiniLM + Chroma (no OpenAI embeddings).
    provider = settings.effective_llm_provider
    if retriever is None:
        retriever = ChromaRetriever(settings)

    if llm is None:
        if provider == "anthropic":
            llm = LLMService(settings)
        else:
            llm = LocalExtractiveLLM()

    return AskService(
        settings=settings,
        retriever=retriever,
        reranker=reranker or HeuristicReranker(),
        llm=llm,
        prompt_builder=PromptBuilder(),
        confidence_calculator=ConfidenceCalculator(settings),
        coverage_calculator=CoverageCalculator(),
        health_calculator=DocumentHealthCalculator(),
        citation_builder=CitationBuilder(),
        explainability_builder=ExplainabilityBuilder(),
        quality_evaluator=AnswerQualityEvaluator(),
        action_resolver=RecommendedActionResolver(),
        question_service=question_service,
        document_service=document_service,
        gap_count_provider=gap_count_provider,
        event_bus=event_bus,
    )
