#!/usr/bin/env python3
"""llama-swap test: start it on :8100 with llama-swap.yaml, hit each model id (cold load, swap, swap back), record latency + decode tok/s, check /running, run the smoke suite through it."""
import json, os, subprocess, sys, time, urllib.request
H = os.path.expanduser("~/llm-bench"); PORT = 8100
os.environ["LLM_BASE"] = f"http://127.0.0.1:{PORT}/v1"
sys.path.insert(0, H + "/scripts")
import lib
log = open(f"{H}/logs/llama-swap-test.log", "w")
p = subprocess.Popen([H + "/tools/llama-swap-v265/bin/llama-swap", "-config", H + "/llama-swap.yaml", "-listen", f"127.0.0.1:{PORT}"], stdout=log, stderr=subprocess.STDOUT)
def get(path):
    return json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=10))
out = dict(steps=[])
try:
    for _ in range(60):
        try: urllib.request.urlopen(f"http://127.0.0.1:{PORT}/v1/models", timeout=2); break
        except Exception: time.sleep(1)
    out["models"] = [m["id"] for m in get("/v1/models")["data"]]
    for mid in ["qwen38", "gptoss20b", "qwen36-35b", "qwen38", "qwen38"]:
        lib.MODEL = mid; t0 = time.time()
        r = lib.chat([{"role": "user", "content": "Write a 120-word summary of how a hash map handles collisions."}], max_tokens=400, think=False, temperature=0.3)
        run = get("/running")
        out["steps"].append(dict(model=mid, wall=round(time.time() - t0, 1), ttft=round(r.get("ttft") or -1, 1), tps=round(r.get("tps") or 0, 1), err=r.get("error"), running=[x.get("model") for x in run.get("running", [])]))
        print(out["steps"][-1], flush=True)
    lib.MODEL = "qwen38"
    sm = subprocess.run(["python3", H + "/scripts/smoke.py", "swap-qwen38"], capture_output=True, text=True, cwd=H, env=dict(os.environ, LLM_BASE=os.environ["LLM_BASE"], LLM_MODEL="qwen38"))
    out["smoke_tail"] = sm.stdout[-400:]; print(sm.stdout[-400:], flush=True)
finally:
    p.terminate()
    try: p.wait(30)
    except Exception: p.kill()
    subprocess.run("pkill -f 'llama-server.*--port 5[0-9][0-9][0-9][0-9]'", shell=True)  # swap-assigned ports
json.dump(out, open(f"{H}/results/llama-swap-test.json", "w"), indent=1)
