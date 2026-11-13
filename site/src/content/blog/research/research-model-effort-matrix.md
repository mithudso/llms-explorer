---
title: "A model and effort matrix for bounded research"
description: "A model and effort matrix for bounded research. An edited historical research report with its original evidence limits retained."
date: "2026-11-13"
category: research
tags: [research, historical-study]
evidenceStatus: unverified
evidenceNote: "Editorial review does not independently reproduce the original experiment. Results retain the source study’s dates, assumptions and limitations."
---

# /dr model × effort matrix — 2026-10-13

Single-concept experiment, **2026-10-13**. Names, versions, prices and availability are historical. Claim counts measure volume; failed and unavailable cells remain visible.

One `/dr` research concept, run once per model × effort cell, with every cell scored the same way.

- **Concept:** "SQLite WAL checkpointing" (topic "SQLite write-ahead logging (WAL)"), depth `standard`: at least 3 independent sources, 1 negation round.
- **Brief:** the identical `dr_run.py` worker brief (`research --dry-run`) for every cell.
- **Isolation:** each cell has its own `HUB_DIR`, so the source cache, run state and telemetry never leak between cells. No cell touched the real hub, concept tree or skill tree.
- **Judge:** one fixed blind claim gate for every cell: `claude-opus-5-5` at `medium`, a requested sample of 10 assertions. The judge refetches the cited pages and returns SUPPORTED, UNVERIFIED, NOT-IN-SOURCE or CONTRADICTED.
- **Harness:** `scripts/dr_model_matrix.py` (`run`, `report`). Raw per-cell data: `cells/<id>/result.json`, the claims file and `gate.json`.

## How each lane ran

| Lane | Runtime | Web tools | Effort control |
|---|---|---|---|
| Claude | `claude -p` via `dr_run.py research` | WebSearch + WebFetch | `--effort low/high/max` |
| OpenAI | `codex exec` 0.162.1, workspace-write sandbox with network | built-in web_search + `curl` | `model_reasoning_effort` |
| Antigravity | `agy -p` 1.3.3 | agy built-in search + `curl` | effort is baked into the model id (`gemini-3.8-flash-low/high`) |
| Local | `llmsx-ollama-agent` (Claude Code tool loop, inference on Ollama `:11435`, M5 Max 64 GB) | Firecrawl search/scrape relay | `--effort` passed through; the local server may ignore it |

## Results

| Lane | Model | Effort | Research s | Claims | High-conf | Sources cached | Gate | Research $ |
|---|---|---|---:|---:|---:|---:|---|---:|
| Claude | Haiku 5.5 | low | 174 | 12 | 5 | 5 | 10/10 | 0.08 |
| Claude | Haiku 5.5 | high | 211 | 15 | 11 | 7 | 9/10 (1 unverified) | 0.12 |
| Claude | Haiku 5.5 | max | 984 | 26 | 16 | 10 | 10/10 | 0.46 |
| Claude | Sonnet 5.5 | low | 66 | 8 | 1 | 3 | 9/10 (1 not-in-source) | 0.24 |
| Claude | Sonnet 5.5 | high | 158 | 14 | 7 | 7 | 10/10 | 0.45 |
| Claude | Sonnet 5.5 | max | 948 | **39** | **24** | 16 | 10/10 | 2.43 |
| Claude | Opus 5.5 | low | 87 | 9 | 5 | 7 | 9/10 (1 unverified) | 0.40 |
| Claude | Opus 5.5 | high | 161 | 15 | 8 | 8 | 10/10 | 0.77 |
| Claude | Opus 5.5 | max | 919 | 28 | 22 | 16 | 10/10 | 3.12 |
| Claude | Fable 5.1 | low | 166 | 13 | 10 | 6 | 10/10 | 1.69 |
| Claude | Fable 5.1 | high | 257 | 21 | 10 | 9 | 10/10 | 2.04 |
| Claude | Fable 5.1 | max | 534 | 26 | 15 | **17** | 10/10 | 3.73 |
| OpenAI | GPT-6.1 Sol | low | 183 | 9 | 5 | 4 | 8/8 | n/a |
| OpenAI | GPT-6.1 Sol | high | 238 | 10 | 1 | 5 | 10/10 | n/a |
| OpenAI | GPT-6.1 Sol | max | 469 | 10 | 8 | 6 | 10/10 | n/a |
| OpenAI | GPT-6 Astra | low | 104 | 7 | 5 | 4 | 10/10 | n/a |
| OpenAI | GPT-6 Astra | high | 160 | 11 | 0 | 5 | 10/10 | n/a |
| OpenAI | GPT-6 Astra | max | 521 | 12 | 1 | 5 | 10/10 | n/a |
| OpenAI | GPT-6 Luna | low | 253 | 7 | 7 | 8 | 10/10 | n/a |
| OpenAI | GPT-6 Luna | high | 237 | 6 | 5 | 5 | 10/10 | n/a |
| OpenAI | GPT-6 Luna | max | 409 | 8 | 6 | 6 | 9/9 | n/a |
| Antigravity | Gemini 3.8 Flash | low | 195 | 5 | 5 | 3 | 6/7 (1 unverified) | n/a |
| Antigravity | Gemini 3.8 Flash | high | 567 | 8 | 8 | 6 | 9/10 (**1 contradicted**) | n/a |
| Antigravity | Gemini 3.8 Flash | max | — | — | — | — | not offered by agy | — |
| Antigravity | GPT-OSS 120B | medium (only level) | 480 | 4 | 3 | 5 | 8/10 (**1 contradicted**, 1 not-in-source) | n/a |
| Local | Gemma 4 31B MLX (`llmsx-research-gemma31-mlx`) | low | 405 | 9 | 8 | 5 | 9/9 | 0 |
| Local | Gemma 4 31B MLX | high | 776 | 10 | 7 | 5 | 10/10 | 0 |
| Local | Gemma 4 31B MLX | max | 543 | 10 | 10 | 7 | 9/10 (**1 contradicted**) | 0 |
| Local | Qwen 3.5 35B | low | 551 | 13 | 9 | 6 | 9/10 (**1 contradicted**) | 0 |
| Local | Qwen 3.5 35B | high | 493 | 14 | 9 | 9 | 8/10 (**1 contradicted**, 1 unverified) | 0 |
| Local | Qwen 3.5 35B | max | 389 | 17 | 15 | 8 | 8/10 (**1 contradicted**, 1 not-in-source) | 0 |
| Local | eGPU Qwen 3.6 27B IQ2_XXS | low/high/max | — | — | — | — | unavailable: `:8000` did not answer an 8-token chat in 90 s | — |

Each single-model gate run cost $0.39–0.70 on top of the research cost (Opus 5.5 at medium effort). Token counts per cell are in `results.json`.

## What the numbers say

1. **No sampled assertion from the 21 Claude/OpenAI cells received a CONTRADICTED verdict.** This does not establish that every produced claim was correct. Every CONTRADICTED verdict came from Antigravity (2 of 3 cells) or the local models (4 of 6 cells). Qwen 3.5 35B produced one contradicted claim at every effort level.
2. **Higher effort was associated with more output in the Claude cells.** For Claude, low → max raised claims 2–5× and sources 2–3×, while the gate rate stayed 90–100% throughout. The low-effort misses were UNVERIFIED or NOT-IN-SOURCE, not CONTRADICTED.
3. **Largest claim counts in this single-concept sample:** Sonnet 5.5 max (39 claims, 16 sources, $2.43) and Opus 5.5 max (28 claims, 22 high-confidence, $3.12). Fable 5.1 max cited the most sources (17) and was the fastest Claude max run (534 s).
4. **Lowest recorded Claude research cost per output claim in this sample:** Haiku 5.5. At low effort it produced 12 claims, 10/10 supported, for $0.08. At max it produced 26 claims for $0.46. Sonnet and Opus at high (~160 s, 14–15 claims, 10/10) are the efficient middle.
5. **OpenAI produced fewer claim rows in this sample.** All judged assertions in its nine cells were SUPPORTED; this is sampled source support, not full-output accuracy. However, claims plateaued at 6–12, and higher effort added few claim rows. GPT-6 Astra marked almost no claim as high-confidence at high/max.
6. **Antigravity had the fewest claim rows and the only sampled cloud contradictions in this run.** It produced the fewest claims (4–8), the only cloud contradictions, and the GPT-OSS run skipped the negation round. GPT-OSS also hit a provider 503 on the first try; the retry succeeded.
7. **Local:** Gemma 31B had fewer sampled contradictions than Qwen 35B in these six cells; this single topic cannot establish a general safety ranking. It was 9/9 and 10/10 at low/high, with one contradiction at max. Qwen 35B gave more claims but was wrong once per run. Local low/high runs took longer than most Claude low/high cells; max timings overlap, and effort barely changed local output.

## Staged pipeline lane (added 2026-10-13)

Question: does splitting `/dr` into passes, each handed to the model + effort that the matrix favoured for that job, beat one model doing everything? Cell `pipeline__sonnet-max+haiku+opus__staged`, same concept, same fixed gate.

| Pass | Model / effort | What it does | Calls | Wall s | $ |
|---|---|---|---:|---:|---:|
| 1. Discover | Sonnet 5.5 / max | Picks and vets sources; writes a source list with org, tier and "why", no claims | 1 | 574 | 1.42 |
| 2. Snapshot | none (`dr_run.py source snapshot`) | Fetches each URL with stdlib, stores text + sha256 in the source library | 16 | 4 | 0 |
| 3. Extract | Haiku 5.5 / low | One call per source snapshot; facts with a verbatim quote; `source facts-put` drops any quote not found in the snapshot | 16 (6 parallel) | 90 | 0.15 |
| 4. Synthesize | Haiku 5.5 / medium | Merges the quote-checked facts into the claims file; confidence from distinct urls and orgs | 1 | 362 | 0.14 |
| 5. Validate | Opus 5.5 / medium | Checks **every** claim against the stored snapshots (no web); drops CONTRADICTED / NOT-IN-SOURCE, rewrites OVERSTATED | 1 | 294 | 2.44 |
| Total | | | | 1326 | 4.15 |

Head-to-head with the best single-model cells:

| Cell | Claims | High / medium / low | Sources (orgs) | Gate | Research $ | $ per claim | Research s |
|---|---:|---|---:|---|---:|---:|---:|
| Sonnet 5.5 max | 39 | 24 high | 16 | 10/10 | 2.43 | 0.062 | 948 |
| Opus 5.5 max | 28 | 22 high | 16 | 10/10 | 3.12 | 0.111 | 919 |
| Fable 5.1 max | 26 | 15 high | 17 | 10/10 | 3.73 | 0.143 | 534 |
| **Staged pipeline** | **135** | 24 / 33 / 78 | 16 (8) | 10/10 | 4.15 | **0.031** | 1326 |

What happened:

1. **The pipeline produced 135 claim rows versus Sonnet-max’s 39 (3.46×), at lower recorded research cost per row.** This does not measure distinct evidence coverage or validated breadth: extraction can split or restate information. Both recorded 16 sources; the pipeline processed their snapshots separately. Haiku pulled 398 facts; 397 quotes were verbatim in the snapshot (1 dropped by the machine check).
2. **The full validation pass caught what a 10-claim sample cannot.** Opus checked all 136 synthesized claims: 128 SUPPORTED, 7 OVERSTATED (scope widened, a condition dropped, a mode omitted; each rewritten from the validator's fix), 1 CONTRADICTED (a forum position attributed to the wrong participant; dropped). That is a 5.9% flaw rate before validation. The single-model cells were only ever sampled 10 claims at a time, so their true rate at this resolution is unknown.
3. **It was not cheaper or faster in total.** My pre-run estimate (~$1.6, faster) was wrong. Validation of every claim is the largest cost ($2.44, 59%), and synthesis is a serial step. Without the validation pass the pipeline costs $1.71 for 136 claims, under Sonnet max alone.
4. **Most claims are low confidence.** 78 of 135 cite one source, so they render as "Tentative:". The pipeline assigned 57 claims to high or medium confidence; those labels are not a fresh independent-source audit, vs 39 total for Sonnet max.

Cheaper variants to try next: validate only high/medium claims with Opus and low claims with Sonnet medium; or validate with Sonnet medium throughout and keep Opus for the fixed gate.

Confound: `dr_run.py source lookup` now answers from the library, so this cell's gate read stored snapshots instead of refetching pages. Verdict rules were unchanged.

### Source library

Built for this lane and now part of `dr_run.py` for every run (`dr_run.py` in the historical hub installation, commits c5e9922c and fe8304a6 in the hub repo):

- `source snapshot --url U [--tier --org --concept --slug]`: fetch (or reuse if under 30 days old) a text snapshot; stable id `src:<16 hex of sha256(normalized url)>`; stores sha256, ETag, Last-Modified, org, concepts, runs and a change history.
- `source facts-put / facts`: quote-anchored extracts per source. A quote must appear verbatim in the snapshot. Extracts are tied to the snapshot sha256, so a changed page invalidates them automatically.
- `source get / list`: metadata by id or url; list by concept or org.
- `source put` (used by every `/dr` worker) now also snapshots the page into the library, and `source lookup` answers read-instead-of-fetch from a fresh library snapshot first. Every existing `/dr` run therefore builds the library and reuses it.
- Snapshot text lives under `HUB_DIR/research/.library/` only. It is third-party content and is never committed; this directory commits only the discovery list and validation verdicts.

Not yet measured: cross-concept reuse. A sibling concept that cites the same sqlite.org pages should skip snapshot and extraction entirely.

## Limits

- One concept, one run per cell. Repeated-run variability, judge variability and an equivalence margin were not estimated. A one-verdict difference therefore has no calibrated noise or tie interpretation in this experiment.
- The gate samples at most 10 claims, so it hits a ceiling quickly. CONTRADICTED counts are the most discriminating signal here.
- The judge is a Claude model. It verdicts against refetched source text, not against its own knowledge, but a cross-family judge could test for family-dependent judgment differences.
- Lanes use their own CLI and web tools, by design ("realistic"). Differences in harness and search quality are part of each result.
- Claude research `$` is the `claude -p` list-price estimate. Codex and agy report tokens only, so their `$` is n/a. Local `$ = 0` denotes no metered local inference API fee. Electricity, hardware and client orchestration costs were not measured; the client-side estimate in `result.json` is not a real charge.
- The eGPU finalist (Qwen 3.6 27B on the RTX 5080) could not run: the llama-server on `:8000` answered `/health` but did not complete a chat. Re-run with `python3 scripts/dr_model_matrix.py run --lanes local --force --only local__egpu-qwen3.6-27b-iq2-xxs__low` once it serves again.

## Reproduce

```bash
python3 scripts/dr_model_matrix.py run                 # all lanes, skips finished cells
python3 scripts/dr_model_matrix.py run --only <cell-id> --force
python3 scripts/dr_model_matrix.py report              # rewrites results.md / results.json
python3 scripts/dr_model_matrix.py run --lanes pipeline  # staged discover/extract/validate cell
```

### Measurement and reproduction boundary

The saved Sonnet-low cell has eight worker claim rows but ten judge verdicts; Astra-low has seven rows but ten verdicts. The retained artifacts do not establish a one-to-one mapping. Gate fractions therefore describe judge-reported assertions, not uniform coverage of worker rows. The separate staged-pipeline sample gate cost $0.76, beyond its $4.15 research total; the pipeline’s $2.44 all-claim validation pass is already included in that total.

The reproduction commands require the original harness, source archive and configured model access. They start new research calls and can incur charges; this editorial review did not run them. Cross-concept reuse and repeated-run uncertainty remain unmeasured.
