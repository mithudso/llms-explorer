#!/usr/bin/env python3
"""build_llms — the site's own llms family, generated from its .md twins.

Writes a banner mirror of every twin under dist/, runs the vendored
docset_refine chain over it (clean → extract → render → export → vocabulary;
no model tokens), copies the family into dist/, refreshes _headers and lints
every file. Hand inputs live in site/llms.overrides.json, never in the output.

Three things this site does that a crawled docset does not need, all of them
here rather than in the vendored chain: the route decides a page's class
(`_classify_twin`), the authored section order decides the page order
(`order_pages`), and the units that page templates produce are dropped before
they reach the fact and vocabulary layers (`filter_units`).

Exit 1 on any High finding, or above `--max-medium` Mediums.

Usage: build_llms.py [--dist dist] [--site-url URL] [--work .llms-work]
                     [--max-medium N]
"""
from __future__ import annotations

import argparse
import contextlib
import json
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parents[1]                 # site/
REPO = HERE.parent
sys.path.insert(0, str(REPO / "hub" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import concept_tree as ct
import llms_lint
import twins
from docset_refine import (
    clean,
    export_llms,
    extract,
    reference_dir,
    render,
    vocabulary,
)

BANNER = "=" * 10
FILES = ("llms.txt", "llms-full.txt", "llms-small.txt", "llms-facts.txt", "manifest.json")
VOCAB = "llms-vocabulary.txt"
FACTS = "llms-facts.txt"
SUBJECT = "LLMS-Explorer"
TREE_DIR = REPO / "concept-tree"
OVERRIDES = HERE / "llms.overrides.json"
# `/reference/`, `/essays/` and `/examples/` are the durable layers — the spec,
# the reasoning and the how-to recipes. llms-small.txt is "the reference layers
# within ~50k tokens", so they are the reference class and the blog is not;
# with everything a guide, the alphabetically-first blog filled the budget and
# all 13 recipes were dropped from the file that claims to carry them.
REFERENCE_SECTIONS = ("reference", "essays", "examples")
# H2s the page templates repeat (recipes: Goal/Steps/Cost/Expected output;
# posts: Problem/Inputs/Outputs/Reproduce/…). extract types the first paragraph
# under every heading as a `definition`; under these it defines nothing — the
# heading is furniture, and the paragraph is a step or a lead-in. Left in, they
# reach llms-facts.txt as `- [definition] Problem — …` and become the raw
# material llms-vocabulary.txt publishes as terms of the niche.
TEMPLATE_HEADINGS = frozenset({
    "problem", "inputs", "commands", "outputs", "what the lint found", "lessons",
    "reproduce", "goal", "steps", "cost", "what it does", "expected output",
    "when not to use it", "references", "run", "why",
})
# …and any heading repeated on this many pages is furniture too, whatever it is
# called: one page's heading is a claim, ten pages' is a template slot.
TEMPLATE_MIN_PAGES = 3
# a definition body that is a numbered step ("1. Run the lint.") is a procedure,
# not a definition of its heading
_STEP_BODY_RE = re.compile(r"^\d+[.)]\s")
# The build fails on any High (the CI gate). It cannot fail on any Medium: this
# site is table-heavy, so llms-facts.txt sits above P5 S4's 0.30 facts/full
# ratio — the rubric and evidence tables ARE the content, and cutting their rows
# to two columns to buy the ratio would make the fact layer less true. The
# remaining Mediums are held at a ceiling instead, so a regression fails.
# Medium budget, per file linted. The Mediums this family genuinely accepts are
# S4 (facts/full ratio) on llms-facts.txt and P4 (steer) on llms-full.txt and
# llms-small.txt, which quote the forbidden phrasings from reference/ethos.md —
# plus C3 residue. A section file inherits none of those: its one Medium was P1
# (no provenance banner), a defect, and `build()` now stamps every spoke, so the
# budget is back to 1.0 per file rather than the 1.5 that quietly left room for
# five more.
MAX_MEDIUM_PER_FILE = 1.0
# provenance comments (`<!-- hand page · … -->`) and figure markers
# (`<!-- fig:x.pages --> 191`) are authoring metadata, not page text; left in,
# the first one becomes the page's index description
_LINE_COMMENT_RE = re.compile(r"^[ \t]*<!--.*?-->[ \t]*\n?", re.MULTILINE | re.DOTALL)
_FIG_MARK_RE = re.compile(r"<!--\s*fig:[^>]*-->\s*")
_VOCAB_SRC_RE = re.compile(r" — https?://\S+")


def clean_body(body: str) -> str:
    return _FIG_MARK_RE.sub("", _LINE_COMMENT_RE.sub("", body))


def write_mirror(dist: Path, site_url: str, out: Path) -> int:
    """One banner block per twin: `==========\\nURL: <site_url><route>\\n==========\\n<body>`."""
    parts = []
    for twin in sorted(Path(dist).rglob("*.md")):
        if twin.name.startswith("llms"):
            continue
        route = "/" + twin.relative_to(dist).with_suffix("").as_posix() + "/"
        body = clean_body(twin.read_text(encoding="utf-8").split("-->\n", 1)[-1]).lstrip()
        parts.append(f"{BANNER}\nURL: {site_url}{route}\n{BANNER}\n{body}\n")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(parts), encoding="utf-8")
    return len(parts)


def _classify_twin(url: str, text: str, *, policy=None) -> str:
    """Every twin is an authored content page. clean's URL heuristics were built
    for crawled third-party sites (a `/blog/` segment is marketing, a short page
    is a link farm, a `changelog` segment is a release log) and would drop or
    misfile the site's own pages; the route decides instead.

    `clean.FIRST_PARTY` (added to the hub after this workaround) fixes the
    dropping, but it tunes thresholds and segment sets — it cannot express a
    rule keyed on the FIRST path segment, which is what ranks this site's
    durable layers ahead of its blog. So the patch stays, and it accepts and
    ignores the `policy=` keyword `clean.run` now passes.

    The class only ranks pages for llms-small.txt (`build_small` takes the
    reference class first), so the durable layers — reference, essays,
    examples — are all `reference`; the blog is the guide layer that gets cut
    when the budget runs out."""
    segs = [s for s in urlparse(url).path.split("/") if s]
    return "reference" if segs and segs[0] in REFERENCE_SECTIONS else "guide"


@contextlib.contextmanager
def _twin_classifier():
    orig = clean.classify
    clean.classify = _classify_twin
    try:
        yield
    finally:
        clean.classify = orig


def order_pages(mirror: Path, section_order: list[str] | None) -> list[str]:
    """Put `pages.json` in the authored section order (llms.overrides.json).

    Every downstream file walks pages in this order: llms-full.txt renders
    them in it, and llms-small.txt re-sorts its kept pages back into it
    (`build_small`: `kept.sort(key=lambda p: pages.index(p))`). Left in mirror
    order — alphabetical by route — both files opened with the blog while the
    index opened with Reference. Returns the section names in the order used."""
    ref = reference_dir(mirror)
    path = ref / "pages.json"
    pages = json.loads(path.read_text(encoding="utf-8"))
    ranks = {s.lower(): i for i, s in enumerate(section_order or [])}

    def section(p: dict) -> str:
        segs = [s for s in urlparse(p.get("url", "")).path.split("/") if s]
        return segs[0] if segs else ""

    order = sorted(range(len(pages)),
                   key=lambda i: (ranks.get(section(pages[i]).lower(), len(ranks)), i))
    pages = [pages[i] for i in order]
    path.write_text(json.dumps(pages, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    seen: list[str] = []
    for p in pages:
        if section(p) not in seen:
            seen.append(section(p))
    return seen


def _heading_label(unit: dict) -> str:
    """The heading a `definition` unit was cut under (`<heading> — <body>`)."""
    kws = unit.get("keywords") or []
    return (kws[0] if kws else unit.get("text", "").split(" — ", 1)[0]).strip()


def template_headings(units: list[dict]) -> set[str]:
    """Case-folded headings that are page furniture: named in TEMPLATE_HEADINGS,
    or repeated on TEMPLATE_MIN_PAGES or more pages."""
    pages_by_heading: dict[str, set[str]] = defaultdict(set)
    for u in units:
        if u.get("origin") == "heading":
            pages_by_heading[_heading_label(u).casefold()].add(u.get("source_url", ""))
    return {h for h, pages in pages_by_heading.items()
            if h in TEMPLATE_HEADINGS or len(pages) >= TEMPLATE_MIN_PAGES}


def is_template_unit(unit: dict, headings: set[str]) -> bool:
    """A heading-derived unit that defines nothing: the heading is a template
    slot, or the body under it is a numbered step."""
    if unit.get("origin") != "heading":
        return False
    heading = _heading_label(unit)
    if heading.casefold() in headings:
        return True
    body = unit.get("text", "").split(" — ", 1)[-1].strip()
    return bool(_STEP_BODY_RE.match(body))


def filter_units(units_path: Path) -> dict:
    """Drop the template-heading units from `all_units.jsonl` — the pool both
    llms-facts.txt and llms-vocabulary.txt are built from — and renumber what
    is left (ids must stay unique). `structured.jsonl` keeps them: the index
    descriptions in llms.txt are the first heading unit of each page
    (`export_llms._definitions`), and on a recipe that is its `## Goal`."""
    units = [json.loads(ln) for ln in units_path.read_text(encoding="utf-8").splitlines() if ln]
    headings = template_headings(units)
    kept = [u for u in units if not is_template_unit(u, headings)]
    for n, u in enumerate(kept, 1):
        u["id"] = f"u{n:06d}"
    units_path.write_text(
        "".join(json.dumps(u, ensure_ascii=False) + "\n" for u in kept), encoding="utf-8")
    return {"units": len(kept), "dropped": len(units) - len(kept),
            "template_headings": sorted(headings)}


def provenance(date: str) -> str:
    """The banner the lint looks for (P9 P1) and the reader needs: who built
    this file, from what, and when. `docset_refine` runs here, in the site's
    own `postbuild`, over the page twins — not on the hub."""
    return (f"<!-- generated {date} by site/tools/build_llms.py from the .md twin "
            "of every page in this site's build output -->")


def stamp(path: Path, banner: str) -> str:
    """Insert `banner` after the leading H1 + blockquote of a family file."""
    text = path.read_text(encoding="utf-8")
    if banner in text:
        return text
    lines = text.splitlines()
    at = 0
    for i, ln in enumerate(lines[:12]):
        if ln.startswith(("# ", ">")):
            at = i + 1
    text = "\n".join(lines[:at] + ["", banner] + lines[at:]).rstrip() + "\n"
    path.write_text(text, encoding="utf-8")
    return text


def _resize(out_dir: Path, name: str) -> None:
    """Re-record a file's size in manifest.json after it was edited in place
    (H8: the manifest and the bytes on disk must not drift)."""
    man, path = out_dir / "manifest.json", out_dir / name
    if not (man.exists() and path.exists()):
        return
    manifest = json.loads(man.read_text(encoding="utf-8"))
    text = path.read_text(encoding="utf-8")
    manifest.setdefault("files", {})[name] = {
        "bytes": len(text.encode("utf-8")),
        "tokens": max(1, len(text) // export_llms.CHARS_PER_TOKEN)}
    man.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def _site_overrides() -> dict | None:
    if not OVERRIDES.exists():
        return None
    data = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if k in export_llms.OVERRIDE_KEYS}


def _load_tree() -> ct.ConceptTree:
    """The vendored tree only — queue and research state are hub run-state and
    are pointed at paths that do not exist here, so nothing reads ~/.global-ai-hub."""
    return ct.ConceptTree.load(TREE_DIR / "tree.json", TREE_DIR / "RESEARCH_QUEUE.md",
                               TREE_DIR / "research_state.json")


def is_definition(line: str) -> bool:
    """False for a `## Terms` line whose definition does not define its term.

    The blockquote tells the reader to trust this file before the index, so a
    term line has to be a definition. Three shapes are not: one that only
    repeats the term (`- **Inputs** — Inputs — …`), one whose body is a step of
    a procedure (`- **Run** — Migrating a v1 file — 1. Run the lint.`), and one
    that is a lead-in whose claim is in the block below it (`… shown:`)."""
    m = re.match(r"- \*\*(?P<term>.+?)\*\*\s*(?:\([^)]*\))?\s*(?:[:—]\s*)?(?P<rest>.*)$", line)
    if not m:
        return True
    definition = _VOCAB_SRC_RE.split(m["rest"])[0].strip()
    parts = [p.strip() for p in definition.split(" · ")[0].split(" — ") if p.strip()]
    if not parts:
        return False
    if parts[0].casefold() == m["term"].strip().casefold():
        return False
    return not (parts[-1].endswith(":") or any(_STEP_BODY_RE.match(p) for p in parts))


GAPS = "## Named, not yet defined"


def publish_vocabulary(text: str) -> str:
    """vocabulary.render lists every term under `## Terms`, defined or not; a
    bold line with no ` — url` is a lint High (P7 C6). The undefined ones are
    already listed under `## Named, not yet defined`, so drop them here. A term
    whose definition does not define it (`is_definition`) is demoted into that
    same section — named, not yet defined is exactly what it is — and the two
    counts in the header are rewritten to what the file actually carries."""
    out, in_terms, demoted = [], False, []
    for ln in text.splitlines():
        if ln.startswith("## "):
            in_terms = ln == "## Terms"
        if in_terms and ln.startswith("- **"):
            if not _VOCAB_SRC_RE.search(ln):
                continue
            if not is_definition(ln):
                demoted.append(ln.split("**")[1])
                continue
        out.append(ln)
    if demoted:
        if GAPS not in out:
            out += ["", GAPS, "",
                    "Terms the pool names without a sentence that defines them — research gaps."]
        out += [f"- {t}" for t in demoted]
    cut = out.index(GAPS) if GAPS in out else len(out)
    defined = sum(1 for ln in out[:cut] if ln.startswith("- **"))
    total = defined + sum(1 for ln in out[cut:] if ln.startswith("- "))
    text = "\n".join(out).rstrip() + "\n"
    text = re.sub(r"\b\d+ terms, \d+ with a definition",
                  f"{total} terms, {defined} with a definition", text, count=1)
    return re.sub(r"(vocabulary v1 · )\d+( terms)", rf"\g<1>{total}\g<2>", text, count=1)


def build_vocabulary(units: Path, out_dir: Path) -> dict:
    """llms-vocabulary.txt from the deterministic units; returns vocabulary.run's
    summary plus `published` (False when no term carries a definition — a file
    with no term lines is a lint High, not a vocabulary)."""
    info = vocabulary.run([units], SUBJECT, out_dir, tree=_load_tree(), llm=None,
                          log=lambda *_: None)
    info["published"] = bool(info.get("defined")) and (out_dir / VOCAB).exists()
    man = out_dir / "manifest.json"
    manifest = json.loads(man.read_text(encoding="utf-8")) if man.exists() else {}
    files = manifest.setdefault("files", {})
    if info["published"]:
        text = publish_vocabulary((out_dir / VOCAB).read_text(encoding="utf-8"))
        # publish_vocabulary demotes the terms whose definition does not define;
        # the manifest states what the file carries, not what render offered
        info["defined"] = sum(1 for ln in text.splitlines() if ln.startswith("- **"))
        info["published"] = bool(info["defined"])
        manifest.setdefault("vocabulary", {})["defined"] = info["defined"]
        (out_dir / VOCAB).write_text(text, encoding="utf-8")
    if info["published"]:
        files[VOCAB] = {"bytes": len(text.encode("utf-8")),           # H8: no drift
                        "tokens": max(1, len(text) // vocabulary.CHARS_PER_TOKEN)}
    else:
        files.pop(VOCAB, None)
    man.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return info


def build(dist: Path, site_url: str, work: Path, today: str | None = None) -> dict:
    dist, work = Path(dist), Path(work)
    work.mkdir(parents=True, exist_ok=True)
    mirror = work / "site.md"
    write_mirror(dist, site_url, mirror)
    # a <stem>.llms.overrides.json beside the mirror wins for the hand inputs
    # (tests drop one there); otherwise site/llms.overrides.json is read fresh
    # on every build. The provenance banner is added on top of either: it is
    # generated, so it cannot live in a hand file.
    sibling = work / "site.llms.overrides.json"
    overrides = dict(json.loads(sibling.read_text(encoding="utf-8")) if sibling.exists()
                     else (_site_overrides() or {}))
    # local date, to agree with the stamp vocabulary.render puts on llms-vocabulary.txt
    banner = provenance(today or datetime.now().date().isoformat())  # noqa: DTZ005
    overrides["note"] = "\n\n".join(x for x in (overrides.get("note"), banner) if x)
    with _twin_classifier():
        clean.run(mirror)
    order_pages(mirror, overrides.get("section_order"))
    extract.run(mirror)
    render.run(mirror)
    filtered = filter_units(reference_dir(mirror) / "all_units.jsonl")
    export_llms.run(mirror, overrides=overrides)
    out_dir = work / "site.llms"
    if (out_dir / FACTS).exists():           # llms.txt carries the banner in its note
        stamp(out_dir / FACTS, banner)
    units = reference_dir(mirror) / "all_units.jsonl"
    vocab = {"published": False}
    if units.exists() and units.stat().st_size:
        vocab = build_vocabulary(units, out_dir)
    _resize(out_dir, FACTS)
    # Every published file carries the provenance banner, not just the root: the
    # section indexes are what the root index sends a reader to, and P1 applies
    # to all of them (five spokes, five P1 Mediums, before this). Stamped and
    # re-measured (H8) before manifest.json is copied, or dist's manifest would
    # record the pre-banner bytes.
    spokes = sorted(out_dir.rglob("*/llms.txt"))              # hub-and-spoke split, if any
    for spoke in spokes:
        stamp(spoke, banner)
        _resize(out_dir, spoke.relative_to(out_dir).as_posix())
    for name in FILES:
        if (out_dir / name).exists():
            shutil.copy(out_dir / name, dist / name)
    if vocab["published"]:
        shutil.copy(out_dir / VOCAB, dist / VOCAB)
    for spoke in spokes:
        dest = dist / spoke.relative_to(out_dir)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(spoke, dest)
    twins.write_headers(dist)
    counts = {"high": 0, "medium": 0, "files": 0, "units": filtered, "vocabulary": vocab}
    targets = [dist / n for n in FILES if n != "manifest.json"] + [dist / VOCAB]
    targets += sorted(dist.rglob("*/llms.txt"))
    for f in targets:
        if not f.exists():
            continue
        c = llms_lint.check(f, mirror=mirror)["counts"]
        counts["high"] += c["high"]
        counts["medium"] += c["medium"]
        counts["files"] += 1
    return counts


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dist", default="dist")
    p.add_argument("--site-url", default=None,
                   help="default: $SITE_URL, else the twins.py fallback")
    p.add_argument("--work", default=".llms-work")
    p.add_argument("--max-medium", type=int, default=None,
                   help="fail above this many Medium findings "
                        f"(default: {MAX_MEDIUM_PER_FILE} x the number of files linted); "
                        "-1 to only gate on High")
    a = p.parse_args(argv)
    site_url = (a.site_url or twins.default_site_url()).rstrip("/")
    counts = build(HERE / a.dist, site_url, HERE / a.work)
    print(json.dumps(counts))
    if counts["high"]:
        return 1
    budget = (a.max_medium if a.max_medium is not None
              else int(MAX_MEDIUM_PER_FILE * max(1, counts.get("files", 1))))
    if 0 <= budget < counts["medium"]:
        print(f"{counts['medium']} Medium findings across {counts.get('files', '?')} files "
              f"(> {budget})", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
