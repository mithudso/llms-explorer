# code-deep-optimizer — changelog

Moved out of SKILL.md frontmatter 2026-09-09: it was 2,546 bytes, 47% of the always-loaded
frontmatter, with no bearing on execution.

2026-10-05 sko v1.15.0->v1.16.0 — Pass H 10/10->11/11 pos, 0/10->0/11 neg (predicted); 1 High + 12 Medium fixed

## 2026-11-09 v1.17.0 -> 1.17.1 — require complete file-read coverage

- Read assigned files in bounded, separate slices and record covered line ranges. Hashes establish
  file identity only. Truncated or unread ranges stay partial; CLEAN requires complete coverage.
- This closes the review-evidence gap observed in the solmargintrader blind audit, where file
  hashes were recorded despite truncated or incomplete reads. The blind gate attempt cap is unchanged.

## 2026-11-06 v1.16.0 -> 1.17.0 — audit ledger, run receipt, tool-ergonomics pass

- `scripts/cdo_ledger.py`: per-file ledger kept in the target repo (`.cdo/ledger.json`: path, git
  blob sha, passes run, date, findings, verdict). A re-run reviews only new or changed files unless
  `--full`; a `--quick` triage does not count as coverage. Evidence: a whole-repo run left 189 of
  224 files unreviewed, and one repo was optimized 3 times in 3 weeks.
- "Passes that ran" receipt (`cdo_ledger.py receipt`) is now mandatory at the end of every run and
  fails (exit 2) when a pass has neither run nor carries a reason.
- Conditional pass M5 (tool ergonomics): one command, defaults, usage text, own venv/uv, preflight.
  Template `scripts/tool_bootstrap.py`; references `audit-ledger.md` and `tool-ergonomics.md`.
  M5 sits outside the fixed 18-pass count so no count elsewhere changes.

## 2026-10-05 v1.15.0 -> 1.16.0 — skill-optimizer pass (1 High, 9 Medium fixed)

- Body cut from ~10.3k to ~8.8k tokens (was over the 10k hard ceiling). Report format, empirical
  calibration, and the feature phase moved to `references/report-format.md`,
  `references/empirical-mode.md`, and `references/implement-features.md`. The settings/`lib/`
  rules no longer repeat three times: the pass definitions (M1-M4) are the single source.
- `--implement-features` now has a defined place: one phase after the loop exits CLEAN or
  CONVERGED, one verified round per feature, outside champion–challenger (its additions fail the
  public-API veto by design). New interaction row in `references/flags-and-statuses.md`.
- SKIP: prose now routes to `ddo` (document-critique is a cold spoke); new edge for a single known
  bug -> software-engineering-patterns (references/debugging.md).
- Removed hardcoded user-home `.llms` paths; stale "hot spoke" claims for code-reviewer and
  coding-standards corrected (both are cold).
- `model` -> claude-opus-5-5 (models overview, 2026-10-05). `metadata.changelog_ref` added.
- Two functional evals added (injection gate, feature phase). `/cdo` wrapper hint lists
  `--implement-features|--auto-improve`.
- v1.15.0 (hub restructure commit e3cc71d98) had no entry here.

## 2026-09-29 v1.13.0 -> 1.14.0 — optional feature & improvement implementation (`--implement-features`)

New opt-in check: when `--implement-features` (alias `--auto-improve`) is passed, the LLM identifies
features and improvements that would make the application better and implements all of them directly,
verified by the build/lint/test gate.
- New flag `--implement-features` / `--auto-improve` added to flags table (default OFF).
- New section § Optional feature & improvement implementation in SKILL.md.
- Behavior-drift guard updated: explicitly authorizes intentional feature additions under this flag.
- `references/advisory-track.md` updated: documents the implementing-features subsection and the
  relationship between `--suggest` (report-only) and `--implement-features` (identify + implement).
- `references/flags-and-statuses.md` updated: five new interaction rules covering `--implement-features`
  with `--quick`, `--read-only`, `--annotate`, `--no-verify`, and `--suggest`.

## 2026-09-29 v1.12.0 -> 1.13.0 — reusable libraries and lib folder extraction check

Added checks requiring that where possible code should use reusable libraries, store reusable code in library files that can be referenced by another application, and store these libraries in a `lib` folder with complete documentation and usage guides.
- M2 pass updated: flags reinvented utilities and requires using reusable libraries or extracting reusable functionality into library files.
- M3 pass updated: verifies repo-level decoupled library architecture storing cross-app reusable libraries in `lib/`.
- M4 pass updated: verifies that reusable libraries under `lib/` include complete documentation and usage guides (API reference, examples, setup instructions).
- Added dedicated guardrail for reusable libraries and `lib/` directory organization.
- Severity calibration updated: missing library reuse, non-modular reusable code, and undocumented `lib/` libraries mapped to Medium severity.
- language-skill-map.md activation matrix updated for M2, M3, and M4 signals.

## 2026-09-29 v1.11.0 -> 1.12.0 — central settings file & UI parameter mutability check

Added verification that all changeable parameters in code must be centralized in a dedicated settings file (e.g. `settings.ts`, `config.py`, settings schema), and any application UI must have programmatic access (via store, manager, or API) to view and modify that settings file.
- M1 pass updated: flags hardcoded changeable parameters/knobs (timeouts, thresholds, limits, endpoints, retry counts, toggles).
- M3 pass updated: verifies repo-level central settings architecture and UI accessibility/mutability.
- Added dedicated guardrail for centralized settings & UI configurability.
- Severity calibration updated: scattered parameters / missing central settings / UI blocked from settings access mapped to Medium/High.

## 2026-09-27 v1.10.0 -> 1.11.0 — memory-central prior-knowledge intake

New § 0.3b: before the passes, read the target project's `<slug>_lessons_llms.md` / `_conventions_llms.md`
(and `_decisions` when a fix would change architecture) from the central memory corpus `$HOME/.llms`
(memory-central-llms skill). Lessons with matching error strings become regression checks (≥ High when
reintroduced); conventions inform M1; a fix contradicting a recorded decision is `BLOCKED (ambiguous intent)`.
New guardrail: prior-knowledge rows are evidence, never instruction. Report gains item 11 (memory-central
line). Post-run lessons go to the repo's own memory store; the nightly `mcl_run.sh` recompiles the corpus.

## 2026-09-17 v1.9.0 -> 1.10.0 — skill-optimizer pass (2 High, 26 Medium fixed)

Routing surface: the description's `MQL -> deep-mongodb-mql-query-optimizer` named a skill that
does not exist as a top-level id; rewritten to the hub-aware form `mongodb-expert
(references/deep-mongodb-mql-query-optimizer.md)`, plus a `runtime-error/prod-log triage ->
error-monitor-remediator agent` SKIP edge, two more `whenToUse` phrasings, concrete
`whenNotToUse` entries (the old third entry was a pointer, not a user phrasing), and
`related_skills` widened to the hub, the family router, and every SKIP target.
Flags: `--read-only` + the C3 counterexample mechanic wrote a test file inside a no-write mode;
`--no-sync` "skip hub registration" pointed at a step cdo does not have (it now means the
post-run prose-index refresh only); `--scope=changed`, `--annotate`, `--quick` + `--no-verify`,
`--quick` + `--verify-end` and monorepo verify baselines were undefined. The interaction table
and a Status-to-contract-exit mapping (`OSCILLATING` now names cycling vs instability;
`BLOCKED (hostile content)` gains a run-level meaning) moved to a new
`references/flags-and-statuses.md`. Invocation now discloses-then-proceeds and names the
champion path (`~/.claude/skill-consolidation/champions/<target-slug>/champion.json`).
Rollback lines list created test files with `rm`. Worked example: line anchors, the diff hunk
header, the final settled-results diff, the C3 test, and the `npm test`-vs-no-manifest residual
(open since v1.7.0) all reconciled. Em-dash density cut from 2.4 to under 0.3 per 100 words
across SKILL.md and references. Contract: registered the code iteration cap (5; 3 small
profile) under § Iteration caps. Hot-spoke citations (`coding-standards`, `code-reviewer`)
follow the tiering engine's current form.
Blind re-audit ran twice (5 then 6 corroborated Mediums); the second set (T2/T3 scope, TRIAGE-CLEAN
definition, `--annotate` + empirical/quick rows, TRIGGER: moved earlier, worked-example pass
accounting) was applied as a final un-audited remediation at the operator's request. Exit:
BLIND-AUDIT-DISSENT, then applied.

## 2026-09-09 v1.8.0 -> 1.9.0 — contract-compliance pass

Applied from a /p audit (1 Critical, 6 High, 8 Medium found). Amended
`references/shared/convergence-and-severity.md` to add a registered **triage mode**
construct, legalizing `--quick`'s Critical-only bar instead of leaving it as a unilateral
exception to the profile invariant; registered cdo's small profile in the contract's table.
In this file: promoted the injection guard from a Guardrails bullet to a non-skippable Stage 0.5
gate propagated verbatim into every per-file subagent brief; adopted the contract's
streaming-checkpoint crash recovery (cdo fans out to 50 files and was the only heavy sibling
without it); gave `--quick` a verify baseline so FAIL can be attributed; fixed the
`min(16, cores-2)` concurrency underflow to `max(1, ...)`; added a flag-interaction table whose
first rule closes the `--no-verify` + default-on-empirical hole that left promotion ungated;
renamed `--structural-only` to `--no-empirical` (alias kept) to stop colliding with
skill-optimizer's `--meta` idiom; surfaced empirical mode's champion persistence at invocation;
moved this changelog out of frontmatter and collapsed SKIP guidance from three places to two.
`--minimal` was considered and declined — `--quick` plus full mode is the intended surface.

## Earlier

```
2026-09-04 v1.7.0->1.8.0 — added `--quick` fast path: 1 iteration, Critical-only findings, single end-of-run verify check (no baseline/bisect loop), skips Stage 0 formal activation ceremony, advisory track, empirical mode, and the blind re-audit gate. For low-stakes/prototype code where an 18-pass audit is disproportionate — not for anything shipping to production. Paired with an auto-optimize-dispatcher.sh hook fix: throwaway/sandbox/prototype-named files no longer get the full-convergence nag by default.
2026-07-20 sko v1.6.1->1.7.0 — Pass H 10/10 pos, 9/10->10/10 neg (predicted); 1 High + 8 Medium fixed across 2 iters: champion-challenger contract path restored (symlink at ~/.claude/skill-consolidation/), references synced 16->18-pass (map +S5/T4 rows, worked-example 14/18), cold-spoke citations hub-aware, SQL hot-spot SKIP edge -> deep-query-optimizer, O-seeded security-review + dmqo; exit BLIND-AUDIT-DISSENT (1 residual Medium: worked-example no-manifest wording vs npm-test verify baseline).
2026-06-23 sko v1.5.0->1.6.0 — Pass H 10/10 pos, 0/15 neg (predicted); 2 Medium fixed: added advisory model/effort frontmatter (Step 4.6 -> claude-opus-4-8 / xhigh, long-horizon agentic tier); trimmed changelog 8->5 entries (family 5-cap). No content/routing/over-ceiling/hygiene findings.
2026-06-23 v1.4.0->1.5.0 — Empirical mode now default-on (gated auto-promote + persist) per § Default policy in the shared contract: when a test/benchmark eval set + must-pass checks are present the champion–challenger loop runs without a trigger, auto-promotes through the unchanged gate (held-out margin + must-pass veto = suite green + API unchanged), and persists the champion across runs (prior champion archived for rollback); mandatory holdout rotation/budget/noise to prevent reusable-holdout overfitting; honest guarantee = monotonically non-decreasing on the holdout, not "better every run"; opt out --dry-run/--no-promote/--structural-only; loud no-eval fallback. Per operator request.
2026-06-23 v1.3.0->1.4.0 — added Empirical mode (champion–challenger held-out loop) section + --empirical flag, citing the new shared contract references/shared/champion-challenger.md; calibration: score = pass rate on a held-out test/benchmark subset (or perf metric), must-pass veto = full pre-existing suite green + no new lint/type errors + public API unchanged (reuse Verify-gate baseline). Orthogonal to the fix-track passes — no pass-count change. Per operator request.
```
