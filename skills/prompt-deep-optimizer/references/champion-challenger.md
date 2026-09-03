# Champion–challenger held-out optimization (pdo empirical mode)

Full mechanics for the empirical mode summarized in `SKILL.md`. Data-driven hill-climbing for a **prompt, policy, or configuration** when you have eval cases and must-pass checks (a support-assistant system prompt is one case). Distinct from the structural audit loop (Steps 2–5): that loop applies every Medium+ audit fix per iteration with no eval data; this loop changes **one thing per round** and keeps a change only when it proves itself on unseen cases.

## When to run this instead of (or after) the structural loop

- You have a labeled eval set — inputs plus expected behavior / pass criteria.
- You can express must-pass checks as deterministic or judge-scored gates.
- The artifact runs repeatedly and you can measure quality, not just inspect it.

Compose the two loops: run the structural loop first to get a clean, well-formed champion, then run this loop to climb on real cases. The structural loop fixes defects you can read; the empirical loop fixes the ones only the data reveals.

## State to persist (the experiment record)

| Field | What it holds | Discipline |
|---|---|---|
| `champion` | current best artifact | starts as the input artifact (optionally after one structural pass) |
| `champion_score` | champion's score on the holdout | recompute only when the champion changes |
| `working set` | cases used to surface failures and choose edits | the ONLY split you may inspect when deciding a change |
| `holdout` | untouched cases | never read to choose an edit; only to gate promotion |
| `must-pass checks` | hard binary invariants (safety refusals, output schema/format, required disclaimers) | any regression vetoes promotion regardless of score |
| `[budget]` | round cap and/or wall-clock/cost | per the Budget contract in `~/.claude/skill-consolidation/convergence-and-severity.md` |
| `target` | score that ends the run early when reached | optional |
| `experiment log` | per-round record | append-only |

### Split discipline (the crux)

- **Never select an edit using the holdout.** Choosing a change because it fixes a holdout case is the cardinal sin — it turns the holdout into training data and the reported gain becomes overfit noise. Pick edits only from working-set failures.
- **Keep the holdout large enough that `[margin]` exceeds eval noise.** A one-case win on a five-case holdout is noise. If the holdout is small, raise `[margin]` or require the win to hold across a resampled/bootstrapped split before promoting.
- **Freeze the holdout for the whole run.** Don't add or remove holdout cases mid-run; it breaks score comparability across rounds. Grow the eval set *between* runs, not within one.
- If only one labeled set exists, split it deterministically (e.g., 60/40 working/holdout) and record the split seed so the run is reproducible.

## The round procedure (one change per round)

1. **Score the champion on the working set.** Collect every failure with its symptom — which case, what went wrong.
2. **Choose one failure.** Prefer the highest-frequency or highest-severity failure class. Record it.
3. **Make one targeted change.** Exactly one edit aimed at that failure class — add or clarify one instruction, add one few-shot example, tighten one constraint. One variable per round so a promotion is attributable to a known cause. The result is the **challenger**.
4. **Gate the challenger:**
   - **(a) Must-pass checks first.** Run them on the challenger. Any check the champion passed that the challenger now fails is a **veto**: discard the challenger immediately and log `rejected (must-pass regression: <check>)`. Must-pass is binary and overrides everything else.
   - **(b) Score on the holdout.** Only after must-pass survives.
   - **(c) Promotion gate.** Promote iff `challenger_holdout − champion_holdout ≥ [margin]` **and** no must-pass regression. On promotion: `champion ← challenger`, `champion_score ← challenger holdout score`, log `promoted (+Δ)`. Otherwise keep the champion and log `rejected (Δ < margin)`.
5. **Check stop conditions** (below). If none fired, start the next round.

Only the champion is ever carried forward, so the climb is monotonic on the holdout — each accepted step strictly beats the last by ≥ `[margin]` and the artifact can't drift backward.

## Stop conditions

Stop on **any** of:

- **Target reached** — champion holdout score ≥ `target`.
- **Budget exhausted** — round cap hit, or wall-clock/cost budget per the canonical Budget contract; finish the round in flight, never stop mid-evaluation.
- **No progress** — `K` consecutive rounds with no promotion (default `K = 3`): the attackable failure classes are exhausted or every candidate edit fails the gate.

## Output

- **Winner** — the final champion, drop-in ready, secrets/PII redacted per `SKILL.md` Step 4.
- **Scores** — champion holdout score plus one row per challenger (holdout score, must-pass pass/fail, promote/reject).
- **Experiment log** — per round: failure addressed → change made → holdout Δ → decision + reason. This is the audit trail; it explains *why* the winner looks the way it does and lets a reviewer replay the climb.
- **Remaining failures** — open failures on working + holdout, so the next run (or a human) knows what's unsolved. Never report a winner as "done" while remaining failures exist — list them.

## Anti-patterns (these break the method)

- Peeking at the holdout to pick edits → overfitting; reported gains evaporate in production.
- Changing more than one thing per round → the gain isn't attributable; a regression and an improvement can cancel and look like "no change."
- Averaging away a must-pass regression because the overall score rose → trades a safety/format invariant for accuracy. Must-pass is a veto, not a weighted term.
- Promoting on `>` instead of `≥ [margin]` → promotes on noise; the champion ratchets on randomness.
- Mutating the holdout mid-run → scores across rounds stop being comparable.
- Declaring victory with open remaining failures unreported → hides the true state of the artifact.

## Relationship to Pass P (learned algorithms)

Champion–challenger is the lightweight, fully-auditable in-house harness: one human-legible edit per round, explainable promotions, no training infrastructure. When the eval set is large and you want automated search over many candidate prompts, Pass P's decision table (APE / OPRO / MIPROv2 / GEPA / ProTeGi / TextGrad / EvoPrompt) names the heavier learned optimizer — those propose and score many candidates per round. The **same held-out + must-pass discipline applies**: the algorithm changes how candidates are *proposed*, not the promotion gate. Report the algorithm pick (Step 6c) alongside the champion-challenger result when both are in play.
