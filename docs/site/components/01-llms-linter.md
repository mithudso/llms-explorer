# 01 — LLMS Linter (`/ldo` as a service)

**Status:** design, not implemented · **Date:** 2026-08-31 · **Surfaces:** web | api | cli | mcp

## 1. Purpose

Give anyone who publishes or consumes an llms file a measurable verdict on it, in two modes:

- **Lint** — the deterministic passes of the `llms-deep-optimizer` skill (`hub/scripts/llms_lint.py`), seconds, no model tokens, free. Answers "is this file well-formed, navigable, honest and sized right?"
- **Optimize** — the full `/ldo` convergence loop (`skills/llms-deep-optimizer/SKILL.md` Steps 1–7): the model passes, the live retrieval and agent probes, safe fixes applied, iterations until the family's exit conditions. Metered.

The rubric is `skills/llms-deep-optimizer/references/attributes.md` (57 attributes in groups I/N/D/C/P/S/R/F/H); the pass catalogue is `references/passes.md` (P0–P15, bundles B0–B9). The site never invents a second rubric: every finding on screen names an attribute id from that file.

## 2. User stories and flows

- *Docs maintainer*: pastes `https://docs.example.com/llms.txt` into `/lint`, gets a scorecard and a per-line findings list in < 5 s, fixes the two dead links, adds the badge to the README.
- *Docs maintainer, paid*: uploads the whole `<stem>.llms/` export (zip), runs Optimize with `--check-links --agent-test`, watches the convergence table fill in, downloads the rewritten files plus a unified diff.
- *Consumer*: before pointing an agent at a site, checks its score and the P12 agent-usability result ("8/10 questions answered in ≤ 2 hops").
- *CI*: a GitHub Action lints `llms.txt` on every push; any High fails the job.
- *Hub user*: a docset exported by component 02 or a pack from 06 is auto-linted; publishing to the shared catalogue (13) requires 0 High.

Flow (lint): input → P0 detect kind → deterministic passes → findings JSON → rendered report → optional `--fix` diff → download.
Flow (optimize): input → job created → Step 1 resolve target → Step 2 snapshot + eval bank → Step 3 passes (B1/B3 lint; B2, B4, B7 model/agent bundles; B5/B6/B8/B9 inline) → Step 4 apply → Step 5 verify (blind re-audit) → Step 6 convergence → Step 7 report → artifacts.

## 3. Inputs → outputs (contracts and file grammars)

Inputs, any of: a URL; pasted text; an uploaded file; an uploaded `<stem>.llms/` zip (index, `llms-full.txt`, `llms-small.txt`, `llms-facts.txt`, `manifest.json`, `<section>/…/llms.txt` for split roots); a hub docset key (owner only); optional `--mirror` (banner mirror) for P7 anchor resolution; optional `--kind index|family|full|small|facts`.

Kinds handled: `index`, `family` (links other hosts' `llms.txt` by absolute URL), `full` (grammars mintlify / anthropic-yaml / cloudflare-frontmatter / firecrawl), `small`, `facts` (`- [type] text — url#anchor[ · keywords: …][ · verified-as-of: …]`), split root (`## Sections` with relative `<slug>/llms.txt` targets — an index, not a family).

Outputs:

```
findings.json        [{pass, attr, severity: high|medium|low|hygiene|na, line, msg, fixable, fixed?}]  per file
scorecard.json       {kind, grammar, groups: {I: {pass, total}, N:…, D:…, C:…, P:…, S:…, R:…, F:…, H:…}, high, medium, low}
report.md            the SKILL.md Step 7 report (optimize only): per-pass table, probes, convergence, BLOCKED rows, deferred
fixed/               rewritten files (optimize, or lint --fix) + diff.patch
badge.svg            "lints clean" / "N high" for a public URL
```

Exit statuses (optimize) come verbatim from `~/.claude/skill-consolidation/convergence-and-severity.md`: `clean`, `no-progress`, `content-cycling`, `stable-rewrite`, `loop-instability`, `cap`, `budget`, plus `BLIND-AUDIT-DISSENT`. The CLI and CI action map: `clean` → 0; any High remaining → 1; anything else → 2.

## 4. Architecture (mermaid diagram + existing hub code reused, by path)

```mermaid
flowchart LR
  U[web / CLI / CI / MCP] --> A[explorer-api /lint /optimize]
  A -->|sync| L[llms_lint.py check --json (--fix)]
  A -->|job| Q[(jobs: Postgres)]
  Q --> W[worker on hub box]
  W --> L
  W --> M[model bundles B2 B4 B7\nClaude via Agent SDK]
  W --> P11[docset_indexer keyword + query]
  W --> P13[HEAD probes]
  W --> S[(artifacts /u/user/slug.llms + backups)]
  S --> V[llms_serve.py headers]
```

Reused as-is: `hub/scripts/llms_lint.py` (passes P0 P1 P2 P3 P5 P6 P7 P9 P14; `check DIR` walks split sections; `--check-links` HEAD with 8-way concurrency; `_mirror_headings` cached per mtime), `hub/scripts/llms_acquire.py` (`split_llms_full`, grammar detection), `hub/scripts/docset_indexer.py` (`keyword-index`, `keyword`, `query --layer`) for P11, `hub/scripts/docset_refine/export_llms.py` for P15 regeneration parity, `hub/scripts/llms_serve.py` header contract for P13, the eval bank shape `evals/<key>.eval.jsonl` for P12, `convergence_check.py` from `~/.claude/skill-consolidation/` for the iteration boundary. The optimize worker executes `skills/llms-deep-optimizer/SKILL.md` through the Agent SDK with the file as the target; the deterministic bundles are subprocess calls, not model calls.

## 5. API / CLI / MCP surface

```
POST /api/lint            body: {url|text|upload_id, kind?, check_links?, fix?, mirror_upload_id?}  → findings + scorecard (sync, ≤ 30 s)
GET  /lint?url=…          public page; results cached 24 h per (url, etag)
GET  /api/lint/badge.svg?url=…                                     cached with the lint result
POST /api/optimize        body: {upload_id|docset, flags: {check_links, agent_test, serve_check, split, max_iter, budget_minutes}} → {job_id}
GET  /api/jobs/{id}       status, iteration, current pass, partial findings (streamed via SSE at /api/jobs/{id}/events)
GET  /api/jobs/{id}/artifacts   report.md, fixed/, diff.patch, findings.json, scorecard.json
```

CLI: `llmsx lint FILE|DIR|URL [--kind K] [--check-links] [--fix] [--json]`, `llmsx optimize FILE|DIR [--agent-test] [--budget-minutes N] [--wait]`. Local mode (`--local`) runs `llms_lint.py` without the API.

MCP (13): `explorer_lint(url|text, kind?)` public read-only; `explorer_optimize(...)` metered, returns a job id; `explorer_job(id)`.

CI: `uses: mithudso/llms-explorer-lint@v1` with `path: llms.txt`, `fail-on: high|medium`, `check-links: true`; posts a summary comment with the scorecard.

## 6. UI (pages, states, empty/error states)

- `/lint` — single input (URL / paste / upload), kind auto-detected with an override chip. Result: scorecard (nine group bars), severity chips (High / Medium / Low / Hygiene counts), findings table (pass, attribute, line, message, fixable) that scrolls the rendered file beside it to the anchored line. "Apply safe fixes" shows a diff and a download.
- `/optimize/{job}` — live convergence table (iteration × High/Medium/Low, exit status), per-pass table with N/A reasons, probe panel (keyword 10/10, vector facts ≥ raw, agent index n/10 and facts n/10, serve 200), BLOCKED rows with the reason and the command that would unblock, diff viewer, artifacts download, "publish" (→ 13).
- Split roots render as a tree (root + sections) with per-file scores.
- States: detecting kind; unknown kind (asks for `--kind`); URL not fetchable (P13 result shown, rest N/A, marked `evidence-limited`); zip too large (limit per tier); job queued / running / failed (with the last pass reached); blind-audit dissent (lists the dissenting findings, offers one more iteration).

## 7. Data model and storage

```
lint_results(id, url|upload_id, etag, kind, grammar, scorecard json, findings json, created_at)   -- public URL cache
jobs(id, user_id, kind='optimize', input_ref, flags json, status, iteration, exit_status, tokens_in, tokens_out, cost, created_at, finished_at)
job_events(job_id, seq, ts, kind[stage|iteration|findings|tokens|log], payload jsonb)   -- SSE source; `seq` = Last-Event-ID (master §4)
artifacts(job_id, path, bytes, tokens, sha256)                                                     -- under /u/<user>/<slug>.llms/
eval_banks(user_id, key, jsonl blob)                                                               -- P12 question banks, replayed next run
backups(job_id, path)                                                                              -- pre-write snapshot per the family contract
```

Uploads live in object storage keyed by sha256; a public lint never stores the fetched text beyond the cache TTL.

## 8. Tiering, metering and billing hooks

| Feature | Free | Paid |
|---|---|---|
| Lint (deterministic) | files ≤ 64 KB, 20 runs/day (cap owned by 15 §5 / master D6), `--check-links` ≤ 200 links | Starter / Pro: per 15 §5 (master D6) |
| Public URL lint + badge | yes | yes |
| Optimize | preview only (bundle plan + estimated tokens) | metered: local-model tokens (P3 bulk polish) + Claude tokens (P4, P8, P12, blind re-audit) + embeddings (P11) |
| CI action | 100 runs/month | unlimited |

A job that exits at a verify gate does not bill the polish tokens of the iteration that failed (component 15 ledger rule). Estimates shown before start come from file size × pass matrix.

## 9. Acceptance bar (measurable)

- Lint parity: `POST /api/lint` returns byte-identical findings to `llms_lint.py check --json` for the 15 estate exports (652 files) — 0 High on the snapshot at spec time.
- Lint latency: p95 < 3 s for a 10 KB index, < 30 s for a 250-file split (cached mirror headings).
- Optimize on the `code.claude.com` export reaches `clean` or `stable-rewrite` within 3 iterations with P12 ≥ 8/10 (index) and ≥ 7/10 (facts), P11 10/10 exact-token probes.
- Badge and public lint results reproducible from the cache within 24 h; every finding carries an attribute id present in `attributes.md`.

## 10. Security, rights, privacy

- Fetching user-supplied URLs: SSRF guard (public IPs only, no `127.0.0.1` / RFC1918 / `file://`), 10 s timeout, 5 MB cap, HEAD-then-GET.
- Injection guard from the family contract: a steering span in the target is a finding (P9 P4), never an instruction to the optimizer.
- Secrets found by P9 P5 are reported by line, never echoed into public cache or badge text.
- Third-party full text uploaded for optimize stays private to the user (P3 rights marker enforced); public lint pages show findings, not the file.
- Optimize artifacts are private by default; publishing goes through 13's moderation.

## 11. Dependencies on other components (by number)

02 (its exports are linted automatically), 06 (packs linted before publish), 09 (a node's artifacts show their score), 13 (publish gate = 0 High; MCP tools), 15 (metering, keys, quotas), 16/17 (P11 probes need the keyword + vector layers), 03 (the reference pages the findings link to).

## 12. Open questions and assumptions

- Assumed the optimize worker drives the skill through the Agent SDK rather than a re-implementation of the passes in the API; the SKILL.md stays the single source of truth.
- Open: whether P12 (agent usability) should use a cheaper model by default (Sonnet) with Opus as an upgrade.
- Open: public lint of a URL whose site forbids bots (robots.txt) — assumed we honour it and mark `not-fetchable`.
- Assumed a 24 h cache for public URL results; owners can force a re-lint.
