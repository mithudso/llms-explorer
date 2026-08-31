"""vocabulary — the lexical layer of a topical family: `llms-vocabulary.txt`.

One line per term of the niche — canonical name, definition, how it differs
from its neighbours (`not:`), the words people use instead (`aka:`) — each
anchored to the unit it was taken from. Neither index nor facts: it is what
makes both findable. It feeds three places that are weak without it:

  assignment   `aka:` lists become the concept-tree nodes' `aliases`, so the
               topical builder's keyword pass matches synonyms (--register)
  keyword      the FTS5 layer can expand a query through the aka: list
  descriptions the canonical definition is the one-liner an index wants

Sources, in trust order (deterministic first, model last and verified):
  1. concept-tree node names + existing aliases (the subject and its children)
  2. tokens the pool keeps in backticks (file names, headers, paths, tools),
     clustered by normalised spelling — the most frequent surface is
     canonical, the others are aka:
  3. `definition` units and "X is/are …" sentences → definitions; contrast
     cues (not, unlike, vs, rather than, instead of) → not:
  4. --llm: the local Ollama model writes a missing definition / differentiator
     for a term from ≤ 6 units that mention it; every name it returns must
     appear in those units (evidence rule) or it is dropped

Output `<out>/llms-vocabulary.txt` + `vocabulary.json`; manifest.json gains a
`files` entry. `--register` merges each term's aka: into the matching tree
node's `aliases` (add-only).
"""

from __future__ import annotations

import json
import re
from collections import Counter, OrderedDict
from datetime import datetime
from pathlib import Path

from .topical import CHARS_PER_TOKEN, _STOP as _STOPWORDS, _rec, _tokens, dedupe, load_pool

MIN_TOKEN_USES = 2          # a backtick token seen this often is a term candidate
MAX_UNITS_PER_TERM = 6      # evidence handed to the model per term
MAX_TERMS = 80
_CUE_RE = re.compile(r"\b(?:not|unlike|vs\.?|versus|rather than|instead of|as opposed to|"
                     r"not to be confused with|differs? from)\b", re.I)
_AKA_RE = re.compile(r"\((?:aka|a\.k\.a\.|also called|also known as)\s+([^)]+)\)|"
                     r"\b(?:also called|also known as|a\.k\.a\.)\s+`?([^`,.;]+)`?", re.I)
_DEF_RE = re.compile(r"^(?:a |an |the )?`?(?P<subj>[\w./:-]+(?: [\w./:-]+){0,3})`? "
                     r"(?:is|are|means) (?:a|an|the|one|any|not)\b", re.I)
_SHAPE_RE = re.compile(r"^[\w./:#<>|=\"'\[\]()\s-]{2,60}$")
# markdown syntax quoted as an example is not a term: headings, list grammar,
# blockquote markers, bare `key:` labels
_SYNTAX_RE = re.compile(r"^(#+\s|-\s\[|>\s|\w{1,12}:$)")
_STOP = {"description", "title", "url", "optional", "on", "off", "true", "false"}
_PLAIN_WORD_RE = re.compile(r"^[a-z]{1,12}$")   # a bare English word is not a term of a niche
FAMILY_TOKENS = 200        # the pool's most frequent content tokens define "on topic"
MIN_FAMILY_OVERLAP = 2     # research evidence must share this many family tokens (beyond the term)


# --------------------------------------------------------------------------- #
# candidates
# --------------------------------------------------------------------------- #


def normalise(term: str) -> str:
    """Spelling-insensitive key: `LLMs-Full.txt`, `llms full txt`, `llms_full`
    all map to `llmsfulltxt`."""
    t = term.strip().strip("`").lower()
    t = re.sub(r"^[./]+", "", t)
    return re.sub(r"[^a-z0-9]+", "", t)


def token_clusters(pool: list[dict]) -> dict[str, Counter]:
    """normalised key -> Counter of surface spellings (from keywords + text)."""
    surf: dict[str, Counter] = {}
    for r in pool:
        seen = set()
        for k in r.get("keywords") or []:
            k = k.strip()
            if (not k or len(k) > 60 or not _SHAPE_RE.match(k) or k.lower() in _STOP
                    or _SYNTAX_RE.match(k)):
                continue
            key = normalise(k)
            if len(key) < 3 or key in seen or _PLAIN_WORD_RE.match(k):
                continue
            seen.add(key)
            surf.setdefault(key, Counter())[k] += 1
    return surf


def candidates(pool: list[dict], tree=None, subject: str = "") -> list[dict]:
    """Term records {term, key, aka, kind, node} from the tree and the pool."""
    out: dict[str, dict] = OrderedDict()

    def add(term: str, kind: str, aka=None, node: str = ""):
        key = normalise(term)
        if not key:
            return
        rec = out.setdefault(key, {"term": term, "key": key, "aka": [], "kind": kind,
                                   "node": node})
        for a in aka or []:                  # spelling variants share the key on purpose
            if a and a != rec["term"] and a not in rec["aka"]:
                rec["aka"].append(a)
    if tree is not None and subject:
        node = tree.by_concept.get(subject)
        names = [subject, *((node or {}).get("childConcepts") or [])]
        for n in names:
            cn = tree.by_concept.get(n) or {}
            add(n, "concept", cn.get("aliases") or [], node=n)
    for _key, surfaces in token_clusters(pool).items():
        if sum(surfaces.values()) < MIN_TOKEN_USES:
            continue
        canon, _ = surfaces.most_common(1)[0]
        add(canon, "token", [s for s in surfaces if s != canon])
    return list(out.values())[:MAX_TERMS]


# --------------------------------------------------------------------------- #
# evidence per term
# --------------------------------------------------------------------------- #


def _mentions(text: str, term: dict) -> bool:
    low = text.lower()
    for t in [term["term"], *term["aka"]]:
        t = t.strip("`").lower()
        if len(t) >= 3 and t in low:
            return True
    if term.get("kind") == "concept":
        # a concept name is a phrase; ≥ 60% of its content tokens counts
        toks = {w for w in _tokens(term["term"]) if w not in _STOPWORDS}
        return bool(toks) and len(toks & _tokens(text)) / len(toks) >= 0.6
    return False


def evidence(pool: list[dict], term: dict) -> list[dict]:
    """Units mentioning the term: definitions first, then the shortest."""
    hits = [r for r in pool if _mentions(r["text"], term)]
    hits.sort(key=lambda r: (r["type"] not in ("definition", "concept"), len(r["text"])))
    return hits[:MAX_UNITS_PER_TERM]


def _definition_from(units: list[dict], term: dict) -> dict | None:
    """A unit whose subject IS the term ("X is a …"), else a definition-typed
    unit mentioning it."""
    key = term["key"]
    for u in units:
        m = _DEF_RE.match(u["text"])
        if m and normalise(m.group("subj")) == key:
            return u
    names = [term["term"], *term["aka"]]
    for u in units:
        head = u["text"][:60].lower()
        if u["type"] in ("definition", "concept") and any(
                n.strip("`").lower() in head for n in names):
            return u
    return None


def _contrasts(units: list[dict], term: dict, all_terms: list[dict]) -> list[dict]:
    """Other vocabulary terms named after a contrast cue in a unit that
    mentions this term — the `not:` list, each with its evidence unit."""
    out = []
    for u in units:
        m = _CUE_RE.search(u["text"])
        if not m:
            continue
        tail = u["text"][m.end():].lower()
        for other in all_terms:
            if other["key"] == term["key"]:
                continue
            names = [other["term"], *other["aka"]]
            if any(len(n) >= 3 and n.strip("`").lower() in tail for n in names):
                out.append({"term": other["term"], "unit": u,
                            "how": u["text"][m.start():m.start() + 120].rstrip(",;: ")})
                break
    return out


def _aka_in_text(units: list[dict], term: dict) -> list[str]:
    """"(also called X)" counts only when it follows THIS term's mention."""
    found = []
    names = [n.strip("`").lower() for n in [term["term"], *term["aka"]] if len(n) >= 3]
    for u in units:
        for m in _AKA_RE.finditer(u["text"]):
            before = u["text"][max(0, m.start() - 48):m.start()].lower()
            if not any(n in before for n in names):
                continue
            for cand in (m.group(1) or m.group(2) or "").split(","):
                cand = cand.strip().strip("`\"' ")
                if 2 < len(cand) <= 40 and cand not in found:
                    found.append(cand)
    return found


# --------------------------------------------------------------------------- #
# research: evidence the hub already holds, for terms the pool does not define
# --------------------------------------------------------------------------- #

MAX_RESEARCH_UNITS = 8      # evidence units gathered per term from the estate
_SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z`\"'(\[])")


def _term_patterns(terms: list[dict]) -> dict[str, re.Pattern]:
    pats = {}
    for t in terms:
        names = [n.strip("`") for n in [t["term"], *t["aka"]] if len(n.strip("`")) >= 3]
        if names:
            pats[t["key"]] = re.compile("|".join(re.escape(n) for n in names), re.I)
    return pats


def estate_units(mirror_dir: Path | None = None, topical_dir: Path | None = None):
    """Every fact unit on this box: each docset's `<stem>.reference/all_units.jsonl`
    and every other topical dir's `units.jsonl` — the facts layers' sources of
    truth, read from disk (no store, no embedding)."""
    from hub_manager import core
    root = Path(mirror_dir or core.MIRROR_OUT_DIR)
    for ref in sorted(root.glob("*.reference/all_units.jsonl")):
        for line in ref.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                u = json.loads(line)
            except json.JSONDecodeError:
                continue
            if u.get("text") and u.get("source_url"):
                yield {"text": u["text"], "source": u["source_url"],
                       "type": u.get("type", "statement"), "keywords": u.get("keywords") or [],
                       "origin": f"docset:{ref.parent.name}"}
    tdir = Path(topical_dir) if topical_dir else None
    if tdir and tdir.is_dir():
        for uf in sorted(tdir.glob("*.llms/units.jsonl")):
            for line in uf.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    u = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if u.get("text") and u.get("source_url"):
                    yield {"text": u["text"], "source": u["source_url"],
                           "type": u.get("type", "statement"), "keywords": u.get("keywords") or [],
                           "origin": f"topical:{uf.parent.name}"}


def mirror_sentences(pats: dict[str, re.Pattern], entries=None, max_per_term: int = 40):
    """Sentences from the llms-full mirror that name a term, anchored to the
    page's `Source:` URL. One pass per file; stops per term at max_per_term."""
    import llms_acquire
    import llms_full_catalog

    counts: Counter = Counter()
    for e in (entries if entries is not None else llms_full_catalog.list_entries(min_pages=1)):
        path = Path(e.get("file") or "")
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not any(p.search(text) for p in pats.values()):
            continue
        for page in llms_acquire.split_llms_full(text):
            body = page.get("text") or ""
            for key, pat in pats.items():
                if counts[key] >= max_per_term or not pat.search(body):
                    continue
                for sent in _SENT_RE.split(" ".join(body.split())):
                    if (40 <= len(sent) <= 400 and pat.search(sent)
                            and not sent.startswith(("|", "#"))):
                        yield key, {"text": sent, "source": page["url"], "type": "statement",
                                    "keywords": [], "origin": f"mirror:{e['key']}"}
                        counts[key] += 1
                        if counts[key] >= max_per_term:
                            break


def _normtext(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip().rstrip(".")


def family_tokens(pool: list[dict], n: int = FAMILY_TOKENS) -> set[str]:
    """The pool's most frequent content tokens — what "on topic" means for
    this family. Research evidence that shares none of them is the same
    word in another world (a `page.md` API property, a `/map` data type)."""
    c: Counter = Counter()
    for r in pool:
        for w in _tokens(r["text"]):
            if w not in _STOPWORDS and len(w) > 2:
                c[w] += 1
    return {w for w, _ in c.most_common(n)}


def on_topic(text: str, term: dict, fam: set[str], floor: int = MIN_FAMILY_OVERLAP) -> bool:
    own = _tokens(" ".join([term["term"], *term["aka"]]))
    return len((_tokens(text) & fam) - own) >= floor


def research(pool: list[dict], terms: list[dict], mirror_dir: Path | None = None,
             topical_dir: Path | None = None, mirror_entries=None, log=print) -> list[dict]:
    """For every term the pool cannot define, gather up to MAX_RESEARCH_UNITS
    evidence units from the estate (docset facts layers, other topical
    files, the llms-full mirror) and add them to the pool as records — the
    grounded model pass then defines from them like any other evidence."""
    undefined = [t for t in terms if not _definition_from(evidence(pool, t), t)]
    if not undefined:
        return []
    pats = _term_patterns(undefined)
    by_key = {t["key"]: t for t in undefined}
    fam = family_tokens(pool)
    per_term: dict[str, list[dict]] = {t["key"]: [] for t in undefined}
    seen = {_normtext(r["text"]) for r in pool}
    dropped = 0

    def take(key: str, u: dict) -> None:
        nonlocal dropped
        if len(per_term[key]) >= MAX_RESEARCH_UNITS or _normtext(u["text"]) in seen:
            return
        if not on_topic(u["text"], by_key[key], fam):
            dropped += 1
            return
        per_term[key].append(u)
        seen.add(_normtext(u["text"]))
    for u in estate_units(mirror_dir, topical_dir):
        for key, pat in pats.items():
            if pat.search(u["text"]):
                take(key, u)
    open_keys = {k for k, v in per_term.items() if len(v) < MAX_RESEARCH_UNITS}
    if open_keys:
        for key, u in mirror_sentences({k: pats[k] for k in open_keys}, mirror_entries):
            take(key, u)
    added = []
    seq = len(pool) + 1
    for units in per_term.values():
        for u in units:
            r = _rec(seq, u["type"], u["text"], u["source"], keywords=u["keywords"],
                     origin=u["origin"])
            r["research"] = True
            if _DEF_RE.match(r["text"]):
                r["type"] = "definition"   # "X is a …" sentences rank first as evidence
            added.append(r)
            seq += 1
    log(f"research: {len(undefined)} undefined terms, {len(added)} evidence units found "
        f"({sum(1 for v in per_term.values() if v)} terms with evidence; {dropped} off-topic "
        f"matches dropped)")
    return added


def queue_undefined(entries: list[dict], subject: str) -> int:
    """Terms still undefined after research go to the concept research queue
    under the subject — the hand-off to /dr."""
    import concept_tree as ct
    n = 0
    for e in entries:
        if (not e["definition"] and e["kind"] != "concept"
                and ct.queue_concept(f"{e['term']} (term of {subject})", subject)):
            n += 1
    return n


# --------------------------------------------------------------------------- #
# optional model pass (verified)
# --------------------------------------------------------------------------- #

LLM_PROMPT = """You write ONE vocabulary entry for a technical glossary from evidence.

Term: {term}
Known spellings: {aka}

Evidence (numbered; the ONLY facts you may use):
{evidence}

Rules:
- Output ONLY a JSON object:
  {{"definition": "...", "differs_from": [{{"term": "...", "how": "..."}}], "aka": ["..."]}}
- definition: one sentence, ≤ 30 words, what the term IS, taken from the evidence.
- differs_from: terms the evidence explicitly contrasts with this one (else []); "how" ≤ 15 words.
- aka: alternative names that literally appear in the evidence (else []).
- Never invent a name, number or claim that is not in the evidence."""


GROUND_FLOOR = 0.6   # share of a model sentence's content tokens that must occur in the evidence


def llm_entry(term: dict, units: list[dict], generate=None, model: str | None = None,
              timeout: int = 180, floor: float = GROUND_FLOOR) -> dict:
    """Model-written definition/differentiator, then verified: every name in
    aka/differs_from must literally appear in the evidence, and the
    definition must share ≥ 3 content tokens with it."""
    if generate is None:
        from semantic_ops import llm
        generate = llm.generate
    from .units import llm_options, parse_reply  # noqa: F401  (same JSON tolerance)
    ev = "\n".join(f"{i}. {u['text']}" for i, u in enumerate(units, 1))
    prompt = LLM_PROMPT.format(term=term["term"], aka=", ".join(term["aka"]) or "—",
                               evidence=ev)
    reply = generate(prompt, model=model, timeout=timeout, options=llm_options(prompt),
                     think=False)
    m = re.search(r"\{.*\}", reply, re.S)
    if not m:
        return {}
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}
    evl = ev.lower()
    ev_tokens = _tokens(ev)

    def grounding(text: str) -> float:
        """Share of the sentence's content tokens that occur in the evidence —
        paraphrase scores high, invention low."""
        toks = {w for w in _tokens(text) if w not in _STOPWORDS and len(w) > 2}
        return len(toks & ev_tokens) / len(toks) if toks else 0.0

    def grounded(text: str, floor: float = floor) -> bool:
        return grounding(text) >= floor

    out: dict = {}
    d = str(data.get("definition") or "").strip()
    if d and grounded(d):
        out["definition"] = d
        out["grounding"] = round(grounding(d), 2)
    out["differs_from"] = [x for x in data.get("differs_from") or []
                           if isinstance(x, dict) and str(x.get("term", "")).lower() in evl
                           and normalise(str(x.get("term", ""))) != term["key"]
                           and grounded(str(x.get("how", "")), min(floor, 0.5))]
    # an alias the model proposes must sit next to an alias cue in the evidence
    out["aka"] = [a for a in data.get("aka") or []
                  if isinstance(a, str) and normalise(a) != term["key"]
                  and re.search(r"(?:aka|also called|also known as|a\.k\.a\.|i\.e\.|or)\s+"
                                r"(?:the |a |an )?`?" + re.escape(a.lower()), evl)]
    return out


# --------------------------------------------------------------------------- #
# build
# --------------------------------------------------------------------------- #


def build_entries(pool: list[dict], terms: list[dict], llm=None) -> list[dict]:
    entries = []
    for t in terms:
        ev = evidence(pool, t)
        if not ev and t["kind"] != "concept":
            continue
        dfn = _definition_from(ev, t)
        entry = {"term": t["term"], "key": t["key"], "kind": t["kind"], "node": t["node"],
                 "aka": list(t["aka"]) + [a for a in _aka_in_text(ev, t) if a not in t["aka"]],
                 "definition": dfn["text"] if dfn else "",
                 "definition_source": dfn["source"] if dfn else "",
                 "not": [{"term": c["term"], "source": c["unit"]["source"], "how": c["how"]}
                         for c in _contrasts(ev, t, terms)],
                 "evidence": len(ev), "origin": "extractive" if dfn else ""}
        if llm is not None and ev and (not entry["definition"] or not entry["not"]):
            got = llm(t, ev)
            if got.get("definition") and not entry["definition"]:
                entry["definition"] = got["definition"]
                entry["definition_source"] = ev[0]["source"]
                entry["origin"] = "llm"
                entry["grounding"] = got.get("grounding", 0.0)
            for x in got.get("differs_from", []):
                if normalise(x["term"]) != t["key"] and all(
                        normalise(x["term"]) != normalise(n["term"]) for n in entry["not"]):
                    entry["not"].append({"term": x["term"], "source": ev[0]["source"],
                                         "how": str(x.get("how", ""))[:160], "origin": "llm"})
            for a in got.get("aka", []):
                if a not in entry["aka"]:
                    entry["aka"].append(a)
        entries.append(entry)
    return entries


def render(subject: str, entries: list[dict], generated: str) -> str:
    # A `- **term** …` line under `## Terms` is a *defined* term, and every one of
    # them ends in the URL its definition came from (llms_lint P7 reads the file
    # that way and flags a bold line with no source). A term the pool only names
    # is not a term line: it appears once, as a plain bullet, in the tail below.
    defined: list[dict] = []
    undefined: list[dict] = []
    for e in entries:
        (defined if e["definition"] and e["definition_source"] else undefined).append(e)
    n_def = len(defined)
    out = [f"# {subject} — vocabulary", "",
           f"> Terms of this niche, one per line: canonical name, definition, how it differs "
           f"from its neighbours (`not:`), and the words people use instead (`aka:`). "
           f"Read before the index when a term is unfamiliar. {len(entries)} terms, "
           f"{n_def} with a definition; each line ends in the URL its definition came from.",
           "", f"<!-- generated by docset_refine vocabulary v1 · {len(entries)} terms · "
           f"{generated} -->", "", "## Terms", ""]
    for e in defined:
        line = f"- **{e['term']}**"
        line += f" — {e['definition']}"
        if e["aka"]:
            line += " · aka: " + ", ".join(e["aka"])
        if e["not"]:
            line += " · not: " + ", ".join(x["term"] for x in e["not"])
        diffs = [x["how"] for x in e["not"] if x.get("how")]
        if diffs:
            line += f" · differs: {diffs[0]}"
        line += f" — {e['definition_source']}"
        if e.get("researched"):
            line += " · evidence: hub estate"
        if e.get("origin") == "llm":
            g = e.get("grounding", 0.0)
            line += (f" · origin: llm (grounded {g:.2f}"
                     + (", verify before citing)" if g < GROUND_FLOOR else ")"))
        out.append(line)
    if undefined:
        out += ["", "## Named, not yet defined", "",
                "Terms the pool names (≥ 2 uses) without a sourced sentence that defines "
                "them — research gaps."]
        out += [f"- {e['term']}"
                + (f" — {e['definition']}" if e["definition"] else "")
                + (f" · aka: {', '.join(e['aka'])}" if e["aka"] else "")
                for e in undefined]
    return "\n".join(out).rstrip() + "\n"


def register_aliases(tree, entries: list[dict], subject: str) -> int:
    """Merge each concept-kind term's aka: into its tree node's `aliases`
    (add-only). Returns how many aliases were added."""
    import concept_tree as ct

    added = 0
    for e in entries:
        node = tree.by_concept.get(e["node"]) if e["node"] else None
        if node is None:
            continue
        aliases = node.setdefault("aliases", [])
        for a in e["aka"]:
            if a not in aliases and normalise(a) != normalise(node["concept"]):
                aliases.append(a)
                added += 1
    if added:
        ct.save_nodes(tree.nodes)
    return added


def run(pool_paths: list[Path], subject: str, out_dir: Path, tree=None, llm=None,
        register: bool = False, do_research: bool = False, queue: bool = False,
        mirror_dir: Path | None = None, topical_dir: Path | None = None,
        mirror_entries=None, log=print) -> dict:
    import concept_tree as ct

    tree = tree or ct.ConceptTree.load()
    ct.ensure_slugs(tree.nodes)
    pool, rejected = load_pool([Path(p) for p in pool_paths])
    pool = dedupe(pool)
    terms = candidates(pool, tree, subject)
    researched = 0
    if do_research:
        extra = research(pool, terms, mirror_dir, topical_dir, mirror_entries, log=log)
        pool = pool + extra
        researched = len(extra)
    entries = build_entries(pool, terms, llm=llm)
    research_srcs = {r["source"] for r in pool if r.get("research")}
    for e in entries:                       # provenance: evidence came from the estate
        if e.get("definition_source") in research_srcs:
            e["researched"] = True
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    generated = datetime.now().date().isoformat()
    text = render(subject, entries, generated)
    (out_dir / "llms-vocabulary.txt").write_text(text, encoding="utf-8")
    (out_dir / "vocabulary.json").write_text(
        json.dumps({"subject": subject, "generated": generated, "terms": entries},
                   indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    man_path = out_dir / "manifest.json"
    manifest = {}
    if man_path.exists():
        try:
            manifest = json.loads(man_path.read_text())
        except (OSError, json.JSONDecodeError):
            manifest = {}
    manifest.setdefault("files", {})["llms-vocabulary.txt"] = {
        "bytes": len(text.encode()), "tokens": max(1, len(text) // CHARS_PER_TOKEN)}
    manifest["vocabulary"] = {"terms": len(entries),
                              "defined": sum(1 for e in entries if e["definition"]),
                              "llm": sum(1 for e in entries if e.get("origin") == "llm"),
                              "researched": sum(1 for e in entries if e.get("researched")),
                              "research_units": researched,
                              "generated": generated}
    man_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    added = register_aliases(tree, entries, subject) if register else 0
    queued = queue_undefined(entries, subject) if queue else 0
    log(f"vocabulary: {len(entries)} terms ({manifest['vocabulary']['defined']} defined, "
        f"{manifest['vocabulary']['llm']} by llm, {manifest['vocabulary']['researched']} from "
        f"estate research) → {out_dir / 'llms-vocabulary.txt'}; {added} aliases registered; "
        f"{queued} queued for research")
    return manifest["vocabulary"] | {"aliases_added": added, "queued": queued,
                                     "rejected": len(rejected)}
