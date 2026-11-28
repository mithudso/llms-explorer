"""A row purge erases the runs, sources and receipts that hold a private phrase."""
from __future__ import annotations

import json

import pytest
from test_store_core import Database, lease, make

from research_library_service import cli
from research_library_service.models import MANAGED_BY
from research_library_service.runs import ResearchRunStore
from research_library_service.service import Service
from research_library_service.store import LibraryStore

PHRASES = ["Acme Corp"]
SHARED_BODY = "A body that two runs both keep."


@pytest.fixture
def runs():
    now = [1000.0]
    result = ResearchRunStore(LibraryStore(Database(), clock=lambda: now[0]))
    result.test_clock = now
    return result


def run(runs, subject):
    created = runs.run_create("dr", subject, "Research the exact requested scope", "coordinator")
    rid = created["run"]["_id"]
    item = runs.run_item_put(rid, "first", "coverage", {"label": "first"},
                             created["run"]["revision"], created["lease_token"], "coordinator")
    runs.artifact_put(rid, "report.md", "compiled", SHARED_BODY, item["run"]["revision"],
                      created["lease_token"], "coordinator")
    return rid, created["lease_token"]


def library(runs):
    """A run named after a customer, a clean run that mentions it in one item, and a clean run."""
    named, _ = run(runs, "Acme Corp rollout")
    mentioned, token = run(runs, "Sharding")
    runs.run_item_put(mentioned, "second", "question", {"label": "What did acme-corp ask?"},
                      runs.run_get(mentioned)["revision"], token, "coordinator")
    clean, _ = run(runs, "Replication")
    # A search unit is derived from a file and is stored under its run.
    runs.store.database[runs.store.prefix + "artifact_units"].insert_one({
        "_id": "unit:one", "managed_by": MANAGED_BY, "run_id": named,
        "search_text": "nothing private here"})
    runs.test_clock[0] += 1000
    return named, mentioned, clean


def stored(runs, rid):
    names = ("run_versions", "run_items", "item_versions", "artifacts", "artifact_heads",
             "artifact_units")
    database, prefix = runs.store.database, runs.store.prefix
    return sum(database[prefix + name].count_documents({"run_id": rid}) for name in names)


def test_a_dry_run_reports_counts_and_changes_nothing(runs):
    named, mentioned, _ = library(runs)
    before = (stored(runs, named), stored(runs, mentioned), runs.store.receipts.count_documents({}))
    report = runs.store.purge_rows(PHRASES)
    assert report["applied"] is False and report["runs"] == 2 and report["sources"] == 0
    assert report["removed"]["runs"] == 2 and report["removed"]["run_versions"] >= 6
    assert report["removed"]["receipts"] >= 3
    assert [shape["mode"] for shape in report["run_shapes"]] == ["dr", "dr"]
    assert report["run_shapes"][0] == {"mode": "dr", "state": "planned", "revisions": 4,
                                       "items": 2, "files": 1}
    assert report["not_read"] == ["snapshot_chunks", "artifact_chunks"]
    # Neither a phrase nor a run identity is part of the answer.
    assert "acme" not in json.dumps(report).lower() and named not in json.dumps(report)
    assert before == (stored(runs, named), stored(runs, mentioned),
                      runs.store.receipts.count_documents({}))


def test_a_run_that_holds_a_phrase_anywhere_is_erased_whole(runs):
    named, mentioned, clean = library(runs)
    kept = stored(runs, clean)
    report = runs.store.purge_rows(PHRASES, apply=True)
    assert report["applied"] is True and report["still_holding"] == {}
    for rid in (named, mentioned):
        with pytest.raises(KeyError):
            runs.run_get(rid)
        assert stored(runs, rid) == 0
        assert runs.run_leases.count_documents({"_id": rid}) == 0
    # The clean run keeps everything, and so does the body it shares with the erased runs.
    assert runs.run_get(clean)["subject"] == "Replication" and stored(runs, clean) == kept
    artifact = runs.artifacts.find_one({"run_id": clean})
    assert runs.artifact_get(artifact["_id"])["text"] == SHARED_BODY
    assert runs.artifact_chunks.count_documents({}) == 1
    # No receipt and no record of the purge repeats the phrase.
    for collection in (runs.store.receipts, runs.store.meta):
        assert "acme" not in json.dumps(list(collection.find({})), default=str).lower()
    record = runs.store.meta.find_one({"_id": report["audit_record"]})
    assert record["kind"] == "purge-rows" and record["runs"] == 2
    # Nothing is left for a second run.
    assert runs.store.purge_rows(PHRASES, apply=True)["removed"] == {}


def test_a_body_no_other_file_lists_goes_with_its_run(runs):
    named, _ = run(runs, "Acme Corp rollout")
    runs.test_clock[0] += 1000
    runs.store.purge_rows(PHRASES, apply=True)
    assert runs.artifact_chunks.count_documents({}) == 0 and stored(runs, named) == 0


def test_a_run_with_a_live_lease_waits_unless_told(runs):
    named, _ = run(runs, "Acme Corp rollout")
    waiting = runs.store.purge_rows(PHRASES, apply=True)
    assert waiting["runs"] == 0 and waiting["skipped"]["runs_with_a_live_lease"] == 1
    assert runs.run_get(named)["subject"] == "Acme Corp rollout"
    assert waiting["still_holding"]["runs"] == 1
    erased = runs.store.purge_rows(PHRASES, apply=True, include_held=True)
    assert erased["runs"] == 1 and erased["still_holding"] == {}


def test_a_source_goes_unless_a_stored_concept_still_cites_it(runs):
    store = runs.store
    loose = store.source_put("https://example.org/loose", "Notes.",
                             metadata={"title": "Acme Corp case study"})
    body = "Acme corp signed in March."
    cited = store.source_put("https://example.org/cited", body)
    concept, = make(store, "Contracts")
    token = lease(store, [concept])["tokens"][concept["_id"]]
    store.claim_mutate(concept["_id"], "add", {
        "text": "A contract was signed in March.", "sources": [cited["url"]],
        "confidence": "high", "verified_as_of": "2026-11-12", "volatile": False,
        "evidence": [{"url": cited["url"], "source_id": cited["_id"],
                      "snapshot_sha256": cited["snapshot_sha256"], "start": 0, "end": len(body),
                      "quote": body, "extraction_status": "complete"}]},
        expected_revision=1, lease_token=token)

    # A body is read only when asked, so the cited source is not seen yet.
    first = store.purge_rows(PHRASES, apply=True)
    assert first["sources"] == 1 and first["removed"]["sources"] == 1
    assert store.sources.count_documents({"_id": loose["_id"]}) == 0
    assert store.source_versions.count_documents({"source_id": loose["_id"]}) == 0
    assert store.snapshots.count_documents({"source_id": loose["_id"]}) == 0
    assert store.snapshot_chunks.count_documents({}) == 1
    assert first["concept_rows_with_a_phrase"]["concepts"] == 1

    second = store.purge_rows(PHRASES, apply=True, include_bodies=True)
    assert second["not_read"] == [] and second["sources"] == 0
    assert second["skipped"] == {"runs_with_a_live_lease": 0, "sources_still_cited": 1,
                                 "concepts_citing_them": 1}
    assert store.source_get(cited["_id"])["text"] == body
    # Once the citing concept is purged, the source goes too.
    store.purge_concepts([concept["_id"]], apply=True, include_held=True)
    third = store.purge_rows(PHRASES, apply=True, include_bodies=True)
    assert third["sources"] == 1 and third["still_holding"] == {}
    assert store.snapshot_chunks.count_documents({}) == 0


def test_the_purge_is_owner_local_and_the_command_prints_counts(runs, tmp_path, capsys):
    named, _, _ = library(runs)
    service = Service(store=runs.store)
    for role, actor in (("write", "mcp-writer"), ("admin", "mcp-admin")):
        with pytest.raises(PermissionError):
            service.dispatch("purge_rows", {"terms": PHRASES, "apply": True},
                             role=role, actor=actor)
    assert runs.run_get(named)["subject"] == "Acme Corp rollout"
    phrases = tmp_path / "terms.txt"
    phrases.write_text("Acme Corp\n\n")
    assert cli.main(["purge-rows", "--terms-file", str(phrases)], service=service) == 0
    printed = capsys.readouterr().out
    assert json.loads(printed)["applied"] is False and "acme" not in printed.lower()
    assert cli.main(["purge-rows", "--terms-file", str(phrases), "--apply"], service=service) == 0
    assert json.loads(capsys.readouterr().out)["still_holding"] == {}
    with pytest.raises(ValueError):
        runs.store.purge_rows([], apply=True)
