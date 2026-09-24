# Depth-saturation test

## New-information rate

After each pass, diff its claim list against the accumulated list from all prior passes.

```
new_information_rate = new_atomic_claims_this_pass / total_claims_after_this_pass
```

A claim counts as "new" only if it states something the accumulated list didn't already
cover, even in different words — a rephrased claim is not new (see
`references/depth-passes.md`'s fake-deepening example). Record the rate per pass; the
sequence across passes (e.g. 0.62 → 0.31 → 0.14 → 0.03 → 0.01) is the evidence a report
cites, not a single end-state number.

## Stop condition

Stop after **two consecutive passes** each score `new_information_rate < 0.05` (5%). Two
consecutive passes, not one — a single low-yield pass can be an unlucky question angle
rather than true exhaustion; a second low pass in a row, using a different subset of the
six questions in `references/depth-passes.md`, is the corroborating evidence.

Do not stop early just because a pass "felt" unproductive — compute the rate. Do not keep
going past two consecutive low passes on the theory that pass N+1 might get lucky — that is
what `references/depth-passes.md`'s fake-deepening failure mode looks like from the outside
(more words, same facts).

## Distinguishing true saturation from a mislabeled boundary breach

If new-information rate stays high but the *new* claims are increasingly about a different
concept (a sibling, the parent domain, an adjacent field) rather than deeper facts about the
original concept, that is not saturation — it's the boundary-breach exit in Step 5 of
`SKILL.md`. Check this before crediting a high rate: a pass whose new claims are 80% about
a neighboring concept has not deepened anything; it has quietly become a breadth-first map,
which is `concept-family-explorer`'s job, not this skill's.

## Budget as a separate, non-saturation stop

`maxPasses` or `budgetMinutes` hitting its cap is a soft stop (`BUDGET_EXHAUSTED`), reported
distinctly from `SATURATED-DEPTH`. State the last pass's new-information rate in the report
so the reader can judge whether the cap cut off a still-productive line of inquiry (rate was
still high) or landed near natural saturation anyway (rate was already declining toward the
5% floor).
