# Compounding Expertise — An Iterative Skill-Optimization Pipeline

### How an iterative, multi-stage skill-optimization pipeline achieves defensible predictive accuracy in MongoDB case resolution

**A technical whitepaper for MongoDB technical leadership · mdb-tam engineering · June 2026**

---

## Executive summary

Automated case resolution is, at its core, a prediction problem: given only what a customer first reported, predict the root cause accurately enough to act on. The instinct is to solve it with a bigger model and a bigger prompt. The evidence in this paper suggests the binding constraint is knowledge engineering, not model size.

We built a system that treats expertise as something to be **engineered**, not just prompted. It integrates five distinct skillsets — **MongoDB domain authority, applied psychology, writing, troubleshooting/diagnostic reasoning, and expertise engineering** — and drives each one through the same **iterative, multi-stage optimization pipeline**: acquire the missing knowledge, optimize every skill/prompt/document to convergence against a severity-gated quality bar, compose the optimized components in a runtime orchestrator, then validate the whole stack with a blind backtest whose errors feed the next cycle.

The diagnostic core of this pipeline was measured on a **blind panel of 244 real cases** (`okta-blind-244-v1`), under conditions a skeptic would accept: the predictor saw only the customer's first report, never the resolution, and the predictor was never its own grader. The optimized skill-knowledge strategy scored:

- **72.5% raw accuracy** across all 244 cases,  
- **90.3% accuracy on the 196 gradable cases**, and  
- **100% defensibility — zero Wrong predictions.**

The more interesting finding is the comparison. The optimized skill-knowledge strategy **beat** both an authored-flowchart bundle and a documented-flowchart corpus, and adding those two strategies on top of it lifted accuracy by only 1.5 points (72.5% → 74.0%) — so optimized skill knowledge alone accounted for nearly all of the accuracy the three strategies reached together. And the result came not from a single artifact but from a **repeatable pipeline**: the same convergence loop that tuned the diagnostic knowledge also tuned the prompts, the customer replies, and the skills themselves.

This paper documents that pipeline: the problem it solves, why single-technique approaches plateau, the architecture, the backtest evidence, and what a team needs to reproduce it. The intended reader is a technical leader deciding whether to invest in engineered, measured expertise over ad-hoc prompt iteration.

**Scope and honesty note.** The 244-case backtest scores the **diagnostic-accuracy** contribution — can the system name the right root cause. The psychology and writing skillsets address a different part of resolution quality — whether the delivered reply repairs trust, avoids resistance, and lets a human calibrate trust in the AI's hypothesis — which this backtest does not directly score. We are explicit throughout about which claims the evidence supports and which it does not.

---

## 1\. The problem: case resolution is a blind prediction under a low accuracy ceiling

A support case arrives as a customer's first description of a symptom. The resolver — human or machine — must predict the root cause from that description, gather the right evidence, and act. Three properties make this hard, and make naive solutions plateau.

**It is genuinely blind.** At prediction time the resolution does not exist yet. Any method that, in testing, has even indirect access to the answer will overstate its real-world accuracy. A credible accuracy number can only come from a panel where the predictor sees what the customer first saw and nothing more.

**The domain is broad and interacting.** A MongoDB/Atlas case can sit in any of a dozen subdomains — CRUD and indexing, the aggregation framework, replication, sharding, drivers, the Atlas control plane, networking, encryption, search, capacity — and the hardest cases span several at once. A method strong in one subdomain and weak in the next has a low ceiling on a representative panel.

**Resolution is more than the diagnosis.** Even a correct root cause fails the customer if the reply triggers reactance, erodes trust after an incident, or leaves a human unable to judge how far to trust the analysis. Accuracy and delivery are separate axes, and a system optimized for one can still fail on the other.

The consequence is a low, deceptive ceiling. Methods that look strong in a demo — a clever prompt, a favorite flowchart — can collapse on a broad blind panel when they were tuned against the cases their author already understood. The question this paper answers is: *what architecture raises the real, blind-panel ceiling, and how do you prove the number is honest?*

---

## 2\. Why single-technique approaches fall short

Four common approaches each capture part of the answer and stall on the rest.

**A bigger model with a bigger prompt.** Concatenating all available knowledge into one context window is easy and scales badly. It pays for redundant and irrelevant context on every call, buries the few relevant facts, and — most importantly — has no mechanism to *improve*. When it gets a case wrong, nothing changes. There is no loop.

**Raw, un-tuned domain knowledge.** A comprehensive knowledge base is necessary but not sufficient. Knowledge written for humans to browse is not organized for a model to retrieve and reason over under blind conditions; without an optimization pass it carries dead weight, ambiguity, and untested assumptions that surface as wrong or hedged predictions.

**Authored decision flowcharts.** Expert-authored flowcharts encode real diagnostic skill, but they encode *one expert's* paths. On a broad panel they are strong where the author's experience was deep and silent where it was thin. In our backtest, an authored-flowchart bundle and a documented-flowchart corpus were both **outperformed** by optimized skill knowledge — and adding them on top of it produced almost no lift (Section 4).

**Prompt iteration without evaluation.** Hand-tuning a prompt against a handful of cases optimizes for those cases. Without a blind panel and error analysis, the practitioner has no way to know whether a change helped in general or just fit the examples in front of them — the classic overfitting failure that `eval-driven-development` is built to prevent.

The gap common to all four is the same: none of them, alone, both **raises the knowledge quality systematically** and **measures the result honestly**. That is the joint problem the pipeline is built to solve.

---

## 3\. The approach: five skillsets, one optimization loop

The system rests on a single idea: **treat expertise as an engineered artifact with a quality bar, a tuning loop, and an acceptance test.** Concretely, that means five complementary skillsets driven through four pipeline stages.

### 3.1 The five skillsets

These are catalogued in full in the companion *Skill Catalog* (Appendix A); in brief:

1. **MongoDB domain authority** — the deep `mongodb-*` and Atlas expert hubs, compiled for diagnosis into the 66-part `uber-mongodb-skill` behind the read-only `uber-mongodb-diagnostician`. This is the diagnostic engine.  
2. **Troubleshooting / diagnostic reasoning** — the methodology of fault-finding: choosing a diagnostic surface, gathering evidence, and the illness-script and key-feature framings drawn from `teaching-troubleshooting-diagnostic-reasoning` and `software-engineering-patterns`.  
3. **Writing** — the craft and the critique loops (`technical-writing-craft`, `content-and-marketing-writing`, `document-critique`/`ddo`, `kill-the-AI-ism`) that turn a cited analysis into a customer-ready reply and an internal readout.  
4. **Applied psychology** — trust repair (Mayer's ABI model), reactance avoidance, and crucially **calibrated reliance** on AI output (automation bias and algorithm aversion), so that a human neither rubber-stamps nor reflexively rejects the AI's hypothesis.  
5. **Expertise engineering** — the meta-layer that *captures* tacit expert knowledge (`cognitive-task-analysis`), *measures* competence (`assessment-certification-design`, `learning-measurement-evaluation`), and *builds and tunes* the skills, prompts, and code themselves (`skill-creator`/`skill-optimizer`, `prompt-deep-optimizer`, `code-deep-optimizer`, `concept-family-explorer`).

The first four are domains an answer is built from. The fifth is what makes the other four good — and is the reason the pipeline compounds rather than plateaus.

### 3.2 The four pipeline stages

**Stage 1 — Acquire (close the knowledge gaps).** `concept-family-explorer` maps a subject's full conceptual family — parent domain, siblings, sub-concepts, adjacent fields, frontier — surfaces what is *missing*, scores each gap, and loops deep research (`/dr`) on every viable gap until the concept tree saturates. This is how the domain authority reaches breadth before anything is tuned: gaps are found deliberately, not discovered by failing a case in production.

**Stage 2 — Optimize (raise every artifact to a quality bar).** Each artifact type has a deep-optimizer, and they are all the *same loop* over a single shared reference, `convergence-and-severity.md`:

- `prompt-deep-optimizer` — production prompts (a 16-pass audit in 5 parallel bundles)  
- `code-deep-optimizer` — source code (16-pass, verified against build/lint/tests)  
- `document-critique` / `ddo` — prose (passes 0–14)  
- `design-deep-optimizer` — visual/UI artifacts (11-pass)  
- `skill-optimizer` — the skills themselves

The shared model is what makes "optimize" mean something precise. It defines a **severity ladder** (Blocking → Major → Medium → Minor → Nit, with the rule: fix everything Medium-and-above), **seven convergence exit conditions** (clean, no-progress, content-cycling, stable-rewrite, loop-instability, iteration-cap, budget), bounded **iteration caps** (five for prompts; three for skills and documents, raised to five only if Medium+ findings dropped by half in the prior pass), and — the anti-self-congratulation safeguard — a **blind re-audit gate**: before any artifact may be declared "clean," a fresh-context subagent re-audits the final version with no access to the findings history or fix rationale. Only corroborated findings count. This is what stops an optimizer from grading its own homework.

**Stage 3 — Compose (run the optimized components on a live case).** `solve-case` is the runtime orchestrator. Its seven phases take a case from intake → customer identification → troubleshooting and diagnosis → deep-dive on any unknown → fact-based cited analysis → a customer-psychology-informed reply → a wrap-up bundle (analysis, drafted reply, blockers, tools used, who to talk to, escalation decision, insights). It calls the optimized domain authority for diagnosis, the writing loops for the reply, and the psychology agent to pressure-test the message before a human sends it.

**Stage 4 — Evaluate and feed back (measure honestly, improve deliberately).** `diagnosis-methodology-backtest` runs a **blind, parallel, multi-agent** evaluation against ground-truth resolutions. Its design enforces the two invariants Section 1 identified as necessary — a methodology sees only the customer's first report, and the predictor is never its own grader — and runs each methodology in an isolated subagent. `eval-driven-development` supplies the discipline around it: **error analysis as the engine**, the Three Gulfs (Specification, Generalization, Comprehension), and judge calibration against human labels (Cohen's kappa, Krippendorff's alpha). The errors the backtest surfaces become the gaps Stage 1 closes and the findings Stage 2 fixes on the next cycle.

The feedback loop is what makes the architecture self-improving rather than static: Stage 4's errors drive Stage 1's acquisition and Stage 2's optimization, which improve Stage 3's runtime, which Stage 4 then re-measures.

---

## 4\. Proof: the okta-blind-244-v1 backtest

The pipeline's diagnostic core was measured on a blind panel of **244 real cases**, `okta-blind-244-v1`. The conditions were adversarial by design: the predicting methodology saw only what the customer first reported, never the resolution, and a separate grader scored the predictions.

Three diagnosis methodologies were compared:

1. **Phase 1 — skill knowledge:** the optimized `mongodb-*` skill expertise (the diagnostic output of this pipeline).  
2. **Phase 2 — authored flowcharts:** an expert-authored diagnostic flowchart bundle.  
3. **Phase 3 — flowchart corpus:** a documented flowchart corpus.

### 4.1 Results

The Phase-1 skill-knowledge strategy produced this confusion matrix over the 244 cases:

| Outcome | Count |
| :---- | :---- |
| Correct | 158 |
| Partial | 38 |
| **Wrong** | **0** |
| Unverifiable (autoclose / no ground truth) | 48 |

From which the headline metrics follow (partial predictions are half-credited):

| Metric | Value | Definition |
| :---- | :---- | :---- |
| Raw accuracy | **72.5%** | Credit over all 244 cases: (158 \+ ½·38) / 244 |
| Accuracy-on-gradable | **90.3%** | Credit over the 196 gradable cases (excluding 48 unverifiable): (158 \+ ½·38) / 196 |
| Defensibility | **100%** | Zero **Wrong** predictions across all gradable cases |

The **zero-Wrong** result is the more important number. It means that on a 244-case blind panel, the optimized skill-knowledge strategy never confidently asserted a root cause that was actually incorrect; its errors were failures to fully resolve (Partial) or cases with no gradable ground truth (Unverifiable), not confidently wrong diagnoses. For a system whose output a human will act on, "never confidently wrong" is a more important property than raw accuracy.

Two caveats keep the numbers honest. First, treated as a binomial proportion — an approximation, since partial predictions are half-credited — the 95% confidence interval on the 90.3% accuracy-on-gradable (n \= 196\) is roughly **86–94%**. Second, no naive baseline (for example, a most-common-root-cause prior or an un-optimized zero-shot call) was run on this panel, so these figures should be read as absolute performance, not as a measured lift over a baseline; establishing that baseline is named future work.

### 4.2 The strategy-comparison finding

The skill-knowledge strategy did not merely score well; it **outperformed** both alternatives. Combining all three methodologies into a best-of-three ensemble lifted accuracy from 72.5% to only **74.0%** — a gain of about 1.5 percentage points. Optimized skill knowledge alone therefore accounted for nearly all of the accuracy the three strategies reached together. (We report the headline per-strategy comparison and the ensemble lift; the full per-strategy confusion matrices live in the source file cited in Appendix B.)

This is the empirical case against the flowchart-first and ensemble-first instincts: the expert-authored flowchart artifacts, which are expensive to produce and maintain, added only 1.5 points on top of well-engineered skill knowledge. The leverage was in *optimizing the knowledge*, not in *adding more decision structure on top of it*.

### 4.3 What the evidence does and does not establish

It establishes that an optimized, broad skill-knowledge base, queried under blind conditions, predicts MongoDB/Atlas root causes at 90.3% accuracy-on-gradable with zero confidently-wrong calls — and that this beats authored flowcharts. It does **not**, by itself, measure the contribution of the writing or psychology skillsets, which act on reply quality and human trust calibration rather than on the root-cause prediction the panel scores. Those axes need their own instruments (reply-quality review, trust-calibration and CSAT measurement); building them is named future work, not a claim made here. The result also rests on a single 244-case blind panel: its case-type distribution and how representative it is of the broader MongoDB/Atlas caseload are not characterized here, so generalization beyond this panel is not yet established.

---

## 5\. Implementation considerations

A team reproducing this architecture should weigh six points drawn from how it was built.

**Engineer expertise; do not just prompt it.** The single highest-leverage decision was treating each skill as an artifact with a severity-gated quality bar and a convergence loop, rather than as a prompt to hand-tune. Budget for the optimization layer explicitly — it is where the accuracy came from.

**Use one convergence model across artifact types.** Prompts, code, prose, and skills are optimized by the same loop over one shared severity-and-convergence reference. A single model keeps "done" meaning the same thing everywhere and makes the bounded iteration caps and exit conditions auditable. Reinventing a loop per artifact type reintroduces the inconsistency the model exists to remove.

**Make the optimizer prove convergence to a blind auditor.** The blind re-audit gate — a fresh-context reviewer with no access to the fix history — is what separates real convergence from an optimizer flattering its own work. Without it, "no findings remain" is unfalsifiable.

**Measure on a blind panel, and keep the predictor out of the grader's seat.** The 72.5%/90.3%/100% numbers are credible only because the predictor saw what the customer saw and nothing more, and was never its own grader. Any evaluation that relaxes either condition will report a higher, dishonest number. Protect those two invariants above all.

**Prefer optimized knowledge to added decision structure.** The backtest's strategy comparison says the marginal authored flowchart buys little once skill knowledge is well-engineered. Spend the next unit of effort closing a knowledge gap (Stage 1\) or fixing an optimization finding (Stage 2), not authoring another flowchart.

**Separate the accuracy axis from the delivery axis — and instrument both.** Diagnostic accuracy and resolution quality are different things measured by different instruments. The backtest covers the first; trust-repair, reactance, and calibrated-reliance outcomes need their own measurement before any claim is made about them.

### Deliberately out of scope / future work

- **Direct measurement of the psychology and writing contributions** to resolution quality and customer trust — not yet instrumented.  
- **Live-traffic A/B evaluation** of pipeline-resolved vs. human-only cases — the backtest is offline.  
- **Cost and latency optimization** of the runtime composition — addressed separately in the dashboard's caching-and-optimization architecture, not here.

---

## 6\. Conclusion

The most useful finding is the strategy comparison, not the headline accuracy: on a 244-case blind panel, optimized skill knowledge **outperformed both flowchart strategies and made zero confidently-wrong calls**, and adding the flowcharts on top lifted accuracy by only 1.5 points. Exceptional predictive performance in case resolution did not come from a bigger model, a cleverer prompt, or more decision diagrams. It came from treating expertise as an engineered artifact — acquired deliberately, optimized to a severity-gated bar by one shared convergence loop, composed in a runtime orchestrator, and validated by a blind backtest whose errors feed the next cycle.

What the evidence directly validates is the diagnostic core: MongoDB domain authority and troubleshooting methodology. The writing and psychology skillsets address a different axis — whether the delivered reply repairs trust and lets a human calibrate reliance on the AI's hypothesis — and that axis needs its own measurement, which is named future work. The transferable thesis is narrow and testable: **integrate complementary skillsets, drive each through one iterative multi-stage optimization loop, and prove the diagnostic result on a blind panel you cannot game.** The 90.3% accuracy-on-gradable with 100% defensibility is the evidence that the diagnostic thesis holds for MongoDB case resolution.

---

## Appendix A — Skill inventory

The five skillsets and the optimization machinery are summarized below and catalogued in full, with per-skill descriptions and case-resolution roles, in the companion document `docs/skill-catalog-case-resolution-domains-and-machinery.md` (co-located in this repository). That catalog is the basis for this whitepaper; this paper is the argument the catalog supports.

| Family | Lead skills | Role in resolution |
| :---- | :---- | :---- |
| MongoDB domain authority | `mongodb-expert`, `mongodb-atlas-expert`, `mongodb-operations-expert`, `atlas-diagnostics-expert`, `mongodb-kb`, `mongodb-docset-lookup`; compiled into the 66-part `uber-mongodb-skill` behind `uber-mongodb-diagnostician` | Generates and ranks cited root-cause hypotheses — the diagnostic engine measured by the backtest |
| Troubleshooting / diagnostic reasoning | `atlas-diagnostics-expert`, `software-engineering-patterns`, `teaching-troubleshooting-diagnostic-reasoning`, `10gen` | Chooses the diagnostic surface and gathers evidence |
| Writing | `technical-writing-craft`, `content-and-marketing-writing`, `document-critique`/`ddo`, `kill-the-AI-ism` | Turns cited analysis into a customer reply and internal readout |
| Applied psychology | `applied-psychology` hub, `customer-comms-psychologist` agent | Trust repair, reactance avoidance, calibrated human reliance on AI output |
| Expertise engineering | `cognitive-task-analysis`, `assessment-certification-design`, `skill-creator`/`skill-optimizer`, `concept-family-explorer`, `prompt-deep-optimizer`, `code-deep-optimizer`, `eval-driven-development` | Captures, measures, builds, and tunes the other four families |
| Pipeline machinery | shared `convergence-and-severity` model; the deep-optimizer family; `diagnosis-methodology-backtest`; `solve-case` | Acquire → optimize → compose → evaluate → feed back |

## Appendix B — Methodology and sources

**Backtest design (`diagnosis-methodology-backtest`).** Blind, parallel, multi-agent comparison of competing diagnosis methodologies against ground-truth resolutions. Invariants: (1) each methodology sees only the customer's first report, never the resolution; (2) the predictor is never the grader; (3) each methodology runs in an isolated subagent, all dispatched together. Outcomes are scored Correct / Partial / Wrong / Unverifiable; partials are half-credited in the accuracy metrics.

**Panel.** `okta-blind-244-v1`: 244 real cases; 196 gradable, 48 unverifiable (autoclose or no ground truth). Closed-fallback resolutions are explicitly *not* treated as ground truth.

**Headline figures, as recorded.** Phase-1 skill-knowledge strategy: 158 Correct, 38 Partial, 0 Wrong, 48 Unverifiable (partials half-credited) → 72.5% raw, 90.3% accuracy-on-gradable, 100% defensibility. Best-of-three ensemble: 74.0% — a 1.5-point lift over Phase-1 alone. Approximate 95% CI on accuracy-on-gradable (binomial normal approximation, n \= 196): \~86–94%.

**Source of truth.** Internal repository `tse-strategy-backtest-scoreboard` — file `evaluations/hybrid-scoring-analysis-n244.md` (full confusion matrix and per-strategy comparison). The diagnostic reference under test is the 66-part `uber-mongodb-skill` (`knowledge/uber-mongodb-skill.md` in the same repository), surfaced at runtime by the read-only `uber-mongodb-diagnostician` agent. These artifacts are internal; readers without repository access should request it from the mdb-tam team to reproduce the figures.

**Optimization machinery.** Shared convergence-and-severity reference: `~/.claude/skill-consolidation/convergence-and-severity.md` (severity ladder; seven exit conditions; iteration caps; blind re-audit gate). Deep-optimizer pass counts: `prompt-deep-optimizer` (16 passes / 5 bundles), `code-deep-optimizer` (16 passes), `design-deep-optimizer` (11 passes), `document-critique` (passes 0–14).

**Runtime orchestration.** `solve-case` (seven phases, intake → wrap-up). Customer-communication safeguard: `customer-comms-psychologist` agent over the `applied-psychology` hub (Mayer ABI trust model; automation-bias / algorithm-aversion / calibrated-reliance for human-AI interaction).

---

*This whitepaper documents the system as implemented and measured as of June 2026\. All quantitative claims are traceable to the source files cited in Appendix B; consult those files for the authoritative figures.*