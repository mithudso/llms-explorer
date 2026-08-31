#!/usr/bin/env python3
"""docset_rollout.py — roll the reference layer out across every docset.

Usage:
  .venv/bin/python scripts/docset_rollout.py probe              # which hosts publish llms.txt
  .venv/bin/python scripts/docset_rollout.py apply [--group G] [--dry-run]
        move each trafilatura mirror aside and reset its queue item so the
        pipeline re-mirrors via the llms path, then refines and indexes.
        G = llms-full (default) | llms | crawl | all
  .venv/bin/python scripts/docset_rollout.py cleanup [--dry-run]
        delete the orphaned distill-era artifacts (*_master.md,
        *_live_preview.md, .*_distill_index.json) — only for docsets that
        already have a <stem>.reference/summary.json

`probe` writes ~/.global-ai-hub/docset_rollout.json (runtime state, gitignored)
which `apply` reads, so the network is hit once. Start the pipeline manager
(`s` on the Queue tab, or `pipeline_manager.py run`) after `apply`.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import llms_acquire  # noqa: E402
from hub_manager import core, queue_model  # noqa: E402

ROLLOUT_STATE = core.HUB_DIR / "docset_rollout.json"
LEGACY_GLOBS = ("*_master.md", "*_live_preview.md", ".*_distill_index.json",
                "bulk_master.md", "semantic_master.md", "master_distilled.md")


def _mirror_for(url: str) -> Path:
    """Same rule as pipeline_manager.mirror_path_for, rooted at the
    hub_manager core path so tests can redirect it."""
    from urllib.parse import urlparse
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return core.MIRROR_OUT_DIR / f"{host}.md"


def probe(urls: list[str], fetch=llms_acquire._fetch, log=print) -> list[dict]:
    rows = []
    for url in urls:
        found = llms_acquire.probe(url, fetch)
        method = "llms-full" if found["llms_full"] else ("llms" if found["llms"] else "crawl")
        mirror = _mirror_for(url)
        state = mirror.parent / f"{mirror.stem}_state.json"
        acquired = None
        try:
            acquired = json.loads(state.read_text()).get("acquire")
        except (OSError, ValueError):
            pass
        rows.append({"url": url, "method": method, "source": found["llms_full"] or found["llms"],
                     "mirror": str(mirror), "mirror_exists": mirror.exists(),
                     "acquired": acquired,
                     "has_reference": (mirror.parent / f"{mirror.stem}.reference"
                                       / "summary.json").exists()})
        log(f"{method:9} {url}")
    return rows


def queue_urls() -> list[str]:
    return [it.url for it in queue_model.load_items()]


def apply(rows: list[dict], group: str = "llms-full", dry_run: bool = False,
          log=print) -> dict:
    """For each docset in `group`: move the existing mirror + state aside
    (dated, under _oversized_backup/) so text_mirror takes the llms path on
    the next crawl, then reset the queue item for a full rerun."""
    want = {"llms-full": ("llms-full",), "llms": ("llms",), "crawl": ("crawl",),
            "all": ("llms-full", "llms", "crawl")}[group]
    stamp = time.strftime("%Y%m%d-%H%M")
    moved, reset = 0, 0
    running = {it.url for it in queue_model.load_items() if it.status == "running"}
    targets = []
    for r in rows:
        if r["method"] not in want:
            continue
        if r["method"] != "crawl" and r.get("acquired") == r["method"]:
            continue  # already acquired the clean way; refine/index only
        if r["url"] in running:
            log(f"skip {r['url']}: a stage is running on it right now")
            continue
        targets.append(r)
    for r in targets:
        mirror = Path(r["mirror"])
        backup = mirror.parent / "_oversized_backup"
        for src in (mirror, mirror.parent / f"{mirror.stem}_state.json"):
            if not src.exists():
                continue
            dest = backup / f"{src.stem}.pre-llms-{stamp}{src.suffix}"
            log(f"{'would move' if dry_run else 'move'} {src.name} -> {dest}")
            if not dry_run:
                backup.mkdir(exist_ok=True)
                shutil.move(str(src), str(dest))
            moved += 1
        if not dry_run:
            reset += queue_model.recrawl([r["url"]])
        else:
            reset += 1
        log(f"{'would reset' if dry_run else 'reset'} {r['url']} ({r['method']})")
    return {"group": group, "targets": len(targets), "moved": moved, "reset": reset,
            "dry_run": dry_run}


def lint_exports(mirror_dir: Path, log=print) -> dict:
    """Run the llms lint (deterministic passes of /ldo) over every exported
    `<stem>.llms/` dir; the CI gate is any High finding. Uses the export's
    own mirror for anchor resolution when it is beside it."""
    import llms_lint

    docsets, files, high, medium = 0, 0, 0, 0
    worst: list[str] = []
    for d in sorted(mirror_dir.glob("*.llms")):
        stem = d.name[: -len(".llms")]
        mirror = mirror_dir / f"{stem}.md"
        targets = sorted(d.glob("llms*.txt")) + sorted(d.rglob("*/llms.txt"))
        if not targets:
            continue
        docsets += 1
        for f in targets:
            res = llms_lint.check(f, mirror=mirror if mirror.exists() else None)
            files += 1
            c = res.get("counts") or {}
            high += c.get("high", 0)
            medium += c.get("medium", 0)
            for x in res["findings"]:
                if x["severity"] == "high":
                    worst.append(f"{f.relative_to(mirror_dir)}: {x['msg'][:90]}")
    for line in worst[:20]:
        log(f"HIGH {line}")
    return {"docsets": docsets, "files": files, "high": high, "medium": medium}


def cleanup(mirror_dir: Path, dry_run: bool = False, log=print, lint: bool = True) -> dict:
    """Remove distill-era artifacts for docsets that have a fact layer. A
    docset without summary.json keeps its old files — nothing is deleted
    before its replacement exists. Ends with the llms lint over every export
    (`lint=False` skips it); `main` exits 1 on any High finding."""
    freed, deleted, skipped = 0, 0, 0
    for pages_dir in sorted(mirror_dir.glob("*.pages")):
        stem = pages_dir.name[:-len(".pages")]
        if not (mirror_dir / f"{stem}.reference" / "summary.json").exists():
            skipped += 1
            continue
        for pattern in LEGACY_GLOBS:
            for f in pages_dir.glob(pattern):
                if f.name.startswith("._"):
                    continue
                size = f.stat().st_size
                log(f"{'would delete' if dry_run else 'delete'} {f} ({size / 1_048_576:.1f} MB)")
                if not dry_run:
                    f.unlink()
                freed += size
                deleted += 1
    out = {"deleted": deleted, "freed_mb": round(freed / 1_048_576, 1),
           "skipped_docsets": skipped, "dry_run": dry_run}
    if lint:
        out["lint"] = lint_exports(mirror_dir, log=log)
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("probe")
    a = sub.add_parser("apply")
    a.add_argument("--group", choices=("llms-full", "llms", "crawl", "all"), default="llms-full")
    a.add_argument("--dry-run", action="store_true")
    c = sub.add_parser("cleanup")
    c.add_argument("--dry-run", action="store_true")
    c.add_argument("--no-lint", action="store_true", help="skip the llms lint gate")
    args = p.parse_args(argv)
    if args.cmd == "probe":
        rows = probe(queue_urls())
        ROLLOUT_STATE.write_text(json.dumps(rows, indent=1))
        counts = {}
        for r in rows:
            counts[r["method"]] = counts.get(r["method"], 0) + 1
        print(json.dumps({"hosts": len(rows), **counts, "state": str(ROLLOUT_STATE)}, indent=2))
        return 0
    if args.cmd == "apply":
        if not ROLLOUT_STATE.exists():
            print("run `probe` first", file=sys.stderr)
            return 2
        rows = json.loads(ROLLOUT_STATE.read_text())
        print(json.dumps(apply(rows, group=args.group, dry_run=args.dry_run), indent=2))
        return 0
    r = cleanup(core.MIRROR_OUT_DIR, dry_run=args.dry_run, lint=not args.no_lint)
    print(json.dumps(r, indent=2))
    return 1 if r.get("lint", {}).get("high") else 0  # CI gate


if __name__ == "__main__":
    raise SystemExit(main())
