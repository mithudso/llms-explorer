#!/usr/bin/env python3
"""replicate_docsets.py — push the docset vector store to the other boxes.

Replaces what Syncthing's `hub-chroma-docsets` folder used to do, so a docset
indexed on this box stays queryable from every box after Syncthing was removed.

Why rsync and not a sync daemon: the store already has exactly ONE writer by
design (this box runs every `docset_indexer.py index`), so bidirectional sync
bought nothing and cost a last-write-wins conflict storm that once zeroed the
live collection registry on all three boxes at once. A one-way push from the
single writer cannot produce that class of failure.

`chroma.sqlite3` and `docsets.db` are copied through `sqlite3 .backup` rather
than read off disk, because a plain file copy of a database being written to
yields a torn page — Syncthing had no such protection, which is part of why it
kept generating `.sync-conflict-*` copies of exactly these two files.

After a push, each box's LOGS corpus is reindexed (`semantic_ops.logs_corpus
index`) so its refs track the repo's log files. That matters because the logs
are split per track (`prompts-hub.md` / `prompts-tam.md`) and a rename leaves
every stored `prompts.md#vN` ref in a follower's logs.db dangling until it
reindexes. It is incremental — a no-op run costs one embed-free pass.

Usage:
  replicate_docsets.py push [--dry-run]   snapshot + rsync to every other box
  replicate_docsets.py check              compare collection counts per box
  replicate_docsets.py reindex-logs       rebuild the logs corpus on every box
"""

from __future__ import annotations

import argparse
import os
import shlex
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

HUB_DIR = Path.home() / ".global-ai-hub"
CHROMA_DIR = HUB_DIR / ".chroma-docsets"
SQLITE_FILES = ("chroma.sqlite3", "docsets.db")
REMOTE_SUBDIR = ".global-ai-hub/.chroma-docsets"
RSYNC_TIMEOUT = 60 * 60
REINDEX_TIMEOUT = 15 * 60
# Run from the hub root with scripts/ on the path, under the box's OWN venv:
# logs_corpus needs embed_core, so unlike the rest of this script it cannot
# run on system python.
REINDEX_CMD = ("cd ~/.global-ai-hub && PYTHONPATH=scripts "
               ".venv/bin/python -m semantic_ops.logs_corpus index")


def _targets() -> list[tuple[str, str]]:
    """Every OTHER box. pipeline_manager.remote_targets() already filters this
    machine out by matching ssh_targets against every local interface address,
    which matters here because one of the configured entries is this box's own
    LAN address."""
    import pipeline_manager as pm
    return pm.remote_targets()


def _remotes():
    from hub_manager import remotes as hm_remotes
    return hm_remotes


def collection_count(db: Path) -> int:
    try:
        with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as conn:
            return conn.execute("select count(*) from collections").fetchone()[0]
    except sqlite3.Error:
        return -1


def snapshot(dest: Path) -> None:
    """Consistent copies of the two SQLite files into `dest`."""
    dest.mkdir(parents=True, exist_ok=True)
    for name in SQLITE_FILES:
        src = CHROMA_DIR / name
        if not src.exists():
            continue
        with sqlite3.connect(src) as conn:
            with sqlite3.connect(dest / name) as out:
                conn.backup(out)


def cmd_push(args) -> int:
    targets = _targets()
    if not targets:
        print("no other boxes configured")
        return 0
    hm = _remotes()
    rc = 0
    with tempfile.TemporaryDirectory(dir=str(HUB_DIR)) as tmp:
        staged = Path(tmp) / "sqlite"
        snapshot(staged)
        for host, target in targets:
            ok, home_out = hm.run_ssh(target, 'echo "$HOME"', timeout=20)
            home = home_out.strip().splitlines()[-1].strip() if ok and home_out.strip() else ""
            if not home.startswith("/"):
                # Report WHY. "unreachable" alone is useless when this runs
                # unattended from a launchd timer, where the environment
                # differs from an interactive shell.
                print(f"[{host}] unreachable, skipped (ssh ok={ok}): "
                      f"{home_out.strip()[:300] or '<no output>'}")
                rc = 1
                continue
            remote = f"{home}/{REMOTE_SUBDIR}"
            protect = hm.rsync_supports_protect_args(target)
            base = ["--dry-run"] if args.dry_run else []
            # Segment dirs first, excluding the live SQLite files: those go
            # last, from the snapshot, so a follower never has new segment
            # data described by an older database or vice versa.
            ok, log = hm.run_rsync(
                [*base, "-r", "--delete",
                 *[f"--exclude={n}" for n in SQLITE_FILES],
                 f"{CHROMA_DIR}/", f"{target}:{remote}/"],
                timeout=RSYNC_TIMEOUT, protect_args=protect)
            if not ok:
                print(f"[{host}] segment rsync FAILED: {log[-300:]}")
                rc = 1
                continue
            ok, log = hm.run_rsync(
                [*base, f"{staged}/", f"{target}:{remote}/"],
                timeout=RSYNC_TIMEOUT, protect_args=protect)
            print(f"[{host}] {'pushed' if ok else 'db rsync FAILED'}"
                  + (f": {log[-300:]}" if not ok else ""))
            rc |= 0 if ok else 1
    # After the store lands: a follower's logs.db still points at whatever log
    # filenames it last indexed, which a rename in the repo silently breaks.
    reindex_logs(targets, dry_run=args.dry_run)
    return rc


def _quiet(host: str) -> bool:
    """Quiet-hours check that fails OPEN — a schedule this script cannot read
    must not silently stop replication follow-up work."""
    try:
        import box_schedule
        return box_schedule.is_quiet(host)
    except Exception as exc:  # noqa: BLE001
        print(f"[{host}] quiet-hours check failed, assuming available: {exc}")
        return False


def reindex_logs(targets, dry_run: bool = False) -> int:
    """Rebuild the logs corpus here and on every reachable, non-quiet box.

    Reindexing EMBEDS any new entries, so it is real load on the pool and must
    respect quiet hours — a box being skipped is normal, not a fault. Failures
    are reported but never fail the caller: replication succeeding matters more
    than its follow-up, and an hourly timer that goes red because one laptop is
    asleep trains you to ignore it.
    """
    hm = _remotes()
    print("reindexing the logs corpus")
    local = HUB_DIR / ".venv" / "bin" / "python"
    if dry_run:
        print("  [local] would reindex")
    elif not local.exists():
        print(f"  [local] WARN no venv at {local}, skipped")
    else:
        try:
            out = subprocess.run(
                [str(local), "-m", "semantic_ops.logs_corpus", "index"],
                cwd=str(HUB_DIR), capture_output=True, text=True,
                timeout=REINDEX_TIMEOUT,
                env={**os.environ, "PYTHONPATH": str(HUB_DIR / "scripts")})
            tail = (out.stdout + out.stderr).strip().splitlines()
            print(f"  [local] {tail[-1] if tail else 'ok'}"
                  if out.returncode == 0
                  else f"  [local] WARN reindex failed: "
                       f"{(tail[-1] if tail else '')[:200]}")
        except (OSError, subprocess.SubprocessError) as exc:
            print(f"  [local] WARN reindex failed: {exc}")

    for host, target in targets:
        if _quiet(host):
            print(f"  [{host}] quiet hours, skipped")
            continue
        if dry_run:
            print(f"  [{host}] would reindex")
            continue
        ok, out = hm.run_ssh(target, REINDEX_CMD, timeout=REINDEX_TIMEOUT)
        tail = out.strip().splitlines()
        print(f"  [{host}] {tail[-1] if tail else 'ok'}" if ok
              else f"  [{host}] WARN reindex failed: "
                   f"{(tail[-1] if tail else '<no output>')[:200]}")
    return 0


def cmd_reindex_logs(args) -> int:
    targets = _targets()
    return reindex_logs(targets, dry_run=getattr(args, "dry_run", False))


def remote_collection_count(target: str) -> int:
    """Collection count on another box, -1 if it cannot be read.

    Runs python3 rather than the sqlite3 CLI, which is not installed on every
    box, and lets PYTHON expand the ~: shlex.quote() single-quotes the whole
    script, so the remote shell would not expand ~ or $HOME inside it — the
    same trap that made the retired crawl dispatcher write every remote crawl
    into a literal directory named `~`.
    """
    script = ('import os,sqlite3;'
              f'print(sqlite3.connect(os.path.expanduser("~/{REMOTE_SUBDIR}'
              '/chroma.sqlite3")).execute('
              '"select count(*) from collections").fetchone()[0])')
    ok, out = _remotes().run_ssh(
        target, f"python3 -c {shlex.quote(script)} 2>/dev/null", timeout=30)
    try:
        return int(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return -1


def cmd_check(args) -> int:
    local = collection_count(CHROMA_DIR / "chroma.sqlite3")
    print(f"local: {local} collections")
    rc = 0
    for host, target in _targets():
        count = remote_collection_count(target)
        if count != local:
            rc = 1
        print(f"{host}: {count} collections — {'ok' if count == local else 'DRIFT'}")
    return rc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("push", help="snapshot + rsync to every other box")
    p.add_argument("--dry-run", action="store_true")
    sub.add_parser("check", help="compare collection counts per box")
    r = sub.add_parser("reindex-logs",
                       help="rebuild the logs corpus on this box and every other")
    r.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    return {"push": cmd_push, "check": cmd_check,
            "reindex-logs": cmd_reindex_logs}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
