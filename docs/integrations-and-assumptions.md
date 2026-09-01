# Integrations & Environmental Assumptions

## External Services

| Service | Protocol | Purpose | Fallback / Behavior on Outage |
|---|---|---|---|
| PostgreSQL 16 | TCP (asyncpg) | Primary relational database & ledger | Returns 503 with JSON-RPC error envelope |
| Stripe API | HTTPS REST | Subscriptions & customer portal | Retried via Stripe webhook retry mechanism |
| GitHub OAuth | HTTPS OAuth2 | User authentication | User can sign in with Passkey or Google |
| Google OAuth | HTTPS OAuth2 | User authentication | User can sign in with Passkey or GitHub |
| Ollama | HTTP REST | Local embedding & LLM generation | Weighted pooling falls back to available hosts |

## Hardcoded Assumptions

1. **PostgreSQL**: Postgres extensions and triggers (`plpgsql`) must be supported.
2. **Loopback Hub**: `HUB_MCP_URL` must reside on loopback (127.0.0.1 / localhost) to prevent unauthorized network exposure.
