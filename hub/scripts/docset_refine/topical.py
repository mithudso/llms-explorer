"""topical — a topical llms file from a pool of facts, skeleton from the concept tree.

The by-source exports (`export_llms`) answer "what does this site say"; a topical
file answers "what is known about X, across sources". Same llms.txt grammar,
other axis: the H2 sections are the subject's child concepts in
`concept-tree/tree.json`, and every fact from every source is filed under one
of them (keyword first, embedding nearest-centroid second, `## Shared` last).

Pool records (`llms-deep-optimizer/references/facts-to-llms-howto.md` §0):
  {id, type, text, source, anchor, keywords[], origin, also[]}
read from  *.jsonl   docset_refine units (source_url -> source)
           llms-facts.txt lines  `- [type] text — url#anchor`
           *.md      /dr reference spokes: every sentence carrying a [^n]
                     footnote becomes a fact anchored to the footnote's URL
A record with no source is rejected, never guessed (P7 High).

Output `<out>/`:  llms.txt (index by concept), llms-facts.txt (facts by
section, same slugs as the index anchors), manifest.json. Hand edits go in
`manifest.json["overrides"]` (title, summary, section names) so regeneration
keeps them.
"""

from __future__ import annotations

import difflib
import json
import re
from collections import Counter, OrderedDict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from . import UNIT_TYPES, slug

CHARS_PER_TOKEN = 4
SHARED = "Shared"
OPTIONAL = "Optional"
MIN_FACTS = 3           # a section thinner than this is a research gap
MAX_LINKS = 6           # primary source links per section
MAX_DESC_WORDS = 25     # D3 band is 10–25 words
MAX_UNIT_CHARS = 400    # C6: a unit is ≤ 2 sentences / 400 chars
FILE_MATCH_RATIO = 0.8  # difflib ratio between a pool file stem and a section slug
TYPE_ORDER = ("definition", "concept", "statement", "parameter", "actionable", "snippet",
              "fact", "problem", "question", "change", "quote", "idea")
_STOP = {"the", "a", "an", "and", "or", "of", "for", "to", "in", "on", "with", "by", "is",
         "are", "as", "at", "from", "it", "its", "this", "that", "be", "v2", "vs"}
_FACT_LINE_RE = re.compile(
    r"^\s*-\s*\[(?P<type>[a-z]+)\]\s*(?P<text>.+?)\s+—\s+(?P<src>\S+?)(?:\s+·\s+(?P<tail>.*))?\s*$")
_FOOTNOTE_DEF_RE = re.compile(r"^\[\^(?P<n>[^\]]+)\]:\s*(?P<rest>.*https?://.*)$")
_URL_RE = re.compile(r"https?://[^\s)\]>,;\"']+")
_VERIFIED_RE = re.compile(r"verified[- ]as[- ]of:?\s*(\d{4}-\d{2}-\d{2})", re.I)
_FOOTNOTE_REF_RE = re.compile(r"\[\^([^\]]+)\]")
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z`\"'(\[])")
_TICK_RE = re.compile(r"`([^`]{2,60})`")
_WORD_RE = re.compile(r"[a-z0-9][a-z0-9.+_-]*")
_LIST_MARK_RE = re.compile(r"^(?:[-*+]\s+|\d{1,3}[.)]\s+)")
_CELL_SPLIT_RE = re.compile(r"(?<!\\)\|(?=(?:[^`]*`[^`]*`)*[^`]*$)")  # unescaped, outside backticks
_DEAD_CELL = {"", "-", "—", "–", "n/a", "na", "none", "?"}
# a parenthetical instruction to whoever reads the sentence ("(carry into every
# recommendation)") is a steering span once the sentence leaves its skill (P9/P4)
_HEAD_NUM_RE = r"^[0-9]+(?:[.][0-9]+)*[.)]?\s*"   # "3.1 " / "7) " spoke section numbers
_STEER_PAREN_RE = re.compile(
    r"\s*\((?:carry|remember|keep|always|never|do not|don't|make sure|be sure)\b[^)]*\)")


# --------------------------------------------------------------------------- #
# 1. pool
# --------------------------------------------------------------------------- #


_MD_NOISE_RE = re.compile(r"\*\*|__|^>\s*|^\*\s+|^[-•]\s+")


def _clean_md(text: str) -> str:
    """Prose markers that are formatting, not meaning: bold/underline pairs,
    a leading blockquote/bullet marker, doubled spaces. Backticks stay."""
    t = " ".join(text.split())
    t = _MD_NOISE_RE.sub("", t)
    return re.sub(r"\s+([,.;:])", r"\1", t).strip()


def _rec(seq: int, type_: str, text: str, source: str, anchor: str = "", keywords=None,
         origin: str = "pool", also=None, file: str = "", heading: str = "") -> dict:
    also = [u for u in dict.fromkeys(also or []) if u and u != source]
    return {"id": f"t{seq:06d}", "type": type_ if type_ in UNIT_TYPES else "statement",
            "text": _STEER_PAREN_RE.sub("", _clean_md(text)), "source": source,
            "anchor": anchor or "", "keywords": list(dict.fromkeys(keywords or [])),
            "origin": origin, "also": also, "file": file, "heading": heading}


def _split_source(src: str) -> tuple[str, str]:
    url, _, anchor = src.partition("#")
    return url, f"#{anchor}" if anchor else ""


def parse_units_jsonl(path: Path, seq: int) -> tuple[list[dict], list[dict]]:
    out, rejected = [], []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            u = json.loads(line)
        except json.JSONDecodeError:
            rejected.append({"file": path.name, "line": line[:120], "reason": "bad json"})
            continue
        src = u.get("source_url") or u.get("source") or ""
        if not src:
            rejected.append({"file": path.name, "line": line[:120], "reason": "unsourced"})
            continue
        kw = list(u.get("keywords") or [])
        code = u.get("code") or {}
        text = u.get("text") or ""
        if code.get("body"):
            text = f"{text} — `{code['body'].splitlines()[0][:100]}`"
        out.append(_rec(seq + len(out), u.get("type", "statement"), text, src,
                        u.get("anchor", ""), kw + _TICK_RE.findall(text), u.get("origin", "llm")))
    return out, rejected


def parse_facts_txt(path: Path, seq: int) -> tuple[list[dict], list[dict]]:
    out, rejected = [], []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.lstrip().startswith("- "):
            continue
        m = _FACT_LINE_RE.match(line)
        if not m:
            rejected.append({"file": path.name, "line": line[:120], "reason": "bad fact line"})
            continue
        url, anchor = _split_source(m.group("src"))
        text = m.group("text")
        also, kws, verified = [], [], ""
        for field in (m.group("tail") or "").split(" · "):
            k, _, v = field.partition(":")
            if k.strip() == "also":
                also = [x.strip() for x in v.split(",") if x.strip()]
            elif k.strip() == "keywords":
                kws = [x.strip() for x in v.split(",") if x.strip()]
            elif k.strip() == "verified-as-of":
                verified = v.strip()
        r = _rec(seq + len(out), m.group("type"), text, url, anchor,
                 kws + _TICK_RE.findall(text), "facts-file", also=also)
        r["verified"] = verified
        out.append(r)
    return out, rejected


def parse_reference_md(path: Path, seq: int) -> tuple[list[dict], list[dict]]:
    """A /dr reference spoke: `[^n]: url` definitions at the bottom; every
    sentence (or bullet) that cites [^n] becomes a fact anchored to that URL.
    Type: definition when the sentence reads "X is/are …" inside the first
    section that mentions it, actionable for imperative bullets, else
    statement. Fenced blocks and tables are skipped (they are not claims)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    # a footnote may cite several URLs ("[^7]: url1 and url2 — …"): all of them
    # are evidence; the first is the source, the rest ride as also:
    notes = {m.group("n"): _URL_RE.findall(m.group("rest"))
             for m in map(_FOOTNOTE_DEF_RE.match, text.splitlines()) if m}
    vm = _VERIFIED_RE.search(text[:4000])
    verified = vm.group(1) if vm else ""
    out, rejected, in_fence, heading = [], [], False, ""
    inherit: list[str] = []  # footnote urls of a "lead-in:" line, for the bullets under it
    header: list[str] = []   # current table's header cells, for column labels
    last_cells: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            inherit = []
            continue
        if in_fence or _FOOTNOTE_DEF_RE.match(line):
            continue
        if not line.strip():
            inherit, header, last_cells = [], [], []
            continue
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
            inherit, header, last_cells = [], [], []
            continue
        is_bullet = bool(_LIST_MARK_RE.match(line.lstrip()))
        if line.startswith("|"):
            # a table row is one claim: "cell1 — cell2 — cell3". Pipes inside
            # backticks or escaped (\|) are content, not column edges; header
            # and separator rows carry no footnote and fall out below.
            cells = [c.strip().replace("\\|", "|") for c in
                     _CELL_SPLIT_RE.split(line.strip().strip("|"))]
            if all(re.fullmatch(r":?-{2,}:?", c or "--") for c in cells):
                header = [_FOOTNOTE_REF_RE.sub("", c).strip() for c in last_cells]
                continue
            last_cells = cells
            plain = [_FOOTNOTE_REF_RE.sub("", c).strip() for c in cells]
            live = [(i, c) for i, c in enumerate(cells) if plain[i].lower() not in _DEAD_CELL]
            # footnotes on dead cells still cite the row
            tail = "".join(m for i, c in enumerate(cells) if plain[i].lower() in _DEAD_CELL
                           for m in re.findall(r"\[\^[^\]]+\]", c))
            if len(live) < 2:
                continue
            if header and len(header) == len(cells):
                # keep the column meaning: "subject — Col: value; Col: value"
                subj = live[0][1]
                rest = "; ".join(f"{header[i]}: {c}" for i, c in live[1:] if header[i])
                pieces = [(f"{subj} — {rest}" if rest else subj) + tail]
            else:
                pieces = [" — ".join(c for _, c in live) + tail]
        else:
            body = _LIST_MARK_RE.sub("", line.strip()).replace("\\|", "|")
            pieces = [body] if is_bullet else sentences(body)
        for sent in pieces:
            refs = _FOOTNOTE_REF_RE.findall(sent)
            clean = _FOOTNOTE_REF_RE.sub("", sent).strip()
            cited = [notes.get(r, []) for r in dict.fromkeys(refs)]
            cited = [c for c in cited if c]
            # the first footnote is the claim's source; when it lists several
            # URLs, the one whose host the sentence names wins. Later footnotes
            # are corroboration (also:), never the source.
            urls = [u for grp in ([_prefer_named_host(cited[0], sent)] + cited[1:] if cited
                                  else []) for u in grp]
            if refs and not urls:
                rejected.append({"file": path.name, "line": clean[:120],
                                 "reason": f"footnote {refs[0]} has no url"})
                continue
            if not urls and is_bullet and inherit:
                urls = list(inherit)          # a bullet under a cited lead-in
            if not urls:
                continue
            if clean.endswith(":") and not is_bullet:
                inherit = urls                # "Structure, in order:" — the list is the claim
                continue
            if len(clean) < 25:
                continue
            lw = clean.lower()
            if re.match(r"^(a |an |the )?([\w.`/-]+ ){1,3}(is|are|means) (a|an|the|not|one|any)\b",
                        lw) or ("what it is" in heading.lower() and not any(
                            u["heading"] == heading for u in out)):
                type_ = "definition"
            elif line.lstrip().startswith(("-", "*")) and re.match(
                    r"^(use|run|add|set|keep|put|serve|publish|link|split|treat|never|do not|"
                    r"don't|always|prefer|avoid|check|emit|include)\b", lw):
                type_ = "actionable"
            elif re.search(r"\b(bug|breaks?|fails?|cannot|can't|unstable|missing|dead)\b", lw):
                type_ = "problem"
            else:
                type_ = "statement"
            for part in _split_unit(clean):
                r = _rec(seq + len(out), type_, part, urls[0], "", _TICK_RE.findall(part),
                         "reference", also=urls[1:], file=path.stem, heading=heading)
                r["verified"] = verified
                out.append(r)
    return out, rejected


def _pack(parts: list[str], sep: str, limit: int) -> list[str]:
    """Greedy pack of clauses into chunks ≤ limit chars (a single oversize
    clause stays whole rather than being cut mid-token)."""
    out, cur = [], ""
    for part in parts:
        cand = f"{cur}{sep}{part}" if cur else part
        if cur and len(cand) > limit:
            out.append(cur)
            cur = part
        else:
            cur = cand
    if cur:
        out.append(cur)
    return out


def _prefer_named_host(urls: list[str], text: str) -> list[str]:
    """A composite footnote ("[^6]: a.com/x and b.com/y") cites several URLs;
    when the sentence itself names one of those hosts, that URL is the
    source and the others ride as also:."""
    if len(urls) < 2:
        return urls
    low = text.lower()
    for u in urls:
        host = _host(u)
        if host and host in low:
            return [u, *[x for x in urls if x != u]]
    return urls


def _clause_split(text: str, sep: str) -> list[str]:
    """Split on `sep` only outside backtick spans (`Link: <…>; rel=…` is one
    token, not two clauses)."""
    out, cur, ticks = [], "", 0
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "`":
            ticks ^= 1
        if ticks == 0 and text.startswith(sep, i):
            out.append(cur)
            cur = ""
            i += len(sep)
            continue
        cur += ch
        i += 1
    out.append(cur)
    return [x for x in out if x.strip()]


_PRONOUN_START_RE = re.compile(r"^(it|this|that|these|those|they|such|one|its|their)\b", re.I)


def sentences(text: str) -> list[str]:
    """Sentence split that never cuts inside an open quotation, backtick span
    or bracket, and keeps a sentence that opens with a pronoun ("It …",
    "This …") glued to the one that carries its antecedent."""
    out, cur, dq, tick, depth = [], "", 0, 0, 0
    parts = _SENT_SPLIT_RE.split(text)
    for part in parts:
        if cur and dq == 0 and tick == 0 and depth == 0 and not _PRONOUN_START_RE.match(part):
            out.append(cur.strip())
            cur = part
        else:
            cur = f"{cur} {part}" if cur else part
        dq = (dq + part.count('"')) % 2
        tick = (tick + part.count("`")) % 2
        depth = max(0, depth + part.count("(") - part.count(")"))
    if cur.strip():
        out.append(cur.strip())
    return out


def _split_unit(text: str) -> list[str]:
    """C6: a unit is ≤ 2 sentences and ≤ 400 chars. A longer claim is split
    at sentence boundaries, then a still-long sentence or table row at clause
    boundaries (`; ` then `, `); the row's subject ("X — ") is carried onto
    every piece so no piece loses its referent."""
    sents = sentences(text)
    if len(sents) <= 2 and len(text) <= MAX_UNIT_CHARS:
        chunks = [text]
    else:                                     # ≤ 2 sentences per unit, then ≤ 400 chars
        chunks = [y for i in range(0, len(sents), 2)
                  for y in _pack(sents[i:i + 2], " ", MAX_UNIT_CHARS)]
    out = []
    for ch in chunks:
        if len(ch) <= MAX_UNIT_CHARS:
            out.append(ch)
            continue
        subj = ""
        body = ch
        if " — " in ch[:80]:
            subj, body = ch.split(" — ", 1)
            subj += " — "
        if not subj:
            parts = _clause_split(ch, "; ")
            if len(parts) > 1 and all(len(x) >= 60 and x[0] in "`\"'([" + x[0].upper()
                                      for x in parts):
                out += _pack(parts, "; ", MAX_UNIT_CHARS)   # independent claims
            else:
                out.append(ch)      # one long claim: keep whole rather than fragment
            continue
        # semicolon clauses are independent claims; commas are not
        pieces = _pack(_clause_split(body, "; "), "; ", MAX_UNIT_CHARS - len(subj))
        out += [subj + x for x in pieces]
    return out


def load_pool(paths: list[Path]) -> tuple[list[dict], list[dict]]:
    pool, rejected = [], []
    for p in paths:
        p = Path(p)
        if not p.is_file():
            rejected.append({"file": str(p), "line": "", "reason": "missing file"})
            continue
        if p.suffix == ".jsonl":
            recs, rej = parse_units_jsonl(p, len(pool) + 1)
        elif p.name.startswith("llms-facts") or p.suffix == ".txt":
            recs, rej = parse_facts_txt(p, len(pool) + 1)
        else:
            recs, rej = parse_reference_md(p, len(pool) + 1)
        pool += recs
        rejected += rej
    return pool, rejected


# --------------------------------------------------------------------------- #
# 2. dedupe
# --------------------------------------------------------------------------- #


def _norm(text: str) -> str:
    return re.sub(r"[\s]+", " ", text.lower()).strip().rstrip(".")


def dedupe(pool: list[dict]) -> list[dict]:
    """Exact dedupe on normalised text; the loser's source rides along as
    `also` — corroboration is evidence, not noise."""
    seen: dict[str, dict] = {}
    for r in pool:
        k = _norm(r["text"])
        if k in seen:
            keep = seen[k]
            for src in [r["source"], *r.get("also", [])]:
                if src and src != keep["source"] and src not in keep["also"]:
                    keep["also"].append(src)
            for kw in r["keywords"]:
                if kw not in keep["keywords"]:
                    keep["keywords"].append(kw)
            continue
        seen[k] = dict(r, also=list(r.get("also", [])), keywords=list(r["keywords"]))
    return list(seen.values())


def near_dedupe(pool: list[dict], embed, threshold: float = 0.93) -> list[dict]:
    """Merge units that say the same thing in other words (cosine ≥ threshold
    on the pool embedding model): the earlier unit stays, the later one's
    source joins its `also:` — four sibling spokes restate the same facts."""
    if len(pool) < 2:
        return pool
    vecs = embed([r["text"] for r in pool])
    try:
        import numpy as np
        m = np.asarray(vecs, dtype="float32")
        m /= np.linalg.norm(m, axis=1, keepdims=True) + 1e-9
        sims = m @ m.T
        sim = lambda i, j: float(sims[i, j])  # noqa: E731
    except ImportError:
        sim = lambda i, j: _cosine(vecs[i], vecs[j])  # noqa: E731
    keep: list[dict] = []
    keep_idx: list[int] = []
    for i, r in enumerate(pool):
        dup = next((k for k in keep_idx if sim(i, k) >= threshold), None)
        if dup is None:
            keep.append(r)
            keep_idx.append(i)
            continue
        tgt = pool[dup]
        for src in [r["source"], *r.get("also", [])]:
            if src and src != tgt["source"] and src not in tgt["also"]:
                tgt["also"].append(src)
        for kw in r["keywords"]:
            if kw not in tgt["keywords"]:
                tgt["keywords"].append(kw)
    return keep


# --------------------------------------------------------------------------- #
# 3. skeleton + 4. assign
# --------------------------------------------------------------------------- #


def skeleton(tree, subject: str) -> list[dict]:
    """Sections = the subject node's children (researched or frontier), in
    tree order; a childless subject is its own single section."""
    node = tree.by_concept.get(subject)
    if node is None:
        raise SystemExit(f"no concept-tree node for {subject!r} — run concept-family-explorer "
                         "or add the node first")
    secs = []
    for child in node.get("childConcepts") or []:
        cn = tree.by_concept.get(child)
        secs.append({"name": child, "slug": (cn or {}).get("slug") or slug(child),
                     "aliases": list((cn or {}).get("aliases") or []),
                     "frontier": cn is None or tree.status(child) != "researched"})
    if not secs:
        secs.append({"name": subject, "slug": node.get("slug") or slug(subject),
                     "aliases": list(node.get("aliases") or []), "frontier": False})
    return secs


def _tokens(text: str) -> set[str]:
    return {w for w in _WORD_RE.findall(text.lower()) if w not in _STOP and len(w) > 1}


def _section_terms(sec: dict) -> set[str]:
    terms = _tokens(sec["name"])
    for a in sec.get("aliases") or []:
        terms |= _tokens(a)
    return terms


FILE_PRIOR = 1.0  # a spoke written FOR a concept outranks any keyword overlap


def _file_matches(sec: dict, file: str) -> bool:
    """The pool file's stem names the section (slug or alias) — a /dr
    reference spoke is written for exactly one concept."""
    if not file:
        return False
    f = slug(file)
    c = sec["slug"]
    if c and (c == f or f.endswith(c) or c.endswith(f)
              or difflib.SequenceMatcher(None, c, f).ratio() >= FILE_MATCH_RATIO):
        return True
    # an alias names the spoke only when it IS the spoke's stem — fuzzy
    # matching on aliases let "llms-full.txt" claim the "llms-txt" spoke
    return any(slug(a) == f for a in sec.get("aliases") or [])


def keyword_scores(rec: dict, sections: list[dict]) -> list[float]:
    """Per-section score: token overlap with the section name/aliases, plus a
    prior when the record's source file is that section's own spoke."""
    # the source heading is context ("2. The spec, v2" → alias "spec"), so it
    # counts with the text and keywords
    hay = _tokens(" ".join([rec["text"], *(rec.get("keywords") or []), rec.get("heading", "")]))
    out = []
    for sec in sections:
        terms = _section_terms(sec)
        score = len(hay & terms) / len(terms) if terms else 0.0
        if _file_matches(sec, rec.get("file", "")):
            score += FILE_PRIOR
        out.append(score)
    return out


def _cosine(a, b) -> float:
    num = sum(x * y for x, y in zip(a, b, strict=False))
    da = sum(x * x for x in a) ** 0.5
    db = sum(y * y for y in b) ** 0.5
    return num / (da * db) if da and db else 0.0


ASSIGN_STATS: dict[str, int] = {}   # how the last assign() decided each record


def assign(pool: list[dict], sections: list[dict], embed=None, min_margin: float = 0.15,
           embed_floor: float = 0.55) -> dict[str, list[dict]]:
    """section name -> records. Keyword first: the best section wins when it
    is clearly ahead (margin) and non-zero. Otherwise, with an `embed`
    function (texts -> vectors), nearest centroid — the centroid is the
    section name plus its keyword-assigned definitions — above a cosine
    floor. What is left goes to Shared."""
    buckets: dict[str, list[dict]] = OrderedDict((s["name"], []) for s in sections)
    buckets[SHARED] = []
    undecided = []
    stats = {"keyword": 0, "file": 0, "embed": 0, "shared": 0}
    for r in pool:
        sc = keyword_scores(r, sections)
        best = max(range(len(sc)), key=lambda i: sc[i]) if sc else 0
        second = sorted(sc, reverse=True)[1] if len(sc) > 1 else 0.0
        if sc and sc[best] > 0 and sc[best] - second >= min_margin:
            buckets[sections[best]["name"]].append(r)
            stats["file" if _file_matches(sections[best], r.get("file", "")) else "keyword"] += 1
        else:
            undecided.append(r)
    if embed is not None and undecided and sections:
        seeds = []
        for s in sections:
            defs = [x["text"] for x in buckets[s["name"]] if x["type"] in ("definition", "concept")]
            seeds.append(" ".join([s["name"], *s.get("aliases", []), *defs[:3]]))
        cents = embed(seeds)
        vecs = embed([r["text"] for r in undecided])
        for r, v in zip(undecided, vecs, strict=False):
            sims = [_cosine(v, c) for c in cents]
            i = max(range(len(sims)), key=lambda k: sims[k])
            if sims[i] >= embed_floor:
                buckets[sections[i]["name"]].append(r)
                stats["embed"] += 1
            else:
                buckets[SHARED].append(r)
                stats["shared"] += 1
    else:
        buckets[SHARED].extend(undecided)
        stats["shared"] += len(undecided)
    ASSIGN_STATS.clear()
    ASSIGN_STATS.update(stats)
    order = {t: i for i, t in enumerate(TYPE_ORDER)}
    for recs in buckets.values():
        recs.sort(key=lambda r: order.get(r["type"], len(order)))
    return buckets


# --------------------------------------------------------------------------- #
# 5. links + 6. write
# --------------------------------------------------------------------------- #


def _host(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def _desc(text: str, max_words: int = MAX_DESC_WORDS) -> str:
    """≤ 25 words, cut at the last clause boundary inside the budget (never a
    truncation ellipsis: D3 flags it, and it hides the payload)."""
    words = text.split()
    if len(words) <= max_words:
        return " ".join(words)
    head = " ".join(words[:max_words])
    end = max(head.rfind(". "), head.rfind("! "), head.rfind("? "))
    if end >= len(head) // 3:                  # a whole sentence fits: take it
        return head[:end + 1]
    cut = max(head.rfind(sep) for sep in ("; ", ", ", " — ", ": "))
    if cut >= len(head) // 2:
        head = head[:cut]
    for open_, close in (("(", ")"), ("[", "]")):
        while head.count(open_) > head.count(close):   # never leave a bracket open
            head = head[:head.rfind(open_)]
    if head.count("`") % 2:
        head = head[:head.rfind("`")]
    if head.count('"') % 2:
        head = head[:head.rfind('"')]
    return head.rstrip(",;:—- ")


def link_title(url: str) -> str:
    """A link title a reader can tell apart: host plus up to two path segments
    (`github.com/pawamoy/mkdocs-llmstxt`, `mintlify.com/docs/ai`), never a bare
    host when the URL has a path."""
    p = urlparse(url)
    segs = [x for x in p.path.split("/") if x and x not in ("index.html", "index.md")]
    host = _host(url)
    if host.startswith("github.com") or host.startswith("raw.githubusercontent.com"):
        segs = segs[:2]
    else:
        segs = segs[:2]
    return host + ("/" + "/".join(segs) if segs else "")


_VENDOR_RE = re.compile(r"\b([a-z][a-z0-9-]{2,})\.(?:com|org|dev|io|ai|net|site|cloud)\b")
_KNOWN_VENDORS: set[str] = set()   # vendor names seen as source hosts in the pool (run() fills)


def _vendor(url: str) -> str:
    h = _host(url)
    parts = h.split(".")
    return parts[-2] if len(parts) >= 2 else h


def vendors_in(pool: list[dict]) -> set[str]:
    """Second-level names of every source/also host: 'cloudflare', 'vercel'…
    A description that names one of these but links another is a D5 miss."""
    out = set()
    for r in pool:
        for u in [r["source"], *r.get("also", [])]:
            v = _vendor(u)
            if len(v) >= 4 and v not in ("github", "githubusercontent", "google", "www"):
                out.add(v)
    return out


def _names_other_host(text: str, host: str, vendors: set[str] | None = None) -> bool:
    """Does the text name a web host or known vendor other than `host`?"""
    low = text.lower()
    if any(h != host for h in _VENDOR_RE.findall(low)):
        return True
    return any(v != host and re.search(rf"\b{re.escape(v)}\b", low)
               for v in (vendors if vendors is not None else _KNOWN_VENDORS))


def link_targets(recs: list[dict]) -> list[dict]:
    """The section's primary source links. Diversified: one URL per source
    heading first (so a section that mixes adoption numbers with consumer
    behaviour surfaces both), then by fact count. Descriptions are extractive
    — the URL's first definition, else its first record — never invented."""
    by_url: dict[str, list[dict]] = OrderedDict()
    for r in recs:
        by_url.setdefault(r["source"], []).append(r)
    ranked = sorted(by_url.items(), key=lambda kv: -len(kv[1]))
    chosen, seen_heads = [], set()
    for url, rs in ranked:                      # first pass: one per heading
        head = rs[0].get("heading", "")
        if head not in seen_heads:
            seen_heads.add(head)
            chosen.append((url, rs))
        if len(chosen) >= MAX_LINKS:
            break
    for url, rs in ranked:                      # fill the rest by count
        if len(chosen) >= MAX_LINKS:
            break
        if all(u != url for u, _ in chosen):
            chosen.append((url, rs))
    out, titles = [], set()
    for url, rs in chosen:
        # D5: the description must be a claim the target page can carry — a
        # unit that names this host, else one that names no other host; a
        # source with only cross-vendor synthesis units gets no index line
        host = _vendor(url)
        own = [x for x in rs if re.search(rf"\b{re.escape(host)}\b", x["text"].lower())
               and not _names_other_host(x["text"], host)]
        neutral = [x for x in rs if not _names_other_host(x["text"], host)]
        cands = own or neutral
        if not cands:
            continue
        # D3: prefer a description-length unit (≥ 10 words); definitions first
        full = [x for x in cands if len(x["text"].split()) >= 10]
        first = (next((x for x in full if x["type"] in ("definition", "concept")), None)
                 or (full[0] if full else None)
                 or next((x for x in cands if x["type"] in ("definition", "concept")), cands[0]))
        toks = [k for k in first.get("keywords", []) if k.startswith("`") or " " not in k][:3]
        title = link_title(url)
        if title in titles:
            title = f"{title} ({len(out) + 1})"
        titles.add(title)
        out.append({"url": url, "host": title, "count": len(rs),
                    "description": _desc(first["text"]), "tokens": toks})
    return out


def _fact_block(recs: list[dict]) -> list[str]:
    """Unit lines grouped under `### <source heading>` when the records carry
    one — a second navigation level inside a section (the heading names the
    topic more precisely than the section when a spoke is broad)."""
    groups: dict[str, list[dict]] = OrderedDict()
    for r in recs:
        groups.setdefault(r.get("heading") or "", []).append(r)
    if len(groups) <= 1:
        return [_fact_line(r) for r in recs]
    out = []
    for head, rs in groups.items():
        if head:
            out += [f"### {re.sub(_HEAD_NUM_RE, '', head)}", ""]
        out += [_fact_line(r) for r in rs]
        out.append("")
    return out


def _fact_line(r: dict) -> str:
    where = f"{r['source']}{r.get('anchor', '')}"
    line = f"- [{r['type']}] {r['text']} — {where}"
    # field order matters to llms_lint.py's UNIT_RE, which only recognises a
    # tail that starts with keywords:/verified-as-of: — also: rides last
    kws = [k for k in r.get("keywords", []) if k and len(k) < 60][:6]
    if kws:
        line += " · keywords: " + ", ".join(kws)
    if r.get("verified"):
        line += f" · verified-as-of: {r['verified']}"
    if r.get("also"):
        line += " · also: " + ", ".join(r["also"])
    return line


def build_files(subject: str, summary: str, sections: list[dict], buckets: dict,
                base_url: str | None, generated: str, sources: int) -> tuple[str, str]:
    # relative by default: the twin sits beside the index wherever it is served
    # or copied; an absolute base_url is for publishing the index alone
    facts_url = f"{base_url}/llms-facts.txt" if base_url else "llms-facts.txt"
    n_facts = sum(len(v) for v in buckets.values())
    banner = (f"<!-- generated by docset_refine topical v1 · {n_facts} facts / {sources} sources"
              f" · {generated} -->")
    idx = [f"# {subject}", "", f"> {summary}", "", banner, ""]
    facts = [f"# {subject} — facts", "", f"> {summary} Every line ends in the URL it came from; "
             "`also:` lists sources that say the same thing.", "", banner, ""]
    thin, optional_secs = [], []
    for s in sections:
        recs = buckets.get(s["name"], [])
        if s["frontier"] or len(recs) < MIN_FACTS:
            optional_secs.append((s, recs))
            if not s["frontier"]:
                thin.append(s["name"])
            continue
        idx += [f"## {s['name']}", ""]
        n_src = len({r["source"] for r in recs})
        idx.append(f"- [Facts: {s['name']}]({facts_url}#{s['slug']}): {len(recs)} "
                   f"source-anchored facts from {n_src} sources")
        for t in link_targets(recs):
            n = t["count"]
            idx.append(f"- [{t['host']}]({t['url']}): {t['description']} "
                       f"({n} fact{'s' if n != 1 else ''})")
        idx.append("")
        facts += [f"## {s['name']}", f"<a id=\"{s['slug']}\"></a>", ""]
        facts += _fact_block(recs)
        facts.append("")
    shared = buckets.get(SHARED, [])
    if shared:
        idx += [f"## {SHARED}", "",
                f"- [Facts: shared]({facts_url}#shared): {len(shared)} cross-cutting facts that "
                "belong to no single section", ""]
        facts += [f"## {SHARED}", '<a id="shared"></a>', ""]
        facts += [_fact_line(r) for r in shared]
        facts.append("")
    if optional_secs:
        idx += [f"## {OPTIONAL}", ""]
        for s, recs in optional_secs:
            if s["frontier"]:
                idx.append(f"- {s['name']} — known, unresearched (frontier); "
                           f"{len(recs)} facts pooled so far")
            else:
                idx.append(f"- [Facts: {s['name']}]({facts_url}#{s['slug']}): thin — "
                           f"{len(recs)} facts, queued for research")
            if recs:
                facts += [f"## {s['name']}", f"<a id=\"{s['slug']}\"></a>", ""]
                facts += _fact_block(recs)
                facts.append("")
        idx.append("")
    return "\n".join(idx).rstrip() + "\n", "\n".join(facts).rstrip() + "\n"


def default_summary(subject: str, pool: list[dict], sections: list[dict], srcs: set,
                    node: dict) -> str:
    """I2: say what the SUBJECT is and who this index is for, then the counts.
    The definition is extractive — the pool's definition unit that names the
    subject best — never invented."""
    terms = _tokens(subject)
    best, best_score = None, 0.0
    for r in pool:
        if r["type"] not in ("definition", "concept"):
            continue
        score = len(_tokens(r["text"][:120]) & terms) / (len(terms) or 1)
        if score > best_score:
            best, best_score = r, score
    what = best["text"].split(". ")[0].rstrip(".") + "." if best and best_score >= 0.3 else ""
    who = (f"This index is for agents and people building, generating or consuming "
           f"{subject}: {len(pool)} source-anchored facts from {len(srcs)} sources, "
           f"filed under {len(sections)} concepts")
    skill = f"; skill {node['skillId']}" if node.get("skillId") else ""
    return f"{what} {who}{skill}.".strip()


def run(pool_paths: list[Path], subject: str, out_dir: Path, tree=None, embed=None,
        summary: str | None = None, base_url: str | None = None,
        register: bool = False, log=print) -> dict:
    import concept_tree as ct

    tree = tree or ct.ConceptTree.load()
    ct.ensure_slugs(tree.nodes)
    pool, rejected = load_pool([Path(p) for p in pool_paths])
    pool = dedupe(pool)
    if embed is not None:
        pool = near_dedupe(pool, embed)
    sections = skeleton(tree, subject)
    _KNOWN_VENDORS.clear()
    _KNOWN_VENDORS.update(vendors_in(pool))
    buckets = assign(pool, sections, embed=embed)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    man_path = out_dir / "manifest.json"
    overrides = {}
    if man_path.exists():
        try:
            overrides = json.loads(man_path.read_text()).get("overrides") or {}
        except (OSError, json.JSONDecodeError):
            overrides = {}
    subject_title = overrides.get("title") or subject
    node = tree.by_concept.get(subject) or {}
    srcs = {r["source"] for r in pool}
    order = overrides.get("section_order") or []
    if order:                                   # N3: hand-ordered by query frequency
        rank = {n: i for i, n in enumerate(order)}
        sections.sort(key=lambda s: rank.get(s["name"], len(rank)))
    summary = overrides.get("summary") or summary or default_summary(
        subject, pool, sections, srcs, node)
    generated = datetime.now().date().isoformat()   # local date, like the probes
    # the served slug IS the directory name (/t/<slug>/…); the node slug is the fallback
    served = out_dir.name[:-5] if out_dir.name.endswith(".llms") else (
        node.get("slug") or ct.slugify(subject))
    index_text, facts_text = build_files(subject_title, summary, sections, buckets, base_url,
                                         generated, len(srcs))
    (out_dir / "llms.txt").write_text(index_text, encoding="utf-8")
    (out_dir / "llms-facts.txt").write_text(facts_text, encoding="utf-8")
    # units.jsonl in docset_refine's schema: `docset_indexer index units.jsonl
    # --units --name topical__<slug>` builds the vector layer, keyword-index the
    # FTS5 layer — the two probes the how-to's §7 requires
    with (out_dir / "units.jsonl").open("w", encoding="utf-8") as fh:
        for sec in sections:
            for r in buckets.get(sec["name"], []):
                fh.write(json.dumps({
                    "id": r["id"], "type": r["type"], "text": r["text"],
                    "source_url": r["source"], "anchor": r.get("anchor", ""),
                    "page_class": "reference", "keywords": r["keywords"], "code": None,
                    "origin": "llm", "section": sec["slug"]}, ensure_ascii=False) + "\n")
        for r in buckets.get(SHARED, []):
            fh.write(json.dumps({
                "id": r["id"], "type": r["type"], "text": r["text"], "source_url": r["source"],
                "anchor": r.get("anchor", ""), "page_class": "reference",
                "keywords": r["keywords"], "code": None, "origin": "llm", "section": "shared"},
                ensure_ascii=False) + "\n")
    if rejected:
        (out_dir / "pool.rejected.jsonl").write_text(
            "\n".join(json.dumps(r) for r in rejected) + "\n", encoding="utf-8")
    manifest = {
        "kind": "topical", "subject": subject, "title": subject_title,
        "slug": served, "generated": generated,
        "pool": [str(p) for p in pool_paths], "units": len(pool), "sources": len(srcs),
        "rejected": len(rejected),
        "sections": {s["name"]: {"slug": s["slug"], "facts": len(buckets.get(s["name"], [])),
                                 "frontier": s["frontier"]} for s in sections},
        "shared": len(buckets.get(SHARED, [])),
        "assignment": dict(ASSIGN_STATS),
        "types": dict(Counter(r["type"] for r in pool)),
        "files": {n: {"bytes": len(t.encode()), "tokens": max(1, len(t) // CHARS_PER_TOKEN)}
                  for n, t in (("llms.txt", index_text), ("llms-facts.txt", facts_text))},
        "overrides": overrides,
    }
    man_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    if register and subject in tree.by_concept:
        tree.by_concept[subject]["llmsFile"] = f"/t/{manifest['slug']}/llms.txt"
        ct.save_nodes(tree.nodes)
    log(f"topical: {len(pool)} facts from {len(srcs)} sources → {out_dir} "
        f"({', '.join(f'{k}={v['facts']}' for k, v in manifest['sections'].items())}, "
        f"shared={manifest['shared']}, rejected={len(rejected)})")
    return manifest
