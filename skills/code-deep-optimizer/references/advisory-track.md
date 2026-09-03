# Advisory track — code-deep-optimizer

> Reference for the `code-deep-optimizer` skill's opt-in advisory track (`--suggest`). The skill's
> SKILL.md carries the summary + rules; this file holds the full pass definitions and delegation.
> See SKILL.md "## Advisory track".

## What the advisory track is (and is not)

The fix-track (the 18 passes) finds **objective defects** that can be applied in place, verified by
the build/lint/test gate, and converged to zero. Some valuable review output is not that shape —
*new features, better architecture, tooling you don't have yet*. Those are **recommendations**, not
fixes:

- **Report-only.** Never auto-applied. Auto-adding a feature or rewriting an architecture changes
  observable behavior, which the behavior-drift guard forbids.
- **Never gates convergence.** Advisory items carry an advisory severity (**Suggest** / **Consider**)
  that never enters the Medium+ exit math. You cannot "converge to zero suggestions."
- **Opt-in.** Off by default; run only under `--suggest`, so the core run stays a tight fixer.
- **Evidence-grounded.** Every item cites a concrete signal in the code — a `// TODO`, a missing
  `switch` case, a stub, a deprecated API in use. No blue-sky suggestions.

## Dispatch (agent fan-out)

Under `--suggest`, the advisory passes run as a **6th parallel bundle** alongside the five fix-track
group bundles (single-file / top-level mode). In repo mode, the per-file advisory pass (A1) runs
inside each per-file subagent; the repo-scope advisory passes (A2, A3) run once at the top level
with the other repo-scope passes (M3, T2, T3). No nested dispatch — a per-file subagent never spawns
further subagents.

## The three passes

### A1 — Feature / latent-intent enhancements (per-file)

Only improvements the code itself *signals*. Each finding names the signal:

- A `// TODO` / `// FIXME` describing intended-but-unbuilt behavior.
- A `switch` / discriminated-union handler missing a case the type permits.
- A `throw new Error("not implemented")` (or equivalent) stub.
- A caller passing an argument the callee ignores, or an exported option never read.
- A happy-path-only function whose surrounding code clearly expects pagination / cancellation /
  retry it doesn't offer.

Do **not** propose features the code gives no signal for. Delegate domain judgment per Stage 0
(e.g. `api-design-patterns` for an API surface, `frontend-ui` for a component).

### A2 — Architecture & design recommendations (repo scope)

Proposals, not violation-flags (M3 flags violations; A2 proposes the redesign):

- Extract a module/boundary where coupling is high or a file is doing too much.
- Introduce a pattern (strategy, adapter, façade) that would remove duplicated branching.
- Re-layer to break a dependency cluster M3 flagged as a cycle.

Each recommendation states the current shape, the proposed shape, and the concrete benefit.
Delegate to `software-engineering-patterns` (references/software-architect.md).

### A3 — Migration & deprecation roadmap (repo scope)

- Deprecated APIs / language features in use (cite the call site).
- End-of-life or unmaintained dependencies (cite the manifest entry).
- Next-major breaking changes the code will hit on upgrade.

Order by urgency (already-broken → deprecated-now → breaks-on-next-major). Delegate to the relevant
domain skill — e.g. `mongodb-operations-expert` for MongoDB driver/server migrations,
`devops-containers-cicd` for base-image/runtime EOL.

## Report shape

Advisory output lands in the report's **Recommendations** section (only when `--suggest` ran),
grouped A1 / A2 / A3, each item: `evidence (file:line / TODO / caller) | recommendation |
advisory severity (Suggest|Consider)`. It is kept entirely separate from the findings table and the
per-iteration severity table, and the Summary line appends `· Recommendations: N`.
