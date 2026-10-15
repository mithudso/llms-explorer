#!/usr/bin/env python3
# ruff: noqa: E501
"""dr_haiku_repeats.py — how many repeated Haiku 5.5 /dr runs equal one Fable 5.1 run?

Reuses scripts/dr_model_matrix.py: same concept ("SQLite WAL checkpointing"), the identical
dr_run.py worker brief, one isolated HUB_DIR per cell, and the same fixed blind gate
(Opus 5.5 medium). This harness adds repeat-suffixed Haiku cells and three scoring steps:

  run     N fresh Haiku cells per effort level, in parallel (each is one `claude -p`).
  score   For each effort: union the N claims files; one Opus 5.5 medium judge call (no tools)
          maps every Fable claim to the union (covered / partial / missing, by which union
          claims) and clusters duplicate union claims. From that single judgment the script
          computes, for k = 1..N, the mean over every k-subset of runs of: union sources,
          unique claims, Fable claims covered. Then the fixed gate verdicts EVERY non-tentative
          claim of the deduped k=N union, of each single first run, and of the Fable reference.
  report  Writes results.json and results.md.

    python3 scripts/dr_haiku_repeats.py run [--efforts medium,max] [--repeats 5] [--parallel 10]
    python3 scripts/dr_haiku_repeats.py score [--efforts medium,max]
    python3 scripts/dr_haiku_repeats.py report
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import shutil
import statistics
import sys

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dr_model_matrix as mx  # noqa: E402

REPO = mx.REPO
OUT = REPO / "docs" / "research" / "dr-haiku-repeats-2026-10-15"
MATRIX_CELLS = mx.OUT / "cells"
REF_ID = "claude__claude-fable-5-1__max"
MODEL = "claude-haiku-5-5"
JUDGE = ("claude-opus-5-5", "medium")
CLAIMS_REL = Path("hub") / "research" / "bench" / "claims" / "sqlite-wal-checkpointing.json"

# Point the matrix harness at this experiment's directory (run_cell reads these at call time).
mx.OUT = OUT
mx.CELLS_DIR = OUT / "cells"
mx.RESULTS = OUT / "results.jsonl"


def _cells(efforts: list[str], repeats: int) -> list[dict]:
    return [
        {
            "lane": "claude",
            "model": MODEL,
            "effort": e,
            "repeat": r,
            "id": f"claude__{MODEL}__{e}__r{r}",
        }
        for e in efforts
        for r in range(1, repeats + 1)
    ]


def _load(p: Path) -> dict:
    return json.loads(p.read_text())


def _norm_url(u: str) -> str:
    u = u.strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    u = u.split("#", 1)[0]
    return u.rstrip("/")


def _org(u: str) -> str:
    host = _norm_url(u).split("/", 1)[0]
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def _reference() -> dict:
    ref_dir = OUT / "reference"
    ref_dir.mkdir(parents=True, exist_ok=True)
    dst = ref_dir / "fable-max.claims.json"
    if not dst.exists():
        shutil.copy(MATRIX_CELLS / REF_ID / CLAIMS_REL, dst)
        shutil.copy(MATRIX_CELLS / REF_ID / "result.json", ref_dir / "fable-max.result.json")
    return _load(dst)


# --------------------------------------------------------------------------- run ------------
def cmd_run(a) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    mx.AGENT_TIMEOUT = a.agent_timeout
    cells = _cells(a.efforts.split(","), a.repeats)
    if a.only:
        cells = [c for c in cells if c["id"] in a.only]
    with ThreadPoolExecutor(max_workers=a.parallel) as pool:
        for r in pool.map(lambda c: mx._safe(c, a.force), cells):
            print(
                json.dumps(
                    {
                        k: r.get(k)
                        for k in (
                            "id",
                            "status",
                            "claims",
                            "claim_sources",
                            "gate_supported_rate",
                        )
                    }
                    | {"cost": (r.get("research") or {}).get("cost_usd")}
                ),
                flush=True,
            )
    return 0


# --------------------------------------------------------------------------- score ----------
JUDGE_PROMPT = """You are a careful, literal fact comparator. No tools. Output JSON only.

Two sets of research claims about the same concept, "{concept}".
Set F (reference, {nf} claims) and set H (candidate union of {nruns} independent runs, {nh} claims;
each H claim is tagged with its run number).

TASK 1 — coverage. For EVERY F claim decide whether the H set states the same fact:
  "covered"  = at least one H claim states the same fact with the same specifics (numbers,
               versions, names, conditions). List every such H id.
  "partial"  = H states a weaker, narrower, or less specific version of it. List those H ids.
  "missing"  = nothing in H states it.
Judge by what the sentences assert, not by shared keywords. A claim that merely mentions the
same topic is not covered.

TASK 2 — clustering. Group the H claims into clusters that state the SAME fact (same specifics;
a restatement in different words counts, a different number or condition does not). Every H id
appears in exactly one cluster; singletons are clusters of one. Pick as "rep" the member whose
wording is most complete and precise.

TASK 3 — extras. List every cluster (by rep id) that states a fact NO F claim states or covers
(i.e. the candidate found something the reference did not).

Output exactly this JSON and nothing else:
{{"coverage": [{{"f": "F1", "status": "covered|partial|missing", "by": ["H3"]}}, ...],
 "clusters": [{{"rep": "H1", "members": ["H1", "H14"]}}, ...],
 "extras": ["H7", ...]}}

SET F:
{fset}

SET H:
{hset}
"""


def _judge(effort: str, ref: dict, union: list[dict], force: bool) -> dict:
    sd = OUT / "score" / effort
    sd.mkdir(parents=True, exist_ok=True)
    jp = sd / "judge.json"
    if jp.exists() and not force:
        return _load(jp)
    fset = "\n".join(f"F{i + 1}: {c['text']}" for i, c in enumerate(ref["claims"]))
    hset = "\n".join(f"{h['id']} (run {h['run']}): {h['text']}" for h in union)
    prompt = JUDGE_PROMPT.format(
        concept=mx.CONCEPT,
        nf=len(ref["claims"]),
        nruns=len({h["run"] for h in union}),
        nh=len(union),
        fset=fset,
        hset=hset,
    )
    (sd / "judge-prompt.md").write_text(prompt)
    out = mx._claude(
        prompt, JUDGE[0], JUDGE[1], sd, sd / "hub", tools="", allowed="", max_turns=1, timeout=1800
    )
    raw = out.get("result") or ""
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        verdict = json.loads(m.group(0)) if m else None
    except json.JSONDecodeError:
        verdict = None
    rec = {
        "model": "/".join(JUDGE),
        "cost_usd": out.get("cost_usd"),
        "tokens": out.get("tokens"),
        "seconds": out.get("seconds"),
        "is_error": out.get("is_error") or verdict is None,
        "raw": raw[-3000:] if verdict is None else None,
        "verdict": verdict,
    }
    jp.write_text(json.dumps(rec, indent=1) + "\n")
    return rec


def _subset_means(
    runs: list[int], per_run_sources: dict, cov_runs: list[set], clus_runs: list[set]
):
    """For k=1..N: mean over every k-subset of (union sources, unique claims, covered F claims)."""
    rows = []
    for k in range(1, len(runs) + 1):
        src, uniq, cov, orgs = [], [], [], []
        for S in itertools.combinations(runs, k):
            s = set()
            for r in S:
                s |= per_run_sources[r]
            src.append(len(s))
            orgs.append(len({_org(u) for u in s}))
            uniq.append(sum(1 for cr in clus_runs if cr & set(S)))
            cov.append(sum(1 for fr in cov_runs if fr & set(S)))
        rows.append(
            {
                "k": k,
                "subsets": len(src),
                "sources_mean": round(statistics.mean(src), 1),
                "sources_min": min(src),
                "sources_max": max(src),
                "orgs_mean": round(statistics.mean(orgs), 1),
                "unique_claims_mean": round(statistics.mean(uniq), 1),
                "unique_claims_min": min(uniq),
                "unique_claims_max": max(uniq),
                "fable_covered_mean": round(statistics.mean(cov), 1),
                "fable_covered_min": min(cov),
                "fable_covered_max": max(cov),
            }
        )
    return rows


def _full_gate(name: str, doc: dict, force: bool) -> dict:
    """Fixed gate over every non-tentative claim: a throwaway saturate-depth run whose only
    content is `doc`, so the gate's default sample is `all`."""
    gd = OUT / "gates" / name
    rp = gd / "gate-result.json"
    if rp.exists() and not force:
        cached = _load(rp)
        if not cached.get("is_error"):
            return cached
    if gd.exists():
        shutil.rmtree(gd)
    hub = gd / "hub"
    hub.mkdir(parents=True)
    mx._dr(
        hub, "init", mx.TOPIC, "--slug", mx.SLUG, "--depth", "saturate", "--concepts", mx.CONCEPT
    )
    cp = gd / "claims.json"
    cp.write_text(json.dumps(doc, indent=1) + "\n")
    done = mx._dr(hub, "concept-done", mx.SLUG, str(cp))
    rec = {"name": name, "claims": len(doc["claims"]), "concept_done": done}
    if not done.get("ok"):
        rec["is_error"] = True
        rp.write_text(json.dumps(rec, indent=1) + "\n")
        return rec
    g = mx._dr(
        hub,
        "gate",
        mx.SLUG,
        "--model",
        JUDGE[0],
        "--effort",
        JUDGE[1],
        "--sample",
        "all",
        "--refetch-cap",
        "60",
        "--agent-timeout",
        "2700",
        timeout=3000,
    )
    rec.update({k: g.get(k) for k in ("counts", "cost_usd", "tokens", "seconds", "error")})
    try:
        rec["verdicts"] = _load(mx._run_dir(hub) / "gate.json").get("verdicts")
    except (OSError, json.JSONDecodeError):
        rec["verdicts"] = None
    rp.write_text(json.dumps(rec, indent=1) + "\n")
    return rec


def _dedup_union(base: dict, union: list[dict], clusters: list[dict], run_docs: dict) -> dict:
    """One claims doc holding one representative per cluster, sources merged across members.
    URLs are canonicalised to the first-seen spelling so claims[].sources match sources[].url
    exactly, which dr_run.py's validator requires."""
    by_id = {h["id"]: h for h in union}
    canon: dict[str, str] = {}
    src_meta: dict[str, dict] = {}
    for d in run_docs.values():
        for s in d.get("sources", []):
            key = _norm_url(s["url"])
            canon.setdefault(key, s["url"])
            src_meta.setdefault(key, dict(s, url=canon[key]))
    rank = {"high": 2, "medium": 1, "low": 0}
    claims, used = [], set()
    for cl in clusters:
        members = [by_id[m] for m in cl["members"] if m in by_id]
        if not members:
            continue
        rep = by_id.get(cl.get("rep")) or members[0]
        keys: list[str] = []
        for m in members:
            for u in m["sources"]:
                k = _norm_url(u)
                if k in canon and k not in keys:
                    keys.append(k)
        if not keys:
            continue
        claim = {k: v for k, v in rep.items() if k not in ("id", "run")}
        claim["sources"] = [canon[k] for k in keys]
        claim["confidence"] = max((m["confidence"] for m in members), key=lambda c: rank.get(c, 0))
        claim["volatile"] = any(m.get("volatile") for m in members)
        if claim["volatile"] and not claim.get("verified_as_of"):
            claim["verified_as_of"] = next(
                (m["verified_as_of"] for m in members if m.get("verified_as_of")), None
            )
            if not claim["verified_as_of"]:
                claim["volatile"] = False
        claims.append(claim)
        used.update(keys)
    doc = dict(base)
    doc["claims"] = claims
    doc["sources"] = [src_meta[k] for k in used]
    return doc


def _tentative_free(doc: dict) -> int:
    return sum(1 for c in doc["claims"] if c.get("confidence") != "low")


def cmd_score(a) -> int:
    ref = _reference()
    report = {
        "reference": {"id": REF_ID, "claims": len(ref["claims"]), "sources": len(ref["sources"])}
    }
    gate_jobs: list[tuple[str, dict]] = [("fable-max", ref)]
    per_effort: dict[str, dict] = {}
    for effort in a.efforts.split(","):
        cells = sorted(
            (
                c
                for c in (OUT / "cells").glob(f"claude__{MODEL}__{effort}__r*")
                if (c / "result.json").exists()
            ),
            key=lambda p: int(p.name.rsplit("r", 1)[1]),
        )
        run_docs, results = {}, {}
        for c in cells:
            res = _load(c / "result.json")
            r = int(c.name.rsplit("r", 1)[1])
            results[r] = res
            if res.get("status") == "ok" and (c / CLAIMS_REL).exists():
                run_docs[r] = _load(c / CLAIMS_REL)
        if not run_docs:
            per_effort[effort] = {"error": "no finished runs"}
            continue
        runs = sorted(run_docs)
        union: list[dict] = []
        for r in runs:
            for c in run_docs[r]["claims"]:
                union.append({"id": f"H{len(union) + 1}", "run": r, **c})
        judge = _judge(effort, ref, union, a.force)
        v = judge.get("verdict") or {}
        by_id = {h["id"]: h for h in union}
        cov_runs = []
        for row in v.get("coverage", []):
            ids = row.get("by") or []
            cov_runs.append(
                {by_id[i]["run"] for i in ids if i in by_id}
                if row.get("status") == "covered"
                else set()
            )
        part_runs = []
        for row in v.get("coverage", []):
            ids = row.get("by") or []
            part_runs.append(
                {by_id[i]["run"] for i in ids if i in by_id}
                if row.get("status") in ("covered", "partial")
                else set()
            )
        clusters = v.get("clusters", [])
        clus_runs = [
            {by_id[m]["run"] for m in cl.get("members", []) if m in by_id} for cl in clusters
        ]
        per_run_sources = {r: {_norm_url(s["url"]) for s in run_docs[r]["sources"]} for r in runs}
        table = _subset_means(runs, per_run_sources, cov_runs, clus_runs)
        table_part = _subset_means(runs, per_run_sources, part_runs, clus_runs)
        for row, rp in zip(table, table_part, strict=True):
            row["fable_covered_or_partial_mean"] = rp["fable_covered_mean"]
        ref_urls = {_norm_url(s["url"]) for s in ref["sources"]}
        all_urls = set().union(*per_run_sources.values())
        dedup = _dedup_union(run_docs[runs[0]], union, clusters, run_docs)
        (OUT / "score" / effort / "union-dedup.claims.json").write_text(
            json.dumps(dedup, indent=1) + "\n"
        )
        per_effort[effort] = {
            "runs": runs,
            "per_run": {
                r: {
                    "claims": results[r].get("claims"),
                    "sources": results[r].get("claim_sources"),
                    "high_conf": results[r].get("high_conf_claims"),
                    "seconds": (results[r].get("research") or {}).get("seconds"),
                    "cost_usd": (results[r].get("research") or {}).get("cost_usd"),
                    "gate10": (results[r].get("gate") or {}).get("counts"),
                }
                for r in runs
            },
            "cost_total_usd": round(
                sum((results[r].get("research") or {}).get("cost_usd") or 0 for r in runs), 3
            ),
            "union_raw_claims": len(union),
            "union_clusters": len(clusters),
            "extras_vs_fable": len(v.get("extras", [])),
            "coverage_status_counts": {
                s: sum(1 for row in v.get("coverage", []) if row.get("status") == s)
                for s in ("covered", "partial", "missing")
            },
            "missing_fable_claims": [
                ref["claims"][int(row["f"][1:]) - 1]["text"][:160]
                for row in v.get("coverage", [])
                if row.get("status") == "missing" and row.get("f", "F0")[1:].isdigit()
            ],
            "union_sources_total": len(all_urls),
            "union_sources_shared_with_fable": len(all_urls & ref_urls),
            "fable_sources_not_in_union": sorted(ref_urls - all_urls),
            "union_sources_not_in_fable": sorted(all_urls - ref_urls),
            "by_k": table,
            "judge": {
                k: judge.get(k) for k in ("model", "cost_usd", "tokens", "seconds", "is_error")
            },
        }
        gate_jobs.append((f"{effort}-union-dedup", dedup))
        gate_jobs.append((f"{effort}-r{runs[0]}", run_docs[runs[0]]))
    report["efforts"] = per_effort
    if not a.skip_gates:
        with ThreadPoolExecutor(max_workers=3) as pool:
            gates = list(pool.map(lambda j: _full_gate(j[0], j[1], a.force), gate_jobs))
        report["full_gates"] = {
            g["name"]: {
                k: g.get(k)
                for k in ("claims", "counts", "cost_usd", "seconds", "error", "is_error")
            }
            | {"gated": sum((g.get("counts") or {}).values())}
            for g in gates
        }
    (OUT / "score.json").write_text(json.dumps(report, indent=1, default=str) + "\n")
    print(json.dumps(report, indent=1, default=str))
    return 0


# --------------------------------------------------------------------------- report ---------
def cmd_report(a) -> int:
    rep = _load(OUT / "score.json")
    ref = _reference()
    lines = [f"# Haiku 5.5 repeats vs one Fable 5.1 run — {mx.CONCEPT}", ""]
    lines += [
        f"Reference: `{REF_ID}` — {len(ref['claims'])} claims, {len(ref['sources'])} sources "
        f"({len({_org(s['url']) for s in ref['sources']})} orgs).",
        "",
    ]
    for effort, e in rep["efforts"].items():
        if "error" in e:
            lines += [f"## Haiku {effort}: {e['error']}", ""]
            continue
        lines += [
            f"## Haiku 5.5 at `{effort}` — {len(e['runs'])} runs, ${e['cost_total_usd']} total",
            "",
        ]
        lines += [
            "| run | claims | high | sources | s | $ | gate-10 |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
        for r, p in e["per_run"].items():
            g = p.get("gate10") or {}
            lines.append(
                f"| r{r} | {p['claims']} | {p['high_conf']} | {p['sources']} | {p['seconds']} | "
                f"{round(p['cost_usd'] or 0, 2)} | {g.get('SUPPORTED', 0)}/{sum(g.values()) if g else 0} |"
            )
        lines += [
            "",
            f"Union of all runs: {e['union_raw_claims']} raw claims → {e['union_clusters']} unique; "
            f"{e['union_sources_total']} sources ({e['union_sources_shared_with_fable']} shared with Fable); "
            f"Fable claims covered/partial/missing = "
            f"{e['coverage_status_counts']['covered']}/{e['coverage_status_counts']['partial']}/"
            f"{e['coverage_status_counts']['missing']}; {e['extras_vs_fable']} facts Fable did not have.",
            "",
            "| k runs | sources (mean, min–max) | orgs | unique claims (mean, min–max) | Fable claims covered (mean, min–max) | covered or partial |",
            "|---:|---|---:|---|---|---:|",
        ]
        for row in e["by_k"]:
            lines.append(
                f"| {row['k']} | {row['sources_mean']} ({row['sources_min']}–{row['sources_max']}) | {row['orgs_mean']} | "
                f"{row['unique_claims_mean']} ({row['unique_claims_min']}–{row['unique_claims_max']}) | "
                f"{row['fable_covered_mean']}/{len(ref['claims'])} ({row['fable_covered_min']}–{row['fable_covered_max']}) | "
                f"{row['fable_covered_or_partial_mean']} |"
            )
        lines.append("")
        if e["missing_fable_claims"]:
            lines += ["Fable claims no Haiku run stated:", ""]
            lines += [f"- {t}" for t in e["missing_fable_claims"]]
            lines.append("")
        if e["fable_sources_not_in_union"]:
            lines += ["Fable sources no Haiku run cited:", ""]
            lines += [f"- {u}" for u in e["fable_sources_not_in_union"]]
            lines.append("")
    if rep.get("full_gates"):
        lines += ["## Full gate (Opus 5.5 medium, every non-tentative claim)", ""]
        lines += [
            "| set | claims | gated | SUPPORTED | OVERSTATED | NOT-IN-SOURCE | CONTRADICTED | UNVERIFIED | $ |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for n, g in rep["full_gates"].items():
            c = g.get("counts") or {}
            lines.append(
                f"| {n} | {g['claims']} | {g['gated']} | {c.get('SUPPORTED', 0)} | {c.get('OVERSTATED', 0)} | "
                f"{c.get('NOT-IN-SOURCE', 0)} | {c.get('CONTRADICTED', 0)} | {c.get('UNVERIFIED', 0)} | "
                f"{round(g.get('cost_usd') or 0, 2)} |"
            )
        lines.append("")
    (OUT / "results.md").write_text("\n".join(lines))
    print("\n".join(lines))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--efforts", default="medium,max")
    r.add_argument("--repeats", type=int, default=5)
    r.add_argument("--parallel", type=int, default=10)
    r.add_argument("--only", action="append")
    r.add_argument("--force", action="store_true")
    r.add_argument("--agent-timeout", type=int, default=mx.AGENT_TIMEOUT, help="seconds per cell")
    r.set_defaults(fn=cmd_run)
    s = sub.add_parser("score")
    s.add_argument("--efforts", default="medium,max")
    s.add_argument("--force", action="store_true")
    s.add_argument("--skip-gates", action="store_true")
    s.set_defaults(fn=cmd_score)
    sub.add_parser("report").set_defaults(fn=cmd_report)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
