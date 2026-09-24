# Saturation and loop control

How to map a conceptual family, decide when it is fully explored, and stop a
loop that drives an expensive worker (`/dr`) without letting it run away.

## Family-mapping taxonomy

The Step 1 map must cover five neighborhoods, or the gap set will be lopsided
toward whatever you happened to think of first. For each, name concepts; do not
score yet.

| Neighborhood | Probe questions | Example for "vector databases" |
| --- | --- | --- |
| **Parent / super-domain** | What is this a special case of? What field owns it? | AI datastores; information retrieval |
| **Siblings** | Same parent, same level — the alternatives and peers | Knowledge graphs; inverted-index search; feature stores |
| **Children / sub-concepts** | What does it decompose into? | HNSW; IVF-PQ; hybrid search; quantization; metadata filtering |
| **Adjacent / cross-over** | Neighboring domains that interface here | Embeddings models; RAG orchestration; re-ranking; eval harnesses |
| **Frontier / emerging** | New, contested, rising (last 12–18 months) | Late-interaction (ColBERT); GPU-native indexes; learned indexes |

**Coverage heuristics**
- Aim for MECE within a neighborhood — overlapping candidates waste scoring.
- Flag cross-cutting concepts (belong to >1 neighborhood); they often score high
  on Interest because of their fan-out.
- The Frontier row is where "novel / interesting" lives — never leave it empty.
  If you cannot name frontier concepts from memory, that itself is a signal to
  let `/dr` surface them and re-expand (Step 7).

## Coverage inventory states

Every candidate carries one tag after Step 2, computed against the concept tree
(`tam_concept_tree_search` / `_list`) and installed skills (`tam_search_skills`).

**Pagination is mandatory.** `tam_concept_tree_list` defaults to 20 rows; a
naive single call silently truncates the inventory and mislabels covered
concepts as GAP. Call with `limit: 100` and loop on the response envelope's
`next_offset` while `has_more: true`. Apply the same loop to the
`staleOnly: true` sweep and to any `tam_concept_tree_search` whose `total`
exceeds the page. Cost: a full inventory of a ~400-node tree is ~5 pages of
dense JSON — page the full list **once per run** (the Step 2 census + stale
sweep); on Step 7 re-expansions re-check only the new candidates per "Dedup
against coverage" below, never re-page the whole tree.

**Alias expansion is mandatory before tagging GAP.** `tam_concept_tree_search`
is substring-only with no relevance ranking (every hit `_score=1`). For each
candidate whose primary-name search returns no strong hit, search 2–3
alias/expansion/abbreviation variants ("RAG" vs "retrieval-augmented
generation") before tagging GAP. Prefer distinctive multi-word variants over
short abbreviations — short queries false-positive heavily ("RAG"
substring-matches "Coverage"/"Storage") — and call with `limit` 5–10 to bound
context noise. A **strong hit** — a returned node whose name contains the *full*
multi-word concept, confirmed by reading the node name (a bare short-token
substring match like "RAG" inside "Coverage"/"Storage" does NOT count) — on any
variant ⇒ HAVE or STALE, not GAP.

- **HAVE** — fresh skill or tree node exists → not a gap (unless a child sub-angle
  is missing, in which case the *child* is the gap, not the parent).
- **STALE** — tree node exists but `researchedAt` > 90 days → a *refresh* gap;
  score Novelty as decay-risk, decision REFRESH if above threshold.
- **GAP** — no coverage anywhere → a true gap; score normally.

## The three saturation conditions

Saturation is the stop condition. Evaluate after each frontier re-expansion
(Step 8). Stop when **any** holds — but report *which* one, because they mean
different things.

### 1. Frontier saturation (the strong signal)
**Two consecutive** re-expansion rounds (Step 7) each produced **zero new gaps
scoring ≥ threshold**. The frontier has stopped yielding worthwhile concepts.
This mirrors `/dr`'s own "2 consecutive searches yield nothing new" — applied
at the family level instead of the source level. This is the condition you
*want* to hit: it means the family is genuinely explored, not merely that a
list ran out.

Two rounds, not one, to avoid a false stop when one batch happened to be
narrow. One empty round = "probably done"; two = "saturated". Note the budget interaction: under the default
`maxRounds=3`, the two empty rounds consume 2 of 3 re-expansions — exactly as
the worked trace below shows (2/3 used).

**Base-size precondition.** Frontier saturation may only be declared after
(i) at least one *productive* round — any round, explicitly including the
initial Round-0 research batch, in which ≥1 concept was researched via `/dr` —
AND (ii) a Round-0 map meeting the 5-names-per-neighborhood floor (5–12 is the
Step 1 target band; 5 is the floor). Otherwise the verdict must say
"map-bounded, not saturated".

**Empty rounds must be evidence-grounded.** A re-expansion round only counts
as a completed probe if its candidates were harvested from external evidence
produced this run — the `childConcepts` each `/dr` passed to
`tam_concept_tree_upsert`, the new skills' Core Concepts/References sections,
and `tam_concept_tree_get` on each new node. Memory-only generation never
counts as a completed probe.

**Measured rate.** The Step 10 saturation verdict must state the per-round
new-information rate (new above-threshold gaps / cumulative candidates
scored), so the claim cites a measured rate; treat ~5% as a starting default,
not validated truth.

**Blind saturation gate (runs AFTER the two consecutive empty rounds, before
reporting).** Per the canonical blind re-audit guardrail in
`~/.claude/skill-consolidation/convergence-and-severity.md` (fresh context,
demote-unless-corroborated, max two runs, explicit dissent status): dispatch
ONE fresh-context subagent that receives ONLY the subject and the
5-neighborhood candidate names — no scores, decisions, or run history — and
ask it to name missing concepts per neighborhood. Score any proposals through
Step 4; corroborated ≥ threshold gaps re-enter the queue for at most ONE
additional round (counting against `maxRounds`), then the gate runs once more.
Persistent dissent exits `SATURATION-DISSENT`, listing the gaps in the
verdict. **No-rounds-left precedence:** when corroborated gaps arrive but
`maxRounds` (or another budget cap) is already exhausted, skip the extra
round and exit `SATURATION-DISSENT` immediately, listing the gaps — never
run a round no budget permits, and never report frontier saturation over
corroborated dissent. On a dissent exit Steps 9–9c still run as normal over
everything researched this run (only the corroborated-but-unresearched gaps
stay open, listed in the verdict). If no isolated dispatch is available, run the gate in-context with
prior rationale set aside and label it "blind gate: in-context". Budget and
coverage exits stay ungated, exactly as the contract leaves cap exits ungated.
Optional `--cross-model` (default OFF): run the gate's second pass on a
different model family per
`~/.claude/skill-consolidation/cross-model-gate.md` — observe its
egress-confidentiality precondition before sending family content off-host.

### 2. Coverage saturation
Every node in the mapped family is now in a terminal state: HAVE, researched-
this-run, decision-SKIP (a logged deliberate skip — below threshold **or
hard-gated**, e.g. Novelty 0 at CVS ≥ threshold), or **failed (a logged failed
gap — Step 6 terminal, not a hole)**. Nothing is left undecided — AND every Step 1 competency question in
`~/.claude/skill-consolidation/evals/<subject-slug>.cq.md` resolves to a HAVE or
researched node. This is exhaustive coverage of the *mapped* family — weaker than
frontier saturation because it cannot speak to concepts the map never named.
When you stop here, note that the map itself bounded the result.

### 3. Budget exhausted (soft stop — NOT true saturation)
`maxConcepts`, `maxRounds`, or the wall-clock budget (`budgetMinutes`) hit.
When `budgetMinutes` is set, check elapsed time after each `/dr` return and
each re-expansion round per the canonical Budget contract
(`~/.claude/skill-consolidation/convergence-and-severity.md` §Budget
contract); on expiry drain Step 6b persistence for **every in-flight `/dr` run**
(all concepts in the current fan-out batch, not just one) — never stop
mid-persist — then exit with status `BUDGET_EXHAUSTED` and wall time in
the Step 10 verdict. This is a resource limit, not evidence of
completeness. When you stop here you **must**:
- report the unresearched above-threshold queue (concept + CVS), and
- recommend a re-run with a larger budget to continue.

On this path Steps 9/9b (optimization + rebalance) are **skipped and listed as
owed work** — but Step 9c's batch sync and Step 10's report always run:
persistence completeness is never budget-gated.

Never report budget exhaustion as "saturated." The user needs to know the family
still has worthwhile gaps that budget — not evidence — left unfilled.

## Loop budgets and anti-runaway

`/dr` is expensive (multi-source web research + skill authoring + hub sync per
call). A naive "research every gap, then re-expand, forever" loop can flood the
skill index and burn enormous time. Guards:

| Guard | Default | Why |
| --- | --- | --- |
| `maxConcepts` | 8 / run | Cap total concepts researched per run (a related cluster counts each concept; `/dr` calls may be fewer). |
| `maxRounds` | 3 | Cap frontier re-expansions; the frontier rarely yields after 3. |
| `budgetMinutes` | unset | Optional wall-clock cap (`--budget-minutes=N`); checked after each `/dr` return and each round per the canonical §Budget contract (cited above); remaining budget propagates into each `/dr` invocation. |
| Viability gate | `Via ≤ 1 → SKIP` | Never spend a run on an un-sourceable concept. |
| Novelty gate | `Nov = 0 → SKIP` | Never re-research a fresh duplicate. |
| Hub-routing | per `/dr` | Route into hub `references/`, not new top-level skills — keeps the index small. |
| dryRun first | recommended | On an unfamiliar subject, plan-only first so the user approves scope before spend. |

State the budget you used in the report so a re-run can pick up where you left
off. If the user gives no budget, use defaults and say so.

## Dedup against coverage (the cheapest win)

The single biggest waste is researching something you already have. Before any
`/dr` call, confirm the concept is still a GAP — coverage can change *during* the
run because `/dr` writes new tree nodes as it goes. Re-checking the tree before
each call (not just once at Step 2) prevents a re-expansion round from queuing a
concept a previous batch already filled. These re-checks are scoped: query
only the candidate (plus its 2–3 alias variants, per the mandatory alias rule
above) — never re-page the whole tree mid-run.

## Worked loop trace — subject "prompt-optimization algorithms"

```
Round 0  map → 27 candidates across 5 neighborhoods (≥5 each — floor met)
         inventory → HAVE: APE, OPRO, ProTeGi (in prompt-deep-optimizer)
                     GAP: GEPA, TextGrad, EvoPrompt, DSPy/MIPROv2, PromptBreeder, …
         score → 24 gaps scored; 5 ≥ 3.2; select all 5 (budget 8, room left)
         /dr "GEPA, TextGrad, EvoPrompt"  (related cluster → one skill)
         /dr "DSPy MIPROv2"
         /dr "PromptBreeder"
Round 1  re-expand on the 5 new concepts
         new candidates: "reflective evolution", "Pareto prompt fronts"
         score → both < 3.2 (low Viability: thin sources) → SKIP, logged
         0 new above-threshold gaps  →  empty round #1
Round 2  re-expand → 0 new candidates  →  empty round #2
         blind saturation gate → fresh-context probe proposes 1 concept;
         scored 2.8 < 3.2 → not corroborated → gate PASSES
         FRONTIER SATURATION reached (2 empty rounds + gate; Round 0 is the
         one productive round — precondition (i) met)
Optimize  /sko on the 3 new/updated skills with --no-sync (all standalone —
          no hub gained a spoke, so the item-2 hub re-audit is a no-op this
          run; the cluster skill's embedded algorithm-selection prompt is
          covered inside its sko run — no separate /pdo); one batch sync
          after (Step 9c)
Verdict   Reached by: frontier saturation (SATURATED-FRONTIER).
          New-information rate: R1 0/26 (0%; 2 new candidates scored, both
          below threshold), R2 0/26 (0%), gate 0 corroborated.
          Budget used: 5/8 concepts via 3 /dr calls; 2/3 rounds.
```

The trace shows the ideal shape: one productive round, then the frontier
goes quiet for two rounds, and the loop stops on *evidence* (empty above-threshold
rounds plus a passed blind gate) with budget to spare — not because it ran out
of room.
