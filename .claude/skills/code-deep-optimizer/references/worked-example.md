# Worked example — code-deep-optimizer

Worked example: `/cdo src/fetch-all.js` (default apply+verify mode). Demonstrates the report
format from `references/report-format.md` end-to-end on one small file: Stage 0 detection,
the 18-pass audit, applied diffs, the verify gate (including one backed-out regression), the
convergence loop, the blind re-audit gate, and the final Summary + rollback line.

The numbers below are internally consistent. The file lives in a small package (a
`package.json` with `vitest` as a dev dependency and a `test` script), which is what the verify
gate detects. The run is single-file scope, so three repo-scope passes plus T4 are N/A by rule, not for
lack of a manifest: M3 (architecture), T2 (dependency/supply-chain) and T3 (tooling-gap) run
only in repo mode (SKILL.md § Architecture, step 3), and T4 (test-suite performance) targets
test files only. 14 of 18 passes run; the detected test surface makes the verify gate
live rather than a syntax check.

---

## The input file

A small Node module with four deliberate, real defects (an await-in-loop, a swallowed fetch
error, a hardcoded credential, and an unbounded input used directly). The line numbers of this
listing are the anchors the findings table cites:

```js
// src/fetch-all.js
const BASE = "https://api.example.com/v1";
const API_KEY = "sk_live_EXAMPLE_DO_NOT_USE";   // defect 3: secret in source
export async function fetchAll(ids) {
  const out = [];
  for (const id of ids) {                        // defect 4: ids unvalidated/unbounded
    let res;
    try {
      res = await fetch(`${BASE}/items/${id}`, {  // defect 1: serial await in loop
        headers: { Authorization: `Bearer ${API_KEY}` },
      });
    } catch {}                                    // defect 2: error swallowed
    if (res) {
      out.push(await res.json());
    }
  }
  return out;
}

export function summarize(items) {
  return items.map((i) => i.name).join(", ");
}
```

---

## Stage 0 — detection and reviewer-skill activation

Detection (SKILL.md § 0.1): extension `.js` + `export`/`async` → JS/TS module; `fetch` +
`await` in a loop → Node async/concurrency surface; a `sk_live_...` literal and a
caller-supplied `ids` array reaching `fetch` → security surface (secret + untrusted input).

Activated (SKILL.md § 0.2, matrix `references/language-skill-map.md`; each cited in the form
that resolves at its current tier):

- `lang-js-ts`: JS module; feeds C1, C2, S2, P1, M1. **why:** `.js` extension + ESM exports.
- `lang-js-ts (references/nodejs-concurrency-internals.md)`: feeds P2, S2, C3. **why:** `await` inside a `for…of` loop (serial network I/O).
- `security-review`: feeds S1, S3, C3. **why:** hardcoded credential literal + unvalidated external input.
- `software-engineering-patterns (references/code-reviewer.md)`: always-on baseline; feeds all passes.
- `software-engineering-patterns (references/coding-standards.md)`: always-on baseline; feeds M1.

Not activated (no signal): `frontend-ui`, `misc-catch-all (references/webcrypto-vault-reviewer.md)`,
`mongodb-expert`, `chrome-extension-expert`. That avoids the over-activation noise the § 0.4
guard warns about.

**Stage 0 status: pass.** Every detected domain has a reviewer loaded.
`memory-central: none for <slug>` (no lessons or conventions file for this repo).

---

## Verify-gate baseline

Detected commands (SKILL.md § Verify gate): `node --check src/fetch-all.js` (syntax) and
`npm test` (the package's `test` script, which resolves to `vitest run`). Surfaced before the
first run, then baselined:

> **baseline: `node --check` PASS · `npm test` 12/12 PASS.** No pre-existing failures, so any
> red check after a fix is a true regression.

One of the 12 existing tests matters later: `"skips an id whose fetch fails and returns the
rest"`. It encodes the module's intended tolerance of a single bad id, and the behavior-drift
guard treats that as the contract to keep.

---

## Iteration 1 — findings

| Pass | file:line | Severity | Finding | Fix | Status |
| --- | --- | --- | --- | --- | --- |
| S1 | `src/fetch-all.js:3` | Critical | Hardcoded API credential `[REDACTED: api key]` committed in source (secret leak) | Read from `process.env.API_KEY`; fail fast if unset | Applied |
| S2 | `src/fetch-all.js:12` | High | `catch {}` swallows fetch errors; network failures are silently dropped | Log the failure at error level and skip that id (keeps the existing tolerant-batch behavior) | Applied (after bisect, see below) |
| C3 | `src/fetch-all.js:13–14` | High | A non-2xx response is still parsed as success (`res.json()` on an error body), so callers receive error payloads as items. **Reproduced by a failing test** (see C3 counterexample below) | Treat `!res.ok` like a failed fetch: log and skip | Applied (test green) |
| P1/P2 | `src/fetch-all.js:6–16` | Medium | `await` per iteration in `for…of`: N sequential round-trips that should be concurrent | Replace the loop with `Promise.allSettled` over the ids | Applied |
| S3 | `src/fetch-all.js:6` | Medium | `ids` is untrusted/unbounded and used directly in the URL path and loop | Guard: require an array; cap length; encode each id | Applied |
| M1 | `src/fetch-all.js:20–21` | Low | `summarize` lacks a guard for items missing `name` | (Low; skipped per Medium+ bar) | Skipped |

**N/A this run (single-file scope):** M3, T2, T3 (repo-scope passes; they run only in repo
mode) and T4 (targets test files only). **Ran clean:** S4 (runtime-compat: `fetch` available
on the target Node; no version flags), S5 (logging coverage: the S2 fix adds the missing
error-path log, asserted by the C3 test; no other unlogged critical path), and M4
(doc-correctness: the comments match behavior). C1, C2 and M2 also ran clean (no logic, contract, or
duplication findings). T1 noted the new error path wants a test; the
C3 counterexample covers it. The one Low (M1) is recorded but not fixed.

---

## Applied diff (final state, after the verify gate)

```diff
--- a/src/fetch-all.js
+++ b/src/fetch-all.js
@@ -1,20 +1,28 @@
 // src/fetch-all.js
 const BASE = "https://api.example.com/v1";
-const API_KEY = "sk_live_EXAMPLE_DO_NOT_USE";   // defect 3: secret in source
+// S1: secret pulled from the environment; value redacted in report as [REDACTED: api key].
+const API_KEY = process.env.API_KEY;
+if (!API_KEY) throw new Error("API_KEY is not set");
 export async function fetchAll(ids) {
-  const out = [];
-  for (const id of ids) {                        // defect 4: ids unvalidated/unbounded
-    let res;
-    try {
-      res = await fetch(`${BASE}/items/${id}`, {  // defect 1: serial await in loop
+  // S3: validate + bound the untrusted input before use.
+  if (!Array.isArray(ids)) throw new TypeError("ids must be an array");
+  if (ids.length > 1000) throw new RangeError("ids exceeds limit of 1000");
+  // P1/P2: issue the requests concurrently; allSettled keeps one bad id from failing the batch.
+  const results = await Promise.allSettled(
+    ids.map(async (id) => {
+      const res = await fetch(`${BASE}/items/${encodeURIComponent(id)}`, {
         headers: { Authorization: `Bearer ${API_KEY}` },
       });
-    } catch {}                                    // defect 2: error swallowed
-    if (res) {
-      out.push(await res.json());
-    }
+      // C3: a non-2xx body is not an item.
+      if (!res.ok) throw new Error(`fetch ${id} failed: ${res.status}`);
+      return res.json();
+    }),
+  );
+  // S2/S5: surface every failure instead of swallowing it, then return the rest.
+  for (const r of results) {
+    if (r.status === "rejected") console.error("fetchAll: item skipped", { reason: String(r.reason) });
   }
-  return out;
+  return results.filter((r) => r.status === "fulfilled").map((r) => r.value);
 }
 
 export function summarize(items) {
```

---

## C3 counterexample → failing test → fix

C3's adversarial probe hypothesized that a non-2xx response is parsed as success. With a test
harness present, it wrote a *failing test* that pins the intended behavior (the bad item is
dropped and the failure is logged, consistent with the existing tolerant-batch test) before
fixing. The package's vitest setup file sets `API_KEY` before any import, which is why the S1
fail-fast guard does not trip in the suite:

```js
// src/fetch-all.test.js (added by C3)
it("drops a non-2xx item and logs the failure instead of returning the error body", async () => {
  const err = vi.spyOn(console, "error").mockImplementation(() => {});
  globalThis.fetch = async () => ({ ok: false, status: 500, json: async () => ({ error: "boom" }) });
  await expect(fetchAll(["x"])).resolves.toEqual([]);
  expect(err).toHaveBeenCalledWith(
    "fetchAll: item skipped",
    expect.objectContaining({ reason: expect.stringMatching(/500/) }),
  );
});
```

- **Red (confirms the bug):** before the fix, `fetchAll(["x"])` resolved to `[{ error: "boom" }]`
  and nothing was logged; the test failed, proving the defect is real (not a hunch).
- **Green (confirms the fix):** the `if (!res.ok) throw …` guard plus the settled-results loop in
  the diff above make it pass, and the log assertion is the S5 coverage T1 asked for.

The reproducing test ships with the fix, so the bug stays fixed. With **no** harness, C3 would
instead report the bug + this repro sketch and leave the fix to review. Under `--read-only` the
test body lands in the report, never on disk (`references/flags-and-statuses.md`).

---

## Verify gate after iteration 1

The first apply of all fixes removed S2's `catch {}` and let every rejection propagate inside a
`Promise.all` (so C3's `if (!res.ok) throw` also rejected the batch), which regressed the suite:
the existing test `"skips an id whose fetch fails and returns the rest"` went red because one
failing id now rejected the whole batch. Bounded bisect
(SKILL.md § Verify gate) reverted the most-recently-applied fix and re-ran:

| command | baseline | after iter-1 (1st apply) | verdict |
| --- | --- | --- | --- |
| `node --check src/fetch-all.js` | PASS | PASS | ok |
| `npm test` (vitest) | 12/12 | 11/12 | **regression → bisect** |

Bisect probe 1 restored S2's swallowing `catch` → suite green again. The backed-out form was recorded
and **re-applied** in the same iteration as a non-breaking variant (`Promise.allSettled`, log each
rejection, return the fulfilled items), which both the existing test and the C3 counterexample
accepted. That variant is the diff shown above:

| command | baseline | after iter-1 (final) | verdict |
| --- | --- | --- | --- |
| `node --check src/fetch-all.js` | PASS | PASS | ok |
| `npm test` (vitest) | 12/12 (+1 new) | 13/13 | **PASS: no regression** |

> Row carried into the findings ledger during the failing probe:
> `| S2 | src/fetch-all.js:12 | High | swallowed error | propagate rejection (Promise.all) | BLOCKED (verify-gate regression) |`
> Re-applied as the settled-results variant once the verify gate went green, so it closed for
> convergence rather than shipping unsatisfied. The behavior-drift guard is what forced the
> variant: the existing test documented intended behavior, so the fix had to keep it.

---

## Iteration 2 — clean

Re-ran the 14 active passes on the patched file: **0 Critical / 0 High / 0 Medium** (the lone
M1 Low remains, below the bar). A CLEAN exit triggers the **blind re-audit gate** (SKILL.md
§ Convergence loop): a fresh-context subagent received only the final code + the pass list and
ran the finding passes once → **0 corroborated Medium+ findings**. Gate corroborates nothing →
**CLEAN** confirmed.

Per-iteration severity table:

| Iteration | Critical | High | Medium | Low | Nit |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 2 | 2 | 1 | 0 |
| 2 | 0 | 0 | 0 | 1 | 0 |

---

## Summary

```
Iterations: 2 · Active passes: 14/18 (M3, T2, T3, T4 N/A: single-file scope, non-test source) · profile: standard · Final: 0C/0H/0M/1L · Verify: PASS · Status: CLEAN
```

`index: n/a (outside corpus roots)`: the target is application code, not a file under the
semantic-index roots.

`memory-central: none for <slug>`: no lessons or conventions rows exist for this repo, so no
regression checks fired.

---

## Snapshot & rollback

```
cp ~/.claude/skill-consolidation/backups/fetch-all.js-20260615-141200/fetch-all.js src/fetch-all.js
rm src/fetch-all.test.js   # created by C3 this run; a snapshot copy cannot restore its absence
```

---

## With `--suggest`: Recommendations (advisory track)

The run above was default mode (fix-track only). Re-running `/cdo src/fetch-all.js --suggest` adds
the advisory bundle: **report-only, never applied, never part of the Status math**. It would append:

**Recommendations**

- **A1 (feature / latent-intent)**: `src/fetch-all.js:20–21` `summarize` ignores items whose
  `name` is absent; the caller clearly wants every item represented. *Consider* a fallback label
  (`i.name ?? i.id`). Evidence: callers map over the same array elsewhere expecting a non-empty
  string. *(Suggest)*
- **A3 (migration / deprecation)**: none. `fetch` is current; no deprecated APIs or EOL deps in a
  single-file module. *(N/A)*
- A2 (architecture) is repo-scope → N/A for a single file.

Summary line then reads `… Status: CLEAN · Recommendations: 1`. None of these changed the fix-track
findings, the severity table, or convergence; they are surfaced for the human to decide.

> **`--quick` triage mode (v1.8.0+).** Under `--quick` this reference does not apply: the mode runs only C1, C3 and S1, skips the advisory track and empirical mode, and fixes Critical findings only. See `references/quick-mode.md`.
