---
description: >-
  Deepen ONE named concept through its mechanism, parts, limits, failure modes, history, primary sources and expert disagreements; repeat measured deepening passes to the stated stop condition.
  TRIGGER: "/rabbithole", "deepen my understanding of X", "exhaust X completely", "go as deep as possible on X".
  SKIP: family/domain gaps → concept-family-explorer; one ordinary research pass → dr; extract concept mentions from an existing corpus → llms-txt-tooling (references/llms-concept-abstractor/llms-concept-abstractor.md); reorganize existing skill tree → skill-tree-architect.
name: rabbithole
version: "1.4.1"
updated: "2026-11-11"
model: gpt-6.1-sol
effort: medium
category: meta
tags: [concept-depth, exhaustive-research, saturation, orchestration]
keywords:
  - deepen
  - rabbithole
  - exhaust a concept
  - go deeper
  - depth-first research
  - narrow inverse of concept-family-explorer
  - everything about one thing
  - primary sources
  - edge cases and failure modes
related_skills:
  - concept-family-explorer
  - deep-research
  - llms-txt-tooling
  - skill-tree-architect
whenToUse:
  - "deepen my understanding of <concept>"
  - "exhaust <concept> completely — go as deep as you can"
  - "rabbithole on <concept>"
  - "give me everything there is to know about <concept>, however deep that goes"
  - "keep researching <concept> until another pass finds nothing new"
whenNotToUse:
  - "the subject is a domain or family, not one concept (use concept-family-explorer)"
  - "one ordinary research pass is enough, no exhaustion loop wanted (use /dr)"
  - "the concept's mentions already sit inside a corpus you hold and you want them pulled out (use llms-concept-abstractor)"
  - "you want the skill tree reorganized, not a concept researched (use skill-tree-architect)"
metadata:
  changelog_ref: references/CHANGELOG.md
---

Read `references/codex-runtime.md` and `references/research-library.md` before executing this workflow. They define
Codex model selection, shared-source reuse, website completion, and resource paths.


## Look for llms files first

Before reading the single concept and its source corpus raw, locate its llms files. If the repo is available, step 4 sets the order.
1. Check the subject's `llms.txt`, its docs site's `/llms.txt`, or matching packs under `~/.global-ai-hub/skills.llms/` and `~/.global-ai-hub/llms-concepts/`; use available hub keyword/search tools as discovery leads.
2. Run `wc -c` first (or inspect a remote size header). Read a file whole only when it fits; otherwise search it.
3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map, not a fact store.
4. If you have the repo, search its code before opening llms files. Verify each fact you act on against the authoritative file and line.
5. Index and llms hits are leads. Confirm them against readable source text before acting.

## Evidence required before publication

Apply this contract to every factual assertion, including summaries, inherited parent
facts, disagreements, open-question premises and final dossiers. Discovery leads and
coverage labels do not establish support.

- Keep each atomic claim's exact statement, immutable claim ID, source URL, source
  snapshot hash, exact quoted passage and locator together. For v4, author an `evidence`
  list of spans with `url`, `source_id`, `snapshot_sha256`, `start`, `end`, `quote` and
  `extraction_status: complete`. Mark complete only after reading a usable source;
  the attestation never overrides a missing identifier or invalid span. Read the snapshot;
  a URL, reference list, cache hash or model recollection supplies no evidence credit.
- Run deterministic integrity checks over **all** claims before paid semantic review.
  Require each quote to exist in the pinned body and belong to the cited source.
  Check exact technical identifiers, values, units and applicability against the
  passage. Missing identifiers or an incomplete Markdown derivative require readable
  rendered HTML, original RST/source or another complete primary source; withhold the
  assertion until reacquisition succeeds. A keyword match alone does not prove support.
- A semantic judge decides whether the passage supports the complete assertion,
  including negation, version, scope and caveats. It cannot override a failed integrity
  check. In research-gate/v4, review every new or changed factual assertion once.
  Reuse a prior validated SUPPORTED verdict only when the exact assertion and bound
  source snapshots are unchanged. Structural binding alone cannot qualify publication.
  Do not turn structural failures into expensive blanket multi-model reruns.
- Preserve contradictory claims with both source passages and their applicability.
  Record the conflict explicitly and block an unconditional conclusion. Resolve it
  with source evidence or publish only an accurately scoped, qualified conflict.
  Never average opposing claims, silently choose the preferred source, lower confidence
  to bypass a failure, or treat absence from an incomplete extract as proof of absence.
- Build prose and every persisted projection from canonical claim records. Validate
  citation and evidence bindings through concept packs, reader JSON, context and facts
  downloads before completion. Missing bindings or changed assertions stop publication;
  a dossier or tree update alone cannot bypass the shared /dr completion gate.
- Repair only failed claim/source pairs. Keep successful claims, snapshots and paid
  attempts. Allow one bounded evidence repair followed by a fresh bound gate; residual
  substantive dissent stops that claim. An unchanged failed evidence packet must not
  incur another paid judgment; one malformed-JSON repair is allowed. Retry recognized
  transport failures at most twice within the original deadline. Do not repeat discovery, whole-family research
  or successful website generation to repair a citation.
- Before shipping changes to this workflow, exercise real failure regressions:
  uncited claims, wrong-source quotes, incomplete derivatives, missing field names,
  negation or version conflicts, stale snapshot hashes and dropped output citations.
  Verify canonical, installed and runtime-specific skill copies with their sync check;
  equal version numbers alone do not establish parity. Report loaded state separately.

# Rabbithole (`/rabbithole`, "deepen")

`concept-family-explorer` maps everything **around** a subject and stops at the first
useful pass over each neighbor. This skill does the opposite: it takes **one** concept CFE
would treat as a single node, and instead of moving outward to siblings, it moves **inward** —
mechanism, sub-parts, edge cases, failure modes, the history of how understanding of it
changed, primary sources, and where experts disagree — pass after pass, until a pass turns up
nothing new. It is depth-first where CFE is breadth-first; the two compose (CFE finds the
node worth this treatment, this skill exhausts it, CFE's frontier re-expansion can pick up
any sibling this run surfaces).

```
concept ─▶ [1] scope & boundary ─▶ [2] pass 0: broad draft ─▶ [3] pass N: deepen
                                                                     ▲        │
                                                     [4] new-info rate ◀──────┘
                                                            │
                                                     [5] saturated? ──no─▶ back to [3]
                                                            │ yes
                                                            ▼
                                              [6] compile dossier ─▶ [7] handoffs + report
```

## When not to use

- Subject is a domain, family, or "what am I missing about X" question → `concept-family-explorer`.
- One ordinary research pass is what's wanted, no forced exhaustion loop → `/dr` directly.
- The concept's mentions already live inside a corpus you hold (docs, notes, a textbook) and
  you want them pulled out and organized → llms-txt-tooling (references/llms-concept-abstractor/llms-concept-abstractor.md).
- Skill tree needs reorganizing, no new research → `skill-tree-architect`.

## Inputs

- **concept** (required) — one named concept, not a domain. If a domain/family is given,
  say so and suggest `concept-family-explorer` instead (or narrow it: "the family is too
  broad to rabbithole directly — which single concept inside it should I exhaust first?").
- **maxPasses** (optional, default 6) — hard cap on deepening passes regardless of
  saturation, since a genuinely deep concept (e.g. "consensus algorithms") could otherwise
  run indefinitely.
- **budgetMinutes** (optional) — wall-clock cap, same contract as `concept-family-explorer`.
- **seedMaterial** (optional) — a corpus, docset, or file the user already has; used as
  Pass 0 evidence before any web research, so passes don't re-derive what's already on disk.

## Research scout handoffs

Before discovery, read `~/.claude/skills/research-scout/references/consumer.md`.
Run `python3 ~/.claude/skills/research-scout/scripts/scout.py seeds --concept "<exact concept>" --parent "<exact parent>"`
to inspect validated candidate URLs. Resolve unknown or ambiguous parents against
the live inventory; do not guess from a slug. No scout is a normal result:
continue ordinary research. Report malformed bundles and keep other discovery available.

Use only leads inside the scoped concept in Pass 0 and later gap-focused passes.
Read relevant mechanism, limitation, issue and disagreement sources. Hand sibling
and adjacent leads to CFE. A scout URL, repeated query or repeated source adds no
researched novelty by itself; measure new sourced claims in the existing depth loop.

Check live coverage and aliases, source applicability, freshness and originating
organization. Acquire readable source text yourself; the scout's access label is
not your read receipt. Preserve partial, stale, blocked and snippet-only limits.
Record retained and rejected leads with reasons in this run's private notes or
briefs, including scout run, revision, bundle hash, source ID and URL. Leave scout
bundles unchanged. Keep the normal source, negation, authority, scope, claim-gate,
CVS and saturation rules; scout leads do not establish verified claims or completion.

## Workflow

### Step 1 — Scope and boundary

State what is explicitly IN scope (the concept's own mechanism, internals, history,
variants, primary sources) and what is explicitly OUT (siblings, parent domain, adjacent
fields — those are CFE's job, not this skill's). Getting this boundary wrong is the most
common failure: without it, "deepen X" quietly turns into "map the family around X," which
duplicates CFE and never saturates because breadth has no natural stopping point the way
depth does.

### Step 2 — Pass 0: broad draft

One ordinary research pass (reuse `/dr` through the Codex adapter; use `research --lane deep --passes 2` for two independent gpt-6.1-sol `medium` passes merged by the shared runtime, or read `seedMaterial` first if given): mechanism in plain terms, the sub-parts/phases it decomposes into, the two or three
most-cited primary sources, the obvious edge cases. This draft is the baseline every later
pass is measured against — write it down as a flat list of atomic claims (one fact per line),
not prose, so Step 4's new-information count is countable.

### Step 3 — Deepen (pass 1..N)

Each pass re-reads the accumulated claim list and asks, of **every** claim still standing:
"why is that true," "what happens at the boundary/limit," "what's the exception," "who
disagrees and on what basis," "what did the earliest/primary source actually say, in its own
words, versus how it's now paraphrased." Follow each answer to its own primary source when
one exists. A pass that only rephrases existing claims produces zero new atomic facts and
counts as empty — depth means new claims, not longer sentences about old ones. See
`references/depth-passes.md` for the six question types in full, with worked examples of a
genuine deepening ("why does TCP slow-start use exponential *then* linear growth" →
surfaces the congestion-avoidance threshold, a new mechanism) versus a fake one (restating
"TCP is reliable" three ways).

### Step 4 — Measure new-information rate

Diff this pass's claim list against the accumulated one. **New-information rate** = new
atomic claims this pass ÷ total claims after this pass. Record the rate per pass — the
declining curve is the evidence exhaustion is real, not assumed. Full formula and the
two-consecutive-empty-passes rule: `references/saturation.md`.

### Step 5 — Saturation test

Stop when **any** holds:

- **Depth saturation** — two consecutive passes each score new-information rate < 5%.
- **Budget exhausted** — `maxPasses` or `budgetMinutes` hit; report as a soft stop, not
  saturation, and say how many more passes looked likely to still pay off.
- **Boundary breach detected** — a pass keeps generating sibling/adjacent concepts instead
  of deeper claims about the same one (a sign the concept was actually a family) → stop,
  say so, hand off to `concept-family-explorer` with this run's claim list as its seed
  inventory rather than forcing a fake depth loop to continue.

Otherwise return to Step 3.

### Step 6 — Compile the dossier

Write the final claim list as a structured dossier: definition, mechanism, history, edge cases, failure modes and disagreements side by side, with primary sources bound per atomic claim. Use one owned `/dr` run for the final accumulated claims, including every new depth-pass assertion; a gate receipt for Pass 0 alone does not cover later additions.

Follow `/dr`'s mandatory repository adapter contract and claim schema. Reuse the owned run; if one does not exist, initialize it through that adapter before recording. Then perform this concrete finalization sequence:

1. Record the complete final structured claims and evidence snapshots through `codex_dr_run.py concept-done <slug> <final-claims.json>`. Preserve immutable claim IDs and every bound source passage.
2. Render with `codex_dr_run.py render <slug>` and the resolved hub/standalone/output arguments owned by `/dr`. Scan for injection and preserve the existing output-binding checks.
3. Gate every new or changed assertion through the adapter. A failed or stale binding withholds publication; repair only the failed pairs within the established bounded-repair rule.
4. Finish through the adapter so the canonical tree and reader/context/facts projections refresh together. Do not write the concept tree directly as a substitute. A failed refresh leaves persistence unfinished.

```sh
python3 "${LLMS_EXPLORER_REPO:-$HOME/dev/llms-explorer}/scripts/codex_dr_run.py" gate <slug>
python3 "${LLMS_EXPLORER_REPO:-$HOME/dev/llms-explorer}/scripts/codex_dr_run.py" finish <slug> --status COMPLETED --minutes <n> --agents <n> --stop-reason "depth gate and projections complete"
```

Use `COMPLETED` only after the final evidence and projection gates pass. A budget stop remains `BUDGET_EXHAUSTED`; a boundary-breach stop uses supported runtime status `BLOCKED` and hands adjacent concepts to CFE. Keep the depth/saturation verdict separate: `SATURATED-DEPTH` is not a substitute for persistence completion. Report the runtime status, exact accepted artifact path, final gate and projection-refresh outcome independently.

### Step 7 — Handoffs and report

Report per-pass new-information rate (the declining curve), total passes run, saturation
verdict (`SATURATED-DEPTH` / `BUDGET_EXHAUSTED` / `BOUNDARY-BREACH → handed to CFE`), the
compiled dossier's location, the separate final claim-gate/persistence status, and any sibling/adjacent concepts surfaced along the way as a
handoff list for `concept-family-explorer` — this skill never chases them itself.

## Quality rules

1. **Depth, not breadth.** The moment a pass wants to talk about a sibling concept instead
   of going deeper into this one, that's a boundary breach (Step 5) — hand off, don't absorb.
2. **Countable claims, not prose.** New-information rate is meaningless against paragraphs;
   keep the accumulated dossier as atomic, diffable claims until Step 6's final compile.
3. **Primary sources over paraphrase.** A pass that only re-reads secondary summaries of the
   same primary source produces no new depth even if the words are new.
4. **Disagreements are data.** Where credible sources conflict, both sides go in the
   dossier, never silently resolved.
5. **Saturation is evidence.** Report the declining new-information curve; a flat "ran out
   of ideas" is not the same claim as "two passes in a row found nothing new," and only the
   second one is the real stop condition.

## Trigger examples

**Should trigger:**
- "Deepen my understanding of the TCP congestion-avoidance algorithm — go as far as it goes."
- "Rabbithole on the halting problem until there's nothing left to learn."
- "Exhaust everything about MongoDB's WiredTiger checkpoint mechanism."

**Should NOT trigger:**
- "What am I missing about distributed systems in general?" → `concept-family-explorer`.
- "Research CRDTs and make a skill" (one pass, no forced exhaustion) → `/dr`.
- "Pull everything these three docsets say about caching" → llms-txt-tooling (references/llms-concept-abstractor/llms-concept-abstractor.md).
