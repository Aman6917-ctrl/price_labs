---
document_id: common-errors
title: Common Errors and Codes
category: Common Errors
last_updated: 2026-06-22
version: 1.7.0
tags: [errors, error-codes, sync, api, support]
---

# Common Errors and Codes

Quick reference for Sync Log and API error codes. Pair with Troubleshooting for full playbooks.

## Channel sync errors

| Code | Meaning | Typical fix |
|------|---------|-------------|
| `AIRBNB_AUTH_EXPIRED` | OAuth token invalid | Re-authorize Airbnb |
| `AIRBNB_LISTING_NOT_FOUND` | Listing removed/transferred | Remap listing |
| `AIRBNB_PRICE_REJECTED` | Airbnb rejected rate | Check listing status / bounds |
| `AIRBNB_RATE_LIMIT` | Airbnb throttling | Automatic retry; wait |
| `BCOM_AUTH_FAILED` | Bad Connectivity credentials | Update Hotel ID / password |
| `BCOM_RATE_PLAN_MISSING` | Mapped rate plan gone | Remap rate plan in extranet + PL |
| `BCOM_PUSH_DELAYED` | Accepted but not visible yet | Wait up to 2 hours |
| `CURRENCY_MISMATCH` | Channel currency ≠ PL currency | Align currencies |
| `SYNC_DISABLED` | Sync toggled off | Enable price sync |
| `DATES_LOCKED` | All dates locked | Unlock or explain intentional |

## API errors

| Code | HTTP | Meaning |
|------|------|---------|
| `unauthorized` | 401 | Bad/missing token |
| `forbidden` | 403 | Missing scope or listing access |
| `not_found` | 404 | Unknown listing/resource |
| `validation_error` | 400 | Bad payload (dates, price ≤ 0) |
| `rate_limit_exceeded` | 429 | Too many requests |
| `conflict` | 409 | Idempotency key reuse with different body |
| `internal_error` | 500 | Escalate with request_id |

## UI messages hosts see

- **"Couldn't push prices"** → open Sync Log for the underlying code.
- **"Market data unavailable"** → new listings may need 24–48h; remote areas may have sparse comps.
- **"Recommendation stalled"** → pricing job queued; usually resolves within an hour; if not, check account status.

## Duplicate report prevention

Before filing a product bug, search Release Notes for known issues and confirm the error is reproducible on a second listing.
