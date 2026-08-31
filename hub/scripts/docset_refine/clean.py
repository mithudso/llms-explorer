"""clean — strip cross-page boilerplate, triage pages, parse changelogs.

Deterministic and token-free. Writes `<stem>.clean.md` (a banner mirror of
the stripped reference/guide/changelog pages — the raw index is built from
this) and `<stem>.reference/pages.json` (per-page url/class/title/headings/
text for the extraction passes).
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from . import clean_mirror_path, mirror_io, reference_dir

CLASSES = ("reference", "guide", "changelog", "marketing", "index")
_LINK_ONLY_RE = re.compile(r"^\s*\[[^\]]*\]\([^)]*\)\s*[.,;:]?\s*$")
_IMG_ONLY_RE = re.compile(r"^\s*!\[[^\]]*\]\([^)]*\)\s*$")
_NAV_BULLET_RE = re.compile(r"^\s*[-*]\s+[A-Za-z][\w .()/+-]{0,30}$")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
_VERSION_RE = re.compile(r"^#{1,4}\s*\[?v?(\d+\.\d+[\w.\-]*)\]?")
_ISO_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
_MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august",
           "september", "october", "november", "december"]
_LONG_DATE_RE = re.compile(
    r"\b(" + "|".join(m.capitalize() for m in _MONTHS) + r")\s+(\d{1,2}),?\s+(\d{4})\b")

MARKETING_SEGMENTS = {"blog", "customers", "pricing", "contact-sales", "contact", "community",
                      "careers", "about", "press", "enterprise", "solutions", "partners",
                      "events", "webinars", "case-studies", "newsroom", "legal"}
CHANGELOG_SEGMENTS = {"changelog", "release-notes", "releases", "whats-new", "changes"}
REFERENCE_HINTS = ("reference", "api", "cli", "env", "errors", "settings", "hooks", "sdk",
                   "schema", "commands", "options", "flags", "config", "spec")
NAV_RUN_MIN = 4

# MDX components (Mintlify / Fern docs export them raw in llms-full.txt).
_MDX_TITLED = {"Step": "### {title}", "Tab": "**{title}**", "Accordion": "#### {title}",
               "Card": "**{title}**", "Expandable": "#### {title}",
               "ParamField": "- `{name}` ({type}) — ", "ResponseField": "- `{name}` ({type}) — "}
_MDX_CALLOUT = {"Tip", "Note", "Warning", "Info", "Check", "Danger", "Callout"}
_MDX_DROP = {"Steps", "Tabs", "CodeGroup", "Frame", "AccordionGroup", "CardGroup", "Columns",
             "Snippet", "Tooltip", "Icon", "img", "br", "video", "iframe", "Embed", "Update"}
_ATTR = r"(?:\s+[\w-]+(?:=(?:\"[^\"]*\"|\'[^\']*\'|\{[^}]*\}))?)*"
_MDX_OPEN_RE = re.compile(r"^\s*<([A-Za-z][\w.]*)(" + _ATTR + r")\s*/?>\s*$")
_MDX_CLOSE_RE = re.compile(r"^\s*</([A-Za-z][\w.]*)>\s*$")
_MDX_INLINE_CALLOUT_RE = re.compile(
    r"^\s*<(" + "|".join(sorted(_MDX_CALLOUT)) + r")>\s*(\S.*?)\s*(?:</\1>)?\s*$")
_MDX_ATTR_RE = re.compile(r"([\w-]+)=(?:\"([^\"]*)\"|\'([^\']*)\')")
_MDX_COMMENT_RE = re.compile(r"\{/\*.*?\*/\}")
_HTML_TAGS = ("div|span|p|td|tr|th|table|tbody|thead|ul|ol|li|a|b|i|em|strong|code|pre|"
              "section|sup|sub|small|hr|h[1-6]")
_HTML_LINE_RE = re.compile(r"^\s*</?(" + _HTML_TAGS + r")(\s[^>]*)?/?>\s*$")
_FENCE_META_RE = re.compile(r"\s+\w+=\{[^}]*\}")  # ```bash theme={null}


def _attrs(raw: str) -> dict:
    return {k: (v1 if v1 is not None else v2) for k, v1, v2 in _MDX_ATTR_RE.findall(raw)}


def mdx_to_markdown(text: str) -> str:
    """Flatten MDX components into plain markdown so they neither pollute the
    fact layer nor hide their titles: `<Step title=X>` -> `### X`, callouts
    -> `**Tip:**`, `<Update label=L description=D>` -> `## L — D` (this is
    how Mintlify changelogs are structured), wrappers dropped, bare HTML
    tag lines dropped, `{/* */}` comments removed. Fences pass through."""
    out: list[str] = []
    in_fence = False
    for raw in text.splitlines():
        if raw.lstrip().startswith("```"):
            # opener: drop MDX props like theme={null}; closer: unchanged
            out.append(_FENCE_META_RE.sub("", raw) if not in_fence else raw)
            in_fence = not in_fence
            continue
        if in_fence:
            out.append(raw)
            continue
        line = _MDX_COMMENT_RE.sub("", raw)
        m = _MDX_INLINE_CALLOUT_RE.match(line)
        if m:
            out.append(f"**{m.group(1)}:** {m.group(2)}")
            continue
        m = _MDX_OPEN_RE.match(line)
        if m:
            tag, attrs = m.group(1), _attrs(m.group(2))
            if tag == "Update":
                label, desc = attrs.get("label", ""), attrs.get("description", "")
                out.append(f"## {label}" + (f" — {desc}" if desc else ""))
            elif tag in _MDX_TITLED:
                fmt = _MDX_TITLED[tag]
                if tag in ("ParamField", "ResponseField"):
                    out.append(fmt.format(name=attrs.get("path") or attrs.get("query")
                                          or attrs.get("body") or attrs.get("header", "?"),
                                          type=attrs.get("type", "")))
                elif attrs.get("title"):
                    out.append(fmt.format(title=attrs["title"]))
            elif tag in _MDX_CALLOUT:
                out.append(f"**{tag}:**")
            elif tag in _MDX_DROP or _HTML_LINE_RE.match(line) or line.rstrip().endswith("/>"):
                pass  # wrapper, bare HTML, or a self-closing widget (<ContactSalesCard />)
            else:
                out.append(line)
            continue
        m = _MDX_CLOSE_RE.match(line)
        if m or _HTML_LINE_RE.match(line):
            continue
        out.append(line)
    return "\n".join(out)


def _norm(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


def _fence_toggle(line: str, in_fence: bool) -> bool:
    return not in_fence if line.lstrip().startswith("```") else in_fence


def boilerplate_lines(pages: list[dict], min_share: float = 0.05, min_pages: int = 3) -> set[str]:
    """Normalized non-fence lines present in >= min_share of pages (and in at
    least min_pages pages): site chrome, footers, repeated CTAs. Headings and
    table separator rows are exempt — '## Overview' legitimately recurs."""
    counts: Counter[str] = Counter()
    for pg in pages:
        seen = set()
        in_fence = False
        for raw in pg["text"].splitlines():
            in_fence = _fence_toggle(raw, in_fence)
            if in_fence or raw.lstrip().startswith("```"):
                continue
            line = _norm(raw)
            if len(line) < 8 or _HEADING_RE.match(line) or set(line) <= set("|-: "):
                continue
            seen.add(line)
        counts.update(seen)
    n = max(1, len(pages))
    floor = max(min_pages, int(n * min_share + 0.999))
    return {line for line, c in counts.items() if c >= floor}


def is_link_only(line: str) -> bool:
    return bool(_LINK_ONLY_RE.match(line) or _IMG_ONLY_RE.match(line))


def strip_page(text: str, boiler: set[str]) -> str:
    """Drop boilerplate, link-only lines and runs of >= NAV_RUN_MIN short nav
    bullets. Fenced blocks pass through untouched. Collapses blank runs."""
    out: list[str] = []
    in_fence = False
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        if raw.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(raw)
            i += 1
            continue
        if in_fence:
            out.append(raw)
            i += 1
            continue
        if _NAV_BULLET_RE.match(raw):
            j = i
            while j < len(lines) and _NAV_BULLET_RE.match(lines[j]):
                j += 1
            if j - i >= NAV_RUN_MIN:
                i = j
                continue
        if _norm(raw) in boiler or is_link_only(raw):
            i += 1
            continue
        out.append(raw)
        i += 1
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip("\n")


def headings(text: str) -> list[str]:
    hs = []
    in_fence = False
    for raw in text.splitlines():
        in_fence = _fence_toggle(raw, in_fence)
        if in_fence:
            continue
        m = _HEADING_RE.match(raw)
        if m:
            hs.append(m.group(2).strip())
    return hs


def title_of(text: str, url: str) -> str:
    for raw in text.splitlines():
        m = _HEADING_RE.match(raw)
        if m:
            return m.group(2).strip()
    return urlparse(url).path.rstrip("/").rsplit("/", 1)[-1] or url


def _shape(text: str) -> dict:
    fences = tables = links = nonblank = 0
    body_chars = 0
    in_fence = False
    for raw in text.splitlines():
        if raw.lstrip().startswith("```"):
            in_fence = not in_fence
            fences += 1
            continue
        if in_fence or not raw.strip():
            continue
        nonblank += 1
        if _TABLE_ROW_RE.match(raw) and not set(raw.strip()) <= set("|-: "):
            tables += 1
        if is_link_only(raw):
            links += 1
        elif not _HEADING_RE.match(raw):
            body_chars += len(raw.strip())
    return {"fences": fences // 2, "tables": tables, "links": links,
            "nonblank": nonblank, "body_chars": body_chars}


def classify(url: str, text: str) -> str:
    path = urlparse(url).path.lower()
    segs = [s for s in path.split("/") if s]
    last = segs[-1] if segs else ""
    if last in CHANGELOG_SEGMENTS:
        return "changelog"
    if not segs or any(s in MARKETING_SEGMENTS for s in segs):
        return "marketing"
    sh = _shape(text)
    hinted = any(h in path for h in REFERENCE_HINTS)
    structured = sh["fences"] + sh["tables"] > 0
    # Reference signals beat thinness: a short page of tables/snippets at a
    # reference URL is reference material, not a link farm.
    if ((hinted and (structured or sh["body_chars"] >= 400))
            or sh["tables"] >= 3 or sh["fences"] >= 5):
        return "reference"
    if sh["body_chars"] < 400 or (sh["nonblank"] and sh["links"] / sh["nonblank"] > 0.6):
        return "index"
    return "guide"


def changelog_entries(text: str) -> list[dict]:
    """Split a changelog at version headings (`## 2.1.0`, `## v2.1.0`) or date
    headings (`## August 19, 2026`, `## 2026-08-19`)."""
    entries: list[dict] = []
    cur: dict | None = None
    in_fence = False
    for raw in text.splitlines():
        in_fence = _fence_toggle(raw, in_fence)
        if not in_fence and raw.startswith("#"):
            vm = _VERSION_RE.match(raw)
            dm = _ISO_DATE_RE.search(raw) or _LONG_DATE_RE.search(raw)
            if vm or dm:
                if cur:
                    entries.append(cur)
                date = None
                if dm:
                    if dm.re is _ISO_DATE_RE:
                        date = dm.group(1)
                    else:
                        date = (f"{dm.group(3)}-{_MONTHS.index(dm.group(1).lower()) + 1:02d}"
                                f"-{int(dm.group(2)):02d}")
                cur = {"version": vm.group(1) if vm else None, "date": date,
                       "heading": raw.lstrip("# ").strip(), "lines": []}
                continue
        if cur is not None:
            cur["lines"].append(raw)
    if cur:
        entries.append(cur)
    for e in entries:
        e["text"] = "\n".join(e.pop("lines")).strip("\n")
    return entries


def run(mirror: Path, min_share: float = 0.05) -> dict:
    mirror = Path(mirror)
    pages = mirror_io.read_pages(mirror)
    pages = [{"url": pg["url"], "text": mdx_to_markdown(pg["text"])} for pg in pages]
    boiler = boilerplate_lines(pages, min_share=min_share)
    kept: list[dict] = []
    meta: list[dict] = []
    classes: Counter[str] = Counter()
    dropped_lines = 0
    for pg in pages:
        cls = classify(pg["url"], pg["text"])
        classes[cls] += 1
        if cls in ("marketing", "index"):
            continue
        stripped = strip_page(pg["text"], boiler)
        dropped_lines += pg["text"].count("\n") - stripped.count("\n")
        kept.append({"url": pg["url"], "text": stripped})
        meta.append({"url": pg["url"], "class": cls, "title": title_of(stripped, pg["url"]),
                     "headings": headings(stripped), "text": stripped})
    mirror_io.write_pages(kept, clean_mirror_path(mirror))
    mirror_io.save_json(meta, reference_dir(mirror) / "pages.json")
    return {"pages": len(pages), "kept": len(kept), "dropped_lines": dropped_lines,
            "boilerplate_lines": len(boiler), "classes": dict(classes)}
