---
title: "Instructional Design & Course Architecture"
description: "The discipline of designing multi-lesson courses and curricula: the layer between learning science (mechanisms of how people learn) and single-tutorial craft (how to write one how-to guide). This skil"
---

# Instructional Design & Course Architecture

The discipline of designing multi-lesson courses and curricula: the layer between learning science (mechanisms of how people learn) and single-tutorial craft (how to write one how-to guide). This skill covers process models, curriculum architecture tools, objective-writing frameworks, and course-format decisions for technical and engineering training contexts.

**Boundary contracts:**
- Learning science mechanisms (cognitive load, retrieval practice, spacing, deliberate practice) → **applied-psychology**
- Tutorial / how-to / reference writing craft → **technical-writing-craft**
- Certification exam design and psychometrics → **assessment-certification-design**
- Training delivery craft, facilitation, live lab instruction → **technical-training-delivery**
- Program evaluation, ROI, Kirkpatrick → not yet a separate skill; out of scope here
- Teaching troubleshooting as a pedagogy → **teaching-troubleshooting-diagnostic-reasoning**

**Typical invocation outputs:** when asked to design a course from scratch, produce a course design document (TO/EO hierarchy, scope-and-sequence, format decision, prerequisite map). When asked to audit an existing course, produce an alignment audit table (ILO verb | TLA description | AT type | match Y/N) plus a findings list. When asked for a lesson plan, produce a Gagné event map for the module. Format adapts to the scope of the request; ask for clarification only when the target audience and learning objective are both absent.

---

## Contents

1. [Process Models: ADDIE, SAM, Dick & Carey](#1-process-models-addie-sam-dick--carey)
2. [Backward Design / Understanding by Design](#2-backward-design--understanding-by-design)
3. [Curriculum Architecture: Scope, Sequence, Prerequisite Mapping](#3-curriculum-architecture-scope-sequence-prerequisite-mapping)
4. [Chunking and Sequencing Technical Content](#4-chunking-and-sequencing-technical-content)
5. [Writing Learning Objectives as a Design Tool](#5-writing-learning-objectives-as-a-design-tool)
6. [Bloom's Taxonomy as a Design Tool](#6-blooms-taxonomy-as-a-design-tool)
7. [Terminal vs. Enabling Objective Hierarchies](#7-terminal-vs-enabling-objective-hierarchies)
8. [Constructive Alignment: ILOs → TLAs → ATs](#8-constructive-alignment-ilos--tlas--ats)
9. [Gagné's Nine Events of Instruction](#9-gagns-nine-events-of-instruction)
10. [Merrill's First Principles and the Pebble-in-the-Pond Model](#10-merrills-first-principles-and-the-pebble-in-the-pond-model)
11. [Course Format Decisions: Self-Paced vs. Cohort vs. Blended](#11-course-format-decisions-self-paced-vs-cohort-vs-blended)
12. [Anti-Patterns](#12-anti-patterns)
13. [Quick Reference](#13-quick-reference)

Full source citations: `references/instructional-design-course-architecture.md` (28 sources).

---

## 1. Process Models: ADDIE, SAM, Dick & Carey

Three process models dominate instructional design practice. They differ on sequencing, iteration, documentation, and stakeholder involvement — not on underlying learning science. Choose based on content stability, timeline, documentation requirements, and team structure.

### ADDIE

ADDIE (Analysis–Design–Development–Implementation–Evaluation) originated in 1975 at Florida State University under U.S. Army contract. It functions as a **meta-framework** describing what must happen in any instructional design project without prescribing how to do it. Most other models are recognizable as ADDIE variants.

**Five phases:**
- **Analysis** — identify the instructional problem, learner characteristics, existing skill gaps, delivery constraints
- **Design** — map learning objectives to assessment strategies; select instructional approach
- **Development** — create content assets (modules, simulations, facilitator guides); pilot test
- **Implementation** — deliver instruction; train facilitators
- **Evaluation** — formative (ongoing quality checks within phases) + summative (outcome assessment post-delivery)

The "ADDIE is a waterfall" characterization is partially a myth: the model never prohibited iteration or mid-phase revision; that rigidity was an implementation choice, not a structural constraint. Contemporary ADDIE explicitly accommodates rapid prototyping as formative feedback within phases.

**Best fit for technical/engineering training:** compliance-mandated curricula, safety certification, regulatory onboarding, content with a long shelf-life, contexts requiring documentation trails.
**Weakest fit:** fast-changing technical content (new platform releases, agile workflows); tight timelines.

---

### SAM (Successive Approximation Model)

Introduced by Michael Allen (Allen Interactions) in *Leaving ADDIE for SAM* (Allen & Sites, ASTD Press, 2012), explicitly as a response to waterfall-ADDIE dynamics. Draws from agile software development, prioritizing rapid prototyping and continuous stakeholder feedback over upfront planning.

**Two tiers:**
- **SAM1** (smaller projects): Preparation (rapid info gathering + "Savvy Start" brainstorm) → Iterative Design (rapid prototyping + stakeholder review) → Iterative Development (alpha/beta/gold with embedded testing)
- **SAM2** (larger projects): same core with added project management scaffolding

**Core differentiator:** produce something usable at every stage so stakeholders interact with real artifacts, not abstract specs.

**Best fit:** evolving technical content; eLearning for new tooling; agile development contexts; tight timelines.
**Weakest fit:** certification-track programs requiring audit trails, regulatory compliance documentation, or large-scale replicability.

---

### Dick & Carey Systems Model

Published by Walter Dick and Lou Carey in *The Systematic Design of Instruction* (1978). A fully elaborated ten-component procedural model grounded in systems theory: instructor, learners, materials, delivery, activities, and environment are treated as interdependent components of a coherent system.

**Ten components (abbreviated):** Identify instructional goals → conduct instructional analysis → analyze learners and contexts → write performance objectives → develop assessment instruments → develop instructional strategy → develop/select materials → design and conduct formative evaluation (1:1, small group, field trial) → revise instruction → design summative evaluation.

Components 1–9 are explicitly iterative and parallel; formative evaluation feeds back into earlier steps continuously.

**Best fit:** complex competency-based programs; technical certification requiring rigorous performance-objective alignment; blended learning with multiple modalities.
**Weakest fit:** small-scale or time-constrained projects; teams without dedicated instructional design expertise.

---

### Model Selection Decision Table

| Factor | ADDIE | SAM | Dick & Carey |
|---|---|---|---|
| **Content stability** | Stable / long shelf-life | Evolving / fast-changing | Stable with complex prerequisite structure |
| **Timeline** | Medium — phase-gate pacing | Fast — iterative sprints | Slow — extensive upfront analysis |
| **Documentation need** | Medium | Low (emergent) | High (explicit at every step) |
| **Stakeholder involvement** | Phase-gate reviews | Continuous rapid feedback | Analysis + formative eval phases |
| **Team ID expertise** | Any | Any | Requires dedicated ID expertise |
| **Compliance/audit trail** | Yes | No | Yes (most rigorous) |
| **Iteration model** | Optional within phases | Mandatory rapid prototyping | Formative eval at 3 levels |

---

## 2. Backward Design / Understanding by Design

Understanding by Design (UbD) — Wiggins & McTighe (ASCD, 1998) — inverts conventional planning: define what students must ultimately *do* first, then design evidence of that performance, and only then plan instruction.

### Three Stages

**Stage 1 — Desired Results:** Establish specific measurable learning objectives and, deeper, "enduring understandings" (transferable big ideas expressed as declarative sentences, e.g., "Systems have emergent properties their components do not") and "essential questions" (open-ended, recurring, thought-provoking questions that anchor the course). The six **facets of understanding** — explain, interpret, apply, have perspective, empathize, have self-knowledge — inform what evidence of understanding looks like.

**Stage 2 — Acceptable Evidence:** Determine *how* learners will demonstrate understanding before designing any instruction. Distinguishes performance tasks (authentic applications) from other evidence (quizzes, reflections). Sequencing this before Stage 3 prevents "teaching to the activity."

**Stage 3 — Learning Plan:** Design instruction last, in service of Stage 2 evidence requirements. The WHERETO heuristic guides design: **W**here and Why, **H**ook, **E**quip and Explore, **R**ethink and Revise, **E**valuate, **T**ailor, **O**rganize.

**Scaling UbD to curriculum:** the backward design logic applies recursively — program-level transfer goals are established first, then courses are designed to build toward them, then units within courses. McTighe and Wiggins explicitly frame UbD as a "unit-planning process" that scales to full curriculum design.

**Limitations:**
- Requires upfront commitment to fixed objectives, which can crowd out emergent or personalized learning pathways
- Highly dependent on the designer's disciplinary grasp — if you cannot distinguish enduring understandings from topic coverage, the output is misaligned curricula
- Expensive to adopt institutionally — working backward against content-first instincts requires significant professional development

---

## 3. Curriculum Architecture: Scope, Sequence, Prerequisite Mapping

### Scope and Sequence

**Scope** defines breadth and depth of coverage. **Sequence** determines the order of content presentation, ensuring learning is cumulative and builds systematically. A well-designed scope and sequence ensures prerequisite skills appear before courses that require them.

### Prerequisite Mapping as a Directed Graph

A curriculum is a directed acyclic graph (DAG): courses are nodes, prerequisite relationships are directed edges. Three structural roles emerge from this framing:

- **Hub courses** — connect many subsequent topics; single point of failure if poorly taught
- **Bridge courses** — connect otherwise isolated clusters
- **Source courses** — foundational material with no prerequisites but many dependents

Mapping the prerequisite graph explicitly surfaces structural bottlenecks before the curriculum is built. A hub course whose prerequisites are unclear or inconsistently enforced creates cascade failures in all downstream courses.

### Curriculum Mapping

A curriculum map is a visual matrix: courses vs. learning outcomes, marked at Introduction / Reinforcement / Mastery (I/R/M) levels. It verifies that critical competencies are:
- Introduced early in the sequence
- Reinforced across multiple courses
- Demonstrated at mastery level before program completion

Missing or misplaced coverage is visible as matrix gaps.

---

## 4. Chunking and Sequencing Technical Content

**Chunking** groups content into manageable units grounded in working memory limits. Practical guidance: target 1–3 learning objectives per module; end each chunk with a practice activity (knowledge check, scenario, reflection) to facilitate transfer to long-term memory.

**Sequencing approaches for technical content:**

| Approach | When to use |
|---|---|
| Simple → complex | Foundational concepts must be stable before advanced ones |
| Known → unknown | Builds on learners' existing mental models |
| Unknown → known | Surfaces learning gaps through challenge before instruction (productive failure) |
| Dependent relationship | Mandatory prerequisite ordering (data types before data structures) |
| Cause → effect | Causal mechanisms must precede troubleshooting |
| General → specific | Conceptual frame before technical detail |
| Chronological | Process or workflow training with fixed execution sequence |

**Standard pattern for technical/engineering content:** Declarative (what it is) → Procedural (how to do it) → Situated (when and why to apply it).

**Key failure mode:** over-loading declarative knowledge before procedural application — the "front-loaded lecture" where learners process concepts they cannot yet connect to practice.

---

## 5. Writing Learning Objectives as a Design Tool

### The ABCD Format (Mager)

Robert F. Mager's *Preparing Instructional Objectives* (1962) established behavioral objectives as a design tool. The ABCD expansion makes all four design elements explicit:

| Component | Design question | Common error |
|---|---|---|
| **Audience (A)** | Who is the learner? | Writing from instructor's perspective |
| **Behavior (B)** | What observable action does the learner perform? | Internal states: "understand", "know", "appreciate" |
| **Condition (C)** | Under what circumstances? With what tools/constraints? | Omitting conditions entirely |
| **Degree (D)** | How good is good enough? | No criterion for pass/fail |

Each component constrains a downstream decision. Once Condition is fixed ("without reference materials"), instructional practice must mirror that constraint. Once Degree is fixed ("with no more than one error"), the rubric writes itself.

**Well-formed technical example:** *Given access to the Atlas UI and current index configurations [C], database administrators [A] will identify the three indexes most likely causing collection scan warnings [B] by selecting all three correctly from a provided list of ten candidates [D].*

**Conditions opener patterns:** *Given a…* / *Without reference to…* / *Using the standard operating procedure…* / *Given access to the cluster dashboard…*

### When to simplify

Not every objective requires all four components spelled out. Explicitly state Condition when the performance constraint differs from daily work context; explicitly state Degree when a pass/fail line must be drawn for certification or safety-critical outcomes.

---

## 6. Bloom's Taxonomy as a Design Tool

Bloom's Revised Taxonomy (Anderson & Krathwohl, 2001) is, for course designers, a **verb selection and objective leveling tool** — use it when writing learning objectives and sequencing lessons, not as a theory of cognition (that belongs in applied-psychology). The 2001 revision replaced nouns with action verbs, making it directly actionable for objective writing.

**Taxonomy as a dependency chain:** a learner who cannot *remember* configuration syntax cannot *apply* it; one who cannot *analyze* a failure trace cannot *evaluate* whether an architectural change is warranted. This chain is a curriculum pacing heuristic.

**Sequencing rule:** lesson-level verbs must be at or below the course-level verb's Bloom's level — never higher.

**Verb table for technical training:**

| Level | Cognitive demand | General verbs | Technical training verbs |
|---|---|---|---|
| **1 – Remember** | Recall facts, syntax, definitions | Define, list, name, state, identify | Name, list, identify, recite, label |
| **2 – Understand** | Explain, describe, interpret | Describe, explain, summarize, classify | Describe, explain, summarize, interpret |
| **3 – Apply** | Execute, use, demonstrate | Execute, implement, solve, use | Configure, deploy, install, run, write, build (from template) |
| **4 – Analyze** | Break down, compare, root-cause | Compare, differentiate, examine, investigate | Diagnose, debug, trace, compare, profile, map dependencies |
| **5 – Evaluate** | Judge, recommend, justify | Assess, defend, recommend, critique | Justify, recommend, validate, weigh trade-offs, prioritize |
| **6 – Create** | Design, build, formulate | Design, construct, plan, produce | Architect, design (from scratch), formulate, engineer, draft |

**Common design defect:** training assessments test at Remember or Understand when the job demands Apply or Analyze.

**Assessment alignment note:** objective-to-assessment alignment (ILO verb → AT demand) is covered in Section 8 (Constructive Alignment). Psychometrics, item writing, and IRT analysis belong in assessment-certification-design.

---

## 7. Terminal vs. Enabling Objective Hierarchies

**Terminal Objective (TO):** the capstone performance the learner must achieve by module/course end. One TO per module scope is a practical limit (5–9 TOs per full course). TOs describe outcomes, not activities.

**Enabling Objectives (EOs):** prerequisite sub-skills derived by asking recursively: "What must the learner already be able to do to achieve this?" The result is a directed graph of prerequisites — not a flat list.

**Design payoff:** once the hierarchy is drawn, the instructional sequence is largely determined. EOs that are prerequisites for other EOs come first; EOs with no dependents can be taught in any order; the TO is assessed last.

**Derivation method (subordinate skills analysis):** Start with the TO. Ask "What must they know/do to achieve this?" for each answer. Continue recursively. Validate the resulting graph with subject-matter experts.

**Worked example — Atlas slow-query diagnosis:**

```
TO: Given a production Atlas cluster with a 24-hour slow-query log, identify the
    three highest-impact missing indexes (all three correct, without assistance).

EOs (prerequisite chain):
  EO1: Recall the components of an explain plan output (Remember)
  EO2: Describe conditions under which a collection scan occurs (Understand)
  EO3: Interpret IXSCAN vs COLLSCAN in an explain plan (Understand → Apply)
  EO4: Compare candidate index strategies for a given query shape (Analyze)
       └── requires EO1, EO2, EO3
  TO: Identify the three highest-impact missing indexes (Analyze/Evaluate)
       └── requires EO4
```

EO1–EO3 have no dependencies on each other and can be taught in any order. EO4 requires EO1–EO3 before it can be practiced. The TO is assessed only after EO4 is demonstrated.

---

## 8. Constructive Alignment: ILOs → TLAs → ATs

John Biggs' constructive alignment (1996) coordinates three components so they address the same learning agenda:

| Component | Design question | Failure mode |
|---|---|---|
| **ILO** (Intended Learning Outcome) | What must the learner *do* to demonstrate learning? | Vague nouns: "understand", "appreciate" — unassessable |
| **TLA** (Teaching & Learning Activity) | Do learners *practice* the ILO verb during instruction? | Passive lecture where ILO requires complex performance |
| **AT** (Assessment Task) | Does the assessment *require* the ILO verb? | Multiple-choice test for an ILO that requires "design" |

**Design sequence:** ILO first → TLA that practices the ILO verb → AT that measures the same verb under the ILO conditions.

**Backwash mechanism:** learners tend to learn what they believe will be assessed. A misaligned course (objective says *analyze*, assessment tests *recall*) produces learners who study for recall and never practice analysis.

**Alignment audit:** map ILO verbs → TLA activities → AT demands. Mismatches at cognitive demand levels are the primary finding.

**Limitations:** When mandated top-down as a quality-assurance tool, constructive alignment can become a paperwork exercise disconnected from actual learning; it specifies the architecture but offers limited guidance on which specific TLAs to select.

---

## 9. Gagné's Nine Events of Instruction

Robert Gagné's framework pairs nine external instructional events with internal cognitive processes. Operates as both a **lesson design scaffold** and a **lesson audit tool**.

| Event | Internal Process | Design example |
|---|---|---|
| 1. Gain Attention | Reception | Case vignette, provocative statistic, video clip |
| 2. Inform of Objectives | Expectancy | Explicit "By the end you will be able to…" statement |
| 3. Stimulate Recall of Prior Learning | Retrieval from long-term memory | Pre-quiz, discussion of prior experience |
| 4. Present Stimulus | Selective Perception | Worked example, demo, reading |
| 5. Provide Guidance | Semantic Encoding | Analogy, mnemonic, elaborated example, concept map |
| 6. Elicit Performance | Responding | Practice problem, simulation, scenario |
| 7. Provide Feedback | Reinforcement | Corrective comment, rubric, answer key with rationale |
| 8. Assess Performance | Retrieval and response verification | Quiz, assignment, performance task |
| 9. Enhance Retention and Transfer | Generalization | Job aid, varied practice context, peer teaching |

**Three-phase structure:** Preparation (Events 1–3) → Acquisition (Events 4–6) → Transfer (Events 7–9).

**Most commonly skipped — and an anti-pattern when absent:** Event 9 (Retention and Transfer). The framework provides a structural reminder to design for transfer, not just comprehension; skipping it is listed as an explicit anti-pattern in Section 12.

**Sequence guidance:** for short modules, several events can be compressed into a single activity. Events should not be permanently omitted; if an event is absent, the designer should document an explicit reason.

**Key limitation:** the framework does not include a motivation principle; Keller's ARCS model (Attention, Relevance, Confidence, Satisfaction) was developed explicitly to fill this gap.

---

## 10. Merrill's First Principles and the Pebble-in-the-Pond Model

M. David Merrill (2002) synthesized five invariant principles from a review of major ID theories. All five are **simultaneously necessary** — no single principle is sufficient without the others.

| Principle | Core claim | Design action | Missing → |
|---|---|---|---|
| Problem-Centered | Anchor all learning in real tasks | Open with a scenario or task, not a content outline | Learners lack context for why content matters |
| Activation | Prior knowledge is the scaffold | Prompt recall before new content | New knowledge has no framework to attach to |
| Demonstration | Show, don't only tell | Worked examples, cases, simulations | Learners know concepts but can't perform |
| Application | Practice with decreasing coaching | Require problem-solving; fade scaffolding | Knowledge stays inert, doesn't transfer |
| Integration | Connect learning to the learner's world | End with reflection, peer teaching, real-world use | Learning decays or stays context-bound |

**Pebble-in-the-Pond model:** Merrill's practical design process radiates outward from a real-world problem: design problem sequences first, then component skills, then demonstrations and practice, then integration activities, then assessments — in that order. Inverts the conventional outline-first approach.

**Design reorientation:** the first question shifts from "What content must I cover?" to "What real-world problem must learners be able to solve?"

**Limitations:** resource-intensive to implement; presupposes design autonomy to restructure course around problem sequences (not always available in institutional/compliance contexts); less explicit about *how* to select specific activities than *what* principles to honor.

---

## 11. Course Format Decisions: Self-Paced vs. Cohort vs. Blended

Course format is an architectural decision that determines which learning activities are feasible and what learner behaviors the design can depend on. ILT = Instructor-Led Training (synchronous, cohort-based delivery).

| Factor | Self-Paced | Cohort / ILT | Blended |
|---|---|---|---|
| **Content type** | Declarative, codified procedural | Situated, interpersonal, complex judgment | Mixed; modular by content type |
| **Learner distribution** | Highly distributed, async-friendly | Co-located or small groups | Distributed with periodic sync points |
| **Learner motivation** | High self-motivation required | External accountability helps | Sync anchors pacing |
| **Feedback latency** | Delayed (automated checks) | Real-time, adaptive | Both: async for basics, sync for application |
| **Scale economics** | High (fixed cost per learner decreases) | Low (cost scales with learners) | Moderate |
| **Skill stakes** | Low-to-medium | High (error cost is real) | High when sync reserved for high-stakes |
| **Community building** | Low | High | High (sync touchpoints preserve cohort identity) |
| **Completion pressure** | Structural dropout risk | Schedule-enforced | Milestone-anchored |

**Design principle for blended:** use self-paced for declarative knowledge and easily codified procedural knowledge; reserve synchronous for situated knowledge and procedural content requiring real-time instructor correction.

---

## 12. Anti-Patterns

| Anti-pattern | Symptom | Fix |
|---|---|---|
| **Modality-first planning** | "We want a video course" → reverse-engineered objectives | Establish transfer goals first; format follows |
| **Coverage trap** | Course lists all topics; objectives say "understand" | Write TOs first; cut content that serves no TO |
| **Objective verb mismatch** | ILO says "analyze"; assessment is multiple choice | Audit ILO verb → AT alignment; raise assessment demand |
| **Missing conditions** | "Configure a replica set" — which environment, which tools? | Specify tool version, reference materials, environment state |
| **Front-loaded lecture** | All declarative before any procedural application | Apply declarative → procedural → situated sequencing |
| **Skipped Event 9** | Training ends at assessment; no transfer design | Build job aids, varied practice, peer discussion into module exit |
| **Over-centralized prerequisite graph** | One hub course; all downstream content depends on it | Distribute prerequisites; build redundant paths to advanced topics |
| **Constructive misalignment** | Alignment documented on paper; actual activities mismatch verbs | Audit TLA activities against ILO verbs, not just labels |

---

## 13. Quick Reference

**When to use which process model:**
- Stable content, compliance required, documentation trail needed → **ADDIE**
- Fast-changing content, agile context, tight timeline, iterative stakeholder feedback → **SAM**
- Complex competency-based program, rigorous performance-objective alignment, blended learning → **Dick & Carey**

**Typical course design deliverables:**
- **Course design document** — TO/EO hierarchy, scope-and-sequence, format decision, assessment strategy, prerequisite map
- **Module blueprint** — objectives (ABCD), Gagné event mapping, activity type per objective, alignment audit table
- **Alignment audit table** — ILO verb | TLA description | AT type | match? (Y/N)
- **Prerequisite graph** — DAG diagram with hub/bridge/source roles labeled

**Use patterns:**
- *Design from scratch:* start with transfer goals → TO/EO hierarchy → process model selection → scope-and-sequence → module blueprints
- *Audit an existing course:* run the alignment audit table; flag ILO/TLA/AT mismatches; apply Gagné event check per module; compare against Merrill's five principles
- *Single-module design:* write the TO first; derive EOs via subordinate skills analysis; map Gagné events; confirm format matches stakes

**Objective quality checklist:**
- [ ] Written from learner's perspective (not "the lesson will cover")
- [ ] Behavior verb is observable (not vague state verbs)
- [ ] Condition specified when it differs from daily work context
- [ ] Degree stated when a pass/fail line is required
- [ ] Bloom's level matches actual job performance demand

**Alignment audit steps:**
1. List all ILO verbs
2. For each, identify the TLA that practices that verb
3. For each, identify the AT that requires that verb
4. Flag any ILO with no TLA and/or no AT → gap in the design

**Curriculum architecture checklist:**
- [ ] Transfer goals defined at program level before course design begins
- [ ] Prerequisite graph drawn as a DAG; hub courses identified
- [ ] I/R/M levels mapped across courses for each critical competency
- [ ] Chunking targets 1–3 objectives per module
- [ ] Sequencing follows declarative → procedural → situated pattern

Full source citations: `references/instructional-design-course-architecture.md` (28 sources).

## Routing Detail

- Measuring whether the training you designed actually worked (Kirkpatrick levels, Phillips ROI, training transfer, L&D dashboards) → `learning-measurement-evaluation`
