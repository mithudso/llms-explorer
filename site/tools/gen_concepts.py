#!/usr/bin/env python3
"""gen_concepts — llms-concept-abstractor packs as build-time JSON.

Reads `~/.global-ai-hub/llms-concepts/<slug>.llms/` and writes one
`src/data/concepts/<slug>.json` per real concept pack found — summary, facts
grouped by facet, related concepts. Feeds the reader page at
`/tree/<slug>/read/` (`site/src/pages/tree/[slug]/read.astro`).

Like `gen_demo.py`, this is the one generator besides it that reads the live
hub, so it is **hand-run, not CI** — its output is committed, and `gen_tree.py`
checks that committed output (never the hub) to decide whether a node links to
a reader page, which is what keeps CI able to build without the hub present.

That same hub directory also holds packs from at least one other generator
(`research-to-llms-txt`, an index over external report files with no
per-fact source-anchored grammar this reader could honestly render) —
`is_concept_abstractor_pack()` tells the two apart and skips anything that
is not the shape this parser understands, rather than guessing at it.

Usage: gen_concepts.py [--hub-dir ~/.global-ai-hub/llms-concepts]
                       [--out-dir src/data/concepts]
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parents[1]                    # site/
DEFAULT_HUB_DIR = Path.home() / ".global-ai-hub" / "llms-concepts"
DEFAULT_OUT_DIR = HERE / "src" / "data" / "concepts"

#: `- [KIND] TEXT — SOURCE_URL[ · keywords: a, b][ · also: url, url][ · note: NOTE]`
#:
#: KIND is any unit kind `llms-concept-abstractor` classifies into, not just
#: `passage`: real packs are 26% `definition` / `parameter` / `snippet` /
#: `fact` / `concept` / `problem` / `idea` / `actionable`, and a pack can carry
#: no `passage` units at all (prompt-caching is 100% definition+parameter).
#: Matching only `passage` silently dropped every other kind.
#:
#: `text` is greedy so `source` binds to the LAST ` — ` on the line: titled
#: kinds (`- [definition] Title — body — URL`) and snippets
#: (`- [snippet] Title: x — \`code\` — URL`) carry more than one separator, and
#: a non-greedy `text` would bind `source` to the title's separator instead.
FACT_RE = re.compile(
    r"^- \[(?P<kind>[a-z]+)\] (?P<text>.+) — (?P<source>\S+)"
    r"(?: · keywords: [^·]+?)?(?: · also: [^·]+?)?(?: · note: (?P<note>.+))?$"
)
#: `- [CONCEPT](anchor): `term` is a RELATION — N units across M sources[; NOTE]`
RELATED_RE = re.compile(
    r"^- \[(?P<concept>[^\]]+)\]\([^)]+\): `[^`]+` (?P<relation>is a [^—]+?)"
    r" — \d+ units? across \d+ sources?(?:; (?P<note>.+))?\s*$"
)
#: Not a facet — vocabulary/coverage bookkeeping, not researched content.
SKIP_SECTIONS = {"vocabulary"}


def is_concept_abstractor_pack(manifest: dict[str, Any]) -> bool:
    """True for real `llms-concept-abstractor` output, false for anything else
    that happens to share this hub directory.

    `"reports"` is the other generator's own marker (an index over external
    files, not extracted facts); a non-empty `"facets"` dict of counts is the
    real generator's, and its absence means this manifest cannot be rendered
    as facets regardless of what else it claims to be.
    """
    if manifest.get("kind") != "concept":
        return False
    if "reports" in manifest:
        return False
    facets = manifest.get("facets")
    return isinstance(facets, dict) and len(facets) > 0


#: `file:///Users/<account>/rest` or a bare `/Users/<account>/rest`, and the
#: Linux equivalent — an operator's home directory, which names a real person.
HOME_PATH_RE = re.compile(r"(?:file://)?/(?:Users|home)/[^/]+/")


def scrub_home_path(source: str) -> str:
    """Rewrite an absolute operator home path in a citation to `~/`.

    A pack harvested from local files cites them as
    `file:///Users/<account>/.claude/skills/...`. These JSON files are
    published to llms-explorer.com, so the account name would ship with them.
    The committed pages carry the `~/` form because a scrub pass rewrote them
    after the fact; doing it here instead means a regeneration cannot quietly
    put the raw paths back, which is exactly what happened before this guard
    (the repo's privacy gate caught 1,456 of them in one regeneration).
    """
    return HOME_PATH_RE.sub("~/", source)


def parse_facets(full_text: str) -> list[dict[str, Any]]:
    """Each `## <Title>` section of `llms-full.txt` (except Vocabulary) as a
    facet, its `- [KIND] ...` lines as that facet's facts.

    `## Disagreements` is not an ordinary facet: the abstractor re-emits units
    that already appeared under their own facet, grouped under `### <conflict-id>`
    subheadings, so a reader sees clashing sources side by side ("Kept side by
    side — never merged"). Those `###` groups are carried through as each fact's
    `group`, because dropping them renders the intentional re-show as an
    unexplained duplicate of a fact further up the page.
    """
    facets: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    group: str | None = None
    for line in full_text.splitlines():
        if line.startswith("## "):
            title = line[3:].strip()
            group = None
            current = None if title.lower() in SKIP_SECTIONS else {"title": title, "facts": []}
            if current is not None:
                facets.append(current)
            continue
        if current is None:
            continue
        if line.startswith("### "):
            group = line[4:].strip()
            continue
        m = FACT_RE.match(line)
        if m:
            fact: dict[str, Any] = {
                "text": m.group("text").strip(),
                "source": scrub_home_path(m.group("source")),
                "note": m.group("note"),
            }
            if group:
                fact["group"] = group
            current["facts"].append(fact)
    for facet in facets:
        facet["facts"] = _dedupe_facts(_drop_one_sided_groups(facet["facts"]))
    return [f for f in facets if f["facts"]]


def _dedupe_facts(facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse facts identical in both text and source, keeping the first.

    Distinct source code blocks can reduce to the same unit text — a `snippet`
    unit is rendered as its fence plus first line, so three different queries
    that all open `const messages = await ctx.db` under one anchor arrive here
    as three byte-identical facts. They render identically and cite the same
    place, so every copy after the first is noise on the page. Keyed on
    (text, source) rather than text alone: the same sentence sourced from two
    different anchors is two real citations and both are kept.
    """
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, Any]] = []
    for fact in facts:
        key = (fact["text"], fact["source"])
        if key in seen:
            continue
        seen.add(key)
        out.append(fact)
    return out


def _drop_one_sided_groups(facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop grouped facts whose group has only one member.

    A `### <conflict-id>` group exists to show two or more sources clashing.
    The classifier sometimes tags a single unit with a conflict id to mean
    "this claim is contentious", which reaches the page as a lone fact under
    Disagreements that duplicates, word for word, a fact already shown under
    its own facet — indistinguishable to a reader from a rendering bug.
    `concept_abstract.py` now filters these at generation, but packs built
    before that fix still carry them, so the display layer drops them too.
    """
    sizes: dict[str, int] = {}
    for fact in facts:
        if fact.get("group"):
            sizes[fact["group"]] = sizes.get(fact["group"], 0) + 1
    return [f for f in facts if not f.get("group") or sizes[f["group"]] >= 2]


def parse_related(index_text: str) -> list[dict[str, Any]]:
    """The `## Related concepts` section of `llms.txt`.

    Skips the trailing "N more terms" line — it links the whole vocabulary
    file, not one concept, so `RELATED_RE` never matches it (no `is a ...`
    relation clause) and this loop simply moves on.
    """
    related: list[dict[str, Any]] = []
    in_section = False
    for line in index_text.splitlines():
        if line.startswith("## "):
            in_section = line[3:].strip().lower() == "related concepts"
            continue
        if not in_section:
            continue
        m = RELATED_RE.match(line)
        if m:
            related.append({
                "concept": m.group("concept"),
                "relation": m.group("relation").strip(),
                "note": m.group("note"),
            })
    return related


def build_one(pack_dir: Path) -> dict[str, Any] | None:
    """One pack's JSON, or `None` if it is missing, malformed, or not a real
    concept-abstractor pack."""
    manifest_path = pack_dir / "manifest.json"
    if not manifest_path.is_file():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not is_concept_abstractor_pack(manifest):
        return None
    full_path = pack_dir / "llms-full.txt"
    index_path = pack_dir / "llms.txt"
    if not full_path.is_file() or not index_path.is_file():
        return None
    return {
        "slug": manifest["slug"],
        "concept": manifest["concept"],
        "generated": manifest.get("generated", ""),
        "summary": manifest.get("summary", ""),
        "facets": parse_facets(full_path.read_text(encoding="utf-8")),
        "related": parse_related(index_path.read_text(encoding="utf-8")),
    }


def build(hub_dir: Path) -> dict[str, dict[str, Any]]:
    """`{slug: pack}` for every real concept-abstractor pack under `hub_dir`."""
    if not hub_dir.is_dir():
        return {}
    out: dict[str, dict[str, Any]] = {}
    for pack_dir in sorted(hub_dir.glob("*.llms")):
        pack = build_one(pack_dir)
        if pack is not None:
            out[pack["slug"]] = pack
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hub-dir", type=Path, default=DEFAULT_HUB_DIR)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = ap.parse_args(argv)

    packs = build(args.hub_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for slug, pack in packs.items():
        (args.out_dir / f"{slug}.json").write_text(
            json.dumps(pack, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    print(f"{args.out_dir}: {len(packs)} concept pack(s) from {args.hub_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
