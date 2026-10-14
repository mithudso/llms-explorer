# Local LLM bake-off blog, part 2

Version: 1.0.0

Delta: First publication record. Final results as of 2026-10-14 09:30 EDT.

## Intent and constraints

Publish the final account of the 16 GB RTX 5080 bake-off: the chosen model and server, the exact launch command, the evidence, a correction to Part 1, the results that were still running when Part 1 went out, and the harness scripts. Every number was re-read from the bench result files on the day of writing, not copied from earlier notes. Cite only pages that were opened: the `sources` list was checked by fetching each page (HTTP 200 and a matching title or content) before publication.

## Where each number comes from

The bench lives outside this repository, in a local `llm-bench` directory. The scripts are published in `harness/` beside this file; the result files, judging packets and sealed keys are not.

- Qwen3.8-27B speed and memory sweep: `results/tune-qwen38-27b.jsonl` and `results/tune-qwen38-27b-q3.jsonl`.
- Coding table: `scripts/code_table.py` over `results/code-*.json`, regraded test by test with `scripts/regrade.py` into `results/regrade.json`. 374 hidden assertions across ten tasks.
- Research judging (this part): `judge-v3/<item>/verdict.json` for `claims0`, `claims1`, `claims2`, `cfe` and `qa`, mapped to groups with the sealed key `judge-key-v3.json`, three outputs per configuration per item, aggregated by `scripts/judge_table.py`.
- Soaks and swap latency: `results/soak-qwen38-via-swap.json`, `results/soak-qwen38-mtp-via-swap.json`, `results/llama-swap-test.json`.
- Server comparison: `results/shootout-{llamacpp,lmstudio,ollama,ikllamafit1024}.json`.
- Embeddings: `results/embed-*.json`.
- Tuning: `results/tune-qwen36-35b.jsonl`, `results/tune-gptoss20b.jsonl`; gpt-oss reasoning effort from `results/code-gptoss20b-llamacpp-{rehigh-r1,rehigh-r2,relow-r1}.json` and the matching `dr-` files.
- Model facts: the Hugging Face pages in the post's `sources`, fetched on 2026-10-14.

## Decisions

- Winner: Qwen3.8-27B UD-Q3_K_XL with the in-file MTP head (draft length 2), thinking off, llama.cpp `77757a3`, behind llama-swap v265 on 127.0.0.1:8200. gpt-oss-20b stays installed as the speed option.
- Part 1's explanation that dense models are too slow on this card is corrected, not deleted. Qwen3.6-27B and Devstral Small 2 were not re-run, so the post says so.
- The production embedder was not changed (asked the owner; default is no).
- Published: harness scripts with identity paths scrubbed. Not published: the ten coding tasks and hidden tests, the research corpus (fetched from public sources by a script), the embedding query set (built from the owner's own code index), result files and judging keys.
