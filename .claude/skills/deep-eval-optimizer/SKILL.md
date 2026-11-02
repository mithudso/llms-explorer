---
name: deep-eval-optimizer
description: >-
  Audit, grade, optimize, and generate evaluation suites for AI agent skills across the corpus: runs a 12-pass convergence loop (Passes A-L) on eval prompts, assertions, near-miss trigger sets, and fixtures; writes Medium+ fixes in place; creates missing evals from templates; executes test runs via --run.
  TRIGGER: "optimize evals", "audit skill evals", "create evals for skill", "eval optimizer", "run deo", "deep eval optimizer", "grade evals", "fix evals", "run skill evals", "eval test cases".
  SKIP: optimize skill markdown/code/prompts → skill-optimizer / sko; optimize general system prompts → prompt-deep-optimizer / pdo; code AST refactoring → code-deep-optimizer / cdo; tree rebalancing → skill-tree-architect.
whenToUse:
  - "optimize evals for a skill"
  - "audit existing eval suite quality"
  - "create evals for a skill missing them"
  - "run skill evals and benchmark performance"
  - "grade assertions and prompts in an eval suite"
  - "calibrate trigger accuracy negative near-misses"
  - "run deo on this skill"
version: 1.0.0
category: meta
updated: "2026-09-29"
model: claude-opus-5
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

Audit, grade, optimize, and generate evaluation suites for AI agent skills. Operates across both functional execution evals (`<skill-dir>/evals/evals.json`) and trigger-accuracy evals (`<skill-dir>/evals/trigger-eval.json`). Runs a 12-pass convergence loop (Passes A–L, defined in `references/passes.md`) to fix Medium+ findings in place, creates missing evals using standard templates from `~/dev/evals/templates/`, and optionally executes benchmarks via `--run`.

## Invocation

Trigger with `/deo <skill-id-or-path> [flags]` or naming the skill in conversation:

- `/deo prompt-deep-optimizer`: Audits and optimizes existing evals for `prompt-deep-optimizer`.
- `/deo my-skill --create`: Generates missing eval suites from templates if not present.
- `/deo my-skill --run`: Optimizes evals and immediately executes them via `~/dev/evals/runner/eval_runner.py`.
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
1. Resolve skill directory (`~/.claude/skills/<id>`, `~/.global-ai-hub/skills/<id>`, or direct path).
2. Inspect `<skill-dir>/evals/` for:
   - Functional evals: `evals/evals.json`
   - Trigger evals: `evals/trigger-eval.json`
   - Canonical corpus: `~/.claude/skill-consolidation/evals/<skill-id>.eval.jsonl`

### Step 2 — Missing Eval Generation
If evals are absent (or caller passed `--create`):
1. Create `<skill-dir>/evals/` directory.
2. Read appropriate template from `~/dev/evals/templates/` (`functional-eval-template.json`, `code-eval-template.json`, or `trigger-eval-template.json`).
3. Tailor prompts, expected outputs, assertions, and trigger queries specifically to the target skill's domain and instructions.
4. Write `<skill-dir>/evals/evals.json` and `<skill-dir>/evals/trigger-eval.json`.

### Step 3 — Autonomous Rewrite-Commit-Eval Convergence Loop
The optimizer **always** executes the rewrite-commit-eval loop until convergence (max 5 iterations):

1. **Passes A–L Audit:** Evaluate `SKILL.md`, `evals/evals.json`, and `evals/trigger-eval.json` against all 12 analytical passes.
2. **Triage Severity:**
   - **High:** Malformed schema, zero assertions, missing input fixtures, artificial answer leakage. (Must fix).
   - **Medium:** Vague/subjective assertions, insufficient near-misses, underspecified expected outputs, missing edge cases, prompt token bloat. (Must fix).
   - **Low:** Minor wording polish, cosmetic formatting. (Defer).
3. **Rewrite in Place:** Apply all High and Medium fixes directly to `SKILL.md`, `evals/evals.json`, and `evals/trigger-eval.json`.
4. **Git Commit Changes:** Automatically commit modifications to git with a clear audit diff trail:
   ```bash
   git add <skill-dir> && git commit -m "fix(<skill-id>): deo convergence loop iteration <N> - resolve Medium+ findings"
   ```
5. **Execute Eval Test Suite:**
   - Validate suite schema & assertions: `python3 ~/dev/evals/benchmarks/suite_validator.py <eval-file>`
   - Execute functional runner: `python3 ~/dev/evals/runner/eval_runner.py <evals.json> --output-dir ~/dev/evals/results/<skill-name>`
   - Execute trigger runner: `python3 ~/dev/evals/runner/trigger_runner.py <trigger-eval.json>`
6. **Convergence Decision:**
   - If findings count (High + Medium) == 0 AND all eval runner assertions pass: **Converged**. Proceed to Step 4.
   - If findings remain OR assertions fail: Advance iteration count $N \leftarrow N + 1$ and repeat from Step 3.1.
   - If iterations reach 5 without full convergence: Terminate with `UNRESOLVED_FINDINGS` warning and detailed triage diff.

### Step 4 — Verification & Benchmark Aggregation
1. Final verification of git working tree status and clean test pass.
2. Re-aggregate corpus benchmark:
   ```bash
   python3 ~/dev/evals/benchmarks/aggregate.py ~/dev/evals/results ~/dev/evals/results/summary.md
   ```

### Step 5 — Report
Emit report containing:
- Iterations executed to achieve convergence
- Baseline vs final eval count and assertion count
- Findings table by Pass (Passes A–L) with resolutions
- Git commit hashes produced during the rewrite loop
- Benchmark test results and pass rates

## Quality Bar
An evaluation suite passes when:
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
- Dynamic canary rollouts governed by Wald's Bayesian Sequential Probability Ratio Test (SPRT) early stopping with precomputed integer martingale boundaries
- When `--run` is executed, positive trigger rate is $\ge 90\%$, false-positive rate is $\le 10\%$, and net capability delta $\Delta > 0$



