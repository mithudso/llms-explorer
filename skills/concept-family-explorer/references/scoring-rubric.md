# Concept Viability Score (CVS) — scoring rubric

> **Run `~/.claude/skill-consolidation/cvs_check.py` — never verify weighted
> sums yourself.** Feed it the scored gap table as JSON: it recomputes each
> composite (asserting |Δ| < 0.005), enforces the `Via ≤ 1` / `Nov = 0` hard
> gates, and checks the threshold decisions (RESEARCH / REFRESH / SKIP).
> Near-threshold tie *ordering* stays a judgment check against the
> Via → Rel → Int rule below — the tie-break governs queue order, not
> decisions.

The selection gate. Every candidate gap is scored on five 0–5 axes and combined
into a single CVS, so the decision to spend a (costly) `/dr` run on a concept is
auditable rather than intuitive. Each axis borrows a method from the data-
analytics (`da-*`) skills — concept selection is itself a multi-criteria
prescriptive-analytics decision, so the same machinery that ranks features,
prices value, and scores relevance applies directly.

Activate the relevant hub before scoring an axis so you apply the method, not a
guess at it. The `da-38/39/40` lenses are folded spokes: activate their owning
hub (`da-analytical-methods` or `da-applied-and-communication`) and it loads the
spoke reference on demand — referencing the bare spoke ID would not resolve to an
indexed skill.

## The five axes

### 1. Relevance (0–5) — `da-analytical-methods` ▸ `references/da-38-recommender-systems-and-ranking`
Semantic proximity to the subject's core. Treat the subject as a query and the
candidate as a document: how high would a good ranker place it? Graph distance in
the concept tree is a useful proxy — a direct child is closer than a third-hop
adjacent concept.

- 5 — core sibling/child; anyone working the subject hits this constantly.
- 3 — one domain hop away; clearly related, not central.
- 1 — distant cross-over; relevant only in edge scenarios.
- 0 — coincidental keyword overlap; different domain.

### 2. Usefulness (0–5) — `da-applied-and-communication` ▸ `references/da-40-pricing-and-revenue-analytics`
Expected outcome lift if the concept were known and skilled. The value/
willingness-to-pay lens: how much would having this materially improve real
work — decisions made better, errors avoided, time saved?

- 5 — unblocks or de-risks frequent, high-stakes work.
- 3 — clear value in a recurring but narrower situation.
- 1 — nice-to-know; rarely changes an outcome.

### 3. Novelty (0–5) — `da-analytical-methods` (candidate generation + dedup)
Gap size against existing coverage (from the Step 2 inventory). Novelty is *not*
"how new the idea is in the world" — it is "how absent it is from your library."
A well-known concept you have zero coverage of still scores high.

- 5 — no skill, no concept-tree node, no adjacent coverage.
- 3 — partially covered; a sub-angle or refinement is missing.
- 1 — substantially covered already; marginal addition.
- 0 — duplicate of an existing fresh skill → decision is SKIP, not RESEARCH.

STALE concepts (covered but >90 days old) get Novelty re-scored as a *refresh*
value: how much is the existing coverage likely to have decayed?

### 4. Interest (0–5) — `da-applied-and-communication` ▸ `references/da-39-augmented-analytics-llm-assisted` (key-driver)
Likelihood of repeated, curious use — the "interesting" the user explicitly
asked for. Key-driver framing: would this concept keep generating follow-on
questions and connect to many other concepts (high fan-out in the tree)?

- 5 — a hub concept; spawns many children, invites exploration.
- 3 — moderately generative; a few natural follow-ons.
- 1 — terminal; learn it once and you are done.

### 5. Viability (0–5) — `da-analytical-methods` feasibility / `da-3-data-acquisition-sampling`
Can it actually be researched into a *useful* skill? The data-availability and
scope-feasibility lens — `/dr` needs ≥3 citable sources and a scope that fits a
skill. Penalize concepts too broad to saturate or too thin to source.

- 5 — well-documented, sources abundant, scope fits one skill cleanly.
- 3 — researchable but scope needs splitting, or sources are uneven.
- 1 — speculative, proprietary, or unbounded; `/dr` would struggle.
- 0 — un-researchable (no public sources) → SKIP with reason.

## Composite

Default weights reflect that a concept must first be *relevant and useful* before
novelty and interest matter, and that an unviable concept cannot be researched
no matter how attractive:

```
CVS = 0.25·Relevance + 0.25·Usefulness + 0.20·Novelty
    + 0.15·Interest  + 0.15·Viability        (range 0–5)
```

**Viability gate (hard):** if `Viability ≤ 1`, decision is SKIP regardless of
CVS — an attractive concept `/dr` cannot source is wasted budget. Likewise
`Novelty = 0` forces SKIP (it is a duplicate).

**Default threshold:** `CVS ≥ 3.2` → RESEARCH. Tunable per run:
- raise toward 3.8 to be selective when budget is tight;
- lower toward 2.6 to cast a wide net on an under-explored subject.

**Decisions:** `RESEARCH` (above threshold, gated) · `REFRESH` (STALE + above
threshold) · `SKIP` (below threshold, or failed a hard gate). Record the score
and reason for every candidate — skips are saturation evidence.

## Tie-breaking

When CVS ties near the threshold, prefer, in order: higher Viability (cheaper,
surer `/dr` win) → higher Relevance (keeps the family coherent) → higher Interest
(fan-out compounds future runs). Group tied related concepts into one clustered
`/dr` call rather than splitting the budget.

## Worked example — subject: "data observability"

Ranked by CVS descending (the output table must be ranked):

| Concept | Rel | Use | Nov | Int | Via | CVS | Decision |
|---------|-----|-----|-----|-----|-----|-----|----------|
| Data contracts | 5 | 5 | 4 | 4 | 5 | **4.65** | RESEARCH |
| OpenLineage / column lineage | 5 | 4 | 5 | 4 | 4 | **4.45** | RESEARCH |
| Data downtime SLOs | 4 | 5 | 4 | 3 | 4 | 4.10 | RESEARCH |
| "Observability for ML feature drift" | 3 | 4 | 5 | 5 | 2 | **3.80** | RESEARCH (Via=2 > 1, passes gate) |
| Anomaly detection on metrics | 4 | 4 | 2 | 3 | 5 | 3.60 | RESEARCH |
| Semantic layer (alias-missed dup) | 4 | 4 | 0 | 3 | 5 | 3.20 | SKIP (Novelty 0 hard gate → dup) |
| General DevOps observability | 2 | 3 | 3 | 2 | 5 | 2.90 | SKIP (< 3.2) |

Reading the table: "Data contracts" and "column lineage" are the highest-value
gaps and lead the queue. The semantic-layer row is a duplicate that slipped
past Step 2's alias expansion into the scored set (a fresh HAVE would normally
never be scored — `GAPS = family − HAVE`); scoring catches it — Novelty 0 —
and it clears the raw threshold (CVS 3.20 ≥ 3.2) yet is SKIPPED, because hard
gates beat threshold. That is the gate's real job: the last line of defense
against inventory misses. Every row carries its computed CVS so `cvs_check.py`
can recompute it (never leave "—"). "General DevOps observability" is
relevant-ish but below threshold and logged as a deliberate skip — that logged
skip is what later proves the frontier was actually explored, not skimmed.
