"""Shared constants — collection names. Prefer enums for domain values."""

from app.models.enums import (
    ConfidenceLevel,
    DocumentHealth,
    KnowledgeGapReason,
)

# MongoDB collection names (single source of truth)
COLLECTION_QUESTIONS = "questions"
COLLECTION_KNOWLEDGE_GAPS = "knowledge_gaps"
COLLECTION_FEEDBACK = "feedback"
COLLECTION_ANALYTICS = "analytics"
COLLECTION_DOCUMENTS = "documents"

# Re-exports for older imports / docs
GAP_REASONS = tuple(r.value for r in KnowledgeGapReason)
HEALTH_HEALTHY = DocumentHealth.HEALTHY.value
HEALTH_NEEDS_REVIEW = DocumentHealth.NEEDS_REVIEW.value
HEALTH_OUTDATED = DocumentHealth.OUTDATED.value
CONFIDENCE_LEVELS = tuple(c.value for c in ConfidenceLevel)
