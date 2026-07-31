---
document_id: account-team-permissions
title: Account Team and Permissions
category: FAQ
last_updated: 2026-02-14
version: 1.2.0
tags: [account, team, permissions, roles, security]
---

# Account Team and Permissions

## Roles

| Role | Capabilities |
|------|----------------|
| Admin | Billing, API keys, webhooks, team, all listings |
| Manager | Listings, pricing, sync, invite Analysts |
| Analyst | Read-only calendars, market views, exports |

## Invites

Admins/Managers invite by email. Invites expire in 7 days. Users can belong to multiple PriceLabs accounts with different roles.

## Support verification

Before making account-sensitive changes (disconnect channel, rotate API keys, change billing email), verify the contact is an **Admin** on the account. Do not take instruction from Analysts for destructive actions.

## Offboarding

When an employee leaves a property management company:
1. Remove their user from **Team**.
2. Rotate API keys they may have accessed.
3. Rotate webhook secrets if they owned endpoints.
4. Revoke OAuth apps they authorized if applicable.

## SSO

Enterprise accounts may enforce SSO. Password login is disabled when SSO is required; users see an SSO redirect on the login page.
