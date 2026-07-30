---
document_id: booking-com-integration
title: Booking.com Integration
category: Booking.com Integration
last_updated: 2026-05-30
version: 3.5.0
tags: [channel, booking.com, sync, rates, occupancy]
---

# Booking.com Integration

Booking.com sync uses the Connectivity API (via PriceLabs channel partnership). Rate plans, occupancy-based pricing, and restrictions (min-stay, CTA/CTD) can be managed from PriceLabs depending on property setup.

## Connection steps

1. Ensure the property is eligible for PriceLabs connectivity (XML / API partner status).
2. In PriceLabs: **Channels → Booking.com → Connect**.
3. Enter Hotel ID and credentials provided by Booking.com extranet / Connectivity.
4. Map room types and rate plans to PriceLabs listings.
5. Choose which rate plan receives dynamic prices.

## Rate plans

Booking.com often has multiple rate plans (Flexible, Non-refundable, Mobile-only). PriceLabs typically drives a **primary** rate plan; derived plans may use Booking.com's own multipliers.

**Important:** Pushing to the wrong rate plan is a top cause of "prices look wrong on Booking.com" tickets.

## Occupancy pricing

If the room uses occupancy-based pricing:
- Configure base occupancy in PriceLabs
- Extra adult amounts must align with Booking.com extranet
- Dynamic prices apply to the base occupancy rate unless advanced occupancy mapping is enabled

## Restrictions

Supported restrictions (when enabled for the property):
- Min stay through / arrival
- Closed to arrival (CTA) / closed to departure (CTD)
- Max stay

## Troubleshooting

| Issue | Likely cause |
|-------|----------------|
| Prices update in PL but not B.com | Wrong rate plan mapped; connectivity delayed up to 2 hours |
| Occupancy prices incorrect | Base occupancy mismatch |
| Min-stay ignored | Restriction sync disabled for that room |
| Auth errors | Extranet password rotation — update credentials in PriceLabs |

## Support escalation

If Connectivity status shows `SUSPENDED` on Booking.com's side, PriceLabs cannot push. Customer must resolve with Booking.com Connectivity Support first.
