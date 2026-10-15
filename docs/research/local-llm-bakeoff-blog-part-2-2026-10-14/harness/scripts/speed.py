#!/usr/bin/env python3
"""Server-level speed: prefill (TTFT at several ctx sizes), decode tok/s, concurrency scaling.
Usage: speed.py <label> [--conc 1,2,4] -> results/speed-<label>.json"""
import sys, os, json, time, random, argparse, threading
sys.path.insert(0, os.path.dirname(__file__))
from lib import chat

WORDS = "engine cluster ledger kernel socket payload thread cache vector buffer router schema worker queue token window parser stream mutex shard index".split()
def doc(ntok, seed):
    r = random.Random(seed); n = int(ntok / 2.15)
    return " ".join(r.choice(WORDS) + str(r.randint(0, 99)) for _ in range(n))

def one(ntok, seed, gen=200):
    msgs = [{"role": "user", "content": doc(ntok, seed) + "\n\nIgnore the text above. Write a 300-word essay on the history of the printing press."}]
    r = chat(msgs, max_tokens=gen, think=False, temperature=0.7)
    return r

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("label"); ap.add_argument("--conc", default="1,2,4"); ap.add_argument("--sizes", default="512,4096,16384"); a = ap.parse_args()
    out = dict(label=a.label, prefill=[], concurrency=[])
    one(256, 1, 16)  # warm
    for sz in [int(x) for x in a.sizes.split(",")]:
        r = one(sz, random.randint(0, 1 << 30))
        pt = r.get("prompt_tokens") or sz
        out["prefill"].append(dict(ctx=sz, prompt_tokens=pt, ttft=r.get("ttft"), pp_tps=(pt / r["ttft"]) if r.get("ttft") else None, tg_tps=r.get("tps"), err=r.get("error")))
        print("prefill", out["prefill"][-1], flush=True)
    for c in [int(x) for x in a.conc.split(",")]:
        res = []; th = []
        def w(i): res.append(one(1024, 1000 + i, 200))
        t0 = time.time()
        for i in range(c): t = threading.Thread(target=w, args=(i,)); t.start(); th.append(t)
        for t in th: t.join()
        wall = time.time() - t0; toks = sum(x.get("comp_tokens") or 0 for x in res); errs = [x["error"] for x in res if x.get("error")]
        out["concurrency"].append(dict(conc=c, agg_tps=toks / wall, per_req_tps=[x.get("tps") for x in res], errors=errs))
        print("conc", out["concurrency"][-1], flush=True)
    json.dump(out, open(os.path.expanduser(f"~/llm-bench/results/speed-{a.label}.json"), "w"), indent=1)
if __name__ == "__main__": main()
