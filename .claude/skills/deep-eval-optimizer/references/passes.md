# Deep Eval Optimizer — Analytical Passes

The 12 analytical passes run by `deep-eval-optimizer` (`/deo`) to audit, grade, and optimize evaluation suites for AI agent skills.

---

### Pass A — Prompt Realism & Ecological Validity
Audits user prompt authenticity.
- **Defects:** Robotic, overly-specified, or synthetic prompts ("Please execute the foo skill using standard parameters").
- **Fix:** Rewrite into authentic, natural user phrasings—including casual, terse, messy, and jargon-rich varieties observed in production logs.
- **Severity:** Medium if unrealistically artificial; High if prompts provide step-by-step instructions not present in real user queries.

### Pass B — Discriminative Power & Baseline Contrast
Evaluates whether the eval discriminates between a model executing with the skill versus baseline (without skill or older version).
- **Defects:** Non-discriminating assertions that pass trivially without the skill or fail regardless of skill quality.
- **Fix:** Anchor assertions directly to behaviors, structures, and outputs that specifically depend on the skill's instructions. Require positive delta lift: $\Delta M = M(\text{Agent} \mid \text{Skill}) - M(\text{Agent} \mid \emptyset) \ge 0.20$.
- **Cost-Benefit Gating:** Evaluate Cost-Adjusted Efficiency Ratio $\mathcal{E} = \frac{\Delta_{\text{acc}}}{\log_2(\text{Tokens}_{\text{with}} / \text{Tokens}_{\text{without}} + 1)}$.
- **Causal Shapley Token Attribution:** Decompose prompt lift to instruction clauses via Shapley values: $\phi_i(v) = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!(|N|-|S|-1)!}{|N|!} [v(S \cup \{i\}) - v(S)]$. Excise any instruction clause where $\phi_i(v) < 0$ to eliminate dead tokens and cognitive impedance.
- **Kernel SHAP Power Set Stratification:** Stratify power set evaluations across cardinality strata $k \in \{1, \dots, N-1\}$ with weights $w_k = \frac{N-1}{k(N-k)}$. Enforce DAG topological poset constraints to eliminate unparseable invalid states and solve using regularized Cholesky decomposition.
- **Severity:** Medium for non-discriminating assertions; High if the entire eval produces identical verdicts with and without skill.

### Pass C — Assertion Objectivity & Verifiability
Audits assertion precision and grading mechanics across the 5 formal assertion classes (Structural, Schema, Deterministic Content, Negative Bounding, Count Reconciliation).
- **Defects:** Subjective assertions ("output looks great", "well-written response", "thoughtful analysis").
- **Fix:** Convert to verifiable structural, deterministic, or negative checks (schema validation, regex patterns, table structures, line limits, explicit fact inclusion).
- **Multiplicative Circuit Breakers:** Enforce tripwires as boolean multipliers: $S_{\text{final}} = S_{\text{pos}} \times \prod_j (1 - T^-_j)$. Any single negative tripwire violation zeroes the test case score.
- **Dynamic Honeypot Syscall Interception:** Seed workspace canary resources (`repo/.env.local`, read-only git trees). Audit system calls via eBPF/`ptrace` (`sys_enter_openat`, `sys_enter_unlinkat`); any unauthorized mutation aborts test execution instantaneously with zero tolerance.
- **eBPF VFS Inode Probes:** Attach in-kernel BPF probes directly to `vfs_write` and `vfs_unlink`, matching `(dev_t, ino_t)` hash maps to eliminate symlink and relative-path bypass vulnerabilities with sub-microsecond latency.
- **Severity:** High if assertions cannot be verified programmatically; Medium if vague criteria allow subjective flakiness.

### Pass D — Near-Miss & False-Positive Coverage (Trigger Calibration)
Audits the negative query set for trigger accuracy and hard-negative boundary calibration.
- **Defects:** Naive, irrelevant negatives ("how to bake a cake" for a database skill) or strawman distractors.
- **Fix:** Replace with true near-misses constructed via contrasting intent: $\text{Query} = \text{Verb}_{\text{competing}} + \text{Noun}_{\text{shared}}$. Harvest production routing failure traces into permanent regression suites.
- **Semantic Vector Boundary Mining:** Probe the exact decision boundary hypersphere strip $\cos(\mathbf{e}_q, \mathbf{e}_{\text{anchor}}) \in [\tau - \delta, \tau)$ ($\delta \in [0.01, 0.05]$) using continuous projection and HotFlip token perturbations. Enforce that hard negative probes fail to trigger the classifier while retaining strict negative ground-truth intent.
- **HotFlip Token Gradient Projection:** Linearize the router loss surface using first-order directional derivatives: $\mathbf{\Delta s}_i = \mathbf{E} \cdot \mathbf{g}_i - (\mathbf{E}_{t_i}^T \mathbf{g}_i) \mathbf{1}_V$. Combine with Part-of-Speech grammatical filters and perplexity beam search to synthesize fluent, minimally perturbed near-miss triggers.
- **Severity:** High if negative set has < 10 queries or 0 near-misses; Medium if negatives lack lexical overlap diversity.

### Pass E — Flakiness & Determinism Hygiene
Audits reproducibility and stability across repeated execution trials.
- **Defects:** Prompts with moving dates ("today", "yesterday"), external network dependencies, or assertions sensitive to minor token variance.
- **Fix:** Freeze temporal references, use static input fixtures in `<INPUT>/`, and define tolerance bands for quantitative assertions. Track flakiness standard deviation across $K=3$ runs ($\sigma_i > 0$ triggers test quarantine).
- **Severity:** High if eval intermittently fails on identical outputs; Medium if unseeded or unbounded.

### Pass F — Leakage & Tautology (Answer Contamination)
Audits prompt independence from internal skill implementation and system prompt instructions.
- **Defects:** Prompt explicitly states the skill name ("use the foo-bar skill to...") or quotes internal system prompt rules verbatim, priming self-attention heads.
- **Fix:** Apply the Natural User Persona Transform: frame prompt purely in terms of user intent, symptoms, and pain points; remove internal nomenclature.
- **N-Gram Gating Invariant:** Enforce $\mathcal{C}_4(p, S) \le 0.05$ and $\mathcal{C}_6(p, S) = 0$ (zero 6-gram matches between prompt and skill).
- **Attention Gradient Saliency Decontamination:** Measure Integrated Gradients path integrals $\text{IG}_i(y_t)$ across prompt embeddings. Compute prompt attention entropy $H(\mathbf{p}) = -\sum p_i \ln p_i$. Enforce leakage score $\mathcal{L}_{\text{leak}} = 1 - \frac{H(\mathbf{p})}{\ln(N)} \le 0.40$; mask or neutralize any token exhibiting outlier attribution spikes ($z \ge 3.0$).
- **Gauss-Legendre Integrated Gradients:** Compute token attributions along straight-line paths via Gauss-Legendre quadrature roots $t_k \in [-1, 1]$ over $m=20$ interpolation steps. Verify the Completeness Axiom ($|\sum \text{IG}_i - \Delta F| / |\Delta F| \le 0.05$) to mathematically guarantee zero uncaptured answer leakage.
- **Severity:** Medium if skill name is leaked; High if prompt spoon-feeds the exact algorithm.

### Pass G — Input Fixture Integrity & Isolation
Audits referenced input files (`files: [...]`).
- **Defects:** Missing fixture files, non-relative paths, multi-megabyte oversized fixtures, or un-sanitized PII.
- **Fix:** Place self-contained fixtures in `inputs/`, reference via `<INPUT>/<file>`, and bound file sizes under 50KB to preserve token budgets.
- **Severity:** High if referenced file is missing; Medium if fixture is unnecessarily bloated (> 5k tokens).

### Pass H — Coverage & Boundary Distribution
Audits breadth of scenarios across the skill's surface.
- **Defects:** All evals test the happy path; edge cases, error recovery, input conflicts, and empty states are unrepresented.
- **Fix:** Balance suite with at least 1 happy-path, 1 edge-case/conflict, and 1 file/data transform or failure-recovery eval.
- **Severity:** Medium if only 1 scenario tested; High if skill has multiple distinct modes with zero eval coverage.

### Pass I — Expected Output Precision & Completeness
Audits the `expected_output` field.
- **Defects:** Terse or empty output descriptions ("returns answer").
- **Fix:** Write an exact specification of expected deliverable, sections, tables, key entities, and concluding counts.
- **Severity:** Medium if vague; High if empty.

### Pass J — Cost, Latency & Token Efficiency
Audits evaluation runtime expense and context bloat.
- **Defects:** Evals requiring massive contexts or multi-turn recursive loops where a focused prompt suffices.
- **Fix:** Compact test inputs while maintaining realism. Ensure skill context overhead does not exceed 20% without measurable quality lift.
- **Severity:** Low to Medium if execution exceeds 100k input tokens without architectural necessity.

### Pass K — Anti-Overfitting & Champion-Challenger Gating
Audits generalization safeguards and regression protection.
- **Defects:** Description or skill instructions tuned to pass exact eval queries while failing slight paraphrases.
- **Fix:** Establish a 60/40 train/validation split; hold out validation queries during prompt/description rewrites. Enforce Champion-Challenger Canary Invariants: zero regressions allowed on the frozen golden regression suite ($\forall t \in \mathcal{G}_{\text{golden}}, \text{Pass}(v_{\text{challenger}}, t) \ge \text{Pass}(v_{\text{champion}}, t)$).
- **Bayesian Sequential Canary Early Stopping:** Implement Wald's Sequential Probability Ratio Test (SPRT) with cumulative log-likelihood ratio $\Lambda_m = S_m \ln(p_1/p_0) + (m - S_m) \ln((1-p_1)/(1-p_0))$. Terminate and abort failing candidate skills dynamically when $\Lambda_m \le \ln(\beta / (1 - \alpha))$, achieving up to 90% compute cost savings.
- **Wald Martingale Linear Boundaries:** Precompute exact integer decision boundaries $S_m \ge \lceil s \cdot m + h_1 \rceil$ (promote) and $S_m \le \lfloor s \cdot m + h_0 \rfloor$ (abort) derived from Doob's Optional Stopping Theorem, ensuring false promotion probability remains strictly bounded by $\alpha$.

### Pass L — Format & Schema Compliance
Audits structural JSON schema compliance.
- **Defects:** Missing `id`, `name`, `prompt`, `expected_output`, or `assertions` arrays; malformed JSON.
- **Fix:** Repair schema to conform strictly to canonical `evals.schema.json` and `trigger-eval.schema.json` specifications.
- **Severity:** High if file fails JSON parse or misses required top-level keys.

