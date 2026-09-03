# Step 9 optimization pass — certification evidence & hub-card mechanics

Full mechanics behind SKILL.md Step 9 items 1–2. The body keeps the decision
rules; this file carries the evidence semantics and rationale.

## Spoke certification (item 1)

A spoke is **CERTIFIED** when a `skill-optimizer` run this session exited
CLEAN. Two producing paths:

- `/dr` Phase 2 step 4 (its own sko gate), or
- the install-write PostToolUse hook
  `~/.claude/hooks/skill-change-trigger-optimizers.sh` being honored. The hook
  fires on `SKILL.md` writes only — NOT on hub `references/<name>.md` writes or
  repo-native `local-sources/` writes; on those paths the `/dr` run itself is
  the certification.

**Evidence rules.** Primary evidence is this session's own record of the CLEAN
run. A same-day `exit_status: CLEAN` row in
`~/.claude/skill-consolidation/optimizer-telemetry.jsonl` corroborates when
present — but telemetry appends are fail-safe, so a missing file or row never
certifies and never de-certifies; it just means no corroboration.

**What certification buys.** Certified spokes get `/sko <id> --meta --no-sync`
only — structural mode: Pass I collision check against the now-expanded sibling
set, Pass O peer edges, routing-surface lint. Add `--eval` only when a
collision is suspected. A `/dr`- or hook-certified CLEAN run already did the
content passes — **never stack a third full content pass** on the same spoke in
one session.

**Why `--max-iter=1` is not the skip.** A single full iteration still runs
every content pass plus Pass H's ~60-call trigger eval — nearly full cost for
a spoke that already passed. `--meta` is the cheap re-check; `--max-iter=1` is
a budget cap, not a certification shortcut.

Uncertified spokes get the full loop: `/sko <skill-id> --no-sync` — multi-pass
quality gate, Medium+ fixes, reciprocal peer references.

## Hub re-audit (item 2)

**Collection.** The distinct set of hubs that gained a spoke this run: look up
each new spoke's `parentConcept` node in the concept tree and take its
`skillId`. Dedupe — a hub that gained N spokes is optimized once.

**Ordering.** Run `/sko <hub-id> --no-sync` on each hub **after** all spokes,
so the pass sees the finalized spoke set.

**Why hubs keep a full loop** (not `--meta`): `/dr` and the hook do audit
updated hubs mid-run, but every mid-run hub audit saw only a partial family —
only the end-of-run pass runs against the finalized spoke set. Routing a new
concept into a hub changes the hub's children, so the hub's **own card** must
be re-audited against the now-expanded family:

- description/keywords — the coverage advertisement,
- TRIGGER/SKIP routing surface,
- trigger-collision check against each new spoke,
- description-length budget.

Running `/sko` on the spokes alone seeds the hub→spoke deferral edge
(spoke-side Pass O edits the hub to defer down) but never re-audits the hub's
own card — so the hub's description, routing surface, and collision check
drift stale as the family grows.

**Scope boundary.** Re-audit only each *changed hub's own* card — don't walk
up to the family router. Whole-tree shape, placement, and cap balance are
Step 9b (skill-tree-architect).
