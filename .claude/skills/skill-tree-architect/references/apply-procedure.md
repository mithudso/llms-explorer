# Phase 3 APPLY — full per-step procedure

Extracted from `SKILL.md` Phase 3 (the body keeps the step skeleton + constraints to stay inside
its length budget; this file is the authoritative step detail). Read this file before any
mutating step. The failure rail and the explicit-go definition live in `SKILL.md` Phase 3 and
apply to every step here. Section numbers mirror the SKILL.md Phase-3 step numbers; steps with
no extra detail (3, 5, 6, 7, 9) have no section here.

## §1 — Snapshot (canonical backups convention)

Copy EVERY file the run will modify into `~/.claude/skill-consolidation/backups/<run>/`:

- `tar` the affected family directory **skills-root-relative**, so the Phase-4 restore command
  (`tar -xzf … -C ~/.claude/skills`) unpacks to the right place:
  `tar -czf ~/.claude/skill-consolidation/backups/<run>/<family>.tar.gz -C ~/.claude/skills <family-dirs>`
  (a naive absolute-path `tar` stores `Users/…/skills/…` paths and restores to a wrong nested
  dir), PLUS
- the out-of-family top-level SKILL.mds that a `referents.mjs --repair` dry-run (run it without
  `--apply`) says it would touch.
- `skill-pack.config.mjs` is git-backed in mdb-context-hub (§8 covers it); it is not in the
  snapshot set.

## §2 — Fold or re-file

### §2a — Full-family fold

Edit `<family>-mapping.json`, then `node build.mjs <family>-mapping.json`. This folds spokes
into `<hub>/references/`, and writes the routing table + family manifest.

### §2b — Single re-file (the complete crossroute sequence)

Invocation: `node crossroute.mjs <new-hub-family-manifest.json> <hubName> <spoke> [--nested]`
(pass the NEW hub's family manifest; `--nested` for multi-file spokes).

`crossroute.mjs` adds the spoke to the NEW hub **only**: always complete the five-step cleanup
below (crossroute performs none of it; steps 1–3 are manual edits, 4–5 are tool/MCP calls).

1. Remove the spoke's row from the OLD hub's family manifest.
2. Delete the OLD hub's routing-table row for the spoke.
3. Move the old `references/<spoke>.md` aside (or banner it superseded).
4. `node referents.mjs --repair --apply`.
5. After any re-file, re-upsert + `tam_concept_tree_link` the spoke's tree node to the new hub.
   If the tam MCP is unavailable, record `tree-link: deferred` in the Phase-4 report and
   continue — the tree link is a remote signal and never trips the Phase-3 failure rail.

Why the sequence is mandatory: unresolved double-ownership makes spoke→owningHub resolution
ambiguous; `hub-registry.mjs` already has to special-case `consolidation-manifest.json` as a
known byte-for-byte duplicate (excluded by default). Do not add another.

## §4 — Spoke-dir removal and the HOT-spoke rule

Fold/remove a spoke dir **only after verifying its `references/<spoke>.md` copy exists**.

If `tiering/tier-state.json` says the spoke is HOT (temporarily promoted standalone), route the
removal through `tiering/tier.mjs --demote <spoke> --apply` (dry-run first by omitting
`--apply`), NEVER raw `rm`. `tier.mjs` does the drift-preserving one-way sync (standalone →
`references/<spoke>.md`) before removal and chains `referents.mjs --repair`.

A manual reconcile (diff banner-stripped content via `tiering/lib.mjs` `stripBanner`) is needed
only on two-sided divergence: the hub reference was ALSO edited since promotion, which
`tier.mjs` would blindly overwrite.

**Live anchor:** as of 2026-06-11, `deep-research-methods` was HOT with 27 diverged lines,
standalone newer; a copy-exists-only check plus raw `rm` would have destroyed them.

## §8 — Hub-registry sync (different repo; user commits)

Add new hub ids to `SELECTED_SKILLS` in
`~/Documents/GitHub/mdb-context-hub/scripts/skill-pack.config.mjs`, then `npm run sync:skills`
(regenerates the live registry). Review-required: this is a separate git-backed repo; the user
commits the change. If the repo is absent on this machine, record `registry-sync: deferred` in
the Phase 4 report and hand the step to the user.
