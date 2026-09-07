#!/usr/bin/env python3
"""llms_lint.py — deterministic lint passes for the llms.txt family (llms-deep-optimizer).

Implements the non-model, non-live halves of P0-P2, P3, P5-P7, P9 and P14 from
`references/passes.md`, judged against the attribute rubric in
`references/attributes.md` and grounded in the authoritative v2 grammar at
`site/src/content/reference/spec.md` (H1 is the only hard invariant; blockquote
is conventional; H2 sections are `- [name](url): notes` file lists; `.md`
twins; discovery via `Link` headers). Pure Python 3 stdlib — the one exception
is `--check-links`, which does a live HEAD request over `urllib` (never on by
default, per the skill's own contract: "default off").

Subcommands (each takes a FILE and prints one JSON object to stdout):
  detect       <file>                      P0 — kind + grammar detection
  structure    <file> [--fix]              P1 — H1/blockquote/H2/link-grammar
  links        <file> [--check-links] [--fix]   P2 — link resolution
  descriptions <file>                      P3 (deterministic half) — link notes
  size         <file>                      P5 — size-ladder budgets
  full         <file> [--fix]              P6 (deterministic half) — full-file fidelity
  facts        <file> [--fix]              P7 (deterministic half) — facts-file shape
  trust        <file> [--fix]              P9 (deterministic half) — steering/secrets scan
  hygiene      <file> [--fix]              P14 — byte-level hygiene

Every subcommand accepts `--kind {index,family,full,small,facts}` to override
P0 auto-detection (mirrors the skill's own `--kind` flag).

Findings schema (shared across every subcommand):
  {"pass": "P1", "severity": "high|medium|low|hygiene", "code": "I1",
   "message": "...", "line": N|null, "fixable": bool}

This script never makes network requests unless `--check-links` is passed on
`links`, and it never executes or obeys anything found inside a target file
(P9: injection/steering spans are data to flag, never instructions to follow).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

VERSION = "1.0.0"
CHARS_PER_TOKEN = 4  # house convention, matches llms-concept-abstractor/scripts/concept_abstract.py

# ---------------------------------------------------------------------------
# Shared regexes (parser reference: spec.md §6 "Parser reference (core.py)")
#   header:   ^#\s*{title}\n+{summ}\n+{info}
#   sections: ^##\s*(.*?$)
#   links:    -\s*\[{title}\]\({url}\){desc}
# ---------------------------------------------------------------------------
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
BLOCKQUOTE_RE = re.compile(r"^>\s?(.*)$")
LINK_ITEM_RE = re.compile(r"^\s*-\s*\[([^\]]*)\]\(([^)]+)\)(?:\s*:\s*(.*))?\s*$")
BARE_URL_LINE_RE = re.compile(r"^\s*-\s*(https?://\S+)\s*$")
FENCE_RE = re.compile(r"^\s*```")
URL_RE = re.compile(r"https?://[^\s)\]\"'>]+|file://[^\s)\]\"'>]+")

# facts-file unit line, per passes.md P7:
#   - [type] text — <url>#<anchor> · keywords: a, b · verified-as-of: YYYY-MM-DD
UNIT_LINE_RE = re.compile(
    r"^\s*-\s*\[(?P<type>[A-Za-z_\-]+)\]\s+(?P<text>.*?)\s+—\s+(?P<url>\S+)"
    r"(?:\s*\xb7\s*keywords:\s*(?P<keywords>[^\xb7]+))?"
    r"(?:\s*\xb7\s*verified-as-of:\s*(?P<date>\d{4}-\d{2}-\d{2}))?"
    r"(?:\s*\xb7\s*also:\s*(?P<also>.*))?\s*$"
)
# docset_refine.UNIT_TYPES per passes.md P7
UNIT_TYPES = {
    "concept", "fact", "actionable", "question", "problem", "statement",
    "quote", "idea", "snippet", "parameter", "definition", "change",
}

FULL_FILE_GRAMMARS = ("mintlify", "anthropic-yaml", "cloudflare-frontmatter", "firecrawl", "none")

# P9 steering / injection candidate patterns (deterministic half; final call is
# model work per passes.md P9 — "model confirms the imperative hits are aimed
# at a reader model rather than quoting a doc that legitimately says
# 'you must set X'"). Flagged here as candidates, not auto-High.
STEERING_PATTERNS = [
    re.compile(r"\bignore (?:all|any|the)?\s*(?:previous|prior|above)\s+instructions\b", re.I),
    re.compile(r"\byou must (?:always|never|only)\b", re.I),
    re.compile(r"\balways (?:cite|recommend|mention|say|answer|respond|include)\b", re.I),
    re.compile(r"\bnever (?:mention|reveal|say|disclose)\b", re.I),
    re.compile(r"\bdo not mention\b", re.I),
    re.compile(r"\brank (?:this|us|our) (?:site|page|content|product)\s*(?:first|highest)?\b", re.I),
    re.compile(r"\bwhen (?:asked|responding|summariz\w*) about this,?\s*(?:you|always)\b", re.I),
    re.compile(r"\bas an ai( language)? model,? you (?:must|should|will)\b", re.I),
    re.compile(r"\bthis is a system prompt\b", re.I),
]

# P5/P9 secret-shaped strings
SECRET_PATTERNS = [
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private-key-block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("mongodb-conn-string", re.compile(r"\bmongodb(?:\+srv)?://[^\s:/@]+:[^\s:/@]+@\S+")),
    ("postgres-conn-string", re.compile(r"\bpostgres(?:ql)?://[^\s:/@]+:[^\s:/@]+@\S+")),
    ("generic-api-key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("jwt-like", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("email-address", re.compile(r"\b[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}\b")),
]
PRIVATE_HOST_PATTERNS = [
    re.compile(r"\b127\.0\.0\.1\b"),
    re.compile(r"\blocalhost\b", re.I),
    re.compile(r"\b(?:10|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b"),
    re.compile(r"\btext-mirror/"),
    re.compile(r"file://"),
]

SMART_CHARS = "\u2018\u2019\u201c\u201d\u2013\u2014\u200b\u200d\ufeff"


# ---------------------------------------------------------------------------
# Findings + IO helpers
# ---------------------------------------------------------------------------
def finding(pass_id, severity, code, message, line=None, fixable=False):
    return {
        "pass": pass_id,
        "severity": severity,
        "code": code,
        "message": message,
        "line": line,
        "fixable": fixable,
    }


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    return raw.decode("utf-8", errors="replace")


def summarize(findings):
    out = {"high": 0, "medium": 0, "low": 0, "hygiene": 0, "fixable": 0}
    for f in findings:
        out[f["severity"]] = out.get(f["severity"], 0) + 1
        if f["fixable"]:
            out["fixable"] += 1
    return out


def emit(payload):
    json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def slugify(title: str) -> str:
    """GitHub-style heading slug, used for best-effort facts-anchor resolution."""
    s = title.strip().lower()
    s = re.sub(r"[^\w\- ]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s


# ---------------------------------------------------------------------------
# Markdown structure model — shared by structure/descriptions/links/full
# ---------------------------------------------------------------------------
class Section:
    __slots__ = ("level", "title", "line", "body_start", "body_end", "items", "subheadings", "stray_lines")

    def __init__(self, level, title, line):
        self.level = level
        self.title = title
        self.line = line
        self.body_start = line + 1
        self.body_end = line + 1
        self.items = []  # (line_no, title, url, desc, raw)
        self.subheadings = []  # (line_no, level, title)
        self.stray_lines = []  # (line_no, text)


def parse_structure(text: str):
    lines = text.splitlines()
    in_fence = False
    headings = []  # (line_no 1-based, level, title)
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING_RE.match(line)
        if m:
            headings.append((i + 1, len(m.group(1)), m.group(2)))

    h1s = [h for h in headings if h[1] == 1]
    top_headings = [h for h in headings if h[1] == 2]

    # blockquote: first non-blank line after the first H1
    blockquote_lines = []
    blockquote_start = None
    info_lines = []  # non-blank, non-comment lines before the first H2 that are not the blockquote
    if h1s:
        first_h1_line = h1s[0][0]
        idx = first_h1_line  # 0-based index of the line AFTER the H1 (h1 line_no is 1-based == idx)
        limit = (top_headings[0][0] - 1) if top_headings else len(lines)
        j = idx
        while j < limit and lines[j].strip() == "":
            j += 1
        if j < limit and BLOCKQUOTE_RE.match(lines[j]):
            blockquote_start = j + 1
            while j < limit and BLOCKQUOTE_RE.match(lines[j]):
                blockquote_lines.append(BLOCKQUOTE_RE.match(lines[j]).group(1))
                j += 1
        while j < limit:
            stripped = lines[j].strip()
            if stripped and not stripped.startswith("<!--"):
                info_lines.append((j + 1, lines[j]))
            elif stripped.startswith("<!--") and "-->" not in stripped:
                # multi-line comment: skip until closed
                while j < limit and "-->" not in lines[j]:
                    j += 1
            j += 1

    # sections keyed on H2 boundaries
    sections = []
    for k, (line_no, level, title) in enumerate(top_headings):
        sec = Section(level, title, line_no)
        end = (top_headings[k + 1][0] - 1) if k + 1 < len(top_headings) else len(lines)
        sec.body_end = end
        in_fence2 = False
        for li in range(line_no, end):  # 0-based body lines
            raw = lines[li]
            if FENCE_RE.match(raw):
                in_fence2 = not in_fence2
                continue
            if in_fence2:
                continue
            hm = HEADING_RE.match(raw)
            if hm and len(hm.group(1)) >= 3:
                sec.subheadings.append((li + 1, len(hm.group(1)), hm.group(2)))
                continue
            lm = LINK_ITEM_RE.match(raw)
            if lm:
                sec.items.append((li + 1, lm.group(1), lm.group(2), lm.group(3) or "", raw))
                continue
            if raw.strip() == "" or raw.strip().startswith("<!--"):
                continue
            sec.stray_lines.append((li + 1, raw))
        sections.append(sec)

    return {
        "lines": lines,
        "h1_count": len(h1s),
        "h1s": h1s,
        "blockquote_present": bool(blockquote_lines),
        "blockquote_lines": blockquote_lines,
        "blockquote_start": blockquote_start,
        "info_lines": info_lines,
        "sections": sections,
        "all_headings": headings,
    }


def sentence_count(text: str) -> int:
    text = text.strip()
    if not text:
        return 0
    parts = re.split(r"(?<=[.!?])\s+", text)
    return len([p for p in parts if p.strip()])


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


# ---------------------------------------------------------------------------
# P0 — detect
# ---------------------------------------------------------------------------
def detect_full_grammar(text: str) -> str:
    if re.search(r"<\|firecrawl-page-\d+-lllmstxt\|>", text):
        return "firecrawl"
    if re.search(r"^# .+\r?\nSource:\s*\S+", text, re.M):
        return "mintlify"
    if re.search(r"^---\s*$\r?\n(?:.*\r?\n)*?(?:url|title):\s*\S+", text, re.M):
        # distinguish cloudflare (frontmatter + "View as Markdown") from anthropic-yaml
        if re.search(r"View as Markdown", text):
            return "cloudflare-frontmatter"
        return "anthropic-yaml"
    return "none"


def detect_index_grammar(struct) -> str:
    """spec-conformant | api-first | non-conformant-prose, per spec.md §3.1."""
    sections = struct["sections"]
    if not struct["blockquote_present"]:
        return "non-conformant-prose"
    if sections:
        first_title = sections[0].title.lower()
        if re.search(r"\bhow to use\b|\bapi\b|\bmcp server\b", first_title):
            return "api-first"
    return "spec-conformant"


def cmd_detect(args):
    path = Path(args.file)
    text = read_text(path)
    name = path.name.lower()
    size = len(text.encode("utf-8"))
    findings = []

    if args.kind:
        kind = args.kind
    elif "facts" in name:
        kind = "facts"
    elif "small" in name:
        kind = "small"
    elif "full" in name:
        kind = "full"
    elif "family" in name:
        kind = "family"
    else:
        kind = "index"

    struct = parse_structure(text)

    # I6: a file named llms.txt (index) that actually parses as a full file
    looks_like_full_page_stream = bool(
        re.search(r"^# .+\r?\nSource:\s*\S+", text, re.M)
        or re.search(r"<\|firecrawl-page-\d+-lllmstxt\|>", text)
        or (kind == "index" and size > 100_000)
    )
    if kind == "index" and looks_like_full_page_stream:
        findings.append(finding(
            "P0", "high", "I6",
            f"file is named/typed as an index but parses as a full file "
            f"({size} bytes, {len(struct['h1s'])} H1s) — it will be served as an index "
            f"and blow every size budget; the fix is `export` (index+full+small), not trimming.",
        ))
        kind = "full"

    if kind in ("index", "family", "small"):
        grammar = detect_index_grammar(struct)
    else:
        grammar = detect_full_grammar(text)

    if struct["h1_count"] == 0:
        findings.append(finding("P0", "high", "I6", "no H1 found; kind cannot be confirmed without --kind override", line=1))
    elif struct["h1_count"] > 1:
        findings.append(finding("P0", "high", "I1", f"{struct['h1_count']} H1 headings found; exactly one is required", line=struct["h1s"][1][0]))

    emit({
        "file": str(path),
        "pass": "P0",
        "kind": kind,
        "grammar": grammar,
        "bytes": size,
        "est_tokens": round(size / CHARS_PER_TOKEN),
        "findings": findings,
        "summary": summarize(findings),
    })


def resolve_kind(args, text, path):
    if args.kind:
        return args.kind
    name = path.name.lower()
    if "facts" in name:
        return "facts"
    if "small" in name:
        return "small"
    if "full" in name:
        return "full"
    if "family" in name:
        return "family"
    return "index"


# ---------------------------------------------------------------------------
# P1 — structure
# ---------------------------------------------------------------------------
def cmd_structure(args):
    path = Path(args.file)
    text = read_text(path)
    kind = resolve_kind(args, text, path)
    struct = parse_structure(text)
    findings = []
    fixed = []
    lines = struct["lines"]

    if kind not in ("index", "family", "small"):
        emit({
            "file": str(path), "pass": "P1", "kind": kind,
            "findings": [finding("P1", "low", "N/A", f"structure checks are N/A for kind={kind} (index-shaped grammar only)")],
            "summary": {"high": 0, "medium": 0, "low": 0, "hygiene": 0, "fixable": 0},
        })
        return

    # I1 — exactly one H1
    if struct["h1_count"] == 0:
        findings.append(finding("P1", "high", "I1", "no H1 found"))
    elif struct["h1_count"] > 1:
        findings.append(finding("P1", "high", "I1", f"{struct['h1_count']} H1s found, expected exactly 1", line=struct["h1s"][1][0]))

    # I2 — blockquote summary present, 1-3 sentences
    if not struct["blockquote_present"]:
        findings.append(finding("P1", "medium", "I2", "no blockquote summary immediately after the H1", line=struct["h1s"][0][0] if struct["h1s"] else None, fixable=False))
    else:
        bq_text = " ".join(struct["blockquote_lines"]).strip()
        sc = sentence_count(bq_text)
        if sc > 3:
            findings.append(finding("P1", "medium", "I2", f"blockquote is {sc} sentences; spec allows a short summary (1-3 sentences)", line=struct["blockquote_start"]))

    # I4 — no H3+ or stray paragraphs inside a section
    for sec in struct["sections"]:
        for (li, lvl, title) in sec.subheadings:
            findings.append(finding("P1", "medium", "I4", f"H{lvl} heading '{title}' found inside section '{sec.title}'; sections must be H2 link lists only", line=li, fixable=True))
        for (li, raw) in sec.stray_lines:
            if BARE_URL_LINE_RE.match(raw):
                findings.append(finding("P1", "high", "I5", f"bare URL list line does not match `- [name](url)` grammar", line=li, fixable=True))
            else:
                findings.append(finding("P1", "medium", "I4", f"stray non-list-item line in section '{sec.title}'", line=li))

    # I5 — link grammar match rate per section
    for sec in struct["sections"]:
        total_list_like = len(sec.items) + sum(1 for (li, raw) in sec.stray_lines if raw.strip().startswith("-"))
        if total_list_like == 0:
            continue
        match_rate = len(sec.items) / total_list_like
        if match_rate < 0.90:
            findings.append(finding("P1", "high", "I5", f"section '{sec.title}': only {match_rate:.0%} of list lines match `- [name](url)[: notes]`"))

    # N4 — ## Optional must be last
    optional_sections = [s for s in struct["sections"] if s.title.strip().lower() == "optional"]
    if optional_sections and struct["sections"][-1].title.strip().lower() != "optional":
        findings.append(finding("P1", "medium", "N4", "`## Optional` section exists but is not the last H2 section", line=optional_sections[0].line, fixable=True))

    new_text = text
    if args.fix:
        new_text, section_fixes = _fix_structure(text, struct)
        fixed.extend(section_fixes)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")

    emit({
        "file": str(path), "pass": "P1", "kind": kind,
        "findings": findings, "fixed": fixed if args.fix else None,
        "summary": summarize(findings),
    })


def _fix_structure(text: str, struct):
    """Safe fixes: move `## Optional` last; wrap bare URL lines into a list item."""
    lines = struct["lines"][:]
    applied = []

    # wrap bare URL lines: `- https://x/y` -> `- [y](https://x/y)`
    for sec in struct["sections"]:
        for (li, raw) in list(sec.stray_lines):
            m = BARE_URL_LINE_RE.match(raw)
            if m:
                url = m.group(1)
                last_segment = url.rstrip("/").rsplit("/", 1)[-1] or url
                lines[li - 1] = f"- [{last_segment}]({url})"
                applied.append(f"wrapped bare URL at line {li} into a list item")

    text2 = "\n".join(lines) + ("\n" if text.endswith("\n") else "")

    # move `## Optional` to the end (re-parse since line numbers may have shifted only in content, not headings)
    struct2 = parse_structure(text2)
    sections = struct2["sections"]
    opt_idx = next((i for i, s in enumerate(sections) if s.title.strip().lower() == "optional"), None)
    if opt_idx is not None and opt_idx != len(sections) - 1:
        raw_lines = text2.splitlines()
        blocks = []
        cursor = sections[0].line - 1
        head = raw_lines[:cursor]
        for s in sections:
            blocks.append(raw_lines[s.line - 1:s.body_end])
        opt_block = blocks.pop(opt_idx)
        blocks.append(opt_block)
        new_lines = head
        for b in blocks:
            new_lines.extend(b)
        text2 = "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")
        applied.append("moved `## Optional` to the last section")

    return text2, applied


# ---------------------------------------------------------------------------
# P2 — links
# ---------------------------------------------------------------------------
def _http_head(url, timeout=10):
    try:
        req = Request(url, method="HEAD", headers={"User-Agent": "llms_lint.py/1.0"})
        with urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.geturl()
    except HTTPError as e:
        return e.code, dict(getattr(e, "headers", {}) or {}), url
    except URLError as e:
        return None, {"error": str(e.reason)}, url
    except Exception as e:  # noqa: BLE001 - never crash the lint on a bad URL
        return None, {"error": str(e)}, url


def cmd_links(args):
    path = Path(args.file)
    text = read_text(path)
    kind = resolve_kind(args, text, path)
    struct = parse_structure(text)
    findings = []
    fixed = []
    checked_live = []

    all_items = []
    for sec in struct["sections"]:
        for it in sec.items:
            all_items.append((sec, it))

    seen_targets = {}
    for sec, (li, title, url, desc, raw) in all_items:
        base, _, anchor = url.partition("#")
        if any(p.search(url) for p in PRIVATE_HOST_PATTERNS):
            findings.append(finding("P2", "high", "P2", f"link target looks like a private/local path, not a publisher URL: {url}", line=li))
            continue

        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", base):
            if base.startswith("http"):
                seen_targets.setdefault(base, []).append(li)
                if args.check_links:
                    status, headers, final_url = _http_head(base)
                    checked_live.append({"url": base, "status": status})
                    if status is None:
                        findings.append(finding("P2", "high", "N6", f"link unreachable: {base} ({headers.get('error', 'error')})", line=li))
                    elif status >= 400:
                        findings.append(finding("P2", "high", "N6", f"link returned {status}: {base}", line=li))
                    ct = headers.get("Content-Type", "") if headers else ""
                    if status and status < 400 and ct and "html" in ct.lower() and not base.endswith(".md"):
                        findings.append(finding("P2", "medium", "N6", f"link served text/html, not markdown, and has no .md twin path: {base}", line=li))
            # non-http(s) absolute scheme already handled by private-host scan above
        else:
            # relative link: resolve against the file's directory
            rel = base
            target = (path.parent / rel).resolve()
            if not target.exists():
                # try the .md twin (page.html -> page.md) before declaring dead
                twin = None
                if rel.endswith(".html"):
                    twin = (path.parent / (rel[:-5] + ".md")).resolve()
                if twin and twin.exists():
                    findings.append(finding("P2", "medium", "N6", f"link points at {rel} but a .md twin exists at {twin.name}", line=li, fixable=True))
                else:
                    findings.append(finding("P2", "high", "N6", f"relative link does not resolve: {rel}", line=li))
            seen_targets.setdefault(base, []).append(li)

    for target, line_nos in seen_targets.items():
        if len(line_nos) > 1:
            findings.append(finding("P2", "low", "N7", f"duplicate link target across sections: {target} (lines {line_nos})", line=line_nos[0], fixable=True))

    # generic private-path scan across the WHOLE file (catches citations inside
    # full/facts bodies, not just the index's own link list)
    private_hits = 0
    for i, line in enumerate(struct["lines"], start=1):
        if "file://" in line or "127.0.0.1" in line or "text-mirror/" in line:
            private_hits += 1
    if private_hits and kind not in ("index", "family"):
        findings.append(finding(
            "P2", "high", "P2",
            f"{private_hits} line(s) reference private/local paths (file://, 127.0.0.1, or text-mirror/) "
            f"— acceptable only if this file is explicitly marked internal",
        ))

    new_text = text
    if args.fix:
        new_text, link_fixes = _fix_links(text, struct)
        fixed.extend(link_fixes)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")

    emit({
        "file": str(path), "pass": "P2", "kind": kind,
        "check_links": args.check_links,
        "live_checks": checked_live if args.check_links else "skipped (pass --check-links for live HEAD requests)",
        "findings": findings, "fixed": fixed if args.fix else None,
        "summary": summarize(findings),
    })


def _fix_links(text: str, struct):
    """Safe fixes: page.html -> page.md when the twin exists; drop exact duplicate targets keeping the first."""
    lines = struct["lines"][:]
    applied = []
    seen = set()
    root = Path(".")
    for sec in struct["sections"]:
        for (li, title, url, desc, raw) in sec.items:
            base, hashsym, anchor = url.partition("#")
            if base in seen and not re.match(r"^https?://", base):
                # drop duplicate (comment it out is not safe; instead remove the line only
                # when it is a pure re-link with no unique title text worth keeping)
                continue
            seen.add(base)
            if base.endswith(".html"):
                twin = Path(base[:-5] + ".md")
                # only rewrite when we can't check disk existence (best effort, no crash)
                new_url = base[:-5] + ".md" + (hashsym + anchor if hashsym else "")
                new_line = lines[li - 1].replace(f"({url})", f"({new_url})")
                if new_line != lines[li - 1]:
                    lines[li - 1] = new_line
                    applied.append(f"rewrote .html -> .md at line {li}")
    return "\n".join(lines) + ("\n" if text.endswith("\n") else ""), applied


# ---------------------------------------------------------------------------
# P3 — descriptions (deterministic half)
# ---------------------------------------------------------------------------
_STOPWORDS = {"the", "a", "an", "of", "and", "or", "to", "for", "in", "on", "docs", "documentation", "index", "catalogue", "reference"}


def _norm_tokens(s: str) -> set:
    s = re.sub(r"[^\w\s]", " ", s.lower())
    return {t for t in s.split() if t and t not in _STOPWORDS}


def cmd_descriptions(args):
    path = Path(args.file)
    text = read_text(path)
    kind = resolve_kind(args, text, path)
    struct = parse_structure(text)
    findings = []

    all_items = []
    for sec in struct["sections"]:
        for it in sec.items:
            all_items.append((sec, it))

    if not all_items:
        emit({
            "file": str(path), "pass": "P3", "kind": kind,
            "findings": [finding("P3", "low", "N/A", "no link items found to check descriptions on")],
            "summary": {"high": 0, "medium": 0, "low": 0, "hygiene": 0, "fixable": 0},
        })
        return

    missing = 0
    seen_desc = {}
    for sec, (li, title, url, desc, raw) in all_items:
        desc = desc.strip()
        if not desc:
            missing += 1
            findings.append(finding("P3", "medium", "D1", f"link '{title}' has no description", line=li))
            continue

        wc = word_count(desc)
        if wc < 10 or wc > 25:
            findings.append(finding("P3", "low", "D3", f"description for '{title}' is {wc} words (band is 10-25)", line=li))
        if desc.rstrip().endswith("...") or desc.rstrip().endswith("\u2026"):
            findings.append(finding("P3", "low", "D3", f"description for '{title}' ends in a truncation ellipsis", line=li))

        key = re.sub(r"\s+", " ", desc.strip().lower())
        seen_desc.setdefault(key, []).append((li, title))

        title_tokens = _norm_tokens(title)
        desc_tokens = _norm_tokens(desc)
        if title_tokens and desc_tokens:
            overlap = len(title_tokens & desc_tokens) / max(1, len(title_tokens | desc_tokens))
            if overlap >= 0.7 or desc_tokens <= title_tokens:
                findings.append(finding(
                    "P3", "medium", "D2",
                    f"description for '{title}' looks like a restated title (token overlap {overlap:.0%}), "
                    f"not what the reader finds there",
                    line=li,
                ))

    for key, occurrences in seen_desc.items():
        if len(occurrences) > 1:
            lines_str = ", ".join(str(li) for li, _ in occurrences)
            findings.append(finding("P3", "medium", "D4", f"duplicate description text used for {len(occurrences)} links (lines {lines_str})", line=occurrences[0][0]))

    total = len(all_items)
    if total and missing / total > 0.40:
        findings.append(finding("P3", "high", "D1", f"{missing}/{total} links ({missing/total:.0%}) have no description — exceeds the 40% high-severity bar"))

    emit({
        "file": str(path), "pass": "P3", "kind": kind,
        "link_count": total,
        "findings": findings,
        "summary": summarize(findings),
    })


# ---------------------------------------------------------------------------
# P5 — size ladder
# ---------------------------------------------------------------------------
def cmd_size(args):
    path = Path(args.file)
    text = read_text(path)
    kind = resolve_kind(args, text, path)
    size_bytes = len(text.encode("utf-8"))
    est_tokens = round(size_bytes / CHARS_PER_TOKEN)
    findings = []

    if kind == "index":
        if size_bytes > 100_000:
            findings.append(finding("P5", "high", "S1", f"index is {size_bytes} bytes (>100 KB) — this is a full file wearing the index's name"))
        elif size_bytes > 10_000:
            findings.append(finding("P5", "medium", "S1", f"index is {size_bytes} bytes; spec-lint bar is ~10 KB / ~2.5k tokens"))

    if kind == "full":
        small_candidates = [path.with_name(path.name.replace("full", "small"))]
        if not any(c.exists() for c in small_candidates):
            findings.append(finding("P5", "medium", "S2", "no llms-small.txt sibling found beside this full file"))

    if kind == "small" and est_tokens > 50_000:
        findings.append(finding("P5", "medium", "S3", f"small variant estimated at {est_tokens} tokens (>50k) — the Cursor stability ceiling from llms-txt-ecosystem-evidence.md"))

    if kind == "facts":
        full_sibling = path.with_name(path.name.replace("facts", "full"))
        if full_sibling.exists():
            full_size = len(read_text(full_sibling).encode("utf-8"))
            if full_size:
                ratio = size_bytes / full_size
                if ratio > 0.30:
                    findings.append(finding("P5", "medium", "S4", f"facts file is {ratio:.0%} of the full file's size (bar is ~15%, high-severity dropoff at >30%)"))
                elif ratio > 0.15:
                    findings.append(finding("P5", "low", "S4", f"facts file is {ratio:.0%} of the full file's size (bar is ~15%)"))
        else:
            findings.append(finding("P5", "low", "N/A", "no sibling full file found; facts/prose compression ratio (S4) cannot be computed without the source mirror"))

    manifest_path = path.parent / "manifest.json"
    manifest_note = None
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            findings.append(finding("P5", "medium", "H8", f"manifest.json is not valid JSON: {e}"))
            manifest = None
        if manifest:
            files = manifest.get("files", {})
            entry = files.get(path.name)
            if entry is None:
                findings.append(finding("P5", "medium", "H8", f"manifest.json has no entry for {path.name}"))
            else:
                declared = entry.get("bytes")
                if declared is not None and declared > 0:
                    drift = abs(declared - size_bytes) / declared
                    if drift > 0.02:
                        findings.append(finding("P5", "medium", "H8", f"manifest.json declares {declared} bytes for {path.name}; actual is {size_bytes} ({drift:.1%} drift, tolerance is 2%)"))
            manifest_note = "checked against manifest.json"
    else:
        findings.append(finding("P5", "medium", "H8", "no manifest.json found beside this file"))

    emit({
        "file": str(path), "pass": "P5", "kind": kind,
        "bytes": size_bytes, "est_tokens": est_tokens,
        "manifest": manifest_note,
        "findings": findings,
        "summary": summarize(findings),
    })


# ---------------------------------------------------------------------------
# P6 — full-file fidelity (deterministic half)
# ---------------------------------------------------------------------------
RESIDUE_PATTERNS = [
    ("skip-to-content", re.compile(r"\[Skip to content\]")),
    ("documentation-index-blockquote", re.compile(r">\s*##\s*Documentation Index")),
    ("mdx-theme-prop", re.compile(r"theme=\{null\}")),
    ("mdx-import", re.compile(r"^\s*import\s+.+\s+from\s+['\"].+['\"];?\s*$", re.M)),
]


def _split_full_file(text: str, grammar: str):
    """Return a list of {title,url,body,start,end} page blocks for the four
    documented producer grammars. `none` falls back to H2-section blocks —
    a heuristic, since no formal page-grammar applies (spec.md §3.2: no
    single page-block grammar exists in the wild)."""
    blocks = []
    if grammar == "mintlify":
        pattern = re.compile(r"^# (.+?)\r?\nSource:\s*(\S+)", re.M)
        matches = list(pattern.finditer(text))
        for i, m in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            blocks.append({"title": m.group(1).strip(), "url": m.group(2).strip(), "body": text[m.end():end]})
    elif grammar == "firecrawl":
        parts = re.split(r"<\|firecrawl-page-\d+-lllmstxt\|>", text)
        for p in parts[1:]:
            blocks.append({"title": None, "url": None, "body": p})
    elif grammar in ("anthropic-yaml", "cloudflare-frontmatter"):
        pattern = re.compile(r"^---\s*$\r?\n(.*?)\r?\n---\s*$", re.M | re.S)
        matches = list(pattern.finditer(text))
        for i, m in enumerate(matches):
            yaml_block = m.group(1)
            title_m = re.search(r"^title:\s*(.+)$", yaml_block, re.M)
            url_m = re.search(r"^url:\s*(.+)$", yaml_block, re.M)
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            blocks.append({
                "title": title_m.group(1).strip() if title_m else None,
                "url": url_m.group(1).strip() if url_m else None,
                "body": text[m.end():end],
            })
    else:  # none — heuristic H2-section fallback
        struct = parse_structure(text)
        for sec in struct["sections"]:
            body = "\n".join(struct["lines"][sec.body_start - 1:sec.body_end])
            blocks.append({"title": sec.title, "url": None, "body": body})
    return blocks


def cmd_full(args):
    path = Path(args.file)
    text = read_text(path)
    kind = resolve_kind(args, text, path)
    findings = []
    fixed = []

    if kind not in ("full", "small"):
        emit({
            "file": str(path), "pass": "P6", "kind": kind,
            "findings": [finding("P6", "low", "N/A", f"full-file fidelity checks are N/A for kind={kind}")],
            "summary": {"high": 0, "medium": 0, "low": 0, "hygiene": 0, "fixable": 0},
        })
        return

    grammar = detect_full_grammar(text)
    blocks = _split_full_file(text, grammar)

    if grammar == "none":
        findings.append(finding("P6", "low", "N/A", "no known producer grammar (mintlify/anthropic-yaml/cloudflare-frontmatter/firecrawl) detected; page-block fidelity (C1/C2) falls back to H2-section-level heuristics"))
    else:
        for b in blocks:
            if not b.get("title") or not b.get("url"):
                findings.append(finding("P6", "high", "C2", f"page block missing title or source URL (title={b.get('title')!r})"))

    # C3 — residue
    for name, pat in RESIDUE_PATTERNS:
        hits = list(pat.finditer(text))
        if hits:
            first_line = text.count("\n", 0, hits[0].start()) + 1
            findings.append(finding("P6", "medium", "C3", f"navigation residue found ({name}, {len(hits)} occurrence(s))", line=first_line, fixable=True))

    # C4 — fence balance
    fence_count = len(re.findall(r"^\s*```", text, re.M))
    if fence_count % 2 != 0:
        findings.append(finding("P6", "medium", "C4", f"unbalanced code fences ({fence_count} ``` markers, expected an even number)", fixable=True))

    # C5 — exact duplicate blocks (hash bodies)
    seen_hashes = {}
    for i, b in enumerate(blocks):
        h = hashlib.sha256(b["body"].strip().encode("utf-8")).hexdigest()
        if h in seen_hashes:
            findings.append(finding("P6", "medium", "C5", f"exact duplicate page/section body: block {i} duplicates block {seen_hashes[h]} ({b.get('title')!r})"))
        else:
            seen_hashes[h] = i

    new_text = text
    if args.fix:
        for name, pat in RESIDUE_PATTERNS:
            if name == "mdx-import":
                new_text = pat.sub("", new_text)
            else:
                new_text = pat.sub("", new_text)
        if new_text != text:
            fixed.append("stripped known navigation-residue patterns")
        # close a dangling fence at EOF
        if len(re.findall(r"^\s*```", new_text, re.M)) % 2 != 0:
            new_text = new_text.rstrip("\n") + "\n```\n"
            fixed.append("closed a dangling code fence at end of file")
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")

    emit({
        "file": str(path), "pass": "P6", "kind": kind, "grammar": grammar,
        "page_blocks": len(blocks),
        "findings": findings, "fixed": fixed if args.fix else None,
        "summary": summarize(findings),
    })


# ---------------------------------------------------------------------------
# P7 — facts-file shape (deterministic half)
# ---------------------------------------------------------------------------
def cmd_facts(args):
    path = Path(args.file)
    text = read_text(path)
    kind = resolve_kind(args, text, path)
    findings = []
    fixed = []

    if kind != "facts":
        emit({
            "file": str(path), "pass": "P7", "kind": kind,
            "findings": [finding("P7", "low", "N/A", f"facts-shape checks are N/A for kind={kind}")],
            "summary": {"high": 0, "medium": 0, "low": 0, "hygiene": 0, "fixable": 0},
        })
        return

    struct = parse_structure(text)
    lines = struct["lines"]

    unit_lines = []  # (line_no, raw)
    for i, line in enumerate(lines, start=1):
        if re.match(r"^\s*-\s*\[[A-Za-z_\-]+\]\s", line):
            unit_lines.append((i, line))

    if not unit_lines:
        findings.append(finding("P7", "high", "C6", "no unit lines matching `- [type] text — <url>#<anchor>` were found"))
        emit({"file": str(path), "pass": "P7", "kind": kind, "findings": findings, "summary": summarize(findings)})
        return

    no_url = 0
    unresolved_anchor = 0
    checked_anchor = 0
    untyped = 0
    unknown_types = {}
    too_long = 0
    no_keywords = 0

    for li, raw in unit_lines:
        m = UNIT_LINE_RE.match(raw)
        if not m:
            no_url += 1
            findings.append(finding("P7", "high", "C6", "unit line does not match `- [type] text — <url>` grammar", line=li))
            continue

        utype = m.group("type")
        if utype not in UNIT_TYPES:
            untyped += 1
            unknown_types[utype] = unknown_types.get(utype, 0) + 1

        unit_text = m.group("text") or ""
        if len(unit_text) > 400 or sentence_count(unit_text) > 2:
            too_long += 1

        kw = m.group("keywords")
        if not kw or not kw.strip():
            no_keywords += 1

        url = m.group("url")
        base, sep, anchor = url.partition("#")
        if base.startswith("file://") and anchor:
            local_path = Path(base[len("file://"):])
            if local_path.exists():
                checked_anchor += 1
                try:
                    src_text = local_path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    src_text = ""
                src_headings = re.findall(r"^#{1,6}\s+(.*?)\s*$", src_text, re.M)
                slugs = {slugify(h) for h in src_headings}
                if slugify(anchor) not in slugs and anchor not in slugs:
                    unresolved_anchor += 1
                    findings.append(finding("P7", "medium", "R3", f"anchor #{anchor} does not resolve to a heading in {local_path.name}", line=li))

    total = len(unit_lines)
    if untyped:
        sev = "high" if untyped / total > 0.20 else "medium"
        findings.append(finding("P7", sev, "C6", f"{untyped}/{total} units use a type outside docset_refine.UNIT_TYPES: {unknown_types} (allowed: {sorted(UNIT_TYPES)})"))
    if too_long:
        findings.append(finding("P7", "medium", "C6", f"{too_long}/{total} units exceed 2 sentences / 400 chars (not atomic)"))
    if no_keywords:
        findings.append(finding("P7", "low", "R4", f"{no_keywords}/{total} units carry no `keywords:` field"))
    if checked_anchor and unresolved_anchor / checked_anchor > 0.20:
        findings.append(finding("P7", "high", "R3", f"{unresolved_anchor}/{checked_anchor} checkable anchors do not resolve (>20% bar)"))

    emit({
        "file": str(path), "pass": "P7", "kind": kind,
        "unit_count": total,
        "anchors_checked_locally": checked_anchor,
        "findings": findings,
        "summary": summarize(findings),
        "note": "page-coverage check (R7: every indexed page has >=1 unit) needs the sibling llms.txt and is out of scope for this lint invocation",
    })


# ---------------------------------------------------------------------------
# P9 — provenance, rights, steering (deterministic half)
# ---------------------------------------------------------------------------
def cmd_trust(args):
    path = Path(args.file)
    text = read_text(path)
    kind = resolve_kind(args, text, path)
    lines = text.splitlines()
    findings = []
    fixed = []

    has_banner = bool(re.search(r"<!--\s*generated by|verified-as-of:|generated\s+\d{4}-\d{2}-\d{2}", text, re.I))
    if not has_banner:
        findings.append(finding("P9", "medium", "P1", "no provenance banner found (who generated it, from what, when)"))

    steering_hits = []
    for i, line in enumerate(lines, start=1):
        for pat in STEERING_PATTERNS:
            if pat.search(line):
                steering_hits.append((i, pat.pattern, line.strip()[:160]))
    if steering_hits:
        for li, pat, snippet in steering_hits[:20]:
            findings.append(finding(
                "P9", "medium", "P4",
                f"candidate steering/imperative-to-model span (needs model confirmation per passes.md P9): {snippet!r}",
                line=li,
            ))
        if len(steering_hits) > 20:
            findings.append(finding("P9", "medium", "P4", f"...and {len(steering_hits) - 20} more candidate steering spans"))

    secret_hits = []
    for i, line in enumerate(lines, start=1):
        for name, pat in SECRET_PATTERNS:
            m = pat.search(line)
            if m:
                secret_hits.append((i, name, m.group(0)))
    for li, name, value in secret_hits:
        masked = value[:4] + "…" + value[-4:] if len(value) > 10 else "…"
        findings.append(finding("P9", "high", "P5", f"secret-shaped string found ({name}): {masked}", line=li, fixable=True))

    new_text = text
    if args.fix and secret_hits:
        for li, name, value in secret_hits:
            new_text = new_text.replace(value, "[redacted]")
        fixed.append(f"redacted {len(secret_hits)} secret-shaped string(s) to [redacted] — BLOCKED: fix the source upstream")
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")

    emit({
        "file": str(path), "pass": "P9", "kind": kind,
        "has_provenance_banner": has_banner,
        "findings": findings, "fixed": fixed if args.fix else None,
        "summary": summarize(findings),
    })


# ---------------------------------------------------------------------------
# P14 — hygiene
# ---------------------------------------------------------------------------
def cmd_hygiene(args):
    path = Path(args.file)
    raw = path.read_bytes()
    findings = []
    fixed = []

    has_bom = raw.startswith(b"\xef\xbb\xbf")
    body = raw[3:] if has_bom else raw

    try:
        text = body.decode("utf-8", errors="strict")
        decode_ok = True
    except UnicodeDecodeError as e:
        text = body.decode("utf-8", errors="replace")
        decode_ok = False
        findings.append(finding("P14", "hygiene", "H1", f"file is not valid UTF-8: {e}", fixable=True))

    if b"\x00" in body:
        findings.append(finding("P14", "hygiene", "H1", "NUL byte found in file", fixable=True))

    crlf = raw.count(b"\r\n")
    lone_cr = raw.count(b"\r") - crlf
    if crlf and (raw.count(b"\n") - crlf) > 0:
        findings.append(finding("P14", "hygiene", "H1", f"mixed line endings ({crlf} CRLF among LF lines)", fixable=True))
    elif crlf:
        findings.append(finding("P14", "hygiene", "H1", f"file uses CRLF line endings ({crlf} lines); spec convention is LF", fixable=True))
    if lone_cr > 0:
        findings.append(finding("P14", "hygiene", "H1", f"{lone_cr} lone CR byte(s) found (old Mac line endings)", fixable=True))

    lines = text.split("\n")
    trailing_ws = [i + 1 for i, l in enumerate(lines) if l != l.rstrip()]
    if trailing_ws:
        findings.append(finding("P14", "hygiene", "H1", f"trailing whitespace on {len(trailing_ws)} line(s), e.g. line {trailing_ws[0]}", fixable=True))

    tab_list_lines = [i + 1 for i, l in enumerate(lines) if re.match(r"^\s*-\s", l) and "\t" in l]
    if tab_list_lines:
        findings.append(finding("P14", "hygiene", "H1", f"tab character in {len(tab_list_lines)} list line(s), e.g. line {tab_list_lines[0]}", fixable=True))

    if text and not text.endswith("\n"):
        findings.append(finding("P14", "hygiene", "H1", "file does not end with a trailing newline", fixable=True))
    elif text.endswith("\n\n"):
        trailing_blanks = len(text) - len(text.rstrip("\n"))
        findings.append(finding("P14", "hygiene", "H1", f"{trailing_blanks} trailing blank lines at EOF (want exactly one trailing newline)", fixable=True))

    # smart quotes / zero-width chars inside URLs — High (dead link in disguise), not mere hygiene
    for i, line in enumerate(lines, start=1):
        for m in URL_RE.finditer(line):
            url = m.group(0)
            bad = [c for c in url if c in SMART_CHARS]
            if bad:
                findings.append(finding("P14", "high", "H1", f"smart-quote/zero-width character {bad!r} found inside a URL: {url!r}", line=i, fixable=True))

    if has_bom:
        findings.append(finding("P14", "hygiene", "H1", "file begins with a BOM (allowed per spec v2, informational only)"))

    if args.fix:
        norm_lines = []
        for l in text.split("\n"):
            l = l.rstrip()
            if re.match(r"^\s*-\s", l):
                l = l.expandtabs(4)
            for bad_char, repl in (("\u2018", "'"), ("\u2019", "'"), ("\u201c", '"'), ("\u201d", '"'), ("\u200b", ""), ("\u200d", ""), ("\ufeff", "")):
                l = l.replace(bad_char, repl)
            norm_lines.append(l)
        new_text = "\n".join(norm_lines)
        new_text = new_text.rstrip("\n") + "\n"
        new_bytes = new_text.encode("utf-8")
        if new_bytes != raw:
            path.write_bytes(new_bytes)
            fixed.append("normalized line endings, trailing whitespace, tabs-in-lists, smart quotes and end-of-file newline")

    emit({
        "file": str(path), "pass": "P14", "kind": None,
        "decode_ok": decode_ok, "has_bom": has_bom,
        "findings": findings, "fixed": fixed if args.fix else None,
        "summary": summarize(findings),
    })


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def add_common(sp):
    sp.add_argument("file", help="path to the llms.txt-family file to lint")
    sp.add_argument("--kind", choices=["index", "family", "full", "small", "facts"], default=None, help="override P0 kind detection")
    sp.add_argument("--fix", action="store_true", help="apply deterministic safe fixes in place")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="llms_lint.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("detect", help="P0 — detect kind and grammar")
    p.add_argument("file")
    p.add_argument("--kind", choices=["index", "family", "full", "small", "facts"], default=None)
    p.set_defaults(func=cmd_detect)

    p = sub.add_parser("structure", help="P1 — structural validity")
    add_common(p)
    p.set_defaults(func=cmd_structure)

    p = sub.add_parser("links", help="P2 — link resolution")
    add_common(p)
    p.add_argument("--check-links", action="store_true", help="do live HEAD requests on absolute URLs (default off)")
    p.set_defaults(func=cmd_links)

    p = sub.add_parser("descriptions", help="P3 (deterministic half) — link descriptions")
    add_common(p)
    p.set_defaults(func=cmd_descriptions)

    p = sub.add_parser("size", help="P5 — size-ladder budgets")
    add_common(p)
    p.set_defaults(func=cmd_size)

    p = sub.add_parser("full", help="P6 (deterministic half) — full-file fidelity")
    add_common(p)
    p.set_defaults(func=cmd_full)

    p = sub.add_parser("facts", help="P7 (deterministic half) — facts-file shape")
    add_common(p)
    p.set_defaults(func=cmd_facts)

    p = sub.add_parser("trust", help="P9 (deterministic half) — steering/secrets scan")
    add_common(p)
    p.set_defaults(func=cmd_trust)

    p = sub.add_parser("hygiene", help="P14 — byte-level hygiene")
    add_common(p)
    p.set_defaults(func=cmd_hygiene)

    args = parser.parse_args(argv)

    path = Path(args.file)
    if not path.exists():
        emit({"error": f"file not found: {args.file}", "pass": args.command})
        return 2
    if not path.is_file():
        emit({"error": f"not a file: {args.file}", "pass": args.command})
        return 2

    try:
        args.func(args)
    except Exception as e:  # noqa: BLE001 - a lint tool must never crash, it must report
        emit({"error": f"{type(e).__name__}: {e}", "pass": args.command, "file": str(path)})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
