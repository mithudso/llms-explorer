---
title: "The API: what it is, and how to call it"
description: "LLMS-Explorer as a service, not a website: what a key buys you, the REST surface, the hosted MCP gateway, the llmsx CLI, and where the free tier ends."
section: reference
order: 8
sources:
  - docs/site/00-platform-design.md
  - docs/site/components/15-accounts-and-billing.md
  - api/explorer_api/gateway.py
  - api/explorer_api/plans.py
---

<!-- hand page · reference/api · 2026-09-05 -->

Everything else in this section describes the llms.txt standard. This page describes the
other half of the site: the hub's own tooling — lint, index, abstract, search — reached
through an account instead of a terminal.

## What you're actually buying

LLMS-Explorer is the concept-family-tree explorer with the hub's llms tooling hung off its
nodes: lint or optimize an llms file, turn notes into one, abstract a concept out of a
corpus, deepen it with a research wave, map its family. Reading is free everywhere on this
site, with no account and no key — the reference, the blog, the directory, the public
concept tree, and every served llms file (`/d/ /m/ /t/`). What a key buys is the tooling
that spends model tokens or GPU time on your behalf: linting with the model passes, semantic
search, indexing your own docset, publishing to the shared catalogue. One ledger records
every token that gets spent; the plan you're on decides how far it goes before you hit a
wall. See [Pricing](/billing/) for what each plan actually includes.

## Three ways in

**Web.** Sign in with a passkey, GitHub, or Google at [/login/](/login/), then
[/keys/](/keys/) to mint an API key and [/usage/](/usage/) to watch what it's spent.

**REST API**, at `api.llms-explorer.com`. A key is `lx_<prefix>_<secret>` — shown once at
creation, sent as a bearer token, scoped to what it's allowed to do:

| Scope | Grants |
|---|---|
| `read` | Queries within your quota; read your own artifacts |
| `run` | Create metered jobs — lint model passes, indexing, concept packs |
| `publish` | Contribute to the shared catalogue |

Routes worth knowing: `GET /api/usage` (ledger aggregates by component, model, day),
`GET /api/billing/plans` (the price table, no sign-in needed), `GET/POST/DELETE /api/keys`
(list, create with scopes, revoke). A metered call past your quota answers with a structured
error naming the plan that would lift the limit, not a bare 402.

**MCP**, hosted or local. The hub runs its own MCP server for tools you point at your own
machine — semantic search, docset indexing, concept-tree queries — and it's unauthenticated
by design, meant for `localhost` only. The **hosted** gateway is what puts that same tool
surface behind a key without exposing the hub process itself: it terminates the session,
resolves your key to an account, applies your plan's limits, and only then forwards the call
over loopback. Five things it enforces that a bare tunnel wouldn't:

1. **Some tools aren't hosted at all.** `hub_ask`, `hub_distill_run`, and the hub's own memory
   and corpus tools are refused by name before your key's scopes are even checked — refused
   with the same message an unknown tool gets, so the hosted surface can't be enumerated by
   trying things.
2. **Your docsets are walled.** A docset key beginning `u_` belongs to exactly one account;
   arguments are checked going in and results are filtered coming back.
3. **A path is never just an argument.** Anything that names a file on the hub's own
   filesystem is resolved inside your own store — an unconfined path is a local-file-read
   primitive, so escaping your store is refused.
4. **One limit, one place.** Every quota comes from the same plan table `/billing/`
   describes; nothing is hardcoded in the gateway.
5. **A ledger row is written once**, after the hub confirms the work happened — not before
   (billing a failure) and not twice.

Third-party full text is never served hosted, at any tier — a mirrored `llms-full.txt` you
don't own stays on the hub, and the concept surface links out to the source instead.

**CLI**, `llmsx`: `llmsx login`, `llmsx keys create --scopes read,run`, `llmsx usage
[--month]`, `llmsx jobs <id>`. See [Downloads](/downloads/) for install.

## The free tier's semantic search

The free tier's semantic and hybrid search is a fixed 16-document demo, rate-limited and not
billed — it's there to show what the retrieval looks like, not to serve your own corpus.
Indexing your own docset, and querying it, both need a paid plan. The recorded three-leg
run (keyword, vector, the fusion of both) is at [/demo/](/demo/) if you want to see the
retrieval quality before paying for it.

## What's deterministic and free even with a key

Not every tool call spends a token. Lint's deterministic passes — the ones that don't run a
model — are free and unlimited-frequency-within-quota on every plan; only the *model* passes
(P4/P8/P12) are metered. Keyword search (FTS5, no embedding call) is free up to a daily
count that scales with your plan. The pattern throughout: cheap path first, deterministic
before model, local Ollama before Claude — every metered step has a free deterministic
shadow, and the lint that gates this site's own published files is exactly that free path.
