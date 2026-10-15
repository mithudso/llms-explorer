# MongoDB research suite, 2026-10-14

A stage-grouped, resumable research pipeline for every unresearched and frontier concept that
matches a MongoDB name pattern. Extraction and synthesis run on a local Qwen3.8-27B (the
"workhorse"); Sonnet 5.5 does the sourcing and validation; a shared text-only source library sits
behind all of it.

- **Status:** the pilot batch (`mongodb-transactions`, 8 of 707 concepts) is complete and registered. The full run was launched at 2026-10-14 18:50 UTC with `--max-usd 600`; at 19:00 UTC, 4 batches were in discover and 1 (the pilot) was done. Run `status` for the current state.
- **Scope:** 707 concepts in 120 batches, mostly of siblings and at most 8 per batch (5.9 on average; the 3 `mixed-*` batches pool 23 concepts from small families). A frontier concept is one the concept tree names but has never researched. The set is 700 frontier concepts plus 7 researched nodes with zero sources; the 29 matching queue lines are all frontier concepts already. The match is a name or ancestor regex (`MONGO_RX`) and let in at least one non-MongoDB concept: "Process & governance (OWASP GenAI Red Teaming Guide, MITRE ATLAS, ...)" in batch `mixed-1`, matched on `atlas`. Run name `mongodb-2026-10-14`.
- **Code:** `hub/scripts/research_suite.py` (this repo, PR #181) and `~/.global-ai-hub/scripts/source_library.py` (the hub repo). The run imports `frontier_research_batch.py` from the same `hub/scripts` directory, so keep the worktree `~/dev/worktrees/llms-explorer-suite` in place until the run exits.
- **Prompt:** the user's request went through the prompt deep optimizer first. `pdo-report.md` records the audit: the loop stalled at iteration 2 (Medium+ findings rose from 20 to 30). `prompt-v2-operational.md` is the form the run follows; it applies the iteration-2 findings and was not re-audited.

## Stages

| # | Stage | Executor | Effort | Workers |
|---|---|---|---|---|
| 1 | Discover sources (library search first, web for gaps and negation) | `claude -p`, Sonnet 5.5 | max | 4 |
| 2 | Snapshot into the library | stdlib fetch | n/a | 2 batches x 4 |
| 3 | Extract verbatim quotes per source, tagged by concept | Qwen3.8-27B via llama-swap `qwen38` | non-thinking | 1 (single slot) |
| 4 | Synthesize claims; sources and confidence computed in code | Qwen3.8-27B | non-thinking | 1 |
| 5 | Validate every claim against the stored text, no web | `claude -p`, Sonnet 5.5 | medium | 3 |
| 6 | Register: claims -> markdown -> `compile_pack` -> `register` | none | n/a | 1 |

`qwen38` (`~/.config/llama-swap/config.yaml`) is `Qwen3.8-27B-UD-Q3_K_XL.gguf` with its built-in MTP
draft head (`--spec-draft-n-max 2`), thinking off, `-np 1` and `-c 32768`, so parallel requests
only queue. All workhorse calls take one lock; parallelism comes from the cloud stages and the
fetch pool, which run ahead of it (`--ahead`, default 6 batches).

Why these executors: `docs/research/dr-model-matrix-2026-10-13/README.md` found that effort buys
breadth (Sonnet 5.5 at max found the most claims of any single-model cell, 39), that local models
produced contradicted claims in 4 of 6 cells, and that a machine quote check plus a full
validation pass catches what sampling misses. Here the local model never writes a claim from
memory: it selects verbatim spans (snapped to the exact source text), then groups them; Sonnet
checks every resulting claim. The matrix's staged lane used Haiku to extract and Opus to validate,
so Qwen3.8 extraction and Sonnet validation rest on this pilot alone; `~/llm-bench/REPORT.md`
holds the benchmark behind the choice of `qwen38`.

## Source library

Under `~/.global-ai-hub/research/.library/` (git-ignored, third-party text, never published):

| Path | Holds |
|---|---|
| `raw/<domain>/<id>.<ext>.gz` | unprocessed body exactly as fetched, text types only |
| `text/<id>.txt` | processed text (HTML stripped, whitespace folded, boilerplate header removed) |
| `sources/<id>.json` | meta: url, org, tier, sha256, fetch date, concepts, runs, history |
| `facts/<id>.json` | quote-checked extracts, valid only while the page's sha256 is unchanged |
| `sites/<domain>/` | `probe.json`, `manifest.json`, `failed.jsonl` for a site pack |
| `library.db` | SQLite: `source`, `tag`, FTS5 `chunk` (BM25), `request` |

Ids are `src:<16 hex of sha256(normalized url)>`, shared with `dr_run.py source`. Tags come from the
URL (domain, site, repo, product, version, section, kind, format), so tagging costs no model call.
Agents query it with `source_library.py search "<terms>" --domain mongodb.com --top 8` and read
only the matching chunks.

Site acquisition order: an existing library entry or pack; the site's `llms-full.txt` (split into
pages); the `llms.txt` tree with `.md` twins (`crawl-site`); the crawl-to-llms-txt skill for a site
with no `llms.txt`. `mongodb.com/docs` publishes a nested `llms.txt` tree with `.md` twins and no
`llms-full.txt`; its pack holds 7,596 of 7,687 pages (91 failed: 31 returned 404, 60 were too short
to keep); the manifest status is `partial`.

**Rate lesson:** the first crawl ran at about 14 requests per second (request log) and the site
answered 403 to everything after roughly 3,600 pages. The crawler now defaults to 3 requests per
second per host (`SL_RPS`). `prompt-v2-operational.md` specifies 2.5, and the request log shows the
pack crawl at 150 requests per minute (2.5 per second); how that rate was set is not recorded.
After 8 consecutive 403 or 429 responses the crawler pauses 60, 120, then 240 s; the fourth such
run aborts it with manifest status `blocked`, and a rerun resumes.

## Pilot (batch `mongodb-transactions`, 8 concepts)

| Stage | Seconds | Cost |
|---|---:|---:|
| discover (24 sources, 9 organisations, 19 library searches) | 1,048 | $2.54 |
| snapshot | 3 | 0 |
| extract (24 sources, 395 quotes proposed, 369 verified verbatim) | 327 | 0 |
| synthesize (234 claims) | 171 | 0 |
| validate | 239 | $2.27 |
| Total | 1,788 | $4.81 |

Validation of all 234 claims: 227 supported, 5 overstated (rewritten from the validator's fix),
2 contradicted (dropped), 0 not in source. The raw `verdicts-<n>.json` files hold 237 rows
(230/5/2): the validator added one out-of-range SUPPORTED row for each of 3 concepts, which the
code ignores. All 7 flagged verdicts sit in concepts whose row count equals their claim count
(45, 60, 52), so their indices line up. `status` counts the per-concept `validation` field
(227/5/2). 8 concepts registered
with 232 claims, and the hub tree went from 1,334 to 1,342 nodes (hub commit `83321b60`): 8
gained, none lost.

A first attempt at extraction asked the model for a paraphrased fact and a quote: 40% of quotes
were dropped as non-verbatim and a long page overran its token limit (this observation is not
recorded in the run directory). Asking for the quote alone, snapping it to the exact source span,
and salvaging a truncated reply raised the kept rate to 93% (369 of 395). The first attempt's four
ledger rows took 20.7 to 37.0 s per source; the final design took 3.6 to 25.3 s, 13.6 s on average.

Projection for the full scope from one full-size batch. The pilot cost about $0.60 and 62 s of
local model time per concept (498 s of extract and synthesize over 8 concepts). Scaled by concept
count, 707 concepts come to roughly $425 and 12 hours of local time. Scaled by cloud call, they come
to roughly $505: 120 discover calls at $2.54, plus validation at $0.0097 per claim ($2.27 over 234
claims) for about 29 claims per concept. Treat both as estimates, not ceilings. Sourcing is the
longest cloud stage (about 17 minutes per batch, 4 in parallel).

`status` sums `ledger.jsonl`, which also holds four extract rows from the abandoned first attempt
(437 s against the 327 s above).

## Run and resume

```bash
cd <checkout>/hub/scripts   # a checkout holding hub/scripts/research_suite.py (today ~/dev/worktrees/llms-explorer-suite)
pgrep -af 'research_suite.py run'                                    # must print nothing before you start a run
python3 research_suite.py scope  --run mongodb-2026-10-14            # already done for this run; do not rerun
python3 research_suite.py run    --run mongodb-2026-10-14 --repo <checkout> --max-usd 600
python3 research_suite.py status --run mongodb-2026-10-14            # batches per last stage, spend, verdict tallies
touch ~/.global-ai-hub/research/.pipeline/mongodb-2026-10-14/STOP    # stop starting new work
```

Needs llama-swap serving `qwen38` at `127.0.0.1:8200` and the `claude` CLI; `run` checks the
workhorse first (`research_suite.py preflight` does the same on its own). Run one `run` at a time:
there is no lock, and each start rewrites `run.json` and deletes `STOP`. `--repo` is the checkout
root and defaults to the current directory. `scope` builds `scope.json` and `batches.json`; it re-derives the concept set from the
live tree, and registered concepts leave the frontier, so a second `scope` would shrink and can
rename the batches. `--max-usd` (0 means no ceiling) is checked before a batch starts its discover or
validate stage, so up to 7 in-flight stages (4 discover, 3 validate) finish after the ceiling is
crossed.

State lives in `~/.global-ai-hub/research/.pipeline/<run>/` (git-ignored): `scope.json`,
`batches.json`, `run.json`, `ledger.jsonl`, `results.jsonl`, `failures.json`, `crawl-queue.json`,
`frb/` (compiled packs, tree backup), and `batches/<id>/` with `state.json`, `discovery.json`,
`sources.json`, `extract.json`, `claims/`, `verdicts-<n>.json` and `validated/`. A rerun skips
finished stages and retries failed batches. A concept that cannot register (fewer than 3 validated
claims, a blocked synthesis, a pack error) is written to `results.jsonl` as `failed`; its batch
still finishes, and a rerun does not retry it (`status` shows `concepts_failed`). Exit status: 0 clean, 1 some batches failed, 2 halted
(five batches failing in a row, an unreachable workhorse, a provider rate or session limit,
`--max-usd` reached, or `STOP` touched while a batch is in flight), 3 the workhorse preflight failed.

Registered packs go to `~/.global-ai-hub/llms-concepts/<slug>.llms/` and nodes to
`~/.global-ai-hub/concept-tree/tree.json` (the hub's tree, not this repo's `concept-tree/tree.json`).
The code copies the tree to `<run>/frb/backup/tree.json` before a run's first registration, but the
pilot's copy already holds the 8 new nodes (the cause is not recorded), so it is not a restore
point. The pre-pilot tree is the parent of hub commit `83321b60`. In the hub repo, commit only
`tree.json` and the new pack directories.

## Fixed: pack structure

The first 13 packs were built with one bulleted block per concept, and the abstractor makes one
unit per blank-line-separated paragraph, so each pack had 1 unit (the other packs in
`~/.global-ai-hub/llms-concepts/` have a median of 65). `synthesis_markdown` now writes one
paragraph per claim under a heading per section. The 13 packs were regenerated and now have 19 to
58 units each.

## GPU memory

`qwen38` in llama-swap needs about 15.7 GB of the card's 16.3 GB. With the desktop and an Ollama
embed model resident it fails to load (`cudaMalloc failed: out of memory`, shown by llama-swap as
HTTP 500). The run uses a second entry, `qwen38-research` in `~/.config/llama-swap/config.yaml`:
the same Qwen3.8-27B `UD-Q3_K_XL` file and MTP draft head with a 24,576-token context and 256-token
batches, which leaves about 0.9 GB free. Select it with `RS_LLM_MODEL=qwen38-research`. Any other
llama-swap client that requests a different model evicts it; workhorse calls wait up to about
5 minutes for a reload before the run counts it as a systemic failure and halts.
