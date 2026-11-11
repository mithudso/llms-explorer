"""Corpus boundaries, provenance and exact span regression tests."""

import hashlib
import json
from pathlib import Path

import pytest


pytest.importorskip("research_expertise", reason="Standalone expertise package has its own CI")

from research_expertise.corpus import (
    chunk_document,
    extract_urls,
    iter_documents,
    iter_relations,
)


def pack(root: Path, slug="topic", text="Source prose", **metadata) -> Path:
    path = root / f"{slug}.llms"
    path.mkdir(parents=True)
    (path / "manifest.json").write_text(json.dumps({"concept": slug, **metadata}))
    (path / "llms-facts.txt").write_text(text)
    return path


def test_one_canonical_rendering_and_no_research_or_staging(tmp_path):
    concepts = tmp_path / "llms-concepts"
    path = pack(concepts)
    (path / "llms-full.txt").write_text("Duplicate rendering")
    (path / "llms-small.txt").write_text("Another duplicate")
    pack(concepts, ".hidden")
    pack(concepts, "staging")
    pack(tmp_path / "research", "other")
    docs = list(iter_documents(tmp_path))
    assert len(docs) == 1
    assert docs[0]["text"] == "Source prose"
    assert docs[0]["relative_path"] == "topic.llms/llms-facts.txt"


def test_changed_bytes_change_sha_and_chunks_not_logical_id(tmp_path):
    path = pack(tmp_path, text="Original prose", research_status="COMPLETED")
    original = next(iter_documents(tmp_path))
    (path / "llms-facts.txt").write_text("Revised prose")
    revised = next(iter_documents(tmp_path))
    assert original["id"] == revised["id"]
    assert original["sha256"] != revised["sha256"]
    assert chunk_document(original)[0]["id"] != chunk_document(revised)[0]["id"]
    assert revised["qualification"] == "unreviewed"
    assert revised["claimed_status"] == "COMPLETED"


def test_manifest_hash_is_distinct_and_claimed_support_is_not_proof(tmp_path):
    path = pack(tmp_path, validation_status="SUPPORTED")
    original = next(iter_documents(tmp_path))
    (path / "manifest.json").write_text('{"research_status":"SUPPORTED"}')
    revised = next(iter_documents(tmp_path))
    assert original["manifest_sha256"] != revised["manifest_sha256"]
    assert original["sha256"] == revised["sha256"]
    assert revised["qualification"] == "unreviewed"


def test_unicode_crlf_spans_are_exact_and_cover_whole_source(tmp_path):
    text = "# Résumé 🧠\r\n\r\n" + "café 🚀 evidence\r\n" * 100
    path = pack(tmp_path)
    (path / "llms-facts.txt").write_bytes(text.encode())
    doc = next(iter_documents(tmp_path))
    assert doc["sha256"] == hashlib.sha256(text.encode()).hexdigest()
    assert doc["text"] == text
    chunks = chunk_document(doc, max_chars=100, overlap=10)
    covered = set()
    for chunk in chunks:
        assert chunk["text"] == text[chunk["start"] : chunk["end"]]
        assert len(chunk["text"]) <= 100
        assert chunk["start_line"] == text[: chunk["start"]].count("\n") + 1
        assert chunk["end_line"] == text[: chunk["end"] - 1].count("\n") + 1
        covered.update(range(chunk["start"], chunk["end"]))
    assert covered == set(range(len(text)))
    assert chunks[-1]["end"] == len(text)


@pytest.mark.parametrize("max_chars,overlap", [(0, 0), (20, -1), (20, 20)])
def test_invalid_chunk_options_fail(max_chars, overlap):
    with pytest.raises(ValueError):
        chunk_document({"text": "a"}, max_chars=max_chars, overlap=overlap)


def test_external_symlinks_do_not_import_prose_or_manifest(tmp_path):
    root = tmp_path / "corpus"
    root.mkdir()
    outside = pack(tmp_path / "outside", "secret")
    (root / "external.llms").symlink_to(outside, target_is_directory=True)
    internal = pack(root, "internal")
    (internal / "llms-facts.txt").unlink()
    (internal / "llms-facts.txt").symlink_to(outside / "llms-facts.txt")
    assert list(iter_documents(root)) == []
    (internal / "manifest.json").unlink()
    (internal / "manifest.json").symlink_to(outside / "manifest.json")
    (internal / "llms-full.txt").write_text("Still must not import")
    assert list(iter_documents(root)) == []


def test_hub_concept_symlink_cannot_escape_supplied_root(tmp_path):
    hub = tmp_path / "hub"
    hub.mkdir()
    outside = tmp_path / "outside"
    pack(outside)
    (hub / "llms-concepts").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="escapes corpus root"):
        list(iter_documents(hub))


def test_full_fallback_without_duplicate_small(tmp_path):
    path = pack(tmp_path)
    (path / "llms-facts.txt").unlink()
    (path / "llms-full.txt").write_text("Full source")
    assert next(iter_documents(tmp_path))["relative_path"] == "topic.llms/llms-full.txt"


def test_urls_strip_markdown_closers_preserve_balanced_parentheses():
    assert extract_urls(
        "[one](https://example.com/a_(b)) and https://example.org/x?q=1, "
        "https://example.net/path#anchor. file:///private/test"
    ) == [
        "https://example.com/a_(b)",
        "https://example.net/path#anchor",
        "https://example.org/x?q=1",
    ]


def test_only_explicit_existing_child_paths_become_graph_edges(tmp_path):
    pack(
        tmp_path,
        "parent",
        children={
            "child": {"path": "child.llms"},
            "missing": {"path": "missing.llms"},
            "escape": {"path": "../outside.llms"},
        },
    )
    pack(tmp_path, "child")
    rows = list(iter_relations(tmp_path))
    assert len(rows) == 1
    assert (rows[0]["source"], rows[0]["target"], rows[0]["relation"]) == (
        "parent",
        "child",
        "HAS_CHILD",
    )
    manifest = tmp_path / "parent.llms" / "manifest.json"
    assert rows[0]["source_path"] == str(manifest)
    assert rows[0]["source_sha256"] == hashlib.sha256(manifest.read_bytes()).hexdigest()
    assert rows[0]["navigation_only"] is True


def tree_file(hub, nodes):
    tree = hub / "concept-tree" / "tree.json"
    tree.parent.mkdir(parents=True, exist_ok=True)
    tree.write_text(json.dumps(nodes))
    return tree


def test_tree_links_declared_topics_without_fabricating_prose_packs(tmp_path):
    root = tmp_path / "llms-concepts"
    pack(root, "child")
    tree = tree_file(
        tmp_path,
        [
            {"slug": "parent", "concept": "Parent", "childConcepts": ["Child", "Missing"]},
            {"slug": "child", "concept": "Child", "parentConcept": "Parent"},
        ],
    )
    rows = list(iter_relations(root))
    assert len(rows) == 1  # parent/child declarations describe the same edge
    row = rows[0]
    assert (row["source"], row["target"], row["relation"]) == ("parent", "child", "TOPIC_CHILD")
    assert row["source_title"] == "Parent"
    assert row["target_title"] == "Child"
    assert row["source_path"] == str(tree)
    assert row["source_sha256"] == hashlib.sha256(tree.read_bytes()).hexdigest()
    assert row["navigation_only"] is True
    assert [doc["concept"] for doc in iter_documents(root)] == ["child"]


def test_tree_changes_invalidate_relation_fingerprint(tmp_path):
    root = tmp_path / "llms-concepts"
    pack(root, "child")
    nodes = [
        {"slug": "parent", "concept": "Parent", "childConcepts": ["Child"]},
        {"slug": "child", "concept": "Child"},
    ]
    tree = tree_file(tmp_path, nodes)
    original = next(iter_relations(root))
    tree.write_text(json.dumps(nodes, indent=2))
    revised = next(iter_relations(root))
    assert original["source_sha256"] != revised["source_sha256"]


def test_tree_ambiguous_names_or_slugs_and_unknown_targets_are_not_guessed(tmp_path):
    root = tmp_path / "llms-concepts"
    pack(root, "topic")
    tree_file(
        tmp_path,
        [
            {"slug": "parent", "concept": "Parent", "childConcepts": ["Child", "Unknown"]},
            {"slug": "child", "concept": "Child"},
            {"slug": "other-child", "concept": "CHILD"},
            {"slug": "parent", "concept": "Duplicate slug"},
        ],
    )
    assert list(iter_relations(root)) == []


def test_tree_symlink_outside_hub_is_not_imported(tmp_path):
    hub = tmp_path / "hub"
    root = hub / "llms-concepts"
    pack(root)
    outside = tree_file(
        tmp_path / "outside",
        [
            {"slug": "a", "concept": "A", "childConcepts": ["B"]},
            {"slug": "b", "concept": "B"},
        ],
    )
    (hub / "concept-tree").mkdir()
    (hub / "concept-tree" / "tree.json").symlink_to(outside)
    assert list(iter_relations(root)) == []


def test_malformed_manifest_reports_failure_instead_of_partial_silent_success(tmp_path):
    path = pack(tmp_path)
    (path / "manifest.json").write_text("{oops")
    with pytest.raises(ValueError, match="Invalid corpus manifest"):
        list(iter_documents(tmp_path))


class CharacterTokenizer:
    """Token-dense stand-in whose offsets retain Unicode character positions."""

    def encode(self, text, add_special_tokens=False):
        assert add_special_tokens is False
        return type(
            "Encoding",
            (),
            {
                "ids": list(range(len(text))),
                "offsets": [(i, i + 1) for i in range(len(text))],
            },
        )()


def test_token_aware_unicode_chunks_cover_source_and_cannot_stall(tmp_path):
    text = '{"café🚀": [x=>x!==null]}\n' * 12
    pack(tmp_path, text=text)
    doc = next(iter_documents(tmp_path))
    tokenizer = CharacterTokenizer()
    chunks = chunk_document(doc, max_chars=100, overlap=80, tokenizer=tokenizer, max_tokens=20)
    covered = set()
    for chunk in chunks:
        assert chunk["text"] == text[chunk["start"] : chunk["end"]]
        assert len(tokenizer.encode(chunk["text"]).ids) <= 20
        covered.update(range(chunk["start"], chunk["end"]))
    assert covered == set(range(len(text)))
    assert all(a["start"] < b["start"] for a, b in zip(chunks, chunks[1:], strict=False))
    assert chunks[-1]["end"] == len(text)


def test_invalid_token_limit_fails(tmp_path):
    pack(tmp_path)
    with pytest.raises(ValueError, match="max_tokens"):
        chunk_document(next(iter_documents(tmp_path)), max_tokens=0)
