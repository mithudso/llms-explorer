#!/usr/bin/env python3
"""Grade results.jsonl against questions.json and print the tables used in the post.

Correct = every grading regex for the question matches the answer (case-insensitive).
Cost is Claude Code's total_cost_usd (API list prices, cache reads/writes priced as billed).
"""
import collections
import json
import pathlib
import re
import statistics as st
import sys

HERE = pathlib.Path(__file__).resolve().parent
QS = {q["id"]: q for q in json.loads((HERE / "questions.json").read_text())}
rows = [json.loads(l) for l in open(HERE / (sys.argv[1] if len(sys.argv) > 1 else "results.jsonl"))]
OVERRIDES = {}  # (id, cond, rep) -> bool, filled after hand review
ov = HERE / "grade_overrides.json"
if ov.exists():
    OVERRIDES = {tuple(k.split("|")[:2]) + (int(k.split("|")[2]),): v for k, v in json.loads(ov.read_text()).items()}

for r in rows:
    q = QS[r["id"]]
    auto = r["ok"] and all(re.search(p, r["answer"], re.I) for p in q["grade"])
    r["correct"] = OVERRIDES.get((r["id"], r["cond"], r["rep"]), auto)
    r["auto"] = auto
    r["tokens"] = r["input"] + r["cache_create"] + r["cache_read"] + r["output"]
    r["in_docs"] = q["in_docs"]

NAMES = {"A": "code only", "B": "docs on disk", "C": "docs + llms on disk", "D": "docs on disk + index",
         "E": "code + index", "G": "docs + CLAUDE.md loaded", "H": "docs + CLAUDE.md + index",
         "I": "llms + CLAUDE.md pointer"}
CONDS = "ABCDEGHI"  # F excluded: --restricted never loads CLAUDE.md, so its pointer was invisible (F == C)


def table(sel, title):
    print(f"\n### {title}")
    print("| Cond | Setup | n | Correct | Mean $ | vs A | $ per correct | Mean tokens | fresh in | cache write | cache read | out | turns | wall s |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    base = None
    for c in CONDS:
        rs = [r for r in sel if r["cond"] == c and r["ok"]]
        if not rs:
            continue
        n = len(rs)
        ok = sum(r["correct"] for r in rs)
        cost = sum(r["cost_usd"] for r in rs)
        m = lambda k: st.mean(r[k] for r in rs)
        if c == "A":
            base = cost / n
        rel = f"{(cost/n)/base-1:+.0%}" if base else "—"
        print(f"| {c} | {NAMES[c]} | {n} | {ok}/{n} ({ok/n:.0%}) | {cost/n:.4f} | {rel} | "
              f"{(cost/ok if ok else float('nan')):.4f} | {m('tokens'):,.0f} | {m('input'):,.0f} | {m('cache_create'):,.0f} | "
              f"{m('cache_read'):,.0f} | {m('output'):,.0f} | {m('turns'):.1f} | {m('wall_s'):.0f} |")


for r in rows:
    r["kind"] = QS[r["id"]].get("kind", "lookup")
table([r for r in rows if r["kind"] == "lookup"], "Lookup questions (12), both repos")
table([r for r in rows if r["kind"] == "comprehension"], "Comprehension questions (4), both repos")
for repo in ("llm-cache-proxy", "llm-memory-pyramid"):
    table([r for r in rows if r["repo"] == repo and r["kind"] == "lookup"], f"{repo}, lookup")
table([r for r in rows if r["in_docs"] and r["kind"] == "lookup"], "Lookup, answer also in the docs (10)")
table([r for r in rows if not r["in_docs"]], "Lookup, answer only in code (M2, M5)")

print("\n### Behavior")
for c in CONDS:
    rs = [r for r in rows if r["cond"] == c and r["ok"]]
    if not rs:
        continue
    llms_read = sum(any(p.split("/")[-1].startswith("llms") for p in r["reads"]) for r in rs)
    idx = sum(sum(v for k, v in r["tools"].items() if k.startswith("mcp__")) for r in rs)
    reads = st.mean(len(r["reads"]) for r in rs)
    tool_mix = collections.Counter()
    for r in rs:
        tool_mix.update(r["tools"])
    print(f"{c}: runs={len(rs)} mean Read calls={reads:.1f} runs reading an llms file={llms_read} "
          f"index calls={idx} tool mix={dict(tool_mix)}")

print("\n### Per question: correct runs out of 2, mean $")
print("| Q | in docs | " + " | ".join(c for c in CONDS) + " |")
print("|---|---|" + "---|" * len(CONDS))
for qid in QS:
    cells = []
    for c in CONDS:
        rs = [r for r in rows if r["id"] == qid and r["cond"] == c and r["ok"]]
        cells.append(f"{sum(r['correct'] for r in rs)}/{len(rs)} ${st.mean(r['cost_usd'] for r in rs):.3f}" if rs else "–")
    print(f"| {qid} | {'yes' if QS[qid]['in_docs'] else 'no'} | " + " | ".join(cells) + " |")

bad = [r for r in rows if not r["ok"]]
print(f"\nfailed runs (no result): {len(bad)}")
print("auto-graded incorrect, for hand review:")
for r in rows:
    if r["ok"] and not r["auto"]:
        print(f"  {r['id']} {r['cond']} r{r['rep']}: {r['answer'][:260]!r}")
