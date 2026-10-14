#!/usr/bin/env python3
"""Stage-2: per model start server, run agentic code suite (+ optional dr). Usage: finals.py parts model[,model] [-- extra server args]"""
import sys, subprocess, os, time
sys.path.insert(0, os.path.dirname(__file__))
from pipeline import start, sh, H
parts = sys.argv[1].split(","); names = sys.argv[2].split(","); extra = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
tag_sfx = os.environ.get("TAG", "llamacpp"); think = os.environ.get("THINK", "default")
for n in names:
    tag = f"{n}-{tag_sfx}"; print(f"=== {tag}", flush=True)
    p, msg = start(n, extra, tag + "-fin"); print(" ", msg, flush=True)
    if not p: continue
    if "code" in parts:
        r = sh(f"python3 scripts/agent_code.py {tag} --think {think}"); print(r.stdout[-1800:], r.stderr[-300:], flush=True)
    if "dr" in parts:
        r = sh(f"python3 finals/dr/dr_eval.py {tag} --think {think}"); print(r.stdout[-2500:], r.stderr[-300:], flush=True)
    p.terminate()
    try: p.wait(15)
    except Exception: p.kill()
