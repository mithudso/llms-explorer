# Memory Log

## v0.1.0 - 2026-08-31
- **Active Task**: Repo optimization and mdb-tam standard bootstrap.
- **Status**: Clean baseline established.
- **Completed Work**:
  - Full deep code optimizer audit across `api`, `hub`, and `site`.
  - Fixed missing dependencies (`argon2-cffi`, `stripe`) in `api/pyproject.toml`.
  - Added `api.test` and `*.test` wildcard support to `DEFAULT_ALLOWED_HOSTS` in `api/explorer_api/settings.py`.
  - Fixed column type discrepancy in Alembic migration `20260901_a1b2c3d4e5f6_security_and_money_hardening.py` (`sa.Text()` vs `sa.String()`).
  - Fixed unused imports and line-length formatting issues across packages.
  - Verified 100% test pass rate across `api` (232 tests), `hub` (265 tests), `site` (139 tests), and site build (234 pages).
  - Bootstrapped standard workflow infrastructure, dotfiles, CI workflows, and documentation suite.

## v0.2.0 - 2026-09-04
- **Active Task**: Finish OAuth wiring for `/login/` (GitHub + Google sign-in) per `~/Documents/llms-oauth-handoff.md`, left by a prior background session that couldn't drive the browser.
- **Status**: OAuth blocker resolved. Both providers registered and verified end-to-end (GitHub) / at the redirect level (Google).
- **Completed work**:
  - Rebased local `main` (4 stray hub-refresh snapshot commits) onto `origin/main` (51 new commits) to unblock `git pull`; resolved 8 conflicts across two rebase passes by keeping the superset side. `main` is at `c4c985f`, 4 commits ahead of `origin/main`, not pushed.
  - Created GitHub OAuth App "LLMS-Explorer" (github.com/settings/applications/3837907) with prod + local-dev (`127.0.0.1:8790`) callback URIs — GitHub OAuth Apps now support up to 10 redirect URIs, so the handoff's "register a second app" workaround wasn't needed.
  - Created a new GCP project `llms-explorer` (the console defaulted to an unrelated pre-existing "Sticky Sites" project), configured its OAuth consent screen (External, app name LLMS-Explorer), and created a Web-application OAuth client with prod + local-dev redirect URIs.
  - Wrote all four `OAUTH_GITHUB_ID/SECRET`, `OAUTH_GOOGLE_ID/SECRET` into `api/.env` (gitignored, `chmod 600`). Never printed in chat per the handoff's guardrail.
  - Verified: both `/api/auth/oauth/{github,google}` now 307-redirect instead of 404; full browser click-through on `/login/` → GitHub consent screen → callback with a real authorization code.
  - **Lesson**: GitHub's new-format OAuth client IDs start with capital `Ov23…`, not `0v23…` — a screenshot/zoom read misidentified the leading `O` as a zero and an `l` as a `1`, causing a silent wrong-client_id 404 that looked identical to "provider not registered." Caught by reading the page's DOM text instead of the rendered glyphs. Anyone transcribing a GitHub OAuth client ID by eye should copy the DOM text, not read a screenshot.
  - **Known local-dev gap (unrelated to OAuth, not fixed)**: the API's local Postgres has no `explorer` role, so the OAuth callback's session-write step 500s locally (`asyncpg.exceptions.InvalidAuthorizationSpecificationError: role "explorer" does not exist`). OAuth itself is fully wired; this is a separate local Postgres setup task.
- **Changed files**: `api/.env` (new, gitignored), `site/.env` (new, gitignored, for the E2E check only), plus the rebase's file resolutions (`SNAPSHOT.txt`, `logs/memory-hub.md`, `logs/prompts-hub.md`, `hub/tests/test_llms_serve.py`, `hub/pyproject.toml`, `outputs/llms-full/manifest.json`).
- **Next steps**: push `main` (4 local commits) to `origin/main` if desired; set up local Postgres with an `explorer` role (or point `DATABASE_URL` at an existing instance) to actually complete a login round trip locally; consider committing a fixed `site/.env`-free note since it's gitignored by design.

## v0.3.0 - 2026-09-04
- **Active Task**: Push the OAuth work and make this machine's Postgres the canonical dev database "for everyone" (multiple developers) until the user hosts it on AWS.
- **Status**: Done and verified. `origin/main` is at `c4c985f`. Postgres on this machine (`m5`, Tailscale IP `100.93.168.117`) is the shared dev database, reachable over the tailnet.
- **Completed work**:
  - `git push origin main` — 4 commits landed clean.
  - User picked Tailscale as the network scope for "everyone" (already installed on this box, just not running — user started Tailscale.app themselves; no `sudo` was used).
  - `postgresql.conf`: `listen_addresses = 'localhost,100.93.168.117'` (explicit list, not `*` — this box also has a LAN IP `192.168.0.191` and a public WAN IP `98.24.164.36` that must NOT get a Postgres listener).
  - `pg_hba.conf`: added `host explorer explorer 100.64.0.0/10 scram-sha-256` — scoped to just the app's own role+database, not a blanket `all`/`all` rule, so the tailnet only ever gets scram-authenticated access to the `explorer` app data.
  - Generated a strong random password for the `explorer` role (the `.env.example` default `explorer`/`explorer` is fine as a same-machine-only local dev placeholder, but not once the role is network-reachable) and a real `SESSION_SECRET` (was the literal placeholder string from the repo). Created the `explorer` database, ran `alembic upgrade head` (3 migrations, clean).
  - Restarted `brew services restart postgresql@16` to apply the listener change; confirmed `pg_isready` succeeds on both `127.0.0.1:5432` and `100.93.168.117:5432`.
  - Full verification: restarted the API against the real DB, clicked through GitHub login on `/login/` again, and `GET /api/me` returned a real persisted `usr_…` account row — the whole stack works end to end now, not just the OAuth redirect.
  - **Found and fixed**: `explorer_api/routes/auth.py`'s OAuth callback did `RedirectResponse(auth.POST_SIGN_IN_PATH)` with the relative path `/account` — the browser resolves that against the *API's* origin, not the site's. Fixed by building an absolute URL against `settings.site_origins[0]`. `uv run --extra test pytest` — 253 passed, 1 pre-existing unrelated failure (`test_plans.py::test_the_seeded_rows_match_the_module`, confirmed via `git stash` that it fails identically without this change — seed-data drift from the background pipeline's commits, not touched).
- **Changed files**: `api/explorer_api/routes/auth.py` (the fix), `/opt/homebrew/var/postgresql@16/postgresql.conf`, `/opt/homebrew/var/postgresql@16/pg_hba.conf` (both outside the repo — infra, not tracked in git), `api/.env` (real Postgres password + session secret).
- **Next steps**: teammates who want to use this shared Postgres from another Tailscale device need `DATABASE_URL=postgresql+asyncpg://explorer:<password>@100.93.168.117:5432/explorer` in their own `api/.env`, plus the same `OAUTH_GITHUB_ID/SECRET` and `OAUTH_GOOGLE_ID/SECRET` — user distributes these out-of-band, never via git; the pre-existing `test_plans.py` seed-drift failure is still open, unrelated to auth/OAuth work.
