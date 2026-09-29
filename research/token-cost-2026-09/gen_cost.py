#!/usr/bin/env python3
"""Measure what it costs an agent to CREATE the assets the matrix tests.

  G1  llms files   from code + human docs: write llms.txt + llms-small.txt
  G2  human docs   from code only:         write README.md + docs/CONFIGURATION.md

Same isolation as run_matrix.py, plus the Write tool, in a throwaway copy of the corpus.
Appends rows to gen_results.jsonl.
"""
import json
import pathlib
import shutil
import subprocess
import time

HERE = pathlib.Path(__file__).resolve().parent
TASKS = {
    "G1": ("docs", "Create two files at the repository root for AI agents. (1) llms.txt in the llmstxt.org "
                   "format: an H1 with the project name, a one-paragraph blockquote summary, then sections of "
                   "markdown links to the repository's key files, each with a one-line description. "
                   "(2) llms-small.txt: a digest of at most 2,000 tokens with what an agent needs to work on "
                   "this code: purpose, architecture, key files, commands, configuration defaults and gotchas. "
                   "Base every statement on the repository's contents."),
    "G2": ("code", "Write documentation for this repository from its code: README.md (purpose, how it works, "
                   "setup, commands, testing) and docs/CONFIGURATION.md listing every environment variable or "
                   "configuration option with its default and effect. Base every statement on the code; this "
                   "will be the reference for other engineers and agents."),
}

with open(HERE / "gen_results.jsonl", "a") as out:
    for repo in ("llm-cache-proxy", "llm-memory-pyramid"):
        for task, (corpus, prompt) in TASKS.items():
            work = HERE / "gen" / repo / task
            shutil.rmtree(work, ignore_errors=True)
            shutil.copytree(HERE / "sbx" / repo / corpus, work)
            before = {p: p.stat().st_size for p in work.rglob("*") if p.is_file()}
            cmd = ["claude", "-p", "--restricted", "--strict-mcp-config", "--tools", "Read,Grep,Glob,Write",
                   "--allowedTools", "Read,Grep,Glob,Write", "--model", "sonnet",
                   "--output-format", "json", "--max-budget-usd", "5"]
            t0 = time.time()
            p = subprocess.run(cmd, cwd=work, input=prompt, capture_output=True, text=True, timeout=1200)
            d = json.loads(p.stdout) if p.stdout.strip().startswith("{") else {}
            u = d.get("usage", {})
            made = {str(q.relative_to(work)): q.stat().st_size for q in work.rglob("*")
                    if q.is_file() and before.get(q) != q.stat().st_size}
            row = {"repo": repo, "task": task, "cost_usd": d.get("total_cost_usd"), "turns": d.get("num_turns"),
                   "input": u.get("input_tokens", 0), "cache_create": u.get("cache_creation_input_tokens", 0),
                   "cache_read": u.get("cache_read_input_tokens", 0), "output": u.get("output_tokens", 0),
                   "files_written": made, "wall_s": round(time.time() - t0, 1), "err": p.stderr[-300:]}
            out.write(json.dumps(row) + "\n")
            out.flush()
            print(json.dumps({k: row[k] for k in ("repo", "task", "cost_usd", "turns", "files_written", "wall_s")}))
