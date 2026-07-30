---
document_id: webhooks
title: Webhooks
category: Webhooks
last_updated: 2026-06-01
version: 2.0.1
tags: [api, webhooks, events, integrations]
---

# Webhooks

Webhooks notify your server when listings, prices, or sync states change — avoiding aggressive polling.

## Setup

1. Go to **Settings → Developers → Webhooks**.
2. Add HTTPS endpoint URL.
3. Select events.
4. Copy the signing secret.

## Event types

| Event | Fired when |
|-------|------------|
| `listing.updated` | Listing metadata or sync settings change |
| `prices.updated` | Recommendations recalculated or push completes |
| `sync.failed` | Channel push fails |
| `sync.succeeded` | Channel push succeeds |
| `reservation.imported` | New reservation imported from a channel |

## Payload example

```json
{
  "id": "evt_01HZX...",
  "type": "sync.failed",
  "created_at": "2026-06-01T14:22:10Z",
  "data": {
    "listing_id": "lst_123",
    "channel": "airbnb",
    "error_code": "AIRBNB_AUTH_EXPIRED",
    "message": "Airbnb authorization expired"
  }
}
```

## Signature verification

Header: `X-PriceLabs-Signature: t=timestamp,v1=hex_hmac`

Compute HMAC-SHA256 of `{timestamp}.{raw_body}` with the signing secret. Reject if timestamp is older than 5 minutes.

## Delivery and retries

- Timeout: 10 seconds
- Retries: 1m, 5m, 30m, 2h, 24h
- After exhausting retries, endpoint marked `failing`
- After 3 days failing, endpoint auto-disabled

## Support guidance

If a partner "isn't receiving webhooks":
1. Confirm endpoint is HTTPS and publicly reachable.
2. Check delivery log for response codes.
3. Verify signature logic isn't rejecting valid events.
4. Confirm the event types are subscribed.
