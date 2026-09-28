# Token cost of docs, llms files and indexes (2026-09-27)

Harness, questions, answer key and raw results behind the blog post
[What Good Docs, llms Files and Indexes Actually Save: 256 Agent Runs](https://llms-explorer.com/blog/what-docs-llms-files-and-indexes-actually-save/).

| File | What it is |
|---|---|
| `questions.json` | 16 questions (12 lookup, 4 comprehension) with grading regexes and retrieval-hit patterns |
| `build_sandboxes.py` | Builds the code / docs / llms / llms-with-pointer corpora from `git archive HEAD`, plus neutral run copies at `w/v1..v4/<repo>` |
| `build_index.py`, `idx_mcp.py` | FTS5 + local-embedding index and the two-tool stdio MCP server that serves it |
| `retrieval_eval.py` | hit@5 per retriever and embedding model |
| `run_matrix.py` | Runs every (question, condition, rep) as an isolated `claude -p --restricted` session |
| `gen_cost.py` | Measures what it costs an agent to write llms files and docs |
| `analyze.py` | Grades the runs and prints the tables |
| `results.jsonl` | The 256 runs reported in the post (answer, tokens, cost, turns, tool calls) |
| `results_pilot_discarded.jsonl` | The first pass, discarded because sandbox directory names leaked the condition to the agent |
| `retrieval_hits.jsonl`, `gen_results.jsonl` | Retrieval-quality and asset-generation measurements |

Absolute sandbox paths in the result files were rewritten to repo-relative ones before publishing.
