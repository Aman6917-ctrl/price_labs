# API Reference — Support Intelligence Workspace

Base URL (local): `http://localhost:8000`

All business routes are under `/api`.

OpenAPI UI: `/docs`

---

## Health

### `GET /health`

**Response 200**

```json
{
  "status": "ok",
  "service": "Support Intelligence Workspace",
  "mongodb": true,
  "event_handlers": 9
}
```

---

## Ingest

### `POST /api/ingest/`

Load markdown docs → chunk → embed → Chroma.

**Request**

```json
{ "dry_run": false, "replace": true }
```

**Response 200** — `IngestionResult`  
**Errors:** `404` docs path missing · `400` missing API key · `500` ingest failure

---

## Ask

### `POST /api/ask/`

Produce a suggested answer for a support engineer (not a customer chatbot).

**Request**

```json
{
  "question": "How do Airbnb sync failures show up?",
  "session_id": "optional-session",
  "top_k": 5
}
```

**Response 200** (abbrev.)

```json
{
  "request_id": "req_…",
  "answer": "…",
  "confidence": { "level": "high", "score": 82 },
  "coverage": { "score": 78, "label": "Partial documentation exists." },
  "quality": { "label": "good", "reasons": ["…"] },
  "citations": [{ "title": "…", "similarity": 0.88 }],
  "why_this_answer": "…",
  "recommended_action": "send_response",
  "processing": {
    "embedding_ms": 40,
    "retrieval_ms": 12,
    "llm_ms": 900,
    "total_ms": 1100
  },
  "metadata": {
    "token_usage": { "prompt_tokens": 1200, "completion_tokens": 180, "total_tokens": 1380 },
    "debug": {}
  }
}
```

`metadata.debug` is present **only** when `APP_ENV=development`.

**Errors:** `400` validation · `502` embedding / vector / LLM failure

Emits: `DocumentRetrieved`, `AnswerGenerated`, `QuestionCreated` (when persisted).

---

## Knowledge Gaps

### `POST /api/flag-gap`

**Request**

```json
{
  "reason": "missing_documentation",
  "category": "Webhooks",
  "description": "No retry backoff documented",
  "question_id": "optional-object-id",
  "document_id": "webhooks",
  "retrieved_document_ids": ["webhooks", "api-guide"],
  "topic": "webhook retries"
}
```

`reason` enum: `missing_documentation` | `outdated_documentation` | `incorrect_documentation` | `confusing_documentation`

**Response 200** — `KnowledgeGapResponse`  
**Errors:** `400` unknown `question_id` · `503` Mongo down

Emits: `KnowledgeGapFlagged`

### `GET /api/gaps?limit=20`

List recent gap reports.

---

## Feedback

### `POST /api/feedback`

**Request**

```json
{
  "question_id": "…",
  "feedback_type": "thumbs_up",
  "comment": "Clear and accurate"
}
```

`feedback_type`: `thumbs_up` | `thumbs_down` | `positive` | `negative` | `edited` | `regenerated` | `copied`

**Response 200** — `FeedbackResponse`  
**Errors:** `400` unknown question · `503` Mongo down

Emits: `FeedbackSubmitted`

---

## Analytics

### `GET /api/analytics`

Canonical dashboard metrics (computed from questions / gaps / feedback / documents).

**Response 200** — `AnalyticsDashboard`

Includes: questions today/week, gaps, feedback counts + positive/negative %, averages (confidence, coverage, quality, processing time), most retrieved docs, top missing topics, gaps by category, confidence/coverage/health/action distributions.

**Errors:** `503` Mongo down

---

## Documents

### `GET /api/documents/`

List document registry rows (health + stats).

### `GET /api/documents/{document_id}`

Single document.

### `GET /api/documents/{document_id}/stats`

```json
{
  "document_id": "webhooks",
  "retrieval_count": 12,
  "knowledge_gap_count": 2,
  "feedback_count": 3,
  "average_confidence": 74.5,
  "average_coverage": 68.0,
  "average_quality": 75.0,
  "last_retrieved": "2026-07-30T…",
  "health": "needs_review"
}
```

**Errors:** `404` not found

---

## Events (internal)

| Event | Typical emitters | Handlers |
|-------|------------------|----------|
| `QuestionCreated` | AskService | AnalyticsHandler |
| `AnswerGenerated` | AskService | AnalyticsHandler, DocumentStatsHandler |
| `DocumentRetrieved` | AskService | DocumentStatsHandler |
| `KnowledgeGapFlagged` | KnowledgeGapService | AnalyticsHandler, DocumentStatsHandler |
| `FeedbackSubmitted` | FeedbackService | AnalyticsHandler, DocumentStatsHandler |
| `DocumentIngested` | DocumentService | DocumentStatsHandler |

Handlers run **synchronously in-process** via `EventBus`. No Kafka/Redis in MVP.
