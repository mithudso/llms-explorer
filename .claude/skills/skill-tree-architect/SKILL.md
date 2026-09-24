---
name: skill-tree-architect
description: >-
  Whole-tree architect for the ~/.claude/skills hub-and-spoke taxonomy: audits tree-wide
  description-cap headroom (>1000/>1536), hub balance, and cross-hub placement, then drives the
  skill-consolidation toolchain to rebalance/reshape for a new family. TRIGGER: rebalance /
  restructure / optimize the skill tree; is my taxonomy optimal; skill-tree health check; skills
  folder is a mess, reorganize it; reshape for a new family; concept in the wrong hub or family;
  hubs over the cap / too big / should split; audit hub-and-spoke placement; find misplaced
  spokes; hub the homeless skills. SKIP: ONE skill's content/triggers/peer-seeds →
  skill-optimizer; what to build → concept-family-explorer; a prompt → prompt-deep-optimizer /
  phe; detect a single NEW ≥5 homeless family → run detect-candidates.mjs directly; lint one
  skill → run meta-validate.mjs directly.
whenToUse:
  - "rebalance or restructure the whole skill tree"
  - "is my skill taxonomy in an optimal shape"
  - "reshape the tree to absorb a new large skill/concept family"
  - "are any concepts filed under the wrong hub or family"
  - "which hubs are over the description cap (1000/1536) or too big to fit"
  - "find misplaced spokes / audit hub-and-spoke placement"
  - "hub the homeless standalone skills"
  - "run a whole-tree skill analysis / health check"
whenNotToUse:
  - "optimize, audit, or fix ONE skill's content/triggers/peer-seeds (use skill-optimizer)"
  - "detect one new ≥5 homeless family to hub (run detect-candidates.mjs directly)"
  - "decide which NEW skills to build for a domain (use concept-family-explorer)"
  - "structural lint of a single skill (run meta-validate.mjs directly)"
  - "optimize a prompt (use prompt-deep-optimizer / phe)"
version: 1.4.0
category: meta
updated: 2026-07-20
model: claude-opus-5
effort: xhigh
metadata:
  changelog:
    - "Full history: references/CHANGELOG.md"
    - "2026-07-20 sko v1.3.0->v1.4.0 — Pass H 10/10->10/10 pos, 0/10->0/10 neg (predicted); 32 Medium fixed across 4 fix rounds + 2 blind gates"
    - "2026-07-20 v1.3.0->v1.4.0 — sko full-profile run: description tightened (TRIGGER at char 250, terse anchors); script SKIP targets rephrased as direct-run tools; meta-validate hard-gate list corrected; cap tiers relabeled by severity+cause; single-cap --desc-cap semantics + standalone desc sweep; Phase-1 tool-failure rule; Phase-3 explicit-go + failure rail; healthy-tree exit; apply detail extracted to references/apply-procedure.md; model/effort keys added"
    - "2026-06-28 v1.2.0->v1.3.0 — Phase 3 step 9 + Phase 4 step 1 gate: regenerate the consolidated SKILLS-INDEX (node gen-skills-index.mjs) after the tree mutates, then --check it in VERIFY, so the cross-family index never drifts after a rebalance"
keywords:
  - skill tree
  - hub and spoke
  - taxonomy
  - rebalance
  - restructure
  - description cap
  - misplaced spoke
  - cross-hub placement
  - hub balance
  - homeless skill
  - reshape tree
  - skill consolidation
  - skill tree health check
  - reorganize skills folder
triggers:
  - skill-tree-architect
  - rebalance skill tree
  - restructure skill tree
  - skill taxonomy
  - hub balance
  - misplaced spoke
  - audit placement
  - whole-tree skill analysis
  - skill tree health check
tags:
  - meta
  - skills
  - taxonomy
  - consolidation
origin: local
related_skills:
  - skill-optimizer
  - concept-family-explorer
  - claude-code-skills
---

# Skill Tree Architect

You operate at the **whole-tree** altitude: the shape and balance of the entire
`~/.claude/skills` hub-and-spoke taxonomy. Per-skill quality belongs to `skill-optimizer`;
single-new-family detection belongs to `detect-candidates.mjs`. You **orchestrate the existing
toolchain in `~/.claude/skill-consolidation/`; never reimplement it.**

**Read `~/.claude/skill-consolidation/HUB-STRATEGY.md` first.** It is the canonical strategy
(the ≥5-sibling hub threshold, the build/maintain pipeline, reversibility, referent integrity).
This skill adds the one analytic that strategy doc's tools lacked, a tree-level placement +
cap-balance audit, and sequences every tool around it. Mutating phases follow the canonical
contract at `~/.claude/skill-consolidation/convergence-and-severity.md` (snapshots, telemetry,
exit statuses, budget: cite it, never restate it).

## Phase 1 — ANALYZE (read-only; always safe)

Run the whole block (all four analytics) and read them together; none mutates anything:

```bash
node ~/.claude/skill-consolidation/audit-placement.mjs --desc-cap 1000 --json   # cap headroom vs 1000, hub balance, MISPLACED spokes, homeless best-fit
node ~/.claude/skill-consolidation/detect-candidates.mjs      # NEW ≥5 homeless families (dir-name clusters)
for d in ~/.claude/skills/*/; do [ -d "$d/references" ] && node ~/.claude/skill-consolidation/meta-validate.mjs "$(basename "$d")" --json; done
# standalone desc-cap sweep — audit-placement caps HUBS only; this covers homeless/standalone skills
# (parse-tolerant: a skill with broken frontmatter prints PARSE-ERR instead of killing the sweep):
python3 -c 'import pathlib,yaml
for p in sorted(pathlib.Path.home().glob(".claude/skills/*/SKILL.md")):
    try:
        d = yaml.safe_load(p.read_text().split("\n---\n")[0].lstrip("-\n"))
        n = len(str(d.get("description", ""))) if isinstance(d, dict) else 0
    except Exception: print(p.parent.name, "PARSE-ERR"); continue
    if n > 1000: print(p.parent.name, n, "HIGH" if n > 1536 else "MEDIUM")'
```

- `audit-placement.mjs` is the analytic this skill owns: per-hub description length vs the
  **two-tier cap** (>1000 chars = Medium, the Glean import cap, single definition: sko Pass M;
  >1536 = High, harness listing truncation), spoke counts, **misplaced spokes** (a spoke whose
  trigger vocabulary fits a sibling hub better than its current owner; heuristic), and homeless
  best-fit. The tool checks ONE cap per run (`--desc-cap`, default 1536): run it at 1000 and
  derive the >1536 tier from each entry's `descLen` in the JSON output (or run it twice).
- `meta-validate.mjs` is the **hard gate**: it exits 1 on its High findings (spoke-copy-exists,
  dangling routing rows, frontmatter/naming/manifest/file-folder errors). It also reports Medium
  findings that do NOT gate: e.g. circular SKIP, description cap, tier-config presence.
- `detect-candidates.mjs` only sees UNHUBBED skills by dir-name; it cannot see a misplaced
  *spoke*. `audit-placement.mjs` covers that blind spot; run both.
- **Concept-tree crosswalk (targeted, never full-tree):** for each spoke audit-placement flags
  MISPLACED, and any spoke you plan to re-file, pull its tree node via
  `tam_concept_tree_list(skillId:<id>)` or `tam_concept_tree_search` (a handful of calls, not a
  page-through). If the concept tree / tam MCP is unavailable, skip the crosswalk, note it in the
  report, and do not block APPLY on it (the tool-failure rule covers the four local analytics,
  not this remote signal). Treat tree-vs-hub disagreement as "one surface is stale — adjudicate", NOT as
  corroboration: the tree is currently the less-maintained surface (its parents still name
  pre-consolidation skills), so tree parentage must not boost a re-file's rank. A full
  dangling-skillId sweep of the tree is a one-time scripted reconciliation (offline join of the
  tree list vs manifests + installed dirs), not an every-run input.
- **Tool-failure rule:** if any of the four Phase-1 analytics or the `referents.mjs --status`
  baseline read errors or crashes, record it as N/A, do not compute a partial baseline, and do
  not enter APPLY until it re-runs clean. (Only the Phase 3 step 9 index regeneration is
  non-blocking by design; the concept-tree crosswalk is a remote signal outside this rule.)

End Phase 1 by capturing the **tree-health baseline**: `audit-placement.mjs --desc-cap 1000
--json` counts (overCapHubs, misplacedSpokes, capPct distribution, homeless — pin the same
`--desc-cap` in Phase 4 or the overCapHubs delta compares different caps), `referents.mjs
--status` dangling count, and the meta-validate High/Medium aggregates. Phase 4 re-captures the
same numbers; the delta is the rebalance's evidence.

## Phase 2 — PLAN

Produce a ranked plan. Tag every item **safe-auto** or **review-required**:

| Finding | Action | Risk |
| --- | --- | --- |
| Dangling referent (`referents.mjs --status`) | `referents.mjs --repair --apply` | safe-auto (idempotent, ledgered) |
| Hub description **>1536** (High: harness listing truncation) | split by sub-domain, OR compress prose **keeping every spoke keyword** | review-required |
| Hub description **>1000** (Medium; def: sko Pass M) | compress prose **keeping every spoke keyword** | review-required |
| Standalone skill desc >1000 / >1536 (Phase-1 sweep) | hand each to **skill-optimizer** (its Pass M owns the rewrite) | safe-auto to file; review-required to edit |
| PARSE-ERR from the standalone sweep | hand to **skill-optimizer** (strict-YAML frontmatter fix; these files evade the hub-only meta-validate loop) | safe-auto to file |
| Misplaced spoke, margin **≥ 0.25** (`audit-placement.mjs` suggestedScore − ownerScore) | re-file via the full `crossroute.mjs` sequence (apply-procedure §2b) | review-required |
| Misplaced spoke, margin 0.15–<0.25 (the tool's default flag threshold) | watch | informational |
| Tree↔hub parentage disagreement | adjudicate; usual case is a stale TREE node → re-upsert `parentConcept` + `tam_concept_tree_link` to the actual hub; re-file via `crossroute.mjs` only when audit-placement independently flags the spoke | review-required |
| New ≥5 homeless family | full consolidation per `auto-hub-agent-prompt.md` | review-required |
| Hub with ≥14 spokes (audit-placement `HIGH_SPOKES`), cap OK | watch / split later | informational |

**Never drop spoke trigger enumeration to save characters — the enumeration IS the routing signal**
(only the hub name + description are in-context until the hub is chosen). Fix over-cap by splitting
or compressing prose, never by deleting keywords.

**Zero-item plan (healthy tree):** if Phase 2 yields no actionable items, report the Phase-1
tree-health baseline with "no action required" and stop; APPLY and VERIFY do not run.

## Phase 3 — APPLY (explicit go only; the step-1 snapshot is the recovery rail)

**Explicit go** means the operator has confirmed the ranked Phase-2 plan: safe-auto items may
proceed on a blanket confirmation; every review-required item needs per-item approval. No
confirmation, no mutation.

**Failure rail:** on any step error after a write has landed, stop. Restore from the step-1
snapshot (canonical contract, "Pre-write snapshot & rollback") and reverse this run's
`referents-ledger.json` entries before retrying. Never continue past a half-applied step.
Do not substitute git for the snapshot: `~/.claude/skills` may be a git repo on a given
machine, but its tree state is routinely part-untracked/uncommitted (check
`git -C ~/.claude/skills status` if curious) — only the snapshot is a guaranteed rollback.

Drive the existing tools in order; never hand-roll a step. Only `referents.mjs` and `tier.mjs`
default to dry-run (pass `--apply` explicitly to write); `build.mjs`, `crossroute.mjs`, and
`fix-crosshub-generic.mjs` mutate on invocation — snapshot (step 1) before touching them. **Read
`references/apply-procedure.md` before mutating** — it holds the full per-step sequences: the
snapshot set, the complete single re-file (crossroute) checklist, the HOT-spoke demote
procedure with its live anchor, and the hub-registry sync. The step skeleton:

1. **Snapshot (canonical backups convention):** copy EVERY file the run will modify into
   `~/.claude/skill-consolidation/backups/<run>/` (details: apply-procedure §1).
2. **Fold or re-file:** full family via `node build.mjs <family>-mapping.json`; single spoke via
   the complete `crossroute.mjs` sequence — never leave double-ownership (apply-procedure §2).
3. Author/adjust the hub `SKILL.md` (absorb spoke TRIGGER vocab; SKIP → sibling hubs only).
4. Remove a spoke dir only after verifying its `references/<spoke>.md` copy exists, and route a
   HOT spoke through `tiering/tier.mjs --demote <spoke> --apply`, NEVER raw `rm`
   (apply-procedure §4).
5. `node fix-crosshub-generic.mjs <family>-manifest.json` (provenance banners + cross-hub map).
6. `node referents.mjs --repair --apply` (re-point `related_skills:` and inline `→ <id>` peer seeds).
7. Register the family in `tiering/tier-config.json` (`meta-validate.mjs --register-tier --apply`).
8. Sync the hub registry from the mdb-context-hub repo (review-required; user commits;
   apply-procedure §8).
9. **Refresh the consolidated index:** run `node ~/.claude/skill-consolidation/gen-skills-index.mjs`
   to regenerate `SKILLS-INDEX.{json,md}` from the new tree state. Non-blocking: on error, note
   `index: skipped (<reason>)` and continue.

## Phase 4 — VERIFY

1. Four gates, each independently checkable:
   - **1a Re-run** all four Phase-1 analytics plus `referents.mjs --status` (same flags,
     including `--desc-cap 1000 --json`); confirm **zero High** `meta-validate.mjs` findings and
     that the issue you targeted is gone (re-filed spoke now scores to its new hub; over-cap
     entry now under its targeted cap, 1000 or 1536).
   - **1b Delta:** re-capture the Phase-1 tree-health numbers and report the delta; that delta
     is the rebalance's evidence.
   - **1c Telemetry:** append the run's tree-health rows to `optimizer-telemetry.jsonl`
     (`artifact_type: "skill-tree"`, `pass: "tree-health"`) per the canonical telemetry schema.
   - **1d Index gate:** `node ~/.claude/skill-consolidation/gen-skills-index.mjs --check` must
     exit 0 (Phase 3 step 9 regenerated it); a `STALE` exit means the regen did not run — re-run
     it without `--check` and re-gate.
2. **Scored routing-probe replay** (link-checks alone do not satisfy this gate): replay the
   touched family's persisted competency-question (CQ) corpus
   (`~/.claude/skill-consolidation/evals/<family>.cq.md`) plus 1 new probe this run. Dispatch
   each as a fresh-context subagent question with NO hint about hubs/references; it must reach
   the right `references/*.md` by routing alone. If no `.cq.md` exists for the family, seed 5
   probes (an in-hub topic, a moved topic, a cross-hub topic, plus 2 more; the corpus convention
   is 5–10 questions, see `evals/README.md`) AND persist them as that family's seed corpus.
   **Gate:** reached-correct-reference ≥ 80%; record no-hub-backtrack as an informational
   directness column, not a gate. Bounded fail path: failed probe → one fix iteration → one
   re-probe → if still failing, exit `PROBE-DISSENT` listing the failures. Append probe outcomes
   to the family's evals rows.
3. **Exit status:** `CLEAN` and `BLOCKED` carry the canonical contract's semantics (`CLEAN` only
   after the probe gate passes; `BLOCKED` for findings unfixable without inventing content).
   `PROBE-DISSENT` is this skill's probe-gate analog of the contract's `BLIND-AUDIT-DISSENT`,
   defined in step 2 above.
4. End the Phase 4 report with the **literal restore command** for this run's snapshot (e.g.
   `tar -xzf ~/.claude/skill-consolidation/backups/<run>/<family>.tar.gz -C ~/.claude/skills` plus
   copying back the snapshotted out-of-family SKILL.mds) and the rollback procedure: snapshot
   restore, then reverse this run's `referents-ledger.json` entries.

## Hand-offs (peer deferral)

- One skill's content/triggers/length/peer-seeds → **skill-optimizer**.
- Which new skills a domain needs → **concept-family-explorer**, including any tree concepts found skill-less while adjudicating.
- Skill anatomy / frontmatter / description-cap rules → **claude-code-skills**.
- This skill is in the shared EXCLUDE_LIST (`~/.claude/skill-consolidation/exclude-list.mjs`, imported by both `detect-candidates.mjs` and `audit-placement.mjs`); a meta tool is never itself hubbed.
