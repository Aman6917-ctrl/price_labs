---
document_id: airbnb-integration
title: Airbnb Integration
category: Airbnb Integration
last_updated: 2026-06-18
version: 4.0.2
tags: [channel, airbnb, sync, ical, api]
---

# Airbnb Integration

PriceLabs connects to Airbnb via official API (preferred) or iCal (limited). API sync supports prices, availability, and min-stay; iCal is availability-oriented and should not be used for full pricing control.

## Connecting a listing

1. Open **Channels → Airbnb**.
2. Authorize the PriceLabs Airbnb app with the host account that owns the listing.
3. Select listings to import.
4. Map each Airbnb listing to a PriceLabs listing (or create new).
5. Enable **Price Sync** and optionally **Min-Stay Sync**.

## What syncs

| Data | API | iCal |
|------|-----|------|
| Nightly price | Yes | No |
| Availability / blocks | Yes | Yes (blocks only) |
| Min-stay | Yes | No |
| Weekend pricing | Yes (as nightly rates) | No |

## Sync frequency

- Price push: on manual push, or every 1 hour when auto-sync is on
- Pull of reservations: near real-time via webhooks when available; otherwise periodic poll

## Common Airbnb sync issues

### Authorization expired
Host must re-authorize. Prices will not push until OAuth is valid. Error code in logs: `AIRBNB_AUTH_EXPIRED`.

### Listing not found
Listing may have been deleted or transferred. Re-import from Airbnb and remapping is required.

### Price rejected
Airbnb may reject prices outside their allowed bounds or when the listing is suspended. Check Airbnb hosting dashboard for listing status.

### Currency mismatch
PriceLabs listing currency must match Airbnb listing currency. Mismatches cause silent confusion in the UI and failed pushes.

## Best practice

Use API sync. Keep iCal only as a backup calendar block source from external tools, not as the primary pricing path.
