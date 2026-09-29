#!/usr/bin/env python3
"""Run every (question, condition, rep) as an isolated headless Claude Code session and
append one JSON row per run to results.jsonl.

Conditions (corpus on disk / access):
  A  code only              file tools (Read, Grep, Glob)
  B  code + human docs      file tools
  C  code + docs + llms     file tools
  D  code + human docs      file tools + keyword/semantic search over that corpus
  E  code only              file tools + keyword/semantic search over that corpus
  F  C + a CLAUDE.md pointer line (INVALID: --restricted never loads CLAUDE.md, so F == C)
  G  B + the repo CLAUDE.md loaded into context (the realistic "great docs" case)
  H  D + CLAUDE.md loaded
  I  llms files + CLAUDE.md loaded, with the pointer line (llms files used as intended)

Isolation: --restricted (no user/project/local settings, so no hooks or plugins; file
tools confined to the corpus dir), --strict-mcp-config (only the index server, and only
in D/E), no skills. Every run pays the same ~8k-token base prompt.

usage: run_matrix.py [--reps N] [--jobs N] [--only COND,...] [--ids P1,M2,...]
"""
import argparse
import concurrent.futures as cf
import json
import os
import pathlib
import subprocess
import time

HERE = pathlib.Path(__file__).resolve().parent
QS = json.loads((HERE / "questions.json").read_text())
EMB = "mxbai-embed-large"
CORPUS = {"A": "code", "B": "docs", "C": "llms", "D": "docs", "E": "code", "F": "llmsptr",
          "G": "docs", "H": "docs", "I": "llmsptr"}
INDEXED = {"D", "E", "H"}
# --restricted does not auto-load project CLAUDE.md; these conditions inject it the way a
# normal Claude Code session would load it.
WITH_CLAUDE_MD = {"G", "H", "I"}
PROMPT = ("You are answering a question about the code repository in the current directory. {q} "
          "Answer concisely with the specific values, identifiers or file paths, and name the file(s) "
          "you relied on. Do not modify any files.")
OUT = HERE / "results.jsonl"
# Neutral sandbox paths: the agent's cwd is w/<vN>/<repo>, so no condition name leaks
# through the working directory shown in its system prompt (a pilot run leaked it).
VDIR = {"code": "v1", "docs": "v2", "llms": "v3", "llmsptr": "v4"}


def run(q: dict, cond: str, rep: int, model: str) -> dict:
    try:
        return _run(q, cond, rep, model)
    except Exception as ex:  # one bad run must never take down the pool
        return {"id": q["id"], "repo": q["repo"], "cond": cond, "rep": rep, "model": model, "ok": False,
                "answer": "", "cost_usd": None, "turns": None, "duration_ms": None, "input": 0, "cache_create": 0,
                "cache_read": 0, "output": 0, "tools": {}, "reads": [], "queries": [], "wall_s": 0,
                "stderr": f"harness error: {ex!r}"}


def _run(q: dict, cond: str, rep: int, model: str) -> dict:
    cwd = HERE / "w" / VDIR[CORPUS[cond]] / q["repo"]
    cmd = ["claude", "-p", "--restricted", "--strict-mcp-config", "--tools", "Read,Grep,Glob",
           "--model", model, "--output-format", "stream-json", "--verbose", "--max-budget-usd", "3"]
    allowed = ["Read", "Grep", "Glob"]
    if cond in WITH_CLAUDE_MD:
        cmd += ["--append-system-prompt-file", str(cwd / "CLAUDE.md")]
    if cond in INDEXED:
        db = HERE / "sbx" / q["repo"] / f"{CORPUS[cond]}.{EMB}.idx.sqlite"
        cfg = {"mcpServers": {"idx": {"command": "python3", "args": [str(HERE / "idx_mcp.py"), str(db)],
                                      "env": {"EMB_MODEL": EMB}}}}
        cmd += ["--mcp-config", json.dumps(cfg)]
        allowed += ["mcp__idx__search_semantic", "mcp__idx__search_keyword"]
    cmd += ["--allowedTools", ",".join(allowed)]
    t0 = time.time()
    p = subprocess.run(cmd, cwd=cwd, input=PROMPT.format(q=q["q"]), capture_output=True, text=True, timeout=600)
    tools, reads, queries, result = {}, [], [], None
    for line in p.stdout.splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "assistant":
            for c in ev.get("message", {}).get("content", []):
                if c.get("type") == "tool_use":
                    tools[c["name"]] = tools.get(c["name"], 0) + 1
                    inp = c.get("input", {})
                    if c["name"] == "Read" and inp.get("file_path"):
                        reads.append(os.path.relpath(inp["file_path"], cwd))
                    if c["name"].startswith("mcp__idx__"):
                        queries.append((c["name"].split("__")[-1], inp.get("query", "")))
        elif ev.get("type") == "result":
            result = ev
    u = (result or {}).get("usage", {})
    return {"id": q["id"], "repo": q["repo"], "cond": cond, "rep": rep, "model": model,
            "ok": bool(result) and not (result or {}).get("is_error"),
            "answer": (result or {}).get("result", ""), "cost_usd": (result or {}).get("total_cost_usd"),
            "turns": (result or {}).get("num_turns"), "duration_ms": (result or {}).get("duration_ms"),
            "input": u.get("input_tokens", 0), "cache_create": u.get("cache_creation_input_tokens", 0),
            "cache_read": u.get("cache_read_input_tokens", 0), "output": u.get("output_tokens", 0),
            "tools": tools, "reads": reads, "queries": queries, "wall_s": round(time.time() - t0, 1),
            "stderr": p.stderr[-400:] if not result else ""}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--jobs", type=int, default=5)
    ap.add_argument("--only", default="A,B,C,D,E")
    ap.add_argument("--ids", default="")
    ap.add_argument("--model", default="sonnet")
    a = ap.parse_args()
    conds = a.only.split(",")
    ids = set(a.ids.split(",")) if a.ids else None
    done_cells = set()
    if OUT.exists():
        for line in OUT.read_text().splitlines():
            d = json.loads(line)
            if d.get("ok"):
                done_cells.add((d["id"], d["cond"], d["rep"]))
    jobs = [(q, c, r) for r in range(1, a.reps + 1) for q in QS for c in conds
            if (not ids or q["id"] in ids) and (q["id"], c, r) not in done_cells]
    print(f"{len(done_cells)} cells already done; {len(jobs)} to run", flush=True)
    done = 0
    with cf.ThreadPoolExecutor(a.jobs) as ex, open(OUT, "a") as f:
        futs = {ex.submit(run, q, c, r, a.model): (q["id"], c, r) for q, c, r in jobs}
        for fut in cf.as_completed(futs):
            row = fut.result()
            f.write(json.dumps(row) + "\n")
            f.flush()
            done += 1
            print(f"[{done}/{len(jobs)}] {row['id']} {row['cond']} r{row['rep']} ok={row['ok']} "
                  f"cost=${row['cost_usd']} turns={row['turns']} tools={row['tools']}", flush=True)


if __name__ == "__main__":
    main()
