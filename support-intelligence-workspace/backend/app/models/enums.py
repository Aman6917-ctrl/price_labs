"""
Domain enums — prefer these over raw strings across models, schemas, and services.
"""

from __future__ import annotations

from enum import Enum


class KnowledgeGapReason(str, Enum):
    MISSING_DOCUMENTATION = "missing_documentation"
    OUTDATED_DOCUMENTATION = "outdated_documentation"
    INCORRECT_DOCUMENTATION = "incorrect_documentation"
    CONFUSING_DOCUMENTATION = "confusing_documentation"


class DocumentCategory(str, Enum):
    """Aligned with knowledge-base frontmatter categories."""

    DYNAMIC_PRICING = "Dynamic Pricing"
    SEASONAL_PRICING = "Seasonal Pricing"
    LENGTH_OF_STAY_PRICING = "Length of Stay Pricing"
    AIRBNB_INTEGRATION = "Airbnb Integration"
    BOOKING_COM_INTEGRATION = "Booking.com Integration"
    API_GUIDE = "API Guide"
    AUTHENTICATION = "Authentication"
    RATE_LIMITS = "Rate Limits"
    WEBHOOKS = "Webhooks"
    FAQ = "FAQ"
    TROUBLESHOOTING = "Troubleshooting"
    RELEASE_NOTES = "Release Notes"
    CHANGELOG = "Changelog"
    BEST_PRACTICES = "Best Practices"
    COMMON_ERRORS = "Common Errors"
    UNCATEGORIZED = "uncategorized"


class FeedbackType(str, Enum):
    """Thumbs + legacy/extended feedback signals."""

    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    POSITIVE = "positive"  # treated as thumbs_up in analytics
    NEGATIVE = "negative"  # treated as thumbs_down in analytics
    EDITED = "edited"
    REGENERATED = "regenerated"
    COPIED = "copied"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DocumentHealth(str, Enum):
    HEALTHY = "healthy"
    NEEDS_REVIEW = "needs_review"
    OUTDATED = "outdated"


class AnswerQuality(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    NEEDS_REVIEW = "needs_review"
    POOR = "poor"


class RecommendedAction(str, Enum):
    SEND_RESPONSE = "send_response"
    VERIFY_DOCUMENTATION = "verify_documentation"
    FLAG_KNOWLEDGE_GAP = "flag_knowledge_gap"
    ESCALATE_TO_HUMAN = "escalate_to_human"
