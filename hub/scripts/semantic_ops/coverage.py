"""Coverage gap map (idea #14).

Every `hub ask` logs its best fused score. Queries that came back weak are
evidence of what the hub does NOT know — cluster them and each cluster
becomes a concrete suggestion: mirror this docs site, or write this skill.

Closes the loop: retrieval quality data feeds the next indexing decision.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import embed_core
import hub_lib

from semantic_ops import cluster
from semantic_ops.ask import history_path
from semantic_ops.logs_corpus import hub_dir

MIN_SCORE = 0.35
DAYS = 30
STOPWORDS = {"how", "what", "why", "the", "is", "are", "do", "does", "in", "of",
             "to", "for", "and", "a", "an", "with", "on", "my", "i", "we", "it"}

_log = hub_lib.get_logger("semantic_ops")


def reports_dir() -> Path:
    d = hub_dir() / "reports"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_history(days: int = DAYS) -> list[dict]:
    path = history_path()
    if not path.exists():
        return []
    cutoff = time.time() - days * 86400
    rows: list[dict] = []
    for line in path.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue  # hand-edited or truncated line
        if isinstance(rec, dict) and rec.get("query") and \
                float(rec.get("ts", 0)) >= cutoff:
            rows.append(rec)
    return rows


def weak_queries(min_score: float = MIN_SCORE, days: int = DAYS) -> list[str]:
    """Queries whose best hit scored below min_score (or returned nothing)."""
    out: list[str] = []
    for rec in load_history(days=days):
        top = rec.get("top") or []
        best = max((float(h.get("score", 0)) for h in top), default=0.0)
        if best < min_score:
            out.append(rec["query"])
    return out


def _topic(queries: list[str]) -> str:
    """Most frequent content word across a cluster — the mirror/skill hint."""
    counts: dict[str, int] = {}
    for q in queries:
        for w in re.findall(r"[a-z0-9][a-z0-9._-]{2,}", q.lower()):
            if w not in STOPWORDS:
                counts[w] = counts.get(w, 0) + 1
    return max(counts, key=lambda w: counts[w]) if counts else "unknown"


def gaps(min_score: float = MIN_SCORE, days: int = DAYS) -> list[dict]:
    """Clustered knowledge gaps, most-asked first."""
    weak = weak_queries(min_score=min_score, days=days)
    if not weak:
        return []
    try:
        groups = cluster.cluster_texts(weak, threshold=0.75)
    except embed_core.EmbeddingUnavailable as e:
        _log.warning("gap clustering degraded (embed pool down): %s", e)
        groups = [[i] for i in range(len(weak))]
    out: list[dict] = []
    for g in groups:
        queries = [weak[i] for i in g]
        topic = _topic(queries)
        action = f"mirror:{topic}" if len(queries) > 1 else f"skill:{topic}"
        out.append({"queries": queries, "count": len(queries), "topic": topic,
                    "suggested_action": action,
                    "summary": cluster.summarize(queries) if len(queries) > 1
                    else queries[0]})
    out.sort(key=lambda g: g["count"], reverse=True)
    return out


def summary_line(min_score: float = MIN_SCORE, days: int = DAYS) -> str:
    """One-line status for the TUI's Usage tab."""
    history = load_history(days=days)
    if not history:
        return "coverage: no ask history yet (use `scripts/ask` to build one)"
    found = gaps(min_score=min_score, days=days)
    weak = sum(g["count"] for g in found)
    return (f"coverage: {weak} weak of {len(history)} asks in {days}d → "
            f"{len(found)} gap cluster(s); top: "
            f"{found[0]['suggested_action'] if found else 'none'}")


def report(min_score: float = MIN_SCORE, days: int = DAYS) -> Path:
    found = gaps(min_score=min_score, days=days)
    out = reports_dir() / f"coverage-{datetime.now().strftime('%Y-%m-%d')}.md"
    stamp = datetime.now().isoformat(timespec="seconds")
    if not found:
        out.write_text(f"# Coverage map — {stamp}\n\nNo coverage gaps: every "
                       f"ask in the last {days} days retrieved something above "
                       f"score {min_score}.\n")
        return out
    lines = [f"# Coverage map — {stamp}", "",
             f"{sum(g['count'] for g in found)} weak queries "
             f"(best hit < {min_score}) in the last {days} days, "
             f"grouped into {len(found)} gaps.", "",
             "Each gap is a candidate for `docslist.textmirror` (mirror a docs "
             "site) or a new skill:", ""]
    for i, g in enumerate(found, 1):
        lines += [f"## {i}. {g['summary']}",
                  f"- suggested: **{g['suggested_action']}** "
                  f"({g['count']} asked question{'s' if g['count'] != 1 else ''})",
                  "- queries:"]
        lines += [f"  - {q}" for q in g["queries"][:10]]
        lines.append("")
    out.write_text("\n".join(lines))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Map what the hub could not answer into indexing suggestions")
    ap.add_argument("--min-score", type=float, default=MIN_SCORE)
    ap.add_argument("--days", type=int, default=DAYS)
    args = ap.parse_args(argv)
    path = report(min_score=args.min_score, days=args.days)
    print(f"coverage report -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
