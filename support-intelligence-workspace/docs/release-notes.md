---
document_id: release-notes
title: Release Notes
category: Release Notes
last_updated: 2026-07-15
version: 2026.07.15
tags: [releases, product-updates, announcement]
---

# Release Notes

Product changes that affect support answers. Prefer this document over Slack memory when verifying "did we ship X?".

## 2026-07-15 — Pricing Factors panel redesign

- Pricing Factors for each date now shows contribution breakdown (market, season, LOS, last-minute).
- Fixed bug where locked dates still showed stale "recommended" tooltips.
- Support impact: explain that locked dates intentionally skip dynamic recalculation.

## 2026-06-28 — Booking.com occupancy mapping (beta)

- Optional mapping of occupancy-based rates for eligible properties.
- Disabled by default; enable per room type.
- Known issue: mobile-only rate plans may not inherit occupancy mapping.

## 2026-06-10 — Webhook signing secret rotation

- Admins can rotate webhook secrets without deleting the endpoint.
- Old secret remains valid for 24 hours after rotation.
- Partners seeing signature failures after rotation should update secrets promptly.

## 2026-05-22 — Airbnb min-stay sync improvements

- Min-stay push retries on transient Airbnb 5xx errors.
- Sync Log now shows attempt count.

## 2026-04-01 — API Idempotency-Key for price PUT

- See API Guide. Reduce duplicate override tickets from flaky client retries.

## How support should use release notes

1. Search by feature keyword before inventing workarounds.
2. Note "known issues" — do not file as new product bugs without checking.
3. If customers report outdated help center articles, flag a knowledge gap with reason **outdated_documentation**.
