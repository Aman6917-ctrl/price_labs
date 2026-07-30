---
document_id: pms-integrations-overview
title: PMS Integrations Overview
category: Best Practices
last_updated: 2026-06-05
version: 1.4.0
tags: [pms, integrations, guesty, hostaway, lodgify]
---

# PMS Integrations Overview

Many hosts connect PriceLabs through a Property Management System rather than directly to Airbnb/Booking.com. This doc covers the shared model; PMS-specific steps live in partner docs.

## Architecture

```
PriceLabs ←→ PMS ←→ Channels
```

PriceLabs sends prices (and sometimes min-stay) to the PMS. The PMS is responsible for distributing to channels and for availability/reservations.

## Implications for support

- If prices are wrong on Airbnb but correct in the PMS, the issue is PMS→channel, not PriceLabs.
- If prices are wrong in the PMS, check PriceLabs Sync Log to the PMS connector.
- Avoid enabling **both** direct Airbnb sync and PMS sync for the same listing — double writers cause flicker and overwrites.

## Common PMS partners

Guesty, Hostaway, Lodgify, Hostfully, Beddy's, and others. Connection usually requires an API key or OAuth from the PMS side.

## Mapping

Each PMS listing/unit maps to one PriceLabs listing. Multi-unit hotels may map room types similarly to Booking.com.

## When docs are missing

If a customer asks about a PMS not listed in help center, flag a knowledge gap (`missing_documentation`) with the PMS name and what they tried. Do not invent sync steps.
