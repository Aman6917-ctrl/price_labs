"""Typed failures for the Ask pipeline — mapped to HTTP in the route."""

from __future__ import annotations


class AskError(Exception):
    """Base Ask failure."""

    code = "ask_error"
    status_code = 500

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class EmbeddingError(AskError):
    code = "embedding_failure"
    status_code = 502


class VectorStoreError(AskError):
    code = "vector_store_failure"
    status_code = 502


class LLMError(AskError):
    code = "llm_failure"
    status_code = 502


class PersistenceError(AskError):
    code = "persistence_failure"
    status_code = 503


class ValidationAskError(AskError):
    code = "validation_error"
    status_code = 400
