# Logging Standards & Observability

## Philosophy

- **Structured & Contextual**: Logs use standard Python `logging` or JSON formats with clear context (user ID, job ID, request path, status).
- **No Secrets / PII**: Passwords, Argon2 hashes, Stripe keys, session cookies, and WebAuthn signatures are never logged.
- **Auditable Events**: Critical state transitions (account creation, API key issuance/revocation, subscription status changes, ledger writes) emit INFO/WARNING logs.

## Log Levels

- `DEBUG`: Detailed execution tracing without SQL parameters or private content.
- `INFO`: Lifecycle milestones (app startup, job dispatched, invoice paid).
- `WARNING`: Recoverable errors, database reconnect attempts, quota limits hit, unknown webhook events.
- `ERROR`: Unhandled exceptions, failed third-party RPCs, database query failures.
- `CRITICAL`: Security anomalies, data corruption risks, broken database triggers.

## Monitored Files & Streams

- `api/`: Uvicorn stderr / stdout.
- `hub/`: `logs/pipeline_manager.log`, launchd agent stdout/stderr.

## API event safety

Key and ledger helpers log `*_staged` after flushing. These events do not claim
that the caller committed its transaction. API database failures record the
operation and exception class, without SQL text, bound parameters or driver
exception strings. Provider and SMTP outcomes follow the same rule; recipient
addresses, subjects, prompts and provider response bodies stay out of service logs.

Research subprocess output is a separate owner-private artifact: new log
directories use mode `0700`, and files use mode `0600`. Service events identify
the job and lifecycle outcome without copying its argv, output or private path.

## Research expertise

The standalone MCP uses stdout only for JSON-RPC. Ingestion progress and safe
operation diagnostics go to stderr. Captures retain canonical data when indexing
fails and return explicit pending status; diagnostics must identify the operation
and exception class without source bodies, credentials or raw provider errors.
Offline tests assert important failure logging and capture state.
