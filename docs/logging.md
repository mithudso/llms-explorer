# Logging Standards & Observability

## Philosophy

- **Structured & Contextual**: Logs use standard Python `logging` or JSON formats with clear context (user ID, job ID, request path, status).
- **No Secrets / PII**: Passwords, Argon2 hashes, Stripe keys, session cookies, and WebAuthn signatures are never logged.
- **Auditable Events**: Critical state transitions (account creation, API key issuance/revocation, subscription status changes, ledger writes) emit INFO/WARNING logs.

## Log Levels

- `DEBUG`: Detailed execution tracing, SQL statement inspection in dev.
- `INFO`: Lifecycle milestones (app startup, job dispatched, invoice paid).
- `WARNING`: Recoverable errors, database reconnect attempts, quota limits hit, unknown webhook events.
- `ERROR`: Unhandled exceptions, failed third-party RPCs, database query failures.
- `CRITICAL`: Security anomalies, data corruption risks, broken database triggers.

## Monitored Files & Streams

- `api/`: Uvicorn stderr / stdout.
- `hub/`: `logs/pipeline_manager.log`, launchd agent stdout/stderr.

## Research expertise

The standalone MCP uses stdout only for JSON-RPC. Ingestion progress and safe
operation diagnostics go to stderr. Captures retain canonical data when indexing
fails and return explicit pending status; diagnostics must identify the operation
and exception class without source bodies, credentials or raw provider errors.
Offline tests assert important failure logging and capture state.
