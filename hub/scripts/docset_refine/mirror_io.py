"""Read/write the web-text-mirror banner format and the package's JSON files."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

BANNER = "=" * 90
_BANNER_RE = re.compile(r"^={10,}\s*$")
_URL_RE = re.compile(r"^URL:\s*(\S+)\s*$")


def parse_mirror(text: str) -> list[dict]:
    """Same contract as docset_indexer.parse_mirror, kept local so this
    package has no import-time dependency on the embed pool. A bannerless
    file is one synthetic page."""
    lines = text.splitlines()
    starts = []
    for i in range(len(lines) - 2):
        if _BANNER_RE.match(lines[i]) and _BANNER_RE.match(lines[i + 2]):
            m = _URL_RE.match(lines[i + 1])
            if m:
                starts.append((i, m.group(1)))
    if not starts:
        return [{"url": "", "text": text}]
    pages = []
    for n, (i, url) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        pages.append({"url": url, "text": "\n".join(lines[i + 3:end]).strip("\n")})
    return pages


def read_pages(path: Path) -> list[dict]:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    pages = parse_mirror(text)
    if len(pages) == 1 and not pages[0]["url"]:
        pages[0]["url"] = f"file://{Path(path).resolve()}"
    return pages


def write_pages(pages: list[dict], path: Path) -> int:
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for pg in pages:
            fh.write(f"\n\n{BANNER}\nURL: {pg['url']}\n{BANNER}\n\n{pg['text']}\n")
    os.replace(tmp, path)
    return len(pages)


def save_json(obj, path: Path) -> None:
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    os.replace(tmp, path)


def load_json(path: Path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def read_jsonl(path: Path) -> list[dict]:
    out = []
    try:
        with Path(path).open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except OSError:
        pass
    return out


def write_jsonl(rows, path: Path) -> int:
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    n = 0
    with tmp.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += 1
    os.replace(tmp, path)
    return n
