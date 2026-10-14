#!/usr/bin/env python3
"""Stability soak. Usage: soak.py <label> <base_url> <model_id> [minutes=30]
Two workers send a random mix (short chat, ~10k-token prefill, JSON output, tool call) for the duration. Every 60 s logs GPU MiB and total llama-server RSS.
Writes results/soak-<label>.json: error count, decode tok/s early vs late, GPU and RSS drift. A tool-call request counts as ok only if a tool call comes back."""
import json, os, random, subprocess, sys, threading, time
label, base, model = sys.argv[1:4]; minutes = float(sys.argv[4]) if len(sys.argv) > 4 else 30
os.environ["LLM_BASE"] = base; H = os.path.expanduser("~/llm-bench"); sys.path.insert(0, H + "/scripts")
import lib
lib.MODEL = model
WORDS = "engine cluster ledger kernel socket payload thread cache vector buffer router schema worker queue token window parser stream mutex shard index".split()
def doc(n, seed): r = random.Random(seed); return " ".join(r.choice(WORDS) + str(r.randint(0, 99)) for _ in range(int(n / 2.9)))
TOOL = [{"type": "function", "function": {"name": "get_weather", "description": "Get the weather for a city", "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}]
def kinds(i):
    return {
     "short": lambda: lib.chat([{"role": "user", "content": f"Explain in about 100 words how a B-tree stays balanced. (variant {i})"}], max_tokens=300, think=False, temperature=0.5),
     "prefill": lambda: lib.chat([{"role": "user", "content": doc(10000, i) + "\n\nIgnore the text above and list three uses of a mutex in two sentences."}], max_tokens=150, think=False, temperature=0.3),
     "json": lambda: lib.chat([{"role": "user", "content": 'Return ONLY JSON {"items":[{"name":str,"why":str}]} with 5 sibling concepts of "speculative decoding".'}], max_tokens=600, think=False, temperature=0.3),
     "tool": lambda: lib.chat([{"role": "user", "content": "What is the weather in Lisbon right now? Use the tool."}], tools=TOOL, max_tokens=200, think=False, temperature=0.1),
    }
rows = []; lock = threading.Lock(); t_end = time.time() + minutes * 60; t_start = time.time(); n = [0]
def worker():
    while time.time() < t_end:
        with lock: n[0] += 1; i = n[0]
        kind = random.choice(["short", "short", "prefill", "json", "tool"]); t0 = time.time()
        try: r = kinds(i)[kind]()
        except Exception as e: r = {"error": repr(e)}
        ok = not r.get("error") and (bool(r.get("tool_calls")) if kind == "tool" else bool((r.get("content") or "").strip()))
        with lock: rows.append(dict(t=time.time() - t_start, kind=kind, ok=ok, wall=time.time() - t0, tps=r.get("tps"), ttft=r.get("ttft"), err=r.get("error")))
samples = []
def sampler():
    while time.time() < t_end:
        g = subprocess.run("nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits", shell=True, capture_output=True, text=True).stdout.strip()
        rss = subprocess.run("ps -C llama-server -o rss= | awk '{s+=$1} END {print s/1024}'", shell=True, capture_output=True, text=True).stdout.strip()
        samples.append(dict(t=time.time() - t_start, gpu_mib=int(g or 0), rss_mib=float(rss or 0))); time.sleep(60)
ths = [threading.Thread(target=worker) for _ in range(2)] + [threading.Thread(target=sampler)]
for t in ths: t.start()
for t in ths: t.join()
mean = lambda xs: round(sum(xs) / len(xs), 1) if xs else None
half = lambda f: [x["tps"] for x in rows if x["kind"] in ("short", "json") and x["tps"] and f(x["t"])]
res = dict(label=label, model=model, minutes=minutes, requests=len(rows), errors=sum(1 for x in rows if not x["ok"]), by_kind={k: [sum(1 for x in rows if x["kind"] == k), sum(1 for x in rows if x["kind"] == k and not x["ok"])] for k in ("short", "prefill", "json", "tool")},
           tps_first_third=mean(half(lambda t: t < minutes * 20)), tps_last_third=mean(half(lambda t: t > minutes * 40)), gpu_mib_first=samples[0]["gpu_mib"] if samples else None, gpu_mib_last=samples[-1]["gpu_mib"] if samples else None,
           gpu_mib_max=max((s["gpu_mib"] for s in samples), default=None), rss_mib_first=samples[0]["rss_mib"] if samples else None, rss_mib_last=samples[-1]["rss_mib"] if samples else None,
           error_samples=[x["err"] for x in rows if not x["ok"]][:5], samples=samples)
json.dump(res, open(f"{H}/results/soak-{label}.json", "w"), indent=1)
print({k: v for k, v in res.items() if k != "samples"})
