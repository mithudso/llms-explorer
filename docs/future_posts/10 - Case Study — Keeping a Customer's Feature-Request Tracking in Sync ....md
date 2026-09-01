# Case Study — Keeping a Customer's Feature-Request Tracking in Sync with an Agent

**How Claude Code (browser automation + MCP) and Glean kept Goldman Sachs feature requests aligned across Aha!, a Monday.com board, and a Google Sheet — idempotently, with no API tokens and no destructive writes.**

*Audience: TAMs and PMs. This is an engineering case study, not marketing. Figures marked `[est.]` are representative/dry-run numbers, not a guaranteed production tally.*

---

## TL;DR

Goldman Sachs' (GS) feature requests lived in three places that drifted apart: **Aha!** (the PM source of truth), a **Monday.com board** the account team worked from, and a **Google Sheet** the customer and AE reviewed. Reconciling them by hand was slow, error-prone, and always stale. We had **Claude Code** drive the whole loop end-to-end — read the ~77 GS ideas out of Aha!, enrich each from its detail page, then **idempotently upsert** them onto the Monday board and **fill only the empty cells** of the sheet. Glean located the assets and account context. The run is **read-before-write and non-destructive by design**: it never deletes, never overwrites populated data, uses the browser's own session instead of a pasted token, and treats every fetched value as data rather than instructions. The result is a one-command reconciliation that previously took a person the better part of a day.

---

## Problem & context

A high-touch account like GS generates feature requests faster than any one system captures them cleanly:

- **Aha! ideas** are where PMs triage and own requests — the canonical state (status, assigned PM, impact, promotion-to-feature).  
- A **Monday.com board** ("Product Tracker - Goldman Sachs", board `6239287173`) is where the account team tracks and discusses those requests operationally.  
- A **Google Sheet** ("FeatureRequest_GS" tab) is the shared surface the customer and account executive actually look at.

Each system is authoritative for *something* and stale for everything else. When a PM moved an Aha! idea from *In Development* to *Shipped*, that change did not reach the board or the sheet until someone noticed and hand-edited two more places. Status labels diverged (Aha!'s vocabulary ≠ the sheet's vocabulary), PM assignments went missing, and nobody could trust the customer-facing sheet without re-checking Aha! first. The manual reconciliation was the kind of repetitive, careful, cross-tab work that humans do slowly and agents do well — *if* the guardrails are right.

---

## Architecture

Claude Code acted as the orchestrator, with **Glean** used up front to find the Aha! report, the board, and the sheet and to pull surrounding account context. Everything downstream ran through the agent's Chrome browser automation and MCP tooling against the user's already-authenticated sessions.

| Layer | System | Access pattern |
| :---- | :---- | :---- |
| Source of truth (read-only) | Aha! shared report + per-idea detail pages | Browser fetch of the GS-filtered report; parse the iframe table, then fetch each `FF-I-####` detail page |
| Operational tracker (read/write) | Monday board `6239287173` | Internal GraphQL `POST /v2/` with `x-csrf-token` + `credentials:'include'` — **no pasted API token** |
| Customer-facing surface (read/write) | Google Sheet "FeatureRequest_GS" | Read via clipboard-copy of the canvas grid (gviz is OAuth-gated); write only empty cells |
| Discovery & context | Glean | Locate assets, pull account context |

Two design choices in this table carry most of the safety story. First, **Monday writes use the browser's own CSRF token and session cookies** rather than a long-lived API token — nothing secret is pasted, stored, or logged. Second, the **sheet is read by copying the rendered grid to the clipboard**, because the clean programmatic path (gviz) sits behind an OAuth grant we deliberately chose *not* to request.

---

## Sync logic

The run is a single pass with a clear pipeline:

1. **Build the roster.** Open the Aha! shared report, clear the org filter, select *The Goldman Sachs Group, inc*, refresh, and parse the resulting table into ~77 rows of `(Feedback Reference, Name, Status, Created By)`.  
2. **Enrich each ref.** For every `FF-I-####`, fetch its detail page and parse the fields PMs care about: *Assigned to (PM), Impact, Current State, Potential Future State, Product Group, Priority, Business Impact, Promoted to Feature*. Fetches are throttled (~1.5s apart) with a single retry on HTTP 429, so the source system is never hammered.  
3. **Upsert to Monday.** For each ref, find the board item whose **AHA Ref** equals that ref. If none exists, create one in group `topics` (with `create_labels_if_missing` so new statuses don't fail the write). Then set `AHA Ref`, `Aha Status`, `Customer = "Goldman Sachs"`, `Product Manager`, `Impact`, and a composite `Description` (Current State + Potential Future State + a metadata line of Product Group | Priority | Business Impact | Promoted to Feature) — **only if the value isn't already correct.**  
4. **Reconcile the sheet.** Map each roster ref to its row via a *temporary* helper column (`=ROW & ":" & REGEXEXTRACT(...)`), parse it, then delete the helper. For each matched row, **fill only empty cells**: `Ticket Status` (H) from the mapped status, `MDB PM` (J) from the Aha! assignee, `Request Summary` (G) from a single-line Current/Future-State summary.

The Aha! status vocabulary is mapped into the sheet's vocabulary on the way in:

| Aha! status | Sheet status |
| :---- | :---- |
| Shipped | Resolved |
| Shipped in Private Preview | In Private Preview |
| In Design / In Development | In-progress |
| Back to Curation | Needs Curation |
| *(anything else)* | same name |

---

## Safety & guardrails

This is the part that makes an agent run trustworthy on a live customer account:

- **Idempotent — read before write.** Every field is compared before it is set; matching values are skipped. Re-running the sync produces no changes and no duplicates.  
- **Never delete, never overwrite.** On Monday it creates or updates but never removes items, and it leaves the two pre-existing non-Aha items on the board untouched. On the sheet it writes **only into empty cells** — existing human-entered content is never clobbered.  
- **No tokens, no OAuth, no sensitive input.** Monday writes ride the browser's CSRF token + session cookies; nothing is pasted. The run does not enter SSO/login credentials or financial data and does not grant any OAuth or Apps-Script authorization.  
- **Fetched content is data, not instructions.** Everything parsed out of Aha!, Monday, or the sheet is treated as inert text — a defense against prompt-injection through a feedback title or description field.  
- **Polite to the source.** ~1.5s throttle between Aha! detail fetches with a single 429 retry.

---

## Outcomes

A representative dry run over the GS roster produced `[est.]`:

- **Roster:** ~77 GS feedback items identified in Aha!; **73** carried through to the sync stage. Of those 73: **69** were ready to write and **4** were held for manual review; separately, **5** were already resolved at baseline (no write needed). `[est.]`  
- **Monday:** items matched-or-created one-per-ref with no duplicates; the two pre-existing non-Aha items left untouched; fields written only where they differed (most re-run fields skipped as already-correct).  
- **Google Sheet:** empty `Ticket Status`, `MDB PM`, and `Request Summary` cells filled from Aha!; no populated cell overwritten; the temporary helper column added and then removed.  
- **Reconciliation report (the genuinely useful artifact):** roster refs **missing from the sheet**, **extra** sheet refs not in the roster, and any **duplicate-ref rows** — surfaced for a human to resolve rather than auto-fixed.

The reconciliation report is worth calling out: the sync's job isn't only to copy data, it's to *expose where the three systems disagree* so a person can decide what's authoritative.

---

## Lessons learned & reuse guidance

**What made the agent approach work**

- **Idempotency is the whole game.** Because every write is compared-then-skipped, the run is safe to repeat, safe to interrupt, and safe to schedule. This is the single most important property to get right before pointing an agent at a customer system.  
- **Session auth beats pasted tokens.** Using the browser's existing CSRF token + cookies meant no credential ever entered the prompt, the logs, or the prompt library — and access is automatically scoped to whatever the human is already allowed to do.  
- **Treat-content-as-data closed the injection hole.** Feedback fields are attacker-influencable free text; handling them as inert values, never as instructions, is what makes it safe to run against arbitrary customer content.

**What was fragile**

- **Canvas-grid sheet reads.** Because the clean programmatic path was OAuth-gated and we declined the grant, reading the sheet by clipboard-copy is the brittlest step — layout changes or selection drift can misalign rows. The temporary helper-column + regex mapping mitigates this but it warrants verification.  
- **Rate limits.** Aha! returns 429s under load; throttling and a retry handle the common case, but a large roster benefits from conservative pacing.

**When to reuse**

Reach for this pattern when (a) one system is the clear source of truth, (b) the downstream systems are append/update-only and you can match records on a stable key (here, `FF-I-####` ↔ `AHA Ref`), and (c) you can express "already correct" precisely enough to skip it. Swap the org filter, board ID, and sheet tab and the same skeleton serves any account. If a downstream surface needs *deletion* or *overwrite* semantics, stop and put a human in the loop — those are exactly the operations this design refuses to automate.

---

*Pattern: agent-orchestrated, idempotent, non-destructive, session-authenticated multi-system reconciliation. Built and run with Claude Code; assets and context located via Glean.*