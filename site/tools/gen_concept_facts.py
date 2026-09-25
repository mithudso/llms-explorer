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

Deterministic: the only date is the pack's own `generated`; the output
directory is rebuilt from scratch so a removed pack cannot linger.

Usage: gen_concept_facts.py [--out public/downloads/concepts] [--site-url URL]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]                  # site/
DEFAULT_CONCEPTS = HERE / "src" / "data" / "concepts"
DEFAULT_TREE = HERE / "src" / "data" / "tree.json"
DEFAULT_SOURCES = HERE / "src" / "content" / "sources"
DEFAULT_OUT = HERE / "public" / "downloads" / "concepts"
DEFAULT_SITE_URL = "https://llms-explorer.com"
CHARS_PER_TOKEN = 4                                         # the family's estimator
SOURCE_URL_RE = re.compile(r"^https?://[^/]+/sources/([^/]+)/([^/#?]+)/")
FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def default_site_url() -> str:
    return os.environ.get("SITE_URL", "").strip().rstrip("/") or DEFAULT_SITE_URL


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
        if src.startswith(("http://", "https://")):
            line += f" — [source]({src})"
        elif src:
            line += f" — source: `{src}`"
        if fact.get("note"):
            line += f" *({_md_text(fact['note'])})*"
        lines.append(line)
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

    body = []
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

    cited: list[tuple[str, str]] = []
    for facet in facets:
        for fact in facet.get("facts") or []:
            m = SOURCE_URL_RE.match(str(fact.get("source") or ""))
            if m and (m.group(1), m.group(2)) not in cited:
                cited.append((m.group(1), m.group(2)))
    if cited:
        body += ["## Context files", ""]
        for hub, name in cited:
            body.append(f"- [{_source_title(sources_dir, hub, name)}]"
                        f"({site_url}/downloads/sources/{hub}/{name}.md)")
        body.append("")

    text = "\n".join(head + body).rstrip() + "\n"
    tokens = len(text) // CHARS_PER_TOKEN
    dated = pack.get("generated") or "undated"
    banner = f"<!-- llms-explorer concept facts · {page} · pack {dated} · ~{tokens} tokens -->\n\n"
    return banner + text


def build(concepts_dir: Path, tree_path: Path, out: Path, site_url: str,
          sources_dir: Path) -> int:
    nodes = json.loads(tree_path.read_text(encoding="utf-8")).get("nodes") or {}
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted(concepts_dir.glob("*.json")):
        pack = json.loads(f.read_text(encoding="utf-8"))
        pack.setdefault("slug", f.stem)
        (out / f"{pack['slug']}.md").write_text(
            render_pack(pack, nodes, site_url, sources_dir), encoding="utf-8")
        n += 1
    return n


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
