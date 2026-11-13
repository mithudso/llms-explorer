from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path

import pytest

from research_library_service.importer import _hash, import_library, read_inventory
from research_library_service.models import source_id

REPO = Path(__file__).resolve().parents[3]


def write_json(path, value):
    import json
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False))
    return path


def test_inventory_keeps_aliases_frontier_score_precedence_and_exact_queue_names(tmp_path):
    tree = write_json(tmp_path / "tree.json", [
        {"concept": "Root", "slug": "root", "childConcepts": ["Never researched", "Alias child"],
         "researchedAt": "2026-11-01", "sourcesCount": 2, "cvs": 3.5},
        {"concept": "Child", "slug": "stable-child", "aliases": ["Alias child"],
         "parentConcept": "Root", "cvs": 4},
    ])
    scores = write_json(tmp_path / "scores.json", {
        "Child": {"cvs": 1}, "Never researched": {"cvs": 0, "decision": "SKIP"},
    })
    quote = chr(96)
    queue = tmp_path / "queue.md"
    queue.write_text(
        f"- [ ] Concept: {quote}Never researched{quote} | CVS: {quote}4.8{quote}\n"
        f"- [ ] Concept: {quote * 2} C++ {quote}API{quote} {quote * 2} "
        f"| Parent: {quote}Root{quote}\n"
        f"- [x] Concept: {quote}Finished queue only{quote}\n")
    result = read_inventory([tree], [queue], [scores])
    by_name = {row["name"]: row for row in result["concepts"]}
    assert len(by_name) == 4
    assert by_name["Child"]["slug"] == "stable-child"
    assert "Alias child" in by_name["Child"]["aliases"]
    assert by_name["Never researched"]["cvs"] == 0
    assert by_name["Child"]["cvs"] == 4
    assert by_name[f"C++ {quote}API{quote}"]["cvs"] is None
    assert "Finished queue only" not in by_name
    assert {"concept_id": "c:never-researched", "target_id": "c:root",
            "relation": "parent"} in result["relations"]
    assert by_name["Root"]["metadata"]["qualification"] == "unreviewed-import"
    assert all(row["state"] != "complete" for row in result["concepts"])


def test_explicit_parent_wins_child_lead_and_conflict_is_retained(tmp_path):
    tree = write_json(tmp_path / "tree.json", [
        {"concept": "A", "childConcepts": ["X"]},
        {"concept": "B"},
        {"concept": "X", "parentConcept": "B"},
    ])
    result = read_inventory([tree])
    assert result["relations"] == [{"concept_id": "c:x", "target_id": "c:b", "relation": "parent"}]
    assert result["warnings"][0]["kind"] == "conflicting-parent-leads"
    assert result["warnings"][0]["other_parents"] == ["c:a"]


def test_equal_priority_parent_preserves_authoritative_input_order(tmp_path):
    canonical = write_json(tmp_path / "canonical-tree.json", [
        {"concept": "B"}, {"concept": "X", "parentConcept": "B"},
    ])
    mirror = write_json(tmp_path / "mirror-tree.json", [
        {"concept": "A"}, {"concept": "X", "parentConcept": "A"},
    ])
    result = read_inventory([canonical, mirror])
    assert result["relations"] == [{"concept_id": "c:x", "target_id": "c:b", "relation": "parent"}]
    assert result["warnings"][0]["other_parents"] == ["c:a"]


def test_import_rejects_parent_cycle_before_writing(tmp_path):
    tree = write_json(tmp_path / "tree.json", [
        {"concept": "A", "parentConcept": "B"}, {"concept": "B", "parentConcept": "A"},
    ])
    with pytest.raises(ValueError, match="parent cycle"):
        read_inventory([tree])


def test_slug_collision_preserves_distinct_exact_identities(tmp_path):
    tree = write_json(tmp_path / "tree.json", [{"concept": "C++"}, {"concept": "C#"}])
    result = read_inventory([tree])
    assert len({row["slug"] for row in result["concepts"]}) == 2
    assert result["warnings"][0]["kind"] == "slug-collision"


@pytest.mark.parametrize("length", [150, 160, 161, 421])
def test_imported_slug_fits_actual_core_identity_contract_and_replays_stably(tmp_path, length):
    from test_store_core import Database

    from research_library_service.models import concept_id
    from research_library_service.store import LibraryStore

    original = "a" * length
    tree = write_json(tmp_path / "tree.json", [{"concept": original, "slug": original}])
    first = read_inventory([tree])["concepts"][0]
    again = read_inventory([tree])["concepts"][0]
    assert concept_id(first["slug"]) == "c:" + first["slug"]
    assert len(first["slug"]) <= 160 and again["slug"] == first["slug"]
    if length <= 160:
        assert first["slug"] == original
    else:
        assert first["metadata"]["original_slug"] == original
    store = LibraryStore(Database())
    assert import_library(store, tree_paths=[tree])["imported"] == 1
    assert import_library(store, tree_paths=[tree])["unchanged"] == 1
    assert store.versions.count_documents({}) == 1


def test_unicode_names_and_maximum_length_slug_collisions_keep_stable_distinct_ids(tmp_path):
    from research_library_service.models import concept_id

    tree = write_json(tmp_path / "tree.json", [
        {"concept": "研究の概念", "slug": "x" * 160},
        {"concept": "Another research concept", "slug": "x" * 160},
        {"concept": "é" * 180 + " field"},
    ])
    first, second = read_inventory([tree]), read_inventory([tree])
    ids = [concept_id(row["slug"]) for row in first["concepts"]]
    assert len(ids) == len(set(ids)) == 3
    assert ids == [concept_id(row["slug"]) for row in second["concepts"]]
    assert any(row["name"] == "研究の概念" for row in first["concepts"])


def test_public_projection_hash_checked_without_inventing_evidence(tmp_path):
    artifact = {"schema": "research-public-artifact/v1", "concept": "Public",
                "slug": "public", "canonical_artifact_sha256": "a" * 64,
                "claims": [{"text": "A public statement", "validation_status": "SUPPORTED"}]}
    artifact["projection_sha256"] = _hash(artifact)
    path = write_json(tmp_path / "public.json", artifact)
    result = read_inventory([], artifact_paths=[path])
    record = result["concepts"][0]
    assert record["claims"] == []
    assert record["state"] == "frontier"
    assert record["metadata"]["public_claim_projections"][0]["validation_status"] == "SUPPORTED"
    assert "missing-private-evidence-bindings" in record["incomplete_reasons"]
    artifact["claims"][0]["text"] = "Tampered"
    write_json(path, artifact)
    with pytest.raises(ValueError, match="projection hash"):
        read_inventory([], artifact_paths=[path])


def canonical_artifact(path, body=None):
    import hashlib
    import importlib.util
    helper_path = REPO / "scripts/research_claims.py"
    spec = importlib.util.spec_from_file_location("fixture_claim_identity", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    claim = {"text": "Fixture mechanism has an exact source.", "sources": ["https://docs.example/a"],
             "confidence": "high", "verified_as_of": None, "volatile": False,
             "evidence": [{"url": "https://docs.example/a", "source_id": source_id("https://docs.example/a"),
                           "snapshot_sha256": hashlib.sha256(body.encode()).hexdigest()
                           if body is not None else "a" * 64, "start": 0, "end": 10,
                           "quote": "Exact span", "extraction_status": "complete"}]}
    claim["canonical_claim_id"] = "clm:" + _hash(helper.claim_identity("original-slug", claim))
    claim.update(validation_status="LEGACY-UNBOUND", evidence_ids=[])
    artifact = {"schema": "research-artifact/v1", "run": "fixture", "topic": "Target",
                "status": "COMPLETED", "concept_slugs": {"Target": "target"},
                "documents": {"original-slug": {"concept": "Target", "claims": [claim]}}}
    artifact["artifact_sha256"] = _hash(artifact)
    return write_json(path, artifact), artifact


def test_canonical_artifact_uses_repository_verifier_and_preserves_original_claim_identity(tmp_path):
    path, artifact = canonical_artifact(tmp_path / "canonical.json")
    result = read_inventory([], artifact_paths=[path], repo=REPO)
    record = result["concepts"][0]
    assert record["artifact_proof"]["artifact_sha256"] == artifact["artifact_sha256"]
    assert record["artifact_proof"]["document_slug"] == "original-slug"
    assert record["metadata"]["canonical_claim_versions"][0]["identity_slug"] == "original-slug"
    assert record["metadata"]["canonical_claim_versions"][0]["canonical_claim_id"].startswith("clm:")
    assert record["metadata"]["canonical_claim_versions"][0]["validation_status"] == "LEGACY-UNBOUND"
    assert "validation_status" not in record["claims"][0]
    assert record["metadata"]["qualification"] == "unreviewed-import"
    with pytest.raises(ValueError, match="requires the repository"):
        read_inventory([], artifact_paths=[path])


class ImportStore:
    """Behavioral fake for importer orchestration, not a Mongo transaction substitute."""

    def __init__(self):
        self.docs = {}
        self.source_calls = []
        self.relations = []
        self.live_lease = set()
        self.context = None
        self.released = []
        self.queue_rows = {}

    def import_concept(self, document, source_identity, source_sha256, **kwargs):
        cid = "c:" + document["slug"]
        existing = self.docs.get(cid)
        if cid in self.live_lease or existing and existing.get("locally_edited"):
            return {"skipped": True, "reason": "local-edit-or-lease"}
        if existing and existing["import_provenance"]["source_sha256"] == source_sha256:
            return {"unchanged": True}
        self.docs[cid] = {
            **deepcopy(document), "_id": cid, "revision": 1 if not existing else existing["revision"] + 1,
            "parent_id": (existing or {}).get("parent_id"),
            "import_provenance": {"source_identity": source_identity,
                                  "source_sha256": source_sha256,
                                  "managed_revision": 1 if not existing else existing["revision"] + 1},
        }
        return {"changed": True}

    @contextmanager
    def importing(self, source_identity):
        self.context = source_identity
        try:
            yield
        finally:
            self.context = None

    def concept_get(self, concept_id):
        return deepcopy(self.docs[concept_id])

    def lease_acquire(self, ids, **kwargs):
        if set(ids) & self.live_lease:
            raise ValueError("held")
        return {"tokens": dict.fromkeys(ids, "fixture-lease-token")}

    def relation_mutate(self, child, parent, relation, action, revisions, tokens, **kwargs):
        assert self.context and set(revisions) == set(tokens)
        self.relations.append((child, parent))
        self.docs[child]["parent_id"] = parent
        for cid in (child, parent):
            self.docs[cid]["revision"] += 1
            self.docs[cid]["import_provenance"]["managed_revision"] = self.docs[cid]["revision"]
        return {"changed": True}

    def lease_release(self, ids, tokens, **kwargs):
        self.released.extend(ids)

    def source_put(self, url, **kwargs):
        self.source_calls.append((url, kwargs))
        return {"source_id": source_id(url)}

    def import_queue(self, cid, record, source_identity, source_sha256):
        if cid in self.queue_rows:
            return {"unchanged": True}
        self.queue_rows[cid] = deepcopy(record)
        return {"projection_only": True, "dispatched": False}


def test_import_is_repeatable_and_preserves_local_edits_and_live_leases(tmp_path):
    tree = write_json(tmp_path / "tree.json", [
        {"concept": "Root", "childConcepts": ["Child"]},
        {"concept": "Child", "parentConcept": "Root"},
    ])
    store = ImportStore()
    first = import_library(store, tree_paths=[tree])
    assert first["imported"] == 2 and first["relations_updated"] == 1 and not first["partial"]
    assert set(store.released) == {"c:root", "c:child"}
    second = import_library(store, tree_paths=[tree])
    assert second["unchanged"] == 2 and second["relations_updated"] == 0
    store.docs["c:root"]["locally_edited"] = True
    store.live_lease.add("c:child")
    third = import_library(store, tree_paths=[tree], replace_import=True)
    assert len(third["skipped"]) == 2 and third["partial"]
    assert len(store.relations) == 1


def test_dry_run_does_not_acquire_leases_or_write_any_rows(tmp_path):
    tree = write_json(tmp_path / "tree.json", [{"concept": "Root"}])
    store = ImportStore()
    result = import_library(store, tree_paths=[tree], dry_run=True)
    assert result["dry_run"] and result["counts"]["concepts"] == 1
    assert not store.docs and not store.released and not store.source_calls


def test_snapshot_import_checks_content_hash_and_never_moves_current_pointer(tmp_path):
    path, artifact = canonical_artifact(tmp_path / "canonical.json")
    library = tmp_path / "library"
    snapshots = library / "provenance/snapshots"
    snapshots.mkdir(parents=True)
    # Fixture requests a deliberately absent/hash-invalid source. It is reported
    # as incomplete accounting without exposing body content in the receipt.
    (snapshots / ("a" * 64 + ".txt")).write_text("Wrong snapshot body")
    store = ImportStore()
    result = import_library(store, tree_paths=[], artifact_paths=[path], repo=REPO,
                            source_library_path=library)
    assert result["snapshots"]["failed"][0]["reason"] == "snapshot-unavailable-or-invalid"
    assert "Wrong snapshot body" not in str(result)
    assert not store.source_calls


def test_adding_artifacts_does_not_change_corpus_owner_identity(tmp_path):
    tree = write_json(tmp_path / "tree.json", [{"concept": "Root"}])
    path, _ = canonical_artifact(tmp_path / "artifact.json")
    first = read_inventory([tree])
    second = read_inventory([tree], artifact_paths=[path], repo=REPO)
    assert first["source_identity"] == second["source_identity"]


def test_imported_queue_is_projected_without_dispatch_or_clearing_stop(tmp_path):
    tree = write_json(tmp_path / "tree.json", [{"concept": "Root"}])
    queue = tmp_path / "queue.md"
    tick = chr(96)
    queue.write_text(
        f"- [ ] Concept: {tick}Root{tick} | Status: {tick}paused{tick} "
        f"| STOP: {tick}true{tick}\n")
    store = ImportStore()
    receipt = import_library(store, tree_paths=[tree], queue_paths=[queue])
    assert receipt["queue_imported"] == 1
    assert store.queue_rows["c:root"]["status"] == "paused"
    assert store.queue_rows["c:root"]["stop"]
    assert not store.relations
    again = import_library(store, tree_paths=[tree], queue_paths=[queue])
    assert again["queue_unchanged"] == 1


def test_gate_attempt_snapshot_fallback_is_hash_bound_and_history_only(tmp_path):
    import hashlib
    body = "Exact span from a complete fixture source."
    run = tmp_path / "research/run"
    artifact_path, _ = canonical_artifact(run / "artifacts/canonical/artifact.json", body)
    attempt = run / "gate/attempts/accepted"
    evidence = attempt / "evidence"
    evidence.mkdir(parents=True)
    checksum = hashlib.sha256(body.encode()).hexdigest()
    (evidence / (checksum + ".txt")).write_bytes(body.encode())
    write_json(run / "manifest.json", {"gate": {"attempt": "gate/attempts/accepted"}})
    library = tmp_path / "library"
    library.mkdir()
    store = ImportStore()
    receipt = import_library(store, tree_paths=[], artifact_paths=[artifact_path],
                            repo=REPO, source_library_path=library)
    assert receipt["snapshots"]["imported"] == 1 and not receipt["snapshots"]["failed"]
    assert store.source_calls[0][1]["text"] == body
    assert store.source_calls[0][1]["make_current"] is False


def test_malformed_alias_list_does_not_merge_unrelated_single_characters(tmp_path):
    tree = write_json(tmp_path / "tree.json", [{"concept": "Root", "aliases": "bad-scalar"}])
    with pytest.raises(ValueError, match="nonempty string lists"):
        read_inventory([tree])


def test_core_import_initial_family_precedes_new_queue_hold_and_repeat_has_no_revisions(tmp_path):
    from test_store_core import Database

    from research_library_service.store import LibraryStore

    tree = write_json(tmp_path / "tree.json", [
        {"concept": "Parent", "childConcepts": ["Child"]},
        {"concept": "Child", "parentConcept": "Parent"},
    ])
    queue = tmp_path / "queue.md"
    tick = chr(96)
    queue.write_text(f"- [ ] Concept: {tick}Child{tick} | Status: {tick}paused{tick} "
                     f"| STOP: {tick}true{tick}\n")
    store = LibraryStore(Database())
    first = import_library(store, tree_paths=[tree], queue_paths=[queue])
    assert not first["partial"] and first["relations_updated"] == 1
    assert store.concept_get("c:child")["parent_id"] == "c:parent"
    assert store.concept_get("c:parent")["children_ids"] == ["c:child"]
    assert store.queue.find_one({"_id": "c:child"})["stop"] is True
    versions = store.versions.count_documents({})
    again = import_library(store, tree_paths=[tree], queue_paths=[queue])
    assert not again["partial"] and again["relations_updated"] == 0
    assert store.versions.count_documents({}) == versions


def test_core_source_history_import_preserves_existing_current_pointer(tmp_path):
    from test_store_core import Database

    from research_library_service.store import LibraryStore

    historical = "Exact span from the historical source."
    artifact, _ = canonical_artifact(tmp_path / "artifact.json", historical)
    import hashlib
    library = tmp_path / "library"
    snapshots = library / "provenance/snapshots"
    snapshots.mkdir(parents=True)
    sha = hashlib.sha256(historical.encode()).hexdigest()
    (snapshots / (sha + ".txt")).write_bytes(historical.encode())
    store = LibraryStore(Database())
    current = store.source_put("https://docs.example/a", "New current version.")
    receipt = import_library(store, tree_paths=[], artifact_paths=[artifact], repo=REPO,
                            source_library_path=library)
    assert receipt["snapshots"]["imported"] == 1 and not receipt["snapshots"]["failed"]
    assert store.sources.find_one({"_id": current["_id"]})["snapshot_sha256"] == current[
        "snapshot_sha256"]
    assert store.source_get(current["_id"], sha)["text"] == historical
    assert store.concept_get("c:target")["qualification"] == "unreviewed"


def test_owner_bulk_runner_isolates_invalid_record_without_losing_valid_neighbors():
    import importlib.util

    from test_store_core import Database

    from research_library_service.models import MANAGED_BY
    from research_library_service.store import LibraryStore

    path = Path(__file__).resolve().parents[1] / "scripts/import_owner_library.py"
    spec = importlib.util.spec_from_file_location("owner_bulk_scenario", path)
    owner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner)
    store = LibraryStore(Database())
    store.concepts.create_index([("managed_by", 1), ("alias_keys", 1)], unique=True,
        name="research_alias_identity_v1", partialFilterExpression={"managed_by": MANAGED_BY})
    inventory = {"source_identity": "scenario", "concepts": [
        {"name": "Valid first", "slug": "valid-first", "claims": [], "source_refs": []},
        {"name": "b" * 501, "slug": "invalid-name", "claims": [], "source_refs": []},
        {"name": "Valid last", "slug": "valid-last", "claims": [], "source_refs": []},
    ]}
    result = owner.TimedStore(store, {}).prepare_new_batches(inventory)
    assert result["bulk_created"] == 2 and result["fallback_records"] == 1
    assert store.concepts.count_documents({}) == store.versions.count_documents({}) == 2
    assert store.concepts.find_one({"_id": "c:invalid-name"}) is None


@pytest.mark.parametrize("unavailable", ["not-imported", "missing", "deleted"])
def test_owner_family_reserves_only_eligible_existing_endpoints(unavailable):
    import importlib.util

    from test_store_core import Database

    from research_library_service.models import MANAGED_BY
    from research_library_service.store import LibraryStore

    path = Path(__file__).resolve().parents[1] / "scripts/import_owner_library.py"
    spec = importlib.util.spec_from_file_location("owner_family_scenario", path)
    owner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner)
    store = LibraryStore(Database())
    for row in [
        {"_id": "c:child", "parent_id": "c:parent", "children_ids": []},
        {"_id": "c:parent", "parent_id": None, "children_ids": ["c:child"]},
    ]:
        store.concepts.insert_one({**row, "managed_by": MANAGED_BY})
    if unavailable == "deleted":
        store.concepts.insert_one({"_id": "c:unavailable", "managed_by": MANAGED_BY,
                                   "deleted": True})
    calls = []
    def reservations(ids, actor, run_id):
        calls.append(ids)
        assert ids == ["c:child", "c:parent"]
        return {}
    store.reservation_provider = reservations
    timed = owner.TimedStore(store, {})
    apply, _ = owner.family_applier(timed, {"concepts": []}, lambda _: None)
    eligible = {"c:child", "c:parent"}
    if unavailable != "not-imported":
        eligible.add("c:unavailable")
    result = apply(timed, [
        {"concept_id": "c:child", "target_id": "c:parent"},
        {"concept_id": "c:unavailable", "target_id": "c:parent"},
    ], eligible, "scenario")
    assert calls == [["c:child", "c:parent"]]
    assert result["unchanged"] == 1 and result["updated"] == 0
    assert result["skipped"][0]["reason"] == (
        "endpoint-not-import-managed" if unavailable == "not-imported" else "endpoint-unavailable")
    assert not store.versions.count_documents({})


def test_owner_family_fails_closed_if_reservation_inventory_changes():
    import importlib.util

    from test_store_core import Database

    from research_library_service.models import MANAGED_BY
    from research_library_service.store import LibraryStore
    path = Path(__file__).resolve().parents[1] / "scripts/import_owner_library.py"
    spec = importlib.util.spec_from_file_location("owner_family_changed", path)
    owner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner)
    store = LibraryStore(Database())
    for cid in ["c:child", "c:parent"]:
        store.concepts.insert_one({"_id": cid, "managed_by": MANAGED_BY})
    def unavailable(*args):
        raise KeyError("A reserved research concept is unavailable")
    store.reservation_provider = unavailable
    timed = owner.TimedStore(store, {})
    apply, _ = owner.family_applier(timed, {"concepts": []}, lambda _: None)
    result = apply(timed, [{"concept_id": "c:child", "target_id": "c:parent"}],
                   {"c:child", "c:parent"}, "scenario")
    assert result["updated"] == 0
    assert result["skipped"][0]["reason"] == "reservation-check-unavailable"
    assert result["skipped"][0]["error_type"] == "KeyError"
    assert not store.versions.count_documents({})
