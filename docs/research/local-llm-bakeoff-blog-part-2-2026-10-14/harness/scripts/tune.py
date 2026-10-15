#!/usr/bin/env python3
"""Server-flag sweep. Usage: tune.py <model> "<args1>" "<args2>" ...   (each variant = extra llama-server args)
Per variant: start server, speed.py at TUNE_SIZES (default 4096,16384; pp16k column = second size) + decode, report GPU MiB, stop. Appends to results/tune-<model>.jsonl.
The server is always stopped (a crash used to leak it on :8080 and break the next queue step), and a failed request
or failed start is recorded as a row with err set instead of crashing."""
import sys, os, json, ast, subprocess, time
sys.path.insert(0, os.path.dirname(__file__))
from pipeline import start, sh, H
model = sys.argv[1]; variants = sys.argv[2:] or [""]
rnd = lambda x: round(x, 1) if x is not None else None
def record(rec):
    print(json.dumps(rec), flush=True)
    open(f"{H}/results/tune-{model}.jsonl", "a").write(json.dumps(rec) + "\n")
for i, v in enumerate(variants):
    tag = f"tune-{model}-{i}-{int(time.time()) % 100000}"; extra = v.split()
    print(f"=== {model} [{v or 'default'}]", flush=True)
    p, msg = start(model, extra, tag); print(" ", msg, flush=True)
    if not p:
        record(dict(model=model, args=v, gpu_mib=None, load=msg, pp4k=None, pp16k=None, tg=None, err="server did not start")); continue
    try:
        gpu = subprocess.run("nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits", shell=True, capture_output=True, text=True).stdout.strip()
        r = sh(f"python3 scripts/speed.py {tag} --conc 1 --sizes {os.environ.get('TUNE_SIZES', '4096,16384')}")  # real prompt tokens ~1.35x the size; keep size*1.35+200 < -c
        rows = [ast.literal_eval(l[len('prefill '):]) for l in r.stdout.splitlines() if l.startswith("prefill ")]
        good = [x for x in rows if x.get("tg_tps") is not None and not x.get("err")]
        errs = "; ".join(str(x["err"])[:120] for x in rows if x.get("err")) or r.stderr[-200:]
        if rows and len(good) == len(rows): errs = ""  # all requests answered: ignore stray stderr warnings
        record(dict(model=model, args=v, gpu_mib=gpu, load=msg, pp4k=rnd(rows[0]["pp_tps"]) if rows else None, pp16k=rnd(rows[1]["pp_tps"]) if len(rows) > 1 else None,
                    tg=rnd(sum(x["tg_tps"] for x in good) / len(good)) if good else None, err=errs))
    finally:
        p.terminate()
        try: p.wait(20)
        except Exception: p.kill()
        time.sleep(3)
