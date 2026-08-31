"""Change digests (ideas #10, #11).

recrawl(): what actually changed in a re-crawled docs mirror, by embedding
drift rather than by textual diff noise — clustered and summarized so a
2000-page recrawl reads as a handful of themes.

weekly(): what landed in the file corpus over the last N days, clustered by
topic. Both write markdown to $HUB_DIR/digests/.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

import hub_lib

from semantic_ops import cluster, snapdiff
from semantic_ops.logs_corpus import hub_dir

MAX_CLUSTER_ITEMS = 8
# Scale guards for weekly(): the corpus is ~49k files and the crawlers touch
# tens of thousands of them a day (measured: 44k in one 24h window), while
# clustering is O(files x clusters) in Python and each summary is an LLM call.
# Both caps are DISCLOSED in the report — never silently truncated.
MAX_WEEKLY_FILES = 500
MAX_SUMMARIZED_CLUSTERS = 12

_log = hub_lib.get_logger("semantic_ops")


def digest_dir() -> Path:
    d = Path(os.environ.get("HUB_DIGEST_DIR", str(hub_dir() / "digests")))
    d.mkdir(parents=True, exist_ok=True)
    return d


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _summary(texts: list[str]) -> str:
    return cluster.summarize(texts)


def prev_path(mirror_path: str | Path) -> Path:
    mirror_path = Path(mirror_path)
    return mirror_path.parent / ".prev" / mirror_path.name


def snapshot_previous(mirror_path: str | Path) -> Path | None:
    """Copy the current mirror aside before a recrawl overwrites it."""
    mirror_path = Path(mirror_path)
    if not mirror_path.is_file():
        return None
    dest = prev_path(mirror_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(mirror_path, dest)
    return dest


def _cluster_block(title: str, items: list[tuple[str, str]]) -> list[str]:
    """Section lines: cluster summary + the page refs behind it."""
    lines = [f"## {title}", ""]
    if not items:
        lines += ["_none_", ""]
        return lines
    try:
        groups = cluster.cluster_texts([t for _k, t in items])
    except Exception as e:  # embed pool down — fall back to a flat list
        _log.warning("digest clustering degraded: %s", e)
        groups = [[i] for i in range(len(items))]
    for g in groups:
        texts = [items[i][1] for i in g]
        lines.append(f"- **{_summary(texts)}** ({len(g)} chunk"
                     f"{'s' if len(g) != 1 else ''})")
        for i in g[:MAX_CLUSTER_ITEMS]:
            lines.append(f"  - `{items[i][0]}`")
        if len(g) > MAX_CLUSTER_ITEMS:
            lines.append(f"  - …and {len(g) - MAX_CLUSTER_ITEMS} more")
    lines.append("")
    return lines


def recrawl(mirror_path: str | Path) -> Path | None:
    """Digest the semantic delta between the previous and current mirror.

    Returns None when no previous snapshot exists (first crawl)."""
    mirror_path = Path(mirror_path)
    prev = prev_path(mirror_path)
    if not prev.exists() or not mirror_path.exists():
        return None
    old = snapdiff.mirror_chunks(prev.read_text(errors="ignore"))
    new = snapdiff.mirror_chunks(mirror_path.read_text(errors="ignore"))
    delta = snapdiff.diff(old, new)
    out = digest_dir() / f"{mirror_path.stem}-{_today()}.md"
    stamp = datetime.now().isoformat(timespec="seconds")
    changed_items = [(k, n) for k, _o, n, _c in delta["changed"]]
    if not (delta["added"] or delta["removed"] or changed_items):
        out.write_text(f"# Recrawl digest — {mirror_path.name} — {stamp}\n\n"
                       "No semantic changes since the previous crawl.\n")
        return out
    lines = [f"# Recrawl digest — {mirror_path.name} — {stamp}", "",
             f"{len(delta['added'])} added · {len(changed_items)} changed · "
             f"{len(delta['removed'])} removed (chunk-level).", ""]
    lines += _cluster_block("Changed", changed_items)
    lines += _cluster_block("Added", delta["added"])
    lines += _cluster_block("Removed", delta["removed"])
    out.write_text("\n".join(lines))
    return out


def weekly(days: int = 7, max_files: int = MAX_WEEKLY_FILES) -> Path:
    """Topic digest of files indexed/modified in the last `days`.

    Samples the `max_files` most recently modified files when more qualify;
    the report says so explicitly."""
    cutoff = time.time() - days * 86400
    vectors = hub_lib.load_embeddings()
    scored: list[tuple[float, str, list[float]]] = []
    for path in hub_lib.load_index():
        try:
            mtime = Path(path).stat().st_mtime
        except OSError:
            continue  # indexed file no longer on disk
        if mtime < cutoff:
            continue
        vec = (vectors.get(path) or {}).get("embedding")
        if vec:
            scored.append((mtime, path, vec))
    out = digest_dir() / f"weekly-{_today()}.md"
    stamp = datetime.now().isoformat(timespec="seconds")
    if not scored:
        out.write_text(f"# Weekly digest — {stamp}\n\n"
                       f"No files indexed in the last {days} days.\n")
        return out
    total = len(scored)
    scored.sort(key=lambda r: r[0], reverse=True)
    recent = [(p, v) for _m, p, v in scored[:max_files]]
    if total > max_files:
        _log.warning("weekly digest sampled the %d most recent of %d files",
                     max_files, total)
    groups = sorted(cluster.agglomerate([v for _p, v in recent]),
                    key=len, reverse=True)
    lines = [f"# Weekly digest — {stamp}", ""]
    if total > max_files:
        lines.append(f"{total} files touched in the last {days} days; this "
                     f"digest covers the {max_files} most recently modified "
                     f"({total - max_files} not shown).")
    else:
        lines.append(f"{total} files touched in the last {days} days.")
    lines += [f"Grouped into {len(groups)} topics"
              + (f"; the {MAX_SUMMARIZED_CLUSTERS} largest are summarized."
                 if len(groups) > MAX_SUMMARIZED_CLUSTERS else "."), ""]
    for n, g in enumerate(groups):
        if n < MAX_SUMMARIZED_CLUSTERS:
            texts = [hub_lib.get_text_content(recent[i][0], max_chars=1500) or ""
                     for i in g]
            label = _summary([t for t in texts if t])
        else:
            label = Path(recent[g[0]][0]).parent.name or "misc"
        lines.append(f"- **{label}** ({len(g)} files)")
        for i in g[:MAX_CLUSTER_ITEMS]:
            lines.append(f"  - `{recent[i][0]}`")
        if len(g) > MAX_CLUSTER_ITEMS:
            lines.append(f"  - …and {len(g) - MAX_CLUSTER_ITEMS} more")
    out.write_text("\n".join(lines) + "\n")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Semantic change digests")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("recrawl", help="digest one mirror against its .prev snapshot")
    r.add_argument("mirror")
    w = sub.add_parser("weekly", help="topic digest of recently indexed files")
    w.add_argument("--days", type=int, default=7)
    w.add_argument("--max-files", type=int, default=MAX_WEEKLY_FILES,
                   help=f"sample cap, most recent first (default {MAX_WEEKLY_FILES})")
    args = ap.parse_args(argv)
    if args.cmd == "recrawl":
        path = recrawl(args.mirror)
        if path is None:
            print("no previous snapshot — nothing to diff "
                  "(a digest appears after the next recrawl)")
            return 0
        print(f"recrawl digest -> {path}")
        return 0
    print(f"weekly digest -> {weekly(days=args.days, max_files=args.max_files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
