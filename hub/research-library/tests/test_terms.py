"""A phrase search reads every stored row and names concepts, never the phrase."""
from __future__ import annotations

import json
import stat

import pytest
from test_store_core import Database, evidence_fixture, lease, make

from research_library_service import cli, terms
from research_library_service.service import Service
from research_library_service.store import LibraryStore


@pytest.fixture
def store():
    return LibraryStore(Database(), clock=lambda: 1000.0)


def library(store):
    named, claimed, clean = make(store, "Acme Corp renewal", "Pricing models", "Sharding")
    tokens = lease(store, [named, claimed, clean])["tokens"]
    _, claim = evidence_fixture(store)
    store.claim_mutate(claimed["_id"], "add", {**claim, "text": "The acme\ncorp contract ends."},
                       expected_revision=1, lease_token=tokens[claimed["_id"]])
    store.concept_update(clean["_id"], {"description": "Chunks move. Acmecorporate is a word."},
                         1, tokens[clean["_id"]])
    return named["_id"], claimed["_id"], clean["_id"]


def test_a_phrase_is_a_whole_word_or_phrase_in_any_spelling_of_its_gap():
    matcher = terms.compile_terms(["Acme Corp", "C++"])
    for text in ("ACME corp", "acme\n corp", "c:acme-corp-renewal", "acme_corp", "uses C++ here"):
        assert matcher.search(text), text
    for text in ("acmecorp", "acme corporate", "macme corp", "acme, corp"):
        assert not matcher.search(text), text
    for bad in ([], ["   "], ["---"], ["x" * 201], "acme"):
        with pytest.raises(ValueError):
            terms.compile_terms(bad)


def test_every_row_is_read_and_a_concept_is_named_with_the_fields_that_hold_a_phrase(store):
    named, claimed, clean = library(store)
    report = store.find_terms(["Acme Corp"])
    found = {entry["id"]: entry for entry in report["concepts"]}
    # A name is found in the listing fields, a claim only by reading the concept in full.
    assert set(found) == {named, claimed}
    assert "name" in found[named]["found_in"]["concepts"]
    assert "claims[].text" in found[claimed]["found_in"]["concepts"]
    assert "name" not in found[claimed]["found_in"]["concepts"]
    assert "versions" in found[claimed]["found_in"] and found[claimed]["claims"] == 1
    assert found[named]["exists"] is True and found[named]["state"] == "frontier"
    assert report["rows_with_a_phrase"]["concepts"] == 2 and report["rows_read"]["concepts"] == 3
    assert report["rows_with_a_phrase"]["receipts"] >= 2
    assert report["not_read"] == ["snapshot_chunks", "artifact_chunks", "artifact_units"]
    # The phrase itself is never part of the answer.
    assert "acme corp" not in json.dumps([report["rows_read"], report["rows_with_a_phrase"]]).lower()
    assert clean not in found
    # After a purge the concept is gone from the search too.
    store.purge_concepts([named], apply=True, include_held=True)
    assert named not in {entry["id"] for entry in store.find_terms(["Acme Corp"])["concepts"]}


def test_the_search_is_owner_local_and_writes_its_findings_to_private_files(store, tmp_path):
    named, claimed, _ = library(store)
    service = Service(store=store)
    for role, actor in (("write", "mcp-writer"), ("admin", "mcp-admin")):
        with pytest.raises(PermissionError):
            service.dispatch("find_terms", {"terms": ["Acme Corp"]}, role=role, actor=actor)
    phrases = tmp_path / "terms.txt"
    phrases.write_text("Acme Corp\n\n")
    out = tmp_path / "findings"
    args = cli.parser().parse_args(
        ["find-terms", "--terms-file", str(phrases), "--out-dir", str(out)])
    summary = cli._find_terms(service, args)
    assert summary["concepts_with_a_phrase"] == 2 and summary["of_them_still_stored"] == 2
    # Only counts are printed: no identity and no phrase.
    assert named not in json.dumps(summary) and "acme" not in json.dumps(summary).lower()
    assert (out / "concept-ids.txt").read_text().split() == sorted([named, claimed])
    assert len(list((out / "concepts").iterdir())) == 2
    saved = json.loads((out / "concepts" / "c_acme-corp-renewal.json").read_text())
    assert saved["_id"] == named and saved["name"] == "Acme Corp renewal"
    for path in (out / "report.json", out / "concept-ids.txt"):
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(out.stat().st_mode) == 0o700
