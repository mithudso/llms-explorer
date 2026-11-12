---
name: deep-eval-optimizer
description: >-
  Audit, improve and create evaluation suites for AI agent skills. TRIGGER: "optimize evals", "run deo", "audit skill evals", "create missing evals", "grade assertions", "run skill benchmarks". The 12-pass loop covers realistic prompts, objective assertions, near-miss triggers, fixtures, leakage and schemas; fixes Medium+ and preserves valid cases. --run requires a verified real executor; audit/dry-run writes nothing. SKIP: skill markdown → skill-optimizer; production prompts → prompt-deep-optimizer; code refactoring → code-deep-optimizer; skill-tree taxonomy → skill-tree-architect.
whenToUse:
  - "optimize evals for a skill"
  - "audit existing eval suite quality"
  - "create evals for a skill missing them"
  - "run skill evals and benchmark performance"
  - "grade assertions and prompts in an eval suite"
  - "calibrate trigger accuracy negative near-misses"
  - "run deo on this skill"
version: "1.1.1"
category: meta
updated: "2026-11-11"
model: claude-opus-5-5
effort: xhigh
triggers:
  - deo
  - deep eval optimizer
  - eval optimizer
  - optimize evals
  - audit evals
  - grade evals
  - create evals
  - run evals
  - fix evals
keywords:
  - deep-eval-optimizer
  - eval-suite
  - assertion-grading
  - trigger-accuracy
  - convergence-loop
  - benchmark-runner
  - prompt-realism
related_skills:
  - skill-optimizer
  - prompt-deep-optimizer
  - code-deep-optimizer
  - skill-creator
metadata:
  changelog_ref: references/CHANGELOG.md
---

# Deep Eval Optimizer (DEO)

Audit, grade, optimize, and generate evaluation suites for AI agent skills. Operates across both functional execution evals (`<target-dir>/evals/evals.json`) and trigger-accuracy evals (`<target-dir>/evals/trigger-eval.json`). Runs a 12-pass convergence loop (Passes A–L, defined in `references/passes.md`) to fix Medium+ findings in place, creates missing evals using bundled templates from `templates/`, and optionally executes benchmarks via a separately configured real executor. Call this optimizer's own directory `<optimizer-dir>` and the skill being audited `<target-dir>`. Resolve templates and `scripts/suite_validator.py` from `<optimizer-dir>`; resolve the target definition, fixtures and eval files from `<target-dir>`. For example, `/deo some-skill` validates its eval file with this optimizer's bundled helper, not `some-skill/scripts/suite_validator.py`.

## Look for llms files first

Before reading the target skill and its evaluation tree raw, look for its llms files and open them by size. If you have the repo, step 4 sets the order.
1. Look for the subject's `llms.txt`, its hub llms map, and memory-central keyword-index rows for the target terms.
2. Run `wc -c` first (or read `x-markdown-tokens` on a remote). Read a file whole only when it fits. Otherwise search it.
3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map, not a fact store.
4. If you have the repo, grep the code before you open an llms file. The code is the authority. Use maps to find the right file and verify every fact against its `path:line`.
5. Index and llms hits are leads. Confirm them with Read before you act.

## Invocation

Trigger with `/deo <skill-id-or-path> [flags]` or naming the skill in conversation:

- `/deo prompt-deep-optimizer`: Audits and optimizes existing evals for `prompt-deep-optimizer`.
- `/deo my-skill --create`: Generates missing eval suites from templates if not present.
- `/deo my-skill --run`: Optimizes evals and runs them only when an actual executor and its measurement contract are available; otherwise report `EXECUTOR_UNAVAILABLE`.
- `/deo my-skill --audit`: Read-only pass; reports findings across Passes A-L without writing.
- `/deo my-skill --max-iter=2`: Caps convergence iterations.

Full flag catalog lives in `references/flags-and-statuses.md`.

## The 12 Analytical Passes

Defined in detail in `references/passes.md`:

| Pass | Focus | Core Question |
|---|---|---|
| **Pass A** | Prompt Realism | Are prompts authentic and natural rather than robotic or synthetic? |
| **Pass B** | Discriminative Power | Does the eval separate skill vs baseline / old skill performance? |
| **Pass C** | Assertion Objectivity | Are assertions deterministic, verifiable, and free of vague vibes? |
| **Pass D** | Near-Miss Coverage | Do negative trigger queries probe realistic domain collisions? |
| **Pass E** | Determinism Hygiene | Are temporal refs frozen, inputs isolated, and flakiness eliminated? |
| **Pass F** | Leakage / Tautology | Does the prompt avoid leaking skill names or spoon-feeding answers? |
| **Pass G** | Fixture Integrity | Are input files verified, self-contained, and token-budgeted? |
| **Pass H** | Surface Coverage | Does the suite cover happy path, edge cases, and transformations? |
| **Pass I** | Output Precision | Is `expected_output` an exact, measurable specification? |
| **Pass J** | Cost & Efficiency | Are fixtures right-sized to minimize unnecessary token burn? |
| **Pass K** | Anti-Overfitting | Is there a held-out train/validation split during prompt tuning? |
| **Pass L** | Schema Compliance | Does the JSON strictly conform to canonical eval schemas? |

## Process

**Pipeline:** 1 Locate target & existing evals → 2 Create missing evals (if absent) → 3 Autonomous Rewrite-Commit-Eval Convergence Loop (Audit → In-Place Rewrite → Git Commit → Run Eval Suite → Loop until 0 Medium+) → 4 Verification & Re-aggregate → 5 Report.

### Step 1 — Locate Skill & Evals
1. Resolve write mode first. `--audit` and `--dry-run` are read-only: no file creation, rewrite, snapshots, corpus updates, commits or executor runs. A plugin-managed or unowned target is read-only unless the caller authorizes an owned fork. Missing suites become proposed artifacts in the report.
2. Resolve skill directory (`~/.claude/skills/<id>`, `~/.global-ai-hub/skills/<id>`, or direct path).
3. Inspect `<target-dir>/evals/` for:
   - Functional evals: `evals/evals.json`
   - Trigger evals: `evals/trigger-eval.json`
   - Canonical corpus: `~/.claude/skill-consolidation/evals/<skill-id>.eval.jsonl`

### Step 2 — Missing Eval Generation
If evals are absent and write mode permits it (`--create` never overwrites valid existing cases):
1. Create `<target-dir>/evals/` directory.
2. Read the appropriate bundled template from `templates/` (`functional-eval-template.json`, `code-eval-template.json`, or `trigger-eval-template.json`).
3. Tailor prompts, expected outputs, assertions, and trigger queries specifically to the target skill's domain and instructions.
4. Write `<target-dir>/evals/evals.json`. Preserve/replay any canonical trigger corpus, update its query/expectation rows first, then derive `<target-dir>/evals/trigger-eval.json`; the projection is never the source of truth. Under read-only mode, print proposals instead.

### Step 3 — Autonomous Rewrite-Commit-Eval Convergence Loop
In write mode, run the audit/rewrite/verification loop (default 3 iterations; `--max-iter=N` may set 1–5). In audit/dry-run mode run one diagnostic iteration without writes or execution:

1. **Passes A–L Audit:** Evaluate `SKILL.md`, `evals/evals.json`, and `evals/trigger-eval.json` against all 12 analytical passes.
2. **Triage Severity:**
   - **High:** Malformed schema, zero assertions, missing input fixtures, artificial answer leakage. (Must fix).
   - **Medium:** Vague/subjective assertions, insufficient near-misses, underspecified expected outputs, missing edge cases, prompt token bloat. (Must fix).
   - **Low:** Minor wording polish, cosmetic formatting. (Defer).
3. **Rewrite in Place:** Apply all High and Medium fixes directly to `SKILL.md`, `evals/evals.json`, and `evals/trigger-eval.json`.
4. **Preserve work:** Follow the target repository's instructions and user authorization for commits. Stage only owned changes; do not automatically commit another person's work.
5. **Validate and execute (write mode only):** Run the bundled validator with `python3 <optimizer-dir>/scripts/suite_validator.py <eval-path>` (the resolved target eval JSON path). Inspect its findings; a zero process exit alone does not mean the suite passed. If `--run` is requested, discover a real execution harness, verify that it actually invokes the target skill, and record its command, observations and exit status. Replay, generated expected outputs and simulated grading are not executed skill results. If no suitable executor exists, report `EXECUTOR_UNAVAILABLE` and do not claim benchmark rates or convergence.
6. **Convergence decision:** Require zero unresolved Medium-or-higher findings and the selected verification evidence. Missing requested execution remains `EXECUTOR_UNAVAILABLE`. Stop at the iteration cap with unresolved findings reported.

### Step 4 — Verification and aggregation
Verify the final changes and report completed checks. Aggregate benchmark results only from actual recorded executions; label simulated or replay data separately.

### Step 5 — Report
Emit report containing:
- Iterations executed to achieve convergence
- Baseline vs final eval count and assertion count
- Findings table by Pass (Passes A–L) with resolutions
- Git commit hashes produced during the rewrite loop
- Benchmark test results and pass rates

## Quality Bar
Core checks below apply to every selected suite. Kernel tracing, gradient attribution, boundary mining, Shapley analysis and sequential canary trials are optional diagnostics: select them only with explicit scope, compatible tools and actual observations. Mark selected unavailable methods UNAVAILABLE and retain their evidence gap. Never install kernel probes or collect telemetry merely to audit a suite. Apply the following checks when the required tools, evidence and scope exist. Mark unavailable methods UNAVAILABLE; never claim a measurement without executing it. A clean or converged verdict requires all selected checks and evidence. An evaluation suite passes when:
- 0 High or Medium findings remain across Passes A–L
- Contains at least 2–3 diverse functional test cases (happy path, edge case, data/fixture handling)
- Contains at least 2 verifiable, objective assertions per test case (Structural, Schema, Deterministic, Negative Bounds, Count Reconciliation)
- Negative tripwires are enforced multiplicatively ($S_{\text{final}} = S_{\text{pos}} \times \prod_j (1 - T^-_j)$)
- Workspace honeypot canary traps (`.env`, protected directories) are integrated with zero-tolerance kernel syscall interception via eBPF VFS inode maps
- Trigger evals contain exactly 20 queries (10 positives, 10 realistic near-miss negatives with contrasting intent $\text{Verb}_{\text{competing}} + \text{Noun}_{\text{shared}}$)
- Hard negative trigger queries probe the annular decision boundary shell ($\cos \in [\tau - 0.05, \tau)$) via HotFlip first-order gradient projection and POS filtering
- Zero answer leakage: $\mathcal{C}_4(p, S) \le 0.05$, $\mathcal{C}_6(p, S) = 0$, and attention gradient saliency leakage $\mathcal{L}_{\text{leak}} \le 0.40$ ($H(\mathbf{p}) \ge 0.50 \ln N$) verified via Gauss-Legendre Integrated Gradients completeness
- System prompt instructions exhibit non-negative Causal Shapley attribution ($\forall i, \phi_i(v) \ge 0$) via Stratified Kernel SHAP with dead tokens pruned
- Zero regressions allowed on frozen golden datasets ($\forall t \in \mathcal{G}_{\text{golden}}, \text{Pass}(v_{\text{challenger}}, t) \ge \text{Pass}(v_{\text{champion}}, t)$)
- Dynamic canary rollouts governed by a predeclared Sequential Probability Ratio Test (SPRT) early stopping with precomputed integer martingale boundaries
- When `--run` is executed, positive trigger rate is $\ge 90\%$, false-positive rate is $\le 10\%$, and net capability delta $\Delta > 0$
