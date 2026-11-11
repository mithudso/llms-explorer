---
title: "The API: what it is, and how to call it"
description: "Accounts, scoped API keys, the hosted MCP gateway, local tools, and the limits of the donation-supported free plan."
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

## Accounts and donations

LLMS-Explorer publishes reference pages, articles and a concept tree that you can read
without an account. Concept facts are available through the [context index](/context/)
and its downloads. Archived source reports and third-party full-text mirrors are not
public site content.

The current implementation has one **free**, donation-supported plan. An account adds
scoped API keys and the operations that plan permits; a key does not unlock a paid tier
or every tool in the local hub. [Donate](/donate/) supports the project through one-time
or monthly donations via Stripe. Donations do not change the plan's permissions.

Implementation checked on 2026-11-11. The limits below describe the repository's plan
and gateway policy; a running deployment may also be unavailable or rate-limited.

## Three ways in

**Web.** Sign in with a passkey, GitHub, or Google at [/login/](/login/), then
[/keys/](/keys/) to mint an API key and [/usage/](/usage/) to watch what it's spent.

**REST API**, at `api.llms-explorer.com`. A key is `llmsx_<prefix>_<secret>` — shown once at
creation, sent as a bearer token, scoped to what it's allowed to do:

| Scope | Grants |
|---|---|
| `read` | Queries within your quota; read your own artifacts |
| `run` | Create metered jobs — lint model passes, indexing, concept packs |
| `publish` | A contribution scope; the current free plan does not enable direct publication |

Routes worth knowing: `GET /api/usage` for your usage, `GET /api/keys` to list your
keys, `POST /api/keys` to create one with scopes, and `DELETE /api/keys/<id>` to revoke
one. These account routes require a signed-in session. The gateway separately accepts
an API key as a bearer token. Quota failures do not imply that a paid upgrade is available.

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
3. **File arguments are confined.** Hosted tools that accept a file path must resolve it
   inside your own store; paths that escape it are refused.
4. **Plan quotas have one table.** Feature quotas come from the plan table. The gateway
   also applies its own request-rate and resource limits.
5. **A ledger row is written once**, after the hub confirms the work happened — not before
   (billing a failure) and not twice.

Third-party full text is never served hosted, at any tier — a mirrored `llms-full.txt` you
don't own stays on the hub, and the concept surface links out to the source instead.

**Local CLI**, `llmsx`: browse the tree with `llmsx tree`, open the terminal workbench
with `llmsx explorer`, or download public packs with `llmsx context`. It is a separate
local interface; it does not implement `login`, `keys`, `usage` or `jobs` subcommands.
See [Downloads](/downloads/) for installation and the [user guide](/explorer/guide/) for
the workbench.

## The free tier's semantic search

Semantic and hybrid search on the free plan is limited to the fixed 16-document demo,
rate-limited and not billed. It does not provide semantic querying of your own corpus.
The plan allows one index of up to 20,000 units and 0.2 GB of storage; hosted indexing
also requires a `run` key and inputs confined to your own store. Keyword queries have a
200-per-day allowance. The [recorded demo](/demo/) shows keyword, vector and fused retrieval;
it is an example, not a guarantee for a different corpus.

## What's deterministic and free even with a key

Deterministic linting and keyword search require no generation model. The hosted model-pass
showcase requires your own Anthropic API key and limits input to 65,536 bytes and 20 model
passes per day. These checks differ from local deterministic scripts and from the gateway's
semantic-operation policy. The site's build uses deterministic linting; passing it does not
establish that model, retrieval or live-agent checks ran.
