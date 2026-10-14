#!/usr/bin/env python3
"""Coding-finals comparison table from results/code-*.json + results/regrade.json.
Per-task denominators = max hidden-test count seen for that task (collection errors count as 0 of N)."""
import glob, json, os
R = os.path.expanduser("~/llm-bench/results")
rg = json.load(open(f"{R}/regrade.json"))
den = {}
for ts in rg.values():
    for t, v in ts.items():
        if v: den[t] = max(den.get(t, 0), v["passed"] + v["failed"] + v["error"])
rows = []
for f in sorted(glob.glob(f"{R}/code-*.json")):
    d = json.load(open(f)); lab = d["label"]; ts = rg.get(lab)
    toks = sum(t.get("comp_tokens") or 0 for t in d["tasks"]); errs = sum(1 for t in d["tasks"] if t.get("error"))
    if ts:
        fr = [(ts[t["task"]]["passed"] / den[t["task"]]) if ts.get(t["task"]) else 0.0 for t in d["tasks"]]
        asserts = sum(ts[t]["passed"] for t in ts if ts[t]); tot = sum(den[t["task"]] for t in d["tasks"] if t["task"] in den)
        rows.append((lab, d["passed"], d["total"], sum(fr) / len(fr), asserts, tot, d["wall"], toks, errs))
    else:
        rows.append((lab, d["passed"], d["total"], None, None, None, d["wall"], toks, errs))
rows.sort(key=lambda r: (-(r[3] or 0), -r[1]))
print(f"{'label':36} {'full':>6} {'mean-frac':>9} {'asserts':>11} {'wall(s)':>8} {'tokens':>8} {'errs':>4}")
for lab, p, n, mf, a, tot, w, tk, e in rows:
    print(f"{lab:36} {p:>3}/{n:<2} {('%.3f' % mf) if mf is not None else '   n/a':>9} {(f'{a}/{tot}') if a is not None else 'n/a':>11} {w:>8.0f} {tk:>8} {e:>4}")
