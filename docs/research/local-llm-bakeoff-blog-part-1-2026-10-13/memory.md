# Local LLM bake-off blog, part 1

Version: 1.0.0

Delta: First publication record. Interim results as of 2026-10-13 17:15 EDT, with the Devstral result and the Qwen3.8 shortlist note added before merge.

## Intent and constraints

Publish an honest interim account of the 16 GB RTX 5080 model and server bake-off. Part 2 will carry the winners and reasons, so Part 1 must not name a winner. Every number in the post was re-read from the bench result files on the day of writing, not copied from earlier notes. Cite only pages that were opened and whose titles matched; the post's `sources` list was checked with curl (HTTP 200 and matching title) before publication.

## Where each number comes from

The bench lives outside this repository, in a local `llm-bench` directory. The harness scripts are not published.

- Stage 1 speed and smoke: `results/speed-<model>-llamacpp.json`, `results/smoke-<model>-llamacpp.json`.
- Coding table: `scripts/code_table.py` over `results/code-*.json`, regraded test by test with `scripts/regrade.py` into `results/regrade.json`. 374 hidden assertions across ten tasks.
- Research judging: `judge/key.json` maps shuffled IDs to group and file. Group means were recomputed from `judge/<item>/verdict.json` for `claims0`, `claims1`, `claims2`, `cfe` and `qa`, three outputs per model per item.
- Server shoot-out: `results/shootout-lmstudio.json`, `results/shootout-ollama.json`, with the two out-of-memory strings read from `logs/so-vllm.log` and `logs/so-sglang.log`.
- Mixture-of-experts offload: `results/moe-llamacpp-fit-ub2048.json`, `results/moe-ikllama-fit-ub2048.json` and the matching `speed-moe-*` files.
- Embedding baseline: `results/embed-mxbai.json` and `results/embed-mxbai-noprefix.json`.
- Engine versions: llama.cpp `77757a3`, ik_llama.cpp `6c1022e`, vLLM 0.31.0, SGLang 0.5.21, Ollama 0.40.3.

## Corrections made while drafting

- A note in the bench's running file listed the QA invention and grounding counts in an order that read as gpt-oss first. The verdict files show Qwen3.6 invented about 2.7 details and gpt-oss-20b about 1.0. The post uses the verdict-file values.
- The first draft said the Qwen3.6 claims files "covered more key points". The judge's per-concept counts show more on two concepts and fewer on the llama.cpp and vLLM concept. The post now says so.
- VRAM figures are whole-card `nvidia-smi` values in MiB, which include the desktop's share. An early draft mislabeled them as GB.
- The Bionic documentation page describes an agent app that is separate from LM Studio. It does not say how it is built or whether it has a headless mode. The post states only what the probe observed.

- After the first draft, Devstral finished (3 of 10 tasks, 305 of 374 hidden assertions, 0.782 mean fraction, 13,407 s) and was added to the coding table.
- The owner asked whether Qwen3.7 was tested. It was not: Qwen3.7 Max and Plus are hosted-only and the Qwen organization on Hugging Face (queried via the Hugging Face API on 2026-10-13) has no Qwen3.7 repositories. It does have Qwen3.8-27B (dense, Apache-2.0, created 2026-08-05), which the shortlist missed. The post discloses this under "A gap in the shortlist" and Part 2 carries the Qwen3.8-27B results.

## Not yet done (Part 2)

Qwen3.8-27B speed sweep, coding run and `/dr` runs, llama.cpp and ik_llama.cpp `--fit` runs in the shoot-out harness, the five-model embedding comparison against `mxbai-embed-large`, speculative-decoding and cache-quantization tuning, gpt-oss-20b high and low reasoning effort, a multi-model proxy test, a stability soak, service installation and the final recommendation.

## Verification

`npm run build` in `site/` built 1,383 pages with the publication policy check passing. The site test suite gave 259 passed and 3 failed. The same 3 fail with the post removed: two need the `sqlalchemy` module that the local hub environment lacks, and one counts 60 rubric rows where the test pins 59. The llms lint gate reported no High findings. The publish privacy gate reported clean over the whole tree.
