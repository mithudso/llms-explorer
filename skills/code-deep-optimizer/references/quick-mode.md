# `--quick` triage mode — full mechanics

Extracted from SKILL.md 2026-09-09 to keep the always-loaded body under the family length
budget. `--quick` is a **registered triage mode** under
`~/.claude/skill-consolidation/convergence-and-severity.md` § Triage modes, which is the only
construct in the family permitted to narrow the Medium+ severity bar, and only while satisfying
that section's five conditions (registered, explicit opt-in, bar named in the Summary, unfixed
findings reported, never a converged status).

## Mechanics

When `--quick` is set, skip the formal Stage 0 activation ceremony (note the
detected stack in one line instead of a full activated-skills block), the
advisory track, empirical mode, and the blind re-audit gate entirely. Run
exactly one iteration:

1. Detect the stack (Stage 0.1) — skip 0.2/0.3's formal skill-activation
   record-keeping, just note it.
2. Run **only** the passes that can produce a Critical finding: **C1**
   (correctness/logic), **C3** (adversarial bug-hunt, but skip the
   counterexample-test mechanic — no time budget for that in quick mode), and
   **S1** (security — injection, secrets, unsafe crypto). Skip C2, S2–S5, P1–P2,
   M1–M4, T1–T4, and the advisory bundles entirely.
3. Apply **Critical findings only**. Everything else — including High, which
   full mode always fixes — is recorded as "noticed, not fixed (--quick mode
   only applies Critical)" so a follow-up full pass isn't starting blind.
4. **Verify gate:** run the detected suite **once before applying and once
   after** — the baseline is a single extra run, not a loop, and without it a
   `FAIL` cannot be attributed. Skip only the bisect. If the after-run is red
   and the baseline was green, report
   `Verify: FAIL (regression introduced by this run)` and leave the fix in
   place with that warning — quick mode has no iteration budget to bisect; the
   caller decides whether to revert or run full `/cdo`. If the baseline was
   already red, report `Verify: FAIL (pre-existing — baseline was red)` and do
   not attribute it to this run. If no suite is detected, report
   `Verify: N/A` and never `FAIL`.
5. Report the Summary line as
   `mode: --quick (bar: Critical)` with `Iterations: 1` and the required
   `Unfixed: N High / M Medium` field, exiting `TRIAGE-PARTIAL` (or
   `TRIAGE-CLEAN` when nothing above Critical was found). Per
   `~/.claude/skill-consolidation/convergence-and-severity.md` § Triage modes,
   a quick run may never report `CLEAN` or `CONVERGED`.

**Composes with the small-profile auto-shrink** (SKILL.md § Convergence loop) but
overrides its cap and bundle count: `--quick` always runs 1 iteration with the
3-pass set above, regardless of file size or detected build/test surface.

This mode exists for prototypes, throwaway scripts, and one-off exploratory
code — **not** for anything shipping to production, touching customer data,
or handling auth/secrets in a real deployment. If the target is clearly one of
those, say so and recommend full `/cdo` (or at least `--no-empirical`)
instead of running `--quick`.


## Why these three passes

C1 (correctness/logic), C3 (adversarial bug-hunt) and S1 (security) are the only passes that can
independently produce a Critical finding under this skill's severity calibration — wrong output,
data loss, RCE/injection, secret leak. Running the other fifteen would cost the full audit budget
to surface findings the mode has already decided not to fix, so they are skipped rather than run
and discarded. C3 runs without its counterexample-test mechanic: writing a failing test, confirming
red, then fixing to green needs an iteration budget quick mode does not have.

## What it does not skip

§ Stage 0.5, the injection gate. The attack it defends against does not care how short the run is,
and a Critical-only pass over untrusted source is exactly the situation where a planted directive
is most likely to be obeyed.
