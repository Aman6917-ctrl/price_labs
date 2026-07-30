"""
Declarative MongoDB index definitions.

ensure_indexes() applies these at startup. Documented here for production
review even if a deployment chooses to manage indexes out-of-band.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.utils.constants import (
    COLLECTION_ANALYTICS,
    COLLECTION_DOCUMENTS,
    COLLECTION_FEEDBACK,
    COLLECTION_KNOWLEDGE_GAPS,
    COLLECTION_QUESTIONS,
)


@dataclass(frozen=True)
class IndexSpec:
    keys: list[tuple[str, int]]
    unique: bool = False
    name: str | None = None
    sparse: bool = False


@dataclass(frozen=True)
class CollectionIndexes:
    collection: str
    indexes: list[IndexSpec] = field(default_factory=list)


# Production index plan -------------------------------------------------------
#
# questions:
#   - created_at          (dashboard: questions today / recent)
#   - session_id          (group turns in one engineer session)
#   - workspace_id+created_at  (future multi-workspace queries)
#
# knowledge_gaps:
#   - category            (gaps by category)
#   - created_at          (recent reports)
#   - reason              (optional filter — included for support)
#
# feedback:
#   - question_id         (all feedback for a question)
#
# documents:
#   - document_id UNIQUE  (registry lookup / upsert)
#
# analytics:
#   - date UNIQUE         (one aggregate row per day; compound w/ workspace later)
#
INDEX_PLAN: list[CollectionIndexes] = [
    CollectionIndexes(
        collection=COLLECTION_QUESTIONS,
        indexes=[
            IndexSpec(keys=[("created_at", -1)], name="questions_created_at"),
            IndexSpec(keys=[("session_id", 1)], name="questions_session_id"),
            IndexSpec(
                keys=[("workspace_id", 1), ("created_at", -1)],
                name="questions_workspace_created_at",
                sparse=True,
            ),
        ],
    ),
    CollectionIndexes(
        collection=COLLECTION_KNOWLEDGE_GAPS,
        indexes=[
            IndexSpec(keys=[("category", 1)], name="gaps_category"),
            IndexSpec(keys=[("created_at", -1)], name="gaps_created_at"),
            IndexSpec(keys=[("reason", 1)], name="gaps_reason"),
            IndexSpec(keys=[("question_id", 1)], name="gaps_question_id", sparse=True),
        ],
    ),
    CollectionIndexes(
        collection=COLLECTION_FEEDBACK,
        indexes=[
            IndexSpec(keys=[("question_id", 1)], name="feedback_question_id"),
            IndexSpec(keys=[("created_at", -1)], name="feedback_created_at"),
        ],
    ),
    CollectionIndexes(
        collection=COLLECTION_DOCUMENTS,
        indexes=[
            IndexSpec(
                keys=[("document_id", 1)],
                unique=True,
                name="documents_document_id_unique",
            ),
            IndexSpec(keys=[("category", 1)], name="documents_category"),
            IndexSpec(keys=[("health", 1)], name="documents_health"),
        ],
    ),
    CollectionIndexes(
        collection=COLLECTION_ANALYTICS,
        indexes=[
            IndexSpec(
                keys=[("date", 1)],
                unique=True,
                name="analytics_date_unique",
            ),
            # When multi-workspace is enabled, replace the unique date index with:
            # unique (workspace_id, date)
            IndexSpec(
                keys=[("workspace_id", 1), ("date", 1)],
                name="analytics_workspace_date",
                sparse=True,
            ),
        ],
    ),
]
