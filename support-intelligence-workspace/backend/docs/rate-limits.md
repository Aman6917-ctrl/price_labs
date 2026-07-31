---
document_id: rate-limits
title: API Rate Limits
category: Rate Limits
last_updated: 2026-03-15
version: 1.9.0
tags: [api, rate-limits, throttling, 429]
---

# API Rate Limits

Rate limits protect platform stability. Limits apply per API key (or per OAuth client + account).

## Default limits

| Plan | Requests / minute | Burst |
|------|-------------------|-------|
| Standard | 60 | 20 |
| Growth | 180 | 40 |
| Enterprise | Custom | Custom |

Bulk price `PUT` counts as **one request** regardless of date span (max 365 days per call).

## Response headers

Every response includes:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1710000000
```

`Reset` is a Unix timestamp (UTC) when the window refreshes.

## HTTP 429

When exceeded:

```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Retry after 12 seconds.",
    "retry_after": 12
  }
}
```

Also sent as `Retry-After: 12`.

## Recommended client behavior

1. Respect `Retry-After`.
2. Use exponential backoff with jitter for repeated 429s.
3. Cache `GET /listings` responses; they change infrequently.
4. Batch price updates into fewer `PUT` calls.

## Webhook deliveries

Webhook delivery retries are separate from API rate limits. Failed webhook endpoints may be paused after repeated failures (see Webhooks).

## Raising limits

Enterprise customers can request higher limits via support. Provide:
- Integration name
- Expected peak RPM
- Endpoints used
- Idempotency strategy

Support should not raise limits for clients that poll `/prices` every second — recommend webhooks or longer intervals instead.
