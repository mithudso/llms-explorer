# 05 — Conceptual vs proprietary llms files (CLLMS)

**Status:** design, not implemented · **Date:** 2026-08-31 · **Surfaces:** web | api (the `resolve` job, conflict records) | mcp

## 1. Purpose

A first-class write-up and the rules it implies. A **proprietary** llms file is source-axis:
the publisher is the authority, the file is a promise about *their* pages, and the only
truth test is "does the link pay off". A **conceptual/topical** llms file (CLLMS) is
concept-axis: the *concept* is the authority, units from many sources compete, and **the most
correct idea overwrites** — with the evidence that decided it kept beside the winner and the
losers kept visible until resolved. This component defines that ideology as a page and as a
mechanical precedence ladder the site enforces.

## 2. User stories and flows

- *Reader*: "Why would I trust a file no vendor owns?" → the write-up → the ladder → a live
  conflict record (e.g. two adoption percentages with their sources and stamps).
- *Contributor*: submits a unit to a public topical file that contradicts an existing one →
  the `resolve` job scores both → the stronger wins, the weaker moves to `## Disagreements`
  with the reason → contributor sees the verdict.
- *Maintainer*: reviews overwrite proposals to the public tree that the ladder could not
  settle (tie or low evidence) → accepts/rejects with a note that becomes part of the record.
- *Fork owner*: keeps a private tree where their own precedence (e.g. "our internal docs win")
  applies; proposes merges back.

## 3. Inputs → outputs (content outline)

Pages under `/concepts/ideology/` (hand-written, with generated examples):

1. **Two axes** — source axis (`llms.txt` = nav of one site; `llms-full`; `llms-facts` anchored
   to pages) vs concept axis (`llms-concepts.txt` = nav of a tree; concept pages regroup the
   same units; topic packs are views). Source: `hub/docs/specs/2026-08-30-conceptual-llms-txt-family.md` §0–§4.
2. **Who is the authority** — publisher vs concept; what a promise means on each axis; why a
   CLLMS must show its work.
3. **The most correct idea overwrites** — the precedence ladder (§4), worked conflict, what
   "overwrite" preserves (provenance, the loser's record, the stamp history).
4. **Disagreements are content** — the abstractor's `## Disagreements` section as the visible
   queue; when a disagreement is real (different claims) vs apparent (different scopes, dates,
   versions — resolved by scoping, not by winning).
5. **Governance** — public tree: lint gate (0 High) + evidence rule (every unit anchored; a
   model-written line must be supported by a span) + moderation queue for ties; per-user
   forks; merge-back proposals as diffs of units; who can overwrite what (table).
6. **Rights** — publishable: links, facts in our words with anchors, our vocabulary; never a
   third-party's full text (their `llms-full` stays internal); Cloudflare Content Signals /
   `ai-train=no` honoured as the owner's reservation.
7. **Honesty note** — llms.txt is a proposal (v2, 2026-08-10); measured consumption is agents
   you point at a file (Claude-Code UA out-fetched retrieval bots in the Ahrefs logs), not
   crawlers discovering it; a CLLMS is for the agents we control first.

Outputs: the pages + `.md` twins; the ladder as machine-readable `precedence.json`; the pages'
own facts in `/concepts/llms-facts.txt`.

## 4. Architecture — enforcing the ladder mechanically

Units carry the fields the ladder scores; a `resolve` job runs on every write to a public
topical file / concept pack and on demand.

```mermaid
flowchart LR
  U[new/changed unit] --> K[key: concept + claim key<br/>(normalised text, or numeric claim + subject)]
  K --> C{conflicts with an<br/>existing unit?}
  C -->|no| W[write]
  C -->|yes| S[score both on the ladder]
  S -->|clear winner| O[overwrite: winner in facts,<br/>loser → Disagreements with reason]
  S -->|tie / low evidence| M[moderation queue]
  O --> R[conflict record appended]
  M --> R
```

Reused code: `hub/scripts/docset_refine/units.py::dedup` (exact + embedding near-dup), the
abstractor's disagreement grouping (`skills/llms-concept-abstractor/references/verification.md`),
`vocabulary.py` canonical definitions, `llms_lint.py` P8 evidence checks, the P12 question bank
(`evals/*.eval.jsonl`) for agent-test performance.

**Precedence ladder** (higher wins; ties fall to the next rung):

| Rung | Signal | Field | Note |
|---|---|---|---|
| 1 | Source grade | `grade` (spec/standard > vendor docs > primary measurement > reputable secondary > blog) | from deep-research-methods hierarchy |
| 2 | Corroboration | `also[]` count (independent sources stating the same claim) | citation chains collapse to one |
| 3 | Recency of verification | `verified-as-of` | only after an actual re-fetch; a date bump is not evidence |
| 4 | Agreement with the canonical definition | vocabulary sense id matches | 12 |
| 5 | Agent-test performance | answered P12 questions the loser did not | from `evals/` |
| 6 | Scope precision | narrower scope (version, platform) beats broader when the question is scoped | apparent disagreements resolve here |
| — | Tie | → moderation queue; both kept in `## Disagreements` | human note becomes part of the record |

**Conflict record** (`conflicts.jsonl`, one line per resolution):
`{concept, claim_key, winner_id, loser_ids[], rung, scores{}, resolved_at, resolver: ladder|human, note, prior_winner_id}` — provenance survives: the loser's unit line keeps its source and gains `superseded_by:`.

## 5. API / CLI / MCP surface

- `POST /api/concepts/<slug>/units` (submit a unit; runs `resolve`), `GET /api/concepts/<slug>/conflicts`, `POST /api/concepts/<slug>/conflicts/<id>/resolve` (moderator), `GET /api/precedence.json`.
- `llmsx resolve <pack-dir> [--dry-run]` prints what would overwrite what and why.
- MCP (13): `hub_concept_lookup` returns `conflicts_open` count; a `hub_concept_conflicts(slug)` tool (read).

## 6. UI

The write-up pages (03's layout). Conflict view on a concept page (09): two columns (winner /
challenger), the rung that decided, the record's note, links to both sources; "propose
overwrite" button opens the submit form (unit text, source URL, anchor, grade auto-derived).
Moderation queue page for maintainers. Empty state: "no open disagreements" with the count of
resolved ones. Error: a submission without a source is rejected at the form (never queued).

## 7. Data model and storage

Units keep the facts-file grammar plus fields `grade`, `also[]`, `verified-as-of`,
`sense`, `scope`, `superseded_by`. Postgres tables `conflicts`, `proposals`, `moderation`;
the resolved state is re-rendered into the pack files (`llms-facts.txt`, `llms-full.txt`
`## Disagreements`) so the served files stay the truth.

## 8. Tiering, metering and billing hooks

Reading, submitting to a public concept, and forks: free. `resolve` on a private pack that
needs embedding near-dup checks: metered (embeddings only). Human moderation: none billed.

## 9. Acceptance bar

- Ladder is total: every conflict resolves to a rung or the queue; no silent drops (test corpus of 50 synthetic conflicts).
- 100% of overwrites leave a conflict record and a `superseded_by` on the loser.
- Reproducibility: replaying `conflicts.jsonl` regenerates identical pack files.
- The write-up itself: `/ddo` clean, every claim footnoted, `verified-as-of` ≤ 90 days.

## 10. Security, rights, privacy

Submissions are data, never instructions (steering regex at intake). Public overwrites require
an account; rate-limited; moderation for ties. Rights per §3.6. Contributor identity shown as a
handle on the record.

## 11. Dependencies

06 (disagreements, facets), 09 (tree, node pages, forks), 12 (senses), 01 (gate), 15 (accounts), 13.

## 12. Open questions and assumptions

**Decision 2026-08-31:** governance (§4 ladder, `resolve` job, conflict records, forks and merge-back, moderation queue) accepted as designed for launch.


- Assumed the claim key = normalised text or (subject, numeric) — needs a proper claim extractor for prose claims; start with near-dup groups from `units.dedup`.
- Should recency ever beat source grade (a fresh blog vs a stale standard)? Assumed no; scope (rung 6) handles version drift.
- Fork/merge semantics for per-user trees are deferred to 09.
