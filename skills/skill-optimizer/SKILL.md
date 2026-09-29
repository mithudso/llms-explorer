---
name: skill-optimizer
description: >-
  Audit and improve a Claude Code skill to production quality: runs a convergence-loop quality gate, writes Medium+ fixes, seeds peer-deferral edges, verifies, and rebuilds the local hub registry index.
  TRIGGER: "optimize skill", "audit skill", "run sko", "skill trigger accuracy", "skill too long", "fix skill", "skill collision check". Structural-only `--meta` mode does wiring/registry/validation without content passes: "register skill to the hub", "validate placement/folder/manifest", "fix skill naming", "wire up peer deferral edges", "run sko --meta".
  SKIP: non-skill prompt files → prompt-deep-optimizer / phe; new skill from scratch → skill-creator; prose-only edits → writing-expert; deep MCP tool audits → ai-mcp-sdk-prompting (references/mcp-tool-search-optimizer.md); whole-TREE rebalance / cross-hub placement / duplicate-copy cleanup → skill-tree-architect; freshness/currency → skill-refresher.
whenToUse:
  - "optimize the <skill-name> skill"
  - "audit skill quality"
  - "my skill has bad trigger accuracy"
  - "skill file is too long, needs trimming"
  - "run sko on this skill"
  - "skill has AI-isms, clean it up"
  - "check for cross-skill trigger collisions"
  - "skill manifest keywords are wrong"
  - "run sko --meta on this skill"
  - "register my skill to the context hub"
  - "validate skill placement, folder, and manifest"
  - "wire up peer deferral references for this skill"
  - "recommend which model and effort this skill should run under"
version: 2.18.1
category: meta
updated: "2026-09-14"
model: claude-opus-5
effort: xhigh
triggers:
  - sko
  - optimize skill
  - improve skill
  - skill audit
  - skill quality check
  - skill trigger accuracy
  - skill length budget
  - skill collision check
  - sko --meta
  - structural-only skill pass
  - validate skill structure
  - register skill to hub
  - skill placement check
keywords:
  - skill-optimizer
  - skill audit
  - quality gate
  - convergence loop
  - trigger evals
  - manifest audit
  - cross-skill collision
  - anti-AI-isms
  - progressive disclosure
related_skills:
  - prompt-deep-optimizer
  - prompt-helper-optimizer
  - writing-expert
  - skill-creator
  - skill-tree-architect
  - skill-refresher
metadata:
  changelog_ref: references/CHANGELOG.md
---
# Skill Optimizer

Audit + rewrite Claude Code skill til pass measurable quality bar. Reads `SKILL.md` (or legacy `context.md` + `manifest.yaml`), runs 15 analytical passes (A–O, defined in `references/passes.md`) inside convergence loop (≤3 iterations, extendable to 5 per canonical contract; configurable via `--max-iter`), fixes all Medium+ findings, recommends model + effort skill run under and writes to frontmatter (Step 4.6), seeds reciprocal deferral refs into peer skills (Pass O), verifies post-write state, rebuilds hub registry index over target + touched peers.

**Registry model.** The hub registry is **derived, not authored**: `~/.global-ai-hub` indexes `~/.claude/skills/*/SKILL.md` (plus its own `skills/` and the plugin cache) into `registry.db` via `semantic_ops.router build`. There is no create/update API call — you write the file, then rebuild the index. Every registry read is `hub_route` (or its CLI form); Step 7 is a rebuild, not a push.

## When not to use

- Skill file doesn't exist or can't locate; report failure, stop.
- Skill ID doesn't resolve at `~/.claude/skills/<id>/SKILL.md` and `hub_route` surfaces no matching `ref`; ask caller for file path instead of guessing.
- Caller said skill read-only or under active development by another agent; defer, report.
- Target's one-off, single-line, or machine-generated prompt; route to `ph` / `phe` instead.
- Target's hub `references/*.md` spoke file not top-level `SKILL.md`; optimize owning hub's `SKILL.md` (its routing surface authoritative), leave reference-pointer repair to `referents.mjs`.

## Invocation

Trigger with `/sko <skill-id-or-path>` or naming skill in conversation:

- `/sko phe`: optimize prompt-helper-optimizer skill
- `/sko ~/.claude/skills/my-skill/SKILL.md`: optimize by direct path
- `/sko mongodb-expert --meta`: structural-only. validate placement/manifest, wire routing, register to hub; skip content-quality passes
- `/sko mongodb-ops-manager --max-iter=2 --no-sync`: cap convergence loop, skip hub sync (outer-loop shape below)
- `/sko mongodb-expert --budget-minutes=15`: wall-clock budget: finish current iteration's writes on expiry, exit `BUDGET_EXHAUSTED` (see contract's Budget contract section)

Full flag catalog + exit-status vocab live in `references/flags-and-statuses.md`. No target specified? Ask once: "Which skill should I optimize?"

### When driven by outer loop

Orchestrating agent (e.g., convergence-loop-runner) owns iteration? Invoke skill with `--max-iter=1 --no-sync` per outer iteration (outer loop owns convergence + remediation), one hub sync after outer loop's own convergence, not per iteration.

## Structural-only mode (`--meta`)

`/sko <target> --meta` (aliases `--structural`, `--meta-only`, `--structural-only`) runs only wiring/registry/validation work, skips content-quality passes, for hub-consolidation cleanup, post-move/rename fixes, pre-sync checks, not prose review. **Orchestrates** `~/.claude/skill-consolidation/` scripts, fills gaps via `meta-validate.mjs`; doesn't reimplement them.

- **Runs:** A′ (reference resolvability only), G (frontmatter/manifest), I (collision), L (whitespace), N (SKIP/`whenToUse`/`triggers`), O (peer seeding), Step 4.6 (model/effort recommendation, frontmatter-only, runs here too), read-only tool-search discoverability check, Step 6 verify, Step 7 registry rebuild + routing verify (sub-step 2), Step 7.7 SKILLS-INDEX refresh, Step 7.8 degraded tally — plus deterministic gap-lints in `~/.claude/skill-consolidation/meta-validate.mjs` (file/folder + kebab-case naming, manifest schema, spoke-copy-exists-before-delete, dangling routing rows, same-topic circular-SKIP, tier-config presence). Step 7.6 is a no-op in every mode.
- **Skips:** A (content contradictions), B, C, D, E, F, J, K. Pass H (trigger eval) opt-in via `--meta --eval`; Pass M (description rewrite) via `--meta --rewrite-desc`.
- **Still registers.** Step 7 runs in `--meta` and is not a dry run; write suppressed only when `--no-sync` passed or run exited w/ High findings remaining (override: `--sync-anyway`).
- **Resolvability not dropped.** A′ + N + O + dangling-row lint together guarantee every reference, `SKIP:` target, routing-table row, seeded `→ <id>` edge resolves to real skill or hub spoke.

Full orchestration sequence, `meta-validate.mjs` check list, tool-search check, meta-mode report shape live in `references/structural-mode.md`. Read it before running `--meta`.

## Process

**Pipeline:** 1 locate + duplicate guard → 2 snapshot + eval corpus → 3–5 convergence loop (passes → triage → 4.6 model/effort → writes) → 6 verify + blind re-audit → 6.5 cross-model (opt-in) → 7 registry rebuild + routing verify → 7.5 compress (opt-in) → 7.6 prose index (no action) → 7.7 catalog-index refresh → 7.8 degraded-run tally → 8 report.

### Step 1 — Locate skill

1. Skill ID given? Resolve to `~/.claude/skills/<id>/SKILL.md`, the canonical location and the only one the router indexes. Not there? Try `~/.global-ai-hub/skills/<id>/SKILL.md`, then a folded hub spoke via `~/.claude/skill-consolidation/*-manifest.json`.
2. Claude Code skill path given (`~/.claude/skills/<name>/SKILL.md`)? Treat single file as both context + manifest (frontmatter is manifest).
3. Legacy `context.md` / `manifest.yaml` path given? Derive its companion and optimize the pair. Note in Step 8 that this format is **not indexed**: the router globs `*/SKILL.md` only, so Step 7's rebuild will not surface it.
4. Read all files in full before any analysis. Only one file readable (e.g., `manifest.yaml` absent)? Proceed w/ available file, note missing companion in Step 8 report.
5. **Duplicate-copy guard (High).** Before any analysis, glob every copy of the target on disk:

   ```bash
   find ~/.claude/skills ~/.global-ai-hub/skills -name SKILL.md -path "*/<id>/*" 2>/dev/null
   ```

   More than one hit? Compare their `version` values and report a **High** finding naming every path and version. Optimize the canonical copy (`~/.claude/skills/<id>/SKILL.md`) only; never edit a twin, never merge them. Reconciling or deleting duplicate copies is `skill-tree-architect`'s job, not this skill's; this step exists so a run cannot silently optimize one of several copies and report clean. Two copies differ in kind:

   - **A twin under `~/.global-ai-hub/skills/<id>/`** shadows the canonical copy in the registry: that root is searched first and the first `name` wins, so no amount of rebuilding will register your edit. Mirror the canonical file into the hub root (back the twin up first) as part of Step 7, or the rebuild is theatre. See `references/sync-protocol.md` § The shadowing trap.
   - **A nested `<bucket>/<id>/SKILL.md`** is invisible to both the router (one-level glob) and the Claude Code loader, so it is stale-staging risk rather than live competition. Report, do not panic.
6. **Registry unavailable fallback.** `global_ai_hub` MCP not connected? Use the CLI for every registry read:

   ```bash
   cd ~/.global-ai-hub && PYTHONPATH=scripts .venv/bin/python -m semantic_ops.router route "<task>" --top 5 --kinds skill
   ```

   `registry.db` absent entirely? Registry-dependent checks in Passes A/G/I/N/O fall back to `~/.claude/skill-consolidation/SKILLS-INDEX.json` plus the current available-skills listing; record the degradation per Step 8's degraded-run rule.

### Step 2 — Establish baseline snapshot

Before any rewrite:

1. Record `wc -l` for `SKILL.md` (or `context.md`) + `manifest.yaml`.
2. Compute SHA-256 of each file, store as `baseline.sha256`; alongside, persist pre-write copy of every file run will modify to `~/.claude/skill-consolidation/backups/<skill>-<YYYYMMDD-HHMMSS>/<filename>` (contract's pre-write snapshot guardrail — central directory, never sibling `.bak` files). Persisted copy makes Step 8's `diff -u baseline current` preview computable, is rollback source. Same run directory holds streaming-checkpoint stub (§ Guardrails, "Streaming checkpoint" in `~/.claude/skill-consolidation/convergence-and-severity.md`) — appended after each pass bundle + each iteration's writes, so crash resumes from last completed step instead of re-running Step 3 from scratch; cite that section for write mechanics.
3. Assemble Pass H trigger-eval set per `references/passes.md` (Pass H, step 1). **Canonical corpus** is `~/.claude/skill-consolidation/evals/<skill-id>.eval.jsonl`, the single store of record, carrying every query, verdict, description hash, skill version, and `retired:` marker. Replay it when it exists, fill to the 20-query set w/ fresh queries, persist every query + verdict back to it. The target's own `<skill-dir>/evals/trigger-eval.json` is a **derived, disposable projection** of that corpus, regenerated from it only when Pass H runs the measured harness (`run_eval` requires that exact path + shape) — never hand-edited, never read as the source of truth. Disagreement between the two? Canonical wins; overwrite the projection.

Snapshot used in Step 5 to produce unified diff.

### Step 3 — Run analytical passes (convergence loop)

15 passes run as four concurrent bundles in a single tool-call batch: **B1** {A–F} content, **B2** {G, M, N} routing surface, **B3** {H} trigger eval, **B4** {I, J, K, L}. **Pass O runs after B2 and B4 return.** No agent tool? Run sequentially.

Two rules are load-bearing enough to state here:

- **Collect all findings before writing any changes**, so one pass's rewrite cannot invalidate another pass's findings.
- **Steps 3, 4, 5 are the loop.** Exit conditions, severity ladder, and guardrails are imported by reference from `~/.claude/skill-consolidation/convergence-and-severity.md`. Cite that file; never restate or silently diverge from it. Cap is 3 iterations, raised to 5 only if Medium+ findings dropped by at least 50% in the prior iteration, and `--max-iter` is a hard ceiling that raise never exceeds.

Bundle map, the Pass index (A–O), artifact-size profiles, composed-artifact handling, the full loop boundary, and the guardrail set live in `references/convergence-loop.md`. Read it before dispatching. Per-pass checks live in `references/passes.md`.

### Step 4 — Triage + conflict resolution

Score each finding by impact:

| Level | Criteria | Action |
|---|---|---|
| High | Changes behavior or prevents correct execution; trigger eval misses by ≥ 20 points; `description` > 1000 chars (Pass J.1, always-loaded); body > ~10k tokens (Pass J.2 hard ceiling) | Always fix |
| Medium | Reduces clarity, causes inconsistent output, or any finding w/ measurable impact, where measurable means the finding names specific trigger-eval query, routing edge, or output defect changes (calibrate against contract's "Anchored examples" appendix) | Always fix |
| Low | Subjective polish, cosmetic, taste-level preference | Skip |

These tiers = this skill's calibration of canonical model in `~/.claude/skill-consolidation/convergence-and-severity.md` (shared w/ prompt-deep-optimizer, ddo, document-critique); keep consistent w/ it. This skill folds Critical into High by design — see that file's mapping table. Pass-local severity rules take precedence where defined: Pass L's deterministic hygiene severities (+ YAML-tab High exception), Pass O's Medium/Low edge rule, Pass H's threshold-miss Medium stand as written.

Voice preservation handled by Constraints section; not reason to skip Medium finding.

**Conflict resolution** for parallel-agent findings:

Two agents recommend conflicting rewrites to same section:

1. Take higher-severity finding.
2. Tie? Take finding from earlier-letter pass (A > B > C > ...).
3. Still tie? Prefer more concise rewrite.
4. Record rejected alternative in Step 8 report so operator can override.

### Step 4.6 — Model & effort recommendation

Pick the model tier and effort level the target should *run under*, staged for Step 5's frontmatter write. Advisory only: an orchestrator can honor the `model` and `effort` keys, but they do not change how `/sko` itself runs.

Classify by dominant cognitive load and pick the **lowest** tier that covers the work: mechanical work takes the small tier at `low`, routine transforms the mid tier at `medium`, analytical or audit work the flagship tier at `high`, long-horizon agentic work the flagship tier at `xhigh`. Default to flagship plus `high` when uncertain, and never guess below it for a skill that makes judgments.

**Resolve the tier to a current model ID via the `claude-api` skill's `shared/models.md`, never from memory.** Cannot reach it? Write no `model` key and record `model: unresolved`. An absent key is advisory-neutral; a wrong one misroutes every future dispatch.

Full tier table, effort-validity rules, and caller-override handling live in `references/model-effort.md`. Record the chosen pair, tier, source (`heuristic` or `caller-pinned`), and a one-sentence rationale for Step 8.

### Step 5 — Implement changes

Write all High + Medium findings directly into source files:

- Edit `SKILL.md` / `context.md` for content, structure, clarity changes.
- Edit `manifest.yaml` (or top-of-file frontmatter) for keyword, description, metadata changes.
- Write `model` + `effort` frontmatter keys from Step 4.6 (advisory run-under hint). Overwrite existing value only when new recommendation differs, wasn't caller-pinned; unchanged? leave it. Adding/changing these keys counts as structural change for version bump.
- Bump `version` (semver patch for content fixes, minor for structural changes, major for scope changes).
- Set `updated` to today's ISO date.
- Don't rewrite sections that don't need changes.
- Preserve author's voice + terminology; accuracy/clarity conflicts w/ voice? prefer accuracy + clarity.

Pass J recommendations: extraction to `references/` recommended? Create file, replace original section w/ one-paragraph summary + pointer.

**Pass O peer writes.** Pass O only pass editing files other than target. Every peer edit obeys **peer-write rail** in `references/passes.md` (Pass O section, the authoritative definition): additive-only (one seeded deferral line; sole non-additive change is semver-patch + `updated` bump), snapshotted to run's central backup dir before first edit, bounded (≤ 1 line per peer per run, ≤ 5% peer growth), idempotent (existing edge ⇒ no edit, downgrade to Low), gated (no read-only/active-dev peers, no dangling targets, no mutual-hard-SKIP cycles), tracked for Step 6 re-verify + Step 7 re-sync.

### Step 6 — Post-write verification

After Step 5's writes:

1. Re-read both files (or single SKILL.md).
2. **Blind re-audit (full-content runs only).** Per contract's blind re-audit gate: dispatch one fresh-context subagent receiving ONLY final artifact + pass definitions (`references/passes.md`), with no findings tables, no fix rationale, and no revision history, runs finding passes once. Only corroborated Medium+ findings (second read of flagged span or deterministic check) can fail gate; any remain? feed into at most one additional loop iteration (counts against `--max-iter`), re-run blind audit once, second dissent? exit w/ status `BLIND-AUDIT-DISSENT` listing findings. `--meta` exempt: its confirm-clean is deterministic `meta-validate.mjs` re-run (references/structural-mode.md step 7), since `--meta` skips content passes by design.
3. Confirm 0 High findings remain. High findings remain? Loop back to Step 3 (counts against `--max-iter`).
4. Compute SHA-256 on rewritten files, assert differs from `baseline.sha256` (sanity check writes actually landed).
5. Claude Code skill? Confirm frontmatter still parses as valid YAML. Parse failure? Fix via item-3 loop-back first; auto-restore from Step 2 snapshot only if frontmatter still fails to parse once loop budget exhausted, report restore as run outcome — never silently.
6. Every peer file Pass O edited: re-read it; confirm frontmatter still parses under **strict YAML parser** (js-yaml, per Pass M's Glean requirement); confirm `description` still ≤ 1000 chars — seed pushed it over? apply Pass M's relocation fallback on peer instead; confirm only additive deferral line + version/`updated` bump added (purpose/description lead clause unchanged); confirm seeded edge didn't introduce mutual-hard-SKIP cycle.

### Step 6.5 — Cross-model exit gate (optional)

Only when caller passed `--cross-model` (default off): run shared gate procedure in `~/.claude/skill-consolidation/cross-model-gate.md`: availability check, confidentiality preconditions, one different-model-family review of final artifact, severity-ladder triage, at most one extra loop iteration. Cross-model finding triaged High holds Step 7 sync, reported as sync-blocking residual. Without flag, skip step.

### Step 7 — Rebuild hub registry index

Execute mechanics per `references/sync-protocol.md`. Read it before this step (7.0 outcome-changelog line → rebuild → per-skill routing verify). The registry is derived, so there is no per-skill write and no fallback chain: one rebuild covers the target and every Pass O peer at once. Invariants:

- **Rebuild (sub-step 1)** runs unless caller passed `--no-sync` **or run exited w/ High findings remaining** (gate; override `--sync-anyway`); withheld rebuild reports `rebuild withheld: N High findings remain` in Step 8.
- **Routing verify (sub-step 2)** **always runs**, read-only, and records **indexed / stale / unroutable** per skill written, including every Pass O peer.
- Step 7 runs at most once, only after final loop exit; verify never re-enters convergence loop.
- **`unroutable` is a routing defect, not a sync failure.** The file is on disk and the index is fresh, yet the skill does not surface for its own top intent phrase. That is the same failure Pass H measures, caught from the index side. File it as a standing Pass M finding for the next run; do not retry the rebuild.
- **`stale` retries the rebuild once**, then reports as a Step 7 failure, never silently dropped. Under `--no-sync`, `stale`/`unroutable` are reported as-is (no retry).

### Steps 7.5-7.8 — Post-sync

Four steps run between the registry rebuild and the report. Full procedure in `references/post-sync-steps.md`. Read it before executing 7.5:

- **7.5 compress (opt-in, `--compress`).** Default off; Pass J extraction is the preferred way to cut body size. Rebuild the index again afterwards.
- **7.6 prose index (no action).** `hub.db` is maintained by the `idle-indexer` / `hub-daemon` daemon. Never invoke it to force a refresh; confirm it is alive and report if not.
- **7.7 SKILLS-INDEX refresh.** `node ~/.claude/skill-consolidation/gen-skills-index.mjs`, gated with `--check`. Runs in `--meta` and under `--no-sync`.
- **7.8 degraded tally.** Two or more post-sync outcomes that did not land (including a `stale`/`unroutable` Step 7 verdict) ⇒ exit `DEGRADED` instead of `converged`. Report-and-exit only; never withholds writes or re-enters the loop.

### Step 8 — Report

Emit report sections in exact order + shape defined in `references/report-format.md`. Read it before writing the report. Brief: convergence table (+ Hygiene row), findings table (cap 20), Pass H trigger-eval table (labeled `measured`/`predicted`), unified diff preview, routing-verification table, then one-line outcomes for compress (7.5), prose-index daemon (7.6), index (7.7), degraded tally (7.8), model/effort (4.6), snapshot & rollback, telemetry, closing w/ one-line summary + modified-sections list. No Medium+ findings exist? Say so in one line, skip rest.

## Empirical mode — champion–challenger held-out loop

Gated champion–challenger promotion around Pass H (on by default when eval corpus + must-pass invariants present; opt out w/ `--dry-run`/`--no-promote`/`--structural-only`) defined in `references/empirical-mode.md`, citing shared contract `~/.claude/skill-consolidation/champion-challenger.md`. Read when eval corpus exists for target.

## Constraints

- Never change fundamental purpose or domain of skill; fix how it works, not what it does.
- Don't add features user didn't ask for unless Pass F identifies them as clearly missing.
- Preserve existing keywords in manifest unless factually wrong.
- Don't embed user-specific absolute paths (`/Users/<username>/...`) in skill instructions; use repo-root-relative references.
- Never hand-edit `registry.db` or any index artifact. The index is derived: write the skill file, then rebuild via `semantic_ops.router build`. An index edited directly is overwritten by the next rebuild and lies until then.
- Only Pass O may edit skill other than target, only under peer-write rail (`references/passes.md`, Pass O); every other pass writes solely to target.

## Quality bar

Skill passes quality bar when:

- All analytical passes return 0 High findings on final iteration
- Pass H trigger eval hits ≥ 9/10 on positives, ≤ 1/10 on negatives, measured via the skill-creator harness on final iteration when available, predicted otherwise (report labels which)
- Persisted eval corpus exists? Empirical promotion gate (`references/empirical-mode.md`) approved final state: held-out Pass H non-regression plus must-pass invariants
- Pass I returns no unresolved collisions
- Pass J.1 reports the always-loaded surface clean: `description` ≤ 1000 chars, no changelog or other non-executing bulk in frontmatter. Pass J.2 reports the body within the ~6k-token soft budget, or over it with a recorded justification (load-bearing content), or extracted; ~10k tokens = hard ceiling regardless
- Pass K returns 0 banned terms outside code blocks
- Pass L returns 0 whitespace/character-hygiene defects (no trailing whitespace, no multiple blank lines, no tabs in body, no non-printing characters, LF line endings)
- Pass M confirms description leads w/ what skill does, carries both `TRIGGER:` and `SKIP:` clause, ≤ 1000 chars (Glean hard cap)
- Pass N confirms every `whenToUse` entry concrete phrasing, every `SKIP:` exclusion names real peer skill
- Pass O confirms routing mesh seeded: required downward, upward, lifecycle-handoff deferral edges exist, every seeded peer edit additive-only + re-synced, no mutual-hard-SKIP cycle introduced
- Step 4.6 set `model` + `effort` frontmatter keys to valid model ID + effort level matched to skill's cognitive load (or caller's pinned override)
- Instructions internally consistent (no rule contradicts another)
- Every non-trivial instruction either example-bearing or links to one
- Manifest keywords + description accurately reflect what skill does
- Post-write verification (Step 6) confirms High = 0
- Routing verification (Step 7 sub-step 2) confirms target (+ every peer Pass O touched) is **indexed**, meaning the description stored in `registry.db` matches the file's and the skill surfaces for its own top intent phrase, rather than **stale** or **unroutable**; or, under `--no-sync` or a withheld rebuild (High findings remained at budget exhaustion), index-behind state reported. Compare stored text, never mtimes: a rebuild can exit 0 having silently skipped an entry
- Step 1's duplicate-copy guard found exactly one copy of the target on disk, or reported every extra copy as a High finding
- Run did not exit `DEGRADED` (Step 7.8): fewer than two post-sync outcomes failed to land

## Meta-optimization note

Target's skill-optimizer itself? Step 5 writes alter instructions subsequent loop iterations would read. Step 3's "collect all findings before writing" rule makes this safe within single iteration. Across iterations, loop intentionally re-reads rewritten skill; this = convergence behavior, not bug. **Frozen pass definitions:** run's own pass definitions live in file being rewritten (target = skill-optimizer itself, its `references/`, or shared `~/.claude/skill-consolidation/convergence-and-severity.md`)? Pass list, severity rubric, exit conditions frozen at Step 2 baseline snapshot for entire run; rewrite changing pass list takes effect only on NEXT run. Findings still recomputed each iteration against current file state; only evaluation procedure frozen. Freeze doesn't extend to sibling-optimizer targets generally; optimizing prompt-deep-optimizer never edits this skill's rubric mid-run, since Pass O peer writes additive-only.