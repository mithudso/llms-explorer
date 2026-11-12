"""Transactional batch imports retain ownership, graph and lease invariants."""
from __future__ import annotations

import copy
from collections import Counter
from types import SimpleNamespace

import pytest
from pymongo import InsertOne, ReplaceOne
from test_store_core import Collection, Database

from research_library_service import bulk_family
from research_library_service.models import (
    MANAGED_BY,
    Conflict,
    LeaseConflict,
    OwnershipError,
    digest,
)
from research_library_service.store import LibraryStore

IDENTITY = "owner-library/test/v1"


class BatchCollection(Collection):
    """Adapt PyMongo's write models to the transactional mongomock fixture.

    Mongomock 4.3's native bulk builder lacks PyMongo 4.19's `sort` argument.
    These adapters preserve the real filters, write models and matched counts.
    The shared Database fixture still provides rollback and transaction locking.
    """

    def __getattr__(self, name):
        value = super().__getattr__(name)
        if not callable(value):
            return value

        def call(*args, **kwargs):
            self.database.operations.append((self.name, name))
            return value(*args, **kwargs)
        return call

    def bulk_write(self, requests, ordered=True, session=None):
        self.database.operations.append((self.name, "bulk_write"))
        if self.database.fail and self.database.fail(self.name, "bulk_write"):
            raise RuntimeError("injected batch write failure")
        matched, inserted = 0, 0
        for request in requests:
            if isinstance(request, InsertOne):
                self.database.raw[self.name].insert_one(copy.deepcopy(request._doc))
                inserted += 1
            elif isinstance(request, ReplaceOne):
                result = self.database.raw[self.name].replace_one(
                    request._filter, copy.deepcopy(request._doc), upsert=request._upsert)
                matched += result.matched_count
            else:
                raise AssertionError("Unexpected bulk operation in the backend adapter")
        return SimpleNamespace(matched_count=matched, inserted_count=inserted)


class BatchDatabase(Database):
    def __init__(self):
        super().__init__()
        self.operations = []

    def __getitem__(self, name):
        return BatchCollection(self, name)


@pytest.fixture
def library():
    clock = [1000.0]
    store = LibraryStore(BatchDatabase(), clock=lambda: clock[0])
    return store, clock


def imported(store, *names):
    return [store.import_concept({"name": name}, IDENTITY, digest(name)) for name in names]


def edge(child, parent):
    return {"concept_id": child["_id"], "target_id": parent["_id"], "relation": "parent"}


def pair(store, child, parent):
    ids = [child["_id"], parent["_id"]]
    grant = store.lease_acquire(ids, "setup")
    with store.importing(IDENTITY):
        store.relation_mutate(child["_id"], parent["_id"], "parent", "add",
            {cid: store.concept_get(cid)["revision"] for cid in ids}, grant["tokens"])
    store.lease_release(ids, grant["tokens"], "setup")


def snapshot(store, *docs):
    return {doc["_id"]: store.concept_get(doc["_id"]) for doc in docs}


def assert_no_live_leases(store):
    assert store.lease_list()["leases"] == []


def test_fifty_edges_use_bounded_queries_and_one_concept_bulk_write(library):
    store, _ = library
    parent, *children = imported(store, "Parent", *(f"Child {index}" for index in range(50)))
    old = snapshot(store, parent, *children)
    store.database.operations.clear()
    result = bulk_family.apply_family_batch(store, [edge(child, parent) for child in children], IDENTITY)
    counts = Counter(store.database.operations)
    assert result["updated"] == 50 and result["unchanged"] == 0
    assert len(result["affected_concepts"]) == 51
    assert counts[(store.concepts.name, "bulk_write")] == 1
    assert counts[(store.versions.name, "insert_many")] == 1
    assert counts[(store.leases.name, "bulk_write")] == 1
    assert counts[(store.leases.name, "update_many")] == 2
    assert counts[(store.concepts.name, "find_one")] == 0
    assert counts[(store.concepts.name, "find")] <= 4
    assert store.concept_get(parent["_id"])["children_ids"] == sorted(c["_id"] for c in children)
    for cid, before in old.items():
        current = store.concept_get(cid)
        assert current["revision"] == 2
        assert current["import_provenance"]["managed_revision"] == 2
        if cid != parent["_id"]:
            assert current["parent_id"] == parent["_id"]
        historical = store.concept_get(cid, 1)
        assert historical["parent_id"] == before["parent_id"]
        assert historical["children_ids"] == before["children_ids"]
    assert_no_live_leases(store)
    assert "tokens" not in result and "token_hash" not in repr(result)


def test_reparent_updates_all_three_endpoints_and_replays_exact_receipt(library):
    store, _ = library
    child, old, new = imported(store, "Child", "Old Parent", "New Parent")
    pair(store, child, old)
    original = snapshot(store, child, old, new)
    result = bulk_family.apply_family_batch(store, [edge(child, new)], IDENTITY)
    assert result["updated"] == 1
    assert store.concept_get(child["_id"])["parent_id"] == new["_id"]
    assert child["_id"] not in store.concept_get(old["_id"])["children_ids"]
    assert child["_id"] in store.concept_get(new["_id"])["children_ids"]
    assert {item["concept_id"] for item in result["affected_concepts"]} == set(original)
    version_count = store.versions.count_documents({})
    graph_revision = store.status()["graph_revision"]
    assert bulk_family.apply_family_batch(store, [edge(child, new)], IDENTITY) == result
    assert store.versions.count_documents({}) == version_count
    assert store.status()["graph_revision"] == graph_revision
    assert_no_live_leases(store)


def test_new_import_generation_gets_new_receipt_without_churning_unchanged_edges(library):
    store, _ = library
    child, parent = imported(store, "Child", "Parent")
    first = bulk_family.apply_family_batch(store, [edge(child, parent)], IDENTITY)
    store.import_concept({"name": "Child", "description": "new canonical metadata"},
                         IDENTITY, digest("new generation"))
    current = snapshot(store, child, parent)
    second = bulk_family.apply_family_batch(store, [edge(child, parent)], IDENTITY)
    assert second["request_id"] != first["request_id"]
    assert second["updated"] == 0 and second["unchanged"] == 1
    assert second["affected_concepts"] == []
    assert snapshot(store, child, parent) == current


def test_curated_child_is_preserved_but_parent_placement_flag_is_not_erased(library):
    store, _ = library
    child, parent = imported(store, "Child", "Parent")
    store.concepts.update_one({"_id": child["_id"]}, {"$set": {"family_override": True}})
    with pytest.raises(OwnershipError, match="curated"):
        bulk_family.apply_family_batch(store, [edge(child, parent)], IDENTITY)
    assert store.concept_get(child["_id"])["parent_id"] is None
    store.concepts.update_one({"_id": child["_id"]}, {"$unset": {"family_override": ""}})
    store.concepts.update_one({"_id": parent["_id"]}, {"$set": {"family_override": True}})
    result = bulk_family.apply_family_batch(store, [edge(child, parent)], IDENTITY)
    assert result["updated"] == 1
    assert store.concept_get(parent["_id"])["family_override"] is True


@pytest.mark.parametrize("condition", ["edited", "other-source", "archived", "missing"])
def test_import_never_replaces_an_unowned_or_missing_endpoint(library, condition):
    store, _ = library
    child, parent = imported(store, "Child", "Parent")
    if condition == "edited":
        grant = store.lease_acquire([parent["_id"]], "researcher")
        store.concept_update(parent["_id"], {"description": "private working edit"},
                             parent["revision"], grant["tokens"][parent["_id"]])
        store.lease_release([parent["_id"]], grant["tokens"], "researcher")
    elif condition == "other-source":
        store.concepts.update_one({"_id": parent["_id"]}, {"$set": {
            "import_provenance.source_identity": "other-owner"}})
    elif condition == "archived":
        store.concepts.update_one({"_id": parent["_id"]}, {"$set": {"deleted": True}})
    else:
        parent = {"_id": "c:missing-parent"}
    before = store.concept_get(child["_id"])
    with pytest.raises((OwnershipError, Conflict)):
        bulk_family.apply_family_batch(store, [edge(child, parent)], IDENTITY)
    assert store.concept_get(child["_id"]) == before
    assert_no_live_leases(store)


@pytest.mark.parametrize("condition", ["active-lease", "legacy", "stop", "paused"])
def test_all_or_nothing_hold_checks_preserve_other_workers(library, condition):
    store, _ = library
    child, sibling, parent = imported(store, "Child", "Sibling", "Parent")
    original = snapshot(store, child, sibling, parent)
    if condition == "active-lease":
        store.lease_acquire([sibling["_id"]], "other-worker")
    elif condition == "legacy":
        store.reservation_provider = lambda ids, owner, run_id: {sibling["_id"]: "paused legacy"}
    else:
        store.queue.insert_one({"_id": sibling["_id"], "managed_by": MANAGED_BY,
            "status": "queued" if condition == "stop" else "paused", "stop": condition == "stop"})
    with pytest.raises(LeaseConflict):
        bulk_family.apply_family_batch(store, [edge(child, parent), edge(sibling, parent)], IDENTITY)
    assert snapshot(store, child, sibling, parent) == original
    assert store.leases.find_one({"_id": child["_id"]}) is None
    if condition == "active-lease":
        assert store.leases.find_one({"_id": sibling["_id"]})["owner"] == "other-worker"


@pytest.mark.parametrize("condition", ["expiry", "nonce", "takeover", "late-stop"])
def test_changed_fences_or_late_holds_abort_and_cannot_release_an_heir(
        library, monkeypatch, condition):
    store, clock = library
    child, parent = imported(store, "Child", "Parent")
    before = snapshot(store, child, parent)
    acquire = bulk_family._acquire

    def interfere(*args):
        grant = acquire(*args)
        if condition in {"expiry", "takeover"}:
            clock[0] += 901
        if condition == "takeover":
            store.lease_acquire([child["_id"]], "replacement-worker")
        elif condition == "nonce":
            store.leases.update_one({"_id": child["_id"]}, {"$set": {"nonce": "changed-nonce"}})
        elif condition == "late-stop":
            store.queue.insert_one({"_id": child["_id"], "managed_by": MANAGED_BY,
                                    "status": "paused", "stop": True})
        return grant

    monkeypatch.setattr(bulk_family, "_acquire", interfere)
    with pytest.raises(LeaseConflict):
        bulk_family.apply_family_batch(store, [edge(child, parent)], IDENTITY)
    assert snapshot(store, child, parent) == before
    assert store.meta.find_one({"_id": "graph"}) is None
    if condition == "takeover":
        assert store.leases.find_one({"_id": child["_id"]})["owner"] == "replacement-worker"
    if condition in {"nonce", "late-stop"}:
        # An unrelated still-owned live lease is safely cleaned up.
        assert store.leases.find_one({"_id": parent["_id"]})["status"] == "released"


def test_new_canonical_revision_between_snapshot_and_acquisition_is_not_overwritten(
        library, monkeypatch):
    store, _ = library
    child, parent = imported(store, "Child", "Parent")
    acquire = bulk_family._acquire

    def interfere(*args):
        store.import_concept({"name": "Child", "description": "new canonical revision"},
                             IDENTITY, digest("later canonical revision"))
        return acquire(*args)

    monkeypatch.setattr(bulk_family, "_acquire", interfere)
    with pytest.raises(Conflict, match="changed"):
        bulk_family.apply_family_batch(store, [edge(child, parent)], IDENTITY)
    current = store.concept_get(child["_id"])
    assert current["description"] == "new canonical revision" and current["parent_id"] is None
    assert store.concept_get(parent["_id"])["children_ids"] == []
    assert_no_live_leases(store)


@pytest.mark.parametrize("outside_ancestor", [False, True])
def test_cycles_in_batch_or_through_existing_ancestors_roll_back(library, outside_ancestor):
    store, _ = library
    first, second, third = imported(store, "First", "Second", "Third")
    if outside_ancestor:
        pair(store, first, second)
        pair(store, second, third)
        edges = [edge(third, first)]
    else:
        edges = [edge(first, second), edge(second, first)]
    before = snapshot(store, first, second, third)
    versions = store.versions.count_documents({})
    with pytest.raises(Conflict, match="cycle"):
        bulk_family.apply_family_batch(store, edges, IDENTITY)
    assert snapshot(store, first, second, third) == before
    assert store.versions.count_documents({}) == versions
    assert_no_live_leases(store)


def test_version_insert_failure_rolls_back_all_graph_writes_and_receipts(library):
    store, _ = library
    child, sibling, parent = imported(store, "Child", "Sibling", "Parent")
    before = snapshot(store, child, sibling, parent)
    versions = store.versions.count_documents({})
    store.database.fail = lambda name, operation: name == store.versions.name and operation == "insert_many"
    with pytest.raises(RuntimeError, match="injected"):
        bulk_family.apply_family_batch(store, [edge(child, parent), edge(sibling, parent)], IDENTITY)
    store.database.fail = None
    assert snapshot(store, child, sibling, parent) == before
    assert store.versions.count_documents({}) == versions
    assert store.receipts.count_documents({"operation": "import_family_batch"}) == 0
    assert store.meta.find_one({"_id": "graph"}) is None
    assert_no_live_leases(store)


def test_foreign_lease_identity_and_immutable_version_are_never_overwritten(library):
    store, _ = library
    child, parent = imported(store, "Child", "Parent")
    foreign = {"_id": parent["_id"], "managed_by": "another-producer", "sentinel": "preserve"}
    store.leases.insert_one(foreign)
    with pytest.raises(OwnershipError):
        bulk_family.apply_family_batch(store, [edge(child, parent)], IDENTITY)
    assert store.leases.find_one({"_id": parent["_id"]}) == foreign
    store.leases.delete_one({"_id": parent["_id"]})
    version = {"_id": child["_id"] + "@2", "managed_by": "another-producer", "sentinel": "preserve"}
    store.versions.insert_one(version)
    before = snapshot(store, child, parent)
    with pytest.raises(Conflict):
        bulk_family.apply_family_batch(store, [edge(child, parent)], IDENTITY)
    assert snapshot(store, child, parent) == before
    assert store.versions.find_one({"_id": version["_id"]}) == version
    assert store.meta.find_one({"_id": "graph"}) is None
    assert_no_live_leases(store)


def test_replay_does_not_ignore_current_research_or_stop_hold(library):
    store, _ = library
    child, parent = imported(store, "Child", "Parent")
    bulk_family.apply_family_batch(store, [edge(child, parent)], IDENTITY)
    store.lease_acquire([child["_id"]], "new-researcher")
    with pytest.raises(LeaseConflict):
        bulk_family.apply_family_batch(store, [edge(child, parent)], IDENTITY)


@pytest.mark.parametrize("edges", [[], [{"concept_id": "c:x", "target_id": "c:y"}] * 51,
    [{"concept_id": "c:x", "target_id": "c:y", "relation": "related"}],
    [{"concept_id": "c:x", "target_id": "c:y", "command": "forbidden"}],
    [{"concept_id": "c:x", "target_id": "c:y"}, {"concept_id": "c:x", "target_id": "c:z"}]])
def test_invalid_or_oversized_batch_is_rejected_before_database_reads(library, edges):
    store, _ = library
    with pytest.raises(ValueError):
        bulk_family.apply_family_batch(store, edges, IDENTITY)
    assert store.database.operations == []
