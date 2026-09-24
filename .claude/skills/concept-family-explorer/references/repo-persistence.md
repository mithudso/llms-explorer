# Repo-native persistence & placement (Step 6b procedure)

The full procedure behind SKILL.md Step 6b. **Authoritative contract:** `/dr`'s
Phase 3 (`~/.claude/commands/dr.md`) and the header comment of
`scripts/persist-spoke.mjs` in the mdb-context-hub repo — this file defers to
both and does not re-specify them. Repo-native only: a no-op in plain
`~/.claude/skills`, where `/dr` installs and persists directly.

## When this applies

Skills authored via `tam_create_skill` in the mdb-context-hub repo (the
repo-native path, and the fallback when `/dr`'s research backend is
unavailable). A `tam_create_skill` skill lands in `local-sources/<id>/` and
`skills/registry.json` but is **not durable**: the next `npm run sync:skills`
regenerates the pack from `SELECTED_SKILLS` and wipes any skill not pinned
there.

## Procedure (per skill created this run)

1. **Install first (precondition).** Ensure the skill's markdown is installed
   under `~/.claude/skills` — hub reference at
   `~/.claude/skills/<hub>/references/<id>.md`, or standalone
   `~/.claude/skills/<id>/SKILL.md`. `persist-spoke.mjs` resolves its source
   there and hard-fails otherwise ("no source for '<id>'"). For skills authored
   only via `tam_create_skill`, install the markdown from `local-sources/<id>/`
   before persisting.
2. **Persist.** From the mdb-context-hub repo root, run
   `node scripts/persist-spoke.mjs <skill-id> [--hub <hub-id>]` once per
   skill/spoke. It writes the `local-sources/<id>/` pair, **idempotently** pins
   the `SELECTED_SKILLS` entry at the auto-persist marker, and best-effort
   upserts `skills/registry.json` for immediate discoverability. Pass `--hub`
   for a hub reference (routes its family tags); omit for a standalone skill.
   Re-running is safe.
   - **Never hand-edit `SELECTED_SKILLS` or `registry.json`** (dr.md Phase 3
     step 2). If the script is unavailable, the fallback is
     `tam_create_skill`/`tam_update_skill` — never a hand-pin.
3. **Concept tree (every skill, every path).**
   `tam_concept_tree_upsert(concept, skillId, parentConcept=<owning hub's
   concept node>, …)`, then `tam_concept_tree_link(<hub concept>,
   <new concept>)`. The link is **required**: `upsert` sets the child's
   `parentConcept` back-pointer but does *not* append to the parent's
   `childConcepts` forward list — without the link the spoke is not "under" the
   hub when the tree is read parent-down. Match the hub by domain; if no hub
   fits and the new family is large, hand placement to Step 9b
   (skill-tree-architect). Tag the manifest with the hub family
   (`programming-languages`, `da-*`, …); `--hub` handles the
   `SELECTED_SKILLS`-side family tags.
4. **Verify reachability.** After upsert + link, `tam_concept_tree_get` the
   parent and assert the new concept appears in its `childConcepts` before
   declaring the skill persisted; on failure re-run `tam_concept_tree_link`
   and re-verify. (The live tree already contains an anonymous node with no
   concept name — unswept integrity defects are real, and an unlinked child is
   invisible to every future parent-down inventory.)
5. **Sync once, verify it stuck — AT STEP 9c, not here.** Steps 1–4 run per
   skill as its agent returns; this step and steps 6–7 are deferred to
   SKILL.md Step 9c (after the Step 9b rebalance, which can re-file skills) and
   run ONCE per run. The sync itself: batch-canonicalize with
   `node scripts/persist-spoke.mjs <last-id> --hub <hub> --sync` (or
   `npm run sync:skills`) — the batch form dr.md Phase 3 step 3 addresses to
   concept-family-explorer by name; per-skill `--sync` is wasteful in a batch.
   Confirm each id survives (`grep` the id in `skills/registry.json`, confirm
   `skills/contexts/<id>.md` regenerated). Missing post-sync ⇒ not pinned —
   re-run step 2 and re-sync.
6. **Repair referents (at Step 9c, with step 5).** If this run routed a topic
   into a hub or created/folded a spoke, run
   `node ~/.claude/skill-consolidation/referents.mjs --repair` (dry-run first
   to inspect, then `--apply`). Skip for standalone-only runs.
7. **Workflow log (at Step 9c, with step 5).** Follow the repo rule for the
   resulting repo change: append `prompts.md`, update `memory.md`, bump the
   patch version in `package.json` / `package-lock.json` /
   `mcp-server/src/constants.ts`; note that `sync:skills` ran.

Checkpoint: set the concept's `persisted: true` in
`~/.claude/skill-consolidation/run-state/cfe-<subject-slug>.json` only after
steps 2–4 succeed (see `references/run-state-and-resume.md`).
