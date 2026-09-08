---
title: "MongoDB Atlas App Services"
description: "> CRITICAL STATUS NOTE (as of May 2026): Atlas App Services reached a split end-of-life on September 30, 2025."
---

# MongoDB Atlas App Services — Full Platform Reference

> **CRITICAL STATUS NOTE (as of May 2026):** Atlas App Services reached a split end-of-life on September 30, 2025.
> - **STILL LIVE:** Database Triggers, Scheduled Triggers, Authentication Triggers, Atlas Functions (invoked by triggers only)
> - **EOL (shut down September 30, 2025):** Atlas Data API, GraphQL API, Custom HTTPS Endpoints, Atlas Device Sync & Device SDKs, static hosting
> - Auth providers, Rules/Permissions, and Values/Secrets are only relevant now as context for the still-live Triggers surface

## Authentication Providers

| Provider | Type ID | Status (2026) |
|---|---|---|
| Anonymous | `anon-user` | Active |
| Email/Password | `local-userpass` | EOL (Sep 30 2025) |
| API Key | `api-key` | Active |
| Google/Facebook/Apple OAuth2 | `oauth2-*` | EOL |
| Custom JWT | `custom-token` | EOL |
| Custom Function | `custom-function` | EOL |

### Key Auth Notes
- Email confirmation links expire in 30 minutes
- `callResetPasswordFunction()` is unauthenticated — always return `pending` for out-of-band verification
- Custom JWT: App Services always enforces 30-minute access token expiry regardless of JWT `exp` claim

## Rules and Permissions Engine

Permissions are defined per-collection. Role evaluation: first matching role wins (role order matters). If no role matches, the operation is denied entirely. System functions bypass all rules.

Variables: `%%user.id`, `%%user.custom_data.<field>`, `%%root.<field>`, `%%environment.values.<name>`

## Schema Validation

App Services schemas are JSON Schema (draft 4 + BSON extensions). Validates every write after the operation is computed but before commit. Key differences from mongod `$jsonSchema`: App Services validates post-operation; system functions bypass App Services schema.

## Atlas GraphQL API (DEPRECATED — EOL March 5, 2025)

Migration: [Hasura on MongoDB](https://www.mongodb.com/docs/atlas/app-services/graphql/migrate-hasura/) or Apollo Server + driver.

## Atlas Data API (DEPRECATED — EOL September 30, 2025)

Migration paths: MongoDB driver + Express/FastAPI/Spring Boot, cloud functions (Lambda, Azure, GCR), or [Delbridge Data API](https://github.com/delbridge-io/data-api) (open source drop-in).

## Custom HTTPS Endpoints (DEPRECATED — EOL September 30, 2025)

Migration: AWS Lambda, Azure Functions, Google Cloud Run, or Vercel serverless functions + MongoDB driver.

## Values and Secrets

- **Values**: Named JSON constants accessed via `context.values.get("name")`
- **Secrets**: Private strings (max 500 chars) stored encrypted; access indirectly by linking to a Value
- **Environment Values**: `context.environment.values.<name>` for env-specific config

## App Services Deployment

Methods: UI (immediate), CLI (`appservices push/pull`), GitHub auto-deploy (any push triggers deployment), Admin API.

- Last 25 deployments stored for rollback
- Secrets are NOT included in exported config or git repos — must re-enter manually

## Billing Model (Still relevant for Triggers)

Free tier per project: 1M requests/month, 500 compute hours, 10 GB data transfer. Trigger invocations count as requests.

## Migration Reference (Post-EOL)

| Feature | EOL Date | Recommended Replacement |
|---|---|---|
| Atlas Data API | Sep 30, 2025 | MongoDB driver + cloud functions |
| Atlas GraphQL API | Mar 5, 2025 | Hasura, Apollo Server + driver |
| Custom HTTPS Endpoints | Sep 30, 2025 | Cloud functions |
| Atlas Device Sync | Sep 30, 2025 | Custom sync layer |

## Anti-Patterns

- Auto-confirm in production — allows fake email addresses
- `callResetPasswordFunction` returning `success` immediately — unauthenticated callers can reset any user's password
- Collection-level roles defined but relying on default roles — if any collection-level roles defined, default roles are NOT checked
- Role order wrong — most specific roles should come first
- Running App Services schema AND mongod `$jsonSchema` with `validationAction: "error"` — can cause confusing double-rejection errors

## References

1. [Atlas App Services Documentation](https://www.mongodb.com/docs/atlas/app-services/)
2. [Data API and HTTPS Endpoints Deprecation](https://www.mongodb.com/docs/atlas/app-services/data-api/data-api-deprecation/)
3. [Atlas Device Sync EOL Forum Post](https://www.mongodb.com/community/forums/t/atlas-device-sync-end-of-life-and-deprecation/296687)
