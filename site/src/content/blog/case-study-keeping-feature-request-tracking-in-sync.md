---
title: "Case Study — Keeping a Customer's Feature-Request Tracking in Sync with an Agent"
description: "Claude Code and Glean kept a customer's feature requests in sync across Aha!, Monday.com and Google Sheets with idempotent writes, no deleted customer data and no pasted tokens."
date: "2026-10-14"
order: 10
---

**How Claude Code (browser automation plus MCP) and Glean kept one enterprise customer's feature requests aligned across Aha!, a Monday.com board, and a Google Sheet — idempotently, with no pasted API tokens and no customer data deleted.**

*Audience: technical account managers (TAMs) and product managers (PMs). This is an engineering case study, not marketing. Figures marked `[est.]` are estimates; the Outcomes figures come from the production run.*

---

## TL;DR

One enterprise customer's feature requests lived in three places that drifted apart: **Aha!** (the PM source of truth), a **Monday.com board** the account team worked from, and a **Google Sheet** the customer and the account executive (AE) reviewed. Reconciling them by hand was slow, error-prone, and always stale.

We had Claude Code drive the whole loop end to end. It read the customer's ~77 ideas out of Aha!, enriched each from its detail page, then idempotently upserted them onto the Monday board (create or update, so a re-run changes nothing further) and filled only the empty cells of the sheet.

By design, the run reads before it writes. It never deletes the customer's data, never overwrites a populated sheet cell, and writes Monday fields only where they differ from Aha!. It uses the browser's own session instead of a pasted token and treats every fetched value as data rather than instructions. The result is a single-pass reconciliation of work that took a person the better part of a day by hand `[est.]`.

---

## Problem & context

A high-touch enterprise account generates feature requests faster than any one system captures them cleanly:

- **Aha! ideas** are where PMs triage and own requests: the canonical state (status, assigned PM, impact, promotion to feature).
- A **Monday.com board** (a product tracker kept for this one customer) is where the account team tracks and discusses those requests operationally.
- A **Google Sheet** (a feature-request tab) is the shared surface the customer and the AE actually look at.

Each system is authoritative for *something* and stale for everything else. When a PM moved an Aha! idea from *In Development* to *Shipped*, that change did not reach the board or the sheet until someone noticed and hand-edited two more places. Status labels diverged (Aha!'s vocabulary ≠ the sheet's vocabulary), PM assignments went missing, and nobody could trust the customer-facing sheet without re-checking Aha! first. The manual reconciliation was the kind of repetitive, careful, cross-tab work that humans do slowly and agents do well, *if* the guardrails are right.

---

## Architecture

Claude Code acted as the orchestrator, with Glean used up front to find the Aha! report, the board, and the sheet and to pull surrounding account context. Everything downstream ran through the agent's Chrome browser automation and MCP tooling, against the operator's already-authenticated sessions.

| Layer | System | Access pattern |
| :---- | :---- | :---- |
| Source of truth (read-only) | Aha! shared report + per-idea detail pages | Browser fetch of the report filtered to the customer; parse the iframe table, then fetch each idea's detail page |
| Operational tracker (read/write) | The customer's Monday board | Internal GraphQL `POST /v2/` with `x-csrf-token` + `credentials:'include'`; **no pasted API token** |
| Customer-facing surface (read/write) | The feature-request tab of the Google Sheet | Read via clipboard-copy of the canvas grid (gviz, Google's Visualization query API, needs an OAuth credential unless the sheet is public); write only empty cells |
| Discovery & context | Glean | Locate assets, pull account context |

Two design choices in this table carry most of the safety story. First, Monday writes use the browser's own CSRF token and session cookies rather than a long-lived API token, so no API token is pasted or stored. Second, the sheet is read by copying the rendered grid to the clipboard, because the clean programmatic path (gviz) sits behind an OAuth grant we deliberately chose *not* to request.

---

## Sync logic

The run is a single pass through four steps:

1. **Build the roster.** Open the Aha! shared report, clear the org filter, select the customer's organization, refresh, and parse the resulting table into ~77 rows of `(Feedback Reference, Name, Status, Created By)`. The `Feedback Reference` is the *ref*: the key that matches records across all three systems.
2. **Enrich each ref.** For every ref, fetch its detail page and parse the fields PMs care about: *Assigned to (PM), Impact, Current State, Potential Future State, Product Group, Priority, Business Impact, Promoted to Feature*. Fetches are throttled (~1.5s apart) with a single retry on HTTP 429, so the run does not flood Aha!.
3. **Upsert to Monday.** For each ref, find the board item whose `AHA Ref` equals that ref. If none exists, create one in group `topics`, with `create_labels_if_missing` so new statuses don't fail the write (the flag adds missing status labels, so it needs permission to change the board's structure). Then set `AHA Ref`, `Aha Status`, `Customer` (the same value on every item), `Product Manager`, `Impact`, and a composite `Description` (Current State + Potential Future State + a metadata line of Product Group | Priority | Business Impact | Promoted to Feature), but only if the value isn't already correct.
4. **Reconcile the sheet.** Map each roster ref to its row via a *temporary* helper column (`=ROW() & ":" & REGEXEXTRACT(...)`), parse it, then delete the helper. For each matched row, **fill only empty cells**: `Ticket Status` (H) from the mapped status, `MDB PM` (J, the sheet's PM column) from the Aha! assignee, and `Request Summary` (G) from a single-line Current/Future-State summary.

The Aha! status vocabulary is mapped into the sheet's vocabulary on the way in:

| Aha! status | Sheet status |
| :---- | :---- |
| Shipped | Resolved |
| Shipped in Private Preview | In Private Preview |
| In Design / In Development | In-progress |
| Back to Curation | Needs Curation |
| *(anything else)* | same name |

Any status outside this map reaches the customer-facing sheet under its Aha! name, so check new Aha! statuses before they appear there.

---

## Safety & guardrails

These guardrails are what let an agent run on a live customer account:

- **Idempotent: read before write.** Every field is compared before it is set, and matching values are skipped. Re-running the sync against unchanged sources produces no changes and no duplicates.
- **Non-destructive writes.** On Monday it creates items, adds any missing status labels, and updates the fields it manages to match Aha!, the source of truth, but never removes an item, and it leaves the two pre-existing non-Aha items untouched. On the sheet it writes **only into empty cells**, so human-entered content is never clobbered. The only thing it deletes is the temporary helper column it created itself.
- **No pasted tokens, no OAuth, no sensitive input.** Monday writes ride the browser's CSRF token and session cookies; nothing is pasted. The run does not enter SSO/login credentials or financial data and does not grant any OAuth or Apps-Script authorization.
- **Fetched content is data, not instructions.** Everything parsed out of Aha!, Monday, or the sheet is treated as inert text, a defense against prompt injection through a feedback title or description field.

---

## Outcomes

The production run over the customer's roster produced these results:

- **Roster:** ~77 of the customer's ideas identified in Aha!; 73 carried through to the sync stage. Of those 73, 69 were ready to write and 4 were held for manual review. Separately, 5 were already resolved at baseline and needed no write. The counts do not show why the remaining ~4 did not reach the sync stage, or how the 5 overlap the 69 and the 4.
- **Monday:** items matched or created one per ref, with no duplicates; the two pre-existing non-Aha items left untouched; fields written only where they differed (most fields were skipped as already correct on re-run).
- **Google Sheet:** empty `Ticket Status`, `MDB PM`, and `Request Summary` cells filled from Aha!; no populated cell overwritten; the temporary helper column added and then removed.
- **Reconciliation report:** the most useful artifact. It lists roster refs missing from the sheet, extra sheet refs not in the roster, and any duplicate-ref rows, surfaced for a human to resolve rather than auto-fixed.

The sync's job is not only to copy data. It also exposes where the three systems disagree, so a person can decide what's authoritative.

---

## Lessons learned & reuse guidance

**What made the agent approach work**

- **Idempotency is the whole game.** Because every write is compared and skipped when already correct, the run is safe to repeat. It is safe to interrupt too, except that stopping between adding and deleting the temporary helper column could leave it on the sheet. Get this right before pointing an agent at a customer system.
- **Session auth over pasted tokens.** Using the browser's existing CSRF token and cookies meant no long-lived API token or login credential had to be pasted into the prompt. The trade-off is that access is whatever the operator is already allowed to do, so the write rules, not the credential, are what restrain the agent.
- **Treat content as data.** Feedback fields are free text that other people can influence, so the agent handles them as inert values, never as instructions. That lowers the injection risk without removing it; the write rules limit the damage if an instruction slips through.

**What was fragile**

- **Canvas-grid sheet reads.** Because the clean programmatic path was OAuth-gated and we declined the grant, reading the sheet by clipboard-copy is the brittlest step. Layout changes or selection drift can misalign rows. The temporary helper column and regex mapping mitigate this, but the result warrants verification, especially before running it on a schedule.
- **Populated sheet cells never refresh.** The run never overwrites a filled cell, so a later Aha! status change does not reach it, and a value written to the wrong row after a misaligned read stays until a person fixes it.
- **An undocumented write path.** The Monday write uses the web app's internal GraphQL call, not the token-based API monday.com documents, so a change on monday.com's side could break it without warning.
- **Rate limits.** Aha! returns 429s under load, so a large roster benefits from conservative pacing beyond the throttle and single retry.

**When to reuse**

Reach for this pattern when (a) one system is the clear source of truth, (b) the downstream systems are append- or update-only and you can match records on a stable key (here, the Aha! idea reference ↔ `AHA Ref`), and (c) you can express "already correct" precisely enough to skip it. Swap the org filter, board ID, sheet tab, status map, and column mappings and the same skeleton should serve another account. If a downstream surface holds content people entered by hand (here, the sheet) and the sync would need to delete or overwrite it, stop and put a human in the loop. This design refuses to automate those operations.

