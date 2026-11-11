# External Calls Inventory

| Component | Target Service | Transport | Error Handling | Retry Policy |
|---|---|---|---|---|
| `api/explorer_api/billing.py` | Stripe API | HTTPS REST (`stripe` SDK) | `stripe.error.StripeError` | Handled via webhook idempotency & exponential backoff |
| `api/explorer_api/auth.py` | GitHub OAuth | HTTPS REST (`httpx`) | `auth.OAuthError` | Fast fail on bad authorization code |
| `api/explorer_api/auth.py` | Google OAuth | HTTPS REST (`httpx`) | `auth.OAuthError` | Fast fail on bad authorization code |
| `api/explorer_api/routes/skills.py` | Anthropic Claude API | HTTPS REST (`anthropic` SDK) | `anthropic.APIError` / `gw.GatewayRefusal` | Fail on provider error; ledger records all attempts (component 16 §1) |
| `hub/scripts/embed_core.py` | Ollama Hosts | HTTP REST (`urllib`) | ConnectionError / Timeout | Weighted failover across cluster nodes |
| `hub/scripts/llms_full_catalog.py` | External Documentation Sites | HTTPS GET (`urllib`) | Log and skip | Single retry on HTTP 5xx |

## Research expertise boundary

This inventory is partial, not a complete five-standard operations audit. The
standalone package does not use the TAM Node operations-registry/dashboard
framework. Do not infer missing calls are covered by the historical table above.

| Source | Call target | Trigger | Failure / retry / verification | Test and contract |
| --- | --- | --- | --- | --- |
| `hub/research-expertise/src/research_expertise/store.py:Store.read/write` | Local Neo4j Bolt | CLI and bounded MCP | Managed driver transactions; ingestion records failed state; capture reads back its exact document and complete vectors | `tests/test_store.py`, `tests/test_capture.py`; package `README.md` and `MCP.md` |
| `hub/research-expertise/src/research_expertise/store.py:Embedder.model` | Public Hugging Face model snapshot | Explicit first embedding use | Pinned repository/revision; download failure propagates; model remains cached locally | `tests/test_store.py`; package model identity/migration guide |
| `hub/research-expertise/src/research_expertise/store.py:Embedder.passages/query` | Local ONNX CPU runtime | Search or explicit projection refresh | No remote prose transfer; dimensions validated; failure propagates or leaves capture pending | `tests/test_store.py`; package retrieval guide |
| `hub/research-expertise/install.py:main` | Local `uv` and optional `launchctl` subprocesses | Explicit installer | Checked installation/bootstrap subprocesses; optional prior launch-agent bootout is best effort | Installer source; package installation guide |

The broader inventory still needs call-level source anchors, logger/test/retry
coverage and an accurate generated operations map. A new generic registry and
dashboard would be a separate architecture change; this audit does not invent
those surfaces.
