---
document_id: troubleshooting
title: Troubleshooting Guide
category: Troubleshooting
last_updated: 2026-06-10
version: 3.0.0
tags: [troubleshooting, sync, support-playbook]
---

# Troubleshooting Guide

Use this playbook for the highest-volume support themes. Escalate only after completing the listed checks.

## Prices not updating on the channel

1. Confirm sync is **enabled** for the listing + channel.
2. Confirm listing is not fully **locked** for the date range.
3. Check **Sync Log** for the last push status and error code.
4. Verify channel authorization is valid (Airbnb OAuth / Booking.com credentials).
5. Confirm currency match between PriceLabs and channel.
6. Wait for channel propagation (Airbnb often < 15m; Booking.com up to 2h).

## Recommendations look wrong

1. Verify bedroom/bathroom count and location on the listing.
2. Check base price vs. recent booked ADR.
3. Inspect seasonal profiles overlapping the dates.
4. Review aggressiveness and last-minute factors.
5. Compare market occupancy for those dates in Market View.

## Duplicate calendars / double bookings

1. Ensure only one pricing system pushes rates.
2. Disable conflicting iCal loops (A → B → A).
3. Confirm PMS is source of truth for availability if applicable.

## Login / access issues

1. Password reset via login page.
2. Check whether SSO is enforced for the organization.
3. Confirm user invite accepted and role assigned.

## API integration failures

1. Capture `request_id` from error payload.
2. Check auth method and scopes.
3. Check rate limit headers.
4. Reproduce with a minimal `GET /listings` call.

## When to escalate

Escalate to Technical Support when:
- Sync log shows repeated `INTERNAL_ERROR`
- Channel partner status is healthy but pushes fail for > 6 hours
- Data corruption suspected (prices pushed to wrong listing)

Include: listing ID, channel, timeframe, screenshots of Sync Log, and `request_id` if API-related.
