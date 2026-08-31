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


def grade_for(counts: dict) -> str:
    """A = clean, B = a couple of Mediums, C = more, D = one High, F = two or more."""
    high, medium = counts.get("high", 0), counts.get("medium", 0)
    if high >= 2:
        return "F"
    if high == 1:
        return "D"
    if medium == 0:
        return "A"
    if medium <= 2:
        return "B"
    return "C"


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
    return {
        "key": entry["key"],
        "name": entry.get("name") or entry["key"],
        "site": entry.get("site", ""),
        "url": entry.get("url", ""),
        "category": entry.get("category", ""),
        "pages": int(entry.get("pages") or 0),
        "bytes": int(entry.get("bytes") or 0),
        "fetched_at": entry.get("fetched_at", ""),
        "grade": grade_for(counts),
        "counts": {k: counts[k] for k in ("high", "medium", "low")},
        "groups": dict(sorted(groups.items())),
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
