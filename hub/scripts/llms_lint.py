#!/usr/bin/env python3
"""llms_lint — the deterministic passes of the llms-deep-optimizer (`/ldo`).

Judges an llms.txt / family index / llms-full.txt / llms-small.txt / llms-facts.txt /
llms-vocabulary.txt against the attribute rubric in
~/.claude/skills/llms-deep-optimizer/references/attributes.md and emits findings
`{pass, attr, severity, line, msg, fixable}`. Severities follow the family ladder
(high / medium / low / hygiene). `--fix` applies only the fixes the passes
reference marks safe (byte hygiene, `## Optional` last, bare-URL wrap, residue
strip in full files). Model and live passes (P4, P8, P11-13) live in the skill.

Usage:
    llms_lint.py detect FILE
    llms_lint.py check  FILE [--kind K] [--check-links] [--fix] [--json] [--mirror M]
                             [--third-party] [--base-url U]
    llms_lint.py hygiene FILE [--fix]

Exit status: 1 when any High finding remains, else 0 — usable as a CI gate.
"""

from __future__ import annotations

import argparse
import functools
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

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
INDEX_MAX_BYTES = 10_000
INDEX_HARD_BYTES = 100_000
SMALL_MAX_CHARS = 200_000
BLOCK_MAX_BYTES = 200_000
FACTS_RATIO_LOW, FACTS_RATIO_MED = 0.15, 0.30
DESC_WORDS = (10, 25)
LINK_TIMEOUT = float(os.environ.get("HUB_LLMS_LINK_TIMEOUT", "10"))
LINK_CONCURRENCY = int(os.environ.get("HUB_LLMS_LINK_CONCURRENCY", "8"))

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
PRIVATE_RE = re.compile(
    r"^(file://|https?://(127\.0\.0\.1|localhost)\b|/Users/|.*text-mirror/)", re.I
)
INTERNAL_MARK_RE = re.compile(r"<!--.*\binternal\b.*-->", re.I | re.S)
BANNER_RE = re.compile(r"<!--.*(generated|verified-as-of|llms-full grammar).*-->", re.I | re.S)
RESIDUE_RES = (
    re.compile(r"^\s*>\s*Documentation Index\b"),
    re.compile(r"^\s*\[Skip to (content|main)\]"),
    re.compile(r"theme=\{null\}"),
    re.compile(r"^\s*import\s+\{?[\w, ]+\}?\s+from\s+['\"][^'\"]+['\"];?\s*$"),
)
SECRET_RES = (
    re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
)
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
FENCE_RE = re.compile(r"^\s*(```|~~~)")
BAD_URL_CHARS = re.compile(r"[‘’“”​‌‍﻿]")


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
    head = text[:200_000]
    if "<|firecrawl-page-" in head:
        return "firecrawl"
    if re.search(r"^Source:\s*https?://", head, re.M):
        return "mintlify"
    if re.search(r"^---\s*\n(?:.*\n)*?title:", head, re.M):
        if "[View as Markdown]" in head or re.search(r"^source_url:", head, re.M):
            return "cloudflare-frontmatter"
        return "anthropic-yaml"
    return "none"


def detect_kind(text: str, name: str = "") -> tuple[str, str]:
    """(kind, grammar). Name first, then shape; a misnamed file is reported by P0."""
    n = name.lower()
    grammar = detect_grammar(text)
    lines = text.splitlines()
    units = sum(1 for ln in lines[:400] if UNIT_RE.match(ln))
    links = [m for m in (LINK_RE.match(ln) for ln in lines) if m]
    h1 = next((ln for ln in lines if ln.startswith("# ")), "")
    if n.startswith("llms-vocabulary") or h1.rstrip().lower().endswith("— vocabulary"):
        return "vocabulary", grammar
    if n.startswith("llms-facts") or (units >= 3 and h1.rstrip().endswith("facts")):
        return "facts", grammar
    if grammar != "none" and (
        len(split_llms_full(text)) >= 2 or n.startswith("llms-full") or n.startswith("llms-small")
    ):
        return ("small" if n.startswith("llms-small") else "full"), grammar
    if links:
        # a family links OTHER sites' indexes (absolute URLs); a split hub links
        # its own sections by relative path and is still an index
        idx_targets = sum(
            1 for m in links if m.group(2).rstrip("/").endswith("llms.txt") and "://" in m.group(2)
        )
        if idx_targets and idx_targets >= 0.6 * len(links):
            return "family", grammar
        return "index", grammar
    if h1 and n.startswith("llms"):
        return "index", grammar
    return "unknown", grammar


# ---------------------------------------------------------------------------
# index parsing (P1-P3)
# ---------------------------------------------------------------------------


def parse_index(text: str) -> dict:
    lines = text.splitlines()
    out = {
        "h1": [],
        "blockquote": [],
        "sections": [],
        "h3plus": [],
        "stray": [],
        "entries": [],
        "bare": [],
    }
    cur = None
    in_fence = False
    seen_h2 = False
    for i, ln in enumerate(lines, 1):
        if FENCE_RE.match(ln):
            in_fence = not in_fence
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
        if _sentences(bq) > 3:
            f.append(
                Finding(
                    "P1",
                    "I2",
                    "medium",
                    f"blockquote is {_sentences(bq)} sentences (max 3)",
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
                "high" if share < 0.9 else "medium",
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


def pass_links(
    px: dict, kind: str, text: str, check: bool = False, base_dir: Path | None = None
) -> list[Finding]:
    f = []
    if base_dir is not None:
        rel = [
            e
            for e in px["entries"]
            if "://" not in e["url"] and not e["url"].startswith(("/", "#"))
        ]
        missing = [e for e in rel if not (base_dir / e["url"].split("#")[0]).exists()]
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
    internal = bool(INTERNAL_MARK_RE.search(text[:4000]))
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
    seen: dict[str, int] = {}
    dups = 0
    for e in px["entries"]:
        u = e["url"].rstrip("/")
        if u in seen:
            dups += 1
        seen.setdefault(u, e["line"])
    if dups:
        f.append(Finding("P2", "N7", "low", f"{dups} duplicate link target(s) across sections"))
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


def _head(url: str) -> tuple[str, int, str]:
    import urllib.error
    import urllib.request

    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "llms-lint/1.0"})
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=LINK_TIMEOUT) as r:  # noqa: S310
                return url, r.status, r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            return url, e.code, ""
        except Exception:
            if attempt == 2:
                return url, 0, ""
    return url, 0, ""


def _check_links(entries: list[dict]) -> list[Finding]:
    if not entries:
        return []
    with ThreadPoolExecutor(max_workers=LINK_CONCURRENCY) as ex:
        res = list(ex.map(_head, [e["url"] for e in entries]))
    dead = [(e, s) for e, (_, s, _ct) in zip(entries, res, strict=False) if s == 0 or s >= 400]
    html = [
        e
        for e, (_, s, ct) in zip(entries, res, strict=False)
        if 200 <= s < 400 and "text/html" in ct and not e["url"].endswith(".md")
    ]
    f = []
    if dead:
        f.append(
            Finding(
                "P2",
                "N6",
                "high",
                f"{len(dead)} dead link(s): " + ", ".join(f"{e['url']} [{s}]" for e, s in dead[:8]),
                dead[0][0]["line"],
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
        f.append(
            Finding(
                "P3",
                "D1",
                "high" if share > 0.4 and len(missing) >= 3 else "medium",
                f"{len(missing)}/{len(es)} link(s) without a description",
                missing[0]["line"],
            )
        )
    band_out = [
        e
        for e in es
        if e["notes"] and not (DESC_WORDS[0] <= len(e["notes"].split()) <= DESC_WORDS[1])
    ]
    if es and len(band_out) / len(es) > 0.05:
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
    seen: dict[str, int] = {}
    dup = 0
    for e in es:
        k = e["notes"].strip().lower()
        if k and k in seen:
            dup += 1
        seen.setdefault(k, e["line"])
    if dup:
        f.append(Finding("P3", "D4", "medium", f"{dup} duplicate description(s)"))
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
            m = json.loads(man.read_text())
            files = m.get("files", m)
            rec = files.get(path.name, {}) if isinstance(files, dict) else {}
            b = rec.get("bytes")
            if b and abs(b - n) / max(b, 1) > 0.02:
                f.append(
                    Finding(
                        "P5",
                        "H8",
                        "medium",
                        f"manifest says {b:,} bytes, file is {n:,} (> 2% drift — regenerate)",
                    )
                )
        except Exception as e:  # unreadable manifest is itself the finding
            f.append(Finding("P5", "H8", "medium", f"manifest.json unreadable: {e}"))
    return f


# ---------------------------------------------------------------------------
# P6 full-file fidelity
# ---------------------------------------------------------------------------


def pass_full(text: str, grammar: str) -> list[Finding]:
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
    blocks = split_llms_full(text)
    if not blocks:
        return [
            Finding("P6", "C1", "high", f"grammar {grammar} detected but zero page blocks parsed")
        ]
    if not BANNER_RE.search(text[:2000]):
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
    residue = sum(1 for ln in text.splitlines() if any(r.search(ln) for r in RESIDUE_RES))
    unbalanced = 0
    untagged = 0
    fences = 0
    big = 0
    seen: dict[str, int] = {}
    dups = 0
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
        u = (b.get("url") or "").rstrip("/")
        if u in seen:
            dups += 1
        seen.setdefault(u, 1)
    if residue:
        f.append(
            Finding("P6", "C3", "medium", f"{residue} navigation/MDX residue line(s)", fixable=True)
        )
    if unbalanced:
        f.append(
            Finding("P6", "C4", "medium", f"{unbalanced} page block(s) with an unclosed code fence")
        )
    if fences and untagged / fences > 0.10:
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
    mirror is tens of MB, so re-parsing it per file made the gate O(n²)."""
    if not mirror or not mirror.exists():
        return {}
    return _mirror_headings_cached(str(mirror), mirror.stat().st_mtime_ns)


@functools.lru_cache(maxsize=8)
def _mirror_headings_cached(path: str, _mtime: int) -> dict[str, set[str]]:
    mirror = Path(path)
    try:
        from docset_indexer import parse_mirror
        from docset_refine import slug
    except Exception:
        return {}
    pages = parse_mirror(mirror.read_text(errors="replace")) or []
    out: dict[str, set[str]] = {}
    for p in pages:
        s = set()
        for ln in p.get("text", "").splitlines():
            m = H_RE.match(ln)
            if m:
                s.add("#" + slug(m.group(2)))
        out[p["url"].rstrip("/")] = s
    return out


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
        if len(body) > 400 or _sentences(body) > 2:
            long_u.append(i)
        if heads:
            base, _, anchor = src.partition("#")
            page = heads.get(base.rstrip("/"))
            if page is not None and anchor and ("#" + anchor) not in page:
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
    if long_u and len(long_u) / max(1, len(units)) > 0.10:
        f.append(
            Finding(
                "P7",
                "C6",
                "medium",
                f"{len(long_u)} unit(s) longer than 2 sentences / 400 chars",
                long_u[0],
            )
        )
    if unresolved:
        share = len(unresolved) / max(1, len(units))
        f.append(
            Finding(
                "P7",
                "R3",
                "high" if share > 0.2 else "medium",
                f"{len(unresolved)} anchor(s) do not resolve to a heading in the mirror",
                unresolved[0],
            )
        )
    idx = path.parent / "llms.txt"
    if idx.exists() and page_urls:
        px = parse_index(idx.read_text(errors="replace"))
        idx_urls = {re.sub(r"\.md$", "", e["url"]).rstrip("/") for e in px["entries"]}
        idx_urls |= {re.sub(r"\.html?\.md$", "", u) for u in idx_urls}
        gap = [u for u in idx_urls if u.startswith("http") and u not in page_urls]
        if idx_urls and len(gap) / len(idx_urls) > 0.05:
            f.append(
                Finding(
                    "P7",
                    "R7",
                    "medium",
                    f"{len(gap)}/{len(idx_urls)} indexed page(s) have no units in the facts file",
                )
            )
    if not heads:
        f.append(Finding("P7", "R3", "na", "anchor resolution N/A (no mirror; pass --mirror)"))
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
    seen: dict[str, int] = {}
    dupes: list[int] = []
    heads = _mirror_headings(mirror)
    for i, ln in enumerate(text.splitlines(), 1):
        if not ln.startswith("- **"):
            continue
        parsed = parse_vocab_line(ln)
        if parsed is None:
            no_src.append(i)
            continue
        term, definition, src = parsed
        terms.append(i)
        key = " ".join(term.casefold().split())
        if key in seen:
            dupes.append(i)
        else:
            seen[key] = i
        if not src:
            no_src.append(i)
        if len(definition) > VOCAB_DEF_MAX:
            long_d.append(i)
        if heads and src:
            base, _, anchor = src.partition("#")
            page = heads.get(base.rstrip("/"))
            if page is not None and anchor and ("#" + anchor) not in page:
                unresolved.append(i)
    if not terms and not no_src:
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
        f.append(Finding("P7", "R3", "na", "anchor resolution N/A (no mirror; pass --mirror)"))
    return f


# ---------------------------------------------------------------------------
# P9 trust
# ---------------------------------------------------------------------------


def pass_trust(text: str, kind: str, third_party: bool) -> list[Finding]:
    f = []
    head = text[:4000]
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
                fixable=True,
            )
        )
    in_fence = False
    pem_open = False
    for i, ln in enumerate(text.splitlines(), 1):
        if FENCE_RE.match(ln):
            in_fence = not in_fence
        if any(r.search(ln) for r in SECRET_RES):
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
                if _EXAMPLE_RE.search(_heading_above(text, i)):
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
        m = None if in_fence or ln.lstrip().startswith(("|", ">")) else _steer_hit(ln)
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


def _heading_above(text: str, line_no: int, window: int = 80) -> str:
    """Nearest markdown heading above `line_no` (1-based), within `window` lines."""
    lines = text.splitlines()
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


def _in_quotes(line: str, pos: int) -> bool:
    """True when `pos` sits inside an open \", ' or ` span on the line."""
    before = line[:pos]
    return any(before.count(q) % 2 == 1 for q in ('"', "`")) or before.count("'") % 2 == 1


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


def apply_fixes(text: str, kind: str, grammar: str) -> str:
    lines = text.split("\n")
    if kind in ("index", "family"):
        # bare URL -> link line
        for i, ln in enumerate(lines):
            m = BARE_URL_RE.match(ln)
            if m and not LINK_RE.match(ln):
                url = m.group(1)
                name = url.rstrip("/").rsplit("/", 1)[-1] or url
                lines[i] = f"- [{name}]({url})"
        # ## Optional last
        text = "\n".join(lines)
        parts = re.split(r"(?m)^(?=## )", text)
        head, secs = parts[0], parts[1:]
        opt = [s for s in secs if s.lower().startswith("## optional")]
        rest = [s for s in secs if not s.lower().startswith("## optional")]
        if opt:
            text = (
                head
                + "".join(s if s.endswith("\n\n") else s.rstrip("\n") + "\n\n" for s in rest)
                + opt[0]
            )
        return text.rstrip("\n") + "\n"
    if kind in ("full", "small"):
        kept = [ln for ln in lines if not any(r.search(ln) for r in RESIDUE_RES)]
        text = "\n".join(kept)
        if grammar == "mintlify" and not BANNER_RE.search(text[:2000]):
            text = (
                "<!-- llms-full grammar: mintlify — per page: '# Title' / 'Source: <url>' / "
                "blank / body -->\n\n" + text
            )
        return text.rstrip("\n") + "\n"
    return text


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
    raw = path.read_bytes()
    hyg, fixed_bytes = pass_hygiene(raw)
    text = fixed_bytes.decode("utf-8", errors="replace")
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
        return {"file": str(path), "kind": kind, "grammar": grammar, "findings": findings}
    if kind in ("index", "family"):
        px = parse_index(text)
        findings += pass_structure(px, kind)
        findings += pass_links(px, kind, text, check_links, path.parent)
        findings += pass_descriptions(px, kind)
    elif kind in ("full", "small"):
        findings += pass_full(text, grammar)
    elif kind == "facts":
        findings += pass_facts(text, path, mirror)
    elif kind == "vocabulary":
        findings += pass_vocabulary(text, mirror)
    findings += pass_size(path, kind, text)
    findings += pass_trust(text, kind, third_party)
    if fix:
        new = apply_fixes(text, kind, grammar)
        path.write_bytes(new.encode("utf-8"))
        fixed = [x for x in findings if x["fixable"]]
        for x in fixed:
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
    c.add_argument("--kind", choices=KINDS[:-1])
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
        kind, grammar = detect_kind(path.read_text(errors="replace"), path.name)
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
            files = sorted(path.glob("llms*.txt"), key=lambda q: (q.name != "llms.txt", q.name))
            files += sorted(path.rglob("*/llms.txt"))  # sections of a split index, any depth
        else:
            files = [path]
        for f_ in files:
            res = check(
                f_,
                a.kind,
                a.check_links,
                Path(a.mirror) if a.mirror else None,
                a.third_party,
                a.fix,
            )
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
