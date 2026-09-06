# Donations and the community directory — design

**Status:** design, approved · **Date:** 2026-09-06 · **Surfaces:** web | api
**Authority:** amends component `15-accounts-and-billing.md`; extends `05-conceptual-vs-proprietary.md`
and `09-concept-family-tree-explorer.md`, both otherwise unchanged.

## 0. Why this doc exists

The site was going to be a metered product with a Free/Starter/Pro ladder. The owner decided,
after that billing stack was fully wired and tested against a live Stripe sandbox, to make the
site free and support it through voluntary donations instead — and to give it a second purpose:
a human-readable, community-contributed directory of "llms subjects," built by letting signed-in
visitors submit new ones.

Two independent pieces of work follow. They share nothing except both touching `api/.env`-adjacent
billing code, so they are specified together but may be implemented and shipped in either order.

## 1. Part A — Billing → donations

### 1.1 What changes

- `/billing/` (the pricing page) is deleted, along with `site/tools/gen_plans.py` and
  `site/src/data/plans.json` — there is no tier table left to source from a build.
- A new `/donate/` page: a "Support this project" page with a few preset amounts, a custom-amount
  field, and a one-time/monthly toggle. It calls Stripe Checkout directly with inline
  `price_data` — donations are arbitrary amounts, so there is no `Product`/`Price` to pre-create
  the way the (now-removed) plan tiers needed one.
- `api/explorer_api/plans.py` collapses to one plan. `PLAN_ORDER = ("free",)`; `PLANS` keeps only
  the `free` row, with its quotas **unchanged from today's Free tier** — this is now every
  account's limit, not an entry tier. `upgrade_target`/`upgrade_url` and `BILLING_URL` are deleted
  along with every call site (there is nothing left to upgrade to).
- A migration drops the `starter`/`pro` rows from the `plans` table and tightens
  `ck_plans_plans_id` (`users.plan_id`'s check constraint) to `id = 'free'`. `users.plan_id`
  itself stays — every account still has one, it can just only ever be `'free'`.
- `api/explorer_api/billing.py` loses `start_checkout` (plan-based) and the subscription-specific
  webhook handling (`customer.subscription.*`, the plan-change logic in
  `_handle_subscription`/`_plan_for_price`). It gains `create_donation_checkout(amount_cents,
  currency, interval)` — one-time (`mode="payment"`) or monthly (`mode="subscription"` with
  `recurring={"interval": "month"}` on the inline price). A new `Donation` model/table records
  `id, user_id (nullable — donations don't require an account), amount_usd, interval
  ("once"|"month"), stripe_checkout_session_id, stripe_subscription_id (nullable), status,
  created_at`. The webhook handler's `HANDLED_EVENTS` set drops the subscription events and keeps
  `checkout.session.completed` (record the donation) and, for recurring donations,
  `invoice.paid`/`invoice.payment_failed` (mark it lapsed on failure — no grace-period logic is
  needed since nothing is gated behind it).
- `/api/billing/plans` and `/api/billing/checkout` (plan-based) are removed. A new
  `POST /api/donate/checkout` takes `{amount_usd, interval}` and returns the same
  `{url, session_id}` shape `CheckoutOut` already has.
- The Stripe test-mode Products/Prices created earlier this session (`LLMS-Explorer Starter`,
  `LLMS-Explorer Pro`) are left in place in Stripe, simply unused — deleting them isn't necessary
  and Stripe doesn't allow deleting a Price with a subscription history anyway.
- Nav: remove "Pricing", add "Donate".

### 1.2 What does not change

- Accounts, sign-in (passkey/OAuth), API keys, usage/ledger pages — all untouched. The ledger
  keeps recording spend for cost visibility even though nothing is billed against it; that was
  always separable from the tier system (component 15 §1 already frames the ledger as the record,
  Stripe as what turns it into money — donations just mean nothing turns it into money anymore).
- Every quota in `plans.py` keeps its current Free-tier number. No feature that was free stays
  gated differently; no feature that was paid-only becomes newly free beyond "no more upsell path
  exists" (`publish` was already `False` on Free and is not touched by this doc — see §2.4).

## 2. Part B — the community directory ("Contribute a subject")

### 2.1 What already exists and is reused unchanged

- **`/tree/`** — the concept tree is already the browsable, human-readable directory of subjects.
  No new information architecture is needed; contribution adds *to* it.
- **`api/explorer_api/moderation.py`** (871 lines) and **`/api/proposals`** — a complete
  merge-back system: submit a patch (`{"ops": [{"op": "add"|"update"|"remove", "node": {...},
  "concept": "..."}]}`, ≤200 ops) against a named `tree_sha`, run it through `llms_lint.check`
  (a High finding or missing provenance banner auto-rejects with the findings attached, as a 201
  not a 4xx — the rejection is itself the record), score any surviving conflict against the
  6-rung precedence ladder, and land it in a moderator queue (`GET /api/proposals?scope=queue`)
  gated by `moderation.MODERATOR_ENV`, an env-var allow-list of verified emails. Accept applies
  the patch to the tree file atomically, guarded by the sha it expected to overwrite (a race is a
  409, never a silent overwrite).
- **`POST /api/skills/concept-abstract-mini/run`** — a bounded, single-to-few-pass demo of the
  full `/lca` (llms-concept-abstractor) skill: caps input at `MAX_INPUT_CHARS = 4000`, requires
  the `run` scope, meters through the same ledger every other metered surface uses, and returns
  the generated llms-family text in the response body (it does not persist anything today).

### 2.2 What's new

**A. A read path — the concept-pack reader**

Today a `/tree/<slug>/` page is metadata only: parent, children, source/concept counts, aliases.
The actual researched content for a concept — summary, facts grouped by facet, related concepts,
sources — lives in a separate "concept pack" (`llms.txt`/`llms-full.txt`/etc. under the hub's
`llms-concepts/<slug>.llms/`) that no page renders as prose today; it's servable raw text only,
the same problem `/family/` solves for this site's own llms family.

New route `/tree/<slug>/read/` (only linked from the node page when a pack exists for that slug):
renders the pack's summary, each facet as an `<h2>` with its facts as a list (each fact keeps its
source anchor as a footnote-style link), and "Related concepts" as links — to that concept's own
`/tree/<other-slug>/read/` when it has a pack, to `/tree/<other-slug>/` otherwise.

Sourced from a new `site/tools/gen_concepts.py`, following `gen_demo.py`'s precedent exactly: it
is the one generator besides `gen_demo.py` that reads the live hub (`~/.global-ai-hub/llms-concepts/`),
so — like `gen_demo.py` — it is **hand-run, not CI**, and its output (`src/data/concepts/<slug>.json`,
one file per pack that exists at generation time) is committed. `tree.json` nodes gain an optional
`hasPack: boolean` field (set by `gen_tree.py` when a matching pack directory exists) so the node
page knows whether to link to `/read/` without the reader page's own generator needing to run
first.

**B. A write path — `POST /api/contribute`**

One new endpoint, one atomic server-side flow, session-cookie authenticated (see §2.3 for why that
needs a small fix elsewhere):

1. Validate: signed in, `concept` (1–200 chars) and `text` (≤4000 chars, reusing
   `skills.MAX_INPUT_CHARS`) present, `concept` does not already name a node in the current tree
   (V1 is additions only — see §2.4).
2. Run the same bounded pass `concept-abstract-mini` runs (reusing its policy/prompt/pricing —
   this is a call into the same internal function `run_skill` calls, not a second implementation).
3. Persist the output as a new artifact under the contributor's own store — this is new: nothing
   in `explorer_api.artifacts` writes today, it only resolves/reads/serves. Add
   `artifacts.write(stores_root, user_id, slug, relative, content) -> Path`, mirroring `resolve`'s
   existing path-safety checks (§2.5 covers why this matters).
4. Build the patch: `{"ops": [{"op": "add", "node": {"concept": <concept>, "parent": <parent or
   null>, "slug": <slugified concept>, "llmsFile": <the new artifact's served URL>, "state":
   "researched", "sourcesCount": 1, "conceptsCount": <from the pass output>, "researchedAt":
   <today>}}]}`.
5. Call `moderation.submit(session, user, tree_sha=<current tree's sha, read server-side — the
   client never supplies it, so this flow can't race a stale-sha 409>, patch=..., artifact_ids=[the
   new artifact's id], summary=<first ~200 chars of the pass output or a caller-supplied one-liner>)`.
6. Return the proposal (same `ProposalPublic` shape `/api/proposals` already returns) plus the raw
   pass output, so the contribute page can show "here's what was generated" immediately without a
   second round trip.

A failure at step 2 (provider error) or step 5 (lint rejection, which is itself success at the
HTTP layer — see §2.1) are the only two branches the client needs to distinguish; everything else
is the existing `gw.GatewayRefusal` → structured-error path every metered surface already uses.

**C. Three new pages**

- **`/contribute/`** — signed-in only (a signed-out fallback matching `keys.astro`'s pattern):
  a "Subject name" field, an optional "Parent concept" field (free text against the existing tree —
  V1 does not need a full picker), a textarea, and a file input whose `change` handler reads the
  file client-side (`FileReader.readAsText`) into that same textarea rather than uploading it
  separately — `concept-abstract-mini` takes text either way, so there's no reason for a second
  upload code path. Submits to `POST /api/contribute`, shows the returned pass output and the
  proposal's status inline.
- **`/proposals/`** — "my proposals": calls the already-existing `GET /api/proposals?scope=mine`,
  lists each with its status, lint verdict summary, and decided-at date. Same island pattern as
  `keys.astro`.
- **`/moderate/`** — moderator-only (same `MODERATOR_ENV` allow-list the API enforces; a
  non-moderator's `GET /api/proposals?scope=queue` call 403s and the page shows a plain "you are
  not a moderator" message, never a broken table). Lists the pending queue with each proposal's
  patch, lint verdict, and Accept/Reject buttons calling the existing
  `/api/proposals/{id}/accept|reject`.

### 2.3 One existing-code fix: dual auth on the skill run path

`run_skill` (and therefore the function §2.2.B's new endpoint calls into) currently requires an
`Authorization: Bearer` API key — `principal.anonymous` is a hard 401, with no session-cookie path.
Every other browser-facing authenticated surface on this site (`artifacts.py`'s `optional_user`,
`keys.astro`, `usage.astro`, the new `/api/billing→donate/checkout`) accepts the session cookie
`current_user`/`optional_user` already provides. Forcing a wiki contributor to first create and
paste in an API key before they can submit a paragraph of text is real, avoidable friction.

Fix: extract the shared "resolve identity from either the session cookie or a bearer key" logic
`artifacts.py`'s `optional_user` already implements into something both modules call, and have
`gw.authenticate` (or the specific call site in `run_skill`) accept a `CurrentUser`-shaped identity
alongside the existing key-based `principal`. This is a small, targeted fix to one function's
identity resolution — not a new auth system — and it only changes *who counts as identified*, not
any of `run_skill`'s scope/quota/pricing logic, which stays exactly as strict.

### 2.4 Explicitly out of scope for this iteration

- **Editing or adding facts to an existing subject.** `moderation.apply_patch`'s `update` op exists
  and is untouched, but nothing in this doc's new UI or `/api/contribute` produces one — V1 is
  `add` only. A future iteration would need a real design for translating a simple "add this fact"
  form into a structured node update, which is materially more UI/UX work than adding a leaf.
- **Full-size document / whole-corpus uploads.** `concept-abstract-mini`'s 4,000-character cap is
  reused as-is. A real `/lca` run (multi-pass, convergence loop) cannot execute inside one HTTP
  request; supporting it would mean async job infrastructure (queue the upload, run the full
  pipeline out of band, notify on completion) that does not exist today and is a separate project.
- **A rich parent-concept picker, or renaming a proposal after submission.** The `parent` field is
  free text checked server-side against existing concept names; picking a bad name is exactly the
  case the existing lint-and-moderator gate exists to catch.
- **Anonymous contribution.** `/api/contribute` requires a signed-in account, consistent with the
  rest of the moderation system (`moderation.submit` already takes a `User`, not an optional one).
- **Changing the `publish` plan-quota flag.** It's unrelated to this flow — `moderation.submit`
  never reads `plans.quota(..., "publish")`, confirmed by grep; every signed-in account can already
  submit a proposal today regardless of plan, and that stays true after Part A's single-plan
  collapse.

### 2.5 Security notes carried over from the systems being reused

- **Artifacts are named by id, not by path** (`gateway.py`'s rule 3, already enforced for reads).
  The new `artifacts.write` must resolve the destination the same way `artifacts.resolve` does —
  inside the caller's own store, nothing that escapes it — so a malicious `concept`/slug value
  can't become a path-traversal write.
- **Submissions are data, never instructions** (`moderation.py`'s own stated decision, already
  enforced for proposal `summary`/patch text via the hub's steering regexes at intake). The new
  `/api/contribute` text field and the model pass's output both flow through the exact same intake
  path proposals already use — no new trust boundary is introduced, but it must not be
  accidentally bypassed by treating `/api/contribute`'s inputs as pre-validated because they come
  from a "simpler" form.
- **A failed lint gate stays a 201, not a 4xx** — this doc's new endpoint inherits that from
  `moderation.submit` directly and must not wrap it in a try/except that turns a real, reviewable
  rejection into an opaque error.

## 3. Testing

- **API:** migration test (plans table has exactly one row after upgrade); `plans.py`
  unit tests updated for the single-plan shape; donation checkout tests (preset/custom amount,
  one-time vs monthly, webhook recording a `Donation` row, webhook failure marking one lapsed);
  `/api/contribute` — happy path (artifact written, proposal created, pending), lint-rejection
  path (201 with findings), name-collision path (422), over-cap path (422, matching
  `concept-abstract-mini`'s existing message), unauthenticated (401 with session-cookie identity
  now accepted, still 401 with neither cookie nor key), quota-exceeded (matches
  `concept-abstract-mini`'s existing `_check_plan` behavior since it's the same call).
- **Site:** `gen_concepts.py` output committed and read correctly by the reader page;
  `test_scaffold.py`/`test_account_pages.py`-style tests for the three new pages (nav present,
  signed-out fallback, island fetch pattern, no user data baked into the static build); nav no
  longer links `/billing/`, links `/donate/` and `/contribute/`; `/moderate/` page's non-moderator
  fallback.

## 4. Open items for the implementation plan to sequence

Part A and Part B are independent and can ship in either order or in parallel. Within Part B, the
reader page (§2.2.A) has no dependency on the write path (§2.2.B/C) and could ship first on its
own, giving the directory a "read" half before the "contribute" half exists.
