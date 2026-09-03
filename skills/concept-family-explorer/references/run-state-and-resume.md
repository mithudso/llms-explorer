# Run-state checkpoint & resume (Step write points + re-entry algorithm)

cfe is the family's longest-running orchestrator (a multi-batch saturation
loop spawning many `/dr` runs); without a checkpoint, an interrupted Step 8
loop restarts at Step 1 and repays the full Steps 1–4 scoring cost.

**Schema is defined once** in
`~/.claude/skill-consolidation/run-state/README.md` (`cfe-run-state/v1`:
subject, budget as an opaque object, `round`, `scored`, `researched` with
per-entry `persisted` flags, `skipped`, `failed`, `queue`, `status`) — cite
it, never restate it. The checkpoint is mutable working state; the JSONL
telemetry ledgers are the immutable audit. Plain file writes, no scripts.

## Write points

| When | Write |
| --- | --- |
| End of Step 4 | initial `scored` table |
| End of Step 5 | `queue` (above-threshold selection) |
| After each `/dr` return + its Step 6b persistence | move the concept `queue` → `researched`; set `persisted: true` only after persistence succeeds (honors the budget rule: never stop mid-persist) |
| On a `/dr` failure (Step 6) | move the concept `queue` → `failed` with the reason — keeps resume from re-researching it and keeps the remaining-budget counter (`maxConcepts` − researched − failed) honest |
| End of each Step 7 round | `round`++, merge new `scored` rows |
| Step 8 verdict (entering Steps 9–9c) | `status: "optimizing"` — queue drained, optimization phase begun; on the `BUDGET_EXHAUSTED` path write `"optimizing:budget"` instead (9/9b already skipped as owed work; only 9c+10 remain) |
| Step 10 | `status: "complete:<verdict>"` — the file is then evidence, not a lock |

**dryRun exception:** a plan-only `dryRun` (stops at Step 5; SKILL.md Inputs)
writes **no** checkpoint — the Step 4/5 write points above apply only to a real
run — so a preview is never mislabelled `in-progress` and offered for resume.

Every write also refreshes `updated`. Writes are fail-safe per the canonical
rule (`~/.claude/skill-consolidation/convergence-and-severity.md` §Telemetry:
a write error never blocks or fails a run) — log the failure in the report and
continue.

## Run lock (checked before re-entry) — NORMATIVE SPEC

This section is the single normative lock definition (the SKILL.md section
summarizes and points here). Two concurrent cfe runs on the same subject race
this checkpoint and double-research the queue. Lock file:
`~/.claude/skill-consolidation/run-state/cfe-<subject-slug>.lock`, one JSON
line `{"pid","startedAt","subject"}` (same slug derivation as the checkpoint —
SKILL.md "Run lock, slug & exit statuses"). Taken before the first
shared-surface write; existing lock < 2h old ⇒ exit `LOCK-HELD` (zero writes —
no checkpoint, no CQ file, no telemetry row — and no resume offer: a live lock
means another run owns the subject); ≥ 2h ⇒ steal + note the steal in the
report. Every lock this run created is deleted on EVERY exit path. `dryRun`
never takes a lock, but before its one persistent write (the Step 1 CQ file)
it checks for a live lock and skips that write if one exists.

## Re-entry algorithm

On invocation, check the lock first (above), then check for
`~/.claude/skill-consolidation/run-state/cfe-<subject-slug>.json`:

1. **No file, or `status` starts with `complete:`** → fresh run; a complete
   checkpoint is evidence for the report, not a lock.
2. **Any status not starting `complete:`** (`in-progress`, `optimizing`,
   `optimizing:budget`) → ask **resume-vs-fresh ONCE**, showing file age,
   stored budget, queue size, and the status. Never auto-resume — a
   deliberately abandoned run must not silently restart. (Branches 3–4 define
   what "resume" then does per status.)
3. **On resume:**
   - Skip Steps 1–5; use the stored `scored` table.
   - Re-run the Step 2 inventory ONLY for `queue` items, to catch coverage
     added since the checkpoint (a queued concept another run filled is
     re-tagged HAVE and dropped from the queue, logged as a skip).
   - `researched` entries with `persisted: false` re-run **Step 6b only** —
     persist-spoke is idempotent (dr.md Phase 3: re-running is safe). This
     closes the silent-wipe window where a researched-but-unpinned skill
     vanishes on the next sync yet reads as HAVE.
   - Enter Step 6 at the queue head.
   - Remaining budget = counts only: `maxConcepts` − (researched + failed),
     `maxRounds` − `round`. If the stored budget carries a time cap
     (`budgetMinutes`), surface it to the user — do not reconcile elapsed
     wall-clock across sessions.
4. **`status: "optimizing"`** (queue drained; interrupted during Steps 9–9c) →
   on resume skip Steps 1–8 entirely; rebuild the changed-skill set from the
   `researched[]` rows (skillId + hub per entry) and re-enter at Step 9.
   `/sko` re-runs are convergence loops and `persist-spoke`/sync are
   idempotent, so repeating a partially-done optimization phase is safe.
   **`"optimizing:budget"`** → re-enter at Step 9c only — the budget verdict
   already skipped 9/9b as owed work; resuming must not un-skip them.
5. **On fresh (user chose fresh):** overwrite the checkpoint at the first
   Step 4 write.
