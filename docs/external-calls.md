# External Calls Inventory

| Component | Target Service | Transport | Error Handling | Retry Policy |
|---|---|---|---|---|
| `api/explorer_api/billing.py` | Stripe API | HTTPS REST (`stripe` SDK) | `stripe.error.StripeError` | Handled via webhook idempotency & exponential backoff |
| `api/explorer_api/auth.py` | GitHub OAuth | HTTPS REST (`httpx`) | `auth.OAuthError` | Fast fail on bad authorization code |
| `api/explorer_api/auth.py` | Google OAuth | HTTPS REST (`httpx`) | `auth.OAuthError` | Fast fail on bad authorization code |
| `hub/scripts/embed_core.py` | Ollama Hosts | HTTP REST (`urllib`) | ConnectionError / Timeout | Weighted failover across cluster nodes |
| `hub/scripts/llms_full_catalog.py` | External Documentation Sites | HTTPS GET (`urllib`) | Log and skip | Single retry on HTTP 5xx |
