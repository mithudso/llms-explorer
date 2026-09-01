#!/usr/bin/env python3
"""Promote due posts from site/scheduled-posts/ into site/src/content/blog/.

A post is "scheduled", not published, until its frontmatter `date` arrives.
Holding it as a file outside src/content/ (rather than date-filtering inside
Astro at build time) means an unpublished post simply does not exist in the
built site — no future-dated route, no risk of a lint/link-check pass
discovering a page that "shouldn't" be there yet.

Run daily (see .github/workflows/publish-scheduled.yml), before the site's
own daily rebuild. Exits 0 whether or not anything was due; prints what it
promoted so the workflow can decide whether to commit and notify.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
SCHEDULED = SITE / "scheduled-posts"
BLOG = SITE / "src" / "content" / "blog"

DATE_RE = re.compile(r'^date:\s*"?(\d{4}-\d{2}-\d{2})"?\s*$', re.MULTILINE)
TITLE_RE = re.compile(r'^title:\s*"(.+)"\s*$', re.MULTILINE)


def due_posts(today: dt.date) -> list[Path]:
    if not SCHEDULED.is_dir():
        return []
    due = []
    for path in sorted(SCHEDULED.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        m = DATE_RE.search(text)
        if not m:
            print(f"skip {path.name}: no date in frontmatter", file=sys.stderr)
            continue
        if dt.date.fromisoformat(m.group(1)) <= today:
            due.append(path)
    return due


def main() -> None:
    today = dt.date.today()
    promoted = []
    for path in due_posts(today):
        text = path.read_text(encoding="utf-8")
        title_match = TITLE_RE.search(text)
        title = title_match.group(1) if title_match else path.stem
        dest = BLOG / path.name
        path.rename(dest)
        promoted.append({"slug": path.stem, "title": title})
        print(f"promoted {path.name}")
    # Machine-readable summary for the workflow step that follows.
    print(json.dumps(promoted))


if __name__ == "__main__":
    main()
