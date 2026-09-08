---
title: "Behavioral Decision-Making and Cognitive Biases"
description: "The descriptive account of judgment and decision-making: how people actually decide, not how they should. Use it to read why a customer, buyer, or stakeholder made a seemingly irrational choice, to et"
---

# Behavioral Decision-Making & Cognitive Biases

The **descriptive** account of judgment and decision-making: how people *actually* decide, not how they *should*. Use it to read why a customer, buyer, or stakeholder made a seemingly irrational choice, to ethically shape the decision environment, and to catch bias in your own forecasts and recommendations.

> Installed as a Claude Code skill with four on-demand reference files (not duplicated here): `references/biases-catalog.md` (full heuristics-and-biases catalog with canonical experiments + TAM application notes), `references/choice-architecture.md` (defaults, EAST, MINDSPACE, sludge vs nudge vs boost, choice overload, ethics of influence), `references/debiasing-and-application.md` (debiasing procedures + worked operator scenarios), and `references/replication-status.md` (what survived vs what is contested/failed, with citable sources — read before citing any effect externally).

**Descriptive vs normative: keep them separate.** This skill is descriptive (the psychology of real decisions). For the *normative* side, computing the optimal action under constraints (linear programming, decision trees, EVPI, expected-utility maximization), use `da-33-prescriptive-analytics`. The gap between the two *is* the subject matter here: people deviate from the normative optimum in systematic, predictable ways.

**The honesty rule (read first).** Decision/social psychology went through a replication crisis. Several once-famous effects did **not** survive (power posing, social priming, and ego depletion are contested/failed). The core judgment-and-decision-making findings (anchoring, framing, the disposition effect, present bias, default effects) replicate well; several adjacent social-psych effects do not. **Never present a debunked effect as established fact.** See `references/replication-status.md` before citing any effect to a customer or in a written recommendation.

## When to reach for this skill

- A customer/buyer made a choice that looks irrational -> name the bias, then address the real driver.
- You're setting a price, an opening offer, or a contract renewal -> anchoring and framing.
- A renewal/expansion stalls on "we already invested in X" -> sunk-cost; on "let's keep things as they are" -> status-quo/default bias.
- You're designing a signup, plan-selection, or opt-in/opt-out flow -> choice architecture (and the sludge you should *remove*).
- You're writing a forecast, capacity plan, or project timeline -> debias your *own* judgment (overconfidence, planning fallacy).
- Someone cites "power posing" / "priming" / "ego depletion" as fact -> check replication status first.

If the task is changing a customer's *behavior over time* (adoption, habit, enablement), that's `behavior-change-psychology`, not this skill.

## Core concepts (the minimum working set)

### 1. Dual-process theory: System 1 / System 2
Two modes of cognition. **System 1** is fast, automatic, associative, affect-laden, and effortless; it produces most snap judgments and most biases. **System 2** is slow, deliberate, effortful, and lazy (it endorses System 1 unless prompted). Labels coined by **Stanovich & West**, popularized by **Kahneman** (*Thinking, Fast and Slow*, 2011). Biases are System 1 outputs that System 2 fails to catch.
- *Caveat:* treat "two systems" as a **useful metaphor, not literal brain architecture**. The strict two-box model is contested (better read as a continuum of automaticity). Don't oversell it.
- *Operator use:* high-stakes decisions (renewals, escalations, architecture calls) deserve a deliberate System-2 step (a checklist or premortem) precisely because the default is a System-1 gut call.

### 2. Heuristics & biases (Tversky & Kahneman, 1974, *Science*)
Mental shortcuts that are "highly economical and usually effective" but produce "systematic and predictable errors." The working set every operator should recognize: **anchoring-and-adjustment** (the first number dominates; the single most useful effect in negotiation), **availability** (judging probability by ease of recall; the loud outage feels likelier than the silent risk), **representativeness** (stereotype/similarity over base rates; the conjunction fallacy), **confirmation bias** (the engine behind most bad root-cause calls), **hindsight bias** ("knew it all along"; corrupts postmortems), **overconfidence** (90%-confident estimates are right far less than 90% of the time; the planning fallacy), **status-quo / default bias**, and **sunk-cost fallacy** (honoring unrecoverable past spend instead of deciding on the margin). Detail and operator scripts: `references/biases-catalog.md`.

### 3. Prospect theory (Kahneman & Tversky, 1979, *Econometrica*)
How people choose under risk, the descriptive replacement for expected-utility theory: **reference dependence** (outcomes judged as gains/losses from a reference point; whoever sets the reference frames the decision), **loss aversion** (losses loom larger than equivalent gains; classic estimate ~2x, but CONTESTED, do not state "2x" as universal law), **diminishing sensitivity** (concave for gains, convex for losses), **probability weighting** (small probabilities overweighted, hence lottery tickets AND insurance; the certainty effect), **the fourfold pattern** (risk-averse for likely gains and unlikely losses; risk-seeking for unlikely gains and likely losses), and **framing effects** ("90% uptime" vs "10% downtime" flip the choice).

> **Loss aversion is contested, not debunked.** Gal & Rucker (2018), "The Loss of Loss Aversion," argue it is far more context-dependent than the "universal 2x law" implies; gains can loom larger at small magnitudes (Harinck et al., 2007) and predicted pain of loss overstates the actual (Kermer et al., 2006). Real in many settings (especially higher-stakes, endowed goods) but **not** a context-free constant. Use it as a *hypothesis to test for this customer*, not a guaranteed lever.

### 4. Bounded rationality & satisficing (Simon) vs ecological rationality (Gigerenzer)
- **Bounded rationality (Herbert Simon)** — limited information/time/compute, so people **satisfice**: pick the first option clearing an aspiration threshold rather than optimizing. Buyers rarely run an exhaustive comparison; they stop at "good enough."
- **Ecological rationality / fast-and-frugal heuristics (Gerd Gigerenzer)** — the *counterpoint* to heuristics-and-biases. Simple heuristics (take-the-best, recognition, 1/N) are **adaptive** and often *more* accurate than complex models under scarce/uncertain information (less-is-more). A heuristic is "rational" relative to its environment.
- *Why both matter:* one says shortcuts cause errors, the other says shortcuts are often the smart move. The truth is conditional: **match the diagnosis to the environment** before "fixing" a heuristic. These two programs are the respective foundations of nudging and boosting.

### 5. Mental accounting & present bias
- **Mental accounting (Thaler)** — money sorted into non-fungible mental "buckets" (budget categories, "house money," renewal-vs-new-purchase), violating fungibility. A spend framed against the "innovation budget" lands differently than against "BAU/maintenance."
- **Present bias / hyperbolic discounting** — near-term costs/rewards discounted far more steeply than distant ones (quasi-hyperbolic beta-delta; Laibson 1997). Produces **time-inconsistency**: "we'll migrate next quarter" gets reversed when next quarter arrives. Upfront-cost / delayed-benefit work (migrations, upgrades, tech-debt paydown) is chronically under-chosen.

### 6. Choice architecture & nudges (Thaler & Sunstein, 2008) and boosts (Hertwig)
- **Choice architecture** — every presentation of options (order, defaults, count, framing) influences choice; there is no neutral presentation, so design it deliberately.
- **Nudge** — alters behavior predictably without forbidding options or changing incentives (libertarian paternalism). The most powerful nudge is the **default** (opt-out organ donation, 401(k) auto-enrollment, pre-checked tiers).
- **EAST** (UK Behavioural Insights Team) — make the desired action **Easy, Attractive, Social, Timely**. The most practical operator checklist.
- **MINDSPACE** — Messenger, Incentives, Norms, Defaults, Salience, Priming, Affect, Commitments, Ego. (The "Priming" element rests on social-priming research that largely failed to replicate; treat it as the weakest element.)
- **Sludge** — friction added *against* the person's own interest (cancellation mazes, hidden opt-outs). **Find and remove sludge in your own onboarding/renewal flows**; don't deploy it.
- **Boosts (Hertwig & Grüne-Yanoff, 2017)** — the *contrast* to nudges. Instead of steering the chooser, **build their competence** (teach a decision rule, give a fast-and-frugal tree, present risks as natural frequencies). Boosts preserve agency and persist after the intervention; prefer them for long-term, trust-based relationships, which is most TAM work.
- *Ethics:* nudge toward the chooser's *own* interest, keep it transparent, never sludge. Full applied detail (incl. choice overload): `references/choice-architecture.md`.

### 7. Debiasing
You cannot will a bias away, but structured procedures help: **consider-the-opposite** (best-evidenced general debiaser, strong against anchoring/overconfidence), **premortem (Gary Klein)** (imagine the project has failed and explain why; prospective hindsight, cheap and high-yield), **reference-class forecasting (Flyvbjerg / Kahneman's "outside view")** (estimate from the distribution of comparable past cases; the fix for the planning fallacy), and **checklists** (force System 2 through a disciplined pass; only work with consistent adherence). Procedures and worked scenarios: `references/debiasing-and-application.md`.

## Operator quick-map (bias -> tell -> move)

**This table is a hypothesis generator, not a verdict.** Treat the observed "tell" (what the customer said or did) as *data*, not a confirmed diagnosis. A tell suggests a *candidate* effect; confirm it against this specific person/context before acting (several effects are context-dependent). If the tell is ambiguous, gather one more observation or ask a clarifying question first. Never state the bias label *to* the customer or imply they are irrational; the label is your internal hypothesis, the "move" is what you do.

| Situation / tell | Candidate effect (verify) | Operator move |
| --- | --- | --- |
| First price/number sets the whole conversation | Anchoring | Set the anchor first; if anchored against, re-anchor with your own reference before negotiating |
| "We've already sunk 18 months into this design" | Sunk-cost fallacy | Reframe to the *marginal* decision from today; make past spend explicitly irrelevant |
| "Let's just keep what we have / leave it as-is" | Status-quo / default bias | Make the better option the default; reduce switching friction; or set a decision deadline |
| Renewal framed only as new spend | Reference dependence / framing | Reframe against the reference point (cost of *losing* current capability, not net-new cost) |
| Team is 90% sure the timeline holds | Overconfidence / planning fallacy | Reference-class forecast + premortem; widen the interval |
| Customer fixates on the rare catastrophic risk | Availability + probability weighting | Provide base rates as **natural frequencies** ("3 in 1,000," not "0.3%") — a boost |
| Buyer stopped at the first "good enough" vendor | Satisficing (bounded rationality) | Don't assume full comparison happened; be the easy, salient option that clears the bar |
| You catch yourself collecting only confirming evidence | Confirmation bias | Consider-the-opposite; assign a devil's advocate |
| Post-incident "it was obviously going to fail" | Hindsight bias | In the postmortem, reconstruct what was *knowable at the time* (see `postmortem-writing`) |
| Signup/cancel flow has hidden friction | Sludge | Remove it; measure completion; opt-out only where it serves the user |

## Anti-patterns

- **Calling a customer "irrational."** They're predictably *boundedly* rational. Name the mechanism and design around it.
- **Citing a debunked effect.** Power posing, social priming, ego depletion are contested/failed; the "2x loss-aversion constant" is over-stated. Check `references/replication-status.md` first.
- **Weaponizing nudges (sludge / dark patterns).** Steering a customer against their own interest is self-defeating in a TAM relationship. Prefer boosts.
- **Treating System 1/2 as literal neuroanatomy.** It's a model. Don't overclaim.
- **One-shot debiasing.** Awareness alone barely moves biases; only structured procedures reliably help, and only with disciplined use.
- **Over-applying loss aversion / "fixing" a heuristic that's actually ecologically rational.** Diagnose the environment first (Gigerenzer's caution).

## Cross-references

- `behavior-change-psychology` — adjacent and complementary. *This* skill = the descriptive psychology of a **decision** (biases, framing, choice architecture). *That* skill = changing **behavior over time** (motivation, Fogg B=MAP, stages-of-change, habit loops, adoption). "Design an onboarding nudge to drive adoption" -> that skill; "what default/framing shapes this purchase decision" -> this skill.
- `da-33-prescriptive-analytics` — the **normative** counterpart (optimal action under constraints: LP/MILP, decision trees, EVPI, utility theory). Compute the optimum there; understand why humans deviate from it here.
- `executive-comms` — persuasion and decision-driving *communication* (board memos, negotiation prep, influence). For the rhetoric/persuasion craft go there; for the underlying decision psychology stay here.
- `postmortem-writing` — applies hindsight-bias control in incident reviews.
- `deep-research-methods` — covers confirmation bias / echo chambers as research anti-patterns.

## Sources

- Tversky, A. & Kahneman, D. (1974). "Judgment under Uncertainty: Heuristics and Biases." *Science* 185(4157), 1124-1131.
- Kahneman, D. & Tversky, A. (1979). "Prospect Theory: An Analysis of Decision under Risk." *Econometrica* 47(2), 263-291.
- Tversky, A. & Kahneman, D. (1991). "Loss Aversion in Riskless Choice: A Reference-Dependent Model." *QJE* 106(4).
- Kahneman, D. (2011). *Thinking, Fast and Slow.*
- Simon, H. A. (1955/1956). Bounded rationality and satisficing.
- Gigerenzer, G. & ABC Research Group. Fast-and-frugal heuristics / ecological rationality.
- Thaler, R. & Sunstein, C. (2008/2021). *Nudge* (and *Nudge: The Final Edition*).
- Laibson, D. (1997). "Golden Eggs and Hyperbolic Discounting." *QJE*.
- Hertwig, R. & Grüne-Yanoff, T. (2017). "Nudging and Boosting." *Perspectives on Psychological Science* 12(6), 973-986.
- Dolan, P. et al. (2010). MINDSPACE; Behavioural Insights Team (2014). EAST.
- Gal, D. & Rucker, D. (2018). "The Loss of Loss Aversion." *Journal of Consumer Psychology*.
- Replication: Open Science Collaboration (2015) *Science*; Many Labs 2; Ranehill et al. (2015) and Simmons & Simonsohn (2017) on power posing; Hagger et al. (2016) on ego depletion.
