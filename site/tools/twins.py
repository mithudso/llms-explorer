#!/usr/bin/env python3
"""twins — .md twins for every built page + the Cloudflare _headers file.
Usage: twins.py [--content src/content] [--dist dist] [--site-url URL]"""
from __future__ import annotations

import argparse
import datetime
import re
from pathlib import Path

FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def _title(fm: str) -> str:
    m = re.search(r"^title:\s*(.+)$", fm, re.M)
    return m.group(1).strip().strip("'\"") if m else "Untitled"


def write_twins(content_dir: Path, dist_dir: Path, site_url: str) -> list[Path]:
    out = []
    stamp = datetime.date.today().isoformat()
    for src in sorted(content_dir.rglob("*.md")):
        rel = src.relative_to(content_dir)                      # essays/a.md
        route = f"/{rel.with_suffix('').as_posix()}/"
        text = src.read_text(encoding="utf-8")
        m = FM_RE.match(text)
        fm, body = (m.group(1), text[m.end():]) if m else ("", text)
        twin = dist_dir / rel
        twin.parent.mkdir(parents=True, exist_ok=True)
        twin.write_text(f"<!-- llms-explorer twin of {site_url}{route} · generated {stamp} -->\n\n"
                        f"# {_title(fm)}\n\n{body.lstrip()}", encoding="utf-8")
        out.append(twin)
    return out


def write_headers(dist_dir: Path) -> Path:
    lines = ["/*.md", "  Content-Type: text/markdown; charset=utf-8", '  Link: </llms.txt>; rel="describedby"',
             "/llms*.txt", "  Content-Type: text/markdown; charset=utf-8", '  Link: </llms.txt>; rel="describedby"']
    for f in sorted(dist_dir.rglob("*.md")):
        lines += [f"/{f.relative_to(dist_dir).as_posix()}", f"  X-Markdown-Tokens: {f.stat().st_size // 4}"]
    for f in sorted(dist_dir.glob("llms*.txt")):
        lines += [f"/{f.name}", f"  X-Markdown-Tokens: {f.stat().st_size // 4}"]
    dest = dist_dir / "_headers"
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dest


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--content", default="src/content")
    p.add_argument("--dist", default="dist")
    p.add_argument("--site-url", default="https://llms-explorer.pages.dev")
    a = p.parse_args(argv)
    here = Path(__file__).resolve().parents[1]
    n = len(write_twins(here / a.content, here / a.dist, a.site_url.rstrip("/")))
    write_headers(here / a.dist)
    print(f"{n} twins, _headers written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
