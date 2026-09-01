# Requirements Specification

## Functional Requirements

1. **llms.txt Directory & Indexing**:
   - Crawl, ingest, and validate `llms.txt` and `llms-full.txt` files according to specification v2.
   - Support semantic and keyword search across indexed documentation sets.
2. **Interactive 3D Concept Tree**:
   - Render hierarchical concept trees in 3D force-directed layouts.
3. **Accounts & API Metering**:
   - Provide secure authentication via WebAuthn passkeys and OAuth (GitHub, Google).
   - Issue and manage scoped API keys with per-key daily budget caps.
   - Record all billable usage to an append-only ledger in PostgreSQL.
4. **Subscription Billing**:
   - Support multi-tier plans (Free, Starter, Pro) via Stripe Checkout & Customer Portal.
   - Automatically credit monthly allowances based on invoice settlement events.

## Non-Functional Requirements

1. **Financial Accuracy**: Zero floating-point calculations for billing; exact decimal math (`Numeric(12,6)`).
2. **Auditability**: Database triggers prevent modification or deletion of ledger entries.
3. **Performance**: Sub-100ms response times for cached directory pages and documentation lookups.
4. **Portability**: Hermetic build and testing processes across macOS and Linux.
