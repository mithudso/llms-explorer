# Skill Catalog — Domain Authority and Optimization Machinery for Case Resolution

**Scope note.** This catalog explains the skills across five families — **MongoDB, psychology, writing, troubleshooting, and expertise** — that together support automated and human-assisted MongoDB/Atlas case resolution. Per the agreed scope, "expertise" is covered in **both senses**: the domain-authority skills (the deep `*-expert` hubs) *and* the expertise-engineering machinery that captures, teaches, measures, and optimizes expertise. A final section explains the optimization-pipeline machinery that connects them, because that machinery is the subject of the companion whitepaper.

**How to read this.** The skill tree is organized hub-and-spoke: a **hub** skill routes to on-demand **reference files** (spokes). When an entry says "hub," it is the routing entry point; its spokes load only when a task matches. Skill names in `code font` are the exact identifiers.

---

## 1\. MongoDB & Atlas — domain authority

These are the knowledge bases an answer is built from. They are split by *plane* (data vs. platform vs. operations) and by *mode* (distilled guidance vs. live diagnostics vs. raw lookup), so a task loads only the surface it needs.

| Skill | What it is | Case-resolution role |
| :---- | :---- | :---- |
| `mongodb-expert` | Primary **data-plane and engine** hub (24 references): CRUD/MQL, aggregation pipelines and deep stages, index design, query optimization and explain plans, schema design, transactions, change streams, time-series, geospatial, BSON, error codes, driver internals (CMAP/SDAM/retryable writes), WiredTiger internals, sharding, replication. | First stop for any query/index/schema/engine question; the deepest single body of MongoDB knowledge. |
| `mongodb-atlas-expert` | Broad **Atlas platform** hub (27 references): control plane, Admin API v2, Atlas CLI, Terraform, Kubernetes Operator, tiers/limits, security and private networking, alerts/metrics, plus sub-areas (Atlas Search, Vector Search, Stream Processing, Charts, Triggers, Online Archive, Federated Auth, cloud networking/PrivateLink). | Anything about the managed platform's configuration, surface choice, or security posture. |
| `mongodb-operations-expert` | **Operations and reliability** hub (18 references): backup/restore and PITR, DR and RTO/RPO, Ops/Cloud Manager, upgrade paths and FCV, migration patterns (`mongosync`, Relational Migrator), CDC, security architecture, encryption (CSFLE/Queryable Encryption), compliance, cost optimization, Kafka/Spark connectors. | Reliability, data-movement, security-architecture, and cost questions — the "keep it running and safe" plane. |
| `atlas-diagnostics-expert` | **Live diagnostics, performance, monitoring, and capacity** hub: `ts-diag`, FTDC/log tooling, Performance Advisor, Atlas alert conditions, benchmarking (YCSB), observability (Prometheus/Datadog/Grafana), capacity planning. Also owns the `@mdb-tam/atlas-diagnostics` Chrome-extension package. | The triage surface — chosen first when a *live* case has a performance or health symptom. |
| `mongodb-kb` | Index of \~2,717 **Knowledge Base articles**: error-code lookup, symptom→article matching, shareable `support.mongodb.com` URLs (Public only — never Internal). | Matches reported symptoms to a known issue and yields a citeable, customer-shareable reference. |
| `mongodb-docset-lookup` | **Offline MongoDB Manual** lookup via a version-pinned Dash docset (3,555 pages; 6,159 indexed entries). | Grounds a generated claim in exact, authoritative Manual text — the fact-check substrate. |
| `mongodb-university-certification` | MongoDB University platform, certifications, and enablement learning paths. | Used when the resolution is enablement (build the customer's competence), not a code fix. |
| `10gen` | **10gen GitHub repo intelligence**: repo prioritization, symptom→repo mapping, install/run guidance, the diagnostic-tool catalog (FTDC, explain plans, Jira enrichment). | Maps a diagnostic scenario to the right internal tool or repo. |
| `solve-case` | **End-to-end case solver** that orchestrates the skills above plus the case/account MCPs and the diagnostic and psychology agents: identify customer → troubleshoot/diagnose → cited analysis → psychology-informed reply \+ blockers/tools/escalation. | The runtime that turns intake into a drafted, defensible customer reply. |
| `uber-mongodb-diagnostician` *(agent)* | Deep multi-subdomain diagnostic reasoning backed by the **66-part `uber-mongodb-skill`** monolithic reference (compiled from the family of `mongodb-*` specialist skills). Read-only; emits a rank-ordered root-cause hypothesis with diagnostic evidence to collect, remediation, confidence ratings, and citations to the exact Part(s) grounding each claim. | The productized form of the highest-scoring backtest strategy (see §6 and the whitepaper). |

---

## 2\. Psychology — human factors

A correct diagnosis still fails if the *delivery* triggers resistance, or if a human over- or under-trusts the AI's output. These skills cover the human side of resolution.

| Skill | What it is | Case-resolution role |
| :---- | :---- | :---- |
| `applied-psychology` *(hub)* | Operator-facing applied-psychology hub, 10 evidence-based, replication-honest references: **behavior change & adoption** (Self-Determination Theory, Fogg B=MAP, habits); **decision-making** (biases, prospect theory, nudge, System 1/2); **persuasion** (ELM, dissonance, **reactance**, inoculation); **trust, rapport & psychological safety** (**Mayer ABI**, Trust Equation, Edmondson); **human-AI interaction** (**automation bias, algorithm aversion/appreciation, calibrated reliance**); **learning & expertise** (cognitive load, retrieval practice, spacing, deliberate practice); **emotion & affect** (emotion regulation, EI); **performance & resilience** (growth mindset, grit, flow, self-efficacy, burnout); **personality** (Big Five, HEXACO, Dark Triad); **moral psychology**. | The two most case-relevant spokes: *human-AI interaction* (so a TAM calibrates trust in an AI hypothesis rather than blindly accepting or rejecting it) and *trust/persuasion* (so a reply repairs trust and avoids reactance). |
| `customer-comms-psychologist` *(agent)* | Drafts a customer-facing communication **and** pressure-tests it against behavioral science before a human sends it. Four jobs: post-incident trust-repair, stalled-adoption nudges, renewal/expansion framing, enablement. Routes through `applied-psychology`, then `document-critique` and `kill-the-AI-ism`. | Converts a technical resolution into a psychologically sound message; the TAM owns final send. |
| `psychology-of-charitable-giving`, `fundraising-and-donor-psychology`, `volunteer-and-prosocial-motivation`, `health-behavior-change-and-donor-registration`, `social-marketing-and-cbsm`, `effective-altruism-and-philanthropic-decision` | The **nonprofit/prosocial spokes** of the psychology family — donor motivation, behavior-change campaigns, volunteer motivation, effective-giving decision-making. | Out of scope for support cases; included for completeness of the psychology family. The transferable cores (behavior change, framing) live in `applied-psychology`. |

---

## 3\. Writing — communication and synthesis

A resolution is only as good as the artifact that carries it. This family covers drafting, and — critically for the pipeline — the **critique loops** that bring an artifact to publication quality.

| Skill | What it is | Case-resolution role |
| :---- | :---- | :---- |
| `writing-expert` *(hub)* | General prose craft, voice, style, and editing (18 sub-skills): sentence/paragraph craft; frameworks (BLUF, Minto Pyramid, SCQA, STAR, Inverted Pyramid); tone by audience; data storytelling; plain/inclusive language. | The base layer of voice and clarity for every written output. |
| `technical-writing-craft` *(hub)* | Technical and product writing: API docs, READMEs, how-tos, KB articles, RFCs/design docs, **runbooks**, **postmortems**, **incident/status-page comms**, changelogs, error messages. Style-guide grounded (Google, Microsoft WSG). | The genre conventions for the operational artifacts a case produces. |
| `executive-comms` *(hub)* | Leadership and persuasion artifacts: BLUF, board memos, decision memos, status updates, decks, **whitepapers**, **case studies**, OKRs, proposals. | Turns a resolution into an exec-ready readout or escalation. |
| `content-and-marketing-writing` *(hub)* | External communications, including **customer-support and TAM ticket replies and escalation handoffs**, NPS/CSAT/review-response writing at scale. | The genre home for the customer-facing reply itself. |
| `career-and-formal-writing` *(hub)* | Career, academic, legal, and policy/governance writing; survey-question design. | Rarely on the case path; here for family completeness. |
| `kill-the-AI-ism` | Diagnostic skill that detects and replaces generator artifacts ("AI-isms") across four pattern categories, producing a findings report with human-voice replacements and an H1–H7 heuristic score. | The voice gate — strips machine tells before a reply reaches a customer. |
| `document-critique` | **Multipass document review agent** (passes 0–14 plus sub-passes) with a convergence loop until no medium-or-higher findings remain; includes authoritative verification and an adversarial/hallucination guard. | The general-purpose document optimization loop; one instance of the shared machinery in §6. |
| `ddo` *(Document Deep Optimizer)* | The apply-in-place driver over `document-critique`: runs the multipass critique and **applies every medium-or-higher fix**, looping to convergence (max 3 iterations). Fast paths: `--voice-only`, `--read-only`, `--annotate`. | One command to take a draft to convergence. |
| `draft-review-revise-loop` | Meta-skill defining the explicit three-pass workflow (draft → review → revise) with hard/soft stop conditions to prevent infinite-polish loops. | The discipline that decides *when to stop* optimizing. |

---

## 4\. Troubleshooting — diagnostic reasoning

Domain knowledge tells you *what is true*; diagnostic reasoning tells you *how to find the fault*. This family covers both the live act and the pedagogy and evaluation of fault-finding.

| Skill | What it is | Case-resolution role |
| :---- | :---- | :---- |
| `atlas-diagnostics-expert` *(cross-listed from §1)* | Live MongoDB/Atlas diagnostics, performance, monitoring, and capacity. | The hands-on fault-finding surface for live cases. |
| `software-engineering-patterns` *(hub)* | Language-agnostic engineering practice, including **debugging and root-cause analysis (5 Whys)**, code review (OWASP checklist), performance profiling, and **automated program repair** (fault localization, patch generation). | The general RCA discipline behind code-level case resolution. |
| `teaching-troubleshooting-diagnostic-reasoning` | The **pedagogy** of fault-finding: cognitive apprenticeship, productive failure (Kapur), mental-model instruction, the novice→expert trajectory, **illness scripts**, dual-process theory, **key-feature assessment**, game-day/fire-drill as pedagogy. | Designs how humans (and, by analogy, agents) are trained to diagnose novel faults; the source of the "illness script" framing used in diagnosis. |
| `10gen` *(cross-listed from §1)* | The diagnostic-tool catalog and symptom→repo mapping. | Points the diagnosis at the right instrument. |
| `mongodb-kb` *(cross-listed from §1)* | Symptom→article matching and error-code lookup. | The fast path from a symptom to a known root cause. |
| `diagnosis-methodology-backtest` | Runs a **blind, parallel, multi-agent backtest** comparing competing diagnosis methodologies against ground-truth resolutions, scoring which predicts root causes most accurately. A methodology sees only what the customer first reported — never the resolution; the predictor is never the grader; each methodology runs in its own isolated subagent. | The evaluation harness that proved the skill-knowledge strategy's accuracy (§6). |

---

## 5\. Expertise — both layers

Per scope, "expertise" spans two layers: **(5a)** the domain authorities that *hold* expertise, and **(5b)** the expertise-engineering skills that *build, teach, measure, and tune* it.

### 5a. Domain authorities (the experts)

The `*-expert` hubs and `uber-mongodb-diagnostician` from §1, plus the diagnostic-reasoning skills from §4. These are "expertise" in the everyday sense: the skills that know the most about a domain. They are the *inputs* the pipeline optimizes and composes.

### 5b. Expertise engineering (capture → teach → measure → optimize)

This layer is what makes the domain authorities *good* and keeps them good. It is the part most people miss, and it is where the pipeline's leverage comes from.

**Capture — elicit expert knowledge**

| Skill | What it is |
| :---- | :---- |
| `cognitive-task-analysis` | Front-end knowledge-elicitation methodology (CDM, ACTA, PARI, GDTA, think-aloud, concept mapping) that surfaces the tacit decision steps experts omit — addressing the "expert blind spot" (experts leave out \~70% of their decision steps unprompted). The feedstock for any skill or training that encodes diagnostic expertise. |

**Teach — encode expertise into instruction**

| Skill | What it is |
| :---- | :---- |
| `technical-instruction` *(hub)* | Family hub routing to the instruction spokes below. |
| `instructional-design-course-architecture` | Course/curriculum design (ADDIE, SAM, Dick & Carey, backward design, Gagné, Merrill); learning objectives and constructive alignment. |
| `technical-training-delivery` | Hands-on labs, live coding, developer/customer academies, faded examples. |
| `teaching-troubleshooting-diagnostic-reasoning` *(cross-listed from §4)* | The pedagogy of diagnostic reasoning specifically. |
| `genai-education-instructional-design` | GenAI applied to education — AI tutors/ITS, AI-assisted instructional design, AI-resistant assessment. |
| `human-performance-technology` | Diagnoses whether training is even the right intervention (ISPI HPT, Gilbert's BEM, Mager-Pipe) before anyone builds a course — the "is this a skill gap or an environment gap" filter. |

**Measure — quantify expertise and learning**

| Skill | What it is |
| :---- | :---- |
| `assessment-certification-design` | Certification/exam design and psychometrics (item writing, cut scores via Angoff/Bookmark, CTT/IRT, reliability/validity, DIF). The rigor layer for measuring competence. |
| `learning-measurement-evaluation` | Training effectiveness (Kirkpatrick four levels, Phillips ROI Level 5, xAPI/SCORM, transfer climate). |
| `skills-taxonomies-cbe` | Skills taxonomies and competency frameworks (O\*NET, ESCO, SFIA, KSAOs) and Competency-Based Education — the substrate competence is certified against. |

**Optimize — build and tune the skills, prompts, and code themselves (the meta layer)**

| Skill | What it is |
| :---- | :---- |
| `concept-family-explorer` | Gap-discovery layer *above* deep research: maps a subject's full conceptual family, surfaces what you're missing, scores each gap, then loops `/dr` on every viable gap until the concept tree saturates. The skill-*acquisition* engine. |
| `skill-creator` | Creates new skills from scratch and measures skill performance via evals. |
| `skill-optimizer` | Audits and improves a skill to production quality via a convergence-loop quality gate, then syncs it to the context hub. |
| `skill-tree-architect` | Whole-tree architect — audits the hub-and-spoke taxonomy against description caps and hub balance and rebalances it. |
| `prompt-deep-optimizer` | Iteratively optimizes production prompts: a **16-pass audit in 5 parallel bundles**, applies every Medium+ fix, loops to convergence; recommends a training-data optimization algorithm (APE/OPRO/MIPROv2/GEPA/…). |
| `prompt-helper-optimizer` *(`/ph`, `/phe`)* | One-off/exploratory prompt improvement — interpret, critique, rewrite, and (in `/phe`) save and run. |
| `prompt-engineering` | The reference body — foundational and advanced prompting techniques, structured output, injection defense, evaluation. |
| `code-deep-optimizer` | Multi-stage review-and-fix optimizer for source files/repos: **16-pass audit**, applies Medium+ fixes in place, verifies via build/lint/tests, loops to convergence. |
| `eval-driven-development` | The build-time discipline of evaluating LLM/agent apps: the analyze→measure→improve loop with **error analysis as the engine**, the Three Gulfs (Specification/Generalization/Comprehension), and LLM-as-judge calibration (Cohen's kappa, Krippendorff's alpha). |

---

## 6\. The optimization-pipeline machinery (connective tissue)

The skills above are *components*. What turns a pile of components into a system with measurable predictive accuracy is a small set of shared mechanisms. These are the subject of the companion whitepaper; they are catalogued here because they are themselves skills/artifacts.

**The shared convergence-and-severity model** (`~/.claude/skill-consolidation/convergence-and-severity.md`). One canonical reference defines a **severity ladder** (Blocking/Critical → Major → Medium → Minor → Nit; fix everything Medium-and-above), **7 convergence exit conditions** (clean / no-progress / content-cycling / stable-rewrite / loop-instability / iteration-cap / budget), **iteration caps** (prompts 5; skills and documents 3, raised to 5 if Medium+ findings dropped ≥50%), and a **blind re-audit gate** (a fresh-context subagent that re-audits the final artifact with no access to the findings history before "clean" can be declared). Every optimizer below is an instance of this one loop.

**The deep-optimizer family** — the same loop applied to different artifact types:

- `prompt-deep-optimizer` — prompts (16 passes, 5 parallel bundles)  
- `code-deep-optimizer` — source code (16 passes; build/lint/test verification)  
- `document-critique` / `ddo` — prose (passes 0–14)  
- `design-deep-optimizer` — UI/visual designs (11 passes)  
- `skill-optimizer` — skills themselves

**The acquisition and evaluation ends:**

- `concept-family-explorer` — finds and fills knowledge gaps until a concept family saturates (front of the pipeline)  
- `diagnosis-methodology-backtest` — blind, parallel, multi-agent evaluation against ground truth (back of the pipeline)  
- `eval-driven-development` — the error-analysis discipline that the backtest operationalizes  
- `solve-case` — the runtime orchestrator that composes the optimized components on a live case

### The evidence this machinery produces

On the **okta-blind-244-v1** blind panel (244 real cases; predictor blind to the resolution; predictor ≠ grader), the **Phase-1 "skill-knowledge" strategy** — optimized `mongodb-*` skill expertise, the input the pipeline produces — scored:

| Metric | Value | Meaning |
| :---- | :---- | :---- |
| Raw accuracy | **72.5%** | Correct over all 244 cases (partials half-credited) |
| Accuracy-on-gradable | **90.3%** | Correct over the 196 gradable cases (48 were unverifiable autocloses) |
| Defensibility | **100%** | Zero **Wrong** predictions across all gradable cases |

Confusion matrix: **158 Correct, 38 Partial, 0 Wrong, 48 Unverifiable**. The skill-knowledge strategy beat both an authored-flowchart bundle and a documented-flowchart corpus; combining all three (Best-of-3) added only **7** correct cases (74.0% vs. 72.5%), so optimized skill knowledge alone captured \~95% of the achievable accuracy.

*Source:* `~/Documents/GitHub/tse-strategy-backtest-scoreboard/evaluations/hybrid-scoring-analysis-n244.md`.

---

## 7\. How the families compose for case resolution

A live case flows through the families in order:

1. **Troubleshooting** chooses the diagnostic surface and gathers evidence (`atlas-diagnostics-expert`, `10gen`, `software-engineering-patterns`).  
2. **MongoDB domain authority** generates and ranks root-cause hypotheses with citations (`uber-mongodb-diagnostician` over the 66-part reference; `mongodb-kb` and `mongodb-docset-lookup` for grounding).  
3. **Writing** turns the cited analysis into a customer reply and an internal readout (`content-and-marketing-writing`, `technical-writing-craft`, `document-critique`/`ddo`, `kill-the-AI-ism`).  
4. **Psychology** ensures the reply repairs trust and avoids reactance, and that humans calibrate their reliance on the AI hypothesis (`applied-psychology`, `customer-comms-psychologist`).  
5. **Expertise engineering** runs underneath all of it: `concept-family-explorer` finds missing knowledge, the deep-optimizers tune every skill/prompt/document to production quality, and `diagnosis-methodology-backtest` measures whether the whole stack actually predicts root causes — feeding errors back into the next optimization cycle.

`solve-case` is the orchestrator that runs steps 1–4 on a single case; the expertise-engineering layer (step 5\) is the offline loop that makes steps 1–4 progressively better. The companion whitepaper argues that this composition — five complementary skillsets, each driven to convergence by one shared optimization loop and validated by one blind backtest — is what produces the measured accuracy above.