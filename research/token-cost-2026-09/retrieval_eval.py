#!/usr/bin/env python3
"""hit@5 for keyword and semantic search, per embedding model and corpus.
Drives idx_mcp.py over JSON-RPC exactly as the agent would.

usage: EMB_MODEL=<model> retrieval_eval.py   (indexes must exist: sbx/<repo>/<corpus>.<tag>.idx.sqlite)
"""
import json
import os
import pathlib
import re
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
QS = json.loads((HERE / "questions.json").read_text())
MODEL = os.environ.get("EMB_MODEL", "nomic-embed-text")
TAG = MODEL.replace(":", "-")
out = []
for corpus in ("code", "docs"):
    for tool in ("search_keyword", "search_semantic"):
        hits = 0
        for i, q in enumerate(QS):
            db = HERE / "sbx" / q["repo"] / f"{corpus}.{TAG}.idx.sqlite"
            msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                    {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                     "params": {"name": tool, "arguments": {"query": q["q"]}}}]
            r = subprocess.run(["python3", str(HERE / "idx_mcp.py"), str(db)],
                               input="\n".join(json.dumps(m) for m in msgs) + "\n",
                               capture_output=True, text=True, env={**os.environ, "EMB_MODEL": MODEL})
            text = json.loads(r.stdout.strip().split("\n")[-1])["result"]["content"][0]["text"]
            hit = bool(re.search(q["hit"], text))
            hits += hit
            out.append({"model": MODEL, "corpus": corpus, "tool": tool, "id": q["id"], "hit": hit})
        print(f"{MODEL:22} {corpus:5} {tool:16} hit@5 = {hits}/{len(QS)}")
with open(HERE / "retrieval_hits.jsonl", "a") as f:
    for row in out:
        f.write(json.dumps(row) + "\n")
