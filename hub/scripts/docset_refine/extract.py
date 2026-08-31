"""extract — deterministic reference units, no LLM.

Every fenced code block becomes a `snippet` captioned by its nearest heading,
every markdown table row a `parameter`, every H2/H3 with a real first
paragraph a `definition`, and every changelog entry a `change`. This is the
highest-precision material and exactly what trafilatura used to lose.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from . import mirror_io, new_unit, reference_dir, slug
from .clean import _HEADING_RE, changelog_entries

_TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_FENCE_RE = re.compile(r"^(\s*)```([\w+.-]*)\s*(.*?)\s*$")
_SENT_END_RE = re.compile(r"(?<=[.!?])\s+")
MAX_DEF_CHARS = 300
MAX_SNIPPET_CAPTION = 120
MAX_UNIT_CHARS = 400          # a unit is one claim; longer text is the page's job (lint P7)
MAX_DEF_SENTENCES = 2
MAX_LEAD_CHARS = 200          # "… supports the following:" — a lead-in, not yet a claim


def _clip(text: str, limit: int = MAX_UNIT_CHARS) -> str:
    """Cut at the last word boundary under `limit`, marking the cut."""
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:—-")
    return f"{cut}…"


def real_headings(pages: list[dict]) -> dict[str, set[str]]:
    """url -> heading slugs that exist on the SOURCE page. Cleaning turns MDX
    <Step>/<Tab>/<Accordion> titles into headings the site never renders as
    anchors, so a unit filed under one would point nowhere (1,124 of 11,965
    units on the code.claude.com pilot); extractors anchor to the nearest
    real heading above instead."""
    out: dict[str, set[str]] = {}
    for p in pages:
        slugs = set()
        in_fence = False
        for ln in p.get("text", "").splitlines():
            if ln.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            m = _HEADING_RE.match(ln)
            if m:
                slugs.add(slug(m.group(2).strip()))
        out[p["url"].rstrip("/")] = slugs
    return out


def _cells(row: str) -> list[str]:
    inner = row.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", inner)]


def _walk(text: str, real: set[str] | None = None):
    """Yield (kind, payload) events: heading, fence (lang, title, body,
    heading), table (header, rows, heading), para (text, heading). Every
    payload also carries `anchor_heading`: the nearest heading above that
    exists on the source page (`real` slugs), so anchors always resolve."""
    lines = text.splitlines()
    heading = ""
    anchor_heading = ""
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        m = _FENCE_RE.match(line)
        if m:
            indent, lang, title = m.group(1), m.group(2), m.group(3)
            body = []
            i += 1
            while i < n and not lines[i].lstrip().startswith("```"):
                body.append(lines[i][len(indent):] if lines[i].startswith(indent) else lines[i])
                i += 1
            i += 1  # closing fence
            yield "fence", {"lang": lang, "title": title, "body": "\n".join(body).strip("\n"),
                            "heading": heading, "anchor_heading": anchor_heading}
            continue
        hm = _HEADING_RE.match(line)
        if hm:
            heading = hm.group(2).strip()
            if real is None or slug(heading) in real:
                anchor_heading = heading
            yield "heading", {"level": len(hm.group(1)), "text": heading,
                              "anchor_heading": anchor_heading}
            i += 1
            continue
        if _TABLE_ROW_RE.match(line) and i + 1 < n and _TABLE_SEP_RE.match(lines[i + 1]):
            header = _cells(line)
            rows = []
            i += 2
            while i < n and _TABLE_ROW_RE.match(lines[i]):
                rows.append(_cells(lines[i]))
                i += 1
            yield "table", {"header": header, "rows": rows, "heading": heading,
                            "anchor_heading": anchor_heading}
            continue
        if line.strip():
            para = [line.strip()]
            i += 1
            while (i < n and lines[i].strip() and not _FENCE_RE.match(lines[i])
                   and not _HEADING_RE.match(lines[i]) and not _TABLE_ROW_RE.match(lines[i])):
                para.append(lines[i].strip())
                i += 1
            yield "para", {"text": " ".join(para), "heading": heading,
                           "anchor_heading": anchor_heading}
            continue
        i += 1


def _anchor(heading: str) -> str:
    return f"#{slug(heading)}" if heading else ""


def _first_code_line(body: str) -> str:
    for ln in body.splitlines():
        s = ln.strip()
        if s and not s.startswith(("#", "//")):
            return s
    return body.strip().splitlines()[0] if body.strip() else ""


def _real_for(page: dict, real) -> set[str] | None:
    return None if real is None else real.get(page["url"].rstrip("/"), set())


def snippets(page: dict, start: int = 1, real=None) -> list[dict]:
    out = []
    seq = start
    for kind, ev in _walk(page["text"], _real_for(page, real)):
        if kind != "fence" or not ev["body"].strip():
            continue
        caption = ev["title"] or ev["heading"] or page.get("title", "")
        first = _first_code_line(ev["body"])[:MAX_SNIPPET_CAPTION]
        text = f"{caption}: {first}" if caption else first
        out.append(new_unit(seq, type="snippet", text=_clip(text), source_url=page["url"],
                            anchor=_anchor(ev["anchor_heading"]), page_class=page.get("class", ""),
                            keywords=[k for k in (ev["lang"], ev["title"]) if k],
                            code={"lang": ev["lang"], "body": ev["body"]}, origin="code"))
        seq += 1
    return out


def tables(page: dict, start: int = 1, real=None) -> list[dict]:
    out = []
    seq = start
    for kind, ev in _walk(page["text"], _real_for(page, real)):
        if kind != "table":
            continue
        header = ev["header"]
        for row in ev["rows"]:
            if not row or not row[0]:
                continue
            first, rest = row[0], row[1:]
            if len(rest) == 1:
                text = f"{first}: {rest[0]}"
            else:
                pairs = [f"{h}={v}" for h, v in zip(header[1:], rest, strict=False) if v]
                text = f"{first}: " + "; ".join(pairs) if pairs else first
            out.append(new_unit(seq, type="parameter", text=_clip(text), source_url=page["url"],
                                anchor=_anchor(ev["anchor_heading"]),
                                page_class=page.get("class", ""),
                                keywords=header, origin="table"))
            seq += 1
    return out


def definitions(page: dict, start: int = 1, real=None) -> list[dict]:
    """The first paragraph after each heading (H1-H3), trimmed to whole
    sentences under MAX_DEF_CHARS and MAX_DEF_SENTENCES (a single run-on
    sentence is clipped at a word boundary).

    A first paragraph that only introduces what follows ("… supports the
    following:") is a promise, not a claim: the items that answer it live in
    the next block, which the old rule skipped for starting with `- `. Such a
    lead-in is held and merged with the block after it, so the unit carries its
    body. A lead-in followed by a table or code fence is emitted unchanged —
    those bodies are extracted as their own units."""
    out = []
    seq = start
    pending: dict | None = None
    lead = ""

    def emit(head: dict, para: str, seq: int) -> int:
        kept = ""
        for n_sent, sent in enumerate(_SENT_END_RE.split(para)):
            if n_sent >= MAX_DEF_SENTENCES:
                break
            if kept and len(kept) + len(sent) + 1 > MAX_DEF_CHARS:
                break
            kept = f"{kept} {sent}".strip()
        kept = _clip(kept, MAX_DEF_CHARS)
        out.append(new_unit(seq, type="definition", text=f"{head['text']} — {kept}",
                            source_url=page["url"],
                            anchor=_anchor(head["anchor_heading"]),
                            page_class=page.get("class", ""),
                            keywords=[head["text"]], origin="heading"))
        return seq + 1

    for kind, ev in _walk(page["text"], _real_for(page, real)):
        if kind == "heading":
            if pending is not None and lead:
                seq = emit(pending, lead, seq)
            pending = ev if ev["level"] <= 3 else None
            lead = ""
            continue
        if kind == "para" and pending is not None:
            para = ev["text"]
            if not lead and para.endswith(":") and len(para) <= MAX_LEAD_CHARS:
                lead = para                     # hold: the claim is in the next block
                continue
            if lead:
                para = f"{lead} {para}"
            elif para.startswith(("**", "- ", "* ", "|")):
                pending = None
                continue
            if len(para) >= 40:
                seq = emit(pending, para, seq)
            pending = None
            lead = ""
        elif kind != "para":
            if pending is not None and lead:
                seq = emit(pending, lead, seq)   # table/fence body is its own unit
            pending = None
            lead = ""
    if pending is not None and lead:
        seq = emit(pending, lead, seq)
    return out


def changes(page: dict, start: int = 1, real=None) -> list[dict]:
    out = []
    seq = start
    mine = _real_for(page, real)
    for e in changelog_entries(page["text"]):
        body = re.sub(r"\s+", " ", e["text"]).strip()
        if not body:
            continue
        label = e["version"] or e["date"] or e["heading"]
        head = e["heading"] if mine is None or slug(e["heading"]) in mine else ""
        out.append(new_unit(seq, type="change", text=_clip(f"{label}: {body}"),
                            source_url=page["url"], anchor=_anchor(head),
                            page_class="changelog",
                            keywords=[k for k in (e["version"], e["date"]) if k],
                            origin="changelog"))
        seq += 1
    return out


def run(mirror: Path) -> dict:
    mirror = Path(mirror)
    ref = reference_dir(mirror)
    pages = mirror_io.load_json(ref / "pages.json", default=None)
    if pages is None:
        raise SystemExit(f"{ref / 'pages.json'} missing — run `clean` first")
    real = real_headings(mirror_io.read_pages(mirror)) if mirror.exists() else None
    units: list[dict] = []
    seq = 1
    counts: Counter[str] = Counter()
    for page in pages:
        passes = (changes,) if page.get("class") == "changelog" else (snippets, tables, definitions)
        for fn in passes:
            got = fn(page, seq, real)
            seq += len(got)
            units.extend(got)
            counts.update(u["origin"] for u in got)
    mirror_io.write_jsonl(units, ref / "structured.jsonl")
    return {"pages": len(pages), "units": len(units), **dict(counts)}
