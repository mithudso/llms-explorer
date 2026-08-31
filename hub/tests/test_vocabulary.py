"""docset_refine vocabulary: candidates, evidence, extractive entries, verified
LLM entries, rendering, alias registration."""

import json

import pytest

import concept_tree as ct
from docset_refine import topical, vocabulary as V

NODES = [
    {"concept": "llms.txt and LLM-readable documentation", "skillId": "document-formats",
     "parentConcept": None, "childConcepts": ["llms-full.txt page grammars"],
     "researchedAt": "2026-08-30"},
    {"concept": "llms-full.txt page grammars", "skillId": "document-formats",
     "parentConcept": "llms.txt and LLM-readable documentation", "childConcepts": [],
     "researchedAt": "2026-08-30", "aliases": ["full file"]},
]


def _pool():
    return [
        topical._rec(1, "definition", "`llms-full.txt` is the whole docset inlined as one markdown "
                     "file, unlike `llms.txt`, which is only an index.", "https://a/1",
                     keywords=["llms-full.txt", "llms.txt"]),
        topical._rec(2, "statement", "Starlight ships `llms-small.txt` (also called the small "
                     "variant) beside `LLMs-Full.txt`.", "https://b/2",
                     keywords=["llms-small.txt", "LLMs-Full.txt"]),
        topical._rec(3, "statement", "Consumers break above 50k tokens, so producers split "
                     "`llms-full.txt` rather than truncating it.", "https://c/3",
                     keywords=["llms-full.txt", "llms.txt"]),
        topical._rec(4, "statement", "A `.md` twin is served per page.", "https://d/4",
                     keywords=[".md"]),
        topical._rec(5, "statement", "Page grammars differ per host.", "https://e/5",
                     keywords=["page grammars"]),
    ]


@pytest.fixture
def tree(tmp_path, monkeypatch):
    tp = tmp_path / "tree.json"
    tp.write_text(json.dumps(NODES))
    (tmp_path / "RESEARCH_QUEUE.md").write_text("# q\n")
    monkeypatch.setattr(ct, "TREE_PATH", tp)
    monkeypatch.setattr(ct, "QUEUE_PATH", tmp_path / "RESEARCH_QUEUE.md")
    t = ct.ConceptTree.load()
    ct.ensure_slugs(t.nodes)
    return t


def test_normalise_and_token_clusters():
    assert V.normalise("`LLMs-Full.txt`") == V.normalise("llms full txt") == "llmsfulltxt"
    assert V.normalise("./llms.txt") == "llmstxt"
    clusters = V.token_clusters(_pool())
    assert clusters["llmsfulltxt"].most_common(1)[0][0] == "llms-full.txt"
    assert "LLMs-Full.txt" in clusters["llmsfulltxt"]


def test_syntax_examples_and_plain_words_are_not_terms():
    pool = [topical._rec(i, "statement", f"x {i}", "https://s", keywords=k) for i, k in
            enumerate([["# Title", "url:", "- [name](url): description", "> Documentation Index",
                        "x-markdown-tokens", "promote", "sections", "/map"]] * 2)]
    keys = set(V.token_clusters(pool))
    assert keys == {"xmarkdowntokens", "map"}          # bare words out; a path-like token stays


def test_candidates_tree_first_then_tokens(tree):
    terms = V.candidates(_pool(), tree, "llms.txt and LLM-readable documentation")
    keys = [t["key"] for t in terms]
    assert keys[0] == V.normalise("llms.txt and LLM-readable documentation")
    assert terms[1]["term"] == "llms-full.txt page grammars" and terms[1]["aka"] == ["full file"]
    full = next(t for t in terms if t["key"] == "llmsfulltxt")
    assert full["kind"] == "token" and full["aka"] == ["LLMs-Full.txt"]
    assert "llmssmalltxt" not in keys                  # single use → not a term


def test_entries_extractive_definition_contrast_and_aka(tree):
    pool = _pool()
    terms = V.candidates(pool, tree, "llms.txt and LLM-readable documentation")
    entries = {e["key"]: e for e in V.build_entries(pool, terms)}
    full = entries["llmsfulltxt"]
    assert full["definition"].startswith("`llms-full.txt` is the whole docset")
    assert full["definition_source"] == "https://a/1" and full["origin"] == "extractive"
    assert [n["term"] for n in full["not"]] == ["llms.txt"]        # "unlike `llms.txt`"
    assert full["evidence"] == 3
    # single-use tokens are not terms; concept nodes always get an entry
    assert V.normalise("llms-full.txt page grammars") in entries


def test_llm_entry_is_verified_against_evidence():
    term = {"term": "llms-small.txt", "key": "llmssmalltxt", "aka": [], "kind": "token"}
    units = _pool()[1:2]
    reply = json.dumps({"definition": "The small variant Starlight ships beside llms-full.txt.",
                        "differs_from": [{"term": "llms-full.txt",
                                          "how": "shipped beside llms-full.txt as the small "
                                                 "variant"},
                                         {"term": "sitemap.xml", "how": "invented"}],
                        "aka": ["small variant", "tiny file"]})
    got = V.llm_entry(term, units, generate=lambda *a, **k: "junk " + reply + " trailing")
    assert got["definition"].startswith("The small variant") and got["grounding"] >= 0.6
    assert [d["term"] for d in got["differs_from"]] == ["llms-full.txt"]  # sitemap invented
    assert got["aka"] == ["small variant"]        # cue-backed ("also called"); tiny file invented
    # a paraphrase whose content is not in the evidence is dropped
    bad = json.dumps({"definition": "A file that describes language models for search engines.",
                      "differs_from": [{"term": "llms-small.txt", "how": "beside llms-full.txt"}],
                      "aka": []})
    got = V.llm_entry(term, units, generate=lambda *a, **k: bad)
    assert "definition" not in got and got["differs_from"] == []    # self-contrast dropped
    assert "definition" in V.llm_entry(term, units, generate=lambda *a, **k: bad, floor=0.0)
    assert V.llm_entry(term, units, generate=lambda *a, **k: "no json here") == {}


def test_run_renders_registers_and_updates_manifest(tree, tmp_path, monkeypatch):
    monkeypatch.setattr(V, "load_pool", lambda paths: (_pool(), []))
    out = tmp_path / "t.llms"
    out.mkdir()
    (out / "manifest.json").write_text(json.dumps({"files": {"llms.txt": {"bytes": 1}}}))
    calls = []

    def fake_llm(term, units):
        calls.append(term["term"])
        return {"definition": "Grammars are the page-block shapes producers use.",
                "grounding": 0.4, "differs_from": [], "aka": []}
    res = V.run([tmp_path / "x.md"], "llms.txt and LLM-readable documentation", out, tree=tree,
                llm=fake_llm, register=True, log=lambda *_: None)
    text = (out / "llms-vocabulary.txt").read_text()
    assert text.startswith("# llms.txt and LLM-readable documentation — vocabulary\n\n> ")
    assert "## Terms" in text
    assert ("- **llms-full.txt** — `llms-full.txt` is the whole docset inlined as one markdown "
            "file, unlike `llms.txt`, which is only an index. · aka: LLMs-Full.txt · "
            "not: llms.txt · differs: unlike `llms.txt`, which is only an index. "
            "— https://a/1") in text
    # the parenthetical "(also called the small variant)" belongs to llms-small.txt, not to
    # llms-full.txt; and llms.txt does not inherit llms-full.txt's definition
    assert "the small variant" not in text.split("- **llms-full.txt**")[1].split("\n")[0]
    llms_line = next(ln for ln in text.splitlines() if ln.startswith("- **llms.txt**"))
    assert "whole docset" not in llms_line
    assert "— https://a/1" in text
    assert "origin: llm (grounded" in text            # the grammars node got an LLM definition
    man = json.loads((out / "manifest.json").read_text())
    assert man["files"]["llms-vocabulary.txt"]["bytes"] > 0 and man["vocabulary"]["terms"] >= 3
    assert res["defined"] >= 2 and res["llm"] >= 1
    vj = json.loads((out / "vocabulary.json").read_text())
    assert vj["subject"] == "llms.txt and LLM-readable documentation"
    # aliases registered add-only on the matching node
    saved = json.loads(ct.TREE_PATH.read_text())
    node = next(n for n in saved if n["concept"] == "llms-full.txt page grammars")
    assert "full file" in node["aliases"]
    # a term with no definition lands under "Named, not yet defined" (none here) — the
    # section only appears when needed
    assert ("## Named, not yet defined" in text) == any(
        not e["definition"] for e in vj["terms"])


def test_research_gathers_estate_evidence_and_defines(tree, tmp_path, monkeypatch):
    # an estate: one docset facts layer, one other topical file, one mirrored llms-full.txt
    mirror = tmp_path / "text-mirror"
    (mirror / "acme.reference").mkdir(parents=True)
    (mirror / "acme.reference" / "all_units.jsonl").write_text(json.dumps({
        "type": "definition", "text": "llms-small.txt is a size-capped subset of llms-full.txt "
        "that Starlight ships for small-context tools.", "source_url": "https://acme/docs",
        "keywords": ["llms-small.txt"]}) + "\n")
    topical_dir = tmp_path / "llms-topical"
    (topical_dir / "other.llms").mkdir(parents=True)
    (topical_dir / "other.llms" / "units.jsonl").write_text(json.dumps({
        "type": "statement", "text": "Nuxt also publishes llms-small.txt beside llms-full.txt "
        "for consumers with a token budget.",
        "source_url": "https://nuxt/x", "keywords": []}) + "\n")
    full = tmp_path / "vendor.txt"
    full.write_text("# Sizes\nSource: https://vendor/sizes\n\nThe llms-small.txt file exists for "
                    "consumers that break above fifty thousand tokens. Other text here.\n"
                    + "x" * 1200)
    # an off-topic literal match: the same token in another world
    (mirror / "nativescript.reference").mkdir()
    (mirror / "nativescript.reference" / "all_units.jsonl").write_text(json.dumps({
        "type": "statement", "text": "llms-small.txt is a read-only property returning the "
        "parent view node.", "source_url": "https://ns/api", "keywords": []}) + "\n")
    entries = [{"key": "vendor", "file": str(full)}]
    pool = _pool()
    terms = V.candidates(pool, tree, "llms.txt and LLM-readable documentation")
    # llms-small.txt is named once in the pool → make it a term by a second use
    pool.append(topical._rec(9, "statement", "Ship `llms-small.txt` beside the full file.",
                             "https://z", keywords=["llms-small.txt"]))
    terms = V.candidates(pool, tree, "llms.txt and LLM-readable documentation")
    small = next(t for t in terms if t["key"] == "llmssmalltxt")
    assert V._definition_from(V.evidence(pool, small), small) is None     # undefined before
    extra = V.research(pool, terms, mirror_dir=mirror, topical_dir=topical_dir,
                       mirror_entries=entries, log=lambda *_: None)
    srcs = {r["source"] for r in extra}
    assert {"https://acme/docs", "https://nuxt/x", "https://vendor/sizes"} <= srcs
    assert "https://ns/api" not in srcs                                  # off-topic dropped
    assert all(r["research"] for r in extra)
    ent = {e["key"]: e for e in V.build_entries(pool + extra, terms)}
    assert ent["llmssmalltxt"]["definition"].startswith("llms-small.txt is a size-capped subset")
    assert ent["llmssmalltxt"]["definition_source"] == "https://acme/docs"


def test_queue_undefined_terms_and_run_flags(tree, tmp_path, monkeypatch):
    monkeypatch.setattr(V, "load_pool", lambda paths: (_pool(), []))
    monkeypatch.setattr(V, "estate_units", lambda *a, **k: iter([]))
    monkeypatch.setattr(V, "mirror_sentences", lambda *a, **k: iter([]))
    out = tmp_path / "t.llms"
    out.mkdir()
    res = V.run([tmp_path / "x.md"], "llms.txt and LLM-readable documentation", out, tree=tree,
                do_research=True, queue=True, log=lambda *_: None)
    assert res["research_units"] == 0 and res["queued"] >= 1
    queue = ct.QUEUE_PATH.read_text()
    assert "(term of llms.txt and LLM-readable documentation)" in queue
    assert "Parent: `llms.txt and LLM-readable documentation`" in queue
    # concept-kind terms are never queued as terms
    assert "llms-full.txt page grammars (term of" not in queue
    text = (out / "llms-vocabulary.txt").read_text()
    assert "## Named, not yet defined" in text
