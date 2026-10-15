# Local LLM bake-off harness

The scripts behind the two-part post "Choosing a local LLM for a 16 GB RTX 5080". They drive a llama.cpp `llama-server` (or any OpenAI-compatible server) through a smoke and speed check, a ten-task coding run graded by hidden tests, a research (`/dr`) run, blind-judging packets, an embedding retrieval test, a mixed-load soak and a llama-swap model-swap test.

They are research scripts, not a package. Run everything from the `~/llm-bench` directory, with this tree copied into it (the scripts call each other as `scripts/...` and `finals/...`). They assume that directory (paths are built with `os.path.expanduser("~/llm-bench/...")`), a `llama-server` binary at `~/llm-bench/src/llama.cpp/build/bin/llama-server`, GGUF files under `~/llm-bench/models/`, and a Python environment with `pytest` at `~/llm-bench/envs/pytest`. Edit the `MODELS` table in `scripts/pipeline.py` to point at your own files.

## What is here

| Path | Purpose |
| --- | --- |
| `scripts/lib.py` | OpenAI-style chat client used by every other script (`LLM_BASE`, `LLM_MODEL` environment variables) |
| `scripts/pipeline.py` | The `MODELS` table and `start()`: launch `llama-server`, wait for `/health` |
| `scripts/speed.py`, `scripts/smoke.py` | Decode and prompt-processing speed at 512 / 4k / 16k tokens; the 19-check smoke set |
| `scripts/agent_code.py`, `scripts/finals.py` | The coding agent loop (six tools, hidden-test grading) and the wrapper that starts a server and runs it |
| `scripts/regrade.py`, `scripts/code_table.py` | Re-run hidden tests per saved workdir, count passed assertions, print the comparison table |
| `finals/dr/dr_eval.py`, `finals/dr/fetch_corpus.py`, `finals/dr/community-notes.txt` | The research evaluation: claims files, seven grounded questions, a saturation test, a concept-family map. `fetch_corpus.py` downloads the public papers and pages into `corpus/` (run it from inside `finals/dr`); `community-notes.txt` is the forum-style file that contradicts them and carries an embedded instruction as a prompt-injection check |
| `scripts/dr_summary.py` | Automated metrics per `/dr` run (these overstated the confident model; see the post) |
| `scripts/judge_pack.py`, `scripts/judge_table.py` | Build shuffled, anonymous judging packets with a sealed key; aggregate the judges' verdict files by model group |
| `scripts/tune.py`, `scripts/pickcfg.py` | Sweep server flags (context size, draft length, KV cache type) and pick the fastest valid row |
| `scripts/shootout.py` | The same model behind llama.cpp, LM Studio, Ollama and ik_llama.cpp |
| `scripts/soak.py`, `scripts/swap_test.py` | Thirty-minute mixed-load stability soak; swap latency across models behind llama-swap |
| `finals/embed/build_set.py`, `finals/embed/embed_eval.py` | Build a docstring-to-code retrieval set from a chunk database; recall@k and MRR for an embedding model |
| `config/llama-swap.example.yaml` | The llama-swap config we run |

## What is not here

- The ten coding tasks and their hidden tests. Publishing hidden tests would let models train on them and would defeat the grading. Write your own tasks as `finals/code/tNN/{task.md,repo/,tests_visible/,tests_hidden/}` and `agent_code.py` and `regrade.py` will pick them up.
- The research corpus. Third-party papers and pages are fetched by `fetch_corpus.py`, not redistributed.
- The embedding query set. It was built from our own code index, so it is not published; `build_set.py` shows how to build one from yours (`CHUNK_DB` points at a SQLite file with a `chunks(id, text, meta, kind)` table).
- Our result files and the sealed judging keys.

## Known limits

- The scripts were run once, on one machine, while the experiment was in progress. They contain no tests of their own.
- `regrade.py` grades only the task's own hidden-test files and reads pytest's final summary line. Earlier versions did neither, and both mistakes changed counts; see the post.
- Stored concept-family maps are cut at 6,000 characters (`dr_eval.py`), so judges see a truncated tail on long maps.

## Typical run

```
# server, speed and smoke
python3 scripts/pipeline.py gptoss20b
# coding: starts the server itself, writes results/code-<model>-<tag>.json
THINK=off TAG=run1 python3 scripts/finals.py code qwen38-27b -- -np 1 -ngl 99 -c 24576
python3 scripts/regrade.py results/code-qwen38-27b-run1.json
python3 scripts/code_table.py
```
