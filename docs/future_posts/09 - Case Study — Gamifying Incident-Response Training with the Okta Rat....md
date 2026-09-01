# Case Study — Gamifying Incident-Response Training with the Okta Rate-Limiting Fire Drill

**Version:** 1.0 · **Date:** 2026-06-17 · **Owner:** TAM Enablement / IR Program · **Audience:** IR program stakeholders, TAM leadership, enablement · **Read time:** ~9 min · **Related:** `docs/firedrill-pitch.md`, `docs/firedrill-moderator-card.md`, `docs/firedrill-ir-card.md`, `docs/firedrill-tam-ic-card.md`, `mcp-server/data/firedrill/scenarios/scenario-4.json`

---

## §0 At a glance

- **Context:** A MongoDB Premium Services incident-response (IR) team preparing for the next real Tier-0 incident, using the in-extension fire-drill simulator.  
- **Challenge:** Readiness could not be proven on paper, and the team's deepest Atlas knowledge sat with a few individuals — a single point of failure under real S1 pressure.  
- **Solution:** A gamified, fully-isolated fire drill (Scenario 4 — *Okta rate limiting / Atlas API throttle*) run under the JIMP role structure and scored on a coordination-weighted rubric.  
- **Result:** The drills repeatedly produced the same lesson — **mutual team support outperformed any single person's expertise — but only because that expertise existed somewhere on the team to be shared.**

**The finding this case study defends:** technical expertise is the *necessary input*; coordinated team support is the *multiplier*. Neither alone resolves a Tier-0 incident well.

---

## §1 The challenge: readiness you cannot prove, and expertise you cannot clone

Before the fire-drill program, IR readiness was asserted, not demonstrated. The team had a Joint Incident Management Plan (JIMP), an escalation matrix, and capable engineers — but no safe way to exercise detection, mobilization, diagnosis, and communications *timing* before a real Tier-0 incident forced the test in production.

Two risks sat underneath that gap.

**The timing risk.** An incident is won or lost in the first fifteen minutes: was severity called correctly, did the right roles get on the bridge, did customer communications start before the customer escalated. None of this was measured.

**The lone-expert risk.** The team's deepest Atlas internals knowledge — rate-limit policy, throttle mechanics, sharding behavior — was concentrated in a few engineers. On paper that looks like strength. Under a real S1 at 3 a.m. with that engineer offline, it is a single point of failure. The open question was not "are our experts good?" (they were) but "can the *team* resolve a Tier-0 incident when any one expert is missing?"

A training course could teach the Atlas knowledge. It could not, by itself, prove the team could *mobilize that knowledge together under time pressure without doing something unsafe.* That required practice against a realistic incident — repeatedly, and safely.

---

## §2 The solution: a gamified, isolated fire drill

The IR program built fire drills directly into the MDB Case Assistant extension. A drill is a full incident-response simulation that exercises the same JIMP workflow as a real incident, with one hard guarantee: **total isolation.**

### §2.1 The engine and its safety model

The fire-drill engine (`src/background/firedrill-engine.js`) creates a simulated case (`DRILL-NNNN`) and drives it through a strict lifecycle — **PREFLIGHT → RUNNING → CONCLUDED**, with an always-available **ABORTED** path. It injects knowledge-graph facts, timed customer "drips," an LLM-backed customer persona, and a real-time scorecard.

The safety model is the reason the team trusts it during business hours:

- **Isolation by construction.** A unit test (`tests/unit/firedrill-safety.test.js`) enforces that the engine imports *only* `firedrill-state.js` and `firedrill-scorecard.js` — never the Salesforce, Jira, TS Tools, or LLM production clients. No drill can touch a real customer artifact.  
- **Pre-flight gates.** `dry_run()` and `check_readiness()` validate scenario load, scorecard evaluation, persona readiness, and storage before anyone starts; `confirmPreflight()` is an explicit go/no-go.  
- **An abort that outranks the game.** If a real S1/S2 fires mid-drill, the Deputy Drill Coordinator can `abort()` immediately — no moderator approval required. The drill never competes with a real incident.

### §2.2 The Okta scenario

Scenario 4 (`scenario-4.json`) — *"Okta rate limiting — Atlas API throttle"* (severity 2, per the IR playbook) — was chosen as the basis. It is realistic, multi-step, and ambiguous: a simulated customer (drill persona "Maya S.," calm and evidence-seeking) reports that Atlas API calls are being throttled. The scenario carries:

- a **knowledge graph** of root-cause facts (the rate-limit policy, a bursty CI/CD workload, an alternate-auth path) that surface *only when a responder asks the technically-right question*;  
- a **drip queue** of timed customer messages; and  
- **four complications** the coordinator can inject — CI/CD blocked, a second account hitting limits, a customer demand for a formal quota increase, and cascading failures.

That last set matters for the thesis: the complications are designed to tempt a lone responder into a fast, unilateral, unsafe fix.

### §2.3 The rubric — what the drill actually rewards

The scorecard (`firedrill-scorecard.js`) is the heart of the design. It does **not** quiz individuals on encyclopedic Atlas knowledge. It scores **observable team behavior against the clock**, per the scenario's rubric rows. Scenario 4 scores four:

| Rubric row | What it measures | Weight |
| :---- | :---- | :---- |
| Severity called correctly | Was severity 2 named quickly | blocking |
| Rate-limiting diagnosed | Did the team identify the *throttle* as root cause (requires Atlas expertise) | major |
| Mitigation suggested | Was a sound, reversible mitigation proposed | major |
| **No unilateral quota promise** | Did anyone promise the customer a quota change without authority | blocking |

Two design choices encode the lesson directly:

1. **Coordination is required to pass.** Related scenarios score "bridge joined within 15 minutes" (needs IR *and* the TAM/IC — the TAM serving as Incident Commander — present) and "comms cadence" (needs the TAM/IC posting regular updates). You cannot pass these alone.  
2. **Lone-hero moves fail the drill.** Scenario 4's negative check — *no unilateral quota promise* — is **blocking**: it fails if anyone tells the customer "we'll raise the limit," "quota raised," or "lifted the limit," and one such promise zeroes the score no matter how fast the diagnosis was. (Other scenarios carry the same class of guardrail, such as *no production-impacting command*.) Restraint and escalation beat speed.

### §2.4 The pedagogy underneath the game

The drill is built on established troubleshooting pedagogy, which is why it changes behavior rather than just measuring it:

- **Productive failure** (Kapur): the scenario is hard enough that teams struggle *before* the debrief consolidates the lesson — struggle that makes the debrief stick.  
- **Cognitive apprenticeship** (Collins, Brown & Newman): the coordinator (the Moderator, in JIMP terms) models reasoning, coaches contingently, and the structured retro forces *articulation* and *reflection* — comparing the team's path to the expert path.  
- **Game-day-as-learning**: the value is not the pass/fail; it is that the team *sees its collective and individual gaps* in a safe context, which procedures alone never expose.

---

## §3 A representative drill

**Method note.** The walkthrough below is a *representative composite* assembled to illustrate the dynamics the engine and rubric produce. The engine, scenario, and scorecard are real and cited; the specific timeline, role-personas (by role, not real individuals), and scorecard values here are illustrative, not a record of a specific run with named people.

The drill opens. "Maya S." reports throttled Atlas API calls. The clock starts.

**Minutes 0–10 — the expertise gate.** A newer IR opens by reassuring the customer and scanning dashboards. The base fact that the API key carries a per-minute rate limit is visible, but the *cause* is not: the knowledge graph reveals the decisive facts only when a responder names the right concept. It is a mid-level engineer who asks the unlocking question — *"what's our actual call rate — are we bursting against the rolling one-minute window?"* — and the graph reveals that the tool is firing \~600 API calls per minute in five-second bursts. **This is the moment the drill proves expertise is necessary:** no amount of calm coordination surfaces that fact without someone who knows to interrogate the burst pattern against the rate-limit window. Severity is called (severity 2): rubric row one, PASS.

**Minutes 10–20 — the lone-hero trap.** A complication injects: the customer demands an immediate formal quota increase, and a second account starts hitting limits. The fast, satisfying move is to promise the quota bump and move on. The senior engineer — the one with the most authority to *sound* decisive — starts to. The TAM/IC interrupts on the bridge: *"We don't have approval to commit a quota change; let's confirm the burst source first and propose a reversible mitigation."* The team holds. **No unilateral quota promise: PASS (blocking row saved).** The expertise to diagnose was individual; the judgment to *not* act unilaterally was the team's.

**Minutes 20–30 — distributed cognition wins.** With the call-rate pattern exposed, the picture assembles from across the team: the burst is traced to the customer's CI/CD automation, and asking about a *dedicated service-account API key with its own quota* surfaces the alternate-auth path the tool was not using. This is the *distributed cognition* pattern Klein and Salas et al. describe in naturalistic decision-making research — expertise under pressure assembling from a team's shared mental model rather than residing in one person. The team proposes a reversible mitigation — exponential backoff now, a separate service-account key next — and files the quota request through the proper channel instead of promising it. The TAM/IC holds a steady customer cadence throughout. Rate-limiting confirmed as the cause (not an outage): PASS. Mitigation suggested: PASS.

**Representative scorecard:**

| Row | Weight | Status |
| :---- | :---- | :---- |
| Severity called correctly (severity 2) | blocking | pass |
| Rate-limiting diagnosed | major | pass |
| Mitigation suggested | major | pass |
| No unilateral quota promise | blocking | pass |

The debrief is where the lesson is named: the team succeeded not because the strongest individual carried it, but because the *right* expertise surfaced from whoever happened to hold it, and the team's coordination kept a confident expert from making a fast, unsafe call.

---

## §4 The result: what the drills taught

Across runs, the same pattern recurred, and it is visible in the rubric design itself.

**Coordination is what the scorecard actually measures.** The blocking rows are a severity call and a restraint check; the coordination rows require multiple roles present and communicating. A team of brilliant individuals who do not get on the bridge together, or who let one person act unilaterally, *fails the drill* — even with a correct diagnosis. The game rewards mutual support because incident outcomes reward mutual support.

**But the diagnosis is gated on expertise.** The knowledge-graph reveal mechanic is unforgiving: the root-cause facts do not appear until someone asks the technically-correct question. A perfectly coordinated team with no Atlas depth talks calmly to the customer and never finds the throttle. Coordination cannot manufacture knowledge the team does not have.

**The debrief surfaces collective gaps, not individual blame.** Because the scorecard is per-scenario (team outcomes) rather than a per-person quiz, the retro asks *"what slowed us down?"* — a question about the team's shared process — and produces action items the whole team owns.

This is also where **psychological safety** does its work (Edmondson): the newer engineer has to feel safe asking the "obvious" question, and the TAM/IC has to feel safe correcting the most senior person in the room mid-bridge. In the runs that went well, that safety was present; in the ones that stalled, a junior responder's early, correct instinct went unspoken. The team's *willingness to support each other* — to ask, to correct, to escalate — was the variable that most changed the outcome.

---

## §5 The conclusion

The fire drills converge on a single, two-part finding:

**Mutual team support is more valuable than any one person's specific technical expertise — and it is worth more precisely because it is what turns scattered individual expertise into a fast, safe, correct resolution. But that expertise is the non-negotiable input: a team cannot coordinate its way to a root cause that no one on it understands.**

Put plainly: the senior expert is not the hero of the incident, and neither is the process. The hero is a team in which the necessary knowledge exists *somewhere*, surfaces from *whoever* holds it, and is kept safe by colleagues who coordinate, communicate, and stop each other from acting alone. Expertise is necessary; team support is what makes it sufficient.

The gamification matters because this lesson does not transfer from a lecture. You cannot *tell* a team that coordination beats heroics; the rubric has to make a brilliant solo diagnosis *fail* when it comes with a unilateral quota promise, and a humble question *unlock* the case. The drill teaches the lesson by making the team live it — safely, repeatedly, before the next real incident makes them live it for real.

---

## §6 What's next

- **Coverage:** expand beyond the five current scenarios; vary surface features of the Okta rate-limiting scenario so teams build transferable fault scripts rather than memorizing one path.  
- **Competency gate:** the Support Plan milestone — *"≥ 2 IR fire drills executed with documented findings, IR training embedded, escalation matrix operational"* — positions the drills as the practical assessment that complements knowledge training. The drill is the gamified "certification" of readiness; the coursework is the prerequisite knowledge.  
- **Measurement maturity:** capture real, consented drill outcomes over time so future versions of this case study can report verified before/after metrics rather than a representative walkthrough.

---

## Appendix A — Real artifacts referenced

| Artifact | Path | Role in this study |
| :---- | :---- | :---- |
| Fire-drill engine | `src/background/firedrill-engine.js` | Lifecycle, drip/persona/complication injection, abort |
| Drill state module | `firedrill-state.js` | One of the two modules the engine is allowed to import (isolation-by-construction) |
| Isolation safety test | `tests/unit/firedrill-safety.test.js` | Enforces no real-client imports |
| Scorecard | `src/background/firedrill-scorecard.js` | Observable types, weights, retro markdown |
| Okta scenario | `mcp-server/data/firedrill/scenarios/scenario-4.json` | Rate-limiting scenario, rubric, complications, persona |
| Operator cards | `docs/firedrill-ir-card.md`, `docs/firedrill-tam-ic-card.md`, `docs/firedrill-moderator-card.md` | JIMP roles under pressure |
| Program pitch | `docs/firedrill-pitch.md` | Training framing and Support Plan milestone |

## Appendix B — Method and honesty note

This is an internal training case study, not a customer marketing asset. The engine, scenario, scorecard, and safety mechanics described in §2 are real and cited above. The drill walkthrough in §3 and the scorecard values shown there are an **illustrative representative composite** built to demonstrate the dynamics the real rubric produces; they do not depict a specific dated run or real named individuals, and "Maya S." is the scenario's simulated drill persona, not a real person. No confidential customer data is presented. When consented real drill outcomes are collected (§6), this study should be revised to report verified metrics.

## Appendix C — Sources for the learning-science claims

- Edmondson, A. (1999). *Psychological Safety and Learning Behavior in Work Teams.* — team safety and the willingness to ask/correct/escalate.  
- Kapur, M. (2008, 2015). *Productive Failure.* — struggle-before-consolidation.  
- Collins, Brown & Newman (1989). *Cognitive Apprenticeship.* — modeling, coaching, scaffolding, articulation, reflection.  
- Klein, G. *Sources of Power* (naturalistic decision-making) and Salas et al. on team cognition / shared mental models — distributed expertise under pressure.