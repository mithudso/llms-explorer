#!/usr/bin/env python3
"""Per-concept "where did it land" receipts for become-expert and concept-family-explorer.

One JSONL file per run: <run-dir>/landing-receipts.jsonl (append-only, last row per
concept wins). Stdlib only; no network, no cost of its own.

  landing_receipts.py add   <run-dir> <concept> [--path ABS ...] [--kept N] [--dropped N]
                            [--gate PASS|FAIL|NOT-RUN|DISSENT] [--cost-usd X]
                            [--skipped "reason"] [--note TEXT]
  landing_receipts.py table <run-dir>        print the final table (Markdown) and exit 2 if any row is incomplete
  landing_receipts.py check <run-dir>        same checks, no table

A row is complete when it has at least one absolute output path that exists on disk, or an
explicit --skipped reason; and a gate verdict (NOT-RUN is a valid, honest verdict).
Exit codes: 0 ok, 2 incomplete rows or bad input.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

VERDICTS = {"PASS", "FAIL", "NOT-RUN", "DISSENT"}


def load(run: Path) -> dict[str, dict]:
    f = run / "landing-receipts.jsonl"
    rows: dict[str, dict] = {}
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "concept" in r:
                prev = rows.get(r["concept"], {})
                paths = list(dict.fromkeys(prev.get("paths", []) + r.get("paths", [])))
                rows[r["concept"]] = {**prev, **{k: v for k, v in r.items() if v not in (None, [])}, "paths": paths}
    return rows


def problems(row: dict) -> list[str]:
    out = []
    paths = row.get("paths", [])
    if not paths and not row.get("skipped"):
        out.append("no output path and no skipped reason")
    for p in paths:
        if not p.startswith("/"):
            out.append(f"relative path {p}")
        elif not Path(p).exists():
            out.append(f"missing on disk {p}")
    if row.get("gate") not in VERDICTS:
        out.append("no gate verdict")
    return out


def cmd_add(a) -> int:
    run = Path(a.run_dir)
    run.mkdir(parents=True, exist_ok=True)
    if a.gate and a.gate not in VERDICTS:
        print(f"gate must be one of {sorted(VERDICTS)}", file=sys.stderr)
        return 2
    row = {"concept": a.concept, "paths": [str(Path(p)) for p in (a.path or [])],
           "claims_kept": a.kept, "claims_dropped": a.dropped, "gate": a.gate,
           "cost_usd": a.cost_usd, "skipped": a.skipped, "note": a.note}
    with open(run / "landing-receipts.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps({k: v for k, v in row.items() if v not in (None, [], "")}, ensure_ascii=False) + "\n")
    return 0


def cmd_table(a) -> int:
    rows = load(Path(a.run_dir))
    if not rows:
        print("no receipts recorded: this run left nothing that landed", file=sys.stderr)
        return 2
    bad = 0
    if a.cmd == "table":
        print("| concept | gate | kept | dropped | cost USD | landed at |")
        print("|---|---|---|---|---|---|")
    total = 0.0
    for c, r in rows.items():
        probs = problems(r)
        bad += bool(probs)
        total += float(r.get("cost_usd") or 0)
        if a.cmd == "table":
            land = "<br>".join(r.get("paths", [])) or f"skipped: {r.get('skipped', '?')}"
            flag = f" **INCOMPLETE: {'; '.join(probs)}**" if probs else ""
            print(f"| {c} | {r.get('gate', '?')} | {r.get('claims_kept', '-')} | {r.get('claims_dropped', '-')} "
                  f"| {float(r.get('cost_usd') or 0):.2f} | {land}{flag} |")
        elif probs:
            print(f"{c}: {'; '.join(probs)}")
    if a.cmd == "table":
        print(f"\n{len(rows)} concepts, ${total:.2f} total, {bad} incomplete.")
    return 2 if bad else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("add")
    s.add_argument("run_dir"); s.add_argument("concept")
    s.add_argument("--path", action="append"); s.add_argument("--kept", type=int)
    s.add_argument("--dropped", type=int); s.add_argument("--gate")
    s.add_argument("--cost-usd", type=float); s.add_argument("--skipped"); s.add_argument("--note")
    s.set_defaults(fn=cmd_add)
    for n in ("table", "check"):
        t = sub.add_parser(n); t.add_argument("run_dir"); t.set_defaults(fn=cmd_table)
    a = p.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
