# Worked example — code-deep-optimizer

Worked example: `/cdo src/fetch-all.js` (default apply+verify mode). Demonstrates the report
format from SKILL.md "## Report format" end-to-end on one small file — Stage 0 detection,
the 18-pass audit, applied diffs, the verify gate (including one backed-out regression), the
convergence loop, the blind re-audit gate, and the final Summary + rollback line.

The numbers below are internally consistent: a single non-test file with no manifest → M3, T2, T3, and T4 are N/A
(architecture, dependency/supply-chain, and tooling-gap are repo-scope; test-suite performance targets test files only), so 14 of 18 passes run; the file has a detected test surface, so the verify
gate is live rather than degenerating to a syntax check.

---

## The input file

A small Node module with four deliberate, real defects (an await-in-loop, a swallowed fetch
error, a hardcoded credential, and an unbounded input used directly):

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

Activated (SKILL.md § 0.2, matrix `references/language-skill-map.md`):

- `lang-js-ts` — JS module; feeds C1, C2, S2, P1, M1. **why:** `.js` extension + ESM exports.
- `nodejs-concurrency-internals` — feeds P2, S2. **why:** `await` inside a `for…of` loop (serial network I/O).
- `security-review` — feeds S1, S3. **why:** hardcoded credential literal + unvalidated external input.
- `software-engineering-patterns (references/code-reviewer.md)` — always-on baseline; feeds all passes.
- `coding-standards` — always-on baseline; feeds M1.

Not activated (no signal): `frontend-ui`, `webcrypto-vault-reviewer`, `mongodb-expert`,
`chrome-extension-expert` — avoiding the over-activation noise the § 0.4 guard warns about.

**Stage 0 status: pass** — every detected domain has a reviewer loaded.

---

## Verify-gate baseline

Detected commands (SKILL.md § Verify gate): `node --check src/fetch-all.js` (syntax) and
`npm test` (resolves to `vitest run`). Surfaced before the first run, then baselined:

> **baseline: `node --check` PASS · `npm test` 12/12 PASS.** No pre-existing failures, so any
> red check after a fix is a true regression.

---

## Iteration 1 — findings

| Pass | file:line | Severity | Finding | Fix | Status |
| --- | --- | --- | --- | --- | --- |
| S1 | `src/fetch-all.js:3` | Critical | Hardcoded API credential `[REDACTED: api key]` committed in source (secret leak) | Read from `process.env.API_KEY`; fail fast if unset | Applied |
| S2 | `src/fetch-all.js:14` | High | `catch {}` swallows fetch errors — network failures are silently dropped | Log and rethrow (or collect) instead of discarding | Applied |
| C3 | `src/fetch-all.js:8` | High | non-2xx responses are still parsed as success (`res.json()` on an error body) — **reproduced by a failing test** (see C3 counterexample below) | Guard on `res.ok` before `res.json()`; throw on non-ok | Applied (test green) |
| P1/P2 | `src/fetch-all.js:7–16` | Medium | `await` per iteration in `for…of` — N sequential round-trips that should be concurrent | Replace loop with `Promise.all` over the ids | Applied |
| S3 | `src/fetch-all.js:6` | Medium | `ids` is untrusted/unbounded and used directly in the URL path and loop | Guard: require an array; cap length; encode each id | Applied |
| M1 | `src/fetch-all.js:21` | Low | `summarize` lacks a guard for items missing `name` | (Low — skipped per Medium+ bar) | Skipped |

**N/A this run (single file):** M3 (architecture — no cross-module structure), T2 (dependency/supply-chain — no manifest in scope), T3 (tooling-gap — no project/repo context), and T4 (test-suite performance — non-test source file). **Ran clean:** S4 (runtime-compat — `fetch` available on the target Node; no version flags), S5 (logging coverage — the S2 fix adds the missing error-path log; no other unlogged critical paths), and M4 (doc-correctness — the comments match behavior). T1 noted the new error paths want tests — the C3 counterexample test covers the error branch. The one Low (M1) is recorded but not fixed.

---

## Applied diff

```diff
--- a/src/fetch-all.js
+++ b/src/fetch-all.js
@@ -1,10 +1,18 @@
 // src/fetch-all.js
 const BASE = "https://api.example.com/v1";
-const API_KEY = "sk_live_EXAMPLE_DO_NOT_USE";   // defect 3: secret in source
+// S1: secret pulled from the environment; value redacted in report as [REDACTED: api key].
+const API_KEY = process.env.API_KEY;
+if (!API_KEY) throw new Error("API_KEY is not set");
 export async function fetchAll(ids) {
-  const out = [];
-  for (const id of ids) {
-    let res;
-    try {
-      res = await fetch(`${BASE}/items/${id}`, {
-        headers: { Authorization: `Bearer ${API_KEY}` },
-      });
-    } catch {}
-    if (res) {
-      out.push(await res.json());
-    }
-  }
-  return out;
+  // S3: validate + bound the untrusted input before use.
+  if (!Array.isArray(ids)) throw new TypeError("ids must be an array");
+  if (ids.length > 1000) throw new RangeError("ids exceeds limit of 1000");
+  // P1/P2: issue the requests concurrently instead of awaiting one at a time.
+  return Promise.all(
+    ids.map(async (id) => {
+      const res = await fetch(`${BASE}/items/${encodeURIComponent(id)}`, {
+        headers: { Authorization: `Bearer ${API_KEY}` },
+      });
+      if (!res.ok) {
+        // S2: surface the failure instead of swallowing it.
+        throw new Error(`fetch ${id} failed: ${res.status}`);
+      }
+      return res.json();
+    }),
+  );
 }
```

---

## C3 counterexample → failing test → fix

C3's adversarial probe hypothesized that a non-2xx response is parsed as success. With a test
harness present, it wrote a *failing test* to confirm the bug before fixing it:

```js
// fetch-all.test.js (added by C3)
it("rejects on a non-2xx response instead of parsing the error body", async () => {
  globalThis.fetch = async () => ({ ok: false, status: 500, json: async () => ({ error: "boom" }) });
  await expect(fetchAll(["x"])).rejects.toThrow(/500/);
});
```

- **Red (confirms the bug):** before the fix, `fetchAll` returned `[{error:"boom"}]` — the test failed, proving the defect is real (not a hunch).
- **Green (confirms the fix):** the `if (!res.ok) throw …` guard in the diff above makes the test pass.

The reproducing test ships with the fix, so the bug stays fixed. With **no** harness, C3 would instead report the bug + this repro sketch and leave the fix to review.

---

## Verify gate after iteration 1

First apply of all four fixes regressed the suite (a test asserted `fetchAll` tolerated a
single bad id by skipping it; the unconditional rethrow broke it). Bounded bisect (SKILL.md
§ Verify gate) reverted the most-recently-applied fix and re-ran:

| command | baseline | after iter-1 (1st apply) | verdict |
| --- | --- | --- | --- |
| `node --check src/fetch-all.js` | PASS | PASS | ok |
| `npm test` (vitest) | 12/12 | 11/12 | **regression → bisect** |

Bisect probe 1 backed out the S2 rethrow → suite green again. The backed-out form was recorded
and **re-applied** in the same iteration as a non-breaking variant (rethrow wrapped in
`Promise.allSettled` semantics so one bad id no longer fails the batch), which the suite
accepted:

| command | baseline | after iter-1 (final) | verdict |
| --- | --- | --- | --- |
| `node --check src/fetch-all.js` | PASS | PASS | ok |
| `npm test` (vitest) | 12/12 | 12/12 | **PASS — no regression** |

> Row carried into the findings ledger during the failing probe:
> `| S2 | src/fetch-all.js:14 | High | swallowed error | unconditional rethrow | BLOCKED (verify-gate regression) |`
> — re-applied as a settled-results variant once the verify gate went green, so it closed for
> convergence rather than shipping unsatisfied.

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
Iterations: 2. Active passes: 14/18 (M3, T2, T3, T4 N/A — single non-test file, no manifest). Profile: standard. Final: 0 Critical, 0 High, 0 Medium, 1 Low. Verify: PASS. Status: CLEAN.
```

---

## Snapshot & rollback

```
cp ~/.claude/skill-consolidation/backups/fetch-all.js-20260615-1412/fetch-all.js src/fetch-all.js
```

---

## With `--suggest`: Recommendations (advisory track)

The run above was default mode (fix-track only). Re-running `/cdo src/fetch-all.js --suggest` adds
the advisory bundle — **report-only, never applied, never part of the Status math**. It would append:

**Recommendations**

- **A1 (feature / latent-intent)** — `src/fetch-all.js:23` `summarize` ignores items whose `name`
  is absent; the caller clearly wants every item represented. *Consider* a fallback label
  (`i.name ?? i.id`). Evidence: callers map over the same array elsewhere expecting a non-empty
  string. *(Suggest)*
- **A3 (migration / deprecation)** — none. `fetch` is current; no deprecated APIs or EOL deps in a
  single-file module. *(N/A)*
- A2 (architecture) is repo-scope → N/A for a single file.

Summary line then reads `… Status: CLEAN · Recommendations: 1`. None of these changed the fix-track
findings, the severity table, or convergence — they are surfaced for the human to decide.
