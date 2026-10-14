#!/usr/bin/env python3
"""Print the fastest working server-arg string for <model> from results/tune-<model>.jsonl (nothing if none qualifies).
Usage: pickcfg.py <model> [min_tps=20] [min_ctx=0]. Ignores rows with err, tg below min_tps (e.g. the CPU-offload rows from the
first Qwen3.8 sweep) or a -c value below min_ctx."""
import json, os, re, sys
model = sys.argv[1]; MIN_TPS = float(sys.argv[2]) if len(sys.argv) > 2 else 20.0; MIN_CTX = int(sys.argv[3]) if len(sys.argv) > 3 else 0
p = os.path.expanduser(f"~/llm-bench/results/tune-{model}.jsonl")
rows = [json.loads(l) for l in open(p)] if os.path.exists(p) else []
ctx = lambda a: int((re.findall(r"-c (\d+)", a) or ["0"])[-1])
ok = [r for r in rows if r.get("tg") and r["tg"] >= MIN_TPS and not r.get("err") and ctx(r["args"]) >= MIN_CTX]
if ok: print(max(ok, key=lambda r: r["tg"])["args"])
