#!/usr/bin/env python3
"""gen_concept_facts — one plain-markdown facts file per concept pack.

/tree/<slug>/ renders a pack's facets and source-anchored facts as HTML. An
agent should not have to parse that page: this writes the same content as
`public/downloads/concepts/<slug>.md`, which Astro copies byte-for-byte into
the build, the `/*.md` header rule serves as text/markdown, and the
`/context.md` twin lists — so a concept's facts are one fetch from the index.

Why a download and not a `.md` twin of the node page: reference/usage.md
promises the per-row pages carry no twin (hundreds of twins would repeat
what the section twin's inventory carries and enter llms-full.txt), and
build_llms.py already keeps `downloads/` out of that family. The token
estimate a twin's header would carry goes in the banner comment instead.

Deterministic: the only date is the pack's own `generated`; generated concept
files are rebuilt so a removed pack cannot linger. Authored paper evidence and
released figures live in research subdirectories and survive regeneration.

Usage: gen_concept_facts.py [--out public/downloads/concepts] [--site-url URL]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parents[1]                  # site/
DEFAULT_CONCEPTS = HERE / "src" / "data" / "concepts"
DEFAULT_TREE = HERE / "src" / "data" / "tree.json"
DEFAULT_SOURCES = HERE / "src" / "content" / "sources"
DEFAULT_OUT = HERE / "public" / "downloads" / "concepts"
# research_site_sync loads this file by absolute path from other checkouts.
# Load its sibling policy by path as well; do not depend on global sys.path/cache.
_origin_spec = importlib.util.spec_from_file_location(
    "_llmsx_site_origin", HERE / "tools/site_origin.py")
assert _origin_spec is not None and _origin_spec.loader is not None
_origin = importlib.util.module_from_spec(_origin_spec)
_origin_spec.loader.exec_module(_origin)
DEFAULT_SITE_URL = _origin.DEFAULT_SITE_URL


def default_site_url() -> str:
    return _origin.default_site_url()


CHARS_PER_TOKEN = 4                                         # the family's estimator
SOURCE_URL_RE = re.compile(r"^https?://[^/]+/sources/([^/]+)/([^/#?]+)/")
FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def _md_text(s: object) -> str:
    """Fact text is prose, but a stray `]` or newline would break the list."""
    return " ".join(str(s or "").split())


def _source_title(sources_dir: Path, hub: str, name: str) -> str:
    f = sources_dir / hub / f"{name}.md"
    if not f.is_file():
        return name
    m = FM_RE.match(f.read_text(encoding="utf-8"))
    if not m:
        return name
    t = re.search(r"^title:\s*(.+)$", m.group(1), re.MULTILINE)
    return t.group(1).strip().strip("'\"") if t else name


def render_facts(facts: list[dict]) -> str:
    """Nested `level` becomes indented markdown bullets; packs without a
    `level` field (the gen_concepts.py ones) render flat, as the page does."""
    lines = []
    for fact in facts:
        level = int(fact.get("level") or 0)
        text = _md_text(fact.get("text"))
        src = str(fact.get("source") or "").strip()
        line = f"{'  ' * level}- {text}"
        # a URL becomes a link; a local path (the older packs cite files under
        # ~/.claude) is shown verbatim in code, since a link to it resolves nowhere
        if src.startswith(("http://", "https://")) and not re.match(
                r"https?://(?:llms-explorer\.com|llmsx\.org)/sources/", src):
            line += f" — [source]({src})"
        elif src:
            line += f" — source: `{src}`"
        for secondary in dict.fromkeys(fact.get("also") or []):
            if not secondary or secondary == src:
                continue
            if secondary.startswith(("http://", "https://")) and not re.match(
                    r"https?://(?:llms-explorer\.com|llmsx\.org)/sources/", secondary):
                line += f" · [also]({secondary})"
            else:
                line += f" · also: `{secondary}`"
        if fact.get("note"):
            line += f" *({_md_text(fact['note'])})*"
        lines.append(line)
    return "\n".join(lines)


def narrative_source_url(value: object) -> bool:
    """Only safe web references become links; rejected paths are never printed."""
    if (not isinstance(value, str) or not value.startswith(("https://", "http://"))
            or re.search(r'[\x00-\x20\x7f<>"`\\]', value)):
        return False
    try:
        parsed = urlsplit(value)
        _ = parsed.port  # Reject malformed ports as the browser URL parser does.
        archived = (parsed.hostname in ("llms-explorer.com", "llmsx.org")
                    and parsed.path.startswith("/sources/"))
        return bool(parsed.hostname and not parsed.username
                    and not parsed.password and not archived)
    except ValueError:
        return False


def render_narrative(narrative: list[dict]) -> str:
    """Complete gated auxiliary assertions, outside factual rows and counts."""
    lines = []
    for assertion in narrative:
        status = assertion["validationStatus"]
        original_status = assertion.get("originValidationStatus", status)
        kind = assertion.get("assertionKind", "summary")
        label = {"disagreement": "Source disagreement", "open_question": "Open question"}.get(kind)
        if label is None:
            label = ("Proposed guidance" if original_status == "NO-FACTUAL-ASSERTION"
                     else "Research summary")
        if status == "REDACTED-PROJECTION":
            label += " (redacted projection)"
        lines += [f"## {label} — {_md_text(assertion['documentConcept'])}", "",
                  assertion["text"], "",
                  f"Gate verdict: `{status}`. Auxiliary assertion: `{assertion['assertionId']}`. "
                  f"Statement hash: `{assertion['statementSha256']}`.", ""]
        if original_status == "NO-FACTUAL-ASSERTION":
            qualifiers = {
                "open_question": (
                    "Question without a factual assertion; contributes no factual evidence."),
                "disagreement": "Nonfactual auxiliary prose; contributes no factual evidence.",
            }
            qualifier = qualifiers.get(
                kind, "Original conditional design guidance; contributes no factual evidence.")
            lines += [qualifier, ""]
        elif assertion.get("evidenceIds"):
            evidence = ", ".join(f"`{value}`" for value in assertion["evidenceIds"])
            lines += ["Evidence IDs: " + evidence + ".", ""]
        sources = [url for url in assertion.get("sources", []) if narrative_source_url(url)]
        if sources:
            links = " · ".join(f"[source {index}](<{url}>)" for index, url in enumerate(sources, 1))
            prefix = ("Context sources: " if original_status == "NO-FACTUAL-ASSERTION"
                      else "Sources: ")
            lines += [prefix + links, ""]
    return "\n".join(lines)


def render_pack(pack: dict, nodes: dict, site_url: str, sources_dir: Path) -> str:
    slug = str(pack["slug"])
    node = nodes.get(slug) or {}
    page = f"{site_url}/tree/{slug}/"
    by_name = {n["concept"].lower(): n["slug"] for n in nodes.values()}

    facets = pack.get("facets") or []
    n_facts = sum(len(f.get("facts") or []) for f in facets)
    head = [f"# {pack.get('concept') or slug}", ""]
    if pack.get("summary"):
        head += [f"> {_md_text(pack['summary'])}", ""]
    meta = []
    if node.get("parent_slug"):
        meta.append(f"Parent: [{node.get('parent')}]({site_url}/tree/{node['parent_slug']}/)")
    meta.append(f"{len(facets)} facets")
    meta.append(f"{n_facts} facts")
    meta.append(f"page: {page}")
    head += [" · ".join(meta), ""]

    body = [render_narrative(pack["narrative"])] if pack.get("narrative") else []
    for facet in facets:
        body += [f"## {_md_text(facet.get('title')) or 'Facts'}", "",
                 render_facts(facet.get("facts") or []), ""]

    related = pack.get("related") or []
    if related:
        body += ["## Related concepts", ""]
        for r in related:
            name = _md_text(r.get("concept"))
            target = by_name.get(name.lower())
            label = f"[{name}]({site_url}/tree/{target}/)" if target else name
            line = f"- {label}"
            if r.get("relation"):
                line += f" — {_md_text(r['relation'])}"
            if r.get("note"):
                line += f"; {_md_text(r['note'])}"
            body.append(line)
        body.append("")

    text = "\n".join(head + body).rstrip() + "\n"
    tokens = len(text) // CHARS_PER_TOKEN
    dated = pack.get("generated") or "undated"
    banner = f"<!-- llms-explorer concept facts · {page} · pack {dated} · ~{tokens} tokens -->\n\n"
    return banner + text


def download_texts(packs: dict, nodes: dict, redirects: dict, site_url: str,
                   sources_dir: Path) -> dict:
    """Retain published download URLs without duplicate reader/context packs."""
    texts = {slug: render_pack(pack, nodes, site_url, sources_dir) for slug, pack in packs.items()}
    for alias, target in redirects.items():
        if alias in texts:
            continue
        if Path(alias).name != alias or alias in (".", ".."):
            raise ValueError(f"Invalid facts download alias: {alias!r}")
        seen = {alias}
        while target not in texts and target in redirects:
            if target in seen:
                raise ValueError("Facts download redirect cycle")
            seen.add(target)
            target = redirects[target]
        if target in texts:
            texts[alias] = texts[target]
    return texts


def research_download_texts(packs: dict) -> dict[str, str]:
    """Recreate public canonical artifacts from committed reader data in CI."""
    result = {}
    for slug, pack in packs.items():
        if not pack.get("canonicalArtifactSha256"):
            continue
        artifact = {"schema": "research-public-artifact/v1",
                    "concept": pack["concept"], "slug": slug,
                    "canonicalArtifactSha256": pack["canonicalArtifactSha256"],
                    "canonicalConceptId": pack.get("canonicalConceptId"),
                    "claims": [fact for facet in pack["facets"] for fact in facet["facts"]]}
        if pack.get("narrative"):
            artifact["narrative"] = pack["narrative"]
        result[slug] = json.dumps(artifact, ensure_ascii=False, indent=2) + "\n"
    return result


def build(concepts_dir: Path, tree_path: Path, out: Path, site_url: str,
          sources_dir: Path) -> int:
    tree = json.loads(tree_path.read_text(encoding="utf-8"))
    nodes = tree.get("nodes") or {}
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    packs = {}
    for f in sorted(concepts_dir.glob("*.json")):
        pack = json.loads(f.read_text(encoding="utf-8"))
        pack.setdefault("slug", f.stem)
        packs[pack["slug"]] = pack
    texts = download_texts(packs, nodes, tree.get("redirects", {}), site_url, sources_dir)
    for slug, text in texts.items():
        (out / f"{slug}.md").write_text(text, encoding="utf-8")
    research_out = out.parent / "research"
    research_out.mkdir(parents=True, exist_ok=True)
    # This generator owns only flat <concept>.json proofs. Article bundles
    # under research/<paper>/ are reviewed source assets, not generated output.
    for generated in research_out.glob("*.json"):
        if generated.is_file() or generated.is_symlink():
            generated.unlink()
    for slug, text in research_download_texts(packs).items():
        (research_out / f"{slug}.json").write_text(text, encoding="utf-8")
    return len(texts)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--concepts", default=str(DEFAULT_CONCEPTS))
    p.add_argument("--tree", default=str(DEFAULT_TREE))
    p.add_argument("--sources", default=str(DEFAULT_SOURCES))
    p.add_argument("--out", default=str(DEFAULT_OUT))
    p.add_argument("--site-url", default=default_site_url())
    a = p.parse_args(argv)
    n = build(Path(a.concepts), Path(a.tree), Path(a.out), a.site_url.rstrip("/"),
              Path(a.sources))
    print(f"{a.out}: {n} concept facts file(s) written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
