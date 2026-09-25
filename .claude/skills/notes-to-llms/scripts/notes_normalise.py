#!/usr/bin/env python3
"""Turn a disordered pile of notes into the banner mirror every refine tool reads.

Authority: `docs/site/components/02-notes-to-llms.md` §3 (design intent for the
anchoring rule) and `hub/scripts/docset_refine/mirror_io.py` (the banner
grammar: ``==========`` / ``URL: <source>`` / ``==========`` / body).

Notes have no URLs, and `llms_lint.py` P7 C6 is a **High** on any unit line
without a source. So the one thing this script must get right is giving every
page a source the linter accepts and every heading an anchor the linter can
*resolve*. Four rules follow directly from reading `llms_lint.py`, and each one
exists because the obvious alternative silently fails the gate:

**1. Sources are root-relative, not a custom scheme.** `llms_lint.py`'s unit
check accepts a source starting with ``http``, ``/`` or ``.`` and nothing else,
so a tidy-looking ``upload://<project>/<path>`` is counted as *unsourced* and is
a High. Pages are therefore ``/<project>/<relpath>``, and ``--base-url`` swaps
that for an absolute URL when the material is (or is about to be) served.

**2. Setext headings are rewritten to ATX.** `llms_lint._mirror_headings` finds
anchors with an ATX-only regex, so an ``Underlined heading`` in a note yields no
anchor and every unit pointing at it is unresolved (P7 R3). Converting on the
way in makes the anchor real instead of aspirational.

**3. Anchors are the bare slug, never a `-2` suffix.** Docs sites disambiguate
repeated headings; `_mirror_headings` does not — it collects a *set* of slugs, so
``#burst-2`` resolves to nothing. Two identical headings therefore share one
anchor, and the inventory flags the collision rather than inventing an anchor
the gate will reject.

**4. A page with no headings gets no anchor.** `_mirror_headings` returns an
empty set for it, and the resolution check treats a missing anchor as fine but a
*present, unmatched* one as unresolved. So units from such a page must carry the
bare page URL. The inventory names those pages so the caller can convert them or
accept the loss of precision; it never emits ``#top``, which would fail.

Empty pages are dropped and counted (matching `export_llms.drop_empty_pages`),
byte-identical duplicates are dropped and counted, and unreadable suffixes are
listed rather than skipped in silence.

Stdlib only, no network, no model call: this is the deterministic floor of the
`notes-to-llms` skill, and it must run anywhere the notes do.

Usage
-----
    python notes_normalise.py NOTES_DIR [MORE...] --project my-notes --out build/

Writes ``<out>/<project>.md`` (the banner mirror, named so `docset_refine`
derives ``<project>.reference/`` and ``<project>.llms/`` from its stem) and
``<out>/<project>.pages.json`` (the inventory the skill reads back).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

BANNER = "=" * 90

#: What we know how to read as text. Anything else is listed as `skipped` with
#: its extension so the caller can convert it first (pandoc for .docx,
#: pdftotext for .pdf) rather than silently losing it.
TEXT_SUFFIXES = frozenset({".md", ".markdown", ".mdx", ".txt", ".text", ".rst", ".org"})
HTML_SUFFIXES = frozenset({".html", ".htm"})

#: Below this a page is an empty shell; `export_llms.MIN_PAGE_CHARS` uses the
#: same number, so a page kept here is a page that survives export.
MIN_PAGE_CHARS = 40

#: ATX only, exactly as `llms_lint.H_RE` — the anchors this script promises are
#: the anchors that parser will find, or they are worthless.
_H_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_SETEXT_RE = re.compile(r"^(=+|-+)\s*$")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
_FM_TITLE_RE = re.compile(r"^title\s*:\s*[\"']?(.+?)[\"']?\s*$", re.M)
_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_RE = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)


def slug(text: str) -> str:
    """Heading -> anchor slug, identical to `docset_refine.slug`.

    Kept as a copy rather than an import so this script runs standalone next to
    notes that are nowhere near a hub checkout. The two must not drift: an
    anchor that differs from the one the hub generates is an unresolved anchor.
    """
    s = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[\s_-]+", "-", s)


def _read(path: Path) -> str | None:
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    text = raw.decode("utf-8", errors="replace")
    # A BOM survives into the first heading and breaks its slug (P14 H1).
    return text.lstrip("﻿")


def _html_to_text(html: str) -> str:
    """Enough HTML to keep headings; not a parser and not pretending to be one.

    Headings become ATX so the heading walk below finds them; everything else
    loses its tags. A note dump full of real HTML deserves a real converter —
    this is the fallback that stops an `.html` note from being dropped.
    """
    body = _SCRIPT_RE.sub("", html)
    for level in range(1, 7):
        body = re.sub(
            rf"<h{level}\b[^>]*>(.*?)</h{level}>",
            lambda m, level=level: f"\n\n{'#' * level} {_TAG_RE.sub('', m.group(1)).strip()}\n\n",
            body,
            flags=re.S | re.I,
        )
    body = re.sub(r"<(br|/p|/div|/li)\b[^>]*>", "\n", body, flags=re.I)
    body = _TAG_RE.sub("", body)
    return re.sub(r"\n{3,}", "\n\n", body)


def _strip_frontmatter(text: str) -> tuple[str, str | None]:
    """Return (body, title-from-frontmatter).

    YAML front matter is metadata, not content: left in place it becomes a fake
    first paragraph and every unit extracted from it is unanchored.
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return text, None
    title = _FM_TITLE_RE.search(m.group(1))
    return text[m.end():], (title.group(1).strip() if title else None)


def setext_to_atx(text: str) -> str:
    """Rewrite ``Title\\n=====`` as ``# Title`` (and ``---`` as ``## Title``).

    Required, not cosmetic: `llms_lint._mirror_headings` matches ATX only, so a
    setext heading contributes no anchor and every unit aimed at it fails P7 R3.
    Fenced code is left alone — a ``---`` inside a fence is not a heading.
    """
    lines = text.split("\n")
    out: list[str] = []
    fence: str | None = None
    i = 0
    while i < len(lines):
        line = lines[i]
        f = _FENCE_RE.match(line)
        if f:
            marker = f.group(1)
            fence = None if fence and marker == fence else (fence or marker)
            out.append(line)
            i += 1
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if (
            fence is None
            and line.strip()
            and not _H_RE.match(line)
            and _SETEXT_RE.match(nxt)
            # A single "-" run under a line could be a list or a table rule; a
            # setext underline is at least two characters and the text above it
            # is not itself a list item.
            and len(nxt.strip()) >= 2
            and not line.lstrip().startswith(("-", "*", "+", "|", ">"))
        ):
            out.append(f"{'#' if nxt.strip().startswith('=') else '##'} {line.strip()}")
            i += 2
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def _headings(text: str) -> list[dict]:
    """Every ATX heading, with the anchor a unit may point at.

    Repeated headings share one anchor and are marked ``duplicate``: the linter
    collects anchors into a set, so a ``-2`` suffix would resolve to nothing.
    """
    out: list[dict] = []
    seen: set[str] = set()
    fence: str | None = None
    for i, line in enumerate(text.split("\n"), 1):
        f = _FENCE_RE.match(line)
        if f:
            marker = f.group(1)
            fence = None if fence and marker == fence else (fence or marker)
            continue
        if fence is not None:
            continue
        m = _H_RE.match(line)
        if not m:
            continue
        title = m.group(2).strip()
        anchor = slug(title)
        if not title or not anchor:
            continue
        out.append(
            {
                "level": len(m.group(1)),
                "title": title,
                "anchor": anchor,
                "line": i,
                "duplicate": anchor in seen,
            }
        )
        seen.add(anchor)
    return out


def _title(path: Path, fm_title: str | None, headings: list[dict]) -> str:
    if fm_title:
        return fm_title
    for h in headings:
        if h["level"] == 1:
            return h["title"]
    if headings:
        return headings[0]["title"]
    stem = re.sub(r"[_-]+", " ", path.stem).strip()
    # Obsidian/Notion exports carry a hash suffix on every filename; it is noise
    # in a link name and noise in a description.
    stem = re.sub(r"\s+[0-9a-f]{8,32}$", "", stem)
    return stem[:1].upper() + stem[1:] if stem else path.name


def _iter_inputs(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(sorted(q for q in p.rglob("*") if q.is_file()))
        elif p.is_file():
            files.append(p)
    return [f for f in files if not any(part.startswith(".") for part in f.parts)]


def _relpath(path: Path, roots: list[Path]) -> str:
    for root in roots:
        try:
            rel = path.resolve().relative_to(root.resolve())
        except ValueError:
            continue
        return rel.as_posix()
    return path.name


def normalise(
    inputs: list[Path], *, project: str, base_url: str | None = None
) -> tuple[list[dict], dict]:
    """(pages, report). A page is ``{url, path, title, text, headings, ...}``."""
    roots = [p for p in inputs if p.is_dir()] or [p.parent for p in inputs]
    pages: list[dict] = []
    report = {
        "project": project,
        "files_seen": 0,
        "dropped_empty_pages": 0,
        "dropped_duplicates": 0,
        "skipped_unreadable": [],
        "pages_without_headings": [],
        "duplicate_anchors": [],
    }
    by_hash: dict[str, str] = {}

    for path in _iter_inputs(inputs):
        suffix = path.suffix.lower()
        if suffix not in TEXT_SUFFIXES and suffix not in HTML_SUFFIXES:
            report["skipped_unreadable"].append(
                {
                    "path": _relpath(path, roots),
                    "reason": f"unsupported suffix {suffix or '(none)'}",
                }
            )
            continue
        report["files_seen"] += 1
        raw = _read(path)
        if raw is None:
            report["skipped_unreadable"].append(
                {"path": _relpath(path, roots), "reason": "unreadable"}
            )
            continue

        text = _html_to_text(raw) if suffix in HTML_SUFFIXES else raw
        text, fm_title = _strip_frontmatter(text)
        text = unicodedata.normalize("NFC", text.replace("\r\n", "\n"))
        text = setext_to_atx(text).strip()

        rel = _relpath(path, roots)
        if len(text) < MIN_PAGE_CHARS:
            report["dropped_empty_pages"] += 1
            continue

        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if digest in by_hash:
            report["dropped_duplicates"] += 1
            continue
        by_hash[digest] = rel

        headings = _headings(text)
        if not headings:
            report["pages_without_headings"].append(rel)
        for h in headings:
            if h["duplicate"]:
                report["duplicate_anchors"].append({"path": rel, "anchor": h["anchor"]})

        base = base_url.rstrip("/") if base_url else f"/{project}"
        pages.append(
            {
                "url": f"{base}/{rel}",
                "path": rel,
                "title": _title(path, fm_title, headings),
                "text": text,
                "sha256": digest,
                "bytes": len(text.encode("utf-8")),
                "headings": headings,
            }
        )

    report["pages"] = len(pages)
    report["headings"] = sum(len(p["headings"]) for p in pages)
    return pages, report


def write_mirror(pages: list[dict], path: Path) -> int:
    """The banner mirror, byte-compatible with `mirror_io.write_pages`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for page in pages:
            fh.write(f"\n\n{BANNER}\nURL: {page['url']}\n{BANNER}\n\n{page['text']}\n")
    os.replace(tmp, path)
    return len(pages)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("inputs", nargs="+", type=Path, help="note files and/or directories")
    ap.add_argument(
        "--project", required=True, help="slug for this project; used in every page source"
    )
    ap.add_argument("--out", type=Path, default=Path("."), help="output directory")
    ap.add_argument(
        "--base-url",
        default=None,
        help="absolute URL the pages are (or will be) served from, e.g. "
        "https://example.com/u/me/notes; default is root-relative /<project>",
    )
    args = ap.parse_args(argv)

    project = slug(args.project)
    if not project:
        print("--project must contain at least one word character", file=sys.stderr)
        return 2

    pages, report = normalise(args.inputs, project=project, base_url=args.base_url)
    if not pages:
        print("no readable pages found; nothing written", file=sys.stderr)
        print(json.dumps(report, indent=1), file=sys.stderr)
        return 1

    # `<project>.md`, not `<project>.mirror.md`: docset_refine derives
    # `<stem>.reference/` and `<stem>.llms/` from the stem, and a two-part stem
    # produces `<project>.mirror.llms/`, which no documented command expects.
    mirror = args.out / f"{project}.md"
    write_mirror(pages, mirror)
    inventory = args.out / f"{project}.pages.json"
    inventory.write_text(
        json.dumps(
            {
                "report": report,
                # Bodies stay in the mirror; the inventory is the small file the
                # agent reads to plan sections and anchors.
                "pages": [{k: v for k, v in p.items() if k != "text"} for p in pages],
            },
            indent=1,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"{mirror}  ({report['pages']} pages, {report['headings']} headings)")
    print(f"{inventory}")
    if report["dropped_empty_pages"]:
        print(f"dropped {report['dropped_empty_pages']} empty page(s)")
    if report["dropped_duplicates"]:
        print(f"dropped {report['dropped_duplicates']} duplicate page(s)")
    if report["pages_without_headings"]:
        n = len(report["pages_without_headings"])
        print(f"{n} page(s) have no headings — their units carry the page URL with no anchor")
    if report["duplicate_anchors"]:
        n = len(report["duplicate_anchors"])
        print(f"{n} repeated heading(s) share an anchor; see {inventory}")
    if report["skipped_unreadable"]:
        print(f"skipped {len(report['skipped_unreadable'])} file(s); see {inventory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
