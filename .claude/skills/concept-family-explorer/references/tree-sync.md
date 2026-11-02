# Step 9d — sync the site and global-ai-hub concept trees

The procedure behind SKILL.md Step 9d. `scripts/sync_trees.py` (this skill's
own helper; stdlib only) does the writing — this file says what to feed it and
what to check afterwards.

## Why a separate stage

A run touches **three** tree surfaces; `/dr` covers the first (and the hub file node as it finishes), but nothing writes the website file or corrects parentage after the 9b rebalance:

| Surface | Written by | Where |
| --- | --- | --- |
| mdb-context-hub tree | Step 6b (`tam_concept_tree_upsert` + `_link`), where the MCP exists | MCP; absent on machines without it |
| hub node, per concept | `/dr` v3 `dr_run.py finish` (parent as of that moment) | `~/.global-ai-hub/concept-tree/tree.json` |
| **global-ai-hub tree** | **Step 9d** | `~/.global-ai-hub/concept-tree/tree.json` (+ `RESEARCH_QUEUE.md`) |
| **website tree** | **Step 9d** | `<llms-explorer>/concept-tree/tree.json` → `site/src/data/tree.json` (generated) and `site/src/data/concepts/<slug>.json` (reader pages) |

The two file trees are enriched independently and hold different node sets
(hub ≈ 60 nodes, site ≈ 500). **Never copy one over the other** — a straight
copy has clobbered the site tree three times (`scripts/refresh_snapshot.sh`
carries a shrink guard for exactly this). The helper merges each in place.

It runs **after Step 9b**, so `parentConcept` is the *final* placement, not the
one `/dr` wrote before a re-file moved the spoke.

## 1. Build the spec

One JSON file, from the run-state `researched[]` rows plus the Step 9b
placement:

```json
{"researched": [
   {"concept": "Semantic Layer", "skillId": "da-data-engineering-platform",
    "parentConcept": "Data Engineering Platform",
    "childConcepts": ["Metric Store", "Headless BI"], "aliases": ["metrics layer"],
    "sourcesCount": 7, "conceptsCount": 12}],
 "queue": [{"concept": "Data Contracts", "parentConcept": "Data Engineering Platform", "mode": "dr"}]}
```

- `researched` — every concept researched **or refreshed** this run. `skillId`
  must be installed (the helper refuses an uninstalled one — it would make the
  node's "read the skill" link dead). Include `childConcepts` the `/dr` run
  discovered: known-but-unresearched children become the tree's **frontier**.
- `queue` — only above-threshold gaps the run did not reach
  (`BUDGET_EXHAUSTED`, `SATURATION-DISSENT`). Below-threshold skips are
  saturation evidence for the report, **not** queue entries — queueing them
  would flood the frontier with concepts the run judged not worth researching.
- `scores` (optional, **write it every run**) — `{"<concept>": {"cvs": 3.85, "decision":
  "RESEARCH", "neighborhood": "children"}}` for every row of the run's scored gap table,
  skipped rows included. The helper stores the Concept Viability Score on the concept's node
  (`cvs`, `cvsDecision`, `cvsScoredAt`, `cvsSubject`) when it has one, else in
  `concept-tree/cvs-scores.json`, and tags queue lines `| CVS: \`3.85\``. The site, the
  explorer and the auto-researchers read it (they skip anything below 3.2). Add
  `"subject": "<run subject>"` at the top level of the spec to stamp the run. A `cvs` key
  directly on a `researched` or `queue` item works too.
- `researchedAt` is optional (defaults to today). On a refresh the helper
  advances `researchedAt` and keeps `firstResearchedAt`, per `/dr`.

## 2. Isolate the site repo

The site tree lives in a deploy repo (`main` is only advanced by the CI-gated
snapshot → promote pipeline). Work on a branch or worktree of llms-explorer and
pass it with `--repo`. The helper **refuses** `--apply` for the site target on
`main`/`master`. Never push `main`.

## 3. Dry run, then apply

```sh
S=~/.claude/skills/concept-family-explorer/scripts/sync_trees.py
python3 $S --spec run.json --repo <worktree>                 # plan only; writes nothing
python3 $S --spec run.json --repo <worktree> --apply --regen # write both, rebuild site data
```

Per target the helper: merges → runs `ConceptTree.validate()` before and after →
**refuses to write** if the node count would shrink or the upsert adds any
structural problem (dangling parent, non-reciprocal link, duplicate, slug clash,
uninstalled skill) → takes a `tree.json.bak-sync-<UTC>` backup (newest 3 kept) →
writes atomically. Pre-existing validate problems are left alone; it only blocks
*new* ones. Re-running the same spec is a byte-identical no-op.

Behaviours worth knowing:

- **Missing parent.** A parent with no node *in that tree* is not invented — the
  concept becomes a root there and the line says `-> root`. Expect this on the
  hub tree, which lacks most of the site tree's mid-level nodes. No stub nodes.
- **Moved placement.** If Step 9b re-filed a spoke, the helper removes it from
  the old parent's `childConcepts` and adds it to the new one.
- `--regen` (site only) runs `site/tools/gen_tree.py`, and
  `site/tools/gen_concepts.py` only when `~/.global-ai-hub/llms-concepts/<slug>.llms/`
  exists for a touched slug. `gen_concepts.py` rebuilds *every* pack from the live
  hub — read the printed `git diff --stat` and drop unrelated pack churn before
  committing.

## 4. Verify

- Hub: `HUB_DIR=~/.global-ai-hub python3 ~/.global-ai-hub/scripts/concept_tree.py show "<concept>"`
  for each researched concept, and `… validate` shows no new problems.
- Site: regenerate to a scratch path and diff against the committed file (this is
  the CI check, `.github/workflows/site.yml`):
  `python3 site/tools/gen_tree.py --out "$TMPDIR/tree.json" && diff site/src/data/tree.json "$TMPDIR/tree.json"`.
  Then `uv run --directory hub pytest ../site/tests`.

## 5. Persist

- **Site repo** — append `prompts.md` / `memory.md` (repo Workflow Log Rule),
  commit on the branch as `feat(concept-tree): <subject> …`, and push the branch
  / open a draft PR only where the user has authorised commits. Deploy is the
  snapshot → CI → promote pipeline, not this stage.
- **Hub** — the change is a working-tree edit in `~/.global-ai-hub`; commit it
  locally with the hub's usual hygiene. Do not push from here.

## Failure handling

One target refusing never aborts the run or changes the saturation verdict: the
other target still writes, the run continues to Step 10, and the report's
**Updated concept tree** section says `hub: written · site: REFUSED (<reason>)`
with the backup path if any. The helper is idempotent and merge-only, so a
resumed run (`optimizing` / `optimizing:budget`) simply re-runs Step 9d. If the
site repo or hub dir is absent, state that and skip that target — say so, never
report it as synced.
