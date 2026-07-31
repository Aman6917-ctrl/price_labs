---
document_id: min-max-prices
title: Minimum and Maximum Prices
category: Dynamic Pricing
last_updated: 2026-04-10
version: 1.5.0
tags: [pricing, min-price, max-price, bounds]
---

# Minimum and Maximum Prices

Min and max prices are hard bounds applied after all pricing factors. The engine never recommends or auto-pushes outside these bounds (unless you manually override and lock).

## Setting bounds

- **Min price:** Floor for any night. Protects against aggressive last-minute drops.
- **Max price:** Ceiling for peak demand / event spikes.

You can set:
- Listing-level defaults
- Seasonal overrides
- Date-specific overrides

Priority: date override > season override > listing default.

## When recommendations stick to the bound

If many dates show recommended = min:
- Base price too high for market, or
- Min too high relative to demand, or
- Last-minute factor pushing down into the floor

If many dates stick to max:
- Event demand or underpriced base, or
- Max too low for true peak

## Communication tips for support

Hosts often interpret a min-bound night as "the algorithm failed." Explain that the bound worked as designed and share the Pricing Factors panel. Offer a temporary min adjustment for a test week rather than disabling dynamic pricing entirely.

## Interaction with LOS discounts

LOS discounts apply to the recommended price **after** bounds. A 20% monthly discount will not break below min unless "allow LOS below min" is enabled (off by default on most accounts).
