#!/usr/bin/env python3
"""build_concept_packs — turn a migrated concept's source markdown into two
things this site already knows how to serve:

  1. A public page under site/src/content/sources/<hub>/<id>.md — a straight
     copy of the source doc, so per-fact citations have somewhere to resolve
     (the origin repos, mdb-context-hub and global-ai-hub, are private; a
     GitHub URL into either 404s for a public visitor). Excluded from
     twins.py (see NO_TWIN_COLLECTIONS there) so it doesn't get folded into
     this site's own curated llms.txt/llms-full.txt/llms-small.txt family.
  2. A concept pack (manifest.json + llms.txt + llms-full.txt, the same
     shape gen_concepts.py already reads from ~/.global-ai-hub/llms-concepts/
     and compiles into site/src/data/concepts/<slug>.json) written to a
     staging directory. Facets = the source doc's `## ` sections; each
     section's paragraphs and list items become `- [passage] TEXT — URL`
     lines citing the hosted page's own heading anchor.

Deterministic and mechanical — no model call, no semantic classification.
This is a document-to-format conversion, not the full llms-concept-abstractor
pipeline (which does real cross-source synthesis); a source with no `## `
structure at all yields one catch-all facet.

Usage: build_concept_packs.py --spec SPEC.json --staging DIR
       [--content-dir site/src/content/sources]

SPEC.json: a list of {hub, id, source, concept, slug} objects. `hub` and
`id` combine into the hosted page path and URL; `source` is the absolute
path to the markdown file to mirror; `slug` is the concept-tree slug this
pack is keyed by (must match site/src/data/tree.json after gen_tree.py).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SITE_URL = "https://llms-explorer.com"
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
PROVENANCE_RE = re.compile(r"\A<!--\s*Provenance:.*?-->\n*", re.DOTALL)
DASH_SAFE_RE = re.compile(r"\s—\s")  # em-dash would break FACT_RE's own delimiter

# read.astro interpolates fact.text as a plain string, not markdown — a raw
# **bold** or [text](url) shows its literal asterisks/brackets on the page.
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
MD_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
MD_ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
MD_CODE_RE = re.compile(r"`([^`]+)`")


def strip_inline_markdown(text: str) -> str:
    text = MD_LINK_RE.sub(r"\1", text)
    text = MD_BOLD_RE.sub(r"\1", text)
    text = MD_ITALIC_RE.sub(r"\1", text)
    text = MD_CODE_RE.sub(r"\1", text)
    return text


def slugify_heading(text: str) -> str:
    """github-slugger-equivalent: what rehype-slug (Astro's default) gives
    each heading its id from. Must match, or a fact's #anchor 404s on the
    hosted page even though the page itself resolves."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\- ]", "", s)
    s = re.sub(r"[ ]+", "-", s)
    return s or "section"


def clean_source_text(raw: str) -> str:
    text = FRONTMATTER_RE.sub("", raw)
    text = PROVENANCE_RE.sub("", text)
    return text.strip() + "\n"


#: A whole-line italic marker like `*Generated: 2026-05-31 | Sources: 27 | ...*`
#: — 15 of the 24 global-ai-hub research files open with one right after the
#: H1. Metadata, not prose: skipped everywhere a "first real line" is picked.
METADATA_LINE_RE = re.compile(r"^\*[^*]+\*$")


def is_metadata_line(line: str) -> bool:
    return bool(METADATA_LINE_RE.match(line.strip()))


def first_prose_line(text: str, max_chars: int = 200) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("<!--") \
                and not is_metadata_line(line):
            return strip_inline_markdown(line)[:max_chars].rstrip()
    return ""


LIST_ITEM_RE = re.compile(r"^([-*•]|\d+\.)\s+(.*)$")


def extract_facets(text: str, page_url: str) -> list[dict]:
    """`## ` sections as facets; each paragraph or list item in a section
    becomes one passage, cited to the hosted page's own anchor.

    Hand-authored markdown wraps prose across physical lines with no blank
    line between them — a paragraph, or a list item's second and later
    lines, continue the line above rather than starting a new one. Passages
    are built by buffering consecutive non-blank lines and only flushing at
    a real boundary (blank line, new heading, new list item, fence toggle);
    treating every physical line as its own passage — the previous
    approach — cut mid-sentence and produced two disconnected fact
    fragments from one wrapped sentence."""
    facets: list[dict] = []
    current: dict | None = None
    seen_anchors: dict[str, int] = {}
    buf: list[str] = []

    def start_facet(title: str) -> dict:
        anchor = slugify_heading(title)
        seen_anchors[anchor] = seen_anchors.get(anchor, 0) + 1
        if seen_anchors[anchor] > 1:
            anchor = f"{anchor}-{seen_anchors[anchor] - 1}"
        f = {"title": title, "anchor": anchor, "facts": []}
        facets.append(f)
        return f

    def flush():
        nonlocal buf, current
        if not buf:
            return
        body = " ".join(buf)
        buf = []
        if len(body) <= 20:
            return
        body = strip_inline_markdown(body)
        body = DASH_SAFE_RE.sub(" - ", body).strip()
        if body:
            if current is None:
                current = start_facet("Overview")
            current["facts"].append({"text": body, "anchor": current["anchor"]})

    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            flush()
            in_fence = not in_fence
            continue
        if in_fence:
            continue  # code/config content, not prose — also where connection-string
            # examples like `user:pass@cluster.mongodb.net` live, which this repo's
            # publish-privacy gate (correctly) flags as an address-in-a-path pattern
        m = HEADING_RE.match(line)
        if m and len(m.group(1)) <= 3:  # #, ##, ### only — deeper headings stay prose
            flush()
            current = start_facet(m.group(2))
            continue
        if not stripped:
            flush()
            continue
        if stripped.startswith("|") or is_metadata_line(stripped):
            flush()
            continue
        # A real bullet/numbered item has whitespace right after its marker;
        # `**bold prose**` also starts with `*` but the next char is another
        # `*`, not whitespace, so LIST_ITEM_RE (marker + \s) does not match it
        # and it falls through to the continuation-line branch untouched.
        list_m = LIST_ITEM_RE.match(stripped)
        if list_m:
            flush()  # a new item starts — whatever was buffered belongs to the last one
            buf.append(list_m.group(2).strip())
        else:
            buf.append(stripped)  # continues the paragraph or list item above
    flush()

    return [f for f in facets if f["facts"]]


def write_hosted_page(content_dir: Path, hub: str, id_: str, concept: str,
                       source_text: str) -> Path:
    dest = content_dir / hub / f"{id_}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    desc = first_prose_line(source_text) or f"Source document for {concept}, mirrored from {hub}."
    desc = desc.replace('"', "'")[:200]
    title = concept.replace('"', "'")
    frontmatter = f'---\ntitle: "{title}"\ndescription: "{desc}"\n---\n\n'
    dest.write_text(frontmatter + source_text, encoding="utf-8")
    return dest


def write_pack(staging: Path, slug: str, concept: str, summary: str,
                facets: list[dict], page_url: str) -> Path:
    pack_dir = staging / f"{slug}.llms"
    pack_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "kind": "concept", "concept": concept, "slug": slug,
        "generated": "2026-09-08",
        "summary": summary,
        "facets": {f["title"].lower()[:40]: len(f["facts"]) for f in facets},
    }
    (pack_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    full_lines = [f"# {concept} — concept pack", "", f"> {summary}", ""]
    for facet in facets:
        full_lines.append(f"## {facet['title']}")
        full_lines.append("")
        for fact in facet["facts"]:
            full_lines.append(f"- [passage] {fact['text']} — {page_url}#{fact['anchor']}")
        full_lines.append("")
    (pack_dir / "llms-full.txt").write_text("\n".join(full_lines), encoding="utf-8")

    total = sum(len(f["facts"]) for f in facets)
    index_lines = [
        f"# {concept} — concept pack", "", f"> {summary}", "",
        "## Sources", "",
        f"- [{page_url}]({page_url}): {total} units about {concept}", "",
    ]
    (pack_dir / "llms.txt").write_text("\n".join(index_lines), encoding="utf-8")
    return pack_dir


def build_one(entry: dict, content_dir: Path, staging: Path) -> dict:
    source_path = Path(entry["source"])
    raw = source_path.read_text(encoding="utf-8", errors="ignore")
    text = clean_source_text(raw)

    page_url = f"{SITE_URL}/sources/{entry['hub']}/{entry['id']}/"
    write_hosted_page(content_dir, entry["hub"], entry["id"], entry["concept"], text)

    facets = extract_facets(text, page_url)
    summary = first_prose_line(text) or entry["concept"]
    pack_dir = write_pack(staging, entry["slug"], entry["concept"], summary, facets, page_url)

    fact_count = sum(len(f["facts"]) for f in facets)
    return {"slug": entry["slug"], "concept": entry["concept"],
            "facets": len(facets), "facts": fact_count, "pack_dir": str(pack_dir)}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--spec", required=True)
    p.add_argument("--staging", required=True)
    p.add_argument("--content-dir", default="site/src/content/sources")
    a = p.parse_args(argv)

    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    content_dir = Path(a.content_dir)
    staging = Path(a.staging)
    staging.mkdir(parents=True, exist_ok=True)

    results = [build_one(e, content_dir, staging) for e in spec]
    for r in results:
        print(f"{r['slug']}: {r['facets']} facets, {r['facts']} facts -> {r['pack_dir']}")
    print(f"total: {len(results)} concept(s) built")
    return 0


if __name__ == "__main__":
    sys.exit(main())
