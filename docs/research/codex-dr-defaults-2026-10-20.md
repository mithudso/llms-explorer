# Codex DR defaults and completion artifacts

Codex `/dr` defaults to `gpt-6-luna` at `max` effort. Its standard adaptive
lane runs one research pass with a deliberate scout for papers, source code,
issue threads, forums, engineering blogs, and postmortems. A relevant deeper
source triggers one additional Luna/max pass. The second pass receives the
first pass's discoveries as seed sources. Missing source/claim floors and
missing or malformed scout reports also trigger the follow-up. A complete
docs-only result meeting the floors stops after the first research pass.
The merge and scope check use `gpt-6.1-sol` at `medium`.

Explicit model and effort flags apply to the scout and follow-up. Quick and
saturate retain their explicit contracts: one low-effort pass and two
independent max-effort passes, respectively, using Luna by default.

Every successful Codex `finish`, including a run dispatched by CFE or another
orchestrator, now creates per-concept and topic packs in both locations:

- `/Users/mitch.hudson/.global-ai-hub/llms-concepts/<slug>.llms/`
- `/Users/mitch.hudson/dev/llms-explorer/outputs/llms-concepts/<slug>.llms/`

Each pack contains `llms.txt`, `llms-full.txt`, `llms-small.txt`,
`llms-facts.txt`, `llms-vocabulary.txt`, `units.jsonl`, `concept-graph.json`,
and `manifest.json`. Compilation retains every claim, its original source
URLs, its confidence, and any verification date. Undefined vocabulary terms
remain explicit research gaps. They do not become unsourced definitions.

Completion independently merges the researched concepts into:

- `/Users/mitch.hudson/.global-ai-hub/concept-tree/tree.json`
- `/Users/mitch.hudson/dev/llms-explorer/concept-tree/tree.json`

Each tree keeps its existing nodes, placement, and slugs. A slug difference
between trees receives the corresponding pack in both locations. Tree
validation runs before writes. Existing packs cannot be overwritten by a
different concept. Existing changed packs and trees receive backups under
the run's `artifacts/backups/`. The run records `artifacts/receipt.json` and
`codex_artifacts` in its manifest. An export failure stops finalization so the
same command can be retried. Completed concepts in a budget-exhausted run get
packs marked `BUDGET_EXHAUSTED`. Empty runs and failed verification do not
promote research. Local updates do not commit, push, or publish.

The generated skill is
`/Users/mitch.hudson/dev/llms-explorer/.agents/skills/dr/SKILL.md`.
The tracked generator and adapter preserve these defaults across future
Claude-source syncs. `LLMS_EXPLORER_REPO` selects another repository path.
The shared Claude runtime stays unchanged.

Validation: 37 focused tests pass, Ruff passes, and the 19-file skill sync
check is clean. Tests exercise the shared research state machine with model
responses substituted, then compile real llms packs and finish against two
temporary trees. They check seeding, pass counts, source retention, claim
counts, both pack copies, idempotence, collisions, partial runs, and retry
after export failure. Generated llms fixtures have no High lint findings.
This change did not run another paid research benchmark.
