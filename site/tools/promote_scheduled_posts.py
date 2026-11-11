#!/usr/bin/env python3
"""Publish at most one reviewed due article per New York day, after 09:00.

Scheduled files remain outside Astro's content collection. A persisted receipt
and existing article dates prevent reruns or a backlog from publishing a burst.
Research files require exact document/report bindings from a full /ddo review.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import tempfile
from pathlib import Path
from zoneinfo import ZoneInfo

from publication import (
    TIMEZONE, digest, metadata, publication_day, review_assets, verify_research_review,
)

SITE = Path(__file__).resolve().parents[1]


def ledger_path(site: Path) -> Path:
    return site / "src/data/publication-ledger.json"


def read_ledger(site: Path) -> dict:
    path = ledger_path(site)
    ledger = json.loads(path.read_text()) if path.exists() else {
        "schema": "publication-ledger/v1", "timezone": TIMEZONE, "entries": []}
    if (ledger.get("schema") != "publication-ledger/v1"
            or ledger.get("timezone") != TIMEZONE or not isinstance(ledger.get("entries"), list)):
        raise ValueError("Invalid publication ledger; preserve and repair its history")
    for entry in ledger["entries"]:
        dt.date.fromisoformat(entry["published_on"])
        if (not isinstance(entry.get("slug"), str)
                or not isinstance(entry.get("document_sha256"), str)):
            raise ValueError("Invalid publication ledger entry")
    return ledger


def due_posts(today: dt.date, site: Path = SITE) -> list[Path]:
    scheduled = site / "scheduled-posts"
    if not scheduled.is_dir():
        return []
    due = []
    for path in sorted(scheduled.rglob("*.md")):
        if path.name.endswith(".ddo-report.md"):
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(scheduled.resolve()):
            raise ValueError(f"Scheduled article must be a regular confined file: {path}")
        data = metadata(path.read_text(encoding="utf-8"))
        if not data.get("date"):
            raise ValueError(f"Scheduled article needs a frontmatter date: {path}")
        date = dt.date.fromisoformat(data["date"])
        if data.get("draft", "false").lower() != "true" and date <= today:
            due.append((date, path.relative_to(scheduled).as_posix(), path))
    return [path for _, _, path in sorted(due)]


def _write_ledger(path: Path, ledger: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".publication-ledger-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(ledger, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if Path(temporary).exists():
            Path(temporary).unlink()


def promote(site: Path = SITE, *, now: dt.datetime | None = None,
            dry_run: bool = False) -> list[dict]:
    now = now or dt.datetime.now(dt.UTC)
    today = publication_day(now)
    if now.astimezone(ZoneInfo(TIMEZONE)).hour < 9:
        return []
    ledger = read_ledger(site)
    # A prior scheduled publication or a manually published article consumes
    # today's slot. Source dates stay unchanged so review hashes remain valid.
    if any(entry["published_on"] == today.isoformat() for entry in ledger["entries"]):
        return []
    blog = site / "src/content/blog"
    for path in blog.rglob("*.md") if blog.is_dir() else []:
        data = metadata(path.read_text(encoding="utf-8"))
        if data.get("date") == today.isoformat() and data.get("draft", "false").lower() != "true":
            return []
    for path in due_posts(today, site):
        relative = path.relative_to(site / "scheduled-posts")
        data = metadata(path.read_text(encoding="utf-8"))
        assets = []
        review = None
        if relative.parts[0] == "research" or data.get("category") == "research":
            if relative.parts[0] != "research" or data.get("category") != "research":
                raise ValueError("Research articles require category research "
                                 "and the research/ directory")
            paper = relative.relative_to("research")
            review = verify_research_review(site, paper, path)
            assets = review_assets(site, paper, review)
        dest = blog / relative
        if not dest.resolve().is_relative_to(blog.resolve()):
            raise ValueError(f"Article destination escapes the blog: {dest}")
        checksum = review["document_sha256"] if review else digest(path)
        if digest(path) != checksum:
            raise ValueError("Scheduled source changed after review")
        prior = next((entry for entry in ledger["entries"]
                      if entry["slug"] == relative.with_suffix("").as_posix()), None)
        if dest.exists():
            if prior and prior["document_sha256"] == checksum and digest(dest) == checksum:
                # A crash after the receipt but before unlink left a duplicate
                # scheduled input. Acknowledged bytes may be cleaned up safely.
                if not dry_run:
                    path.unlink()
                    for source, _, _ in assets:
                        if source.exists():
                            source.unlink()
                continue
            raise ValueError(f"Publication destination already exists; refusing overwrite: {dest}")
        if prior:
            raise ValueError("Published article is missing; "
                             f"repair its receipt before continuing: {dest}")
        for source, asset_dest, _ in assets:
            if not source.is_file() or asset_dest.exists():
                raise ValueError("Research images must be queued and have new destinations")
        result = {"slug": relative.with_suffix("").as_posix(),
                  "title": data.get("title", path.stem), "published_on": today.isoformat(),
                  "scheduled_for": data["date"], "document_sha256": checksum}
        if assets:
            result["assets"] = [row for _, _, row in assets]
        if dry_run:
            return [result]
        dest.parent.mkdir(parents=True, exist_ok=True)
        # No-clobber link preserves the reviewed bytes and original permissions.
        created_assets = []
        created_document = False
        try:
            os.link(path, dest)
            created_document = True
            for source, asset_dest, row in assets:
                asset_dest.parent.mkdir(parents=True, exist_ok=True)
                os.link(source, asset_dest)
                created_assets.append((asset_dest, row["sha256"]))
                if digest(asset_dest) != row["sha256"] or digest(source) != row["sha256"]:
                    raise ValueError("Research image changed during publication")
            if digest(dest) != checksum or digest(path) != checksum:
                raise ValueError("Scheduled source changed during publication")
            ledger["entries"].append({**result, "published_at": now.isoformat()})
            _write_ledger(ledger_path(site), ledger)
        except BaseException:
            for asset_dest, expected in created_assets:
                if asset_dest.exists() and digest(asset_dest) == expected:
                    asset_dest.unlink()
            if created_document and dest.exists() and digest(dest) == checksum:
                dest.unlink()
            raise
        path.unlink()
        for source, _, _ in assets:
            source.unlink()
        return [result]
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    # GitHub Actions concurrency serializes remote publishers. flock also keeps
    # local invocations from both consuming an empty daily slot.
    import fcntl
    import hashlib
    lock = Path(tempfile.gettempdir()) / (
        "llms-publication-" + hashlib.sha256(str(SITE.resolve()).encode()).hexdigest() + ".lock")
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        print(json.dumps(promote(dry_run=args.dry_run)))


if __name__ == "__main__":
    main()
