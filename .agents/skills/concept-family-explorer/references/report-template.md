# Step 10 report template

The fixed output shape for a Concept Family Explorer run (SKILL.md Step 10). Fill
every `<…>` placeholder and keep the section order. The deterministic
`cvs_check.py` verify and the telemetry close run around this template, in the
SKILL body — they are logic, not part of the skeleton below.

```markdown
# Concept Family Explorer — <subject>
*Run: <date> · concept-count budget: <user-supplied n | none>, maxRounds=<n>[, budgetMinutes=<n> · wall: <m> min] · threshold: <x>/5*

## Conceptual family map
<the 5-neighborhood map; mark HAVE / STALE / GAP>

## Scored gap table
| Concept | Rel | Use | Nov | Int | Via | CVS | Decision | Why |
|---------|-----|-----|-----|-----|-----|-----|----------|-----|

## Researched this run
<concept → skill ID (new/updated, hub or standalone) → sources → tree node → persisted (local-sources + SELECTED_SKILLS pin + hub) if repo-native>

## Skipped and failed (saturation evidence)
<deliberate skips: concept → CVS → reason below threshold>
<failed gaps: concept → /dr failure reason (errored / below authority threshold)>

## Optimization results
<spoke skill → skill-optimizer findings fixed → prompt-deep-optimizer (if any)>
<hub skill (re-`/sko`'d for its new spokes) → findings fixed / hub→spoke edges seeded>

## Handoffs
<MISPLACED concepts (tree parent vs actual hub disagree) → one
skill-tree-architect handoff row each — never re-filed from here>

## Saturation verdict
Reached by: [frontier saturation (SATURATED-FRONTIER) | coverage saturation (SATURATED-COVERAGE) | budget exhausted (BUDGET_EXHAUSTED) | SATURATION-DISSENT] — status token doubles as the telemetry exit_status.
State the per-round new-information rate (new above-threshold gaps /
cumulative candidates scored) — treat ~5% as a starting default, not
validated truth.
Concepts processed: <n>/<explicit maxConcepts | all queued> via <k> /dr calls; <r>/<maxRounds> rounds[; wall <m> min]   ← mandatory line
<if budget: list the unresearched above-threshold queue + suggested re-run; include wall time when budgetMinutes was set>

## Updated concept tree
<new/updated nodes and their parent/child links>
Tree sync (Step 9d), one line per tree:
- mdb-context-hub: <written | skipped: reason>
- global-ai-hub (`~/.global-ai-hub/concept-tree/tree.json`): <written N add / M update, K queued | REFUSED: reason | skipped: reason>
- website (`concept-tree/tree.json` → `site/src/data/tree.json`): <written + regenerated, branch <name> | REFUSED: reason | skipped: reason>
Never write "synced" for a tree the helper did not write.
```
