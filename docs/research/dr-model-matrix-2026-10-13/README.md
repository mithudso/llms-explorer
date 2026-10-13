# /dr model × effort matrix — 2026-10-13

One `/dr` research concept, run once per model × effort cell, with every cell scored the same way.

- **Concept:** "SQLite WAL checkpointing" (topic "SQLite write-ahead logging (WAL)"), depth `standard`: at least 3 independent sources, 1 negation round.
- **Brief:** the identical `dr_run.py` worker brief (`research --dry-run`) for every cell.
- **Isolation:** each cell has its own `HUB_DIR`, so the source cache, run state and telemetry never leak between cells. No cell touched the real hub, concept tree or skill tree.
- **Judge:** one fixed blind claim gate for every cell: `claude-opus-5-5` at `medium`, sample of 10 claims (all claims when fewer than 10). The judge refetches the cited pages and returns SUPPORTED, UNVERIFIED, NOT-IN-SOURCE or CONTRADICTED.
- **Harness:** `scripts/dr_model_matrix.py` (`run`, `report`). Raw per-cell data: `cells/<id>/result.json`, the claims file and `gate.json`.

## How each lane ran

| Lane | Runtime | Web tools | Effort control |
|---|---|---|---|
| Claude | `claude -p` via `dr_run.py research` | WebSearch + WebFetch | `--effort low/high/max` |
| OpenAI | `codex exec` 0.162.1, workspace-write sandbox with network | built-in web_search + `curl` | `model_reasoning_effort` |
| Antigravity | `agy -p` 1.3.3 | agy built-in search + `curl` | effort is baked into the model id (`gemini-3.8-flash-low/high`) |
| Local | `llmsx-ollama-agent` (Claude Code tool loop, inference on Ollama `:11435`, M5 Max 64 GB) | Firecrawl search/scrape relay | `--effort` passed through; the local server may ignore it |

## Results

| Lane | Model | Effort | Research s | Claims | High-conf | Sources | Gate | Research $ |
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

Each gate run cost $0.39–0.70 on top of the research cost (Opus 5.5 at medium effort). Token counts per cell are in `results.json`.

## What the numbers say

1. **Claude and OpenAI never produced a wrong claim; Antigravity and the local models did.** All 21 Claude and OpenAI cells had zero CONTRADICTED verdicts. Every CONTRADICTED verdict came from Antigravity (2 of 3 cells) or the local models (4 of 6 cells). Qwen 3.5 35B produced one contradicted claim at every effort level.
2. **Effort mostly buys breadth, not accuracy.** For Claude, low → max raised claims 2–5× and sources 2–3×, while the gate rate stayed 90–100% throughout. The low-effort misses were UNVERIFIED or NOT-IN-SOURCE, not CONTRADICTED.
3. **Best depth:** Sonnet 5.5 max (39 claims, 16 sources, $2.43) and Opus 5.5 max (28 claims, 22 high-confidence, $3.12). Fable 5.1 max cited the most sources (17) and was the fastest max run (534 s).
4. **Best value:** Haiku 5.5. At low effort it produced 12 claims, 10/10 supported, for $0.08. At max it produced 26 claims for $0.46. Sonnet and Opus at high (~160 s, 14–15 claims, 10/10) are the efficient middle.
5. **OpenAI was accurate but shallow.** All 9 cells were 100% supported. However, claims plateaued at 6–12, and higher effort added little breadth. GPT-6 Astra marked almost no claim as high-confidence at high/max.
6. **Antigravity was the weakest cloud lane.** It produced the fewest claims (4–8), the only cloud contradictions, and the GPT-OSS run skipped the negation round. GPT-OSS also hit a provider 503 on the first try; the retry succeeded.
7. **Local:** Gemma 31B is still the safer local pick. It was 9/9 and 10/10 at low/high, with one contradiction at max. Qwen 35B gave more claims but was wrong once per run. Local runs took 2–5× longer than Claude at the same effort, and effort barely changed local output.

## Limits

- One concept, one run per cell. A single different verdict is within noise; treat ±1 gate verdict as a tie.
- The gate samples at most 10 claims, so it hits a ceiling quickly. CONTRADICTED counts are the most discriminating signal here.
- The judge is a Claude model. It verdicts against refetched source text, not against its own knowledge, but a cross-family judge would remove any family bias.
- Lanes use their own CLI and web tools, by design ("realistic"). Differences in harness and search quality are part of each result.
- Claude research `$` is the `claude -p` list-price estimate. Codex and agy report tokens only, so their `$` is n/a. Local `$` is the electricity cost only; the client-side estimate in `result.json` is not a real charge.
- The eGPU finalist (Qwen 3.6 27B on the RTX 5080) could not run: the llama-server on `:8000` answered `/health` but did not complete a chat. Re-run with `python3 scripts/dr_model_matrix.py run --lanes local --force --only local__egpu-qwen3.6-27b-iq2-xxs__low` once it serves again.

## Reproduce

```bash
python3 scripts/dr_model_matrix.py run                 # all lanes, skips finished cells
python3 scripts/dr_model_matrix.py run --only <cell-id> --force
python3 scripts/dr_model_matrix.py report              # rewrites results.md / results.json
```
