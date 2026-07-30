---
document_id: api-guide
title: API Guide
category: API Guide
last_updated: 2026-06-20
version: 2.8.0
tags: [api, rest, endpoints, developers]
---

# API Guide

The PriceLabs API lets PMS partners and advanced hosts read listings, fetch recommended prices, and submit overrides. Base URL:

```
https://api.pricelabs.co/v1
```

All requests require HTTPS. JSON request and response bodies use `Content-Type: application/json`.

## Authentication

See **Authentication** for API keys and OAuth. Every request must include:

```
Authorization: Bearer <access_token>
```

## Core resources

### Listings

```
GET /v1/listings
GET /v1/listings/{listing_id}
```

Returns listing metadata: name, timezone, currency, channel mappings, sync status.

### Prices

```
GET /v1/listings/{listing_id}/prices?start=YYYY-MM-DD&end=YYYY-MM-DD
PUT /v1/listings/{listing_id}/prices
```

`GET` returns recommended and currently pushed prices per date.  
`PUT` submits date-level overrides (`price`, `min_stay`, `price_locked`).

### Market data (read-only)

```
GET /v1/markets/{market_id}/metrics?start=YYYY-MM-DD&end=YYYY-MM-DD
```

Occupancy, ADR, and booking pace for the listing's market segment.

## Pagination

List endpoints return:

```json
{
  "data": [],
  "paging": { "next_cursor": "...", "limit": 50 }
}
```

Pass `cursor` on the next request. Default limit 50; max 100.

## Errors

Error envelope:

```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Too many requests",
    "request_id": "req_abc123"
  }
}
```

Always log `request_id` when opening a support ticket about API behavior.

## Idempotency

`PUT /prices` accepts `Idempotency-Key` header. Retries with the same key within 24 hours return the original result without double-applying overrides.

## Versioning

Breaking changes ship under a new path prefix (`/v2`). `/v1` receives backward-compatible additions only. Deprecation notices appear in Release Notes at least 90 days prior.
