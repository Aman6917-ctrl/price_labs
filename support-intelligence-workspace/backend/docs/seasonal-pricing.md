---
document_id: seasonal-pricing
title: Seasonal Pricing
category: Seasonal Pricing
last_updated: 2026-04-28
version: 2.4.1
tags: [pricing, seasonal, holidays, shoulder-season]
---

# Seasonal Pricing

Seasonal Pricing lets you define date ranges with different pricing behavior — peak, shoulder, and off-season — without manually editing every night.

## Season profiles

Create named seasons (e.g. `Peak Summer`, `Holiday Peak`, `Off-Season`) with:
- Start and end dates (inclusive)
- Optional recurrence (repeats yearly)
- Base price override or multiplier on the listing base price
- Weekend factor overrides
- Min/max overrides for the season window

## Priority rules

When seasons overlap:
1. More specific (shorter) ranges win over broader ranges.
2. Explicit date locks always win over seasons.
3. Dynamic Pricing still applies *within* season bounds unless the season is set to fixed pricing.

## Holiday handling

Major holidays often need a dedicated mini-season even inside a broader peak:
- Thanksgiving week (US)
- Christmas / New Year
- Local festival weeks

Recommended pattern: create a 7–14 day holiday season with higher min price and stronger weekend factor.

## Shoulder season tips

Shoulder seasons are where dynamic pricing adds the most value. Prefer multipliers (e.g. 0.9× base) plus dynamic adjustments rather than hard fixed rates, so the system can still react to unexpected demand.

## Sync behavior

Season changes recalculate recommendations on the next pricing run (typically within 15–60 minutes). Auto-push will update channels only for unlocked dates.

## Troubleshooting seasons

| Symptom | Check |
|---------|-------|
| Season not applied | Date timezone — seasons use listing local date |
| Wrong priority | Overlapping seasons; inspect Season Priority panel |
| Prices too flat | Season set to Fixed instead of Dynamic-within-bounds |
