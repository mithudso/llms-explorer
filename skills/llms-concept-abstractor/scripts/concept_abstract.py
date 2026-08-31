#!/usr/bin/env python3
"""concept_abstract.py — the deterministic half of llms-concept-abstractor.

Abstracts ONE concept out of any set of resources (hub docset exports, refine
units, llms-facts files, llms-full mirrors, web-text-mirror .md files, plain
markdown/text such as a converted textbook) into a concept pack: a small-
footprint llms-family reference (index / full catalogue / small / facts /
vocabulary / graph). stdlib only. The model does the two steps a script cannot
(expand the lexicon; classify borderline units); everything mechanical — the
scan, scoring, dedup, rendering, budgeting, stats — runs here at zero tokens.

Subcommands
  harvest  --lexicon L.json --from PATH... --out DIR [--min-score 0.6]
           [--context 0|1] [--max-units N]
           scan every input for lexicon terms → DIR/pool.jsonl + harvest-report.json
           (per-term hits, zero-hit terms, co-occurrence candidates for the next
           lexicon round, heuristic facet/relation per unit)
  view     DIR [--facet F] [--min-score S] [--limit N] [--ids a,b]
           compact one-line-per-unit listing for the model's classification pass
  compile  --out DIR --concept NAME [--lexicon L.json] [--classified DIR/classified.jsonl]
           [--budget-tokens 8000] [--summary TEXT] [--rights extractive|quote]
           [--base-url URL]
           render llms.txt, llms-full.txt, llms-small.txt, llms-facts.txt,
           llms-vocabulary.txt, concept-graph.json, units.jsonl, manifest.json
  semantic --lexicon L.json --from PATH... --out DIR [--z 3.0] [--restart-ollama]
           embed the WHOLE scope (ollama, cached on disk), score every unit against the
           concept's query set + the keyword-harvest centroid, add what the lexicon
           missed → semantic.jsonl, flag keyword hits far from the concept (polysemy
           suspects), rank lexicon candidates by meaning, fold near-duplicates
  query    DIR "question" [--top 10]      semantic query over a compiled pack
  split    --out DIR --groups G.json [--budget-tokens 8000]
           family rule: slice a compiled pack into child packs by ordered term groups;
           parent llms.txt gains `## Child packs`, manifest gains `children`
  stats    DIR            counts, facets, sources, coverage, footprint
  probe    DIR --questions Q.jsonl    keyword coverage of a question bank against the pack

Lexicon (lexicon.json)
  {"concept": "Heart", "slug": "heart",
   "terms": [{"term": "heart", "relation": "self"},
             {"term": "cardiac", "relation": "synonym"},
             {"term": "myocardium", "relation": "part", "aka": ["myocardial"]},
             {"term": "lung", "relation": "related", "weight": 0.3}],
   "exclude": ["heart of the matter", "at heart"]}
  relation → default weight (see RELATION_WEIGHT). A unit's score is the sum of
  the weights of the DISTINCT lexicon terms it matches (+0.25 if a term is in
  its heading path / anchor). `--min-score` (0.6) means a unit matched only by a
  loosely related term is dropped unless a second term corroborates — that is
  the precision guard; recall comes from the lexicon, not from a lower floor.

Classified (classified.jsonl, written by the model, all fields optional but id)
  {"id": "u0042", "keep": true, "facet": "mechanism", "relation": "about",
   "conflict": "c1", "note": "…"}
  compile applies it over the heuristics; units absent from the file keep their
  heuristic facet/relation and keep=true.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, OrderedDict, defaultdict
from datetime import date
from pathlib import Path

VERSION = "1.2.0"
CHARS_PER_TOKEN = 4
CORE_WEIGHT = 0.7   # relations at/above this weight can qualify a unit on their own

RELATION_WEIGHT = {
    "self": 1.0, "synonym": 1.0, "abbreviation": 1.0, "variant": 1.0,
    "hyponym": 0.8, "part": 0.8, "instance": 0.7, "measure": 0.7, "problem": 0.7,
    "near-synonym": 0.6, "contrast": 0.6, "antonym": 0.6,
    "hypernym": 0.4, "whole": 0.4, "related": 0.4, "prerequisite": 0.4, "dependent": 0.4,
}
# how a matched relation maps to the unit's relation to the concept
RELATION_TO_UNIT = {
    "self": "about", "synonym": "about", "abbreviation": "about", "variant": "about",
    "hyponym": "subtype", "part": "component", "instance": "instance", "measure": "measure",
    "problem": "problem", "near-synonym": "neighbour", "contrast": "contrast",
    "antonym": "contrast", "hypernym": "context", "whole": "context", "related": "related",
    "prerequisite": "prerequisite", "dependent": "dependent",
}
RELATION_ORDER = ["about", "component", "subtype", "instance", "measure", "problem",
                  "neighbour", "contrast", "prerequisite", "dependent", "context", "related"]

# unit type → default facet; facet order is the catalogue's section order
FACET_BLURB = {
    "definition": "what it is", "structure": "what it is made of", "mechanism": "how it behaves",
    "parameters": "settings, defaults and limits", "how-to": "steps and recommendations",
    "examples": "code and worked examples", "measures": "numbers with units",
    "problems": "what goes wrong", "comparisons": "alternatives and trade-offs",
    "history": "versions and changes", "questions": "unanswered by the sources",
    "facts": "claims that fit no other facet", "quotes": "verbatim passages",
}
FACETS = OrderedDict([
    ("definition", "Definitions"),
    ("structure", "Structure and components"),
    ("mechanism", "How it works"),
    ("parameters", "Parameters and configuration"),
    ("how-to", "How-to and procedures"),
    ("examples", "Examples and snippets"),
    ("measures", "Measurements and reference values"),
    ("problems", "Problems, failure modes and limitations"),
    ("comparisons", "Comparisons and alternatives"),
    ("history", "Changes and history"),
    ("questions", "Open questions"),
    ("facts", "Facts and statements"),
    ("quotes", "Quotes"),
])
TYPE_TO_FACET = {
    "definition": "definition", "concept": "facts", "parameter": "parameters",
    "snippet": "examples", "example": "examples", "table": "measures",
    "actionable": "how-to", "step": "how-to", "problem": "problems", "question": "questions",
    "change": "history", "fact": "facts", "statement": "facts", "quote": "quotes",
    "idea": "facts", "passage": "facts", "comparison": "comparisons",
}
_DEF_CUE = re.compile(r"^(?:[^.]{0,80}?—\s*)?[^.]{0,60}?\b(?:is|are) (?:a|an|the|any|one|not)\b|"
                      r"\b(?:refers? to|is defined as|means|is called|also known as|is the process)\b", re.I)
_MECH_CUE = re.compile(r"\b(when|because|causes?|results? in|leads? to|triggers?|so that|"
                       r"in order to|works? by|mechanism|process|cycle|flow)\b", re.I)
_STRUCT_CUE = re.compile(r"\b(consists? of|composed of|made up of|contains?|comprises?|"
                         r"layers?|chambers?|components?|parts?|structure|anatomy|walls?)\b", re.I)
_PROB_CUE = re.compile(r"\b(fail|failure|error|limit|limitation|cannot|can't|risk|disease|"
                       r"disorder|pitfall|anti-?pattern|caveat|warning|deprecated|slow)\b", re.I)
_CMP_CUE = re.compile(r"\b(vs\.?|versus|unlike|compared (?:to|with)|rather than|instead of|"
                      r"differs? from|as opposed to|trade-?off)\b", re.I)
_MEAS_CUE = re.compile(r"\d+(?:\.\d+)?\s?(%|ms|s\b|mmHg|bpm|mL|L\b|kg|g\b|mg|MB|GB|KB|ops|"
                       r"qps|rps|x\b|×)", re.I)
_HOWTO_CUE = re.compile(r"^(?:to |set |use |run |configure |create |add |enable |avoid |"
                        r"prefer |ensure |check |install )", re.I)

_WORD_RE = re.compile(r"[a-z0-9][a-z0-9_./+-]{1,}")
_TICK_RE = re.compile(r"`([^`]{2,60})`")
_CAP_RE = re.compile(r"\b([A-Z][a-zA-Z0-9-]{2,}(?:\s+[A-Z][a-zA-Z0-9-]{2,}){0,2})\b")
_FACT_LINE_RE = re.compile(
    r"^\s*-\s*\[(?P<type>[a-z-]+)\]\s*(?P<text>.+?)\s+—\s+(?P<src>\S+?)(?:\s+·\s+(?P<tail>.*))?\s*$")
_URL_RE = re.compile(r"https?://[^\s)\]>,;\"']+")
_STOP = set("""a an the and or of to in on for with by as at from is are was were be been being
this that these those it its into than then there their they them we you your our can will
may might should would could not no yes if else when where which who whom what how why all
any each more most other some such only own same so too very just also about above after
again against between both but do does did doing down during few further has have having
here how off once out over under until up while both new use used using via per e.g i.e etc
section chapter figure table page see also note example""".split())
_PLURAL_RE = re.compile(r"(?:s|es|ies)$")
_MDLINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
_FRONTMATTER_RE = re.compile(r"^\s*(title|description|sidebar_label|sidebar_position|slug|hide_table_of_contents|layout|nav_order):", re.I)
_IMPORT_RE = re.compile(r"^\s*import\s+[\w{}, *]+\s+from\s+['\"]")


def prefilter(u: dict) -> str | None:
    """Reason to drop a unit before scoring, or None. Catches the non-content that
    every docset mirror carries and that a heading match would otherwise let
    through: navigation link lines, link lists, MDX imports, frontmatter keys,
    heading-only stubs. Learned from the eval-2 run (indexing across 10 mirrors)."""
    t = u["text"].strip()
    links = _MDLINK_RE.findall(t)
    if links:
        plain = _MDLINK_RE.sub("", t)
        plain_alpha = len(re.sub(r"[^A-Za-z]", "", plain))
        if plain_alpha < 25 and not re.search(r"[.!?]\s", plain):
            return "nav-link-line"
        if len(links) >= 4 and plain_alpha < 0.35 * max(1, len(re.sub(r"[^A-Za-z]", "", t))):
            return "link-list"
    if _IMPORT_RE.match(t) and u["type"] != "snippet":
        return "import-boilerplate"
    if _FRONTMATTER_RE.match(t):
        return "frontmatter"
    return None


# --------------------------------------------------------------------------- #
# lexicon
# --------------------------------------------------------------------------- #

def load_lexicon(path: Path) -> dict:
    lex = json.loads(Path(path).read_text(encoding="utf-8"))
    if not lex.get("concept"):
        sys.exit("lexicon: 'concept' is required")
    lex.setdefault("slug", slugify(lex["concept"]))
    terms = []
    seen = set()
    for t in lex.get("terms") or []:
        if isinstance(t, str):
            t = {"term": t}
        name = (t.get("term") or "").strip()
        if not name or name.lower() in seen:
            continue
        rel = t.get("relation") or ("self" if not terms else "related")
        if rel not in RELATION_WEIGHT:
            rel = "related"
        w = float(t.get("weight", RELATION_WEIGHT[rel]))
        surfaces = [name] + [a for a in (t.get("aka") or []) if a]
        terms.append({"term": name, "relation": rel, "weight": w, "surfaces": surfaces,
                      "note": t.get("note", "")})
        seen.add(name.lower())
    if not any(t["relation"] == "self" for t in terms):
        terms.insert(0, {"term": lex["concept"], "relation": "self", "weight": 1.0,
                         "surfaces": [lex["concept"]], "note": ""})
    lex["terms"] = terms
    lex["exclude"] = [e for e in (lex.get("exclude") or []) if e]
    return lex


def _surface_pattern(s: str) -> re.Pattern:
    """Word-boundary, case-insensitive, tolerant of a trailing plural and of
    hyphen/space variation inside multi-word terms."""
    parts = [re.escape(p) for p in re.split(r"[\s-]+", s.strip()) if p]
    body = r"[\s-]+".join(parts)
    if re.search(r"[a-z]$", s, re.I) and len(s) > 3:
        body += r"(?:s|es)?"
    return re.compile(r"(?<![\w-])" + body + r"(?![\w-])", re.I)


def compile_lexicon(lex: dict) -> tuple[list[tuple[dict, re.Pattern]], list[re.Pattern]]:
    pats = [(t, _surface_pattern(s)) for t in lex["terms"] for s in t["surfaces"]]
    excl = [_surface_pattern(e) for e in lex["exclude"]]
    return pats, excl


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "concept"


# --------------------------------------------------------------------------- #
# input readers — every reader yields units in one schema
# --------------------------------------------------------------------------- #

def _unit(id_: str, type_: str, text: str, source: str, anchor: str = "", heading: str = "",
          keywords=None, origin: str = "text", source_kind: str = "text", code=None,
          also=None) -> dict:
    return {"id": id_, "type": type_ or "statement", "text": text.strip(), "source_url": source.strip(),
            "anchor": (anchor or "").strip(), "heading_path": heading or "", "keywords": list(keywords or []),
            "origin": origin, "source_kind": source_kind, "code": code, "also": list(also or [])}


def read_units_jsonl(path: Path, prefix: str):
    n = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            u = json.loads(line)
        except json.JSONDecodeError:
            continue
        src = u.get("source_url") or u.get("source") or ""
        if not src:
            continue
        n += 1
        text = u.get("text") or ""
        code = u.get("code") or None
        if code and code.get("body") and code["body"] not in text:
            text = f"{text} — `{code['body'].splitlines()[0][:120]}`"
        yield _unit(f"{prefix}{n:06d}", u.get("type", "statement"), text, src,
                    u.get("anchor", ""), u.get("heading_path") or u.get("section") or "",
                    (u.get("keywords") or []) + _TICK_RE.findall(text), u.get("origin", "llm"),
                    "units", code)


def read_facts_txt(path: Path, prefix: str):
    n = 0
    heading = ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## "):
            heading = line[3:].strip()
            continue
        m = _FACT_LINE_RE.match(line)
        if not m:
            continue
        n += 1
        src = m.group("src")
        url, _, anchor = src.partition("#")
        also, kws = [], []
        for field in (m.group("tail") or "").split(" · "):
            k, _, v = field.partition(":")
            if k.strip() == "also":
                also = [x.strip() for x in v.split(",") if x.strip()]
            elif k.strip() == "keywords":
                kws = [x.strip() for x in v.split(",") if x.strip()]
        yield _unit(f"{prefix}{n:06d}", m.group("type"), m.group("text"), url,
                    f"#{anchor}" if anchor else "", heading, kws + _TICK_RE.findall(m.group("text")),
                    "facts-file", "facts", also=also)


_BANNER_RE = re.compile(r"^={20,}$")
_BANNER_URL_RE = re.compile(r"^URL:\s*(\S+)")
_FULL_SOURCE_RE = re.compile(r"^(?:Source|URL|Canonical):\s*(https?://\S+)\s*$")
_FULL_H1_URL_RE = re.compile(r"^#\s+.+?\((/[^)\s]*)\)\s*$")


def _paragraphs(block: list[str]):
    """Yield (heading_path, paragraph_text) from markdown lines; code fences are
    kept whole as one paragraph of type snippet."""
    heads: list[str] = []
    para: list[str] = []
    in_code = False
    for raw in block + [""]:
        line = raw.rstrip()
        if line.startswith("```"):
            in_code = not in_code
            para.append(line)
            if not in_code:
                yield " > ".join(heads), "\n".join(para), "snippet"
                para = []
            continue
        if in_code:
            para.append(line)
            continue
        hm = re.match(r"^(#{1,6})\s+(.*)", line)
        if hm:
            if para:
                yield " > ".join(heads), " ".join(para), "passage"
                para = []
            level = len(hm.group(1))
            heads = heads[:level - 1] + [hm.group(2).strip().strip("#").strip()]
            continue
        if not line.strip():
            if para:
                yield " > ".join(heads), " ".join(para), "passage"
                para = []
            continue
        para.append(line.strip())


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(`\"'])", text) if s.strip()]


def read_pages(path: Path, prefix: str, base_url: str | None = None):
    """web-text-mirror banner files, llms-full.txt (Source:/URL: lines or `# Title (/path)`
    H1s), or any markdown/text file (headings → anchors, file path → source)."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    pages: list[tuple[str, list[str]]] = []
    cur_url: str = f"file://{path.resolve()}"
    cur: list[str] = []
    i = 0
    banner = any(_BANNER_RE.match(l) for l in lines[:5])
    while i < len(lines):
        line = lines[i]
        if banner and _BANNER_RE.match(line) and i + 2 < len(lines) and _BANNER_URL_RE.match(lines[i + 1]):
            if cur:
                pages.append((cur_url, cur))
            cur_url, cur = _BANNER_URL_RE.match(lines[i + 1]).group(1), []
            i += 3
            continue
        sm = _FULL_SOURCE_RE.match(line)
        if sm and not banner:
            # a Source: line names the page the preceding H1 opened
            if cur and len(cur) <= 3 and cur[0].startswith("# "):
                cur_url = sm.group(1)
            else:
                if cur:
                    pages.append((cur_url, cur))
                cur_url, cur = sm.group(1), []
            i += 1
            continue
        hm = _FULL_H1_URL_RE.match(line) if not banner else None
        if hm and base_url:
            if cur:
                pages.append((cur_url, cur))
            cur_url, cur = base_url.rstrip("/") + hm.group(1), [line]
            i += 1
            continue
        cur.append(line)
        i += 1
    if cur:
        pages.append((cur_url, cur))
    n = 0
    kind = "mirror" if banner else ("llms-full" if len(pages) > 1 else "text")
    for url, block in pages:
        for heading, text, type_ in _paragraphs(block):
            text = re.sub(r"^\s*(?:---|\*\*\*)\s*$", "", text).strip()
            if len(text) < 25 or text.startswith("---") and text.endswith("---"):
                continue
            n += 1
            anchor = "#" + slugify(heading.split(" > ")[-1]) if heading else ""
            yield _unit(f"{prefix}{n:06d}", type_, text, url, anchor, heading,
                        _TICK_RE.findall(text), "text", kind)


def iter_inputs(paths: list[str], base_url: str | None = None):
    """Expand files/dirs/globs; pick a reader per file shape."""
    files: list[Path] = []
    for p in paths:
        pp = Path(p).expanduser()
        if any(ch in p for ch in "*?["):
            files += sorted(Path().glob(p)) if not pp.is_absolute() else sorted(pp.parent.glob(pp.name))
        elif pp.is_dir():
            if (pp / "units.jsonl").exists():
                files.append(pp / "units.jsonl")
            elif (pp / "all_units.jsonl").exists():
                files.append(pp / "all_units.jsonl")
            elif (pp / "llms-facts.txt").exists():
                files.append(pp / "llms-facts.txt")
            else:
                files += sorted(x for x in pp.rglob("*") if x.suffix in (".md", ".txt", ".jsonl"))
        elif pp.is_file():
            files.append(pp)
        else:
            print(f"warn: missing input {p}", file=sys.stderr)
    seen = set()
    for k, f in enumerate(files, 1):
        if f in seen:
            continue
        seen.add(f)
        prefix = f"s{k:02d}u"
        if f.suffix == ".jsonl":
            yield f, read_units_jsonl(f, prefix)
        elif f.name.startswith("llms-facts"):
            yield f, read_facts_txt(f, prefix)
        else:
            yield f, read_pages(f, prefix, base_url)


# --------------------------------------------------------------------------- #
# harvest
# --------------------------------------------------------------------------- #

def heuristic_facet(u: dict) -> str:
    t = u["type"]
    text = u["text"]
    # extractor `definition` units are "Heading — first paragraph": only a real
    # definitional sentence earns the Definitions facet; the rest run the cue chain
    if t in TYPE_TO_FACET and t not in ("passage", "fact", "statement", "concept", "idea", "definition"):
        return TYPE_TO_FACET[t]
    if t == "definition" and _DEF_CUE.search(text[:160]):
        return "definition"
    if _CMP_CUE.search(text):
        return "comparisons"
    if _PROB_CUE.search(text):
        return "problems"
    if _HOWTO_CUE.match(text):
        return "how-to"
    if _STRUCT_CUE.search(text):
        return "structure"
    if _MEAS_CUE.search(text):
        return "measures"
    if _MECH_CUE.search(text):
        return "mechanism"
    if _DEF_CUE.search(text[:120]):
        return "definition"
    return "facts" if t == "definition" else TYPE_TO_FACET.get(t, "facts")


def harvest(args) -> None:
    lex = load_lexicon(args.lexicon)
    pats, excl = compile_lexicon(lex)
    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    pool: list[dict] = []
    term_hits: Counter = Counter()
    term_sources: dict[str, set] = defaultdict(set)
    src_hits: Counter = Counter()
    scanned = 0
    files_seen = []
    cooc: Counter = Counter()
    baseline: Counter = Counter()
    prefiltered: Counter = Counter()
    prev: dict | None = None
    pending_next: list[dict] = []
    for f, units in iter_inputs(args.__dict__["from"], args.base_url):
        files_seen.append(str(f))
        for u in units:
            scanned += 1
            text = u["text"]
            hay = text + " " + u["heading_path"] + " " + u["anchor"]
            if args.context and pending_next:
                for pu in pending_next:
                    pu["context_after"] = text[:400]
                pending_next = []
            for w in set(_WORD_RE.findall(text.lower())):
                if w not in _STOP:
                    baseline[w] += 1
            if any(e.search(hay) for e in excl):
                prev = u
                continue
            why = prefilter(u)
            if why:
                prefiltered[why] += 1
                prev = u
                continue
            matched: dict[str, dict] = {}
            in_heading = False
            in_text = False
            for t, pat in pats:
                if t["term"] in matched:
                    continue
                if pat.search(text):
                    matched[t["term"]] = t
                    in_text = True
                elif pat.search(u["heading_path"] + " " + u["anchor"]):
                    matched[t["term"]] = t
                    in_heading = True
            if not matched:
                prev = u
                continue
            # a short unit that names no term itself and rode in on its heading is a
            # fragment of the page, not a statement about the concept
            if not in_text and len(text) < args.heading_only_min_chars:
                prefiltered["heading-only-short"] += 1
                prev = u
                continue
            score = sum(t["weight"] for t in matched.values()) + (0.25 if in_heading else 0)
            score = round(score, 2)
            has_core = any(t["weight"] >= CORE_WEIGHT for t in matched.values())
            # precision guard: a unit that only mentions a contrast/related/broader term
            # is about THAT term, not ours — unless two such terms corroborate each other
            if score < args.min_score or (args.require_core and not has_core and len(matched) < 2):
                prev = u
                continue
            rels = sorted({RELATION_TO_UNIT[t["relation"]] for t in matched.values()},
                          key=RELATION_ORDER.index)
            rec = dict(u, matched=sorted(matched), relations=rels, relation=rels[0],
                       score=score, facet=heuristic_facet(u), keep=True)
            if args.context:
                rec["context_before"] = (prev or {}).get("text", "")[:400]
                pending_next.append(rec)
            pool.append(rec)
            for name in matched:
                term_hits[name] += 1
                term_sources[name].add(_host(u["source_url"]))
            src_hits[_host(u["source_url"])] += 1
            for w in set(_WORD_RE.findall(text.lower())):
                if w not in _STOP and len(w) > 3:
                    cooc[w] += 1
            for tk in _TICK_RE.findall(text):
                cooc[tk.strip()] += 1
            for cap in _CAP_RE.findall(text):
                if cap.lower() not in _STOP:
                    cooc[cap] += 1
            prev = u
    pool = dedupe(pool)
    if args.max_units and len(pool) > args.max_units:
        pool.sort(key=lambda r: -r["score"])
        pool = pool[:args.max_units]
    with (out / "pool.jsonl").open("w", encoding="utf-8") as fh:
        for r in pool:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    known = {s.lower() for t in lex["terms"] for s in t["surfaces"]}
    # co-occurrence lift: tokens far more frequent inside matched units than in the corpus
    n_pool = max(1, len(pool))
    n_base = max(1, scanned)
    cands = []
    for w, c in cooc.items():
        if c < 3 or w.lower() in known or w.lower() in _STOP:
            continue
        b = baseline.get(w.lower(), c)
        lift = (c / n_pool) / max(b / n_base, 1e-9)
        if lift >= 2.0:
            cands.append({"token": w, "in_pool": c, "in_corpus": b, "lift": round(lift, 1)})
    cands.sort(key=lambda x: (-x["lift"] * min(x["in_pool"], 20), -x["in_pool"]))
    zero = [t["term"] for t in lex["terms"] if term_hits[t["term"]] == 0]
    report = {
        "concept": lex["concept"], "slug": lex["slug"], "version": VERSION,
        "generated": date.today().isoformat(), "inputs": files_seen, "scanned_units": scanned,
        "kept_units": len(pool), "min_score": args.min_score,
        "prefiltered": dict(prefiltered),
        "terms": [{"term": t["term"], "relation": t["relation"], "weight": t["weight"],
                   "hits": term_hits[t["term"]], "sources": len(term_sources[t["term"]])}
                  for t in lex["terms"]],
        "zero_hit_terms": zero,
        "sources": dict(src_hits.most_common()),
        "facets": dict(Counter(r["facet"] for r in pool).most_common()),
        "relations": dict(Counter(r["relation"] for r in pool).most_common()),
        "candidates": cands[:60],
    }
    (out / "harvest-report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    print(f"harvest: {len(pool)} units kept of {scanned} scanned from {len(files_seen)} files → "
          f"{out / 'pool.jsonl'}; {len(zero)} zero-hit terms; {len(cands)} lexicon candidates "
          f"(see harvest-report.json)")


def _host(url: str) -> str:
    m = re.match(r"https?://([^/]+)", url)
    if m:
        return m.group(1)
    if url.startswith("file://"):
        return Path(url[7:]).name
    return url[:40]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip().rstrip(".")


def dedupe(pool: list[dict]) -> list[dict]:
    """Exact dedupe on normalised text; losers' sources ride along as `also` —
    'three sources say this' is evidence the catalogue must keep."""
    seen: dict[str, dict] = {}
    for r in pool:
        k = _norm(r["text"])
        if k in seen:
            keep = seen[k]
            for s in [r["source_url"], *r.get("also", [])]:
                if s and s != keep["source_url"] and s not in keep["also"]:
                    keep["also"].append(s)
            keep["score"] = max(keep["score"], r["score"])
            for t in r["matched"]:
                if t not in keep["matched"]:
                    keep["matched"].append(t)
            continue
        seen[k] = dict(r, also=list(r.get("also", [])), matched=list(r["matched"]))
    return list(seen.values())


# --------------------------------------------------------------------------- #
# view (for the model's classification pass)
# --------------------------------------------------------------------------- #

def load_pool(d: Path) -> list[dict]:
    """pool.jsonl (keyword pass) ∪ semantic.jsonl (semantic pass), text-deduped."""
    p = d / "pool.jsonl"
    if not p.exists():
        sys.exit(f"no pool.jsonl in {d} — run harvest first")
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    sp = d / "semantic.jsonl"
    if sp.exists():
        seen = {_norm(r["text"]) for r in rows}
        for l in sp.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                if _norm(r["text"]) not in seen:
                    rows.append(r)
                    seen.add(_norm(r["text"]))
    return rows


def view(args) -> None:
    d = Path(args.dir).expanduser()
    pool = load_pool(d)
    ids = set(args.ids.split(",")) if args.ids else None
    n = 0
    for r in sorted(pool, key=lambda r: (FACETS_INDEX.get(r["facet"], 99), -r["score"])):
        if ids and r["id"] not in ids:
            continue
        if args.facet and r["facet"] != args.facet:
            continue
        if r["score"] < args.min_score:
            continue
        n += 1
        if args.limit and n > args.limit:
            break
        text = re.sub(r"\s+", " ", r["text"])[:args.width]
        sem = r.get("semantic_z")
        terms = ",".join(r["matched"][:3]) if r.get("matched") else ("~sem" if r.get("pass") == "semantic" else "")
        print(f"{r['id']}|{r['facet']}|{r['relation']}|{r['score']}|{sem if sem is not None else '-'}"
              f"|{terms}|{_host(r['source_url'])}|{text}")


FACETS_INDEX = {k: i for i, k in enumerate(FACETS)}


# --------------------------------------------------------------------------- #
# compile
# --------------------------------------------------------------------------- #

def _apply_classified(pool: list[dict], path: Path | None) -> tuple[list[dict], dict]:
    conflicts: dict[str, list[dict]] = defaultdict(list)
    if not path or not Path(path).exists():
        return [r for r in pool if r.get("keep", True)], {}
    by_id = {r["id"]: r for r in pool}
    dropped = 0
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            c = json.loads(line)
        except json.JSONDecodeError:
            continue
        r = by_id.get(c.get("id"))
        if not r:
            continue
        if c.get("facet") in FACETS:
            r["facet"] = c["facet"]
        if c.get("relation") in RELATION_ORDER:
            r["relation"] = c["relation"]
        if c.get("text_fix"):
            r["text"] = c["text_fix"]          # a trimmed quote, never a rewritten claim
        if c.get("note"):
            r["note"] = c["note"]
        if c.get("conflict"):
            r["conflict"] = c["conflict"]
            conflicts[c["conflict"]].append(r)
        if c.get("keep") is False:
            r["keep"] = False
            dropped += 1
    kept = [r for r in pool if r.get("keep", True)]
    return kept, conflicts


def _src(r: dict) -> str:
    return r["source_url"] + (r["anchor"] if r["anchor"] and not r["source_url"].endswith(r["anchor"]) else "")


def _line(r: dict, with_terms: bool = True) -> str:
    text = re.sub(r"\s+", " ", r["text"]).strip()
    if r["type"] == "snippet" and "\n" in r["text"]:
        text = r["text"].splitlines()[0][:160] + " …"
    line = f"- [{r['type']}] {text} — {_src(r)}"
    tail = []
    # any tail must open with `keywords:` — that is the facts-file grammar llms_lint checks
    if with_terms and r.get("matched"):
        tail.append(f"keywords: {', '.join(r['matched'][:4])}")
    elif r.get("also") or r.get("note"):
        tail.append("keywords: " + ", ".join((r.get("matched") or ["concept"])[:2]))
    if r.get("also"):
        tail.append(f"also: {', '.join(r['also'][:4])}")
    if r.get("note"):
        tail.append(f"note: {r['note']}")
    if tail:
        line += " · " + " · ".join(tail)
    return line.rstrip()


def _tokens_of(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)


def _definition_for(term: dict, pool: list[dict]) -> dict | None:
    """Best definitional unit for a term: prefers a page whose URL names the
    term, text that opens with the term, a real definitional sentence, then
    harvest score. Returns None when nothing in scope defines it."""
    pat = _surface_pattern(term["term"])
    tslug = slugify(term["term"])
    best, best_rank = None, None
    for r in pool:
        head = r["text"][:160]
        if not pat.search(head):
            continue
        defn = r["facet"] == "definition" or bool(_DEF_CUE.search(head))
        if not defn:
            continue
        rank = ((2 if tslug and tslug in r["source_url"].lower() else 0)
                + (1 if pat.match(re.sub(r"^\W+", "", r["text"])) else 0)
                + (1 if r["type"] == "definition" else 0)
                + min(r["score"], 3) / 10)
        if best is None or rank > best_rank:
            best, best_rank = r, rank
    return best


def compile_pack(args) -> None:
    out = Path(args.out).expanduser()
    pool = load_pool(out)
    lex = load_lexicon(args.lexicon) if args.lexicon else {"concept": args.concept,
                                                            "slug": slugify(args.concept),
                                                            "terms": [], "exclude": []}
    concept = args.concept or lex["concept"]
    slug = lex.get("slug") or slugify(concept)
    kept, conflicts = _apply_classified(pool, Path(args.classified) if args.classified else None)
    kept.sort(key=lambda r: (FACETS_INDEX.get(r["facet"], 99),
                             -(r["score"] + 0.5 * float(r.get("semantic_score") or 0))))
    by_facet: dict[str, list[dict]] = defaultdict(list)
    for r in kept:
        by_facet[r["facet"]].append(r)
    sources = Counter(_host(r["source_url"]) for r in kept)
    for r in kept:
        for a in r.get("also", []):
            sources[_host(a)] += 0
    hosts = sorted(sources, key=lambda h: -sources[h])
    generated = date.today().isoformat()
    rights = args.rights
    base = (args.base_url or "").rstrip("/")

    def link(name: str) -> str:
        return f"{base}/{name}" if base else name

    # --- definition / summary
    self_terms = [t for t in lex["terms"] if t["relation"] in ("self", "synonym", "abbreviation")]
    top_def = None
    for t in self_terms or [{"term": concept, "relation": "self", "weight": 1, "surfaces": [concept]}]:
        top_def = _definition_for(t, kept)
        if top_def:
            break
    if args.summary:
        summary = args.summary
    elif top_def:
        summary = re.sub(r"\s+", " ", top_def["text"])[:400] + f" (from {_host(top_def['source_url'])})"
    else:
        summary = (f"Everything the scanned sources say about {concept}: {len(kept)} source-anchored "
                   f"units across {len(hosts)} sources, grouped by facet.")

    # --- graph
    term_hits: Counter = Counter()
    term_srcs: dict[str, set] = defaultdict(set)
    for r in kept:
        for t in r["matched"]:
            term_hits[t] += 1
            term_srcs[t].add(_host(r["source_url"]))
    graph_nodes = []
    for t in lex["terms"]:
        graph_nodes.append({"term": t["term"], "relation": t["relation"], "weight": t["weight"],
                            "hits": term_hits[t["term"]], "sources": sorted(term_srcs[t["term"]]),
                            "note": t.get("note", "")})
    graph = {"concept": concept, "slug": slug, "generated": generated, "nodes": graph_nodes,
             "edges": [{"from": slug, "to": n["term"], "relation": n["relation"], "hits": n["hits"]}
                       for n in graph_nodes if n["relation"] != "self"]}

    # --- llms-full.txt (the catalogue)
    banner = (f"<!-- generated by llms-concept-abstractor v{VERSION} · generated {generated} · "
              f"{len(kept)} units · {len(hosts)} sources · rights: {rights} -->")
    full = [f"# {concept} — concept pack", "", f"> {summary}", "", banner, ""]
    if lex["terms"]:
        full += ["## Vocabulary", "",
                 "Terms this pack was harvested with, grouped by their relation to the concept; "
                 "counts are units matched / sources. Zero-hit terms are listed under Coverage. "
                 "On every unit line, `keywords:` names the terms that matched.", ""]
        by_rel: dict[str, list[dict]] = defaultdict(list)
        for n in graph_nodes:
            if n["hits"]:
                by_rel[n["relation"]].append(n)
        for rel in RELATION_WEIGHT:
            if by_rel.get(rel):
                full.append(f"- **{rel}**: " + ", ".join(
                    f"{n['term']} ({n['hits']}/{len(n['sources'])})" for n in by_rel[rel]))
        full.append("")
    for facet, title in FACETS.items():
        rows = by_facet.get(facet)
        if not rows:
            continue
        full += [f"## {title}", ""]
        if rights == "extractive":
            rows = [dict(r, text=r["text"][:600]) for r in rows]
        full += [_line(r) for r in rows]
        full.append("")
    if conflicts:
        full += ["## Disagreements", "",
                 "Units whose sources make incompatible claims. Kept side by side — never merged.", ""]
        for cid, rows in conflicts.items():
            full.append(f"### {cid}")
            full += [_line(r) for r in rows]
            full.append("")
    full += ["## Related concepts", ""]
    for n in sorted(graph_nodes, key=lambda n: (RELATION_ORDER.index(RELATION_TO_UNIT[n["relation"]]), -n["hits"])):
        if n["relation"] == "self":
            continue
        full.append(f"- {n['term']} — {n['relation']}" + (f" · {n['hits']} units" if n["hits"] else " · no units in scope")
                    + (f" · {n['note']}" if n.get("note") else ""))
    full += ["", "## Sources", ""]
    full += [f"- {h} — {sources[h]} units" for h in hosts]
    zero = [n["term"] for n in graph_nodes if not n["hits"]]
    full += ["", "## Coverage", "",
             f"- units kept: {len(kept)} · facets: {len([f for f in FACETS if by_facet.get(f)])} · sources: {len(hosts)}",
             f"- zero-hit terms: {', '.join(zero) if zero else 'none'}",
             f"- rights: {rights} — " + ("units and short extracts only; page bodies are not reproduced"
                                          if rights == "extractive" else "longer passages kept; do not publish third-party text"),
             ""]
    full_text = "\n".join(full).rstrip() + "\n"

    # --- llms-small.txt (budgeted)
    budget = args.budget_tokens * CHARS_PER_TOKEN
    small = [f"# {concept} — concept pack (small)", "", f"> {summary}", "",
             f"<!-- generated by llms-concept-abstractor v{VERSION} · generated {generated} · budgeted to "
             f"≈{args.budget_tokens} tokens; the full catalogue is {link('llms-full.txt')} -->", ""]
    used = sum(len(l) + 1 for l in small)
    queues = {f: list(by_facet[f]) for f in FACETS if by_facet.get(f)}
    picked: dict[str, list[dict]] = defaultdict(list)
    # definitions first, then round-robin by facet so every facet is represented
    for r in queues.get("definition", [])[:3]:
        picked["definition"].append(r)
        used += len(_line(r, False)) + 1
        queues["definition"].remove(r)
    exhausted = False
    while not exhausted:
        exhausted = True
        for f, q in queues.items():
            if not q:
                continue
            r = q.pop(0)
            ln = _line(r, False)
            if used + len(ln) + 1 > budget:
                q.insert(0, r)
                continue
            picked[f].append(r)
            used += len(ln) + 1
            exhausted = False
        if used >= budget:
            break
    for f, title in FACETS.items():
        if not picked.get(f):
            continue
        small += [f"## {title}", ""]
        small += [_line(r, False) for r in picked[f]]
        more = len(by_facet[f]) - len(picked[f])
        if more > 0:      # a prose pointer, not a unit line — facts linting counts only `- [type]` rows
            small.append(f"_{more} more {title.lower()} units in {link('llms-full.txt')}#{slugify(title)}_")
        small.append("")
    small_text = "\n".join(small).rstrip() + "\n"

    # --- llms-facts.txt (topical-compatible grammar)
    facts = [f"# {concept} — facts", "",
             f"> Source-anchored units about {concept}: {len(kept)} across {len(hosts)} sources. "
             f"Each line ends in the URL and anchor it came from; `keywords:` names the lexicon "
             f"terms that matched.", "", banner, ""]
    for facet, title in FACETS.items():
        rows = by_facet.get(facet)
        if not rows:
            continue
        facts += [f"## {title}", ""]
        for r in rows:
            text = re.sub(r"\s+", " ", r["text"]).strip()
            if r["type"] == "snippet" and "\n" in r["text"]:
                text = r["text"].splitlines()[0][:160]
            ln = f"- [{r['type']}] {text} — {_src(r)}"
            # tail order matters: llms_lint's fact-line grammar wants `keywords:` (or
            # `verified-as-of:`) first; `also:` rides after it
            kws = list(dict.fromkeys(r["matched"] + r.get("keywords", [])))[:6] or [slug]
            tail = ["keywords: " + ", ".join(kws)]
            if r.get("also"):
                tail.append("also: " + ", ".join(r["also"][:4]))
            ln += " · " + " · ".join(tail)
            facts.append(ln)
        facts.append("")
    facts_text = "\n".join(facts).rstrip() + "\n"

    # --- llms-vocabulary.txt
    vocab = [f"# {concept} — vocabulary", "",
             f"> Terms of this concept, one per line: canonical name, relation to {concept}, "
             f"definition where a source gives one, and the words people use instead (`aka:`). "
             f"Read before the index when a term is unfamiliar.", "", banner, "", "## Terms", ""]
    undefined = []
    for t in lex["terms"]:
        d = _definition_for(t, kept)
        line = f"- **{t['term']}** · {t['relation']}"
        aka = [s for s in t["surfaces"][1:]]
        if d:
            line += " — " + re.sub(r"\s+", " ", d["text"])[:300]
        if aka:
            line += " · aka: " + ", ".join(aka)
        if t.get("note"):
            line += " · " + t["note"]
        if d:
            line += f" — {_src(d)}"
        else:
            undefined.append(t["term"])
        vocab.append(line)
    if undefined:
        vocab += ["", "## Named, not yet defined", "",
                  "Lexicon terms no in-scope unit defines — research gaps or terms to drop.", ""]
        vocab += [f"- {u}" for u in undefined]
    vocab_text = "\n".join(vocab).rstrip() + "\n"

    # --- units.jsonl (indexable)
    units_lines = []
    for r in kept:
        units_lines.append(json.dumps({
            "id": r["id"], "type": r["type"], "text": r["text"], "source_url": r["source_url"],
            "anchor": r["anchor"], "page_class": "reference",
            "keywords": list(dict.fromkeys(r["matched"] + r.get("keywords", [])))[:10],
            "code": r.get("code"), "origin": r.get("origin", "text"), "section": r["facet"],
            "relation": r["relation"], "score": r["score"], "also": r.get("also", []),
            "semantic_score": r.get("semantic_score"), "pass": r.get("pass", "keyword")},
            ensure_ascii=False))
    units_text = "\n".join(units_lines) + ("\n" if units_lines else "")

    files = OrderedDict()
    # --- llms.txt (index) — written last so it can carry the others' token counts
    def tok(t): return _tokens_of(t)
    index = [f"# {concept} — concept pack", "", f"> {summary}", "", banner, "",
             "## Read first", "",
             f"- [Small catalogue]({link('llms-small.txt')}): budgeted digest, every facet represented — ≈{tok(small_text)} tokens",
             f"- [Full catalogue]({link('llms-full.txt')}): every kept unit by facet, disagreements, related concepts, sources — ≈{tok(full_text)} tokens",
             f"- [Vocabulary]({link('llms-vocabulary.txt')}): {len(lex['terms'])} terms with relations and definitions — ≈{tok(vocab_text)} tokens",
             f"- [Facts]({link('llms-facts.txt')}): the units in facts-file grammar for indexing — ≈{tok(facts_text)} tokens",
             f"- [Concept graph]({link('concept-graph.json')}): neighbours with relation type and evidence counts",
             "", "## Facets", ""]
    for facet, title in FACETS.items():
        rows = by_facet.get(facet)
        if rows:
            index.append(f"- [{title}]({link('llms-full.txt')}#{slugify(title)}): {FACET_BLURB[facet]} — "
                         f"{len(rows)} unit{'s' if len(rows) != 1 else ''}")
    index += ["", "## Related concepts", ""]
    for n in sorted(graph_nodes, key=lambda n: -n["hits"]):
        if n["relation"] == "self" or not n["hits"]:
            continue
        # the term rides inside the description too: two parts with equal counts would
        # otherwise be duplicate descriptions (llms_lint P3 D4)
        index.append(f"- [{n['term']}]({link('llms-vocabulary.txt')}): `{n['term']}` is a {n['relation']} of "
                     f"{concept} — {n['hits']} units across {len(n['sources'])} source{'s' if len(n['sources']) != 1 else ''}"
                     + (f"; {n['note']}" if n.get("note") else ""))
    index += ["", "## Sources", ""]
    for h in hosts:
        url = f"https://{h}/" if "." in h and not h.endswith((".md", ".txt")) else link("llms-full.txt") + "#sources"
        index.append(f"- [{h}]({url}): {sources[h]} units about {concept} from this source")
    index += ["", "## Optional", "",
              f"- [Manifest]({link('manifest.json')}): counts, lexicon, budget, rights, inputs",
              f"- [Units]({link('units.jsonl')}): indexable rows — `docset_indexer index units.jsonl --units --name concept__{slug}`",
              ""]
    index_text = "\n".join(index).rstrip() + "\n"

    for name, text in (("llms.txt", index_text), ("llms-full.txt", full_text),
                       ("llms-small.txt", small_text), ("llms-facts.txt", facts_text),
                       ("llms-vocabulary.txt", vocab_text), ("units.jsonl", units_text)):
        (out / name).write_text(text, encoding="utf-8")
        files[name] = {"bytes": len(text.encode()), "tokens": tok(text)}
    (out / "concept-graph.json").write_text(json.dumps(graph, indent=1, ensure_ascii=False) + "\n")
    report = {}
    rp = out / "harvest-report.json"
    if rp.exists():
        try:
            report = json.loads(rp.read_text())
        except json.JSONDecodeError:
            report = {}
    manifest = {
        "kind": "concept", "concept": concept, "slug": slug, "version": VERSION,
        "generated": generated, "summary": summary, "rights": rights,
        "budget_tokens": args.budget_tokens, "base_url": args.base_url,
        "inputs": report.get("inputs", []), "scanned_units": report.get("scanned_units"),
        "harvested_units": len(pool), "kept_units": len(kept),
        "dropped_by_classification": len(pool) - len(kept),
        "sources": {h: sources[h] for h in hosts},
        "facets": {f: len(by_facet[f]) for f in FACETS if by_facet.get(f)},
        "relations": dict(Counter(r["relation"] for r in kept)),
        "lexicon": {"terms": len(lex["terms"]), "zero_hit": zero,
                    "by_relation": dict(Counter(t["relation"] for t in lex["terms"]))},
        "conflicts": len(conflicts),
        "semantic": {"units": sum(1 for r in kept if r.get("pass") == "semantic"),
                     "scored": sum(1 for r in kept if r.get("semantic_score") is not None)},
        "files": files,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(f"compile: {len(kept)} units → {out} · full ≈{files['llms-full.txt']['tokens']} tok · "
          f"small ≈{files['llms-small.txt']['tokens']} tok · {len(hosts)} sources · "
          f"{len(zero)} zero-hit terms · {len(conflicts)} conflicts")



# --------------------------------------------------------------------------- #
# semantic index — ollama embeddings with an on-disk vector cache
# --------------------------------------------------------------------------- #

import hashlib
import os
import time
import urllib.error
import urllib.request
from array import array

try:                                   # numpy makes the 20k×1024 dot products instant;
    import numpy as _np                # the pure-python path below works without it
except Exception:                      # pragma: no cover
    _np = None

DEFAULT_EMBED_MODEL = os.environ.get("HUB_EMBED_MODEL", "mxbai-embed-large")
DEFAULT_OLLAMA = (os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434").rstrip("/")
if not DEFAULT_OLLAMA.startswith("http"):
    DEFAULT_OLLAMA = "http://" + DEFAULT_OLLAMA
DEFAULT_CACHE = Path(os.environ.get("LCA_EMBED_CACHE",
                                    "~/.global-ai-hub/llms-concepts/.embcache")).expanduser()
EMBED_MAX_CHARS = 1600      # mxbai-embed-large context is 512 tokens; longer text is truncated anyway
EMBED_BATCH = 64
FACET_QUERIES = [
    "what is {c}", "definition of {c}", "{c} parts and components", "how {c} works",
    "{c} configuration options and parameters", "how to use {c}", "{c} example",
    "{c} problems, errors and limitations", "{c} compared to alternatives",
    "{c} measurements and typical values", "history and changes of {c}",
]


def ollama_up(url: str, timeout: float = 3.0) -> bool:
    try:
        with urllib.request.urlopen(f"{url}/api/tags", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def restart_ollama(url: str, wait: int = 40) -> bool:
    """Best-effort local restart (macOS app, brew service, or a bare `ollama serve`)."""
    import subprocess
    subprocess.run(["pkill", "-f", "ollama serve"], capture_output=True)
    time.sleep(1.5)
    started = False
    for cmd in (["open", "-a", "Ollama"], ["brew", "services", "restart", "ollama"]):
        try:
            if subprocess.run(cmd, capture_output=True, timeout=20).returncode == 0:
                started = True
                break
        except Exception:
            continue
    if not started:
        try:
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
            started = True
        except FileNotFoundError:
            return False
    for _ in range(wait):
        if ollama_up(url):
            return True
        time.sleep(1)
    return False


def _embed_call(texts: list[str], model: str, url: str, timeout: int = 180) -> list[list[float]]:
    body = json.dumps({"model": model, "input": texts}).encode()
    req = urllib.request.Request(f"{url}/api/embed", data=body,
                                 headers={"Content-Type": "application/json"})
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                out = json.loads(r.read().decode())
            vecs = out.get("embeddings") or []
            if len(vecs) != len(texts):
                raise RuntimeError(f"embed: got {len(vecs)} vectors for {len(texts)} texts")
            return vecs
        except Exception as e:      # noqa: BLE001
            last = e
            time.sleep((5, 15, 30, 30)[attempt])
    raise RuntimeError(f"embed failed after retries: {last}")


class VecCache:
    """Append-only vector cache: <dir>/<model>/vectors.f32 + keys.txt (sha1 per row).
    Every text is embedded once per model on this box; re-runs and sibling packs
    over the same docsets cost no ollama time."""

    def __init__(self, root: Path, model: str):
        self.dir = Path(root).expanduser() / re.sub(r"[^A-Za-z0-9._-]+", "_", model)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.vec_path = self.dir / "vectors.f32"
        self.key_path = self.dir / "keys.txt"
        self.dim = 0
        self.keys: list[str] = []
        self.index: dict[str, int] = {}
        self.vecs = None
        self._load()

    def _locked(self):
        """Advisory lock so two packs embedding at once cannot interleave their
        appends (keys.txt and vectors.f32 must stay row-aligned)."""
        import fcntl
        from contextlib import contextmanager

        @contextmanager
        def _cm():
            with (self.dir / ".lock").open("w") as fh:
                fcntl.flock(fh, fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(fh, fcntl.LOCK_UN)
        return _cm()

    def _load(self):
        if self.key_path.exists():
            self.keys = self.key_path.read_text().split()
        meta = self.dir / "meta.json"
        if meta.exists():
            self.dim = json.loads(meta.read_text()).get("dim", 0)
        if self.vec_path.exists() and self.dim:
            rows_bytes = self.vec_path.stat().st_size // (self.dim * 4)
            if rows_bytes != len(self.keys):
                # self-heal: keep the aligned prefix, drop the tail of whichever file is longer
                n = min(rows_bytes, len(self.keys))
                print(f"embcache: keys={len(self.keys)} rows={rows_bytes} misaligned — trimming to {n}",
                      file=sys.stderr)
                with self._locked():
                    with self.vec_path.open("r+b") as fh:
                        fh.truncate(n * self.dim * 4)
                    self.keys = self.keys[:n]
                    self.key_path.write_text("\n".join(self.keys) + ("\n" if self.keys else ""))
        self.index = {k: i for i, k in enumerate(self.keys)}
        if self.vec_path.exists() and self.dim and self.keys:
            if _np is not None:
                self.vecs = _np.fromfile(self.vec_path, dtype=_np.float32).reshape(-1, self.dim)
            else:
                a = array("f")
                with self.vec_path.open("rb") as fh:
                    a.frombytes(fh.read())
                self.vecs = [a[i * self.dim:(i + 1) * self.dim] for i in range(len(a) // self.dim)]

    @staticmethod
    def key(text: str) -> str:
        return hashlib.sha1(text[:EMBED_MAX_CHARS].encode("utf-8", "replace")).hexdigest()

    def get_many(self, texts: list[str], model: str, url: str, log=print):
        """Return unit-normalised vectors for texts (embedding the misses)."""
        keys = [self.key(t) for t in texts]
        misses = [(i, t) for i, (k, t) in enumerate(zip(keys, texts)) if k not in self.index]
        if misses:
            log(f"embedding {len(misses)} new texts with {model} ({len(texts) - len(misses)} cached)")
            new_vecs: list[list[float]] = []
            new_keys: list[str] = []
            seen_new: dict[str, int] = {}
            t0 = time.time()
            batch_texts, batch_keys = [], []
            for n, (i, t) in enumerate(misses, 1):
                k = keys[i]
                if k in seen_new or k in self.index:
                    continue
                seen_new[k] = 1
                batch_texts.append(t[:EMBED_MAX_CHARS])
                batch_keys.append(k)
                if len(batch_texts) == EMBED_BATCH or n == len(misses):
                    vs = _embed_call(batch_texts, model, url)
                    for v, kk in zip(vs, batch_keys):
                        norm = sum(x * x for x in v) ** 0.5 or 1.0
                        new_vecs.append([x / norm for x in v])
                        new_keys.append(kk)
                    batch_texts, batch_keys = [], []
                    if n % (EMBED_BATCH * 10) == 0:
                        log(f"  {n}/{len(misses)} … {time.time() - t0:.0f}s")
            if new_vecs:
                with self._locked():
                    self._load()              # another process may have appended meanwhile
                    fresh = [(v, k) for v, k in zip(new_vecs, new_keys) if k not in self.index]
                    if not self.dim:
                        self.dim = len(new_vecs[0])
                        (self.dir / "meta.json").write_text(json.dumps({"model": model, "dim": self.dim}))
                    if fresh:
                        with self.vec_path.open("ab") as fh:
                            for v, _ in fresh:
                                fh.write(array("f", v).tobytes())
                        with self.key_path.open("a") as fh:
                            fh.write("\n".join(k for _, k in fresh) + "\n")
                    self.vecs = None
                    self._load()
        rows = [self.index[k] for k in keys]
        if _np is not None:
            return self.vecs[rows]
        return [self.vecs[r] for r in rows]


def _matmul(A, B):
    """cosine matrix for unit vectors: A (n×d) · B (m×d)ᵀ → n×m. float64 on purpose:
    macOS Accelerate raises spurious divide/overflow RuntimeWarnings on float32 sgemm."""
    if _np is not None:
        with _np.errstate(all="ignore"):
            return _np.asarray(A, dtype=_np.float64) @ _np.asarray(B, dtype=_np.float64).T
    import operator
    return [[sum(map(operator.mul, a, b)) for b in B] for a in A]


def _col_max(M):
    if _np is not None:
        return M.max(axis=1) if M.shape[1] else _np.zeros(M.shape[0])
    return [max(r) if r else 0.0 for r in M]


def _normalise(v):
    if _np is not None:
        n = float(_np.linalg.norm(v)) or 1.0
        return v / n
    n = sum(x * x for x in v) ** 0.5 or 1.0
    return [x / n for x in v]


def semantic(args) -> None:
    """Semantic pass over the WHOLE scope: embed every unit (cached), score each
    against the concept's query set and against the centroid of the keyword
    harvest, add what the lexicon missed, flag keyword hits that are
    semantically far from the concept (polysemy suspects), rank lexicon
    candidates by meaning, and fold near-duplicates."""
    lex = load_lexicon(args.lexicon)
    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    url = args.ollama.rstrip("/")
    if not ollama_up(url):
        if args.restart_ollama and restart_ollama(url):
            print("ollama restarted")
        else:
            sys.exit(f"ollama not reachable at {url} — start it (open -a Ollama / brew services "
                     f"restart ollama / ollama serve) or pass --restart-ollama; not falling back "
                     f"to keyword-only silently")
    cache = VecCache(Path(args.cache), args.model)
    concept = lex["concept"]

    # 1. scope units
    units: list[dict] = []
    seen: dict[str, int] = {}
    _, excl = compile_lexicon(lex)
    excluded = 0
    for f, it in iter_inputs(args.__dict__["from"], args.base_url):
        for u in it:
            k = _norm(u["text"])
            if k in seen or len(u["text"]) < 25:
                continue
            # the lexicon's excludes apply here too — a foreign sense must not come back
            # through the semantic door after the keyword pass shut it out
            if excl and any(e.search(u["text"] + " " + u["heading_path"]) for e in excl):
                excluded += 1
                continue
            if prefilter(u):          # same non-content filter as the keyword pass
                excluded += 1
                continue
            seen[k] = len(units)
            units.append(u)
    if not units:
        sys.exit("semantic: no units in scope")
    texts = [u["text"] for u in units]
    U = cache.get_many(texts, args.model, url)

    # 2. query set: concept, self/synonym terms, facet phrasings, keyword-pool centroid
    qtexts = [concept] + [t["term"] for t in lex["terms"] if t["relation"] in ("self", "synonym", "abbreviation")]
    qtexts += [q.format(c=concept) for q in FACET_QUERIES]
    qtexts = list(dict.fromkeys(qtexts))
    Q = cache.get_many(qtexts, args.model, url)
    pool_path = out / "pool.jsonl"
    pool = [json.loads(l) for l in pool_path.read_text().splitlines() if l.strip()] if pool_path.exists() else []
    pool_keys = {_norm(r["text"]) for r in pool}
    centroid = None
    if pool:
        # centroid from PROSE keyword hits: parameter/snippet/table rows dominate many
        # docsets' pools and would drag the centroid towards "pricing table" rather
        # than "the concept" — measured: +66 adds with tables vs cleaner adds without
        prose = [r for r in pool if r["type"] not in ("parameter", "snippet", "table", "example")]
        base = prose if len(prose) >= 10 else pool
        top = sorted(base, key=lambda r: -r["score"])[:args.centroid_top]
        C = cache.get_many([r["text"] for r in top], args.model, url)
        if _np is not None:
            centroid = _normalise(_np.asarray(C).mean(axis=0))
        else:
            d = len(C[0])
            centroid = _normalise([sum(v[i] for v in C) / len(C) for i in range(d)])
    # 3. centred, z-scored similarity. Raw cosine is useless as an absolute
    # threshold (mxbai's floor is ~0.5 and every unit of an API docset is
    # "about the API"); subtracting each unit's similarity to the scope mean
    # removes the domain background, and z-scoring across the scope makes the
    # floor comparable between a 400-unit textbook and a 20k-unit estate scan.
    if _np is None:
        sys.exit("semantic: numpy is required (run with ~/.global-ai-hub/.venv/bin/python)")
    Un = _np.asarray(U, dtype=_np.float64)
    mean_vec = _normalise(Un.mean(axis=0))
    bg = _matmul(Un, [mean_vec])[:, 0]
    sq = _matmul(Un, Q).max(axis=1)
    raw = sq.copy()
    if centroid is not None:
        sc = _matmul(Un, [centroid])[:, 0]
        raw = _np.maximum(sq, sc)
    adj = raw - bg
    mu, sd = float(adj.mean()), float(adj.std() or 1.0)
    z = (adj - mu) / sd
    bands = {f"z>={b}": int((z >= b).sum()) for b in (2.0, 2.5, 3.0, 3.5, 4.0, 5.0)}
    hist = Counter(f"{int(v * 10) / 10:.1f}" for v in raw)
    added, suspects = [], []
    zpool: dict[str, float] = {}
    for i, u in enumerate(units):
        k = _norm(u["text"])
        if k in pool_keys:
            zpool[k] = float(z[i])
            continue
        if z[i] >= args.z:
            rec = dict(u, matched=[], relations=["about"], relation="about",
                       score=round(min(2.0, 0.6 + 0.2 * (float(z[i]) - args.z)), 2),
                       semantic_score=round(float(raw[i]), 3), semantic_z=round(float(z[i]), 2),
                       facet=heuristic_facet(u), keep=True)
            rec["pass"] = "semantic"
            added.append(rec)
    added.sort(key=lambda r: -r["semantic_z"])
    if args.max_add and len(added) > args.max_add:
        added = added[:args.max_add]
    # annotate the keyword pool: a keyword hit far below the concept's meaning is a polysemy suspect
    if pool:
        for r in pool:
            zz = zpool.get(_norm(r["text"]))
            if zz is None:
                continue
            r["semantic_z"] = round(zz, 2)
            if zz < args.suspect_z:
                suspects.append({"id": r["id"], "semantic_z": round(zz, 2), "score": r["score"],
                                 "matched": r["matched"], "text": r["text"][:140]})
        suspects.sort(key=lambda x: x["semantic_z"])
        with pool_path.open("w", encoding="utf-8") as fh:
            for r in pool:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 4. near-duplicates across pool ∪ added (fold, keep sources)
    folded = 0
    if args.near_dedupe and (pool or added) and _np is not None:
        allrecs = pool + added
        V = cache.get_many([r["text"] for r in allrecs], args.model, url)
        S = _matmul(V, V)
        gone = set()
        order = sorted(range(len(allrecs)), key=lambda i: -allrecs[i]["score"])
        for a in order:
            if a in gone:
                continue
            dup = _np.where(S[a] >= args.near_dedupe)[0]
            for b in dup:
                b = int(b)
                if b == a or b in gone:
                    continue
                if _host(allrecs[a]["source_url"]) == _host(allrecs[b]["source_url"]) and \
                        allrecs[a]["source_url"] == allrecs[b]["source_url"]:
                    continue        # same page restating itself: leave to /ldo P7
                keep = allrecs[a]
                for src in [allrecs[b]["source_url"], *allrecs[b].get("also", [])]:
                    if src != keep["source_url"] and src not in keep.setdefault("also", []):
                        keep["also"].append(src)
                gone.add(b)
                folded += 1
        pool = [r for i, r in enumerate(allrecs[:len(pool)]) if i not in gone]
        added = [r for j, r in enumerate(allrecs[len(allrecs) - len(added):], start=len(allrecs) - len(added)) if j not in gone]
        with pool_path.open("w", encoding="utf-8") as fh:
            for r in pool:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    with (out / "semantic.jsonl").open("w", encoding="utf-8") as fh:
        for r in added:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 5. lexicon candidates ranked by meaning
    cands = []
    rp = out / "harvest-report.json"
    report = json.loads(rp.read_text()) if rp.exists() else {}
    cand_tokens = [c["token"] for c in report.get("candidates", [])][:80]
    if cand_tokens:
        Cv = cache.get_many(cand_tokens, args.model, url)
        cs = _matmul(Cv, [Q[0]] if _np is None else Q[:1])
        for c, row in zip(report["candidates"], cs):
            c["sim"] = round(float(row[0]), 3)
        report["candidates"].sort(key=lambda c: -(c.get("sim", 0) * min(c["in_pool"], 20) * c["lift"]))
        cands = report["candidates"][:40]
        rp.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    # nearest-unit vocabulary: backtick / heading tokens of the top semantic hits not in the lexicon
    known = {s.lower() for t in lex["terms"] for s in t["surfaces"]}
    near_terms: Counter = Counter()
    for r in added[:150]:
        for tk in _TICK_RE.findall(r["text"]) + re.split(r"\s*>\s*", r.get("heading_path", "")):
            tk = tk.strip()
            if 2 < len(tk) < 50 and tk.lower() not in known and tk.lower() not in _STOP:
                near_terms[tk] += 1
    sem_report = {
        "concept": concept, "model": args.model, "generated": date.today().isoformat(),
        "scope_units": len(units), "excluded_by_lexicon": excluded, "z_floor": args.z, "z_bands_in_scope": bands,
        "queries": qtexts, "centroid_from_pool_top": args.centroid_top if centroid is not None else 0,
        "added": len(added), "added_by_facet": dict(Counter(r["facet"] for r in added)),
        "added_z_bands": {f"z>={b}": sum(1 for r in added if r["semantic_z"] >= b) for b in (3.0, 3.5, 4.0, 5.0)},
        "added_sources": dict(Counter(_host(r["source_url"]) for r in added).most_common()),
        "near_duplicates_folded": folded,
        "raw_cosine_histogram": dict(sorted(hist.items())),
        "keyword_suspects_z_below": args.suspect_z, "keyword_suspects": suspects[:60],
        "keyword_pool_z": {"median": round(float(_np.median(list(zpool.values()))), 2) if zpool else None,
                           "p10": round(float(_np.percentile(list(zpool.values()), 10)), 2) if zpool else None},
        "candidates_by_meaning": cands,
        "near_terms": [{"token": t, "uses": n} for t, n in near_terms.most_common(30)],
        "cache": str(cache.dir),
    }
    (out / "semantic-report.json").write_text(json.dumps(sem_report, indent=1, ensure_ascii=False) + "\n")
    print(f"semantic: {len(units)} scope units embedded ({args.model}) · +{len(added)} units at z≥{args.z} "
          f"the lexicon missed → semantic.jsonl (bands {bands}) · {len(suspects)} keyword suspects z<{args.suspect_z} · "
          f"{folded} near-dups folded · report: semantic-report.json")


def query(args) -> None:
    """Semantic query over a compiled pack's kept units (units.jsonl)."""
    d = Path(args.dir).expanduser()
    up = d / "units.jsonl"
    if not up.exists():
        sys.exit("no units.jsonl — compile first")
    url = args.ollama.rstrip("/")
    if not ollama_up(url):
        sys.exit(f"ollama not reachable at {url}")
    cache = VecCache(Path(args.cache), args.model)
    rows = [json.loads(l) for l in up.read_text().splitlines() if l.strip()]
    V = cache.get_many([r["text"] for r in rows], args.model, url, log=lambda *_: None)
    qv = cache.get_many([args.question], args.model, url, log=lambda *_: None)
    sims = _matmul(V, qv)
    scored = sorted(((float(sims[i][0]), r) for i, r in enumerate(rows)), key=lambda x: -x[0])[:args.top]
    for s, r in scored:
        print(f"{s:.3f} [{r['type']}] {re.sub(chr(10), ' ', r['text'])[:150]} — {r['source_url']}{r.get('anchor', '')}")



# --------------------------------------------------------------------------- #
# split — the family rule: one big pack → child packs by term group
# --------------------------------------------------------------------------- #

def split_pack(args) -> None:
    """groups.json: [{"slug": "index-types", "concept": "Index types", "terms": ["B-tree", …]}, …]
    in priority order. Each kept unit goes to the first group that shares a matched
    lexicon term with it; the rest stay parent-only. Every child is compiled with the
    parent's lexicon into <parent>/../<slug>.llms/ (or --children-dir), and the parent
    llms.txt gains a `## Child packs` section; manifest gains `children`."""
    import argparse as _ap
    out = Path(args.out).expanduser()
    up = out / "units.jsonl"
    if not up.exists():
        sys.exit("split: compile the parent first (needs units.jsonl)")
    groups = json.loads(Path(args.groups).expanduser().read_text())
    if not isinstance(groups, list) or not groups:
        sys.exit("split: groups.json must be a non-empty list")
    kept = [json.loads(l) for l in up.read_text(encoding="utf-8").splitlines() if l.strip()]
    # units.jsonl rows carry keywords (matched terms first); rebuild matched from the parent pool for fidelity
    pool_by_id = {r["id"]: r for r in load_pool(out)}
    gterms = []
    for g in groups:
        gterms.append({t.lower() for t in g.get("terms", [])})
    assign: dict[str, list[dict]] = defaultdict(list)
    for u in kept:
        src = pool_by_id.get(u["id"], u)
        matched = {m.lower() for m in (src.get("matched") or u.get("keywords") or [])}
        target = "parent-only"
        for g, ts in zip(groups, gterms):
            if matched & ts:
                target = g["slug"]
                break
        assign[target].append(dict(src, facet=u.get("section", src.get("facet")),
                                   relation=u.get("relation", src.get("relation")), keep=True))
    children_dir = Path(args.children_dir).expanduser() if args.children_dir else out.parent
    parent_manifest = json.loads((out / "manifest.json").read_text())
    children = {}
    for g in groups:
        rows = assign.get(g["slug"], [])
        if len(rows) < args.min_units:
            print(f"split: {g['slug']} has {len(rows)} units (< {args.min_units}) — skipped")
            continue
        cdir = children_dir / f"{g['slug']}.llms"
        cdir.mkdir(parents=True, exist_ok=True)
        with (cdir / "pool.jsonl").open("w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        (cdir / "harvest-report.json").write_text(json.dumps({
            "concept": g["concept"], "slug": g["slug"], "parent": parent_manifest.get("slug"),
            "inputs": parent_manifest.get("inputs", []), "scanned_units": parent_manifest.get("scanned_units"),
            "kept_units": len(rows), "terms": g.get("terms", [])}, indent=1))
        cargs = _ap.Namespace(out=str(cdir), concept=g["concept"], lexicon=args.lexicon, classified=None,
                              budget_tokens=args.budget_tokens, summary=g.get("summary"),
                              rights=parent_manifest.get("rights", "extractive"), base_url=None)
        compile_pack(cargs)
        cm = json.loads((cdir / "manifest.json").read_text())
        cm["parent"] = parent_manifest.get("slug")
        cm["split_terms"] = g.get("terms", [])
        (cdir / "manifest.json").write_text(json.dumps(cm, indent=1, ensure_ascii=False) + "\n")
        children[g["slug"]] = {"concept": g["concept"], "units": len(rows), "terms": g.get("terms", []),
                               "full_tokens": cm["files"]["llms-full.txt"]["tokens"],
                               "small_tokens": cm["files"]["llms-small.txt"]["tokens"],
                               "path": str(cdir)}
    # parent index: add / replace the Child packs section (before ## Optional)
    idx_path = out / "llms.txt"
    idx = idx_path.read_text(encoding="utf-8")
    idx = re.sub(r"\n## Child packs\n[\s\S]*?(?=\n## |\Z)", "\n", idx)
    lines = ["## Child packs", ""]
    for slug, c in children.items():
        rel = os.path.relpath(children_dir / f"{slug}.llms" / "llms.txt", out)
        terms = ", ".join((c.get("terms") or [])[:4])
        lines.append(f"- [{c['concept']}]({rel}): {terms} — {c['units']} units, "
                     f"full ≈{c['full_tokens']} tokens, small ≈{c['small_tokens']} tokens")
    po = len(assign.get("parent-only", []))
    if po:
        lines.append(f"- [Parent-only units](llms-full.txt): {po} units matched by no child's terms — read the parent for these")
    block = "\n".join(lines) + "\n"
    if "\n## Optional\n" in idx:
        idx = idx.replace("\n## Optional\n", "\n" + block + "\n## Optional\n", 1)
    else:
        idx = idx.rstrip() + "\n\n" + block
    idx_path.write_text(idx, encoding="utf-8")
    parent_manifest.setdefault("files", {})["llms.txt"] = {"bytes": len(idx.encode()), "tokens": _tokens_of(idx)}
    parent_manifest["children"] = children
    parent_manifest["parent_only_units"] = po
    (out / "manifest.json").write_text(json.dumps(parent_manifest, indent=1, ensure_ascii=False) + "\n")
    (out / "split-assignment.json").write_text(json.dumps(
        {k: [r["id"] for r in v] for k, v in assign.items()}, indent=1))
    print(f"split: {len(children)} child packs under {children_dir} · parent-only {po} · "
          + " · ".join(f"{k}={v['units']}" for k, v in children.items()))


# --------------------------------------------------------------------------- #
# stats / probe
# --------------------------------------------------------------------------- #

def stats(args) -> None:
    d = Path(args.dir).expanduser()
    mp = d / "manifest.json"
    if mp.exists():
        print(json.dumps(json.loads(mp.read_text()), indent=1, ensure_ascii=False))
        return
    pool = load_pool(d)
    print(json.dumps({"units": len(pool),
                      "facets": dict(Counter(r["facet"] for r in pool)),
                      "relations": dict(Counter(r["relation"] for r in pool)),
                      "sources": dict(Counter(_host(r["source_url"]) for r in pool)),
                      "score_hist": dict(sorted(Counter(str(r["score"]) for r in pool).items()))},
                     indent=1))


def probe(args) -> None:
    """Cheap coverage probe: for each question, do its content tokens (minus stopwords)
    appear in the small/full catalogue? Reports hit ratio per question and overall.
    A real agent test (fresh subagent answering from the pack) is in the skill's
    verification reference — this is the free pre-check."""
    d = Path(args.dir).expanduser()
    texts = {n: (d / n).read_text(encoding="utf-8", errors="replace").lower()
             for n in ("llms-small.txt", "llms-full.txt") if (d / n).exists()}
    if not texts:
        sys.exit("no compiled files in dir")
    rows = []
    for line in Path(args.questions).expanduser().read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        q = json.loads(line) if line.startswith("{") else {"q": line}
        toks = [w for w in _WORD_RE.findall((q.get("q") or q.get("question") or "").lower())
                if w not in _STOP and len(w) > 2]
        must = [w.lower() for w in (q.get("must") or [])]
        res = {"q": q.get("q") or q.get("question")}
        for name, text in texts.items():
            hit = sum(1 for w in toks if w in text)
            res[name] = {"tokens": f"{hit}/{len(toks)}",
                         "must": all(m in text for m in must) if must else None}
        rows.append(res)
    if args.semantic:
        d2 = d
        up = d2 / "units.jsonl"
        if up.exists() and ollama_up(args.ollama.rstrip("/")):
            cache = VecCache(Path(args.cache), args.model)
            urows = [json.loads(l) for l in up.read_text().splitlines() if l.strip()]
            V = cache.get_many([r["text"] for r in urows], args.model, args.ollama.rstrip("/"), log=lambda *_: None)
            qs = [r["q"] for r in rows]
            Qv = cache.get_many(qs, args.model, args.ollama.rstrip("/"), log=lambda *_: None)
            S = _matmul(Qv, V)
            for i, r in enumerate(rows):
                best = max(float(x) for x in S[i]) if len(urows) else 0.0
                r["semantic_best"] = round(best, 3)
                r["semantic_covered"] = best >= args.sem_threshold
            print(f"semantic: {sum(1 for r in rows if r['semantic_covered'])}/{len(rows)} questions have a unit ≥ {args.sem_threshold}")
        else:
            print("semantic probe skipped (no units.jsonl or ollama down)")
    total = len(rows)
    for name in texts:
        ok = sum(1 for r in rows if r[name]["must"] is not False and
                 int(r[name]["tokens"].split("/")[0]) >= max(1, round(0.6 * int(r[name]["tokens"].split("/")[1]))))
        print(f"{name}: {ok}/{total} questions covered (≥60% content tokens present, must-terms present)")
    print(json.dumps(rows, indent=1, ensure_ascii=False))


# --------------------------------------------------------------------------- #

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("harvest", help="scan inputs for lexicon terms → pool.jsonl + harvest-report.json")
    h.add_argument("--lexicon", required=True)
    h.add_argument("--from", dest="from", nargs="+", required=True,
                   help="units.jsonl | llms-facts.txt | llms-full.txt | mirror .md | any .md/.txt | dir | glob")
    h.add_argument("--out", required=True)
    h.add_argument("--min-score", type=float, default=0.6)
    h.add_argument("--context", type=int, default=0, help="1 = keep neighbour paragraphs for text inputs")
    h.add_argument("--max-units", type=int, default=0)
    h.add_argument("--heading-only-min-chars", type=int, default=200,
                   help="units shorter than this that match only via their heading are dropped (0 = keep)")
    h.add_argument("--no-require-core", dest="require_core", action="store_false",
                   help="let a single contrast/related/broader term qualify a unit (recall over precision)")
    h.add_argument("--base-url", default=None, help="prefix for `# Title (/path)` H1s in llms-full files")
    h.set_defaults(func=harvest)
    v = sub.add_parser("view", help="one line per unit: id|facet|relation|score|terms|host|text")
    v.add_argument("dir")
    v.add_argument("--facet", default=None)
    v.add_argument("--min-score", type=float, default=0.0)
    v.add_argument("--limit", type=int, default=0)
    v.add_argument("--ids", default=None)
    v.add_argument("--width", type=int, default=160)
    v.set_defaults(func=view)
    c = sub.add_parser("compile", help="render the concept pack from pool.jsonl (+ classified.jsonl)")
    c.add_argument("--out", required=True, help="the harvest dir; files are written beside pool.jsonl")
    c.add_argument("--concept", default=None)
    c.add_argument("--lexicon", default=None)
    c.add_argument("--classified", default=None)
    c.add_argument("--budget-tokens", type=int, default=8000)
    c.add_argument("--summary", default=None)
    c.add_argument("--rights", choices=("extractive", "quote"), default="extractive")
    c.add_argument("--base-url", default=None)
    c.set_defaults(func=compile_pack)
    sp = sub.add_parser("split", help="family rule: slice a compiled pack into child packs by term group")
    sp.add_argument("--out", required=True, help="the compiled parent pack dir")
    sp.add_argument("--groups", required=True, help="groups.json: ordered [{slug, concept, terms[], summary?}]")
    sp.add_argument("--lexicon", default=None)
    sp.add_argument("--children-dir", default=None, help="where <slug>.llms/ dirs go (default: beside the parent)")
    sp.add_argument("--budget-tokens", type=int, default=8000)
    sp.add_argument("--min-units", type=int, default=20)
    sp.set_defaults(func=split_pack)
    s = sub.add_parser("stats", help="manifest or pool statistics")
    s.add_argument("dir")
    s.set_defaults(func=stats)
    p = sub.add_parser("probe", help="keyword coverage of a question bank against the pack")
    p.add_argument("dir")
    p.add_argument("--questions", required=True, help='jsonl: {"q": "...", "must": ["term"]} or plain lines')
    p.add_argument("--semantic", action="store_true", help="also embed questions vs kept units")
    p.add_argument("--sem-threshold", type=float, default=0.55)
    p.add_argument("--model", default=DEFAULT_EMBED_MODEL)
    p.add_argument("--ollama", default=DEFAULT_OLLAMA)
    p.add_argument("--cache", default=str(DEFAULT_CACHE))
    p.set_defaults(func=probe)
    se = sub.add_parser("semantic", help="embed the whole scope; add units the lexicon missed; flag "
                        "keyword suspects; rank candidates by meaning; fold near-dups")
    se.add_argument("--lexicon", required=True)
    se.add_argument("--from", dest="from", nargs="+", required=True)
    se.add_argument("--out", required=True, help="the harvest dir (reads/annotates pool.jsonl)")
    se.add_argument("--model", default=DEFAULT_EMBED_MODEL)
    se.add_argument("--ollama", default=DEFAULT_OLLAMA)
    se.add_argument("--cache", default=str(DEFAULT_CACHE))
    se.add_argument("--z", type=float, default=3.0,
                    help="floor on the centred, scope-z-scored similarity for adding a unit (3.5 strict, 2.5 loose)")
    se.add_argument("--suspect-z", type=float, default=0.5,
                    help="keyword-pool units below this z are listed as polysemy suspects for the model")
    se.add_argument("--centroid-top", type=int, default=40)
    se.add_argument("--max-add", type=int, default=200)
    se.add_argument("--near-dedupe", type=float, default=0.93, help="0 to disable")
    se.add_argument("--base-url", default=None)
    se.add_argument("--restart-ollama", action="store_true")
    se.set_defaults(func=semantic)
    qq = sub.add_parser("query", help="semantic query over a compiled pack")
    qq.add_argument("dir")
    qq.add_argument("question")
    qq.add_argument("--top", type=int, default=10)
    qq.add_argument("--model", default=DEFAULT_EMBED_MODEL)
    qq.add_argument("--ollama", default=DEFAULT_OLLAMA)
    qq.add_argument("--cache", default=str(DEFAULT_CACHE))
    qq.set_defaults(func=query)
    a = ap.parse_args(argv)
    if a.cmd == "compile" and not (a.concept or a.lexicon):
        ap.error("compile needs --concept or --lexicon")
    a.func(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
