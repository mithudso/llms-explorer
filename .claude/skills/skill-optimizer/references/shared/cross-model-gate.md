# Cross-model exit gate (shared mechanics)

Single source of mechanics for the optional `--cross-model` exit gate carried by
`prompt-deep-optimizer`, `skill-optimizer`, and `ddo`/`document-critique`. Each skill carries only
a 3–5 line stub at its insertion point — sko Step 6.5 (before the Step 7 sync), pdo Step 6a.5
(after intent preservation), document-critique/ddo Pass 13.5 (before Pass 14 synthesis, final
iteration only, like Pass 13) — pointing here. Canonical contract:
`convergence-and-severity.md`. This gate is the model-family extension of the contract's blind
re-audit guardrail: that gate isolates the judge's context; this one isolates the judge's model
family and harness.

## Flag and confidentiality (uniform)

`--cross-model` is OPT-IN and **default OFF on every skill, including pdo**. The artifact leaves
the Anthropic harness for a third-party CLI and model — treat this as data egress. Precondition
before sending: confirm pdo's Step 4 redaction sweep ran (pdo targets), or visually confirm the
artifact contains no customer-identifying or internal-only content (sko/ddo targets). Otherwise
abort the gate and log: `cross-model gate: skipped (content not cleared for cross-model egress)`.

## Procedure

1. **Availability check** — `copilot --version`. On failure, log
   `cross-model gate: skipped (copilot CLI unavailable)` in the report and continue to the normal
   exit. The gate must never block a run.
2. **Model detection** — reuse copilot-adversarial-review's Step 0 latest-GPT snippet, or skip
   detection entirely and use the hardcoded fallback to save one CLI round-trip:

   ```bash
   LATEST_GPT=$(copilot -p "What is the single most capable base GPT model ID available to you right now? Reply with only the model ID, nothing else." --silent \
     | grep -oE 'gpt-[0-9]+\.[0-9]+' | head -1)
   [[ "$LATEST_GPT" =~ ^gpt-[0-9] ]] || LATEST_GPT="gpt-4.1"
   ```

3. **One review call** — exactly one `copilot -p` invocation per run (hard limit), passing the
   FINAL artifact with the review-prompt template below.
4. **Triage** — map the returned findings onto the canonical severity ladder with the same
   quote-evidence bar as the contract's evidence rule: verbatim quote or anchor plus a named
   ladder criterion, else recorded as Low.
5. **Re-entry** — Medium+ findings re-enter the loop for at most ONE extra iteration (counts
   against the existing iteration cap — 3/5 per artifact type). After that fix iteration,
   re-triage the residual list WITHOUT a second copilot call. sko wiring: re-enter at Step 3,
   re-run Step 6 verification after the fix, then proceed to Step 7.
6. **Residuals** — anything left is reported as "cross-model residuals" — never silently applied.
   For sko, a cross-model finding triaged High (sko folds Blocking into High per the canonical
   vocabulary mapping) that survives the extra iteration holds the Step 7 hub sync and is
   reported as a sync-blocking residual.

## Review-prompt template (per skill)

> You are reviewing a `<artifact type: production prompt | Claude Code skill | prose document>`.
> Find contradictions, unverifiable claims, and instructions that would misfire — skip style.
> For each finding, give a verbatim quote of the offending text and one line on why it misfires.
>
> `<final artifact>`

## Scope notes

- This is one-shot adversarial finding generation, not repeated statistical eval judging — eval
  judging stays same-provider (cross-model judging introduces confounding; see
  prompt-helper-optimizer `references/prompt-optimization-algorithms.md`).
- ddo: the gate is report-only under `--read-only` and `--annotate` (no fixes applied).
- The gate runs after convergence, so it can never reopen the loop indefinitely: one copilot
  call, at most one extra iteration, then residual reporting.
