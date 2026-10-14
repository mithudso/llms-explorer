#!/usr/bin/env python3
"""Tabulate /dr eval results. Usage: dr_summary.py [results/dr-*.json ...]"""
import glob, json, os, sys
R = os.path.expanduser("~/llm-bench/results")
files = sys.argv[1:] or sorted(glob.glob(f"{R}/dr-*.json"))
def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else float("nan")
print(f"{'label':36} {'claims ok/gnd/inj/cov':22} {'qa ok/cite/hal':16} {'rabbit valid/correct':20} {'cfe ok/cov/dup':16} wall(c,q,r,f)")
for f in files:
    d = json.load(open(f)); c = d.get("claims") or []; q = d.get("qa") or []; r = d.get("rabbit") or []; x = d.get("cfe") or []
    cl = f"{sum(1 for k in c if k.get('valid_json'))}/{len(c)} {mean([k.get('grounded') for k in c]):.2f} {sum(1 for k in c if k.get('injection_followed'))} {mean([k.get('coverage') for k in c]):.2f}" if c else "-"
    qs = f"{sum(k['correct'] for k in q)}/{len(q)} {sum(k['cited_source'] for k in q)} {sum(k['halluc_urls'] for k in q)}" if q else "-"
    rs = f"{sum(1 for k in r if k.get('valid'))}/{len(r)} {sum(1 for k in r if k.get('correct'))}" if r else "-"
    cf = f"{sum(1 for k in x if k.get('valid') and k.get('min_ok'))}/{len(x)} {mean([k.get('coverage') for k in x]):.2f} {sum(k.get('dups', 0) for k in x)}" if x else "-"
    wl = ",".join(f"{d.get(k, 0):.0f}" for k in ("claims_wall", "qa_wall", "rabbit_wall", "cfe_wall"))
    print(f"{d['label']:36} {cl:22} {qs:16} {rs:20} {cf:16} {wl}")
