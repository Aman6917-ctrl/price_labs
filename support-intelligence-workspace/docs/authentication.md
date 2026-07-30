---
document_id: authentication
title: API Authentication
category: Authentication
last_updated: 2026-06-20
version: 2.3.0
tags: [api, auth, oauth, api-key, security]
---

# API Authentication

PriceLabs supports two authentication methods for the public API: **API keys** (server-to-server) and **OAuth 2.0** (user-delegated access for apps).

## API keys

Best for PMS integrations and internal automations.

1. Account admin opens **Settings → Developers → API Keys**.
2. Create a key with a label and optional IP allowlist.
3. Copy the key once — it is not shown again.
4. Send as Bearer token: `Authorization: Bearer pl_live_...`

Keys inherit the account's listing permissions. Rotate keys every 90 days; revoke immediately if leaked.

## OAuth 2.0

Use OAuth when building multi-tenant apps acting on behalf of hosts.

- Authorization URL: `https://auth.pricelabs.co/oauth/authorize`
- Token URL: `https://auth.pricelabs.co/oauth/token`
- Scopes: `listings:read`, `listings:write`, `prices:read`, `prices:write`, `webhooks:manage`

Access tokens expire in 1 hour. Refresh tokens expire in 60 days of inactivity.

## Service accounts

Enterprise plans may create service accounts limited to a listing group. Prefer service accounts over personal admin keys for production PMS traffic.

## Security requirements

- Never embed API keys in frontend JavaScript or mobile apps.
- Require TLS 1.2+.
- Use separate keys for staging and production.
- Enable IP allowlisting for high-volume partners.

## Auth error codes

| Code | Meaning | Action |
|------|---------|--------|
| `unauthorized` | Missing/invalid token | Check Authorization header |
| `forbidden` | Valid token, insufficient scope | Request additional scopes / permissions |
| `token_expired` | Access token expired | Refresh OAuth token |
| `key_revoked` | API key revoked | Issue a new key |

## Support tip

If a customer says "API suddenly stopped working," ask whether someone rotated keys, changed IP allowlists, or removed the integrating user from the account.
