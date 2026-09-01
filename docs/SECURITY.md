# Security & Threat Model

## Authentication & Authorization

1. **Session Security**:
   - Session cookies are signed with `itsdangerous` using `SESSION_SECRET` (min 32 chars).
   - Cookies are configured with `HttpOnly`, `SameSite=Lax`, and `Secure` in production.
   - `session_epoch` in `users` table provides instant revocation of all active sessions.

2. **WebAuthn / Passkeys**:
   - Relying party ID is strictly validated against configured origins.
   - In production, `WEBAUTHN_RP_ID` must be explicitly configured; host header spoofing is prevented by `TrustedHostMiddleware`.

3. **API Keys**:
   - Keys are split into a public prefix (`key_...`) and high-entropy secret.
   - Plaintext secrets are never stored. Hashes use Argon2id (`argon2-cffi`).
   - Every API key can enforce a per-key daily budget (`max_usd_day`).

4. **OAuth Account Linking**:
   - Only emails verified by OAuth providers can link into existing accounts. Unverified emails remain isolated in `pending_email`.

## Financial & Ledger Integrity

1. **Append-Only Ledger**:
   - Postgres triggers `ledger_append_only` and `ledger_append_only_truncate` reject any `UPDATE` or `TRUNCATE` operations on the `ledger` table.
   - No floating-point arithmetic is permitted for monetary calculations; all operations use `Decimal` with 6 decimal places (`Numeric(12,6)`).

2. **Invoice Idempotency**:
   - `credit_grants` uses Stripe's `invoice_id` as the primary key to prevent duplicate credit grants across multiple webhook events.
