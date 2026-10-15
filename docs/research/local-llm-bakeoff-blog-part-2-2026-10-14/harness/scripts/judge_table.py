#!/usr/bin/env python3
"""Aggregate blind-judge verdicts by model group using the sealed key. Usage: judge_table.py [judge-dir=judge] [key=judge-key-v2.json]"""
import json, os, sys, collections
H = os.path.expanduser("~/llm-bench"); jd = H + "/" + (sys.argv[1] if len(sys.argv) > 1 else "judge"); key = json.load(open(H + "/" + (sys.argv[2] if len(sys.argv) > 2 else "judge-key-v2.json")))
groups = sorted({v["group"] for v in key.values()})
def mean(xs): return sum(xs) / len(xs) if xs else float("nan")
def table(item, fields):
    p = f"{jd}/{item}/verdict.json"
    if not os.path.exists(p): print(f"{item}: no verdict yet"); return
    d = json.load(open(p))["outputs"]; acc = collections.defaultdict(lambda: collections.defaultdict(list))
    for oid, v in d.items():
        g = key[oid]["group"]
        for f in fields:
            x = v.get(f)
            if x is None and f == "score": x = v.get("overall")  # some judges named the 1-10 score "overall"
            if isinstance(x, (int, float)): acc[g][f].append(x)
    print(f"\n{item}  (mean over {len(d)//len(groups)} seeds per group)")
    print(f"{'group':8}" + "".join(f"{f[:16]:>18}" for f in fields))
    for g in sorted(groups, key=lambda g: -mean(acc[g][fields[-1]])):
        print(f"{g:8}" + "".join(f"{mean(acc[g][f]):18.2f}" for f in fields))
    rk = json.load(open(p)).get("ranking") or []
    pos = collections.defaultdict(list)
    for i, oid in enumerate(rk): pos[key[oid]["group"]].append(i + 1)
    print("  mean rank (1=best of %d): " % len(rk) + ", ".join(f"{g} {mean(pos[g]):.1f}" for g in sorted(groups, key=lambda g: mean(pos[g]))))
for c in ("claims0", "claims1", "claims2"): table(c, ["n_claims", "n_unsupported", "n_number_errors", "key_points_covered", "score"])
table("cfe", ["n_distinct", "n_fabricated_or_wrong", "specificity", "expert_coverage", "score"])
table("qa", ["n_correct", "n_grounded", "n_invented", "overall"])
