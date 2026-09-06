# Bring-your-own-API-key for the hosted showcase skills — Design

## 0. Why this doc exists

The donations pivot (`docs/superpowers/plans/2026-09-06-donations-and-community-directory-design.md`)
collapsed the plan table to a single free plan. That had a side effect nobody had scoped: the three
hosted showcase skills — `notes-to-llms`, `optimizer-pass`, `concept-abstract-mini`
(`api/explorer_api/routes/skills.py`) — are gated behind the `lint_model_passes` quota, which was
only ever `true` on the now-deleted Starter/Pro plans. With no paid tier left to grant it, every
account is permanently refused, silently converting a real feature into dead code.

Decision (this session, user-directed): instead of trying to fund these calls through donations,
require the caller to supply their own Anthropic API key, and bill Anthropic directly rather than
through this service. This document is that feature's design.

**Also decided, cross-cutting:** the approved donations design doc's Part B (not yet planned as
code) states that the future `/api/contribute` endpoint will reuse `concept-abstract-mini`'s exact
call/quota pattern "since it's the same call." That means the gate this document designs — has this
account stored a working key? — becomes the gate for AI-assisted contribution too, once Plan 3 is
written. A contribution with **no** AI assistance (plain text, no model pass) is unaffected and
needs no key; that path is Plan 3's to design, not this one's.

## 1. Encryption

App-level symmetric encryption via `cryptography.fernet.Fernet`, keyed by a new required setting,
`ANTHROPIC_KEY_ENCRYPTION_SECRET` (a Fernet key: 32 url-safe base64 bytes). Validated at startup
the same way `SESSION_SECRET`/`STRIPE_SECRET_KEY` are today — the app refuses to start without it
once this feature ships, via `Settings`/`MissingSettings`.

Rejected alternatives: Postgres `pgcrypto` (pushes the same problem into SQL with no security
gain, adds a DB extension dependency this repo doesn't otherwise need); an external KMS (this repo
has no cloud-infra dependency yet — Postgres itself is still self-hosted over Tailscale — so
introducing one for a single secret type is more infrastructure than the problem justifies).

## 2. Data model

Two nullable columns added to `User` (`api/explorer_api/models.py`), not a new table — this is a
single optional 1:1 field per account, and a join buys nothing a nullable column doesn't already
give:

- `anthropic_api_key_ciphertext: str | None` — the Fernet-encrypted key. Never leaves the server
  in plaintext after the save call that set it.
- `anthropic_api_key_hint: str | None` — the last 4 characters of the plaintext key, stored
  unencrypted. Not a secret (Anthropic keys are long, high-entropy; 4 trailing characters are not
  guessable-useful) — it exists purely so the account settings UI can show "key ending in …aB3f"
  without ever redisplaying the key itself. Mirrors this app's own API-key convention
  (`ApiKey.prefix` lets `keys.astro` identify a key without reversing its Argon2id hash).

## 3. Save, validate, clear

New route module `api/explorer_api/routes/anthropic_key.py`, prefix `/api/account/anthropic-key`.
Kept separate from `routes/keys.py` (this app's *own* platform API keys — a different concept;
conflating the two files would blur "a key that authenticates to us" with "a key we forward to
Anthropic on your behalf").

- `PUT /api/account/anthropic-key` — body `{"api_key": "sk-ant-..."}`, `current_user` required.
  Before storing anything, makes one real call to Anthropic — `client.models.list()`, which costs
  no tokens — to confirm the key actually authenticates. A bad key is a 422 with a clear message
  immediately, not a confusing failure the next time someone tries to run a skill. On success:
  encrypt, store ciphertext + hint, return `{"hint": "...aB3f"}`.
- `DELETE /api/account/anthropic-key` — `current_user` required. Clears both columns.
- `account.astro` gets a small section: paste a key, Save; if one is stored, show the hint and a
  Remove button. No plaintext key is ever sent back to the browser after the initial save request.

## 4. The gate

`_check_plan` in `routes/skills.py` (called after skill lookup, auth, concept-required, and
input-size checks — that ordering is unchanged) drops its `lint_model_passes` check and replaces
it with: does `principal.user.anthropic_api_key_ciphertext` exist? If not, raise a new
`MissingApiKey(gw.GatewayRefusal)` — `status_code = 403`, `code = "missing_api_key"`, message
pointing at account settings. This is a distinct refusal type from `QuotaExceeded`: it isn't a
tier limit, it's a missing prerequisite, and the client should render a different call to action
("add your API key") than a 402's "upgrade" framing ever implied.

`lint_model_passes` is deleted from `plans.py` (`QUOTA_FEATURES`, `FEATURE_KINDS`, the free plan's
`quotas`) — it no longer describes anything a plan grants. The two remaining checks in
`_check_plan` — `lint_max_bytes` (64 KB) and `lint_per_day` (20/day) — are unchanged in code, and
unchanged in value; they now serve a different purpose (protecting server compute from scripted
abuse) than they did before (protecting the site's own model-provider cost), but "keep modest caps"
means keeping today's numbers, not re-deriving new ones.

Component 15 §5's spoke table gets its "Lint model passes" row's description updated from a bare
`—` to something like "requires your own Anthropic API key" so the doc matches what actually
happens rather than reading as a feature nobody can ever reach.

## 5. Building the model call

The one real structural change. Today, `get_llm_client(request: Request) -> LlmClient` is a
FastAPI `Depends` dependency resolved *before* `run_skill`'s body runs, returning one process-wide
`AnthropicClient` built from the site's own key. `Depends` dependencies resolve ahead of the route
body's own auth logic (`gw.authenticate(...)` is called manually, inside `run_skill`, not injected)
— so a dependency that needs "which user is this and do they have a key" cannot itself be a
directly-injected `LlmClient` without breaking the existing refusal ordering (unknown-skill 404,
then auth 401/403, then argument/size checks, then the plan gate) that several tests already pin.

The fix: `get_llm_client` becomes a factory, injected via `Depends` as before but returning a
callable rather than a client:

```python
LlmClientFactory = Callable[[m.User], LlmClient]

def get_llm_client_factory(request: Request) -> LlmClientFactory:
    def build(user: m.User) -> LlmClient:
        ciphertext = user.anthropic_api_key_ciphertext
        assert ciphertext is not None  # _check_plan already refused otherwise
        api_key = decrypt_secret(ciphertext, request.app.state.settings)
        return AnthropicClient(api_key)
    return build
```

`run_skill` calls `llm = llm_factory(user)` once `_check_plan` has already confirmed a key exists,
immediately before `_run_passes`. No per-user client is cached anywhere — a fresh one is built and
discarded each call, so a decrypted key never outlives the request that needed it. Tests override
`get_llm_client_factory` (`app.dependency_overrides[get_llm_client_factory] = lambda: lambda user: fake_llm`)
in place of today's direct-client override.

## 6. Billing and the ledger

The site spends nothing on these calls anymore — Anthropic bills the caller directly. So `_quote()`
(refuse-before-spend if no price is configured) and the two `ledger.record()` calls (input/output
token rows) are skipped entirely for BYOK-powered runs; recording a dollar figure the site never
paid would misstate what `/api/usage` shows. The `Job` row (kind, status, timing) is still written
exactly as today — that's operational/audit history, not a cost record, and stays useful regardless
of who paid for the tokens.

## 7. What's explicitly out of scope here

- The dual-auth fix (accepting a session cookie, not just a platform API key, on
  `run_skill`/`concept-abstract-mini`) — already called out in the donations design doc as Part B's
  job. This document's changes are auth-mechanism-agnostic; whichever auth Plan 3 wires up still
  reaches the same `_check_plan`.
- `/api/contribute` itself, and anything about the community directory or moderation queue — Plan 3.
- A UI for the three showcase skills beyond the existing `account.astro` key field — no new pages.
- Key rotation reminders, expiry warnings, or usage-based alerts about the caller's own Anthropic
  spend — the site has no visibility into that spend at all once BYOK is in effect, by design.

## 8. Testing

- `test_anthropic_key.py` (new): save with a valid key (mocked Anthropic `models.list()` success)
  stores ciphertext + returns hint; save with an invalid key is 422 and stores nothing; delete
  clears both columns; the stored ciphertext is never equal to the plaintext key sent in.
- `test_skills.py`: rewrite `test_the_free_plan_has_no_model_passes` into
  `test_a_run_without_a_stored_key_is_refused` (403, `code: "missing_api_key"`); the five tests
  currently bypassing `_check_plan` via the temporary `_bypass_model_pass_gate` monkeypatch
  (`test_a_successful_run_writes_exactly_two_ledger_rows`, `test_a_failed_provider_call_bills_nothing`,
  `test_the_providers_own_error_text_never_reaches_the_caller`, `test_the_optimizer_runs_exactly_two_passes`,
  `test_input_at_the_cap_is_allowed`) switch to giving the test caller a real stored (fake-encrypted)
  key instead of bypassing the gate — the gate becomes exercisable again rather than needing a
  workaround. `test_a_successful_run_writes_exactly_two_ledger_rows` is renamed and its assertions
  change: no ledger rows are written anymore (§6), only the `Job` row.
- `test_a_model_with_no_price_is_refused_before_spending` is deleted — `_quote()` no longer runs
  on this path, so its premise is gone.
