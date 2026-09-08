---
title: "Psychology of Human-AI Interaction (Trust &amp; Appropriate Reliance)"
description: "> Standalone skill authored via the /dr deep-research workflow. Full SKILL.md"
---

# Psychology of Human-AI Interaction: Trust & Appropriate Reliance

> Standalone skill authored via the /dr deep-research workflow. Full SKILL.md
> with TRIGGER/SKIP frontmatter and three `references/` files is installed at
> `~/.claude/skills/human-ai-interaction-psychology/`.

How humans decide whether to follow, override, or ignore an AI system, and how
to design and coach for the *right* amount of reliance. This is human-factors
and decision psychology applied to **trust in machines**, not interpersonal
trust. The central problem is not "more trust" or "less trust" but **calibrated
trust**: reliance that tracks the system's *actual* reliability in the specific
task at hand.

## When to use this skill

- A TAM, customer, or team is **over-relying** (rubber-stamping AI output) or
  **under-relying** (ignoring a tool that outperforms them).
- An AI feature hits **adoption resistance** rooted in distrust, or **dangerous
  over-adoption** where users stop checking.
- You are **designing an AI-assisted workflow** (copilot, recommender, triage
  assistant, autoremediation gate) and must decide what to surface (confidence,
  explanations, friction) to get appropriate reliance.
- A **confidently wrong** AI answer was believed and you need the vocabulary to
  diagnose why.
- You are coaching a customer on a **human-in-the-loop** override policy.

## The one thing to get right

**Trust is an attitude; reliance is a behavior; appropriate reliance is the
goal.** They are routinely conflated and must be kept separate. Optimizing for
"trust" (a survey number) is the wrong target — optimize for **reliance that
matches reliability**: follow the AI when it is right, override it when it is
wrong. Most failures in AI-assisted decisions are *miscalibration*, not a global
trust deficit.

## Core concepts

### 1. Calibrated trust and the trust–reliance distinction (Lee & See, 2004)

**Trust** = "the attitude that an agent will help achieve an individual's goals
in a situation characterized by uncertainty and vulnerability." **Reliance** =
the observable behavior that follows. **Calibration** = correspondence between
trust and the system's true capability.

- **Over-trust → over-reliance / misuse.** Defers when it shouldn't.
- **Under-trust → under-reliance / disuse.** Rejects help that would have worked.

The **trust-calibration curve** plots trust against true reliability; the
diagonal is perfect calibration. **Resolution** = fine-grained trust that
discriminates which cases the system handles well from those it doesn't (good
calibration on average can still have poor resolution). Calibration is a closed
loop, updated by performance feedback, disposition, and organizational norms.

> Operator translation: don't ask "do you trust the tool?" Ask "for *which*
> decisions does it earn the follow?" Coach for resolution, not blanket trust.

### 2. Automation bias & complacency (Parasuraman & Manzey, 2010)

With an imperfect aid: **commission errors** (following a wrong automated
directive without cross-checking) and **omission errors** (missing what the
automation failed to flag because you weren't monitoring). **Automation
complacency** is the attentional root — under load, monitoring drops. Appears in
experts and novices; **not reliably removed by training**; occurs in teams
(redundancy can backfire via diffused responsibility); worsens with very high
automation reliability.

> Operator translation: "a human reviews it" is a control only if it forces
> engagement; under load it decays to rubber-stamping.

### 3. Algorithm aversion (Dietvorst et al., 2015)

People **abandon algorithms faster than humans after seeing them err**, even
when the algorithm outperforms them. **Error visibility** is the trigger (seeing
it fail, not the failure rate). The 2018 follow-up: letting people **adjust the
algorithm's output even slightly** restores willingness to use it (control lever).

> Operator translation: a single visible miss can sink a net-better tool —
> counter with adjustability, expectation-setting before the first error, and
> framing errors as bounded.

### 4. Algorithm appreciation (Logg et al., 2019) — reconciling the two

In six experiments people **weighted advice MORE heavily when told it came from
an algorithm** (Weight-On-Advice). Appreciation waned with **domain expertise**
and when choosing algorithm-vs-**their own** judgment. The two literatures are
reconciled by moderators:

| Pulls toward APPRECIATION (over-weight) | Pulls toward AVERSION (discount) |
| --- | --- |
| No error seen yet (pre-feedback) | A visible algorithmic error |
| Objective / numeric task | Subjective / moral / "human" task |
| Non-expert user | Domain expert |
| Algorithm vs. another person | Algorithm vs. the user's own judgment |
| No control over output | Eased when user can adjust output |

### 5. Why explanations & confidence displays often FAIL to calibrate reliance

- **Plausible-but-wrong explanations increase over-reliance** (Bansal et al.,
  2021, "Does the Whole Exceed Its Parts?"): explanations raised acceptance
  whether the AI was right or wrong — agreement up, accuracy not.
- **Confidence helps only if calibrated**; miscalibrated confidence degrades
  decision quality, and displayed AI confidence shifts the human's own
  self-confidence (anchoring uncertainty without improving ability).
- **Mechanism (dual-process):** explanations feed the accept-heuristic rather
  than interrupting it.

> Operator translation: "we added explanations/confidence" is not evidence of
> appropriate reliance — verify behaviorally (does override-rate track
> error-rate?). Ship confidence numbers only if validated as calibrated.

### 6. Cognitive forcing functions (Buçinca, Malaya & Gajos, 2021)

Friction that compels analytical engagement at decision time: **commit-first**
(judge before the AI is revealed), **on-demand reveal / wait**, **show reasoning
on request** + surface disagreement/uncertainty. These reduced over-reliance on
incorrect AI more than explanation-only designs. Costs: effort, often disliked,
benefit interacts with the user (Need for Cognition) — reserve for high-stakes /
likely-wrong cases. Adjacent levers: onboarding on error boundaries, selective
explanations, adjustable outputs.

### 7. Human-AI complementarity (CTP)

**Complementary Team Performance** = human+AI beat both alone, achieved only
when their errors differ and each defers where the other is better. **CTP is
rare by default** — teams often do worse than the AI alone. Put the human where
they have an information edge the model lacks (context, unobservables), not as a
generic reviewer.

### 8. Anthropomorphism, persona & the uncanny valley

Anthropomorphic cues (persona, warmth, avatar) can raise initial trust but are
mediated by perceived empathy/interaction quality. **Uncanny valley** (Mori,
1970): near-human-but-not affinity drops sharply; an "uncanny valley of trust"
raises competence expectations the bot can't meet. A warm, fluent, confident
persona **manufactures over-trust** regardless of correctness (fluency reads as
competence) — match persona confidence to validated capability.

## Design & coaching checklist

1. Target appropriate reliance, measured behaviorally (override tracks error) —
   not a trust survey number or raw agreement.
2. Set honest expectations before the first error.
3. Show confidence only if calibrated; communicate uncertainty honestly.
4. Don't expect explanations to create skepticism (they raise acceptance); pair
   with friction; prefer selective explanations on likely-error cases.
5. Engineer friction where stakes are high (commit-first, on-demand reveal) —
   and reserve it; it has a cost.
6. Give users control/adjustability over outputs (restores reliance after errors).
7. Place the human where they have an information edge, not as a generic reviewer.
8. Match persona confidence to validated capability.
9. Treat "a human reviews it" as a design problem, not a safeguard.

## Anti-patterns

- Optimizing for "trust" as a survey number instead of calibrated reliance.
- Shipping explanations/confidence and declaring over-reliance solved (they
  often increase it).
- Treating a human-in-the-loop step as a guaranteed control.
- Letting one visible AI error kill adoption of a net-better tool.
- Maxing out a confident anthropomorphic persona on a high-stakes tool.
- Assuming "human + AI" beats either alone (complementarity is rare).
- Conflating trust and reliance in instrumentation.

## Operator scenarios (TAM / AI-native workflow)

- **"Team rubber-stamps the AI triage."** → automation bias/complacency +
  over-reliance. Fix: commit-first workflow, surface disagreement, instrument
  agreement-on-wrong, reserve the human for context the model lacks.
- **"Analysts refuse the new recommender."** → likely algorithm aversion
  (experts, post-error, model-vs-own-judgment). Fix: adjustability,
  expectation-setting, advisor framing, show win-rate vs. baseline.
- **"We added explanations and people trust it more — ship it?"** → more
  agreement is not more appropriate reliance; verify override tracks error.
- **"Friendly human persona for the assistant?"** → lifts likability but risks
  over-trust and the uncanny valley; keep high-stakes tools capability-honest.
- **"Human-in-the-loop / override policy?"** → define by resolution (specific
  case classes needing independent judgment), not a blanket "review everything."

## Key sources

1. Lee & See (2004), *Trust in Automation: Designing for Appropriate Reliance*,
   Human Factors 46(1).
2. Parasuraman & Manzey (2010), *Complacency and Bias in Human Use of
   Automation*, Human Factors 52(3).
3. Dietvorst, Simmons & Massey (2015), *Algorithm Aversion*, JEP:General 144(1);
   and Dietvorst et al. (2018), *Overcoming Algorithm Aversion*, Management Science.
4. Logg, Minson & Moore (2019), *Algorithm Appreciation*, OBHDP 151.
5. Bansal et al. (2021), *Does the Whole Exceed Its Parts?*, CHI 2021.
6. Buçinca, Malaya & Gajos (2021), *To Trust or to Think*, Proc. ACM HCI (CSCW1).
7. Mori (1970/2012), *The Uncanny Valley*, IEEE Robotics & Automation Magazine.
8. Microsoft Research (2024), *Appropriate Reliance on Generative AI*; plus CHI
   2024-2025 work on miscalibrated AI confidence and confidence/self-confidence
   alignment.
