# Concept-Pack Reader Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render a concept's researched content — summary, facts grouped by facet, related concepts — as a real prose page at `/tree/<slug>/read/`, for every concept the hub has a pack for.

**Architecture:** A new hand-run generator, `site/tools/gen_concepts.py`, reads `~/.global-ai-hub/llms-concepts/<slug>.llms/` (mirroring `gen_demo.py`'s "the one generator besides X that reads the live hub" precedent) and writes one `src/data/concepts/<slug>.json` per pack, committed. `gen_tree.py` gains a `hasPack` flag per node by checking whether that committed directory has a matching file — a repo-local, CI-safe check, never the live hub. The node page (`tree/[slug].astro`) links to the new reader page only when `hasPack` is true; the reader page itself (`tree/[slug]/read.astro`) is a second `getStaticPaths()`-driven static route, built entirely from the committed JSON, with no client-side fetch.

**Tech Stack:** Python (the generator, mirroring `gen_tree.py`/`gen_demo.py`), Astro static pages (mirroring `tree/[slug].astro`).

**Authority:** `docs/superpowers/plans/2026-09-06-donations-and-community-directory-design.md` §2.2.A.

---

## A real finding from this plan's own research — read before starting

The design doc's §2.2.A assumes every directory under `~/.global-ai-hub/llms-concepts/` is `llms-concept-abstractor` output (the clean "summary → facets → facts, each fact sourced" grammar `heart.llms` has). Reading the actual directory turned up a second generator's output living in the same place — `research-to-llms-txt v1.0.0` (e.g. `code-generation-benchmarks.llms/`), which is a completely different shape: an index over external report files, no per-fact source-anchored grammar at all. Both generators write `manifest.json` with `"kind": "concept"`, so that field alone cannot tell them apart; the reliable markers are a `"reports"` array (only the other generator writes one) and `"facets"` being a non-empty dict of facet-name → count (only the real concept-abstractor writes that shape). `gen_concepts.py`'s `is_concept_abstractor_pack()` (Task 1) checks both.

One consequence worth stating plainly: as of this writing, the two hub packs that happen to share a slug with an existing tree node (`code-generation-benchmarks`, `document-extraction-pipeline`) are **both** from the other generator, so neither will produce a reader page today. That is the correct, honest behavior — rendering `research-to-llms-txt` output through this grammar would misrepresent it — not a bug to work around. `heart.llms` **is** real concept-abstractor output and is used as this plan's fixture and its one committed real example (Task 6), even though "Heart" has no tree node yet: an orphan concept JSON with nothing to link it is harmless, and becomes live the moment that concept enters the tree.

---

## Global notes for every task

- Python: `hub/.venv/bin/python` (this repo's site tests run under the hub venv per `CLAUDE.md`: `uv run --directory hub pytest ../site/tests`), run from the repo root unless noted. Generator scripts themselves run under whichever Python has no site-specific deps — plain `python3` is fine for `gen_concepts.py`/`gen_tree.py` since both are stdlib-only plus `sys.path` tricks already established in this repo.
- Site build: `cd site && npm run build`. Site tests: `cd ~/dev/llms-explorer && hub/.venv/bin/python -m pytest site/tests -q`.
- One commit per task.

---

### Task 1: `gen_concepts.py` — the parser

**Files:**
- Create: `site/tools/gen_concepts.py`
- Test: `site/tests/test_gen_concepts.py`

- [ ] **Step 1: Write the failing test**

```python
# site/tests/test_gen_concepts.py
import json
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import gen_concepts  # noqa: E402

# Trimmed but structurally real: the same shape as the live heart.llms pack —
# manifest.facets as a dict of counts, llms-full.txt's `## <Facet>` / `- [passage]
# ...` grammar, llms.txt's `## Related concepts` list.
HEART_MANIFEST = {
    "kind": "concept", "concept": "Heart", "slug": "heart", "version": "1.4.1",
    "generated": "2026-08-31",
    "summary": "The heart is a hollow muscular organ...",
    "facets": {"definition": 1, "structure": 1},
}
HEART_FULL = """# Heart — concept pack

> The heart is a hollow muscular organ...

## Vocabulary

- **self**: heart (92/1)

## Definitions

- [passage] The heart is the central organ of circulation. — file:///anatomy.md#intro · keywords: heart

## Structure and components

- [passage] It has four chambers. — file:///anatomy.md#chambers · keywords: heart, chamber · note: simplified
"""
HEART_INDEX = """# Heart — concept pack

> The heart is a hollow muscular organ...

## Related concepts

- [atrium](llms-vocabulary.txt#atrium): `atrium` is a part of Heart — 59 units across 1 source
- [valve](llms-vocabulary.txt#valve): `valve` is a part of Heart — 34 units across 1 source; the heart's valves
- [8 more terms](llms-vocabulary.txt): every lexicon term of Heart with its relation, definition and source

## Sources

- [anatomy.md](llms-full.txt#sources): 2 units about Heart
"""

# A pack from the *other* generator this hub directory also holds — must be
# skipped, not crash the parser.
RESEARCH_MANIFEST = {
    "kind": "concept", "concept": "Benchmarks", "slug": "benchmarks",
    "generated": "2026-09-03", "generator": "research-to-llms-txt v1.0.0",
    "reports": [{"path": "../report.md", "title": "Report"}],
}


def _write_pack(root: Path, name: str, manifest: dict, full: str | None = None,
                index: str | None = None) -> Path:
    pack = root / f"{name}.llms"
    pack.mkdir(parents=True)
    (pack / "manifest.json").write_text(json.dumps(manifest))
    if full is not None:
        (pack / "llms-full.txt").write_text(full)
    if index is not None:
        (pack / "llms.txt").write_text(index)
    return pack


def test_a_real_concept_abstractor_pack_is_accepted(tmp_path):
    assert gen_concepts.is_concept_abstractor_pack(HEART_MANIFEST) is True


def test_a_research_to_llms_txt_pack_is_rejected():
    assert gen_concepts.is_concept_abstractor_pack(RESEARCH_MANIFEST) is False


def test_a_pack_with_no_facets_dict_is_rejected():
    assert gen_concepts.is_concept_abstractor_pack({"kind": "concept"}) is False


def test_parse_facets_groups_facts_under_their_section_skipping_vocabulary():
    facets = gen_concepts.parse_facets(HEART_FULL)
    assert [f["title"] for f in facets] == ["Definitions", "Structure and components"]
    assert facets[0]["facts"] == [
        {"text": "The heart is the central organ of circulation.",
         "source": "file:///anatomy.md#intro", "note": None},
    ]
    assert facets[1]["facts"] == [
        {"text": "It has four chambers.", "source": "file:///anatomy.md#chambers",
         "note": "simplified"},
    ]


def test_parse_related_skips_the_more_terms_line():
    related = gen_concepts.parse_related(HEART_INDEX)
    assert related == [
        {"concept": "atrium", "relation": "is a part of Heart", "note": None},
        {"concept": "valve", "relation": "is a part of Heart",
         "note": "the heart's valves"},
    ]


def test_build_one_pack_end_to_end(tmp_path):
    pack_dir = _write_pack(tmp_path, "heart", HEART_MANIFEST, HEART_FULL, HEART_INDEX)
    pack = gen_concepts.build_one(pack_dir)
    assert pack["slug"] == "heart"
    assert pack["concept"] == "Heart"
    assert len(pack["facets"]) == 2
    assert len(pack["related"]) == 2


def test_build_one_skips_a_research_to_llms_txt_pack(tmp_path):
    pack_dir = _write_pack(tmp_path, "benchmarks", RESEARCH_MANIFEST)
    assert gen_concepts.build_one(pack_dir) is None


def test_build_one_skips_a_pack_missing_its_text_files(tmp_path):
    pack_dir = _write_pack(tmp_path, "heart", HEART_MANIFEST)  # no llms-full.txt/llms.txt
    assert gen_concepts.build_one(pack_dir) is None


def test_build_writes_one_file_per_accepted_pack(tmp_path):
    hub_dir = tmp_path / "hub"
    _write_pack(hub_dir, "heart", HEART_MANIFEST, HEART_FULL, HEART_INDEX)
    _write_pack(hub_dir, "benchmarks", RESEARCH_MANIFEST)
    packs = gen_concepts.build(hub_dir)
    assert set(packs) == {"heart"}


def test_build_on_a_missing_hub_dir_returns_empty(tmp_path):
    assert gen_concepts.build(tmp_path / "does-not-exist") == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hub/.venv/bin/python -m pytest site/tests/test_gen_concepts.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'gen_concepts'`.

- [ ] **Step 3: Write `gen_concepts.py`**

```python
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

#: `- [passage] TEXT — SOURCE_URL · keywords: a, b[, c...] [· note: NOTE]`
FACT_RE = re.compile(
    r"^- \[passage\] (?P<text>.+?) — (?P<source>\S+)"
    r"(?: · keywords: [^·]+?)?(?: · note: (?P<note>.+))?$"
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


def parse_facets(full_text: str) -> list[dict[str, Any]]:
    """Each `## <Title>` section of `llms-full.txt` (except Vocabulary) as a
    facet, its `- [passage] ...` lines as that facet's facts."""
    facets: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in full_text.splitlines():
        if line.startswith("## "):
            title = line[3:].strip()
            current = None if title.lower() in SKIP_SECTIONS else {"title": title, "facts": []}
            if current is not None:
                facets.append(current)
            continue
        if current is None:
            continue
        m = FACT_RE.match(line)
        if m:
            current["facts"].append({
                "text": m.group("text").strip(),
                "source": m.group("source"),
                "note": m.group("note"),
            })
    return [f for f in facets if f["facts"]]


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
```

- [ ] **Step 4: Run test to verify it passes, then commit**

```bash
hub/.venv/bin/python -m pytest site/tests/test_gen_concepts.py -q
```
Expected: PASS, 9 tests.

```bash
git add site/tools/gen_concepts.py site/tests/test_gen_concepts.py
git commit -m "feat(site): gen_concepts.py — llms-concept-abstractor packs as build-time JSON"
```

---

### Task 2: `gen_tree.py` gains `hasPack`

**Files:**
- Modify: `site/tools/gen_tree.py`
- Test: `site/tests/test_gen_tree.py`

- [ ] **Step 1: Write the failing test**

Add to `site/tests/test_gen_tree.py`:

```python
def test_a_node_with_a_committed_concept_json_has_haspack_true(tmp_path):
    concepts_dir = tmp_path / "concepts"
    concepts_dir.mkdir()
    (concepts_dir / "root.json").write_text("{}")
    out = gen_tree.build(_repo(tmp_path), concepts_dir=concepts_dir)
    assert out["nodes"]["root"]["hasPack"] is True
    assert out["nodes"]["kid"]["hasPack"] is False


def test_haspack_is_false_when_the_concepts_directory_does_not_exist(tmp_path):
    out = gen_tree.build(_repo(tmp_path), concepts_dir=tmp_path / "nope")
    assert out["nodes"]["root"]["hasPack"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hub/.venv/bin/python -m pytest site/tests/test_gen_tree.py::test_a_node_with_a_committed_concept_json_has_haspack_true -q`
Expected: FAIL — `KeyError: 'hasPack'`.

- [ ] **Step 3: Add the check**

In `site/tools/gen_tree.py`, add a default constant near the top (after `SUMMARIES`):

```python
#: Repo-local, committed output of `gen_concepts.py` — never the live hub, so
#: this stays true in CI. A node's `hasPack` reflects whatever was true the
#: last time both generators were run, which is the same "hand-run, eventually
#: consistent" contract `gen_demo.py`'s data already has.
DEFAULT_CONCEPTS_DIR = HERE / "src" / "data" / "concepts"
```

Change `build`'s signature and the one line that constructs each node:

```python
def build(repo_root: Path, today: str | None = None,
          concepts_dir: Path = DEFAULT_CONCEPTS_DIR) -> dict:
```

```python
        nodes[slug] = {
            "slug": slug, "concept": n["concept"], "skillId": n.get("skillId"),
            "parent": parent, "parent_slug": slug_of.get(parent) if parent else None,
            "children": children, "researchedAt": n.get("researchedAt"),
            "sourcesCount": n.get("sourcesCount", 0), "conceptsCount": n.get("conceptsCount", 0),
            "aliases": n.get("aliases") or [], "state": "researched",
            "skillSummary": skill_summary(repo_root, n.get("skillId"), vendored),
            "hasPack": (concepts_dir / f"{slug}.json").is_file(),
            "artifacts": {},
        }
```

- [ ] **Step 4: Run test to verify it passes, then run the full generator test file and regenerate the committed tree**

```bash
hub/.venv/bin/python -m pytest site/tests/test_gen_tree.py -q
```
Expected: PASS, all tests (existing plus the 2 new ones).

Regenerate the committed `tree.json` so every node gets its `hasPack` field (all `false` until Task 6 commits real concept JSON — that is expected and correct at this point):

```bash
cd site && python3 tools/gen_tree.py && cd ..
git diff --stat site/src/data/tree.json
```
Expected: every node gains `"hasPack": false` — a mechanical, uniform diff, nothing else changes.

- [ ] **Step 5: Commit**

```bash
git add site/tools/gen_tree.py site/tests/test_gen_tree.py site/src/data/tree.json
git commit -m "feat(site): gen_tree.py sets hasPack from gen_concepts.py's committed output"
```

---

### Task 3: The node page links to a reader page when one exists

**Files:**
- Modify: `site/src/pages/tree/[slug].astro`
- Modify: `site/tests/test_tree_pages.py`

- [ ] **Step 1: Write the failing test**

Add to `site/tests/test_tree_pages.py`. This needs its own fixture build with a concept pack present, since the committed tree currently has no real pack (per this plan's own opening note) — extend the existing `fixture_dist` fixture rather than writing a second one, since it already builds a real Astro site from a synthetic tree:

```python
@pytest.fixture(scope="module")
def fixture_dist_with_pack(tmp_path_factory) -> Path:
    """Same as `fixture_dist`, plus one committed concept pack for "root" —
    so the hasPack-gated link and the reader page itself are both exercised
    against a real build, not just unit-tested in isolation."""
    if shutil.which("npx") is None or not (SITE / "node_modules" / "astro").is_dir():
        pytest.skip("needs node + `npm ci` in site/ to build a fixture tree")
    root = tmp_path_factory.mktemp("fixroot-pack")
    for item in ("src", "public", "astro.config.mjs", "tsconfig.json", "package.json"):
        src = SITE / item
        if not src.exists():
            continue
        (shutil.copytree if src.is_dir() else shutil.copy2)(src, root / item)
    os.symlink(SITE / "node_modules", root / "node_modules")
    repo = root / "fixture-repo"
    (repo / "concept-tree").mkdir(parents=True)
    (repo / "concept-tree" / "tree.json").write_text(json.dumps(FIXTURE))
    concepts_dir = root / "src" / "data" / "concepts"
    concepts_dir.mkdir(parents=True, exist_ok=True)
    (concepts_dir / "root.json").write_text(json.dumps({
        "slug": "root", "concept": "Root", "generated": "2026-08-01",
        "summary": "A root concept, for the fixture.",
        "facets": [{"title": "Definitions",
                    "facts": [{"text": "Root is the top.", "source": "file:///r.md#a",
                              "note": None}]}],
        "related": [],
    }))
    (root / "src" / "data" / "tree.json").write_text(
        json.dumps(gen_tree.build(repo, concepts_dir=concepts_dir))
    )
    out = root / "dist"
    r = subprocess.run(["npx", "astro", "build", "--outDir", str(out)],
                       cwd=root, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return out


def test_a_node_with_a_pack_links_the_reader_page(fixture_dist_with_pack):
    html = (fixture_dist_with_pack / "tree" / "root" / "index.html").read_text()
    assert 'href="/tree/root/read/"' in html


def test_a_node_without_a_pack_does_not_link_a_reader_page(fixture_dist_with_pack):
    html = (fixture_dist_with_pack / "tree" / "kid" / "index.html").read_text()
    assert "/read/" not in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hub/.venv/bin/python -m pytest site/tests/test_tree_pages.py::test_a_node_with_a_pack_links_the_reader_page -q`
Expected: FAIL — the link is not in the built HTML (the node page does not know about `hasPack` yet).

- [ ] **Step 3: Add the link**

In `site/src/pages/tree/[slug].astro`, add right after the aliases line (after `{node.aliases.length > 0 && ...}`):

```astro
  {node.hasPack && (
    <p><a href={`/tree/${node.slug}/read/`}>Read the researched content →</a></p>
  )}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
hub/.venv/bin/python -m pytest site/tests/test_tree_pages.py -q
```
Expected: this task's 2 new tests still show as expected at this point — `test_a_node_with_a_pack_links_the_reader_page` will still FAIL, because the *target* page (`/tree/root/read/`) does not exist yet (Task 4). Confirm the failure reason changed from "no such link in the HTML" to a build-time or 404-shaped problem, or that the link now renders but points at a route Task 4 has not created — either way, do not treat this as done until Task 4 lands; this step's job is only to confirm the `href` itself is now emitted correctly. If your build fails outright (rather than just producing a dead link) because `test_internal_links_resolve`-style route validation runs during this build, that's fine and expected — leave it, Task 4 fixes it.

- [ ] **Step 5: Commit**

```bash
git add site/src/pages/tree/[slug].astro site/tests/test_tree_pages.py
git commit -m "feat(site): node page links its reader page when hasPack is true"
```

---

### Task 4: The reader page

**Files:**
- Create: `site/src/pages/tree/[slug]/read.astro`
- Modify: `site/tests/test_tree_pages.py` (the two tests from Task 3 finish passing here)

- [ ] **Step 1: The failing tests already exist**

`test_a_node_with_a_pack_links_the_reader_page` (passes already, from Task 3) and any build failure from Task 3 Step 4 are what this task resolves. Confirm the current state:

```bash
hub/.venv/bin/python -m pytest site/tests/test_tree_pages.py -q 2>&1 | tail -20
```

- [ ] **Step 2: N/A** — the failing state is already established by Task 3.

- [ ] **Step 3: Write the reader page**

```astro
---
// site/src/pages/tree/[slug]/read.astro
import Base from "../../../layouts/Base.astro";
import tree from "../../../data/tree.json";

// Vite's glob-import reads every committed concept pack at build time — the
// same idiom `[slug].astro`'s own `import.meta.glob("./3d.astro")` uses to
// check a sibling page exists, applied here to enumerate data files instead.
function slugFromPath(path: string): string {
  return path.split("/").pop()!.replace(/\.json$/, "");
}

export async function getStaticPaths() {
  const packs = import.meta.glob("../../../data/concepts/*.json", { eager: true });
  return Object.entries(packs).map(([path, mod]) => ({
    params: { slug: slugFromPath(path) },
    props: { pack: (mod as { default: any }).default },
  }));
}

const { pack } = Astro.props;
const node = tree.nodes[pack.slug];

function relatedHref(concept: string): string | null {
  const match = Object.values(tree.nodes as Record<string, any>).find(
    (n) => n.concept.toLowerCase() === concept.toLowerCase()
  );
  if (!match) return null;
  return match.hasPack ? `/tree/${match.slug}/read/` : `/tree/${match.slug}/`;
}
---
<Base
  title={`${pack.concept} — researched`}
  description={String(pack.summary).slice(0, 180)}
  route={`/tree/${pack.slug}/read/`}
  twin={null}
>
  <p><a href={`/tree/${pack.slug}/`}>← {node ? node.concept : pack.concept}</a></p>
  <blockquote>{pack.summary}</blockquote>

  {pack.facets.map((facet: any) => (
    <section>
      <h2>{facet.title}</h2>
      <ul>
        {facet.facts.map((fact: any) => (
          <li>
            {fact.text}{" "}
            <a href={fact.source} class="fact-source" rel="noopener">[source]</a>
            {fact.note && <em> — {fact.note}</em>}
          </li>
        ))}
      </ul>
    </section>
  ))}

  {pack.related.length > 0 && (
    <section>
      <h2>Related concepts</h2>
      <ul>
        {pack.related.map((r: any) => {
          const href = relatedHref(r.concept);
          return (
            <li>
              {href ? <a href={href}>{r.concept}</a> : r.concept}
              {" "}— {r.relation}{r.note && <>; {r.note}</>}
            </li>
          );
        })}
      </ul>
    </section>
  )}
</Base>

<style>
  blockquote { border-left: 3px solid var(--line); padding-left: var(--sp-3); margin-left: 0; }
  .fact-source { font-size: var(--step--1); }
</style>
```

- [ ] **Step 4: Run test to verify it passes**

```bash
hub/.venv/bin/python -m pytest site/tests/test_tree_pages.py -q
```
Expected: PASS, all tests including both new ones from Task 3.

Also add and run one direct content test for the reader page itself:

```python
def test_the_reader_page_renders_facets_and_sourced_facts(fixture_dist_with_pack):
    html = (fixture_dist_with_pack / "tree" / "root" / "read" / "index.html").read_text()
    assert "Definitions" in html
    assert "Root is the top." in html
    assert 'href="file:///r.md#a"' in html


def test_a_slug_with_no_pack_has_no_reader_page(fixture_dist_with_pack):
    assert not (fixture_dist_with_pack / "tree" / "kid" / "read").exists()
```

Add these to `site/tests/test_tree_pages.py` and re-run:
```bash
hub/.venv/bin/python -m pytest site/tests/test_tree_pages.py -q
```
Expected: PASS, all tests.

- [ ] **Step 5: Commit**

```bash
git add "site/src/pages/tree/[slug]/read.astro" site/tests/test_tree_pages.py
git commit -m "feat(site): the concept-pack reader page at /tree/<slug>/read/"
```

---

### Task 5: Full build and site-wide regression check

**Files:** none created or modified — this task is verification only.

- [ ] **Step 1: N/A**
- [ ] **Step 2: N/A**
- [ ] **Step 3: N/A**

- [ ] **Step 4: Run everything**

```bash
cd site && npm run build 2>&1 | tail -20
cd .. && hub/.venv/bin/python -m pytest site/tests -q 2>&1 | tail -40
```
Expected: build succeeds; the full site test suite passes except any test already known to be pre-existing and unrelated (this session's prior work found one such case, `test_the_published_scope_matches_the_mirror_it_was_built_from` — a `directory.json` mirror-manifest drift, unrelated to this plan; confirm any *new* failure is actually new by checking against that known baseline, not assuming everything red is pre-existing).

- [ ] **Step 5: N/A** — nothing to commit for a verification-only task.

---

### Task 6: Generate and commit real output

**Files:**
- Create: `site/src/data/concepts/heart.json` (and any other real concept-abstractor pack found, per the run's own output)

This is the "hand-run, not CI" step `gen_demo.py` already established the precedent for — run it once, by hand, on a box with the hub, and commit whatever it produces.

- [ ] **Step 1: N/A** — no new test; this task's correctness is that the committed output matches what the generator actually produced, checked in Step 4.

- [ ] **Step 2: N/A**

- [ ] **Step 3: Run the generator against the real hub**

```bash
cd site && python3 tools/gen_concepts.py
```
Expected output: `src/data/concepts: N concept pack(s) from ~/.global-ai-hub/llms-concepts` — per this plan's own opening research, `N` is likely small (at least `heart.json`; possibly a few more depending on what else in that directory is real concept-abstractor output at run time — `agents-md-ucp`, `cloudflare-ai-crawler-monetization-verification`, `eu-ai-act-tdm-opt-out`, `nlweb-mcp-agentic-discovery`, `prompt-caching`, `really-simple-licensing`, `robots-txt-content-signals`, and the three `--databases` packs all showed `generator=None` in this plan's research and are worth checking too — do not assume only `heart` qualifies without actually running it).

- [ ] **Step 4: Regenerate `tree.json` so any newly-qualifying node's `hasPack` reflects the real output**

```bash
python3 tools/gen_tree.py && cd ..
git diff --stat site/src/data/concepts/ site/src/data/tree.json
```
Expected: one new JSON file per accepted pack under `site/src/data/concepts/`, and `tree.json` diffs `hasPack` to `true` for any node whose concept name matches one of those packs' `concept` field case-insensitively (today, per this plan's research, that is expected to be none — the two slug-overlapping packs are both the other generator's output — but verify rather than assume, since the hub's contents can change between when this plan was researched and when this task runs).

- [ ] **Step 5: Build, verify, commit**

```bash
cd site && npm run build 2>&1 | tail -15
cd .. && hub/.venv/bin/python -m pytest site/tests -q 2>&1 | tail -20
git add site/src/data/concepts/ site/src/data/tree.json
git commit -m "feat(site): commit real concept packs from the hub (gen_concepts.py run)"
```

If the run produces zero accepted packs (also a legitimate outcome — see this plan's opening note), skip the `git add`/commit for `concepts/` and say so plainly rather than committing an empty directory or fabricating output; `tree.json` regeneration is still worth running and diffing to confirm no spurious change.

---

## Self-review notes

- **Spec coverage:** the route (`/tree/<slug>/read/`), the summary/facet/fact/source/related rendering, the `hasPack` gate, `gen_concepts.py` as a hand-run/committed generator matching `gen_demo.py`'s precedent — all covered, Tasks 1-6.
- **A real deviation from the design doc, found and resolved during research, not silently worked around:** the design assumed one uniform pack shape; the hub actually holds two, and `is_concept_abstractor_pack()` (Task 1) is the fix, with the honest consequence (today's real linkable packs don't qualify) stated up front rather than discovered as a surprise at Task 6.
- **Type/name consistency checked:** `gen_concepts.build()`'s return shape (`{slug: {slug, concept, generated, summary, facets, related}}`) is what Task 2's `gen_tree.py` checks for file existence against (by slug, as a filename) and what Task 4's `read.astro` destructures via `Astro.props.pack` — the same field names throughout, no renaming between tasks.
- **Out of scope, correctly:** `POST /api/contribute` and the three new pages around it (`/contribute/`, `/proposals/`, `/moderate/`) are §2.2.B/C of the design doc — a separate plan (Plan 3), per the already-confirmed sequencing that the reader page has no dependency on the write path.
