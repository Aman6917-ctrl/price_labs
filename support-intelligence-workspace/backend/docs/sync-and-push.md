---
document_id: sync-and-push
title: Sync and Price Push
category: Troubleshooting
last_updated: 2026-05-25
version: 2.0.0
tags: [sync, push, channels, auto-sync]
---

# Sync and Price Push

Explains how prices move from PriceLabs recommendations to channels.

## Manual push

From the calendar, select dates → **Push to channel**. Writes current recommended (or locked) prices for unlocked dates.

## Auto-sync

When enabled, PriceLabs pushes on a schedule (default hourly). Only dates that changed since last successful push are sent (delta push) for supported channels.

## Push pipeline

1. Pricing job calculates recommendations.
2. Bounds, locks, and channel mappings applied.
3. Payload built per channel.
4. Connector sends to channel API.
5. Result written to Sync Log (`succeeded` / `failed` + code).

## Partial success

A push can succeed for Airbnb and fail for Booking.com in the same run. Sync Log is per channel. Do not tell hosts "nothing pushed" without checking each channel row.

## Force full push

Use **Force full push** after remapping rate plans or currencies. This resends the next 365 days (or account limit) and may take longer / count more heavily against channel rate limits.

## Support checklist

- Last successful push timestamp
- Error code on failures
- Whether auto-sync is on
- Whether dates are locked
- Whether the channel listing ID mapping is correct
