# Prompt deep optimizer report

Target: the user's request of 2026-10-14 (inline, 307 tokens, one-off). Routing: the optimizer's
helper offered the `/ph` handoff for a short one-off; the user had asked for the deep optimizer by
name, so the run proceeded (`routing: under-threshold, user override`, profile `small`: 3 merged
audit groups, iteration cap 3).

## Original prompt

> pull all of the unresearched and frontir concepts involving mongodb and start a full research suite on all of them using the ollama.cpp and ollama-swap Qwen3.8-27B, the Unsloth UD-Q3_K_XL build with the draft head to run it as the workhorse. And while it's doing that build a source libray that contains a full raw dump of every source polled so it can be processed and reused by multiple agents. It will need a processed and an unprocessed space, save the text only. If a site is used very often then use the crawl site to llms skill to pull and parse everything the site has, or look for existing document packs that already do this. Make sure to look for the llms-full.txt file on the site to simplify the whole process. You decide how this all should be stored, tagged, and processed to optimize the efficiency and capacity of the research tasks. Also have the various stages of resaearch be done in a grouped fashion like has been noted, and run each stage in parallel so for instance sourcing will be pulled by agents with max effort since that has been exprimentally proven to be far more effective but then switch to lighter reasoning for the processing. Before doing any of this make sure all the repos are up to date.

## Iteration log

| Iter | Active passes | Skipped | Findings C/H/M (deduped) | Delta Medium+ | Edit distance | Action |
|---|---|---|---|---|---|---|
| 1 | 14/16 | L, N | 0 / 13 / 7 | n/a | n/a | rewrote (v1) |
| 2 | 15/16 | N | 0 / 12 / 18 | +10 (20 to 30) | 82.98% (helper) | exit: no progress |

Exit: `STALLED`. The canonical check (`convergence_check.py`, EXECUTED) returned `NO-PROGRESS` for
Medium+ 20 to 30. The grounded rewrite named real files, commands and endpoints, so independent
auditors could check them against the repo and found more to fix; the count rose even though the
High count fell from 13 to 12.

Shipped candidate (best of pool): the iteration-1 rewrite, `0/12/18`. Its successor, which applies
the iteration-2 findings and was not re-audited, is `prompt-v2-operational.md`.

## What the first audit found (iteration 1, 20 deduplicated findings)

High: the preflight scope and end state; the "research suite" and "has been noted" references had
no antecedent (stage list undefined); the concept set had no source or match rule; the runtime
name ("ollama.cpp", "ollama-swap") was ambiguous and had no fallback; stage-to-executor-to-effort
mapping missing; the acquisition order and "very often" threshold undefined; no budgets, stop
conditions or retry policy; parallel versus pipeline semantics undefined; no definition of done;
"you decide" storage with many parallel agents invites diverging layouts; no capture-ordering
guarantee for the raw dump; third-party text stored with no location or publication rule; no
untrusted-data rule.
Medium: raw dump versus "text only"; source citation; long-input handling; failure path;
ordering of the final precondition; clarifying-question policy; no example of the common path.

## Changes made (iteration 1 rewrite, by finding group)

| Finding group | Severity | Fix applied | Status |
|---|---|---|---|
| Preflight scope and end state | High | Section 0: repos, fast-forward rule, preserve then update, skip unreachable | Applied |
| Stage list and executors | High | Section 3 table: six stages with executor, effort, workers, output | Applied |
| Concept set | High | Section 1: union of three named sources, dedupe, fixed `scope.json` | Applied |
| Runtime identity | High | Section 2: llama-swap endpoint, model id, config path, no substitution | Applied |
| Acquisition order | High | Section 5: library, `llms-full.txt`, `llms.txt` tree, crawl skill, single page | Applied |
| Library layout | High | Section 4: location, raw and processed spaces, README before first write, fetch only through `ingest` | Applied |
| Untrusted data | High | Opening rule for fetched pages, search results and files | Applied |
| Publication of third-party text | High | Library git-ignored, never committed or published | Applied |
| Parallelism | High | Pipeline across batches; workhorse queue serial; cloud ahead | Applied |
| Done criterion and report | High | Section 7 | Applied |
| Spend and wall-clock limits | Medium | Pilot projection; limits are the user's | BLOCKED (user decision; none set) |
| Raw versus text only, citations, failure path, order | Medium | Defined in sections 4, 6, 7 | Applied |

Iteration-2 findings (applied in the operational v2, not re-audited): run root and artifact names;
one crawler tool; preflight per-case rules and no pushing of backup refs; one scope predicate;
extraction made deterministic (BM25 query is the batch's concept names); stage-4 sharding; a stage-6
adapter; provider-wide breaker; pilot definition; trust propagation to every worker prompt;
numeric crawl limits.

## Deliberate behavioral deltas (finding-justified)

Same task, same four obligations (research the concepts, build the library, stage by effort, sync
repos first). Deltas: the run stops when the named workhorse is unavailable instead of
substituting (Pass K); fetched content is treated as data (Pass I); the library is never
committed (Pass H); a failed concept is logged instead of blocking the run (Pass C); the
spend and wall-clock limits remain the user's (BLOCKED).

## Summary line

Iterations: 2. Active passes: 15/16. Profile: small. Final: 0 critical, 12 high, 18 medium, 3 low.
Token delta: +977 tokens (307 to 1,284; grounded paths, a stage table, constraints). Status:
STALLED. Smoke: N/A (not executable in-harness: needs the hub, GPU and cloud quota) [no grade].
Evidence: 6a0=N/A 6a2=N/A edit-dist=EXECUTED. routing: under-threshold, user override.
telemetry: 15 rows appended. Shipped iteration 1 rewrite (0/12/18). Self-check: 8/8 (EXECUTED).

Algorithm recommendation: `structural-only`. There is no paired data and no metric, and the run
is a one-shot pipeline, so no learned prompt optimizer applies.
