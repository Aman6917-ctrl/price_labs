---
document_id: changelog
title: Changelog
category: Changelog
last_updated: 2026-07-20
version: 2026.07.20
tags: [changelog, api, engineering]
---

# Changelog

Engineering-facing changelog for API and sync behavior. For narrative product updates, see Release Notes.

## 2026-07-20

- `GET /v1/listings/{id}/prices` adds `pushed_at` per date when channel push succeeded.
- Fixed incorrect `X-RateLimit-Remaining` after burst consumption.

## 2026-07-01

- New webhook event: `reservation.imported`.
- Deprecated `listing.price_changed` (alias of `prices.updated`) — removal targeted 2026-10-01.

## 2026-06-12

- Airbnb connector: treat HTTP 429 from Airbnb as retryable; surface `AIRBNB_RATE_LIMIT` in Sync Log.

## 2026-05-05

- Booking.com connector: honor CTA/CTD when restriction sync enabled.
- Bugfix: seasonal min price ignored when season used multiplier-only mode.

## 2026-03-18

- OAuth refresh tokens revoke on password reset of the authorizing user.

## Compatibility notes

- Clients must tolerate unknown fields in JSON responses.
- Enum extensions are non-breaking; enum removals are announced in Release Notes ≥ 90 days ahead.

## Support usage

When a developer asks "when did X change?", cite the dated entry here and link the related Release Notes item if customer-facing.
