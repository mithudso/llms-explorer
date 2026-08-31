#!/usr/bin/env python3
"""gen_directory — the directory of known llms-full.txt files, scored, as build-time JSON.

Reads the repo's own mirror of the llms-full catalog (never ~/.global-ai-hub, so CI
works) and runs `llms_lint.check(..., kind="full")` over every mirrored file, turning
the linter's findings into a per-site conformance grade. Nothing here is a judgement
of our own: the grade is a pure function of the High/Medium counts the linter reports.

The mirrored text itself is never republished — the directory links each source's own
file at its own URL (master D8). Only the score travels.

Usage: gen_directory.py [--out src/data/directory.json] [--limit N]
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parent
sys.path.insert(0, str(REPO / "hub" / "scripts"))

import llms_full_catalog  # noqa: E402
import llms_lint  # noqa: E402

GRADES = "ABCDF"
# The score, per the directory component spec (docs/site/components/10-directory.md
# §3): each rubric group scores `100 − weighted deductions`, and the overall
# conformance score is their weighted mean. A flat High/Medium threshold — what
# this file used to do — cannot express "one High in one group on a 5,385-page
# file", and collapsed every single-High site onto D whatever else the card said.
DEDUCTION = {"high": 25, "medium": 8, "low": 2}
GROUP_WEIGHTS = {"N": 1.5, "D": 1.5, "C": 1.5, "P": 1.5,
                 "I": 1.0, "S": 1.0, "H": 1.0, "R": 0.5, "F": 0.5}
# The groups `llms_lint.check(..., kind="full")` can actually report on a
# mirrored file: I (P0 identity), C (the full-file grammar), P (trust), S (size)
# and H (hygiene/serving). N and D only fire on an index, R needs an index of
# ours and F a family directory — excluded, per §3's "when applicable".
FULL_GROUPS = ("I", "C", "P", "S", "H")
# Bands, calibrated on the seed as §12 invites ("calibrate on the seed"). §9's
# acceptance is the check: not all A, not all F, and `developers.cloudflare.com`
# (one High and two Mediums in C, one Medium in P → 80.4) lands ≥ B. A ≥ 95
# rather than ≥ 90 because at 90 the 145-site seed grades 140 A, which tells a
# reader nothing; at 95 an A means a file with at most a stray Low. Measured on
# the committed seed: A 91 · B 53 · C 1 (`developers.cloudflare.com` 80.4 → B).
# The band floors leave D and F reachable — this seed simply has no file that
# far gone, because the mirror only keeps files that split into pages.
BANDS = ((95, "A"), (80, "B"), (70, "C"), (60, "D"))
# `hygiene` findings (H1 whitespace/BOM residue, auto-fixable) are not in the
# published `counts` — the card shows High/Medium/Low — so they do not move the
# score either. The H group still scores: H8-class findings would.
SCORED_SEVERITIES = frozenset(DEDUCTION)
# Attributes that judge the *export directory* around a file rather than the file: S2
# wants an llms-small.txt sibling, H8 a manifest.json. A one-file mirror can answer
# neither — the site may well publish a small variant we never fetched — so charging a
# site for their absence measures our storage layout, not its conformance. Dropped.
MIRROR_BLIND = {"S2", "H8"}


def base_dir(repo_root: Path) -> Path:
    """The repo's vendored llms-full mirror. `outputs/llms-full/` in this repo; a bare
    `llms-full/` is accepted too so a fixture tree can be laid out the simple way."""
    for rel in ("llms-full", "outputs/llms-full"):
        cand = repo_root / rel
        if (cand / "manifest.json").is_file():
            return cand
    raise FileNotFoundError(
        f"no llms-full mirror under {repo_root} (tried llms-full/, outputs/llms-full/)")


def entries(base: Path, status: str = "ok", min_pages: int = 1) -> list[dict]:
    """Manifest rows worth scoring, enriched from the catalog and with `file` rebound
    to the repo's own copy.

    Two things the manifest cannot be trusted for off-box. It records absolute paths
    into the machine that downloaded each file, so `list_entries` would call every row
    `missing` anywhere else; and a row need not repeat the catalog's `name`/`site`/
    `category`, which is where the directory's own labels come from. So we take
    `list_entries`' filtering where the rows support it, merge the catalog in by key,
    and resolve each file inside the repo, dropping what is not there.
    """
    manifest = llms_full_catalog.load_manifest(base)
    catalog = {c["key"]: c for c in llms_full_catalog.load_catalog(base) if c.get("key")}
    keyed = all("key" in e for e in manifest.values())
    rows = []
    if keyed:
        rows = llms_full_catalog.list_entries(base=base, status=status, min_pages=min_pages)
    if not rows:  # rows carry no key, or every recorded path is off-box: filter here
        rows = [
            dict(e, key=e.get("key", k))
            for k, e in sorted(manifest.items())
            if e.get("status") == status and int(e.get("pages") or 0) >= min_pages
        ]
    out = []
    for e in rows:
        local = base / "files" / f"{e['key']}.txt"
        if not local.is_file():
            continue
        merged = dict(catalog.get(e["key"], {}))
        merged.update({k: v for k, v in e.items() if v not in (None, "")})
        merged["file"] = str(local)
        out.append(merged)
    return out


def group_scores(findings: list[dict], groups=FULL_GROUPS) -> dict[str, int]:
    """`group → 0–100`. Every applicable group starts clean and is deducted for
    the findings filed under it (the rubric group is the attribute id's first
    letter, one of I N D C P S R F H)."""
    out = {g: 100 for g in groups}
    for f in findings:
        g = f["attr"][0]
        if g in out and f["severity"] in SCORED_SEVERITIES:
            out[g] -= DEDUCTION[f["severity"]]
    return {g: max(0, min(100, v)) for g, v in out.items()}


def score_for(findings: list[dict], groups=FULL_GROUPS) -> tuple[float, dict[str, int]]:
    """The weighted mean of the group scores, and the score card it came from."""
    per = group_scores(findings, groups)
    weight = sum(GROUP_WEIGHTS[g] for g in per) or 1.0
    return round(sum(GROUP_WEIGHTS[g] * v for g, v in per.items()) / weight, 1), per


def grade_for(score: float, highs: int = 0) -> str:
    """The letter for a 0–100 conformance score (BANDS), capped by High findings.

    The score card says WHERE a file fails; the cap says how much that costs.
    A High is "an agent is misled or blocked" (attributes.md), and the weighted
    mean alone dilutes one to about 80 — which would grade a file with a
    dangling grammar or a leaked secret a B. So the plan's rule stands as a
    ceiling over the card: one High caps at D, two or more at F. A clean file
    is graded by its card alone."""
    letter = "F"
    for floor, band in BANDS:
        if score >= floor:
            letter = band
            break
    if highs >= 2:
        return "F"
    if highs == 1:
        return max(letter, "D")     # letters sort A < B < C < D < F
    return letter


def score(entry: dict) -> dict:
    """One site: the lint result folded into a grade, group counts and a findings list.

    The file is linted through a symlink named `llms-full.txt` in a directory of its own,
    so the linter sees the name and the neighbourhood a real llms-full file has instead of
    our flat `files/<key>.txt` mirror, where 600 unrelated sites share one parent.
    """
    src = Path(entry["file"])
    with tempfile.TemporaryDirectory() as tmp:
        link = Path(tmp) / "llms-full.txt"
        link.symlink_to(src)
        res = llms_lint.check(link, kind="full")
    counts = {"high": 0, "medium": 0, "low": 0, "hygiene": 0, "na": 0}
    groups: dict[str, int] = {}
    findings = []
    for f in res["findings"]:
        if f["attr"] in MIRROR_BLIND:
            continue
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
        findings.append({"attr": f["attr"], "severity": f["severity"], "msg": f["msg"]})
        if f["severity"] in ("high", "medium"):
            # the rubric group is the attribute id's first letter, one of I N D C P S R F H
            letter = f["attr"][0]
            groups[letter] = groups.get(letter, 0) + 1
    conformance, card = score_for(findings)
    return {
        "key": entry["key"],
        "name": entry.get("name") or entry["key"],
        "site": entry.get("site", ""),
        "url": entry.get("url", ""),
        "category": entry.get("category", ""),
        "pages": int(entry.get("pages") or 0),
        "bytes": int(entry.get("bytes") or 0),
        "fetched_at": entry.get("fetched_at", ""),
        "score": conformance,
        "grade": grade_for(conformance, counts.get("high", 0)),
        "counts": {k: counts[k] for k in ("high", "medium", "low")},
        "groups": dict(sorted(groups.items())),
        "groupScores": card,
        "findings": findings,
    }


def build(repo_root: Path, limit: int | None = None, today: str | None = None,
          progress: bool = False) -> dict:
    base = base_dir(repo_root)
    rows = entries(base)
    if limit is not None:
        rows = rows[:limit]
    sites = []
    for i, entry in enumerate(rows, 1):
        sites.append(score(entry))
        if progress and (i % 10 == 0 or i == len(rows)):
            print(f"  scored {i}/{len(rows)}", flush=True)
    sites.sort(key=lambda s: (GRADES.index(s["grade"]), s["key"]))
    stamp = today or datetime.datetime.now(datetime.UTC).date().isoformat()
    return {"generated": stamp, "count": len(sites), "sites": sites}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default="src/data/directory.json")
    p.add_argument("--limit", type=int, default=None,
                   help="score only the first N sites (fast local run)")
    a = p.parse_args(argv)
    out = HERE / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    data = build(HERE.parent, limit=a.limit, progress=True)
    out.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    dist: dict[str, int] = {}
    for s in data["sites"]:
        dist[s["grade"]] = dist.get(s["grade"], 0) + 1
    spread = " ".join(f"{g}={dist.get(g, 0)}" for g in GRADES)
    print(f"{out}: {data['count']} sites, {spread}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
