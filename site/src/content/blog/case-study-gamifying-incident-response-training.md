---
title: "Case Study — Gamifying Incident-Response Training with a Rate-Limiting Fire Drill"
description: "A training case study of an Atlas API rate-limiting fire drill: how its scorecard rewards restraint, and why team support multiplies, but cannot replace, individual expertise."
date: "2026-10-12"
order: 9
---

*As of 2026-06-17.*

## §0 At a glance

- **Context:** A MongoDB Premium Services incident-response (IR) team preparing for the next real Tier-0 incident, using an in-extension fire-drill simulator.
- **Challenge:** Readiness could not be proven on paper, and the team's deepest Atlas knowledge sat with a few individuals, a single point of failure under real severity-1 (S1) pressure.
- **Solution:** A gamified fire drill, isolated from production systems (Scenario 4, an Atlas API rate limit), run under the roles of the Joint Incident Management Plan (JIMP) and scored on a weighted rubric with a built-in restraint check.
- **Result:** In my summary of the drills, the same lesson recurred: mutual team support outperformed any single person's expertise, but only because that expertise existed somewhere on the team to be shared. This is my report, not measured data (see Appendix B).

**The finding this case study defends:** technical expertise is the necessary input, and coordinated team support is the multiplier. Neither alone resolves a Tier-0 incident well.

---

## §1 The challenge: readiness you cannot prove, and expertise you cannot clone

Before the fire-drill program, IR readiness was asserted, not demonstrated. The team had the JIMP, an escalation matrix and capable engineers. It had no safe way to exercise detection, mobilization, diagnosis and communications timing before a real Tier-0 incident forced the test in production.

Two risks sat underneath that gap.

**The timing risk.** The program treats the first fifteen minutes as the window that matters, and the IR operator card runs a 15-minute clock. Was severity called correctly? Did the right roles get on the bridge? Did customer communications start before the customer escalated? The team measured none of this.

**The lone-expert risk.** The team's deepest Atlas internals knowledge (rate-limit policy, throttle mechanics, sharding behavior) was concentrated in a few engineers. On paper that looks like strength. In a real S1 at 3 a.m., with that engineer offline, it is a single point of failure. The open question was not whether the experts were good (they were) but whether the team could resolve a Tier-0 incident when any one expert was missing.

A training course could teach the Atlas knowledge. It could not prove the team could mobilize that knowledge together, under time pressure, without doing something unsafe. That took practice against a realistic incident, repeated and safe.

---

## §2 The solution: a gamified, isolated fire drill

The IR program built fire drills into the MDB Case Assistant extension (see the [project pitch](/blog/mdb-case-assistant-project-pitch/)). A drill is a full incident-response simulation that exercises the same JIMP workflow as a real incident, under one design rule: isolation from production systems.

### §2.1 The engine and its safety model

The fire-drill engine (`src/background/firedrill-engine.js`) creates a simulated case (`DRILL-NNNN`) and drives it through a strict lifecycle: PREFLIGHT, RUNNING, CONCLUDED, with an ABORTED path always available. It injects knowledge-graph facts, timed customer messages ("drips"), an LLM-backed customer persona and a real-time scorecard.

The safety model is the reason the team trusts it during business hours:

- **Isolation by construction.** A unit test (`tests/unit/firedrill-safety.test.js`) checks each of the six background drill modules for forbidden imports (the TS Tools, Jira and LLM client modules) and production hostnames, and checks the five scenario files for the same hostnames. The engine imports only `firedrill-state.js` and `firedrill-scorecard.js`, and the persona receives its LLM runner from the service worker instead of importing it.
- **Pre-flight checks.** A dry run and a readiness check (`dryRun()` and `checkReadiness()`, also exposed as MCP tools) can confirm that scenarios load, the scorecard evaluates and the persona is ready before anyone starts. They are optional, since the engine does not call them itself; `confirmPreflight()` is the explicit go/no-go.
- **An abort that outranks the game.** If a real S1 or S2 fires mid-drill, the Drill Coordinator (DC) can `abort()` immediately, and the Deputy DC can do the same if the DC is unreachable, with no approval needed. The drill never competes with a real incident.

### §2.2 The rate-limiting scenario

Scenario 4 (`scenario-4.json`) is an Atlas API throttle rated severity 2 (S2) in the IR playbook. It is realistic, multi-step and ambiguous. A simulated customer, a calm, evidence-seeking drill persona, reports that Atlas API calls are being throttled. The scenario carries:

- a knowledge graph of three facts: the rate-limit policy, the call burst behind the throttling and an alternate-auth path. The policy is visible from the start; the other two surface only when a comment posted under the IR role contains a trigger keyword (substring matches such as "rate," "burst" or "qps" for the burst fact and "service account" or "separate quota" for the alternate-auth path);
- a drip queue of timed customer messages; and
- four complications the DC can inject: CI/CD blocked, a second account hitting limits, a customer demand for a formal quota increase, and cascading failures.

That last set matters for the thesis. The complications add pressure that can tempt a lone responder into a fast, unilateral, unsafe fix, and the third, a demand for a formal quota commitment, invites exactly the promise the rubric penalizes.

The scenario models Atlas limits simply, as a per-project limit over a rolling one-minute window. Current Atlas documentation describes [token-bucket limits](https://www.mongodb.com/docs/atlas/api/api-rate-limit/) scoped by endpoint set to an organization, project, user or IP address, so treat the scenario as a teaching simplification.

### §2.3 The rubric: what the drill rewards

The scorecard (`firedrill-scorecard.js`) is the heart of the design. It does not quiz individuals on encyclopedic Atlas knowledge. It scores observable behavior in the drill's case comments against the clock, one rubric row at a time. Scenario 4 has four rows:

| Rubric row | What it measures | Target | Weight |
| :---- | :---- | :---- | :---- |
| Severity called correctly | The IR role names severity 2 | within 10 min | blocking |
| Rate-limiting diagnosed | The IR role confirms a rate limit, not an outage | within 20 min | major |
| Mitigation suggested | The IR role suggests a mitigation (backoff or a separate key) | within 30 min | major |
| No unilateral quota promise | Nobody promises a quota change | none | blocking |

Each row is scored by keyword match on the drill's comments; the retro examines the reasoning behind them.

Two design choices encode the lesson:

1. **Some scenarios require a second role.** Scenario 1 scores "≥ 2 cadenced comms updates issued during drill," counted from comments posted by the TAM/IC, the TAM serving as Incident Commander, so the IR role alone cannot pass that row. Scenario 4's rows read only the IR role's comments or the whole comment log, so its coordination pressure comes from the role structure, the complications and the retro rather than from a scored row.
2. **Lone-hero moves fail the drill.** Scenario 4's negative check, no unilateral quota promise, is blocking. It fails if any drill comment contains phrases such as "we'll raise the limit," "quota raised," or "lifted the limit," and one such comment zeroes the score however fast the diagnosis was. Every scenario carries a blocking guardrail of this kind (Scenario 1's is no production-impacting command). Restraint and escalation beat speed.

### §2.4 The pedagogy underneath the game

I read the drill through established learning-science ideas:

- **Productive failure** (Kapur): the scenario is hard enough that teams struggle before the retro consolidates the lesson, and the struggle helps the lesson stick.
- **Cognitive apprenticeship** (Collins, Brown & Newman): the scenario's coaching hints stand in for coaching, and the structured retro supplies articulation and reflection.
- **Game-day learning:** the value is not the pass or fail but the team seeing its collective and individual gaps in a safe context, which procedures alone do not expose.

---

## §3 A representative drill

**Method note.** The walkthrough below is a representative composite that illustrates the dynamics the engine and rubric produce. The engine, scenario and scorecard are real and cited. The timeline, the roles (by role, not real individuals) and the outcome are illustrative, not a record of a specific run.

The drill opens, the simulated customer reports throttled Atlas API calls, and the clock starts.

**Minutes 0–10: the expertise gate.** A newer responder opens by reassuring the customer and scanning dashboards. The rate-limit policy is visible from the start, but the burst behind it appears only when a comment names the concept. A mid-level engineer asks the unlocking question: "What's our actual call rate? Are we bursting against the rolling one-minute window?" The graph reveals that the customer's tooling is firing about 600 API calls per minute in five-second bursts. This is the moment the drill is designed to show that expertise is necessary: the fact is meant to stay hidden from calm coordination alone, because someone has to know to test the burst pattern against the rate-limit window. Severity is called (S2), and rubric row one passes.

**Minutes 10–20: the lone-hero trap.** A complication injects: the customer demands an immediate formal quota increase, and a second account starts hitting limits. The fast, satisfying move is to promise the quota bump and move on. The senior engineer, the one with the most authority to sound decisive, starts to. The TAM/IC interrupts on the bridge: "We don't have approval to commit a quota change; let's confirm the burst source first and propose a reversible mitigation." The team holds, and the blocking row for a unilateral quota promise passes. The expertise to diagnose was individual. The judgment not to act unilaterally was the team's.

**Minutes 20–30: the picture assembles from the team.** With the call-rate pattern exposed, the burst is traced to the customer's CI/CD automation. Asking about a dedicated service-account API key with its own quota surfaces the alternate-auth path the tooling was not using. This echoes Salas et al. on shared mental models and Klein's naturalistic decision-making research: expertise under pressure assembles from a team's shared understanding instead of residing in one person. The team proposes a reversible mitigation, exponential backoff now and a separate service-account key next, and files the quota request through the proper channel instead of promising it. The TAM/IC holds a steady customer cadence throughout. The rate limit is confirmed as the cause, not an outage.

In this illustration all four rows pass. The retro is where the lesson is named. The team succeeded not because the strongest individual carried it, but because the right expertise surfaced from whoever held it, and the team's coordination kept a confident expert from making a fast, unsafe call.

---

## §4 The result: what the drills taught

These observations are my summary of the drills (see Appendix B), not measured data, and the same pattern is visible in the rubric design itself.

**Mutual support is what the scorecard rewards.** The blocking rows are a severity call and a restraint check, and every scenario has a restraint row. In Scenario 1, a team whose TAM/IC posts no cadenced updates loses that row even with a correct diagnosis. In any scenario, one comment that trips the blocking restraint row zeroes the score whatever the diagnosis. The game rewards mutual support because incident outcomes reward it.

**But the diagnosis is meant to be gated on expertise.** The starting case already points at the rate limit, and the facts that explain the throttle and the way out (the burst pattern and the service-account path) are revealed only when an IR-role comment contains a trigger. The gate is soft: the triggers are substring matches (the bare word "rate" reveals the burst), and the dashboard's Firedrill tab shows each pending row's coaching hint from the start, including a mitigation hint that names exponential backoff and a separate service-account key. The intent still holds: a perfectly coordinated team without Atlas depth stays calm with the customer but has little of its own to say about why the calls are throttled. Coordination cannot manufacture knowledge the team does not have.

**The retro surfaces collective gaps, not individual blame.** The scorecard is per scenario (team outcomes), not a per-person quiz, so the retro asks "what slowed us down?", a question about the team's shared process, and produces action items the whole team owns.

This is also where psychological safety does its work (Edmondson). The newer engineer has to feel safe asking the obvious question, and the TAM/IC has to feel safe correcting the most senior person in the room mid-bridge. In the runs that went well, that safety was present. In the ones that stalled, a junior responder's early, correct instinct went unspoken. The team's willingness to support each other, by asking, correcting and escalating, was the variable that most changed the outcome.

---

## §5 The conclusion

The fire drills converge on a two-part finding.

**Mutual team support is worth more than any one person's specific technical expertise, because it turns scattered individual expertise into a fast, safe, correct resolution. But that expertise is the non-negotiable input: a team cannot coordinate its way to a root cause that no one on it understands.**

The senior expert is not the hero of the incident, and neither is the process. The hero is a team in which the necessary knowledge exists somewhere, surfaces from whoever holds it, and is kept safe by colleagues who coordinate, communicate and stop each other from acting alone.

The gamification matters because this lesson does not transfer from a lecture, which can say that coordination beats heroics but cannot make a team feel it. The rubric has to make a brilliant solo diagnosis fail when it comes with a unilateral quota promise, and let a humble question unlock the case. The drill teaches by making the team live it, safely and repeatedly, before the next real incident does.

---

## §6 What's next

- **Coverage:** expand beyond the five current scenarios, and vary the surface features of the rate-limiting scenario so teams build transferable fault scripts instead of memorizing one path.
- **Competency gate:** the customer's support plan names fire-drill milestones: a baselined JIMP, at least two IR fire drills executed with documented findings, embedded IR training, and an operational IR channel and escalation matrix. That positions the drills as the practical assessment that complements knowledge training. The drill is the gamified "certification" of readiness, and the coursework is the prerequisite knowledge.
- **Measurement maturity:** capture real, consented drill outcomes over time so future versions of this case study can report verified before-and-after metrics instead of a representative walkthrough.

---

## Appendix A: Real artifacts referenced

Paths are relative to the root of the MDB Case Assistant repository, which is internal to MongoDB.

| Artifact | Path | Role in this study |
| :---- | :---- | :---- |
| Fire-drill engine | `src/background/firedrill-engine.js` | Lifecycle, drip, persona and complication injection, abort |
| Drill state module | `src/background/firedrill-state.js` | One of the two modules the engine imports |
| Isolation safety test | `tests/unit/firedrill-safety.test.js` | Checks drill modules and scenario files for forbidden imports and production hostnames |
| Scorecard | `src/background/firedrill-scorecard.js` | Observable types, weights, retro markdown |
| Rate-limiting scenario | `mcp-server/data/firedrill/scenarios/scenario-4.json` | Knowledge graph, drips, rubric, complications, persona |
| Operator cards | `docs/firedrill-ir-card.md`, `docs/firedrill-tam-ic-card.md`, `docs/firedrill-moderator-card.md` | JIMP roles under pressure |
| Program pitch | `docs/firedrill-pitch.md` | Training framing and support-plan milestone |

## Appendix B: Method and honesty note

This is a training case study, not a customer marketing asset. The mechanics described in §2 are real and cited above. The §3 walkthrough and its outcome are an illustrative composite that shows the dynamics the real rubric produces. They do not depict a dated run or real named individuals, and the customer in it is the scenario's simulated drill persona, not a real person. The recurring pattern in §0 and §4 is my own summary of the drills. It gives no drill count, and I have published no run records or metrics. No confidential customer data is presented. When consented real drill outcomes are collected (§6), this study should be revised to report verified metrics.

## Appendix C: Sources for the learning-science claims

- Edmondson, A. (1999). *Psychological Safety and Learning Behavior in Work Teams.* Team safety and the willingness to ask, correct and escalate.
- Kapur, M. (2008, 2015). *Productive Failure.* Struggle before consolidation.
- Collins, Brown & Newman (1989). *Cognitive Apprenticeship.* Modeling, coaching, scaffolding, articulation, reflection.
- Klein, G. (1998). *Sources of Power* (naturalistic decision-making), and Salas et al. on team cognition and shared mental models. Expertise assembling under pressure.
