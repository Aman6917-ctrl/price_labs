---
document_id: dynamic-pricing
title: Dynamic Pricing Overview
category: Dynamic Pricing
last_updated: 2026-05-12
version: 3.2.0
tags: [pricing, dynamic-pricing, base-price, market]
---

# Dynamic Pricing Overview

Dynamic Pricing automatically adjusts nightly rates based on market demand, seasonality, booking lead time, and competing listings. PriceLabs generates a recommended price for each date; you control how aggressively those recommendations are applied.

## How it works

1. PriceLabs aggregates market occupancy, ADR (average daily rate), and booking pace for your market.
2. Your listing's base price, min/max bounds, and customization rules are applied.
3. A recommended price is produced per date and optionally pushed to the channel (Airbnb, Booking.com, PMS).

## Base price

The **base price** is the anchor for all calculations. It should reflect a typical mid-week, mid-season night for your listing quality and amenities.

Guidelines:
- Set base price from recent closed bookings, not wishful ADR.
- Revisit base price after major renovations or amenity changes.
- If recommendations consistently sit at your minimum, base price is likely too high for the market.

## Customization profile

Each listing (or listing group) has a customization profile:

| Setting | Effect |
|---------|--------|
| Aggressiveness | How far above/below market the algorithm may go |
| Far-out factor | Pricing for dates 90+ days out |
| Last-minute factor | Discounts or holds for near-term vacant dates |
| Weekend factor | Multiplier for Fri–Sat (and optionally Thu/Sun) |

## Demand signals

Dynamic Pricing weighs:
- Market occupancy for similar bedroom/bathroom counts
- Local events and holidays (when market data shows lift)
- Your own booking pace vs. market pace
- Length-of-stay patterns (see Length of Stay Pricing)

## Pushing prices

Recommended prices can be:
- **Reviewed manually** in the PriceLabs calendar before push
- **Auto-pushed** on a schedule (hourly / daily) if sync is enabled

Auto-push respects min/max price and any date-specific overrides you lock.

## Common support questions

**"Why did my price drop overnight?"**  
Usually last-minute factor + soft market occupancy. Check the Pricing Factors panel for that date.

**"Recommendations ignore my comps."**  
Comps inform market context; they do not pin your price to a single competitor. Verify bedroom count and location radius on the market view.

**"Can I exclude certain dates from dynamic pricing?"**  
Yes — lock prices or set fixed prices on those dates. Locked dates are never overwritten by auto-push.
