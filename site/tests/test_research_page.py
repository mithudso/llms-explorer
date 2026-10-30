# site/tests/test_research_page.py — /research/, the research-by-task page.
#
# The search tests run the shipped scorer (src/scripts/research-search.ts) in
# Node with its types stripped, and the curation test reads research-tasks.json
# directly, so neither needs a build. The page tests read site/dist: they skip
# when the site was never built and fail when it was built without the page.
# Every curated pick must render, every row must point at a file the build
# carries, and every copied prompt must name the public site.
# ruff: noqa: E501
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import twins  # noqa: E402

SITE = Path(__file__).resolve().parents[1]
DIST = SITE / "dist"
SEARCH = SITE / "src" / "scripts" / "research-search.ts"
PAGE_SOURCE = SITE / "src" / "pages" / "research" / "index.astro"
CONTEXT = SITE / "src" / "data" / "context.json"
TREE = SITE / "src" / "data" / "tree.json"
CURATED = json.loads((SITE / "src" / "data" / "research-tasks.json").read_text(encoding="utf-8"))
AI_ROOT = CURATED["root"]
TASKS = CURATED["tasks"]
# astro.config.mjs `site`: what every copied prompt and twin link must start with.
PUBLIC = (os.environ.get("SITE_URL") or "https://llms-explorer.com").rstrip("/")

LOAD = r"""
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';

const m = await import('data:text/javascript,' + encodeURIComponent(stripTypeScriptTypes(readFileSync(process.argv[1], 'utf8'))));
"""


def _node(script: str, *args: str) -> str:
    """Run `script` with the search module bound to `m`; fail with everything Node printed."""
    if shutil.which("node") is None:
        pytest.skip("node is not installed")
    run = subprocess.run(["node", "--disable-warning=ExperimentalWarning", "--input-type=module",
                          "-e", LOAD + script, str(SEARCH), *args],
                         capture_output=True, text=True, timeout=60)
    assert run.returncode == 0, run.stdout + run.stderr
    return run.stdout


HARNESS = r"""
const row = (slug, concept, facts, topics = [], aliases = []) => ({
  slug, concept, facts, download: `/downloads/concepts/${slug}.md`,
  family: null, familySlug: null, aliases, topics });
const items = m.indexReferences([
  row('memory', 'Agent Memory Architecture', 40),
  row('stub', 'Agent Memory Router', 2),
  row('caching', 'Prompt caching', 176, ['Cache breakpoints']),
  row('compaction', 'Context-Window Pressure & Compaction', 44, ['Agent Memory Architecture']),
  row('storage', 'Storage tiers', 9),
  row('rag', 'Agentic and Advanced RAG Patterns', 125, ['Re-ranking']),
  row('llms', 'llms.txt', 60, [], ['LLM-readable docs']),
]);
const slugsIn = (pool, query) => m.taskHits(query, pool).hits.map((hit) => hit.slug);
const slugs = (query) => slugsIn(items, query);

// A sentence about a task still finds the concepts it names: filler drops out,
// inflected filler too, and a compound counts once instead of as its parts.
assert.deepEqual(m.taskTerms('Give my agent long-term memory'), ['agent', 'longterm', 'memory']);
assert.deepEqual(m.taskTerms('re-ranking for llms.txt'), ['rerank', 'llmstxt']);
assert.deepEqual(m.taskTerms('wants memory and uses caching'), ['memory', 'cach']);
assert.deepEqual(m.taskTerms('AI LLM prompt caching'), ['prompt', 'cach']);
assert.deepEqual(m.taskTerms('cache caches cached caching'), ['cach']);
// Coverage ranks first; among equal coverage a two-fact stub follows fuller
// packs, and a name match beats a topic match.
assert.deepEqual(slugs('give my agent long-term memory'), ['memory', 'compaction', 'stub', 'rag']);
const both = m.taskHits('agent memory', items);
assert.deepEqual(both.hits.map((hit) => hit.slug), ['memory', 'compaction', 'stub', 'rag']);
assert.equal(both.complete, true);
// Suffixes fold: "caches", "cached" and "caching" meet "cache".
for (const query of ['caches', 'cached', 'caching']) assert.deepEqual(slugs(query), ['caching']);
// A term must begin a word: "rag" is not inside "storage".
assert.deepEqual(slugs('rag'), ['rag']);
// Compounds match however they are written, and aliases are searched.
for (const query of ['reranking', 're-ranking', 're ranking']) assert.deepEqual(slugs(query), ['rag']);
assert.deepEqual(slugs('llms.txt'), ['llms']);
assert.deepEqual(slugs('llm-readable docs'), ['llms']);
const kv = m.indexReferences([row('kv', 'KV cache sizing', 30)]);
assert.deepEqual(slugsIn(kv, 'kv-cache'), ['kv']);
assert.equal(m.taskHits('kv-cache', kv).complete, true);
// A slash lists alternatives; it does not glue words into one.
assert.equal(m.taskHits('agent/memory', items).total, m.taskHits('agent memory', items).total);
// A two-letter term must be a whole word: "go" is not the start of "google".
assert.deepEqual(slugsIn(m.indexReferences([row('adk', 'Google ADK agents', 20)]), 'go'), []);
// No reference covers every word: still ranked, but flagged as incomplete.
const partial = m.taskHits('prompt caching kubernetes', items);
assert.deepEqual(partial.hits.map((hit) => hit.slug), ['caching']);
assert.equal(partial.complete, false);
// Only filler, or nothing that matches: no hits, and no terms for filler alone.
assert.deepEqual(m.taskHits('how do I use it', items), { terms: [], hits: [], total: 0, complete: false });
assert.deepEqual(m.taskHits('zzzz', items).hits, []);
// One-letter words are dropped, so "x" has no terms.
assert.equal(m.taskHits('x', items, 1).total, 0);
// The limit caps the hits but not the total, and never goes below zero.
const capped = m.taskHits('agent', items, 1);
assert.equal(capped.hits.length, 1);
assert.equal(capped.total, 4);
assert.deepEqual(m.taskHits('agent', items, -1).hits, []);
// A reference named exactly what was typed leads, even over a fuller pack or
// when it is a stub.
const exact = m.indexReferences([row('full', 'Agent Memory Architecture', 40), row('thin', 'Agent Memory', 2)]);
assert.deepEqual(slugsIn(exact, 'Agent memory'), ['thin', 'full']);
items.push(...m.indexReferences([row('nlweb', 'NLWeb and MCP as alternatives to llms.txt', 76)]));
assert.deepEqual(slugs('llms.txt'), ['llms', 'nlweb']);
// Lowercasing ignores the browser locale, on the query and the index side:
// Turkish would turn "I" into a dotless "ı".
const localeLower = String.prototype.toLocaleLowerCase;
String.prototype.toLocaleLowerCase = function (locale) { return localeLower.call(this, locale ?? 'tr'); };
assert.deepEqual(m.taskTerms('IF Inference'), ['inferenc']);
assert.deepEqual(slugsIn(m.indexReferences([row('inf', 'Inference engines', 30)]), 'INFERENCE'), ['inf']);
String.prototype.toLocaleLowerCase = localeLower;
// Folding: plurals, -ies, -ly, -ing and -ed with a doubled consonant, a final
// e, and no stripping that would leave a stem under four letters.
for (const [word, term] of [
  ['memories', 'memory'], ['locally', 'local'], ['planning', 'plan'], ['logging', 'log'],
  ['embedding', 'embed'], ['embedded', 'embed'], ['GPUs', 'gpu'], ['status', 'status'],
  ['class', 'class'], ['rolling', 'roll'], ['mode', 'mode'], ['speed', 'speed'],
  ['string', 'string'], ['adding', 'adding'], ['evaluate', 'evaluat'],
]) assert.deepEqual(m.taskTerms(word), [term], word);
// Filler forms the folding cannot reach are listed, and "vs" joins two subjects.
assert.deepEqual(m.taskTerms('giving made used'), []);
assert.deepEqual(m.taskTerms('mlx vs ollama versus llama.cpp'), ['mlx', 'ollama', 'llamacpp']);
// Words that name Object.prototype members are ordinary words, never lookups.
for (const word of ['constructor', '__proto__', 'toString', 'hasOwnProperty', 'valueOf']) {
  assert.doesNotThrow(() => m.taskHits(`agent ${word}`, items), word);
}
// An agent noun also counts as the form names spell out.
assert.deepEqual(slugs('reranker'), ['rag']);
// A term under five letters must be a whole word; a longer one may begin a word.
const words = m.indexReferences([row('model', 'Model routing', 30), row('agentic', 'Agentic RAG', 30)]);
assert.deepEqual(slugsIn(words, 'mode'), []);
assert.deepEqual(slugsIn(words, 'agent'), ['agentic']);
// A short abbreviation also counts as the long form a name spells out.
assert.deepEqual(slugsIn(m.indexReferences([row('docs', 'Documentation linting', 30)]), 'docs'), ['docs']);
// A compound with one usable part still matches that part written apart.
const judge = m.indexReferences([row('judge', 'LLM as a judge calibration', 30)]);
assert.deepEqual(slugsIn(judge, 'LLM-as-a-judge'), ['judge']);
// The joined compound outranks the same compound found only as parts.
const joined = m.indexReferences([row('apart', 'KV cache tiers', 20), row('joined', 'KV-cache tiers', 20)]);
assert.deepEqual(slugsIn(joined, 'kv-cache'), ['joined', 'apart']);
// Ties fall to the bigger pack, then to the name.
const ties = m.indexReferences([row('b', 'Beta agent', 10), row('a', 'Alpha agent', 10), row('c', 'Gamma agent', 50)]);
assert.deepEqual(slugsIn(ties, 'agent'), ['c', 'a', 'b']);
// An index name joins slashed compounds too.
assert.deepEqual(slugsIn(m.indexReferences([row('tcp', 'TCP/IP tuning', 30)]), 'tcpip'), ['tcp']);
// A ?q= link can carry any length; the search stays bounded.
const started = performance.now();
m.taskHits('a-'.repeat(50000), items);
m.taskHits('x'.repeat(100000), items);
assert.ok(performance.now() - started < 500, 'long queries must not freeze the page');
// A row without aliases or topics indexes instead of throwing.
m.indexReferences([{ slug: 'bare', concept: 'Bare row', facts: 9, download: '/downloads/concepts/bare.md', family: null, familySlug: null }]);

// Facet titles become search text without list numbers or markup.
for (const [title, clean] of [
  ['1. Naive-RAG failure points', 'Naive-RAG failure points'], ['3.2 Foo bar', 'Foo bar'],
  ['1) Bar', 'Bar'], ['5a. Thing', 'Thing'], ['2025-2026 frontier', '2025-2026 frontier'],
  ['12V-2x6 Connector', '12V-2x6 Connector'], ['Blackwell sm_120 kernels', 'Blackwell sm_120 kernels'],
  ['SHARED\\_TASK\\_NOTES.md', 'SHARED_TASK_NOTES.md'], ['*Confidence: High*', 'Confidence: High'],
  ['  `code`   spacing ', 'code spacing'],
]) assert.equal(m.cleanTitle(title), clean, title);

const text = m.promptReference('Prompt caching', 'https://llms-explorer.com/downloads/concepts/prompt-caching.md');
assert.match(text, /^Read this reference file before you answer: https:\/\/llms-explorer\.com\/downloads\/concepts\/prompt-caching\.md\n/);
assert.match(text, /about Prompt caching\. Cite the source of each fact you use/);
assert.match(text, /tell me when the file does not cover part of my question\.$/);
console.log('ok');
"""


def test_task_search_ranks_by_covered_terms():
    assert _node(HARNESS).strip() == "ok"


def test_every_curated_pick_resolves():
    """A nightly snapshot that merges or renames a curated concept fails here, so
    the list gets updated, instead of the page quietly losing a row. A curated
    read must also be one the site stands behind: not noindex, not unverified."""
    context = json.loads(CONTEXT.read_text(encoding="utf-8"))
    nodes = json.loads(TREE.read_text(encoding="utf-8"))["nodes"]
    concepts = {c["slug"] for r in context["roots"] for c in r["concepts"]}
    assert AI_ROOT in {r["slug"] for r in context["roots"]}, AI_ROOT
    assert len({t["id"] for t in TASKS}) == len(TASKS), "task ids must be unique"
    gone = []
    for task in TASKS:
        if task["family"] not in nodes:
            gone.append(f"{task['id']}: family {task['family']}")
        gone += [f"{task['id']}: reference {s}" for s in task["references"] if s not in concepts]
        for read in task["reads"]:
            path = SITE / "src" / "content" / read["collection"] / f"{read['id']}.md"
            front = path.read_text(encoding="utf-8").split("\n---", 1)[0] if path.is_file() else ""
            if not front:
                gone.append(f"{task['id']}: {read['collection']}/{read['id']}")
            elif re.search(r"^noindex:\s*true|^evidenceStatus:", front, re.M):
                gone.append(f"{task['id']}: {read['collection']}/{read['id']} is noindex or unverified")
        gone += [f"{task['id']}: skill {s}" for s in task["skills"]
                 if not (SITE / "src" / "content" / "skills" / f"{s}.md").is_file()]
    assert not gone, gone


def _built_file(*parts: str) -> Path:
    """Skip when the site was never built; fail when it was built without the file."""
    if not DIST.is_dir():
        pytest.skip("no site/dist — run `npm run build` first")
    path = DIST.joinpath(*parts)
    assert path.is_file(), f"site/dist is built but {'/'.join(parts)} is missing"
    return path


@pytest.fixture(scope="module")
def page() -> str:
    return _built_file("research", "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def index() -> dict:
    return json.loads(_built_file("research", "references.json").read_text(encoding="utf-8"))


def _built(href: str) -> bool:
    target = DIST / href.lstrip("/")
    return target.is_file() or (target / "index.html").is_file()


def _hidden(tag: str) -> bool:
    return re.search(r"\shidden(?=[\s>=])", tag) is not None


def test_navigation_and_home_page_lead_to_the_page(page):
    assert re.search(r'<a href="/research/"[^>]*\baria-current="page"', page), "the nav marks /research/ current"
    home = _built_file("index.html").read_text(encoding="utf-8")
    assert 'href="/research/"' in home[home.index("<main"):home.index("</main>")], "the home page body links the page"


def _task_bodies(page: str) -> dict[str, str]:
    """Each curated task's id and the markup inside its <details>."""
    return dict(re.findall(r'<details class="rs-task[^"]*"[^>]*id="task-([a-z0-9-]+)"[^>]*>(.*?)</details>', page, re.S))


def test_every_task_renders_its_picks(page):
    tasks = _task_bodies(page)
    assert list(tasks) == [t["id"] for t in TASKS], "the page lost, gained or reordered tasks"
    for spec in TASKS:
        body = tasks[spec["id"]]
        rows = re.findall(r'<li class="rs-ref[^"]*"', body)
        assert len(rows) == len(spec["references"]), f"task {spec['id']} dropped a reference"
        downloads = re.findall(r'href="(/downloads/concepts/[^"]+\.md)"', body)
        assert len(downloads) == len(rows), f"task {spec['id']}: every reference row offers its facts file"
        assert all(_built(href) for href in downloads), spec["id"]
        reads = re.search(r'<ul class="rs-reads"[^>]*>(.*?)</ul>', body, re.S)
        assert len(re.findall(r"<li>", reads.group(1) if reads else "")) == len(spec["reads"]), f"task {spec['id']} dropped a read"
        assert len(re.findall(r'class="rs-skill-name"', body)) == len(spec["skills"]), f"task {spec['id']} dropped a skill"
        buttons = re.findall(r'<button[^>]*\bclass="rs-copy"[^>]*>', body)
        assert len(buttons) == len(rows) + len(spec["skills"]), spec["id"]
        assert all(_hidden(tag) for tag in buttons), f"task {spec['id']}: copy buttons ship hidden for readers without JavaScript"


def test_copied_prompts_name_the_public_facts_files(page):
    urls = re.findall(r'data-url="([^"]+)"', page)
    assert urls, "no copy buttons carry a facts-file URL"
    for url in urls:
        assert re.fullmatch(rf"{re.escape(PUBLIC)}/downloads/concepts/[^/]+\.md", url), url
        assert _built(url.removeprefix(PUBLIC)), url
    install = re.findall(r'data-text="(npx skills add mithudso/llms-explorer --skill ([a-z0-9-]+))"', page)
    assert len(install) == sum(len(t["skills"]) for t in TASKS)
    for _, skill in install:
        assert _built(f"/skills/{skill}/"), skill


def test_the_search_template_carries_no_links(page):
    template = re.search(r'<template id="rs-ref-template"[^>]*>(.*?)</template>', page, re.S)
    assert template, "the search row template is missing"
    assert "href=" not in template.group(1), "the template is filled per result; a placeholder link would be dead"
    assert 'data-field="name"' in template.group(1) and 'data-field="download"' in template.group(1)


def test_the_script_finds_every_element_it_binds_to(page):
    """The loading, empty, error-retry and copy-fallback states run only in a
    browser. They bind to ids and data-field names in the markup, so a rename
    would leave a page that builds and passes every other test with a dead search."""
    source = PAGE_SOURCE.read_text(encoding="utf-8")
    script = source[source.index("<script>"):]
    ids = set(re.findall(r'byId(?:<[^>]+>)?\("([a-z-]+)"\)', script))
    assert {"rs-form", "rs-retry", "rs-status", "rs-empty", "rs-results", "rs-ref-template", "rs-fallback"} <= ids
    for element in ids:
        assert f'id="{element}"' in page, f"the script binds to #{element}, which the page lacks"
    for element in ("rs-form", "rs-examples", "rs-results", "rs-empty", "rs-retry", "rs-fallback"):
        tag = re.search(rf'<[a-z]+ [^>]*\bid="{element}"[^>]*>', page)
        assert tag and _hidden(tag.group(0)), f"#{element} must ship hidden; the script shows it"
    template = re.search(r'<template id="rs-ref-template"[^>]*>(.*?)</template>', page, re.S)
    assert template, "the search row template is missing"
    for name in set(re.findall(r'field(?:<[^>]+>)?\("([a-z-]+)"\)', script)):
        assert f'data-field="{name}"' in template.group(1), f"the script fills data-field={name}; the template lacks it"
    assert 'class="rs-copy"' in template.group(1)
    bundles = [DIST / src.lstrip("/") for src in re.findall(r'<script type="module" src="(/_astro/[^"]+\.js)"', page)]
    assert any("/research/references.json" in b.read_text(encoding="utf-8") for b in bundles), \
        "no shipped script fetches /research/references.json"


def test_the_search_index_lists_every_ai_facts_file(index):
    context = json.loads(CONTEXT.read_text(encoding="utf-8"))
    expected = [c for r in context["roots"] if r["slug"] == AI_ROOT for c in r["concepts"]]
    assert expected, f"context.json has no concepts under root {AI_ROOT}"
    assert index["root"] == AI_ROOT
    assert index["count"] == len(index["items"]) == len(expected)
    assert {i["slug"] for i in index["items"]} == {c["slug"] for c in expected}
    keys = {"slug", "concept", "facts", "download", "family", "familySlug", "aliases", "topics"}
    for item in index["items"]:
        assert set(item) == keys, item["slug"]
        assert _built(item["download"]), item["download"]
        assert _built(f"/tree/{item['slug']}/"), item["slug"]
        if item["familySlug"]:
            assert _built(f"/tree/{item['familySlug']}/"), item["familySlug"]
        assert len(item["topics"]) <= 12


def test_the_search_index_keeps_clean_distinctive_facet_titles(index):
    """Facet titles are most of what search can match beyond a name. A title most
    packs share ("Definitions", "Overview") would match half the index; a broken
    pack lookup would leave every row with its family alone."""
    rich = [i for i in index["items"] if len(i["topics"]) > 1]
    assert len(rich) >= 80, f"only {len(rich)} rows carry facet titles; the pack lookup may be broken"
    for item in index["items"]:
        assert not {"definitions", "overview", "sources", "how it works"} & {t.lower() for t in item["topics"]}, item["slug"]
        for topic in item["topics"]:
            assert not re.match(r"^\s*\d+(\.\d+)*[a-z]?[.)]\s", topic), topic
            assert not re.search(r"[*`]|\\", topic), topic
            assert topic == topic.strip() and "  " not in topic, topic


def test_the_search_index_publishes_no_private_text(index):
    raw = json.dumps(index, ensure_ascii=False)
    leak = re.search(r"/Users/|/home/[^/\s]+/|~/|\b\d{1,3}(?:\.\d{1,3}){3}\b|\.ts\.net|tailscale|\.lan\b", raw)
    assert not leak, leak.group(0)


@pytest.mark.usefixtures("index")
def test_the_search_index_stays_small():
    size = (DIST / "research" / "references.json").stat().st_size
    assert size < 600_000, f"references.json is {size} bytes; /search-keywords.json-sized payloads defeat lazy loading"


EXAMPLES = r"""
const items = m.indexReferences(JSON.parse(readFileSync(process.argv[2], 'utf8')).items);
console.log(JSON.stringify(process.argv.slice(3).map((q) => {
  const found = m.taskHits(q, items);
  return { q, total: found.total, complete: found.complete };
})));
"""


# Spellings a reader types that once found nothing or the wrong packs: a
# hyphenated phrase with filler inside, an acronym plural, inflected verbs.
PROBES = ["LLM-as-a-judge", "tool-use", "GPUs", "planning", "embedding", "docs", "reranker", "mlx vs ollama"]


def test_every_suggested_query_finds_a_full_match(page):
    """A suggestion that returns nothing, or only partial matches, teaches a new
    reader that search does not work."""
    queries = [html.unescape(q) for q in re.findall(r'class="rs-chip"[^>]*data-query="([^"]+)"', page)]
    assert len(queries) >= 4, queries
    queries += PROBES
    results = json.loads(_node(EXAMPLES, str(_built_file("research", "references.json")), *queries))
    weak = [r for r in results if not (r["total"] and r["complete"])]
    assert not weak, weak


def test_the_twin_lists_every_pick_with_absolute_links(page):
    """Agents read /research.md instead of the HTML; twins.py writes it from the
    same research-tasks.json the page renders."""
    assert '<link rel="alternate" type="text/markdown" href="/research.md"' in page
    twin = _built_file("research.md").read_text(encoding="utf-8")
    assert twin.startswith("<!-- llms-explorer twin of ")
    rows = re.findall(r"^- \[.*\]\((\S+)\)$", twin, re.M)
    picks = sum(len(t["references"]) + len(t["reads"]) + len(t["skills"]) for t in TASKS)
    assert len(rows) == picks, "the twin dropped a reference, read or skill"
    assert f"## What this section holds ({picks})" in twin
    for task in TASKS:
        assert f"- [{task['title']} · " in twin, task["id"]
    for url in rows:
        assert url.startswith(f"{PUBLIC}/"), f"twin links must be absolute: {url}"
        assert _built(url.removeprefix(PUBLIC)), url


def test_the_page_and_the_twin_list_the_same_facts_files(page):
    twin = _built_file("research.md").read_text(encoding="utf-8")
    on_page = {h for body in _task_bodies(page).values() for h in re.findall(r'href="(/downloads/concepts/[^"]+\.md)"', body)}
    in_twin = set(re.findall(r"\]\(https?://[^/)]+(/downloads/concepts/[^)]+\.md)\)", twin))
    assert on_page and on_page == in_twin


def test_the_twin_drops_dead_picks_and_emptied_tasks(tmp_path, capsys):
    """_research_rows resolves against the directories it is given, leaves out a
    pick the build lacks, and leaves out a task whose facts files are all gone,
    as the page does."""
    content, data = tmp_path / "content", tmp_path / "data"
    for folder in ("blog", "skills"):
        (content / folder).mkdir(parents=True)
    (content / "blog" / "live-post.md").write_text('---\ntitle: "Live post"\ndescription: "d"\n---\nbody\n')
    (content / "skills" / "live-skill.md").write_text('---\ntitle: "live-skill"\ndescription: "d"\n---\nbody\n')
    data.mkdir()
    (data / "context.json").write_text(json.dumps({"roots": [{"slug": "root", "concepts": [
        {"slug": "alive", "concept": "Alive", "download": "/downloads/concepts/alive.md"}]}]}))
    spec = {"tasks": [
        {"id": "kept", "title": "Kept task", "references": ["alive", "gone"],
         "reads": [{"collection": "blog", "id": "live-post", "kind": "Guide"},
                   {"collection": "blog", "id": "dead-post", "kind": "Guide"}],
         "skills": ["live-skill", "dead-skill"]},
        {"id": "emptied", "title": "Emptied task", "references": ["gone"],
         "reads": [{"collection": "blog", "id": "live-post", "kind": "Guide"}], "skills": ["live-skill"]},
    ]}
    rows = twins._research_rows(spec, content_dir=content, data_dir=data)
    assert rows == [
        ("Kept task · Alive — facts", "/downloads/concepts/alive.md"),
        ("Kept task · Guide: Live post", "/blog/live-post/"),
        ("Kept task · skill: live-skill", "/skills/live-skill/"),
    ]
    printed = capsys.readouterr().out
    for dropped in ("kept: reference gone", "kept: blog dead-post", "kept: skill dead-skill", "emptied: the whole task"):
        assert dropped in printed, dropped
