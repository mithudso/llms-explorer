#!/usr/bin/env python3
"""Package only the Markdown already selected for public context downloads.

Never reads private hub packs. ZIP timestamps, ordering and JSON are stable.
The five-file family is a project convention, not an llms.txt requirement.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import shutil
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"[a-z0-9][a-z0-9_-]{0,199}\Z")


def encoded(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def archive(slug: str, facts: str, concept: str, generated: str, site_url: str) -> bytes:
    if not SLUG.fullmatch(slug):
        raise ValueError(f"Invalid public pack slug: {slug!r}")
    url = f"{site_url}/tree/{slug}/"
    title = f"# {concept}\n\n"
    files = {
        "llms.txt": (
            title + "Source-linked context; inspect dates and original sources. "
            "Publication does not certify factual accuracy.\n\n"
            f"- [Full reference]({site_url}/downloads/concepts/{slug}.md)\n"
            f"- [Reader and sources]({url})\n"
        ).encode(),
        "llms-full.txt": facts.encode(),
        "llms-facts.txt": facts.encode(),
        # Whole lines only; a short extract does not pretend to be the full reference.
        "llms-small.txt": (
            title
            + "Selected opening lines; see llms-full.txt for the full reference.\n\n"
            + facts[:12000].rsplit("\n", 1)[0]
            + "\n"
        ).encode(),
        "llms-vocabulary.txt": (
            title + "No independently curated vocabulary is supplied in this export.\n"
        ).encode(),
        "concept-graph.json": encoded(
            {
                "schema": "llmsx-public-context-graph/v1",
                "nodes": [{"slug": slug, "concept": concept, "url": url}],
                "edges": [],
            }
        ),
    }
    manifest = {
        "schema": "llmsx-public-context/v1",
        "slug": slug,
        "concept": concept,
        "kind": "concept",
        "generated": generated,
        "summary": "Public source-linked reference; inspect its dates and sources.",
        "origin": url,
        "tokenEstimator": "unicode-codepoints-divided-by-4-floor",
        "qualification": ("Source-linked, not a correctness certificate. "
                          "No private reports included."),
        "files": {
            name: {
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "tokens": len(raw.decode()) // 4,
            }
            for name, raw in files.items()
        },
    }
    files["manifest.json"] = encoded(manifest)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, raw in sorted(files.items()):
            item = zipfile.ZipInfo(f"{slug}.llms/{name}", date_time=(1980, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            zf.writestr(item, raw)
    return stream.getvalue()


def build(facts_dir: Path, tree_path: Path, out: Path, site_url: str) -> dict:
    tree = json.loads(tree_path.read_text())
    nodes = tree.get("nodes", {})
    # The context index is the publication inventory; aliases do not duplicate packs.
    context = json.loads((tree_path.parent / "context.json").read_text())
    published = {c["slug"] for root in context["roots"] for c in root["concepts"]}
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    entries = []
    for slug in sorted(published):
        source_path = tree_path.parent / "concepts" / f"{slug}.json"
        source = json.loads(source_path.read_text()) if source_path.is_file() else {}
        if not str(source.get("summary") or "").strip() or not any(
            str(f.get("text") or "").strip() and str(f.get("source") or "").strip()
            for facet in source.get("facets", [])
            for f in facet.get("facts", [])
        ):
            continue
        facts = (facts_dir / f"{slug}.md").read_text()
        node = nodes.get(slug, {})
        concept = node.get("concept", slug)
        raw = archive(slug, facts, concept, tree.get("generated", "undated"), site_url)
        name = f"{slug}.llms.zip"
        (out / name).write_bytes(raw)
        entries.append(
            {
                "slug": slug,
                "concept": concept,
                "download": f"/downloads/context-packs/{name}",
                "facts": f"/downloads/concepts/{slug}.md",
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
                "tokens": len(facts) // 4,
            }
        )
    index = {
        "schema": "llmsx-public-context-index/v1",
        "generated": tree.get("generated"),
        "packs": entries,
    }
    (out / "index.json").write_bytes(encoded(index))
    return index


if __name__ == "__main__":
    from gen_concept_facts import default_site_url

    result = build(
        HERE / "public/downloads/concepts",
        HERE / "src/data/tree.json",
        HERE / "public/downloads/context-packs",
        default_site_url(),
    )
    print(f"Public .llms packs: {len(result['packs'])}; source inventory preserved")
