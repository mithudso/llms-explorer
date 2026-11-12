---
name: skill-optimizer
description: >-
  Audit and improve a skill: run a convergence loop, fix Medium+ findings, add and grade trigger and behavior evals, and check peer routing. Discover copies; synchronize owned destinations only within the requested scope. Rebuild the hub registry when permitted.
  TRIGGER: "optimize skill", "audit skill", "run sko", "skill trigger accuracy", "skill too long", "fix skill", "skill collision check", "check my /command wrapper for drift", "add missing evals", "sync skill copies". `--meta` does wiring/registry/validation only: "register skill to the hub", "validate placement/folder/manifest", "wire up peer deferral edges". `--read-only` audits without writing.
  SKIP: non-skill prompt files → prompt-deep-optimizer / phe; new skill from scratch → skill-creator; prose-only edits → writing-expert; deep eval suite optimization → deep-eval-optimizer / deo; MCP tool audits → ai-mcp-sdk-prompting; whole-TREE rebalance → skill-tree-architect; freshness → skill-refresher.
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
  - "audit this skill but don't change anything (sko --read-only)"
  - "check whether my /command wrapper drifted from its skill"
  - "add appropriate evals to a skill missing them"
  - "make every copy of this skill identical to the one Claude loads"
  - "add the look-for-llms-files-first section to this skill"
version: 2.25.0
category: meta
updated: "2026-11-11"
model: claude-opus-5-5
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
  - sko --read-only
  - command wrapper drift
  - add missing evals
  - generate skill evals
  - sync skill copies
  - find every copy of a skill
  - llms-first section
keywords:
  - skill-optimizer
  - skill audit
  - quality gate
  - convergence loop
  - trigger evals
  - eval generation
  - missing evals
  - location sync
  - llms-first
  - manifest audit
  - cross-skill collision
  - anti-AI-isms
  - progressive disclosure
related_skills:
  - deep-eval-optimizer
  - prompt-deep-optimizer
  - prompt-helper-optimizer
  - writing-expert
  - skill-creator
  - skill-tree-architect
  - skill-refresher
  - agent-deep-optimizer
metadata:
  changelog_ref: references/CHANGELOG.md
---
# Skill Optimizer

Audit a skill against a stated quality bar. Read `SKILL.md` (or legacy `context.md` + `manifest.yaml`), then run the 16 analytical passes A–P in `references/passes.md`. Collect findings before rewriting. The convergence loop defaults to three iterations; the shared contract governs any extension, with `--max-iter` as a hard ceiling. Fix Medium+ findings, add missing evals and report both trigger and behavior results. Recommend runtime-compatible model and effort metadata, verify the candidate, and check peer routing. Discover copies and synchronize only authorized, owned destinations under Step 6.7. Rebuild the registry only when its gates and the session's service permissions allow it. Read-only runs report proposals and write nothing.

**Registry model.** The hub registry is **derived, not authored**: `~/.global-ai-hub` indexes `~/.claude/skills/*/SKILL.md` (plus its own `skills/` and the plugin cache) into `registry.db` via `semantic_ops.router build`. There is no create/update API call — you write the file, then rebuild the index. Every registry read is `hub_route` (or its CLI form); Step 7 is a rebuild, not a push.

## Look for llms files first

Before reading the subject raw, look for its llms files and open them by size. If you have the repo, step 4 sets the order.
1. Locate the subject's `llms.txt`, source-qualified concept pack, or relevant documentation index. Existing keyword hits can help locate it.
2. Run `wc -c` first. Read a file whole only when it fits; otherwise search it.
3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map.
4. If you have the repo, search the code before opening an llms file. The code is the authority. Verify each fact against its source `path:line`.
5. Index and llms hits are leads. Confirm their sources before acting.

## When not to use

- Skill file doesn't exist or can't locate; report failure, stop.
- Skill ID doesn't resolve at `~/.claude/skills/<id>/SKILL.md` and `hub_route` surfaces no matching `ref`; ask caller for file path instead of guessing.
- Caller forbids auditing the artifact, or another agent is actively developing it; defer, report. A permitted audit of a read-only artifact runs with `--read-only`, producing proposed fixes without mutations.
- Target resolves only inside the plugin cache (`~/.claude/plugins/cache/…/skills/<id>/`); plugin updates overwrite it. Run it as `--read-only` (report), never edit a plugin's copy. To get the fixes applied, offer two routes: send the diff upstream to the plugin maintainers, or fork into `~/.claude/skills/<id>/`. The fork needs caller approval, shadows the plugin copy in routing, and is user-maintained from then on.
- Target's one-off, single-line, or machine-generated prompt; route to `ph` / `phe` instead.
- Target is a subagent definition (`~/.claude/agents/<name>.md`, `.claude/agents/<name>.md`); route to `agent-deep-optimizer` (`/ado`): its frontmatter is a tool grant and precedence record, not a skill manifest, and its body is a system prompt.
- Target's hub `references/*.md` spoke file not top-level `SKILL.md`; optimize owning hub's `SKILL.md` (its routing surface authoritative), leave reference-pointer repair to `referents.mjs`.

## Invocation

Trigger with `/sko <skill-id-or-path>` or naming skill in conversation:

- `/sko phe`: `phe` is a `~/.claude/commands/` wrapper, so Step 1 resolves it to the skill it invokes (prompt-helper-optimizer) and lints the wrapper for drift (Pass G)
- `/sko mongodb-expert --read-only`: run every pass, report findings + proposed diffs, write nothing (single iteration; no rebuild, no peer seeds, no changelog line)
- `/sko ~/.claude/skills/my-skill/SKILL.md`: optimize by direct path
- `/sko mongodb-expert --meta`: structural-only. validate placement/manifest, wire routing, register to hub; skip content-quality passes
- `/sko mongodb-ops-manager --max-iter=2 --no-sync`: cap convergence loop, skip hub sync (outer-loop shape below)
- `/sko mongodb-expert --budget-minutes=15`: wall-clock budget: finish current iteration's writes on expiry, exit `BUDGET_EXHAUSTED` (see contract's Budget contract section)

Full flag catalog + exit-status vocab live in `references/flags-and-statuses.md`. No target specified? Ask once: "Which skill should I optimize?" Flag not in the catalog? Stop before Step 1, print the catalog, ask once; never drop or reinterpret it silently.

**Answer shape for scenario, routing, or failure questions.** Lead with a one-line verdict (run / route to `<peer>` / skip + report / exit status), cite the governing rule (section or gate), and say what you are *not* doing. Then give numbered concrete steps that name the resolved target, write set, and report entries. Quote thresholds and paths exactly as this file states them. Never state as fact what you have not seen (spoke counts, which copy wins routing, measured vs. predicted results); name the assumption and the check that settles it. If nothing was executed, label the answer a plan, not results.

### When driven by outer loop

Orchestrating agent (e.g., convergence-loop-runner) owns iteration? Invoke skill with `--max-iter=1 --no-sync` per outer iteration (outer loop owns convergence + remediation), one hub sync after outer loop's own convergence, not per iteration. These inner calls keep Pass H at `predicted`; pass `--eval=measured` on the last outer call to get measured trigger rates.

## Structural-only mode (`--meta`)

`/sko <target> --meta` (aliases `--structural`, `--meta-only`, `--structural-only`) runs only wiring/registry/validation work, skips content-quality passes, for hub-consolidation cleanup, post-move/rename fixes, pre-sync checks, not prose review. **Orchestrates** `~/.claude/skill-consolidation/` scripts, fills gaps via `meta-validate.mjs`; doesn't reimplement them.

- **Runs:** A′ (reference resolvability only), G, I, L, N, O, Step 1.7, Step 6.3 (cheapest level), Step 6.7, Step 4.6, the Step 2 offline pre-lint, the read-only tool-search discoverability check, Steps 6, 7, 7.7, 7.8, plus the deterministic gap-lints in `~/.claude/skill-consolidation/meta-validate.mjs`. The runs-vs-skips table and the lint list live in `references/structural-mode.md`. Step 7.6 is a no-op in every mode.
- **Skips:** A (content contradictions), B, C, D, E, F, J, K, P. Pass H (trigger eval) opt-in via `--meta --eval`; Pass M (description rewrite) via `--meta --rewrite-desc`.
- **Still registers.** Step 7 runs in `--meta` and is not a dry run; write suppressed only when `--no-sync` passed or run exited w/ High findings remaining (override: `--sync-anyway`).
- **Resolvability not dropped.** A′ + N + O + dangling-row lint together guarantee every reference, `SKIP:` target, routing-table row, seeded `→ <id>` edge resolves to real skill or hub spoke.

Full orchestration sequence, `meta-validate.mjs` check list, tool-search check, meta-mode report shape live in `references/structural-mode.md`. Read it before running `--meta`.

## Process

**Pipeline:** 1 locate + wrapper resolution + duplicate guard + 1.7 index discovery → 2 snapshot + eval corpus + missing evals audit + offline pre-lint → 3–5 convergence loop (passes → triage → 4.6 model/effort → writes + eval generation) → 6 verify + blind re-audit → 6.3 eval gate → 6.5 cross-model (opt-in) → 6.7 location sync → 7 registry rebuild + routing verify → 7.5 compress (opt-in) → 7.6 prose index (no action) → 7.7 catalog-index refresh → 7.8 degraded-run tally → 8 report.

### Step 1 — Locate skill

1. Skill ID given? Resolve to `~/.claude/skills/<id>/SKILL.md`, the canonical location. Not there? Try `~/.global-ai-hub/skills/<id>/SKILL.md`, then a folded hub spoke via `~/.claude/skill-consolidation/*-manifest.json`, then the plugin cache (`~/.claude/plugins/cache/*/*/*/skills/<id>/SKILL.md`; indexed by the router, never edited here). **Wrapper resolution:** the argument names a `~/.claude/commands/<arg>.md` file instead (leading `/` optional)? Read it, take the skill it invokes (its `**<id>** skill` line or the `SKILL.md` path it cites) as the target, and keep the wrapper path for Pass G's wrapper-drift check. Skill ID given directly? Still locate its wrappers: `grep -l -e "\*\*<id>\*\*" -e "skills/<id>/" ~/.claude/commands/*.md`.
2. Explicit skill path given? Resolve that path and follow its repository ownership rules. Treat its `SKILL.md` as both context and manifest. Do not silently redirect an explicitly selected repository source to a same-named installed copy. Inventory other copies separately; a selected source does not authorize overwriting them.
3. Legacy `context.md` / `manifest.yaml` path given? Derive its companion and optimize the pair. Note in Step 8 that this format is **not indexed**: the router globs `*/SKILL.md` only, so Step 7's rebuild will not surface it.
4. Read all files in full before any analysis. Only one file readable (e.g., `manifest.yaml` absent)? Proceed w/ available file, note missing companion in Step 8 report.
5. **Duplicate-copy guard.** Before analysis, list copies with the command in `references/sync-protocol.md`. Deduplicate real paths; classify installed competitors, repository distributions, generated overlays, plugin-managed copies and historical snapshots. Compare versions and hashes. A divergent copy that shadows the selected source in an active index is **High**. An intentional distribution copy is not a collision merely because it exists. Optimize the selected owned source. Step 6.7 records permitted syncs and preserved differences; it never grants ownership or permission to overwrite another source.

   - **A top-level twin in another indexed root** can shadow the selected source. Verify the collector's current root order and report the winning file. Preserve a divergent or independently owned twin unless its synchronization is authorized and its preimage is unchanged. Withhold a clean routing verdict while the indexed source differs. See `references/sync-protocol.md` § The shadowing trap.
   - **A nested `<bucket>/<id>/SKILL.md`** is invisible to both the router (one-level glob) and the Claude Code loader, so it is stale-staging risk rather than live competition. Report, do not panic.
6. **Registry unavailable fallback.** `global_ai_hub` MCP not connected? Use the CLI for every registry read:

   ```bash
   cd ~/.global-ai-hub && PYTHONPATH=scripts .venv/bin/python -m semantic_ops.router route "<task>" --top 5 --kinds skill
   ```

   `registry.db` absent entirely? Registry-dependent checks in Passes A/G/I/N/O fall back to `~/.claude/skill-consolidation/SKILLS-INDEX.json` plus the current available-skills listing; record the degradation per Step 8's degraded-run rule.

7. **Index discovery (Step 1.7).** Query the semantic and the keyword index for related and colliding skills, every file that mentions the skill, and every copy, per `references/index-discovery.md`. Fall back to the `search.py` / `keyword_index.py` / `router route` CLIs when the MCP server is unreachable. Index hits are leads; confirm each with Read or `shasum`. The result feeds Pass I, Pass G/N/O and Step 6.7.

### Step 2 — Establish baseline snapshot

**Read-only gate.** Under `--read-only`, keep baseline hashes, corpus selections, findings and proposed hunks in memory. Do not create snapshots, checkpoints, eval projections, telemetry, or command stubs; do not move the installed skill. Pass H uses predictions. Skip the offline pre-lint if it cannot run without writes. This gate takes precedence over the write-mode instructions below.

Before any rewrite:

1. Record `wc -l` for `SKILL.md` (or `context.md`) + `manifest.yaml`.
2. Compute SHA-256 of each file, store as `baseline.sha256`; alongside, persist pre-write copy of every file run will modify to `~/.claude/skill-consolidation/backups/<skill>-<YYYYMMDD-HHMMSS>/<filename>` (contract's pre-write snapshot guardrail — central directory, never sibling `.bak` files). Persisted copy makes Step 8's `diff -u baseline current` preview computable, is rollback source. Same run directory holds streaming-checkpoint stub (§ Guardrails, "Streaming checkpoint" in `references/shared/convergence-and-severity.md`) — appended after each pass bundle + each iteration's writes, so crash resumes from last completed step instead of re-running Step 3 from scratch; cite that section for write mechanics.
3. **Assemble eval suite & audit missing evals.**
   - **Functional execution evals (`evals/evals.json`):** Check if `<skill-dir>/evals/evals.json` exists. If absent or lacking test cases, flag a **Medium** finding (Pass F) to generate appropriate evals: author at least 2–3 realistic test cases with `id`, `name`, realistic user `prompt`, `expected_output`, `files` (if any), and objectively verifiable `assertions` conforming to the schema and template in `references/eval-gate.md#functional-file-schema`.
   - **Trigger-accuracy evals:** Resolve the source corpus with `references/corpus-scope.md`, replay existing rows, then add fresh queries to the 10-positive/10-negative audit set. Preserve query history, verdict level, description hash, skill version and retirement markers. Derive `evals/trigger-eval.json` from the selected corpus; never use that disposable projection as the source. Keep user-level corpus files read-only when the requested scope is a repository.
4. **Offline pre-lint (zero-token).** Run `python3 ~/.claude/scripts/skill_optimizer_offline.py <skill-dir> --json`. Its deterministic findings (frontmatter parse and required keys, duplicate keys, description over the index cap, body token budget, heading hierarchy, table shape, broken links, banned terms) enter iteration 1 as pre-computed evidence for Passes C, G, J, and K at those passes' severities; its prose heuristics (readability, hedges, empty quantifiers) stay Low. Script absent or failing? Record `pre-lint: skipped (<reason>)` and continue; it never blocks. It complements `meta-validate.mjs` (cross-file wiring), never replaces it, and runs in `--meta` too.

Snapshot used in Step 5 to produce unified diff.

### Step 3 — Run analytical passes (convergence loop)

16 passes run as four concurrent bundles in a single tool-call batch: **B1** {A–F, P} content, **B2** {G, M, N} routing surface, **B3** {H} trigger eval, **B4** {I, J, K, L}. **Pass O runs after B2 and B4 return.** No agent tool? Run sequentially.

Two rules are load-bearing enough to state here:

- **Collect all findings before writing any changes**, so one pass's rewrite cannot invalidate another pass's findings.
- **Steps 3, 4, 5 are the loop.** Exit conditions, severity ladder, and guardrails are imported by reference from `references/shared/convergence-and-severity.md`. Cite that file; never restate or silently diverge from it. Cap is 3 iterations, raised to 5 only if Medium+ findings dropped by at least 50% in the prior iteration, and `--max-iter` is a hard ceiling that raise never exceeds.

Bundle map, the Pass index (A–P), artifact-size profiles, composed-artifact handling, the full loop boundary, and the guardrail set live in `references/convergence-loop.md`. Read it before dispatching. Per-pass checks live in `references/passes.md`.

### Step 4 — Triage + conflict resolution

Score each finding by impact:

| Level | Criteria | Action |
|---|---|---|
| High | Changes behavior or prevents correct execution; trigger eval misses by ≥ 20 points; `description` > 1000 chars (Pass J.1, always-loaded); body > ~10k tokens (Pass J.2 hard ceiling) | Always fix |
| Medium | Reduces clarity, causes inconsistent output, missing or deficient evals (`evals/evals.json` functional test cases or Pass H trigger queries missing), or any finding w/ measurable impact, where measurable means the finding names specific trigger-eval query, routing edge, or output defect changes (calibrate against contract's "Anchored examples" appendix) | Always fix |
| Low | Subjective polish, cosmetic, taste-level preference | Skip |

These tiers = this skill's calibration of canonical model in `references/shared/convergence-and-severity.md` (shared w/ prompt-deep-optimizer, ddo, document-critique); keep consistent w/ it. This skill folds Critical into High by design — see that file's mapping table. Pass-local severity rules take precedence where defined: Pass L's deterministic hygiene severities (+ YAML-tab High exception), Pass O's Medium/Low edge rule, Pass H's threshold-miss Medium stand as written.

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

**Match the target runtime, then resolve its tier to a current model ID from a live source:** for Claude targets, use the `claude-api` skill's `shared/models.md` when installed, else the `Claude API ID` row of the models overview (`https://platform.claude.com/docs/en/models/overview`), else the harness's own model roster when the session names current IDs (record `source: harness roster`). None reachable? Write no `model` key and record `model: unresolved`. An absent key is advisory-neutral; a wrong one misroutes every future dispatch.

Full tier table, effort-validity rules, and caller-override handling live in `references/model-effort.md`. The recommendation's headline is always tier + effort (for example, "flagship, `effort: high`"). A concrete ID appears only if it was read from one of the sources above during this run. Never infer a tier from roster order, list position, or naming. Otherwise stage `effort` alone and record `model: unresolved (tier: <tier>)`. For Step 8, record the pair, the tier, two separate provenance fields, and a one-sentence rationale. The two provenance fields are classification source (`heuristic` / `caller-pinned`) and ID source (`models.md` / `models overview` / `harness roster (tier-labelled)` / `unresolved`).

### Step 5 — Implement changes

Write all High + Medium findings directly into source files:

- Edit `SKILL.md` / `context.md` for content, structure, clarity changes.
- Edit `manifest.yaml` (or top-of-file frontmatter) for keyword, description, metadata changes.
- **Add missing evals:** Create realistic functional cases with expected outputs and verifiable assertions in `evals/evals.json`. Establish trigger queries and verdicts in the scoped source corpus from `references/corpus-scope.md`, then derive `evals/trigger-eval.json`. Preserve valid user cases. If an existing case contradicts a verified safety or ownership rule, correct its expectation and record the previous case and the reason in the run receipt.
- Write `model` + `effort` frontmatter keys from Step 4.6 (advisory run-under hint). Overwrite existing value only when new recommendation differs, wasn't caller-pinned; unchanged? leave it. Adding/changing these keys counts as structural change for version bump.
- Bump `version` (semver patch for content fixes, minor for structural changes, major for scope changes).
- Set `updated` to today's ISO date.
- Don't rewrite sections that don't need changes.
- Preserve author's voice + terminology; accuracy/clarity conflicts w/ voice? prefer accuracy + clarity.
- Edit the `~/.claude/commands/` wrapper resolved in Step 1 for Pass G wrapper-drift findings; it is part of the target's write set (snapshotted in Step 2, re-read in Step 6), not a Pass O peer.
- `--read-only` (or a plugin-cache target): write nothing here or anywhere else in the run (no target, wrapper, peer, changelog, or index writes). Stage every fix as a proposed hunk for Step 8's diff preview; the loop runs one iteration (`--max-iter=1` implied, since nothing changes between iterations); Step 6 runs the blind re-audit only; Step 7 skips the rebuild and keeps the read-only routing verify; 7.5 and 7.7 are skipped.

Pass J recommendations: extraction to `references/` recommended? Create file, replace original section w/ one-paragraph summary + pointer.

**Pass O peer writes.** Pass O only pass editing files other than target. Every peer edit obeys **peer-write rail** in `references/passes.md` (Pass O section, the authoritative definition): additive-only (one seeded deferral line; sole non-additive change is semver-patch + `updated` bump), snapshotted to run's central backup dir before first edit, bounded (≤ 1 line per peer per run, ≤ 5% peer growth), idempotent (existing edge ⇒ no edit, downgrade to Low), gated (no read-only/active-dev peers, no dangling targets, no mutual-hard-SKIP cycles), tracked for Step 6 re-verify + Step 7 re-sync.

### Step 6 — Post-write verification

After Step 5's writes:

1. Re-read both files (or single SKILL.md).
2. **Blind re-audit (full-content runs only).** Per contract's blind re-audit gate: dispatch one fresh-context subagent receiving ONLY final artifact + pass definitions (`references/passes.md`), with no findings tables, no fix rationale, and no revision history, runs finding passes once. Only corroborated Medium+ findings (second read of flagged span or deterministic check) can fail gate; any remain? feed into at most one additional loop iteration (counts against `--max-iter`), re-run blind audit once, second dissent? exit w/ status `BLIND-AUDIT-DISSENT` listing findings. `--meta` exempt: its confirm-clean is deterministic `meta-validate.mjs` re-run (references/structural-mode.md step 7), since `--meta` skips content passes by design.
3. Confirm 0 High findings remain. High findings remain? Loop back to Step 3 (counts against `--max-iter`).
4. Compute SHA-256 for the target write set. Every file actually modified must differ from its baseline; every untouched file must match it. A clean run with no changes is valid. New files must exist and parse.
5. Claude Code skill? Confirm frontmatter still parses under a strict YAML parser: js-yaml when `node -e "require('js-yaml')"` succeeds, else PyYAML `yaml.safe_load` (both reject an unquoted `X:` inside a single-line scalar; record which ran). Same check on every wrapper edited. Parse failure? Fix via item-3 loop-back first. The usual cause is an unquoted `: ` inside a value: quote the scalar or reword it to drop the colon. Then re-scan every touched key, especially the `TRIGGER:`/`SKIP:` clauses in `description`, and hold Step 7 until the frontmatter parses; auto-restore from Step 2 snapshot only if frontmatter still fails to parse once loop budget exhausted, report restore as run outcome — never silently.
6. Every peer file Pass O edited: re-read it; confirm frontmatter still parses under the item-5 strict YAML parser (Pass M's Glean requirement); confirm `description` still ≤ 1000 chars — seed pushed it over? apply Pass M's relocation fallback on peer instead; confirm only additive deferral line + version/`updated` bump added (purpose/description lead clause unchanged); confirm seeded edge didn't introduce mutual-hard-SKIP cycle.

### Step 6.3 — Eval gate (every run)

Evals are part of every run, including `--meta` and `--read-only`. Ensure `evals/evals.json` and `evals/trigger-eval.json` exist (created in Step 5; `--meta` and `--read-only` report a missing file as proposed instead), run the trigger eval (Pass H) and the behavior evals at the cheapest level the skill supports, and put both pass rates in the report. A deeper `deep-eval-optimizer` run is a follow-up after `/sko` exits, never part of the run. No eval results means exit `EVALS-MISSING`, never `converged`. Mechanics and levels: `references/eval-gate.md`.

### Step 6.5 — Cross-model exit gate (optional)

Only when caller passed `--cross-model` (default off): run shared gate procedure in `references/shared/cross-model-gate.md`: availability check, confidentiality preconditions, one different-model-family review of final artifact, severity-ladder triage, at most one extra loop iteration. Cross-model finding triaged High holds Step 7 sync, reported as sync-blocking residual. Without flag, skip step.

### Step 6.7 — Location sync

Discover and hash installed copies; treat the explicitly selected source as canonical only after checking the user's intent and repository instructions. Preserve divergent, newer, vendored, plugin-managed and remote copies. Sync only when authorized, after a preimage and ownership check; otherwise report the differences. See `references/location-sync.md`. Report SYNC-PARTIAL when a required sync is blocked.

### Step 7 — Rebuild hub registry index

Execute mechanics per `references/sync-protocol.md`. Read it before this step (7.0 outcome-changelog line → rebuild → per-skill routing verify). The registry is derived, so there is no per-skill write and no fallback chain: one rebuild covers the target and every Pass O peer at once. Invariants:

- **Rebuild (sub-step 1)** runs unless `--no-sync`, residual High findings, scope restrictions or an existing indexing pause withholds it. `--sync-anyway` overrides only the residual-High gate; it never overrides a service pause, ownership or permission. Report the exact reason in Step 8.
- **Routing verify (sub-step 2)** **always runs**, read-only, and records **indexed / stale / unroutable** per skill written, including every Pass O peer.
- Step 7 is one post-loop phase. Its stale retry and any indexed-content refresh after opt-in compression are bounded sub-steps, not another phase or convergence iteration.
- **`unroutable` is a routing defect, not a sync failure.** The file is on disk and the index is fresh, yet the skill does not surface for its own top intent phrase. That is the same failure Pass H measures, caught from the index side. File it as a standing Pass M finding for the next run; do not retry the rebuild.
- **`stale` retries the rebuild once**, then reports as a Step 7 failure, never silently dropped. Under `--no-sync`, `stale`/`unroutable` are reported as-is (no retry).

### Steps 7.5-7.8 — Post-sync

Four steps run between the registry rebuild and the report. Full procedure in `references/post-sync-steps.md`. Read it before executing 7.5:

- **7.5 compress (opt-in, `--compress`).** Default off; Pass J extraction is the preferred way to cut body size. Rebuild only if compression changed the indexed description; obey `--no-sync` and the High-findings gate.
- **7.6 prose index (no action).** `hub.db` is maintained by the `idle-indexer` / `hub-daemon` daemon. Never invoke it to force a refresh; confirm it is alive and report if not.
- **7.7 SKILLS-INDEX refresh.** `node ~/.claude/skill-consolidation/gen-skills-index.mjs`, gated with `--check`. Runs in `--meta` and under `--no-sync`.
- **7.8 degraded tally.** Two or more post-sync outcomes that did not land (including a `stale`/`unroutable` Step 7 verdict) ⇒ exit `DEGRADED` instead of `converged`. Report-and-exit only; never withholds writes or re-enters the loop.

### Step 8 — Report

Emit report sections in exact order + shape defined in `references/report-format.md`. Read it before writing the report. Brief: convergence table (+ Hygiene row), findings table (cap 20), Pass H trigger-eval table (labeled `measured`/`predicted`), unified diff preview, routing-verification table, then one-line outcomes for compress (7.5), prose-index daemon (7.6), index (7.7), degraded tally (7.8), model/effort (4.6), snapshot & rollback, telemetry, closing w/ one-line summary + modified-sections list. No Medium+ findings exist? Omit the empty findings table and diff previews, but still report eval mode/results, routing, post-sync outcomes, degraded status, and snapshot/telemetry outcomes (or their read-only omissions).

## Empirical mode — champion–challenger held-out loop

Gated champion–challenger promotion around Pass H (on by default when eval corpus + must-pass invariants present; opt out w/ `--dry-run`/`--no-promote`/`--structural-only`; `--read-only` implies `--dry-run`) defined in `references/empirical-mode.md`, citing shared contract `references/shared/champion-challenger.md`. Read when eval corpus exists for target.

## Constraints

- Never change fundamental purpose or domain of skill; fix how it works, not what it does.
- Don't add features user didn't ask for unless Pass F identifies them as clearly missing.
- Preserve existing keywords in manifest unless factually wrong.
- Don't embed user-specific absolute paths (`/Users/<username>/...`) in skill instructions; use repo-root-relative references.
- Never hand-edit `registry.db` or any index artifact. The index is derived: write the skill file, then rebuild via `semantic_ops.router build`. An index edited directly is overwritten by the next rebuild and lies until then.
- Only Pass O may edit skill other than target, only under peer-write rail (`references/passes.md`, Pass O); every other pass writes solely to target (its `SKILL.md`, `references/`, and any `~/.claude/commands/` wrapper resolved in Step 1). Step 6.7 is the one other writer: it overwrites copies of the target with the verified canonical, only after a backup.

## Quality bar

Skill passes quality bar when:

- All analytical passes return 0 High findings on final iteration
- Pass H trigger eval hits ≥ 9/10 on positives, ≤ 1/10 on negatives, measured via the skill-creator harness on final iteration when available, predicted otherwise (report labels which)
- Empirical promotion eligible and enabled? The gate (`references/empirical-mode.md`) approved final state: held-out non-regression plus must-pass invariants. An ineligible 20-query corpus or explicit promotion opt-out requires an exploratory/opt-out label, not a promotion verdict
- Pass I returns no unresolved collisions
- Pass J.1 reports the always-loaded surface clean: `description` ≤ 1000 chars, no changelog or other non-executing bulk in frontmatter. Pass J.2 reports the body within the ~6k-token soft budget, or over it with a recorded justification (load-bearing content), or extracted; ~10k tokens = hard ceiling regardless
- Pass K returns 0 banned terms outside code blocks
- Pass L returns 0 whitespace/character-hygiene defects (no trailing whitespace, no multiple blank lines, no tabs in body, no non-printing characters, LF line endings)
- Pass M confirms description leads w/ what skill does, carries both `TRIGGER:` and `SKIP:` clause, ≤ 1000 chars (Glean hard cap)
- Pass N confirms every `whenToUse` entry concrete phrasing, every `SKIP:` exclusion names real peer skill
- Pass G's wrapper-drift check passes for every `~/.claude/commands/` wrapper that invokes the target: description, flags, `model`/`effort`, and any step summary agree with the skill
- Pass O confirms routing mesh seeded: required downward, upward, lifecycle-handoff deferral edges exist, every seeded peer edit additive-only + re-synced, no mutual-hard-SKIP cycle introduced
- Step 4.6 set `effort` matched to skill's cognitive load plus a `model` ID resolved from a named live source, or recorded `model: unresolved` with no `model` key when no source was reachable (caller's pinned override wins)
- Instructions internally consistent (no rule contradicts another)
- Every non-trivial instruction either example-bearing or links to one
- Manifest keywords + description accurately reflect what skill does
- Post-write verification (Step 6) confirms High = 0
- Routing verification (Step 7 sub-step 2) confirms target (+ every peer Pass O touched) is **indexed**, meaning the description stored in `registry.db` matches the file's and the skill surfaces for its own top intent phrase, rather than **stale** or **unroutable**; or, under `--no-sync` or a withheld rebuild (High findings remained at budget exhaustion), index-behind state reported. Compare stored text, never mtimes: a rebuild can exit 0 having silently skipped an entry
- Step 1 inventoried every discovered copy and distinguished active shadowing from intentional distributions and historical snapshots. Unresolved active shadowing remains a High finding; preserved external copies do not establish a global-sync claim
- Target skill has appropriate evals: `<skill-dir>/evals/evals.json` exists with at least 2–3 realistic test cases and verifiable assertions, and Pass H trigger evals (`<skill-dir>/evals/trigger-eval.json` / canonical corpus) are assembled and verified
- Step 2's offline pre-lint reports no unresolved critical or high finding (a false positive is recorded with its reason, not ignored)
- Step 6.3 reported trigger and behavior eval pass rates with their levels; the run did not exit `EVALS-MISSING`
- Step 6.7 printed the location table and verified every authorized destination. Preserved divergent, external or plugin-managed sources are reported separately. A blocked required destination reports `SYNC-PARTIAL`; a global-sync claim requires all required locations to be verified
- Pass P found the llms-first section present, added it, or recorded `n/a (<reason>)`
- Run did not exit `DEGRADED` (Step 7.8): fewer than two post-sync outcomes failed to land

## Meta-optimization note

Target's skill-optimizer itself? Step 5 writes alter instructions subsequent loop iterations would read. Step 3's "collect all findings before writing" rule makes this safe within single iteration. Across iterations, loop intentionally re-reads rewritten skill; this = convergence behavior, not bug. **Frozen pass definitions:** run's own pass definitions live in file being rewritten (target = skill-optimizer itself, its `references/`, or shared `references/shared/convergence-and-severity.md`)? Pass list, severity rubric, exit conditions frozen at Step 2 baseline snapshot for entire run; rewrite changing pass list takes effect only on NEXT run. Findings still recomputed each iteration against current file state; only evaluation procedure frozen. Freeze doesn't extend to sibling-optimizer targets generally; optimizing prompt-deep-optimizer never edits this skill's rubric mid-run, since Pass O peer writes additive-only.
