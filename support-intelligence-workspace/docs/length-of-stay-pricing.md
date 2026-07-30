---
document_id: length-of-stay-pricing
title: Length of Stay (LOS) Pricing
category: Length of Stay Pricing
last_updated: 2026-06-02
version: 2.1.0
tags: [pricing, los, discounts, min-stay]
---

# Length of Stay (LOS) Pricing

LOS Pricing adjusts the effective nightly rate based on how many nights a guest books. It works alongside Dynamic Pricing and channel min-stay rules.

## Discount ladders

Define LOS discounts as a ladder:

| Nights | Discount |
|--------|----------|
| 7+ | 10% |
| 14+ | 15% |
| 28+ | 20% |

Discounts apply to the **recommended nightly price** after dynamic/seasonal calculations, unless configured as base-price discounts.

## Weekly and monthly

- **Weekly (7 nights):** Common for leisure markets; often 8–12% off.
- **Monthly (28+ nights):** Stronger discounts; confirm channel allows monthly discounts and that cleaning fee / extra-guest fee rules still make sense.

## Interaction with min-stay

LOS discounts do **not** change minimum stay. Min-stay is controlled by:
- Channel settings (Airbnb / Booking.com)
- PriceLabs min-stay customization
- Gap rules (orphan day filling)

If a guest cannot book 7 nights because min-stay is 3 with gaps, the weekly discount simply will not apply to shorter stays.

## Orphan day strategy

For 1–2 night gaps between bookings, many hosts:
- Lower min-stay for those dates only
- Keep LOS discounts unchanged
- Optionally boost last-minute factor

## Support notes

**"Guest sees different total than calendar."**  
Channels may display discounted totals differently. Confirm whether the quote includes cleaning fee, taxes, and LOS discount.

**"Monthly discount not syncing to Airbnb."**  
Airbnb monthly discounts must be enabled on the listing; PriceLabs can push rates but cannot enable the Airbnb monthly setting itself.
