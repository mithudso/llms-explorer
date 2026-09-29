# Evaluation pilots

Version: 1.0.0. Delta: initial real-code and live skill execution pilots.

Run the deterministic pilots with the dedicated runtime:

```sh
~/.codex/evals/runtime/venv/bin/python scripts/eval_pilots.py
~/.codex/evals/runtime/venv/bin/python -m pytest tests/test_eval_pilots.py -q
```

Add `--benchmark` to run one real Codex `gpt-6-astra` scenario using existing subscription authentication. This consumes model usage. The default run calls no model or embedding service.

The two deterministic cases execute `scripts/merge_concept_trees.py` against synthetic JSON. They verify that a missing category becomes a reachable parent and that colliding slugs retain the better-supported concept. Expected concepts and edges are declared independently of the implementation. DeepEval measures exact graph agreement with a custom deterministic metric. Promptfoo independently calls the same production code through its Python provider and asserts exact output. These validate code behavior and runtime integration; they do not measure LLM answer quality or semantic retrieval relevance.

The live scenario installs a private copy of the existing caveman skill, asks Codex to compress a synthetic retry policy, and verifies output length, HTTP codes, delay, the negative-condition word, and unchanged input. The verifier lives outside the model workspace. This checks selected necessary properties, not full natural-language equivalence. The runner uses a minimal Codex configuration with no configured MCP servers. Authentication and copied workspaces are confined to a temporary tree, removed even on the bounded timeout. No credentials enter committed files or report artifacts.

Private results default to `~/.codex/evals/pilots/`: `deepeval.json`, `promptfoo-results.json`, `benchmark-result.json`, and raw benchmark events under `caveman/.plugin-eval/runs/`. Do not commit that directory. A custom `--output` path should likewise be private and outside the repository.

Validated on 2026-09-28 (benchmark timestamp 2026-09-29 UTC):

- DeepEval: 2/2 real-code assertions passed.
- Promptfoo: 2/2 real-code assertions passed.
- Pytest: 4 tests passed, including two mutation checks that reject changed behavior.
- Live Codex: 1/1 scenario completed and 1/1 executable verifier passed.
- Observed usage: 52,282 input tokens (46,080 cached), 288 output tokens. These are observed usage counts, not a price estimate.

The Plugin Eval summary reported zero shell commands, but raw Codex JSONL contains `command_execution` events. Its current normalization undercounts this event shape; raw logs remain the evidence for tool activity. This single pilot does not establish quality across the entire installed skill estate. Broad static inventory and audits are separate from task-specific behavioral evaluation.
