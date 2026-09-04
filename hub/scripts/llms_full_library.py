#!/usr/bin/env python3
"""llms_full_library.py — a PRIVATE reference library of llms-full.txt
directories/aggregators, never published.

`llms_full_catalog.py`'s `compile` already discovers candidate SITES from
three known aggregators (llms-txt-hub, llmstxt.site, directory.llmstxt.cloud)
and downloads each site's OWN llms-full.txt into the public mirror — that
part is not duplicated here.

This module is the other half of the librarian's job: a queue of directory/
aggregator URLs to check → download → sweep for more site URLs →
incorporate into the public catalog → periodically re-check for drift. Each
step:

  add           queue a directory/aggregator URL (idempotent by key)
  check         download every `pending` item, archive the page under
                `files/<key>.txt`, sweep it for `*llms-full.txt` URLs
  incorporate   for every `downloaded` item, add its discovered site URLs
                to the PUBLIC catalog (`llms_full_catalog.add_seed`) — the
                normal download/grade/directory pipeline picks each one up
                from there — then mark the item `incorporated`
  stale / requeue-stale   find/reset items overdue for a re-check

The archived aggregator PAGE itself (a "copy their compiled files too"
case — someone's curated directory, not a single site's own llms-full.txt)
lives only under `files/`, which nothing else in the hub ever reads, and
which `scripts/refresh_snapshot.sh` never syncs into the repo — so it never
reaches the public site or the public git history. Only the site URLs a
sweep discovers get incorporated into the public catalog, and only each
site's own URL is ever linked from the public Directory — the same rule
`gen_directory.py` already enforces for the mirror; an aggregator's own
compiled/curated content is never republished.

Layout, all under LIBRARY_DIR (default `<HUB_LLMS_FULL_DIR>/private/`):
  queue.json      dict keyed by key: {key, url, status, added_at,
                  checked_at, bytes, file, discovered: [urls], reason}
  files/<key>.txt the archived page (private only)

Usage:
  llms_full_library.py add URL
  llms_full_library.py check [--jobs N]
  llms_full_library.py incorporate
  llms_full_library.py stale [--max-age-days N]
  llms_full_library.py requeue-stale [--max-age-days N]
  llms_full_library.py list [--status pending|downloaded|rejected|incorporated|all] [--json]

Stdlib only, like llms_full_catalog.py.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import llms_full_catalog as catalog  # noqa: E402

LIBRARY_DIR = catalog.HUB_DIR / "llms-full" / "private"
STATUSES = ("pending", "downloaded", "rejected", "incorporated", "all")


def _base(base: Path | None) -> Path:
    return Path(base) if base is not None else LIBRARY_DIR


def queue_path(base: Path | None = None) -> Path:
    return _base(base) / "queue.json"


def files_dir(base: Path | None = None) -> Path:
    return _base(base) / "files"


def load_queue(base: Path | None = None) -> dict:
    return catalog._load(queue_path(base), {})


def _save_queue(items: dict, base: Path | None = None) -> None:
    catalog._save(queue_path(base), items)


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def add_link(url: str, base: Path | None = None) -> dict:
    """Queue one directory/aggregator URL for `check`. Idempotent by key —
    an already-queued URL is returned unchanged, not re-added."""
    url = catalog._norm_url(url)
    key = catalog.key_for(url)
    items = load_queue(base)
    if key in items:
        return items[key]
    entry = {"key": key, "url": url, "status": "pending", "added_at": _now()}
    items[key] = entry
    _save_queue(items, base)
    return entry


def check(base: Path | None = None, max_bytes: int = 20 * 1024 * 1024, get=None,
          log=print) -> dict:
    """Download every `pending` queue item and sweep it for `*llms-full.txt`
    URLs. Not `llms_lint`-checked here — a directory page is not itself an
    llms-full.txt, so grading it would misapply the rubric; `incorporate`
    is the step that acts on what a sweep found."""
    get = get or catalog._get
    items = load_queue(base)
    todo = [e for e in items.values() if e.get("status") == "pending"]
    counts = {"downloaded": 0, "rejected": 0}
    for e in todo:
        body, _ctype, err = get(e["url"], max_bytes=max_bytes)
        e["checked_at"] = _now()
        if body is None:
            e.update(status="rejected", reason=err, bytes=0)
            counts["rejected"] += 1
            log(f"{e['key']}: rejected ({err})")
            continue
        text = body.decode("utf-8", errors="replace")
        discovered = sorted({r["url"] for r in catalog.parse_url_sweep(text, e["url"])})
        out = files_dir(base) / f"{e['key']}.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(body)
        e.update(status="downloaded", bytes=len(body), file=str(out), discovered=discovered,
                 reason="")
        counts["downloaded"] += 1
        log(f"{e['key']}: {len(discovered)} candidate site url(s)")
    _save_queue(items, base)
    return counts


def incorporate(base: Path | None = None, catalog_base: Path | None = None,
                 log=print) -> dict:
    """For every `downloaded` queue item, add its discovered site URLs to
    the PUBLIC catalog, then mark the item `incorporated`. The aggregator's
    own archived page under `files/` is never touched by this."""
    items = load_queue(base)
    todo = [e for e in items.values() if e.get("status") == "downloaded"]
    added = 0
    for e in todo:
        for url in e.get("discovered", []):
            catalog.add_seed(url, base=catalog_base)
            added += 1
        e["status"] = "incorporated"
        e["incorporated_at"] = _now()
    _save_queue(items, base)
    log(f"incorporated {added} site url(s) from {len(todo)} director"
        f"{'y' if len(todo) == 1 else 'ies'}")
    return {"items": len(todo), "urls_added": added}


def stale(base: Path | None = None, max_age_days: int = 30) -> list[dict]:
    """`downloaded`/`incorporated` items whose `checked_at` is older than
    `max_age_days` — due for a re-check so a directory's listing doesn't
    silently drift out of sync. Never-checked (`pending`) items are not
    "stale" — they just haven't run yet."""
    cutoff = datetime.now(UTC).timestamp() - max_age_days * 86400
    out = []
    for e in load_queue(base).values():
        checked = e.get("checked_at")
        if not checked:
            continue
        try:
            ts = datetime.fromisoformat(checked).timestamp()
        except ValueError:
            continue
        if ts < cutoff:
            out.append(e)
    return sorted(out, key=lambda e: e["key"])


def requeue_stale(base: Path | None = None, max_age_days: int = 30) -> int:
    """Flip every stale item back to `pending` so the next `check`
    re-fetches it — the "keep in sync" half of the periodic-refresh ask."""
    items = load_queue(base)
    due = {e["key"] for e in stale(base, max_age_days)}
    for key in due:
        items[key]["status"] = "pending"
    _save_queue(items, base)
    return len(due)


def list_items(base: Path | None = None, status: str = "all") -> list[dict]:
    items = sorted(load_queue(base).values(), key=lambda e: e["key"])
    if status == "all":
        return items
    return [e for e in items if e.get("status") == status]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", help="queue a directory/aggregator URL")
    a.add_argument("url")
    c = sub.add_parser("check", help="download every pending item")
    c.add_argument("--max-bytes", type=int, default=20 * 1024 * 1024)
    sub.add_parser("incorporate", help="add discovered site URLs to the public catalog")
    s = sub.add_parser("stale", help="list items overdue for a re-check")
    s.add_argument("--max-age-days", type=int, default=30)
    r = sub.add_parser("requeue-stale", help="reset overdue items to pending")
    r.add_argument("--max-age-days", type=int, default=30)
    lst = sub.add_parser("list")
    lst.add_argument("--status", default="all", choices=STATUSES)
    lst.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.cmd == "add":
        print(json.dumps(add_link(args.url)))
    elif args.cmd == "check":
        print(json.dumps(check(max_bytes=args.max_bytes)))
    elif args.cmd == "incorporate":
        print(json.dumps(incorporate()))
    elif args.cmd == "stale":
        print(json.dumps(stale(max_age_days=args.max_age_days), indent=1))
    elif args.cmd == "requeue-stale":
        print(f"requeued {requeue_stale(max_age_days=args.max_age_days)}")
    elif args.cmd == "list":
        items = list_items(status=args.status)
        if args.json:
            print(json.dumps(items, indent=1, ensure_ascii=False))
        else:
            for e in items:
                print(f"{e.get('status', '?'):12} {e['key']:35} {e['url']}")
            print(f"{len(items)} entries", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
