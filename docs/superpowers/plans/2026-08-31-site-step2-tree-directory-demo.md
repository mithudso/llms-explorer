# LLMS-Explorer site — Step 2 (tree, directory, semantic demo) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build-order step 2 of `docs/site/00-platform-design.md` §10: the public concept-tree explorer (component 09 read-only — browser, node pages, 3D view, TUI parity), the directory of known llms files with conformance scores (component 10 read-only), and the semantic-indexing demo (component 16) — all on the existing static site, with no backend.

**Architecture:** Everything step 2 shows is *derived data that only changes when the hub changes*. So it is generated at build time into `site/src/data/*.json` by new tools under `site/tools/`, and the pages are Astro pages plus small client-side islands that filter/search the baked JSON. No FastAPI, no Cloudflare Tunnel, no accounts — those arrive in step 3 when there is per-user state to serve. The 3D view vendors the `json-3d-renderer` bundle and feeds it the same tree JSON. The demo ships as a *recorded* run: the golden questions are executed against the live hub at generation time and the three retrieval legs are baked in, labelled with the date they were recorded.

**Tech Stack:** the step-1 stack unchanged — Astro 5, Cloudflare Pages, Python on `hub/.venv`, pytest, the vendored hub under `hub/`.

## Global Constraints

- Design authority: `docs/site/00-platform-design.md` §10 row 2 and components `09`, `10`, `16`. Decisions D1–D8 in §12 are settled; do not re-decide them.
- **Deliberate deviation from the spokes, recorded here and in §12 of the master by Task 9:** components 09/10/16 §5 specify REST routes (`/api/tree`, `/api/directory/...`, `/api/demo/query`) served by `explorer-api`. Step 2 ships those payloads as **static JSON generated at build time** instead. Reason: the tree is 37 nodes and the directory 145 entries — data that changes only when the hub changes, and the hub already rebuilds the site daily. Standing up FastAPI + a tunnel to serve constants would violate master principle 4 (cheap path first) and add an uptime dependency before there is any per-user state. The JSON files keep the shapes the spokes define, so step 3 can put the same payloads behind the real routes without changing a single consumer.
- Every new page gets a `.md` twin and enters the site's own llms family automatically (step 1's `postbuild` already walks `src/content/**`); pages that are pure UI (the 3D canvas, the demo) are *content pages with an explanation* plus an island, so the twin carries something worth reading.
- The site's own lint gate must stay at **0 High**: `hub/.venv/bin/python hub/scripts/llms_lint.py check site/dist/llms*.txt --json` exits 0.
- Generators are pure functions of their inputs and their output is committed, exactly like `gen_reference.py` / `gen_figures.py` (see `site/README.md` Tools table, which Task 8 extends).
- Data sources, all read-only: `concept-tree/tree.json` (37 nodes, 4 roots, each `{concept, skillId, parentConcept, childConcepts[], researchedAt, sourcesCount, conceptsCount, slug, aliases[]}`), `hub/scripts/concept_tree.py` (`ConceptTree.load(tree_path, queue_path, state_path)`, `detail()`, `render_ascii()`), `llms-full/catalog.json` + `manifest.json` via `hub/scripts/llms_full_catalog.py` `list_entries(status, min_pages)`, `outputs/exports/*.llms/manifest.json`, and `hub/scripts/llms_lint.py` for scoring.
- **Never** read from `~/.global-ai-hub` in a generator: use the vendored copies under the repo (`concept-tree/`, `llms-full/`, `outputs/`, `hub/scripts/`), because CI has no hub. The one exception is Task 7's demo recorder, which is run **by hand on the M5** and commits its output.
- Python for all tools/tests: `hub/.venv/bin/python`. Lint with `hub/.venv/bin/python -m ruff check site/tools site/tests` (config `site/ruff.toml`).
- Commits: one per task, conventional prefix. Never commit `site/dist` or `site/node_modules`.

---

## File structure

```
site/
  tools/gen_tree.py           concept-tree/tree.json + hub/scripts/concept_tree.py → src/data/tree.json
  tools/gen_directory.py      llms-full/ + llms_lint scoring          → src/data/directory.json
  tools/gen_demo.py           golden questions × 3 retrieval legs      → src/data/demo.json   (run on the M5)
  src/data/{tree,directory,demo}.json                                  generated, committed
  src/pages/tree/index.astro          the browser (island: search + filter)
  src/pages/tree/[slug].astro         one page per concept node
  src/pages/tree/3d.astro             the 3D view (island: vendored renderer)
  src/pages/directory/index.astro     the directory (island: search + facets)
  src/pages/directory/[key].astro     one page per known site
  src/pages/demo.astro                the recorded three-leg demo (island)
  src/components/{TreeBrowser,Tree3D,DirectoryTable,DemoExplorer}.astro
  src/content/{essays,reference}/…    the prose that accompanies each (twins + llms family)
  public/vendor/concept-tree-3d.bundle.js   vendored from json-3d-renderer, pinned by commit
  tests/test_gen_tree.py, test_gen_directory.py, test_gen_demo.py, test_step2_pages.py
llmsx/                          the CLI package (Task 6): llmsx/{__init__,__main__,tree,tui}.py
```

Every generator writes JSON in the shape its spoke's §3 defines, so step 3 can serve it verbatim.

---

### Task 1: `gen_tree.py` — the tree as build-time JSON

**Files:**
- Create: `site/tools/gen_tree.py`, `site/tests/test_gen_tree.py`
- Generate: `site/src/data/tree.json`

**Interfaces:**
- Produces: `gen_tree.build(repo_root: Path) -> dict` →
  `{"generated": "<YYYY-MM-DD>", "roots": [slug], "nodes": {slug: node}, "edges": [[parent_slug, child_slug]], "frontier": [{"concept","parent","parent_slug"}]}`
  where `node` = `{"slug","concept","skillId","parent","parent_slug","children":[{"concept","slug","state"}],"researchedAt","sourcesCount","conceptsCount","aliases","state","skillSummary","artifacts":{}}` and `state ∈ {"researched","frontier"}`.
- A **frontier** entry is a name in some node's `childConcepts` with no node of its own — derived, never a stored field (master §4). `slug` for a frontier child is `concept_tree.slugify(concept)`.
- Consumed by Tasks 2, 3, 6.

- [ ] **Step 1: Write the failing test**

```python
# site/tests/test_gen_tree.py
# ruff: noqa: E501  -- fixture strings mirror real tree.json rows
import json
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import gen_tree  # noqa: E402

TREE = [
    {"concept": "Root", "skillId": "root-skill", "parentConcept": None,
     "childConcepts": ["Kid", "Ghost"], "researchedAt": "2026-08-01",
     "sourcesCount": 3, "conceptsCount": 9, "slug": "root", "aliases": ["Roots"]},
    {"concept": "Kid", "skillId": None, "parentConcept": "Root", "childConcepts": [],
     "researchedAt": "2026-08-02", "sourcesCount": 1, "conceptsCount": 2, "slug": "kid", "aliases": []},
]


def _repo(tmp_path):
    (tmp_path / "concept-tree").mkdir()
    (tmp_path / "concept-tree" / "tree.json").write_text(json.dumps(TREE))
    return tmp_path


def test_nodes_edges_and_derived_frontier(tmp_path):
    out = gen_tree.build(_repo(tmp_path))
    assert out["roots"] == ["root"]
    assert set(out["nodes"]) == {"root", "kid"}
    assert out["edges"] == [["root", "kid"]]
    # "Ghost" is named as a child but has no node of its own -> frontier, derived
    assert out["frontier"] == [{"concept": "Ghost", "parent": "Root", "parent_slug": "root"}]
    assert [c["state"] for c in out["nodes"]["root"]["children"]] == ["researched", "frontier"]
    assert out["nodes"]["kid"]["parent_slug"] == "root"
    assert out["nodes"]["root"]["aliases"] == ["Roots"]
    assert out["nodes"]["root"]["state"] == "researched"


def test_generated_stamp_and_stable_ordering(tmp_path):
    out = gen_tree.build(_repo(tmp_path))
    assert len(out["generated"]) == 10 and out["generated"][4] == "-"
    again = gen_tree.build(_repo(tmp_path))
    assert json.dumps(out, sort_keys=True) == json.dumps(again, sort_keys=True)


def test_real_tree_builds():
    out = gen_tree.build(SITE.parent)
    assert len(out["nodes"]) >= 30 and len(out["roots"]) >= 1
    assert all(n["slug"] for n in out["nodes"].values())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/mitch/dev/llms-explorer && hub/.venv/bin/python -m pytest site/tests/test_gen_tree.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'gen_tree'`.

- [ ] **Step 3: Implement**

```python
#!/usr/bin/env python3
"""gen_tree — the concept tree as build-time JSON for the site's tree pages.

Reads the repo's own concept-tree/tree.json (never ~/.global-ai-hub, so CI works)
and emits the renderer/browser contract. Frontier nodes are DERIVED: a name that
appears in some node's childConcepts but has no node of its own.

Usage: gen_tree.py [--out site/src/data/tree.json]
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


def slugify(name: str) -> str:
    """Same rule as hub/scripts/concept_tree.py slugify()."""
    s = re.sub(r"[^\w\s-]", "", name.lower()).strip()
    return re.sub(r"[\s_-]+", "-", s)


def _load(repo_root: Path) -> list[dict]:
    raw = json.loads((repo_root / "concept-tree" / "tree.json").read_text(encoding="utf-8"))
    return raw if isinstance(raw, list) else raw.get("nodes", [])


def build(repo_root: Path, today: str | None = None) -> dict:
    nodes_in = _load(repo_root)
    by_name = {n["concept"]: n for n in nodes_in}
    slug_of = {n["concept"]: n.get("slug") or slugify(n["concept"]) for n in nodes_in}

    nodes, edges, frontier = {}, [], []
    for n in nodes_in:
        slug = slug_of[n["concept"]]
        children = []
        for child in n.get("childConcepts") or []:
            known = child in by_name
            children.append({"concept": child,
                             "slug": slug_of.get(child) or slugify(child),
                             "state": "researched" if known else "frontier"})
            if known:
                edges.append([slug, slug_of[child]])
            else:
                frontier.append({"concept": child, "parent": n["concept"], "parent_slug": slug})
        parent = n.get("parentConcept")
        nodes[slug] = {
            "slug": slug, "concept": n["concept"], "skillId": n.get("skillId"),
            "parent": parent, "parent_slug": slug_of.get(parent) if parent else None,
            "children": children, "researchedAt": n.get("researchedAt"),
            "sourcesCount": n.get("sourcesCount", 0), "conceptsCount": n.get("conceptsCount", 0),
            "aliases": n.get("aliases") or [], "state": "researched",
            "skillSummary": "", "artifacts": {},
        }
    roots = [slug_of[n["concept"]] for n in nodes_in if not n.get("parentConcept")]
    stamp = today or datetime.datetime.now(datetime.UTC).date().isoformat()
    return {"generated": stamp, "roots": sorted(roots), "nodes": nodes,
            "edges": sorted(edges), "frontier": sorted(frontier, key=lambda f: (f["parent"], f["concept"]))}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default="src/data/tree.json")
    a = p.parse_args(argv)
    out = HERE / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    data = build(HERE.parent)
    out.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{out}: {len(data['nodes'])} nodes, {len(data['frontier'])} frontier")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests and generate**

Run: `cd /Users/mitch/dev/llms-explorer && hub/.venv/bin/python site/tools/gen_tree.py && hub/.venv/bin/python -m pytest site/tests/test_gen_tree.py -q`
Expected: prints `…/tree.json: 37 nodes, N frontier`; 3 passed.

- [ ] **Step 5: Commit**

```bash
git add site/tools/gen_tree.py site/tests/test_gen_tree.py site/src/data/tree.json
git commit -m "feat(site): generate the concept tree as build-time JSON, frontier derived"
```

---

### Task 2: The tree browser and node pages

**Files:**
- Create: `site/src/pages/tree/index.astro`, `site/src/pages/tree/[slug].astro`, `site/src/components/TreeBrowser.astro`, `site/src/content/reference/concept-tree.md`
- Test: `site/tests/test_step2_pages.py`

**Interfaces:**
- Consumes: `src/data/tree.json` (Task 1).
- Produces routes `/tree/` and `/tree/<slug>/` for every node; the node page shows concept, state, parent (linked), children (linked; frontier children greyed and not linked), aliases, `researchedAt`, `sourcesCount`, `conceptsCount`, `skillId`, and its frontier list.
- The browser island filters by substring over concept **and aliases**, hiding non-matching branches — the same rule as the hub-manager Concepts tab filter.

- [ ] **Step 1: Write the failing test**

```python
# site/tests/test_step2_pages.py
# ruff: noqa: E501
import json
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
DIST = SITE / "dist"
TREE = json.loads((SITE / "src/data/tree.json").read_text())


def test_a_page_exists_for_every_node():
    missing = [s for s in TREE["nodes"] if not (DIST / "tree" / s / "index.html").is_file()]
    assert not missing, missing[:5]
    assert (DIST / "tree" / "index.html").is_file()


def test_node_page_shows_state_and_links_its_parent():
    kid = next(n for n in TREE["nodes"].values() if n["parent_slug"])
    html = (DIST / "tree" / kid["slug"] / "index.html").read_text()
    assert kid["concept"] in html
    assert f'/tree/{kid["parent_slug"]}/' in html
    assert str(kid["sourcesCount"]) in html


def test_frontier_children_are_marked_and_not_linked():
    node = next((n for n in TREE["nodes"].values()
                 if any(c["state"] == "frontier" for c in n["children"])), None)
    if node is None:
        return  # a fully-researched tree is a valid state
    html = (DIST / "tree" / node["slug"] / "index.html").read_text()
    ghost = next(c for c in node["children"] if c["state"] == "frontier")
    assert ghost["concept"] in html
    assert f'href="/tree/{ghost["slug"]}/"' not in html
    assert "frontier" in html.lower()


def test_tree_index_carries_the_data_for_the_island():
    html = (DIST / "tree" / "index.html").read_text()
    assert "tree-data" in html and TREE["roots"][0] in html
```

- [ ] **Step 2: Run to verify it fails** — `hub/.venv/bin/python -m pytest site/tests/test_step2_pages.py -q` → FAIL (`dist/tree/index.html` missing).

- [ ] **Step 3: Implement**

`site/src/pages/tree/[slug].astro`:
```astro
---
import Base from "../../layouts/Base.astro";
import tree from "../../data/tree.json";
export async function getStaticPaths() {
  return Object.values(tree.nodes).map((n) => ({ params: { slug: n.slug }, props: { node: n } }));
}
const { node } = Astro.props;
const frontier = tree.frontier.filter((f) => f.parent_slug === node.slug);
---
<Base title={node.concept} description={`Concept node: ${node.children.length} children, ${node.sourcesCount} sources, researched ${node.researchedAt}.`} route={`/tree/${node.slug}/`} twin={null}>
  <p>
    {node.parent_slug && <>Parent: <a href={`/tree/${node.parent_slug}/`}>{node.parent}</a> · </>}
    researched {node.researchedAt} · {node.sourcesCount} sources · {node.conceptsCount} concepts
    {node.skillId && <> · skill <code>{node.skillId}</code></>}
  </p>
  {node.aliases.length > 0 && <p>Also known as: {node.aliases.join(", ")}</p>}
  <h2>Children</h2>
  <ul>
    {node.children.map((c) => (
      <li>
        {c.state === "researched"
          ? <a href={`/tree/${c.slug}/`}>{c.concept}</a>
          : <span class="frontier" title="frontier: named but not yet researched">{c.concept} <em>(frontier)</em></span>}
      </li>
    ))}
    {node.children.length === 0 && <li><em>No children recorded.</em></li>}
  </ul>
  {frontier.length > 0 && <p><strong>Frontier under this node:</strong> {frontier.map((f) => f.concept).join(", ")}</p>}
  <p><a href="/tree/">← the whole tree</a> · <a href="/tree/3d/">3D view</a></p>
</Base>
```

`site/src/pages/tree/index.astro` renders the roots as a nested `<ul>` (recursive fragment over `tree.nodes`/`children`), embeds the data for the island as `<script type="application/json" id="tree-data" set:html={JSON.stringify(tree)} />`, and includes `TreeBrowser.astro`.

`site/src/components/TreeBrowser.astro` — an inline `<script>` island: reads `#tree-data`, renders a filter `<input>`, and on input hides every `<li>` whose concept and aliases do not contain the query, keeping ancestors of matches visible (the hub-manager rule: only matching branches shown). No framework, no dependency.

`site/src/content/reference/concept-tree.md` — the prose: what the tree is, that frontier is derived and never a stored status, what each field means, and how to read a node page. This is what gives `/tree/` a `.md` twin and puts it in the llms family.

- [ ] **Step 4: Build and test**

Run: `cd site && npm run build && cd .. && hub/.venv/bin/python -m pytest site/tests -q`
Expected: build succeeds with `Object.keys(tree.nodes).length` extra pages; all tests pass.

- [ ] **Step 5: Commit**

```bash
git add site/src/pages/tree site/src/components/TreeBrowser.astro site/src/content/reference/concept-tree.md site/tests/test_step2_pages.py
git commit -m "feat(site): concept-tree browser and a page per node, frontier greyed"
```

---

### Task 3: The 3D view

**Files:**
- Create: `site/public/vendor/concept-tree-3d.bundle.js` (vendored), `site/src/pages/tree/3d.astro`, `site/src/components/Tree3D.astro`, `site/VENDOR.md`
- Test: extend `site/tests/test_step2_pages.py`

**Interfaces:**
- Consumes: `src/data/tree.json`; the renderer expects `const DATA = {...}` in the page (see `~/dev/json-3d-renderer/README.md` — the demos inline their data and load the bundle by a relative path).
- Produces: `/tree/3d/` — a self-contained page loading `/vendor/concept-tree-3d.bundle.js` with the tree inlined; no network calls.

- [ ] **Step 1: Write the failing test** (append to `test_step2_pages.py`)

```python
def test_3d_page_is_self_contained():
    html = (DIST / "tree" / "3d" / "index.html").read_text()
    assert "/vendor/concept-tree-3d.bundle.js" in html
    assert "concept-tree-3d-data" in html          # the inlined DATA
    assert "http://" not in html.split("<body")[1]  # no third-party CDN in the body
    assert (DIST / "vendor" / "concept-tree-3d.bundle.js").is_file()


def test_vendored_bundle_records_its_provenance():
    v = (SITE / "VENDOR.md").read_text()
    assert "json-3d-renderer" in v and "commit" in v.lower()
```

- [ ] **Step 2: Run to verify it fails** — FAIL, the page and bundle do not exist.

- [ ] **Step 3: Implement**

```bash
cd /Users/mitch/dev/llms-explorer
mkdir -p site/public/vendor
cp ~/dev/json-3d-renderer/concept-tree-3d.bundle.js site/public/vendor/
git -C ~/dev/json-3d-renderer rev-parse --short HEAD    # record this in VENDOR.md
```

`site/VENDOR.md`:
```markdown
# Vendored assets

| File | Source | Commit | Why vendored |
|---|---|---|---|
| `public/vendor/concept-tree-3d.bundle.js` | github.com/mithudso/json-3d-renderer | `<short-sha>` | the 3D view must load offline and from our own origin; the upstream repo ships the bundle, not a package |

Refresh: copy the file again from a checkout at the commit you want and update this row.
```

`site/src/pages/tree/3d.astro` inlines the data as `<script type="application/json" id="concept-tree-3d-data" set:html={JSON.stringify(tree)} />`, loads `<script src="/vendor/concept-tree-3d.bundle.js" is:inline></script>`, and `Tree3D.astro` adapts `tree.json` to the renderer's node/link shape (`{nodes:[{id,name,group,description}], links:[{source,target}]}`) from `nodes`/`edges`, then calls the bundle's entry point. Include a `<noscript>` fallback linking `/tree/` and a one-paragraph explanation above the canvas so the page has real content for its twin.

- [ ] **Step 4: Build, test, and eyeball**

Run: `cd site && npm run build && cd .. && hub/.venv/bin/python -m pytest site/tests -q && python3 -m http.server -d site/dist 8099`
Expected: tests pass; `http://localhost:8099/tree/3d/` renders the graph, and clicking a node opens its details. Stop the server when done.

- [ ] **Step 5: Commit**

```bash
git add site/public/vendor site/src/pages/tree/3d.astro site/src/components/Tree3D.astro site/VENDOR.md site/tests/test_step2_pages.py
git commit -m "feat(site): 3D concept-tree view on the vendored json-3d-renderer bundle"
```

---

### Task 4: `gen_directory.py` — the directory with conformance scores

**Files:**
- Create: `site/tools/gen_directory.py`, `site/tests/test_gen_directory.py`
- Generate: `site/src/data/directory.json`

**Interfaces:**
- Consumes: `llms-full/catalog.json` and `llms-full/manifest.json` through `hub/scripts/llms_full_catalog.py` `list_entries(base=<repo>/llms-full, status="ok", min_pages=1)`; the mirrored files under `llms-full/files/<key>.txt`; `hub/scripts/llms_lint.py` `check()`.
- Produces: `gen_directory.build(repo_root, limit=None) -> dict` →
  `{"generated","count","sites":[{"key","name","site","url","category","pages","bytes","fetched_at","grade","counts":{"high","medium","low"},"groups":{"I":n,...},"findings":[{"attr","severity","msg"}]}]}`
  with `grade` from the High/Medium counts: `A` = 0 High and 0 Medium, `B` = 0 High ≤2 Medium, `C` = 0 High, `D` = 1 High, `F` = ≥2 High.
- Scoring runs `llms_lint.check()` on each mirrored `llms-full.txt` with `kind="full"`; `groups` counts findings by the first letter of the attribute id (the rubric groups I/N/D/C/P/S/R/F/H).

- [ ] **Step 1: Write the failing test**

```python
# site/tests/test_gen_directory.py
# ruff: noqa: E501
import json
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import gen_directory  # noqa: E402

FULL = """<!-- llms-full grammar: mintlify — per page: '# Title' / 'Source: <url>' / blank / body -->

# One
Source: https://ex.dev/one

Body of page one, long enough to be a real page with a sentence in it.

# Two
Source: https://ex.dev/two

Body of page two, also long enough to count as content here.
"""


def _repo(tmp_path, text=FULL):
    base = tmp_path / "llms-full"
    (base / "files").mkdir(parents=True)
    (base / "files" / "ex.dev.txt").write_text(text)
    (base / "catalog.json").write_text(json.dumps([{"key": "ex.dev", "url": "https://ex.dev/llms-full.txt",
                                                    "name": "Ex", "site": "https://ex.dev/", "category": "docs",
                                                    "description": "", "sources": ["probe"]}]))
    (base / "manifest.json").write_text(json.dumps({"ex.dev": {"status": "ok", "pages": 2, "bytes": len(text),
                                                               "fetched_at": "2026-08-31T00:00:00+00:00",
                                                               "file": str(base / "files" / "ex.dev.txt")}}))
    return tmp_path


def test_scores_each_site_and_grades_it(tmp_path):
    out = gen_directory.build(_repo(tmp_path))
    assert out["count"] == 1
    s = out["sites"][0]
    assert s["key"] == "ex.dev" and s["pages"] == 2 and s["name"] == "Ex"
    assert s["grade"] in set("ABCDF")
    assert s["counts"]["high"] == 0
    assert set(s["groups"]) <= set("INDCPSRFH")


def test_a_broken_file_grades_worse_than_a_clean_one(tmp_path):
    good = gen_directory.build(_repo(tmp_path))["sites"][0]
    broken = gen_directory.build(_repo(tmp_path / "b", "# no grammar here\njust prose, no Source: lines\n"))["sites"][0]
    assert broken["counts"]["high"] >= 1
    assert "ABCDF".index(broken["grade"]) > "ABCDF".index(good["grade"])


def test_real_directory_builds_a_sample():
    out = gen_directory.build(SITE.parent, limit=5)
    assert out["count"] == 5 and all(s["grade"] in set("ABCDF") for s in out["sites"])
```

- [ ] **Step 2: Run to verify it fails** — `ModuleNotFoundError: gen_directory`.

- [ ] **Step 3: Implement** — `build()` loads entries via `llms_full_catalog.list_entries`, and for each runs:

```python
res = llms_lint.check(Path(entry["file"]), kind="full")
counts = res["counts"]
groups = {}
for f in res["findings"]:
    if f["severity"] in ("high", "medium"):
        groups[f["attr"][0]] = groups.get(f["attr"][0], 0) + 1
grade = ("F" if counts["high"] >= 2 else "D" if counts["high"] == 1
         else "A" if counts["medium"] == 0 else "B" if counts["medium"] <= 2 else "C")
```

with `--limit` for a fast local run, `sites` sorted by grade then key, and the same `main(argv)` shape as the other tools writing `src/data/directory.json`. Scoring 145 sites over ~700 MB takes a few minutes — print progress every 10 sites.

- [ ] **Step 4: Run tests and generate**

Run: `cd /Users/mitch/dev/llms-explorer && hub/.venv/bin/python -m pytest site/tests/test_gen_directory.py -q && hub/.venv/bin/python site/tools/gen_directory.py`
Expected: 3 passed; `directory.json` with ~145 sites and a grade distribution printed.

- [ ] **Step 5: Commit**

```bash
git add site/tools/gen_directory.py site/tests/test_gen_directory.py site/src/data/directory.json
git commit -m "feat(site): directory of known llms files with lint-derived conformance grades"
```

---

### Task 5: The directory pages

**Files:**
- Create: `site/src/pages/directory/index.astro`, `site/src/pages/directory/[key].astro`, `site/src/components/DirectoryTable.astro`, `site/src/content/reference/directory.md`
- Test: extend `site/tests/test_step2_pages.py`

**Interfaces:**
- Consumes: `src/data/directory.json` (Task 4).
- Produces `/directory/` (sortable, searchable table: name, grade, pages, category, link to the site's own file) and `/directory/<key>/` per site (the score card by rubric group, the findings list, `fetched_at`, and a link to the source's own `llms-full.txt` **at its own URL** — never a copy of the third-party text, per master D8).

- [ ] **Step 1: Write the failing test** (append)

```python
DIRECTORY = json.loads((SITE / "src/data/directory.json").read_text())


def test_directory_index_and_a_page_per_site():
    assert (DIST / "directory" / "index.html").is_file()
    missing = [s["key"] for s in DIRECTORY["sites"] if not (DIST / "directory" / s["key"] / "index.html").is_file()]
    assert not missing, missing[:5]


def test_site_page_shows_the_score_and_links_the_source_not_a_copy():
    s = DIRECTORY["sites"][0]
    html = (DIST / "directory" / s["key"] / "index.html").read_text()
    assert s["grade"] in html and str(s["pages"]) in html
    assert s["url"] in html                                  # the source's own file
    assert "/llms-full/files/" not in html                   # never our mirrored copy (master D8)
```

- [ ] **Step 2: Run to verify it fails.**
- [ ] **Step 3: Implement** the two pages plus `DirectoryTable.astro` (an island doing client-side search over name/site/category and a grade filter, reading the JSON embedded as `#directory-data`), and `reference/directory.md` explaining what the grade means, that it is `llms_lint` output and nothing more, and that the mirrored text is never republished.
- [ ] **Step 4: Build and test** — `cd site && npm run build && cd .. && hub/.venv/bin/python -m pytest site/tests -q`.
- [ ] **Step 5: Commit** — `git commit -m "feat(site): directory pages with per-site conformance score cards"`.

---

### Task 6: `llmsx tree` and the TUI (9a)

**Files:**
- Create: `llmsx/pyproject.toml`, `llmsx/llmsx/{__init__,__main__,tree,tui}.py`, `llmsx/tests/test_tree_cli.py`
- Test: `llmsx/tests/test_tree_cli.py`

**Interfaces:**
- Consumes: `site/src/data/tree.json` by default (`--data <path>`; step 3 swaps in `--api <url>`).
- Produces: `llmsx tree show [root]` (ASCII tree, frontier marked `·`), `llmsx tree detail <slug>` (the node fields), `llmsx tree search <q>` (concept + alias substring), `llmsx tree frontier [slug]`, `llmsx tui` (the Textual screen: `Tree` widget, filter input, detail pane, frontier greyed — parity with the hub-manager Concepts tab minus the write actions, which need step 3).
- `llmsx.tree.load(path) -> dict` and `llmsx.tree.render_ascii(data, root=None) -> str` are the reusable pieces.

- [ ] **Step 1: Write the failing test**

```python
# llmsx/tests/test_tree_cli.py
import json
from pathlib import Path
from llmsx import tree

DATA = {"generated": "2026-08-31", "roots": ["root"], "edges": [["root", "kid"]],
        "frontier": [{"concept": "Ghost", "parent": "Root", "parent_slug": "root"}],
        "nodes": {"root": {"slug": "root", "concept": "Root", "parent": None, "parent_slug": None,
                           "children": [{"concept": "Kid", "slug": "kid", "state": "researched"},
                                        {"concept": "Ghost", "slug": "ghost", "state": "frontier"}],
                           "aliases": ["Roots"], "researchedAt": "2026-08-01", "sourcesCount": 3,
                           "conceptsCount": 9, "skillId": "s", "state": "researched"},
                  "kid": {"slug": "kid", "concept": "Kid", "parent": "Root", "parent_slug": "root",
                          "children": [], "aliases": [], "researchedAt": "2026-08-02",
                          "sourcesCount": 1, "conceptsCount": 2, "skillId": None, "state": "researched"}}}


def test_render_ascii_marks_frontier(tmp_path):
    out = tree.render_ascii(DATA)
    assert "Root" in out and "Kid" in out
    assert "Ghost" in out and "·" in out          # frontier marker
    assert out.index("Root") < out.index("Kid")


def test_search_matches_alias_not_just_concept():
    assert [n["slug"] for n in tree.search(DATA, "roots")] == ["root"]
    assert [n["slug"] for n in tree.search(DATA, "kid")] == ["kid"]
    assert tree.search(DATA, "zzz") == []


def test_load_reads_the_generated_file(tmp_path):
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(DATA))
    assert tree.load(p)["roots"] == ["root"]
```

- [ ] **Step 2: Run to verify it fails** — `cd llmsx && ../hub/.venv/bin/python -m pytest tests -q` → `ModuleNotFoundError: llmsx`.
- [ ] **Step 3: Implement** the package (`pyproject.toml` with `textual>=8,<9` as an extra so the plain CLI stays dependency-free; `python -m llmsx` entry point; `tui.py` importing Textual lazily so `llmsx tree` works without it), then `cd llmsx && ../hub/.venv/bin/python -m pip install -e .`.
- [ ] **Step 4: Run tests and the TUI** — `../hub/.venv/bin/python -m pytest tests -q`; then `../hub/.venv/bin/python -m llmsx tui --data ../site/src/data/tree.json` and confirm parity by eye against `scripts/hub-manager`'s Concepts tab.
- [ ] **Step 5: Commit** — `git commit -m "feat(llmsx): tree CLI and TUI reading the generated tree JSON"`.

---

### Task 7: `gen_demo.py` — the recorded three-leg demo (16)

**Files:**
- Create: `site/tools/gen_demo.py`, `site/tests/test_gen_demo.py`, `site/src/data/demo.json`, `site/src/pages/demo.astro`, `site/src/components/DemoExplorer.astro`, `site/src/content/essays/semantic-indexing.md`
- Test: `site/tests/test_gen_demo.py`, extend `test_step2_pages.py`

**Interfaces:**
- **Run by hand on the M5** (it needs the live hub's indexes): `HUB=~/.global-ai-hub hub/.venv/bin/python site/tools/gen_demo.py --docset codeclaudecom__codeclaudecom`. Its output is committed; CI never runs it.
- Produces `{"generated","docset","questions":[{"q","kind","keyword":[hit],"vector":[hit],"hybrid":[hit],"ms":{"keyword","vector","hybrid"}}]}` where `hit` = `{"score","url","seq","text"}` truncated to 300 chars.
- Questions come from `docs/superpowers/specs/2026-08-30-docset-golden-baseline.md` plus the exact-token probes named in `skills/llms-deep-optimizer/references/passes.md` P11 (≥4 exact-token, ≥4 paraphrase).
- The page states plainly that it is a recording with its date, and links `/reference/` for how to run it yourself. Live querying arrives with the API in step 4 (component 16 §5's `/api/demo/query`).

- [ ] **Step 1: Write the failing test**

```python
# site/tests/test_gen_demo.py
# ruff: noqa: E501
import json
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import gen_demo  # noqa: E402


class FakeStore:
    def docset_model(self, key): return "m"
    def query(self, key, qvec, top): return [{"score": 0.9, "url": "https://h/a", "seq": 1, "text": "vector hit " + "x" * 400}]
    def keyword_count(self, key): return 1
    def keyword_query(self, key, q, top, mode="any"): return [{"score": 5.0, "url": "https://h/b", "seq": 2, "snippet": "kw hit"}]


def test_record_shape_and_truncation():
    rec = gen_demo.record(FakeStore(), "d__facts", [{"q": "why split big files", "kind": "paraphrase"}],
                          embed=lambda qs, model=None: [[0.1]], today="2026-08-31")
    assert rec["generated"] == "2026-08-31" and rec["docset"] == "d__facts"
    q = rec["questions"][0]
    assert {"keyword", "vector", "hybrid"} <= set(q)
    assert len(q["vector"][0]["text"]) <= 300
    assert q["hybrid"], "hybrid must fuse both legs"
    assert set(q["ms"]) == {"keyword", "vector", "hybrid"}


def test_committed_demo_is_present_and_labelled():
    d = json.loads((SITE / "src/data/demo.json").read_text())
    assert len(d["questions"]) >= 8
    assert sum(1 for q in d["questions"] if q["kind"] == "exact-token") >= 4
    assert len(d["generated"]) == 10
```

- [ ] **Step 2: Run to verify it fails.**
- [ ] **Step 3: Implement** — `record(store, key, questions, embed, today)` runs the keyword leg (`store.keyword_query`), the vector leg (`store.query` on the embedded question) and fuses with the same RRF as `mcp-server/hub_mcp_server.py:_rrf` (k=60, keyed by `(url, seq)`), timing each with a monotonic clock passed in as `clock=time.perf_counter` so the test can stub it. `main()` resolves the store through `hub/scripts/docset_indexer.get_store()` and writes `src/data/demo.json`.
- [ ] **Step 4: Record on the M5, build, test** — run the generator, then `cd site && npm run build && cd .. && hub/.venv/bin/python -m pytest site/tests -q`.
- [ ] **Step 5: Commit** — `git commit -m "feat(site): recorded keyword/vector/hybrid demo over a public docset"`.

---

### Task 8: Wire the generators into the build and the docs

**Files:**
- Modify: `site/package.json` (`pregenerate` script), `site/README.md` (Tools table + the step-2 pages), `.github/workflows/site.yml` (a step asserting the committed JSON is current)
- Test: extend `site/tests/test_ci_config.py`

**Interfaces:**
- `npm run generate` = `gen_reference.py && gen_tree.py && gen_directory.py` (not `gen_demo.py`, which needs the hub, and not on every build — the JSON is committed).
- CI proves the committed JSON is current for the two generators that can run anywhere: regenerate `tree.json` into a temp path and diff. A stale file fails the build, which is what keeps "generated, never hand-edited" true.

- [ ] **Step 1: Write the failing test**

```python
def test_ci_checks_the_generated_data_is_current():
    wf = (ROOT / ".github/workflows/site.yml").read_text()
    assert "gen_tree.py" in wf and "--out" in wf
    assert "diff" in wf or "cmp" in wf


def test_readme_documents_the_step2_tools():
    r = (ROOT / "site/README.md").read_text()
    for t in ("gen_tree.py", "gen_directory.py", "gen_demo.py"):
        assert t in r
    assert "run by hand on the M5" in r.lower() or "needs the live hub" in r.lower()
```

- [ ] **Step 2: Run to verify it fails.** — [ ] **Step 3: Implement** the workflow step (`hub/.venv/bin/python site/tools/gen_tree.py --out /tmp/tree.json && diff -q /tmp/tree.json site/src/data/tree.json`), the `generate` script, and the README rows. — [ ] **Step 4: Run tests.** — [ ] **Step 5: Commit** — `git commit -m "ci(site): fail when the committed tree/directory JSON is stale"`.

---

### Task 9: Step-2 acceptance and spec reconciliation

- [ ] **Step 1:** `cd site && npm run build && cd .. && hub/.venv/bin/python -m pytest site/tests llmsx/tests -q && hub/.venv/bin/python -m ruff check site/tools site/tests llmsx` → all green.
- [ ] **Step 2:** the gate — `hub/.venv/bin/python hub/scripts/llms_lint.py check site/dist/llms.txt site/dist/llms-facts.txt site/dist/llms-full.txt site/dist/llms-small.txt site/dist/llms-vocabulary.txt --json; echo $?` → 0.
- [ ] **Step 3:** record the deviation in `docs/site/00-platform-design.md` §12 as **D9**: "Step 2's read-only payloads (tree, directory, demo) ship as build-time JSON, not `/api/*`; components 09/10/16 §5 keep their route contracts for step 3, which serves the same shapes." Add a line to each of 09/10/16 §12 pointing at D9.
- [ ] **Step 4:** after deploy, verify live: `curl -sI https://llms-explorer.com/tree/ | head -3`, `curl -s https://llms-explorer.com/tree/llms-txt-and-llm-readable-documentation/ | head -20`, `curl -sI https://llms-explorer.com/directory/`, and that `/tree/`, `/directory/`, `/demo/` appear in `https://llms-explorer.com/llms.txt`.
- [ ] **Step 5:** update §10 row 2 with the acceptance date and commit.

---

## Self-review

- **Spec coverage.** §10 row 2: 09 read-only tree API → Task 1 (the payload) + Task 2 (browser, node pages); 3D → Task 3; TUI parity (9a) + CLI (9b) → Task 6; 10 read-only → Tasks 4–5; 16 demo → Task 7; the acceptance bar (tree page fast, 3D loads the full tree, demo shows three legs) → Tasks 2/3/7 and Task 9's checks. The route contracts in 09/10/16 §5 are deliberately deferred, recorded as D9 by Task 9.
- **Placeholders.** None: every step names its file, its command and its expected output; the one judgement call (the `grade` thresholds) is written out as code.
- **Type consistency.** `build(repo_root, ...) -> dict` in Tasks 1 and 4; `record(store, key, questions, embed, today) -> dict` in Task 7; `tree.load(path)`, `tree.render_ascii(data, root)`, `tree.search(data, q)` in Task 6; every page consumes `src/data/<name>.json` with the keys its generator's test pins. `Base.astro`'s `twin` prop (added in step 1) is used the same way for generated pages.
