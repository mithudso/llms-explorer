#!/usr/bin/env python3
"""llms_lint — the deterministic passes of the llms-deep-optimizer (`/ldo`).

Judges an llms.txt / family index / llms-full.txt / llms-small.txt / llms-facts.txt /
llms-vocabulary.txt against the attribute rubric in
~/.claude/skills/llms-deep-optimizer/references/attributes.md (llms-vocabulary.txt
reuses the C6/D4/R3 codes by analogy — the rubric has no vocabulary-scoped rows
yet) and emits findings `{pass, attr, severity, line, msg, fixable}`. Severities
follow the family ladder (high / medium / low / hygiene), plus `na` for a check
that could not run (e.g. anchor resolution with no `--mirror`). `--fix` applies
only the fixes `apply_fixes()` actually performs (byte hygiene, `## Optional`
last, bare-URL wrap, residue strip in full files, and a mintlify grammar banner
when one is missing) — a `fixable=True` finding is marked `fixed` only when
`apply_fixes()` reports it touched that attribute, never unconditionally. Model,
live and family passes (P4, P8, P10, P11-13) live in the skill; P15 (regeneration
parity) is not implemented anywhere yet.

Usage:
    llms_lint.py detect FILE
    llms_lint.py check  FILE|DIR... [--kind K] [--check-links] [--fix] [--json]
                                    [--mirror M] [--third-party]
    llms_lint.py hygiene FILE [--fix]

A DIR argument checks every `llms*.txt` in it, plus `*/llms*.txt` at any depth
(split indexes and their facts/full/small/vocabulary siblings).

Outbound link checks (`--check-links`) only ever fetch public hosts: private,
loopback, link-local and reserved addresses are refused before the request and
after every redirect hop, and reported as an `na` finding rather than silently
skipped.

Exit status: 1 when any High finding remains unfixed, else 0 — usable as a CI gate.
"""

from __future__ import annotations

import argparse
import functools
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from ipaddress import ip_address
from pathlib import Path
from socket import getaddrinfo
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llms_acquire import split_llms_full  # noqa: E402

try:  # unit-type vocabulary is owned by the generator
    from docset_refine import UNIT_TYPES  # noqa: E402
except Exception:  # pragma: no cover - refine package absent on a thin box
    UNIT_TYPES = (
        "concept",
        "fact",
        "actionable",
        "question",
        "problem",
        "statement",
        "quote",
        "idea",
        "snippet",
        "parameter",
        "definition",
        "change",
    )

KINDS = ("index", "family", "full", "small", "facts", "vocabulary", "unknown")
SELECTABLE_KINDS = tuple(k for k in KINDS if k != "unknown")  # --kind never accepts the fallback
INDEX_MAX_BYTES = 10_000
INDEX_HARD_BYTES = 100_000
SMALL_MAX_CHARS = 200_000
BLOCK_MAX_BYTES = 200_000
FACTS_RATIO_LOW, FACTS_RATIO_MED = 0.15, 0.30
DESC_WORDS = (10, 25)
DETECT_HEAD_BYTES = 200_000
DETECT_UNIT_SCAN_LINES = 400
HEAD_WINDOW = 4000  # window a provenance/internal-marker banner must sit within
BLOCKQUOTE_MAX_SENTENCES = 3
BARE_URL_HIGH_SHARE = 0.9
DESC_MISSING_HIGH_SHARE, DESC_MISSING_HIGH_MIN = 0.4, 3
DESC_BAND_TOLERANCE = 0.05
MANIFEST_DRIFT_TOLERANCE = 0.02
UNTAGGED_FENCE_TOLERANCE = 0.10
LONG_UNIT_TOLERANCE = 0.10
UNIT_MAX_CHARS, UNIT_MAX_SENTENCES = 400, 2
ANCHOR_UNRESOLVED_HIGH_SHARE = 0.2
FACTS_COVERAGE_GAP_TOLERANCE = 0.05
HEADING_LOOKBACK_LINES = 80
FAMILY_INDEX_TARGET_SHARE = 0.6
MAX_INPUT_BYTES = 100_000_000  # ~10x measured peak-memory amplification beyond this OOMs a CI box


def _env_num(name: str, default: float, cast, lo: float, hi: float):
    """Parse an env-var knob defensively: bad/out-of-range values fall back to
    `default` with a stderr note, never crash import or silently disable rate
    limiting (e.g. a negative timeout or a zero worker count)."""
    v = os.environ.get(name)
    if v is None or not v.strip():
        return default
    try:
        n = cast(v)
    except ValueError:
        print(f"llms_lint: {name}={v!r} is not a number; using {default}", file=sys.stderr)
        return default
    if not (lo <= n <= hi):
        print(f"llms_lint: {name}={n} outside [{lo},{hi}]; clamping", file=sys.stderr)
    return min(max(n, lo), hi)


LINK_TIMEOUT = _env_num("HUB_LLMS_LINK_TIMEOUT", 10.0, float, 0.5, 120.0)
LINK_CONCURRENCY = int(_env_num("HUB_LLMS_LINK_CONCURRENCY", 8, int, 1, 64))
LINK_BUDGET = _env_num("HUB_LLMS_LINK_BUDGET", 120.0, float, 5.0, 3600.0)  # whole-sweep seconds
LINK_UA = "llms-lint/1.0"

LINK_RE = re.compile(r"^\s*[-*]\s+\[([^\]]*)\]\(([^)\s]+)\)\s*(?::\s*(.*))?$")
BARE_URL_RE = re.compile(r"^\s*[-*]?\s*(https?://\S+)\s*$")
H_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
UNIT_RE = re.compile(
    r"^- \[([\w-]*)\]\s+(.*)\s+—\s+(\S+)(?:\s+·\s+(?:keywords|verified-as-of):.*)?$"
)
COUNTS_RE = re.compile(r"\b\d[\d,]*\s*(pages?|tokens?|units?)\b", re.I)
# A vocabulary term line as docset_refine.vocabulary.render() writes it:
#   - **term** — definition · aka: a, b · not: x · differs: … — url#anchor · evidence: …
# The definition follows an em dash and the source comes AFTER the aka/not/differs
# fields, so the line is parsed in two steps: VOCAB_RE takes the bold term (and
# tolerates the `**term** (n): definition — url · aka: …` shorthand), then
# VOCAB_SRC_RE finds the ` — <url>` source wherever it sits; the definition is
# what is left before the first ` · ` field.
VOCAB_RE = re.compile(r"^- \*\*(?P<term>.+?)\*\*(?:\s*\([^)]*\))?\s*(?:[:—]\s*)?(?P<rest>.*)$")
VOCAB_SRC_RE = re.compile(r"\s+—\s+(?P<src>(?:https?://|\.{0,2}/)\S+)(?=\s+·\s+|$)")
VOCAB_DEF_MAX = 400
# the tail vocabulary.render() writes for terms it could not define
NAMED_TAIL_RE = re.compile(r"^#{1,6}\s+Named, not yet defined\s*$", re.I)
PRIVATE_RE = re.compile(
    r"^(file://|https?://(127\.0\.0\.1|localhost)\b|/Users/|.*text-mirror/)", re.I
)
# Bounded (no unanchored `.*` under DOTALL) so a long banner-less comment can't
# trigger catastrophic backtracking — confirmed cubic on the unbounded form.
INTERNAL_MARK_RE = re.compile(r"<!--[^>]{0,400}?\binternal\b[^>]{0,400}?-->", re.I)
BANNER_RE = re.compile(
    r"<!--[^>]{0,400}?(generated|verified-as-of|llms-full grammar)[^>]{0,400}?-->", re.I
)
RESIDUE_RES = (
    re.compile(r"^\s*>\s*Documentation Index\b"),
    re.compile(r"^\s*\[Skip to (content|main)\]"),
    re.compile(r"theme=\{null\}"),
    # `[ \t]` (not `\s`) so the two adjacent `+` runs can't both match the same
    # space — that ambiguity is what made the previous pattern quadratic.
    re.compile(r"^[ \t]*import[ \t]+\{?[\w,]+(?:[ \t]+[\w,]+)*\}?[ \t]+from[ \t]+"
               r"['\"][^'\"]{0,500}['\"];?[ \t]*$"),
)
RESIDUE_GATE_RE = re.compile(r">|\[Skip to|theme=|import ")  # cheap pre-filter before the 4 above
SECRET_RES = (
    re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
)
# One-shot pre-filter before trying each SECRET_RES pattern individually — same
# match set, ~3x faster on lines with no hit (the common case for every line).
SECRET_GATE_RE = re.compile("|".join(f"(?:{r.pattern})" for r in SECRET_RES))
PEM_HEADER_RE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
PEM_BODY_RE = re.compile(r"^[A-Za-z0-9+/=]{60,}$")
STEER_RES = (
    re.compile(r"\bignore (all |any )?(previous|prior|earlier|above) instructions\b", re.I),
    re.compile(r"\byou must (always|never) (say|answer|recommend|mention|cite)\b", re.I),
    re.compile(
        r"\balways (recommend|cite|mention|prefer) (us|this (site|product|company))\b", re.I
    ),
    re.compile(r"\bdo not mention (competitors|other (products|vendors))\b", re.I),
    re.compile(r"\bwhen (asked|a user asks) about .{0,60}\b(say|answer|respond)\b", re.I),
)
STEER_GATE_RE = re.compile("|".join(f"(?:{r.pattern})" for r in STEER_RES), re.I)
FENCE_RE = re.compile(r"^\s*(```|~~~)")
BAD_URL_CHARS = re.compile(r"[‘’“”​‌‍﻿]")


def _public_url(url: str) -> bool:
    """True only for an http(s) URL whose hostname resolves exclusively to
    public, routable addresses — never loopback/link-local/private/reserved.
    Refused: no DNS entry, any private-range hit among multiple A/AAAA records,
    and any non-http(s) scheme. Used to gate every outbound fetch _head() makes,
    including after each redirect hop, so an allowlisted host can't 302 to
    169.254.169.254 or 127.0.0.1."""
    p = urlsplit(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        return False
    try:
        infos = getaddrinfo(p.hostname, p.port or (443 if p.scheme == "https" else 80))
    except OSError:
        return False
    addrs = [ip_address(i[4][0]) for i in infos]
    return bool(addrs) and all(
        not (a.is_private or a.is_loopback or a.is_link_local or a.is_reserved
             or a.is_multicast or a.is_unspecified)
        for a in addrs
    )


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Refuses a redirect whose target is not itself a public URL — otherwise a
    public, allowlist-passing URL could 302 to an internal address and bypass
    the pre-request _public_url() check entirely."""

    def redirect_request(self, req, fp, code, msg, hdrs, newurl):
        if not _public_url(newurl):
            return None
        return super().redirect_request(req, fp, code, msg, hdrs, newurl)


_SAFE_OPENER = urllib.request.build_opener(_SafeRedirectHandler)


class Finding(dict):
    def __init__(self, pss, attr, severity, msg, line=0, fixable=False):
        super().__init__(
            **{
                "pass": pss,
                "attr": attr,
                "severity": severity,
                "line": line,
                "msg": msg,
                "fixable": fixable,
            }
        )


# ---------------------------------------------------------------------------
# P0 detect
# ---------------------------------------------------------------------------


def detect_grammar(text: str) -> str:
    head = text[:DETECT_HEAD_BYTES]
    if "<|firecrawl-page-" in head:
        return "firecrawl"
    if re.search(r"^Source:\s*https?://", head, re.M):
        return "mintlify"
    if re.search(r"^---\s*\n(?:.*\n)*?title:", head, re.M):
        if "[View as Markdown]" in head or re.search(r"^source_url:", head, re.M):
            return "cloudflare-frontmatter"
        return "anthropic-yaml"
    return "none"


def detect_kind(text: str, name: str = "", blocks: list[dict] | None = None) -> tuple[str, str]:
    """(kind, grammar). Name first, then shape; a misnamed file is reported by P0.

    `blocks`, when the caller already has `split_llms_full(text)` on hand (as
    `check()` does), skips a second full-text parse of a large llms-full.txt —
    the string-name checks are tried first so a correctly-named file never
    needs the parse at all."""
    n = name.lower()
    grammar = detect_grammar(text)
    lines = text.splitlines()
    units = sum(1 for ln in lines[:DETECT_UNIT_SCAN_LINES] if UNIT_RE.match(ln))
    links = [m for m in (LINK_RE.match(ln) for ln in lines) if m]
    h1 = next((ln for ln in lines if ln.startswith("# ")), "")
    if n.startswith("llms-vocabulary") or h1.rstrip().lower().endswith("— vocabulary"):
        return "vocabulary", grammar
    if n.startswith("llms-facts") or (units >= 3 and h1.rstrip().endswith("facts")):
        return "facts", grammar
    if grammar != "none" and (
        n.startswith("llms-full")
        or n.startswith("llms-small")
        or len(blocks if blocks is not None else split_llms_full(text)) >= 2
    ):
        return ("small" if n.startswith("llms-small") else "full"), grammar
    if links:
        # a family links OTHER sites' indexes (absolute URLs); a split hub links
        # its own sections by relative path and is still an index
        idx_targets = sum(
            1 for m in links if m.group(2).rstrip("/").endswith("llms.txt") and "://" in m.group(2)
        )
        if idx_targets and idx_targets >= FAMILY_INDEX_TARGET_SHARE * len(links):
            return "family", grammar
        return "index", grammar
    if h1 and n.startswith("llms"):
        return "index", grammar
    return "unknown", grammar


# ---------------------------------------------------------------------------
# index parsing (P1-P3)
# ---------------------------------------------------------------------------


def parse_index(text: str) -> dict:
    """Parse an index/family file's H1, blockquote, H2 sections, and link
    entries. Keys: `h1`/`blockquote` -> (line, text); `h3plus`/`stray` ->
    (line, raw_line); `bare` -> (line, url); `sections` -> {name, line,
    entries}; `entries` -> {line, name, url, notes, section}. `fence_open`
    (int or None) is the line a code fence opened on and never closed — when
    set, every line after it was silently skipped as "inside a fence" and
    none of the other lists include it; the caller must report this, since an
    unclosed fence otherwise drops the rest of the file with zero diagnostic."""
    lines = text.splitlines()
    out = {
        "h1": [],
        "blockquote": [],
        "sections": [],
        "h3plus": [],
        "stray": [],
        "entries": [],
        "bare": [],
        "fence_open": None,
    }
    cur = None
    in_fence = False
    seen_h2 = False
    for i, ln in enumerate(lines, 1):
        if FENCE_RE.match(ln):
            in_fence = not in_fence
            if in_fence:
                out["fence_open"] = i
            else:
                out["fence_open"] = None
            continue
        if in_fence:
            continue
        m = H_RE.match(ln)
        if m:
            lvl = len(m.group(1))
            if lvl == 1:
                out["h1"].append((i, m.group(2)))
            elif lvl == 2:
                seen_h2 = True
                cur = {"name": m.group(2), "line": i, "entries": []}
                out["sections"].append(cur)
            else:
                out["h3plus"].append((i, ln))
            continue
        if ln.startswith(">") and not seen_h2:
            out["blockquote"].append((i, ln[1:].strip()))
            continue
        lm = LINK_RE.match(ln)
        if lm:
            e = {
                "line": i,
                "name": lm.group(1),
                "url": lm.group(2),
                "notes": (lm.group(3) or "").strip(),
                "section": cur["name"] if cur else "",
            }
            out["entries"].append(e)
            if cur:
                cur["entries"].append(e)
            continue
        if BARE_URL_RE.match(ln):
            out["bare"].append((i, BARE_URL_RE.match(ln).group(1)))
            continue
        if seen_h2 and ln.strip() and not ln.lstrip().startswith("<!--"):
            out["stray"].append((i, ln))
    return out


def _sentences(s: str) -> int:
    return len([p for p in re.split(r"(?<=[.!?])\s+", s.strip()) if p])


def pass_structure(px: dict, kind: str) -> list[Finding]:
    f = []
    if px["fence_open"]:
        f.append(
            Finding(
                "P1",
                "I4",
                "high",
                "unclosed code fence swallows the rest of the file "
                "(no headings or link entries below it were parsed)",
                px["fence_open"],
            )
        )
    if len(px["h1"]) != 1:
        f.append(
            Finding(
                "P1",
                "I1",
                "high",
                f"{len(px['h1'])} H1 headings (need exactly one)",
                px["h1"][1][0] if len(px["h1"]) > 1 else 1,
            )
        )
    if not px["blockquote"]:
        f.append(Finding("P1", "I2", "medium", "no blockquote summary after the H1"))
    else:
        bq = " ".join(t for _, t in px["blockquote"])
        if _sentences(bq) > BLOCKQUOTE_MAX_SENTENCES:
            f.append(
                Finding(
                    "P1",
                    "I2",
                    "medium",
                    f"blockquote is {_sentences(bq)} sentences (max {BLOCKQUOTE_MAX_SENTENCES})",
                    px["blockquote"][0][0],
                )
            )
        if px["h1"] and bq.strip().lower() == px["h1"][0][1].strip().lower():
            f.append(
                Finding("P1", "I2", "medium", "blockquote restates the H1", px["blockquote"][0][0])
            )
    for i, _ln in px["h3plus"][:1]:
        f.append(
            Finding(
                "P1",
                "I4",
                "medium",
                f"{len(px['h3plus'])} H3+ heading(s); sections must be H2 link lists",
                i,
            )
        )
    for i, _ln in px["stray"][:1]:
        f.append(
            Finding(
                "P1",
                "I4",
                "medium",
                f"{len(px['stray'])} prose line(s) after the first H2 "
                "(only list items belong there)",
                i,
            )
        )
    total = len(px["entries"]) + len(px["bare"]) + len(px["stray"])
    if px["bare"]:
        share = len(px["entries"]) / total if total else 1
        f.append(
            Finding(
                "P1",
                "I5",
                "high" if share < BARE_URL_HIGH_SHARE else "medium",
                f"{len(px['bare'])} bare URL line(s) not in `- [name](url): notes` form",
                px["bare"][0][0],
                fixable=True,
            )
        )
    names = [s["name"].strip().lower() for s in px["sections"]]
    if "optional" in names and names[-1] != "optional":
        f.append(
            Finding(
                "P1",
                "N4",
                "medium",
                "`## Optional` is not the last section",
                px["sections"][names.index("optional")]["line"],
                fixable=True,
            )
        )
    if "optional" in names:
        opt = px["sections"][names.index("optional")]
        hot = [
            e for e in opt["entries"] if re.search(r"/(reference|api|pricing|auth)", e["url"], re.I)
        ]
        if hot:
            f.append(
                Finding(
                    "P1",
                    "N4",
                    "medium",
                    f"{len(hot)} reference/pricing/auth link(s) under `## Optional`",
                    hot[0]["line"],
                )
            )
    if kind == "index" and not px["sections"] and px["entries"]:
        f.append(
            Finding("P1", "I4", "low", "links are not grouped under H2 sections (validator-only)")
        )
    return f


def _duplicate_lines(items) -> list[int]:
    """Line numbers of every item whose key repeats an earlier one. `items` is
    an iterable of (key, line) pairs; the first occurrence of a key is never
    counted, every later one is. Shared by the four near-identical dedup
    scans (link targets, descriptions, page blocks, vocabulary terms) that
    previously hand-rolled this five-line idiom with divergent shapes."""
    seen: set[str] = set()
    dupes: list[int] = []
    for key, line in items:
        if key in seen:
            dupes.append(line)
        else:
            seen.add(key)
    return dupes


def pass_links(
    px: dict, kind: str, text: str, check: bool = False, base_dir: Path | None = None
) -> list[Finding]:
    f = []
    if base_dir is not None:
        base = base_dir.resolve()
        rel = [
            e
            for e in px["entries"]
            if "://" not in e["url"] and not e["url"].startswith(("/", "#"))
        ]
        escaped, missing = [], []
        for e in rel:
            tgt = (base / e["url"].split("#")[0]).resolve()
            if not tgt.is_relative_to(base):
                escaped.append(e)
            elif not tgt.exists():
                missing.append(e)
        if escaped:
            f.append(
                Finding(
                    "P2",
                    "N6",
                    "high",
                    f"{len(escaped)} relative link(s) escape the export directory via `..`: "
                    + ", ".join(e["url"] for e in escaped[:5]),
                    escaped[0]["line"],
                )
            )
        if missing:
            f.append(
                Finding(
                    "P2",
                    "N6",
                    "high",
                    f"{len(missing)} relative link(s) to files that do not exist beside the index: "
                    + ", ".join(e["url"] for e in missing[:5]),
                    missing[0]["line"],
                )
            )
    internal = bool(INTERNAL_MARK_RE.search(text[:HEAD_WINDOW]))
    priv = [e for e in px["entries"] if PRIVATE_RE.search(e["url"])]
    if priv and not internal:
        f.append(
            Finding(
                "P2",
                "P2",
                "high",
                f"{len(priv)} link(s) to a private mirror path in a file not marked internal "
                "(add `<!-- internal -->` or link the canonical URL)",
                priv[0]["line"],
            )
        )
    dupes = _duplicate_lines((e["url"].rstrip("/"), e["line"]) for e in px["entries"])
    if dupes:
        f.append(
            Finding("P2", "N7", "low", f"{len(dupes)} duplicate link target(s) across sections")
        )
    if kind == "family":
        pages = [
            e
            for e in px["entries"]
            if not e["url"].rstrip("/").endswith("llms.txt")
            and not e["url"].endswith("llms-facts.txt")
        ]
        if pages:
            f.append(
                Finding(
                    "P2",
                    "F1",
                    "high",
                    f"family file links {len(pages)} page(s); families link indexes only",
                    pages[0]["line"],
                )
            )
    if check:
        f += _check_links([e for e in px["entries"] if e["url"].startswith("http")])
    return f


def _head(url: str, deadline: float | None = None) -> tuple[str, int, str, str]:
    """(url, status, content_type, reason). `status` is 0 for a genuine
    network failure, -1 for a URL refused before any request (not public, or
    the whole-sweep deadline already passed) — callers must not treat -1 the
    same as a dead link. Every fetch and every redirect hop is re-validated
    by `_public_url()` via `_SAFE_OPENER`, so an allowlisted URL can't 302 to
    a loopback/private/link-local/reserved address. Retries once, only for
    transient failures (network errors, 429, 5xx), with jittered backoff —
    never for a permanent 4xx or a malformed-URL `ValueError`."""
    if not _public_url(url):
        return url, -1, "", "refused: not a public host"
    if deadline is not None and time.monotonic() > deadline:
        return url, -1, "", "skipped: link-check time budget exhausted"
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": LINK_UA})
    for attempt in range(2):
        try:
            with _SAFE_OPENER.open(req, timeout=LINK_TIMEOUT) as r:  # noqa: S310
                return url, r.status, r.headers.get("Content-Type", ""), ""
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt == 0:
                e.close()
                time.sleep(0.5 + random.random())
                continue
            e.close()
            return url, e.code, "", ""
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt == 0 and not (deadline is not None and time.monotonic() > deadline):
                time.sleep(0.5 + random.random())
                continue
            return url, 0, "", str(e)
        except ValueError as e:  # malformed URL — not transient, never retry
            return url, -1, "", str(e)
    return url, 0, "", "retry loop exhausted"


def _check_links(entries: list[dict]) -> list[Finding]:
    if not entries:
        return []
    urls = list(dict.fromkeys(e["url"] for e in entries))  # dedupe before any request
    deadline = time.monotonic() + LINK_BUDGET
    with ThreadPoolExecutor(max_workers=LINK_CONCURRENCY) as ex:
        try:
            res = list(ex.map(functools.partial(_head, deadline=deadline), urls))
        except Exception as exc:  # a worker escaping _head's own handling degrades, not crashes
            return [Finding("P2", "N6", "na", f"link check aborted: {exc}")]
    by_url = {u: r for u, r in zip(urls, res, strict=False)}
    results = [by_url[e["url"]] for e in entries]
    refused = [(e, r) for e, r in zip(entries, results, strict=False) if r[1] == -1]
    dead = [(e, r) for e, r in zip(entries, results, strict=False) if r[1] == 0]
    bad_status = [(e, r) for e, r in zip(entries, results, strict=False) if r[1] >= 400]
    html = [
        e
        for e, (_, s, ct, _reason) in zip(entries, results, strict=False)
        if 200 <= s < 400 and "text/html" in ct and not e["url"].endswith(".md")
    ]
    f = []
    if dead or bad_status:
        combined = dead + bad_status
        f.append(
            Finding(
                "P2",
                "N6",
                "high",
                f"{len(combined)} dead link(s): "
                + ", ".join(f"{e['url']} [{r[1]}: {r[3]}]" if r[3] else f"{e['url']} [{r[1]}]"
                            for e, r in combined[:8]),
                combined[0][0]["line"],
            )
        )
    if refused:
        f.append(
            Finding(
                "P2",
                "N6",
                "na",
                f"{len(refused)} link(s) not checked: " + "; ".join(
                    f"{e['url']} ({r[3]})" for e, r in refused[:8]
                ),
                refused[0][0]["line"],
            )
        )
    if html:
        f.append(
            Finding(
                "P2",
                "N6",
                "medium",
                f"{len(html)} link(s) return text/html (no markdown twin linked)",
                html[0]["line"],
            )
        )
    return f


def pass_descriptions(px: dict, kind: str) -> list[Finding]:
    f = []
    es = px["entries"]
    if not es:
        return f
    missing = [e for e in es if not e["notes"]]
    if missing:
        share = len(missing) / len(es)
        is_high = share > DESC_MISSING_HIGH_SHARE and len(missing) >= DESC_MISSING_HIGH_MIN
        f.append(
            Finding(
                "P3",
                "D1",
                "high" if is_high else "medium",
                f"{len(missing)}/{len(es)} link(s) without a description",
                missing[0]["line"],
            )
        )
    band_out = [
        e
        for e in es
        if e["notes"] and not (DESC_WORDS[0] <= len(e["notes"].split()) <= DESC_WORDS[1])
    ]
    if es and len(band_out) / len(es) > DESC_BAND_TOLERANCE:
        f.append(
            Finding(
                "P3",
                "D3",
                "low",
                f"{len(band_out)} description(s) outside the "
                f"{DESC_WORDS[0]}–{DESC_WORDS[1]} word band",
                band_out[0]["line"],
            )
        )
    ell = [e for e in es if e["notes"].endswith(("...", "…"))]
    if ell:
        f.append(
            Finding(
                "P3",
                "D3",
                "low",
                f"{len(ell)} truncated description(s) ending in an ellipsis",
                ell[0]["line"],
            )
        )
    dup = _duplicate_lines(
        (e["notes"].strip().lower(), e["line"]) for e in es if e["notes"].strip()
    )
    if dup:
        f.append(Finding("P3", "D4", "medium", f"{len(dup)} duplicate description(s)"))
    restated = [
        e
        for e in es
        if e["notes"] and e["notes"].strip().rstrip(".").lower() == e["name"].strip().lower()
    ]
    if restated:
        f.append(
            Finding(
                "P3",
                "D2",
                "medium",
                f"{len(restated)} description(s) merely restate the link name",
                restated[0]["line"],
            )
        )
    if kind == "family":
        nocount = [
            e
            for e in es
            if e["url"].rstrip("/").endswith("llms.txt") and not COUNTS_RE.search(e["notes"])
        ]
        if nocount:
            f.append(
                Finding(
                    "P3",
                    "D6",
                    "medium",
                    f"{len(nocount)} family line(s) without page/token counts",
                    nocount[0]["line"],
                )
            )
    return f


# ---------------------------------------------------------------------------
# P5 size ladder
# ---------------------------------------------------------------------------


def pass_size(path: Path, kind: str, text: str) -> list[Finding]:
    f = []
    n = len(text.encode("utf-8"))
    d = path.parent
    if kind in ("index", "family"):
        if n > INDEX_HARD_BYTES:
            f.append(
                Finding(
                    "P5",
                    "S1",
                    "high",
                    f"index is {n:,} bytes — that is a full file wearing the wrong name",
                )
            )
        elif n > INDEX_MAX_BYTES:
            f.append(
                Finding(
                    "P5",
                    "S1",
                    "medium",
                    f"index is {n:,} bytes (> {INDEX_MAX_BYTES:,}); split hub-and-spoke",
                )
            )
    if kind == "full" and not (d / "llms-small.txt").exists():
        f.append(
            Finding(
                "P5", "S2", "medium", "no llms-small.txt beside the full file (size ladder missing)"
            )
        )
    if kind == "small" and len(text) > SMALL_MAX_CHARS:
        f.append(
            Finding(
                "P5",
                "S3",
                "medium",
                f"small variant is {len(text):,} chars (> {SMALL_MAX_CHARS:,})",
            )
        )
    if kind == "facts" and (d / "llms-full.txt").exists():
        ratio = n / max(1, (d / "llms-full.txt").stat().st_size)
        if ratio > FACTS_RATIO_MED:
            f.append(
                Finding("P5", "S4", "medium", f"facts/full ratio {ratio:.2f} (> {FACTS_RATIO_MED})")
            )
        elif ratio > FACTS_RATIO_LOW:
            f.append(
                Finding("P5", "S4", "low", f"facts/full ratio {ratio:.2f} (> {FACTS_RATIO_LOW})")
            )
    siblings = [p for p in d.glob("llms*.txt")] if d.is_dir() else []
    man = d / "manifest.json"
    if len(siblings) >= 2 and not man.exists():
        f.append(Finding("P5", "H8", "medium", "manifest.json missing from the export directory"))
    elif man.exists():
        try:
            raw_m = json.loads(man.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            f.append(Finding("P5", "H8", "medium", f"manifest.json unreadable: {e}"))
        except OSError as e:
            f.append(Finding("P5", "H8", "medium", f"manifest.json unreadable: {e}"))
        else:
            if not isinstance(raw_m, dict):
                f.append(Finding("P5", "H8", "medium", "manifest.json is not a JSON object"))
            elif "files" in raw_m and not isinstance(raw_m["files"], dict):
                # Distinct from the "files" key being absent (older manifests
                # keep byte records at the top level, handled below) — this is
                # the key present but malformed, which the old `m.get("files",
                # m)` fallback silently mistook for "absent" and dropped the
                # whole drift check with no finding at all.
                f.append(
                    Finding(
                        "P5", "H8", "medium",
                        f"manifest.json 'files' is a {type(raw_m['files']).__name__}, "
                        "not an object",
                    )
                )
            else:
                files = raw_m.get("files", raw_m)
                rec = files.get(path.name) if isinstance(files, dict) else None
                b = rec.get("bytes") if isinstance(rec, dict) else None
                if b is not None and (isinstance(b, bool) or not isinstance(b, int)):
                    f.append(
                        Finding(
                            "P5",
                            "H8",
                            "medium",
                            f"manifest 'bytes' for {path.name} is {type(b).__name__}, not an int",
                        )
                    )
                elif b and abs(b - n) / max(b, 1) > MANIFEST_DRIFT_TOLERANCE:
                    f.append(
                        Finding(
                            "P5",
                            "H8",
                            "medium",
                            f"manifest says {b:,} bytes, file is {n:,} "
                            f"(> {MANIFEST_DRIFT_TOLERANCE:.0%} drift — regenerate)",
                        )
                    )
    return f


# ---------------------------------------------------------------------------
# P6 full-file fidelity
# ---------------------------------------------------------------------------


def pass_full(text: str, grammar: str, blocks: list[dict] | None = None) -> list[Finding]:
    """P6 full-file fidelity. Emits C1 (grammar/banner), C2 (block title/URL),
    C3 (residue), C4 (fences), C5 (duplicate blocks), S6 (oversized block).
    `blocks`, when the caller already parsed `split_llms_full(text)` (as
    `check()` does), skips a second full-text parse."""
    f = []
    if grammar == "none":
        return [
            Finding(
                "P6",
                "C1",
                "high",
                "no recognised page grammar "
                "(mintlify / anthropic-yaml / cloudflare-frontmatter / firecrawl)",
            )
        ]
    if blocks is None:
        blocks = split_llms_full(text)
    if not blocks:
        return [
            Finding("P6", "C1", "high", f"grammar {grammar} detected but zero page blocks parsed")
        ]
    if not BANNER_RE.search(text[:HEAD_WINDOW]):
        f.append(
            Finding("P6", "C1", "low", "no header comment naming the grammar", 1, fixable=True)
        )
    no_title = [b for b in blocks if not (b.get("title") or "").strip()]
    no_url = [b for b in blocks if not (b.get("url") or "").startswith("http")]
    if no_title or no_url:
        f.append(
            Finding(
                "P6",
                "C2",
                "high",
                f"{len(no_title)} block(s) without a title, {len(no_url)} without a source URL",
            )
        )
    # Union-gated pre-filter before trying all 4 RESIDUE_RES patterns per line
    # — same result, ~3x faster on a large file. Scanned over the whole text
    # (not the per-block loop below) so residue sitting *between* page blocks
    # still counts.
    residue = sum(
        1
        for ln in text.splitlines()
        if RESIDUE_GATE_RE.search(ln) and any(r.search(ln) for r in RESIDUE_RES)
    )
    unbalanced = 0
    untagged = 0
    fences = 0
    big = 0
    dups = len(_duplicate_lines((((b.get("url") or "").rstrip("/")), 1) for b in blocks))
    for b in blocks:
        body = b.get("text", "")
        fence_open = None
        for ln in body.splitlines():
            m = FENCE_RE.match(ln)
            if m:
                if fence_open is None:
                    fence_open = ln.strip()
                    fences += 1
                    if len(ln.strip()) <= 3:
                        untagged += 1
                else:
                    fence_open = None
        if fence_open is not None:
            unbalanced += 1
        if len(body.encode("utf-8")) > BLOCK_MAX_BYTES:
            big += 1
    if residue:
        f.append(
            Finding("P6", "C3", "medium", f"{residue} navigation/MDX residue line(s)", fixable=True)
        )
    if unbalanced:
        f.append(
            Finding("P6", "C4", "medium", f"{unbalanced} page block(s) with an unclosed code fence")
        )
    if fences and untagged / fences > UNTAGGED_FENCE_TOLERANCE:
        f.append(
            Finding("P6", "C4", "low", f"{untagged}/{fences} code fences without a language tag")
        )
    if dups:
        f.append(Finding("P6", "C5", "medium", f"{dups} duplicate page block(s) (same source URL)"))
    if big:
        f.append(Finding("P6", "S6", "low", f"{big} page block(s) over {BLOCK_MAX_BYTES:,} bytes"))
    return f


# ---------------------------------------------------------------------------
# P7 facts-file shape
# ---------------------------------------------------------------------------


def _mirror_headings(mirror: Path | None) -> dict[str, set[str]]:
    """url -> {anchor slugs} from a banner mirror, for anchor resolution.
    Cached per (path, mtime): a split export has hundreds of files and the
    mirror is tens of MB, so re-parsing it per file made the gate O(n²).

    An empty dict here is ambiguous between "no --mirror given" and "a mirror
    was given but couldn't be read/parsed" — the caller must distinguish the
    two (see `_no_mirror_finding`) rather than report both as `--mirror` not
    having been passed."""
    if not mirror:
        return {}
    if not mirror.exists():
        print(f"llms_lint: --mirror {mirror} does not exist", file=sys.stderr)
        return {}
    return _mirror_headings_cached(str(mirror), mirror.stat().st_mtime_ns)


@functools.lru_cache(maxsize=8)
def _mirror_headings_cached(path: str, _mtime: int) -> dict[str, set[str]]:
    mirror = Path(path)
    try:
        from docset_indexer import parse_mirror
        from docset_refine import slug
    except ImportError as e:
        # Previously a bare `except Exception` swallowed this and the caller
        # reported "no mirror; pass --mirror" even when a real, readable
        # mirror WAS passed — actively misleading on a thin box where these
        # optional helper modules aren't installed.
        print(f"llms_lint: mirror anchor resolution unavailable ({e}); "
              "R3 will report na for every facts/vocabulary file this run", file=sys.stderr)
        return {}
    try:
        mirror_text = mirror.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"llms_lint: could not read mirror {mirror}: {e}", file=sys.stderr)
        return {}
    pages = parse_mirror(mirror_text) or []
    out: dict[str, set[str]] = {}
    for p in pages:
        s = set()
        for ln in p.get("text", "").splitlines():
            m = H_RE.match(ln)
            if m:
                s.add("#" + slug(m.group(2)))
        out[p["url"].rstrip("/")] = s
    return out


def _anchor_unresolved(heads: dict[str, set[str]], src: str) -> bool:
    """True when `src`'s `#anchor` doesn't resolve to a heading slug the
    mirror actually has for that page. Shared by pass_facts and
    pass_vocabulary, which previously duplicated this three-line check with
    no mechanism to keep them in sync."""
    base, _, anchor = src.partition("#")
    page = heads.get(base.rstrip("/"))
    return page is not None and bool(anchor) and ("#" + anchor) not in page


def _no_mirror_finding() -> Finding:
    return Finding("P7", "R3", "na", "anchor resolution N/A (no mirror; pass --mirror)")


def pass_facts(text: str, path: Path, mirror: Path | None) -> list[Finding]:
    f = []
    lines = text.splitlines()
    units, bad_type, no_src, long_u, unresolved = [], [], [], [], []
    heads = _mirror_headings(mirror)
    page_urls: set[str] = set()
    for i, ln in enumerate(lines, 1):
        if ln.startswith("<http") and ln.endswith(">"):
            page_urls.add(ln[1:-1].rstrip("/"))
        if not ln.startswith("- ["):
            continue
        m = UNIT_RE.match(ln)
        if not m:
            no_src.append(i)
            continue
        typ, body, src = m.groups()
        units.append(i)
        if typ not in UNIT_TYPES:
            bad_type.append(i)
        if not src.startswith("http") and not src.startswith("/") and not src.startswith("."):
            no_src.append(i)
        if len(body) > UNIT_MAX_CHARS or _sentences(body) > UNIT_MAX_SENTENCES:
            long_u.append(i)
        if heads and _anchor_unresolved(heads, src):
            unresolved.append(i)
    if not units and not no_src:
        return [Finding("P7", "C6", "high", "no unit lines found (`- [type] text — url#anchor`)")]
    if no_src:
        f.append(
            Finding(
                "P7", "C6", "high", f"{len(no_src)} unit line(s) without a source URL", no_src[0]
            )
        )
    if bad_type:
        f.append(
            Finding(
                "P7",
                "C6",
                "medium",
                f"{len(bad_type)} unit(s) with a type outside UNIT_TYPES",
                bad_type[0],
            )
        )
    if long_u and len(long_u) / max(1, len(units)) > LONG_UNIT_TOLERANCE:
        f.append(
            Finding(
                "P7",
                "C6",
                "medium",
                f"{len(long_u)} unit(s) longer than {UNIT_MAX_SENTENCES} sentences / "
                f"{UNIT_MAX_CHARS} chars",
                long_u[0],
            )
        )
    if unresolved:
        share = len(unresolved) / max(1, len(units))
        f.append(
            Finding(
                "P7",
                "R3",
                "high" if share > ANCHOR_UNRESOLVED_HIGH_SHARE else "medium",
                f"{len(unresolved)} anchor(s) do not resolve to a heading in the mirror",
                unresolved[0],
            )
        )
    idx = path.parent / "llms.txt"
    if idx.exists() and page_urls:
        try:
            idx_text = idx.read_text(encoding="utf-8", errors="replace")
        except OSError:
            idx_text = None
        if idx_text is not None:
            px = parse_index(idx_text)
            idx_urls = {re.sub(r"\.md$", "", e["url"]).rstrip("/") for e in px["entries"]}
            idx_urls |= {re.sub(r"\.html?\.md$", "", u) for u in idx_urls}
            gap = [u for u in idx_urls if u.startswith("http") and u not in page_urls]
            if idx_urls and len(gap) / len(idx_urls) > FACTS_COVERAGE_GAP_TOLERANCE:
                f.append(
                    Finding(
                        "P7",
                        "R7",
                        "medium",
                        f"{len(gap)}/{len(idx_urls)} indexed page(s) "
                        "have no units in the facts file",
                    )
                )
    if not heads:
        f.append(_no_mirror_finding())
    return f


# ---------------------------------------------------------------------------
# P7 vocabulary-file shape
# ---------------------------------------------------------------------------


def parse_vocab_line(ln: str) -> tuple[str, str, str] | None:
    """(term, definition, source) for a `- **term** …` line, else None.
    `source` is "" when the line carries no ` — url` field."""
    m = VOCAB_RE.match(ln)
    if not m:
        return None
    term, rest = m.group("term").strip(), m.group("rest")
    src = ""
    sm = VOCAB_SRC_RE.search(rest)
    if sm:
        src = sm.group("src")
        rest = rest[: sm.start()]
    definition = re.split(r"\s+·\s+", rest, maxsplit=1)[0].strip()
    return term, definition, src


def pass_vocabulary(text: str, mirror: Path | None) -> list[Finding]:
    """One term per line, each sourced, unique, and anchored in the mirror.
    Lines under `## Named, not yet defined` are plain `- term` bullets (no
    bold) and are not term lines."""
    f = []
    terms, no_src, long_d, unresolved = [], [], [], []
    term_keys: list[tuple[str, int]] = []
    heads = _mirror_headings(mirror)
    named_only = 0          # plain `- term` bullets under "Named, not yet defined"
    in_tail = False
    for i, ln in enumerate(text.splitlines(), 1):
        if ln.startswith("#"):
            in_tail = NAMED_TAIL_RE.match(ln) is not None
        if in_tail and ln.startswith("- ") and not ln.startswith("- **"):
            named_only += 1
        if not ln.startswith("- **"):
            continue
        parsed = parse_vocab_line(ln)
        if parsed is None:
            no_src.append(i)
            continue
        term, definition, src = parsed
        terms.append(i)
        term_keys.append((" ".join(term.casefold().split()), i))
        if not src:
            no_src.append(i)
        if len(definition) > VOCAB_DEF_MAX:
            long_d.append(i)
        if heads and src and _anchor_unresolved(heads, src):
            unresolved.append(i)
    dupes = _duplicate_lines(term_keys)
    if not terms and not no_src:
        # A generated vocabulary whose terms are all still undefined is a valid
        # file with an empty `## Terms` — the gap is research, not shape.
        if named_only:
            return [
                Finding("P7", "C6", "medium",
                        f"no defined term lines yet — {named_only} term(s) named but undefined")
            ]
        return [
            Finding("P7", "C6", "high", "no term lines found (`- **term** — definition — url`)")
        ]
    if no_src:
        f.append(
            Finding(
                "P7", "C6", "high", f"{len(no_src)} term line(s) without a source URL", no_src[0]
            )
        )
    if dupes:
        f.append(
            Finding(
                "P7",
                "D4",
                "medium",
                f"{len(dupes)} duplicate canonical term(s) — merge or rename",
                dupes[0],
            )
        )
    if long_d:
        f.append(
            Finding(
                "P7",
                "C6",
                "medium",
                f"{len(long_d)} definition(s) longer than {VOCAB_DEF_MAX} chars",
                long_d[0],
            )
        )
    if unresolved:
        f.append(
            Finding(
                "P7",
                "R3",
                "medium",
                f"{len(unresolved)} anchor(s) do not resolve to a heading in the mirror",
                unresolved[0],
            )
        )
    if not heads:
        f.append(_no_mirror_finding())
    return f


# ---------------------------------------------------------------------------
# P9 trust
# ---------------------------------------------------------------------------


def pass_trust(text: str, kind: str, third_party: bool) -> list[Finding]:
    f = []
    head = text[:HEAD_WINDOW]
    if not BANNER_RE.search(head):
        f.append(
            Finding(
                "P9",
                "P1",
                "medium",
                "no provenance banner (generator / generated date / verified-as-of)",
                1,
                fixable=False,
            )
        )
    if third_party and kind in ("full", "small") and not INTERNAL_MARK_RE.search(head):
        f.append(
            Finding(
                "P9",
                "P3",
                "high",
                "third-party full text without an `<!-- internal -->` marker (republication)",
                1,
                # not fixable: inserting a rights marker asserts a fact about
                # licensing that only a human can verify — apply_fixes() has
                # no code path for this attr, so it stays unfixed by design.
                fixable=False,
            )
        )
    in_fence = False
    pem_open = False
    lines = text.splitlines()
    for i, ln in enumerate(lines, 1):
        if FENCE_RE.match(ln):
            in_fence = not in_fence
        if SECRET_GATE_RE.search(ln) and any(r.search(ln) for r in SECRET_RES):
            if _placeholder_secret(ln):
                f.append(Finding("P9", "P5", "low", "placeholder credential in an example", i))
            else:
                f.append(Finding("P9", "P5", "high", "secret/credential pattern in text", i))
        # A PEM header alone carries no key; docs print it constantly. Only a
        # base64 body line right after it is key material.
        if PEM_HEADER_RE.search(ln):
            pem_open = True
            f.append(Finding("P9", "P5", "low", "PEM private-key header (no key material)", i))
        elif pem_open and ln.strip():
            pem_open = False
            if PEM_BODY_RE.match(ln.strip()):
                if _EXAMPLE_RE.search(_heading_above(lines, i)):
                    f.append(
                        Finding(
                            "P9", "P5", "low", "example/sample key material (published as such)", i
                        )
                    )
                else:
                    f.append(
                        Finding("P9", "P5", "high", "private key material after a PEM header", i)
                    )
        # Docs about prompt injection quote the very phrases a steering file
        # would use; a hit inside a code fence, a table row, or a quoted /
        # backticked span is evidence, not steering. Prose hits are candidates
        # the model pass (P9) confirms before they count as High.
        m = (
            None
            if in_fence or ln.lstrip().startswith(("|", ">")) or not STEER_GATE_RE.search(ln)
            else _steer_hit(ln)
        )
        if m is not None and not _in_quotes(ln, m.start()):
            f.append(
                Finding(
                    "P9",
                    "P4",
                    "medium",
                    "possible instruction aimed at the reading model — model confirms (P9)",
                    i,
                )
            )
    return f


_PLACEHOLDER_RE = re.compile(
    r"(\.\.\.|xxx|your[-_ ]|example|placeholder|1234567890|abcdef|AbCd|<[^>]+>|REDACTED|\*{3,})",
    re.I,
)


def _placeholder_secret(line: str) -> bool:
    return bool(_PLACEHOLDER_RE.search(line))


_EXAMPLE_RE = re.compile(r"\b(example|sample|test|dummy|placeholder)\b", re.I)


def _heading_above(lines: list[str], line_no: int, window: int = HEADING_LOOKBACK_LINES) -> str:
    """Nearest markdown heading above `line_no` (1-based) in an already-split
    `lines` list, within `window` lines. Takes the split text, not the raw
    string — re-splitting per call from inside pass_trust's per-line loop
    made this O(k·n) in the number of PEM blocks on a large file."""
    for j in range(line_no - 2, max(-1, line_no - 2 - window), -1):
        m = H_RE.match(lines[j])
        if m:
            return m.group(2)
    return ""


def _steer_hit(line: str):
    for r in STEER_RES:
        m = r.search(line)
        if m:
            return m
    return None


_APOSTROPHE_QUOTE_RE = re.compile(r"(?<!\w)'|'(?!\w)")  # a `'` not glued to a contraction


def _in_quotes(line: str, pos: int) -> bool:
    """True when `pos` sits inside an open \", ' or ` span on the line.

    A `'` between two word characters ("don't", "shouldn't") is a contraction,
    not a quote delimiter — counting it toward the parity check let a single
    contraction anywhere earlier on the line silently suppress a real steering
    match later on the same line (confirmed: "you shouldn't ignore all
    previous instructions" produced zero P4 findings)."""
    before = line[:pos]
    quote_parity_odd = any(before.count(q) % 2 == 1 for q in ('"', "`"))
    apostrophe_parity_odd = len(_APOSTROPHE_QUOTE_RE.findall(before)) % 2 == 1
    return quote_parity_odd or apostrophe_parity_odd


# ---------------------------------------------------------------------------
# P14 hygiene
# ---------------------------------------------------------------------------


def pass_hygiene(raw: bytes) -> tuple[list[Finding], bytes]:
    f = []
    fixed = raw
    if raw.startswith(b"\xef\xbb\xbf"):
        f.append(Finding("P14", "H1", "hygiene", "UTF-8 BOM", 1, True))
        fixed = fixed[3:]
    if b"\r\n" in fixed:
        f.append(Finding("P14", "H1", "hygiene", "CRLF line endings", 1, True))
        fixed = fixed.replace(b"\r\n", b"\n")
    try:
        text = fixed.decode("utf-8")
    except UnicodeDecodeError as e:
        return [Finding("P14", "H1", "high", f"not valid UTF-8 at byte {e.start}")], raw
    lines = text.split("\n")
    out = []
    tabs = trail = badurl = 0
    for i, ln in enumerate(lines, 1):
        if ln.lstrip().startswith(("- ", "* ")) and "\t" in ln:
            tabs += 1
            ln = ln.replace("\t", " ")
        if ln != ln.rstrip():
            trail += 1
            ln = ln.rstrip()
        m = LINK_RE.match(ln)
        if m and BAD_URL_CHARS.search(m.group(2)):
            badurl += 1
            f.append(Finding("P14", "H1", "high", "smart quote / zero-width char inside a URL", i))
        out.append(ln)
    if tabs:
        f.append(Finding("P14", "H1", "hygiene", f"{tabs} list line(s) with tabs", 0, True))
    if trail:
        f.append(
            Finding("P14", "H1", "hygiene", f"{trail} line(s) with trailing whitespace", 0, True)
        )
    text2 = "\n".join(out).rstrip("\n") + "\n"
    if not text.endswith("\n") or text.endswith("\n\n"):
        f.append(Finding("P14", "H1", "hygiene", "file must end with exactly one newline", 0, True))
    return f, text2.encode("utf-8")


# ---------------------------------------------------------------------------
# safe fixes
# ---------------------------------------------------------------------------


def apply_fixes(text: str, kind: str, grammar: str) -> tuple[str, set[str]]:
    """(new_text, applied_attrs). `applied_attrs` names exactly which
    finding attrs this call actually rewrote — `check()` marks a `fixable`
    finding as `fixed` only when its attr is in this set, never on the mere
    presence of `fixable=True`. Before this, every fixable finding was
    stamped fixed unconditionally: a High third-party-marker finding (P3,
    which this function has no code path for) or a non-mintlify grammar
    banner (C1, only handled when grammar == "mintlify") came back `fixed:
    true` with the file byte-for-byte unchanged, silently passing a CI gate
    that should have failed."""
    lines = text.split("\n")
    applied: set[str] = set()
    if kind in ("index", "family"):
        # bare URL -> link line
        for i, ln in enumerate(lines):
            m = BARE_URL_RE.match(ln)
            if m and not LINK_RE.match(ln):
                url = m.group(1)
                name = url.rstrip("/").rsplit("/", 1)[-1] or url
                lines[i] = f"- [{name}]({url})"
                applied.add("I5")
        # ## Optional last
        text = "\n".join(lines)
        parts = re.split(r"(?m)^(?=## )", text)
        head, secs = parts[0], parts[1:]
        opt = [s for s in secs if s.lower().startswith("## optional")]
        rest = [s for s in secs if not s.lower().startswith("## optional")]
        if opt and secs[-1] is not opt[0]:
            text = (
                head
                + "".join(s if s.endswith("\n\n") else s.rstrip("\n") + "\n\n" for s in rest)
                + opt[0]
            )
            applied.add("N4")
        return text.rstrip("\n") + "\n", applied
    if kind in ("full", "small"):
        kept = [ln for ln in lines if not any(r.search(ln) for r in RESIDUE_RES)]
        if len(kept) != len(lines):
            applied.add("C3")
        text = "\n".join(kept)
        if grammar == "mintlify" and not BANNER_RE.search(text[:HEAD_WINDOW]):
            text = (
                "<!-- llms-full grammar: mintlify — per page: '# Title' / 'Source: <url>' / "
                "blank / body -->\n\n" + text
            )
            applied.add("C1")
        return text.rstrip("\n") + "\n", applied
    return text, applied


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------


def check(
    path: Path,
    kind: str | None = None,
    check_links: bool = False,
    mirror: Path | None = None,
    third_party: bool = False,
    fix: bool = False,
) -> dict:
    """Run every deterministic pass on `path`. The returned dict always has
    the same shape — `file`, `kind`, `grammar`, `findings`, `counts` — on
    every path including the unknown-kind and oversized-input early returns;
    a caller reading `res["counts"]` must never see a KeyError."""
    size = path.stat().st_size
    if size > MAX_INPUT_BYTES:
        findings = [
            Finding(
                "P5",
                "S1",
                "high",
                f"{size:,} bytes exceeds the {MAX_INPUT_BYTES:,}-byte lint limit; "
                "split the export before linting",
            )
        ]
        return {
            "file": str(path),
            "kind": "unknown",
            "grammar": "none",
            "findings": findings,
            "counts": _counts(findings),
        }
    raw = path.read_bytes()
    hyg, fixed_bytes = pass_hygiene(raw)
    try:
        fixed_bytes.decode("utf-8")
        valid_utf8 = True
    except UnicodeDecodeError:
        valid_utf8 = False
    text = fixed_bytes.decode("utf-8", errors="replace")
    blocks = None
    det_kind, grammar = detect_kind(text, path.name)
    findings: list[Finding] = list(hyg)
    if kind and kind != det_kind and det_kind != "unknown":
        findings.append(
            Finding("P0", "I6", "medium", f"--kind {kind} but the file parses as {det_kind}")
        )
    kind = kind or det_kind
    name = path.name.lower()
    if name == "llms.txt" and det_kind in ("full", "small"):
        findings.append(
            Finding(
                "P0",
                "I6",
                "high",
                "llms.txt contains page bodies — it is a full file, not an index",
            )
        )
    if kind == "unknown":
        findings.append(
            Finding("P0", "I6", "high", "cannot tell what kind of llms file this is (pass --kind)")
        )
        return {
            "file": str(path),
            "kind": kind,
            "grammar": grammar,
            "findings": findings,
            "counts": _counts(findings),
        }
    if kind in ("index", "family"):
        px = parse_index(text)
        findings += pass_structure(px, kind)
        findings += pass_links(px, kind, text, check_links, path.parent)
        findings += pass_descriptions(px, kind)
    elif kind in ("full", "small"):
        if blocks is None:
            blocks = split_llms_full(text)
        findings += pass_full(text, grammar, blocks)
    elif kind == "facts":
        findings += pass_facts(text, path, mirror)
    elif kind == "vocabulary":
        findings += pass_vocabulary(text, mirror)
    findings += pass_size(path, kind, text)
    findings += pass_trust(text, kind, third_party)
    if fix:
        if not valid_utf8:
            # Encoding a `errors="replace"`-decoded string back to UTF-8 would
            # permanently swap every invalid byte for U+FFFD — irreversible
            # data loss with no backup. Refuse and say so rather than write.
            findings.append(
                Finding(
                    "P14",
                    "H1",
                    "high",
                    "refusing --fix: source is not valid UTF-8 "
                    "(fixing would silently replace invalid bytes with U+FFFD)",
                )
            )
        else:
            new_text, applied = apply_fixes(text, kind, grammar)
            new_bytes = new_text.encode("utf-8")
            if fixed_bytes != raw:  # pass_hygiene's BOM/CRLF/whitespace/EOL fixes
                applied = applied | {"H1"}
            if new_bytes != raw:
                tmp = path.with_name(path.name + ".tmp")
                tmp.write_bytes(new_bytes)
                os.replace(tmp, path)
                print(
                    f"llms_lint: rewrote {path} ({len(raw):,} -> {len(new_bytes):,} bytes; "
                    f"applied {sorted(applied)})",
                    file=sys.stderr,
                )
            for x in findings:
                if x["fixable"] and x["attr"] in applied:
                    x["fixed"] = True
    return {
        "file": str(path),
        "kind": kind,
        "grammar": grammar,
        "findings": findings,
        "counts": _counts(findings),
    }


def _counts(findings) -> dict:
    c = {"high": 0, "medium": 0, "low": 0, "hygiene": 0, "na": 0}
    for x in findings:
        c[x["severity"]] = c.get(x["severity"], 0) + 1
    return c


def _report(res: dict) -> str:
    out = [f"{res['file']}: kind={res['kind']} grammar={res['grammar']}"]
    order = {"high": 0, "medium": 1, "low": 2, "hygiene": 3, "na": 4}
    for x in sorted(res["findings"], key=lambda x: (order.get(x["severity"], 9), x["line"])):
        tag = " [fixed]" if x.get("fixed") else (" [fixable]" if x["fixable"] else "")
        loc = f":{x['line']}" if x["line"] else ""
        out.append(f"  {x['severity']:<7} {x['pass']:<3} {x['attr']:<3}{loc:<7} {x['msg']}{tag}")
    c = res.get("counts") or _counts(res["findings"])
    out.append("  " + " ".join(f"{k}={v}" for k, v in c.items()))
    return "\n".join(out)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("detect", help="print kind and grammar")
    d.add_argument("file")
    c = sub.add_parser("check", help="run every deterministic pass")
    c.add_argument("file", nargs="+")
    c.add_argument("--kind", choices=SELECTABLE_KINDS)
    c.add_argument("--check-links", action="store_true")
    c.add_argument("--fix", action="store_true")
    c.add_argument("--json", action="store_true")
    c.add_argument(
        "--mirror", help="banner mirror for anchor resolution (facts / vocabulary files)"
    )
    c.add_argument(
        "--third-party",
        action="store_true",
        help="source host is not ours (rights marker required)",
    )
    h = sub.add_parser("hygiene", help="byte hygiene only")
    h.add_argument("file")
    h.add_argument("--fix", action="store_true")
    a = p.parse_args(argv)
    if a.cmd == "detect":
        path = Path(a.file)
        # Hygiene-normalize before detecting, same as check() does — an
        # un-normalized BOM can make a link-free, H1-only index misclassify
        # as "unknown" here while check() (which always normalizes first)
        # correctly calls it "index" on the identical bytes.
        _, fixed_bytes = pass_hygiene(path.read_bytes())
        text = fixed_bytes.decode("utf-8", errors="replace")
        kind, grammar = detect_kind(text, path.name)
        print(json.dumps({"file": str(path), "kind": kind, "grammar": grammar}))
        return 0
    if a.cmd == "hygiene":
        path = Path(a.file)
        f, fixed = pass_hygiene(path.read_bytes())
        if a.fix:
            path.write_bytes(fixed)
        print(_report({"file": str(path), "kind": "-", "grammar": "-", "findings": f}))
        return 1 if any(x["severity"] == "high" for x in f) else 0
    rc = 0
    results = []
    for fp in a.file:
        path = Path(fp)
        if path.is_dir():
            depth0 = path.glob("llms*.txt")
            # sections of a split index/family/facts/full/small/vocabulary
            # export, at any depth — previously only literal `llms.txt`
            # siblings were matched below depth 0, so a split facts/full/
            # small/vocabulary file never got linted at all.
            deeper = path.rglob("*/llms*.txt")
            seen_resolved: set[Path] = set()
            files = []
            for q in sorted(
                {*depth0, *deeper},
                key=lambda q: (len(q.relative_to(path).parts), q.name != "llms.txt", str(q)),
            ):
                rq = q.resolve()
                if rq not in seen_resolved:
                    seen_resolved.add(rq)
                    files.append(q)
        else:
            files = [path]
        for f_ in files:
            try:
                res = check(
                    f_,
                    a.kind,
                    a.check_links,
                    Path(a.mirror) if a.mirror else None,
                    a.third_party,
                    a.fix,
                )
            except OSError as exc:
                # A single unreadable file (permissions, deleted mid-walk, a
                # broken symlink) previously aborted the whole batch with a
                # raw traceback and no partial output — now it's one High
                # finding for that file and the rest of the batch still runs.
                unreadable = [Finding("P0", "H1", "high", f"unreadable: {exc}")]
                res = {
                    "file": str(f_),
                    "kind": "unknown",
                    "grammar": "none",
                    "findings": unreadable,
                    "counts": _counts(unreadable),
                }
                print(f"llms_lint: {f_}: {exc}", file=sys.stderr)
            results.append(res)
            if any(x["severity"] == "high" and not x.get("fixed") for x in res["findings"]):
                rc = 1
    if a.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print("\n".join(_report(r) for r in results))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
