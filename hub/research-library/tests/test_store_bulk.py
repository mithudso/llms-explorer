import copy
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import pytest
from pymongo.errors import BulkWriteError
from test_store_core import Collection, Database

import research_library_service.store as store_module
from research_library_service.models import MANAGED_BY, digest
from research_library_service.service import Service
from research_library_service.store import Conflict, LeaseConflict, LibraryStore


@pytest.fixture
def store():
    value = LibraryStore(Database(), clock=lambda: 1000)
    value.concepts.create_index([("managed_by", 1), ("alias_keys", 1)], unique=True,
        name="research_alias_identity_v1", partialFilterExpression={"managed_by": MANAGED_BY})
    return value


def record(name="One", **extra):
    document = {"name": name, **extra}
    return {"document": document, "source_sha256": digest(document)}


def queue_record(cid="c:one", **extra):
    document = {"status": "pending", **extra}
    return {"concept_id": cid, "record": document, "source_sha256": digest(document)}


def test_new_batch_matches_single_import_including_scalar_scores_and_immutable_versions(store):
    records = [record("One", description="Private description", cvs=0, cvs_axes=None,
        aliases=["First"], terms=["terminology"], metadata={"coverage": "frontier"}),
        record("Two", cvs=3.5, cvs_axes=None, state="incomplete", summary="Provisional summary"),
        record("Three", cvs=0, cvs_axes={"Rel": 5, "Use": 5, "Nov": 0, "Int": 5, "Via": 5})]
    single = LibraryStore(Database(), clock=lambda: 1000)
    for entry in records:
        single.import_concept(entry["document"], "corpus", entry["source_sha256"])
    result = store.import_new_concepts(records, "corpus")
    assert result["inserted"] == 3 and result["skipped_ids"] == []
    assert result["revisions"] == {"c:one": 1, "c:two": 1, "c:three": 1}
    assert "Private description" not in repr(result)
    assert not result["dispatch_authorized"] and result["qualification"] == "unreviewed"
    assert list(store.concepts.find().sort("_id")) == list(single.concepts.find().sort("_id"))
    assert list(store.versions.find().sort("_id")) == list(single.versions.find().sort("_id"))
    assert store.concept_get("c:one")["cvs"] == 0
    assert store.concept_get("c:two")["cvs"] == 3.5
    assert store.concept_get("c:three")["cvs_decision"] == "SKIP"
    assert store.receipts.count_documents({}) == 1


def test_batch_replay_returns_current_revisions_and_never_reverts_family_or_local_edits(store):
    records = [record("One"), record("Two")]
    first = store.import_new_concepts(records, "corpus")
    held = store.lease_acquire(first["inserted_ids"], "family")
    with store.importing("corpus"):
        store.relation_mutate("c:two", "c:one", "parent", "add", first["revisions"], held["tokens"])
    store.lease_release(first["inserted_ids"], held["tokens"], "family")
    replay = store.import_new_concepts(list(reversed(records)), "corpus")
    assert replay["inserted"] == 0 and replay["unchanged"]
    assert set(replay["skipped_ids"]) == {"c:one", "c:two"}
    assert replay["revisions"] == {"c:one": 2, "c:two": 2}
    assert store.concept_get("c:two")["parent_id"] == "c:one"
    own = store.lease_acquire(["c:one"], "editor")
    store.concept_update("c:one", {"description": "Local edit"}, 2, own["tokens"]["c:one"])
    store.lease_release(["c:one"], own["tokens"], "editor")
    before = list(store.concepts.find().sort("_id"))
    with pytest.raises(Conflict, match="locally edited"):
        store.import_new_concepts(records, "corpus")
    assert list(store.concepts.find().sort("_id")) == before


@pytest.mark.parametrize("failure_collection,failure_operation", [
    ("versions", "insert_many"), ("receipts", "insert_one")])
def test_batch_rolls_back_all_concepts_versions_and_receipt_on_late_failure(
        store, failure_collection, failure_operation):
    store.database.fail = lambda name, method: name == getattr(store, failure_collection).name and method == failure_operation
    with pytest.raises(RuntimeError, match="injected write failure"):
        store.import_new_concepts([record("One"), record("Two")], "corpus")
    assert all(collection.count_documents({}) == 0 for collection in (store.concepts, store.versions, store.receipts))


@pytest.mark.parametrize("records", [
    [record("One"), record("One", slug="different")],
    [record("One", slug="same"), record("Two", slug="same")],
    [record("One", aliases=["Shared"]), record("Two", aliases=[" SHARED "])],
])
def test_duplicate_batch_names_aliases_and_ids_fail_without_writes(store, records):
    with pytest.raises(Conflict):
        store.import_new_concepts(records, "corpus")
    assert store.concepts.count_documents({}) == store.versions.count_documents({}) == 0


@pytest.mark.parametrize("collision", ["id", "alias", "foreign", "version"])
def test_new_batch_never_overwrites_existing_identity_alias_foreign_or_orphan_history(store, collision):
    if collision == "id":
        store.concept_create("One")
    elif collision == "alias":
        store.concept_create("Existing", aliases=["One"])
    elif collision == "foreign":
        store.concepts.insert_one({"_id": "foreign", "managed_by": "another-producer", "body": "untouched"})
    else:
        store.versions.insert_one({"_id": "c:one@1", "managed_by": "another-producer"})
    before = [list(collection.find()) for collection in (store.concepts, store.versions, store.receipts)]
    with pytest.raises(Conflict):
        store.import_new_concepts([record("One"), record("Two")], "corpus")
    assert before == [list(collection.find()) for collection in (store.concepts, store.versions, store.receipts)]


@pytest.mark.parametrize("status,expires", [("held", 2000), ("held", 1), ("released", 1)])
def test_orphan_mongo_leases_block_new_batch_and_single_fallback(store, status, expires):
    store.leases.insert_one({"_id": "c:one", "managed_by": MANAGED_BY,
                            "status": status, "expires_at": expires})
    entry = record("One")
    with pytest.raises(LeaseConflict):
        store.import_new_concepts([entry], "corpus")
    with pytest.raises(LeaseConflict):
        store.import_concept(entry["document"], "corpus", entry["source_sha256"])
    assert store.concepts.count_documents({}) == 0
    assert store.leases.count_documents({}) == 1


def test_read_projection_does_not_acquire_research_ownership_or_exempt_future_holds(store):
    calls = []

    def held(ids, owner, run_id):
        calls.append((ids, owner, run_id))
        return {cid: {"owner": "legacy-owner", "paused": True} for cid in ids}

    store.reservation_provider = held
    store.import_new_concepts([record("One")], "corpus")
    assert calls == [] and store.leases.count_documents({}) == 0
    with pytest.raises(LeaseConflict):
        store.lease_acquire(["c:one"], "researcher")
    assert calls


def test_race_between_preflight_and_transaction_is_rechecked_atomically(store, monkeypatch):
    transaction = store._tx

    def intervene(callback):
        store.concepts.insert_one({"_id": "racer", "managed_by": MANAGED_BY, "alias_keys": ["one"]})
        return transaction(callback)

    monkeypatch.setattr(store, "_tx", intervene)
    with pytest.raises(Conflict):
        store.import_new_concepts([record("One"), record("Two")], "corpus")
    assert store.concepts.count_documents({}) == 1
    assert store.versions.count_documents({}) == store.receipts.count_documents({}) == 0


@pytest.mark.parametrize("same_batch", [False, True])
def test_concurrent_batch_identity_races_have_one_commit_and_safe_replay(store, monkeypatch, same_batch):
    transaction, rendezvous = store._tx, threading.Barrier(2)

    def overlapping(callback):
        rendezvous.wait(timeout=3)
        return transaction(callback)

    monkeypatch.setattr(store, "_tx", overlapping)
    entries = [[record("One", slug="one", aliases=["Shared"])]] * 2 if same_batch else [
        [record("One", slug="one", aliases=["Shared"])], [record("Two", slug="two", aliases=["Shared"])]]

    def apply(records):
        try:
            return store.import_new_concepts(records, "corpus")
        except Conflict:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [future.result(timeout=5) for future in [pool.submit(apply, rows) for rows in entries]]
    assert sum(result["inserted"] for result in results if result is not None) == 1
    assert sum(result is None for result in results) == (0 if same_batch else 1)
    assert store.concepts.count_documents({}) == store.versions.count_documents({}) == 1
    assert store.receipts.count_documents({}) == 1


def test_bulk_driver_duplicate_error_is_sanitized_and_rolled_back(store, monkeypatch):
    original = store.concepts.insert_many

    def duplicate(*args, **kwargs):
        original(*args, **kwargs)
        raise BulkWriteError({"writeErrors": [{"code": 11000, "errmsg": "private error"}]})

    monkeypatch.setattr(store.concepts, "insert_many", duplicate)
    with pytest.raises(Conflict) as failure:
        store.import_new_concepts([record("One"), record("Two")], "corpus")
    assert "private" not in str(failure.value)
    assert store.concepts.count_documents({}) == store.versions.count_documents({}) == 0


def test_bulk_driver_unlabelled_write_conflict_retries_the_entire_batch(store, monkeypatch):
    original, attempts, sleeps = store.concepts.insert_many, [], []

    def conflict(*args, **kwargs):
        assert store.concepts.count_documents({}) == 0
        result = original(*args, **kwargs)
        attempts.append(True)
        if len(attempts) < 2:
            raise BulkWriteError({"writeErrors": [{"code": 112, "errmsg": "WriteConflict"}]})
        return result

    monkeypatch.setattr(store.concepts, "insert_many", conflict)
    monkeypatch.setattr(store_module.time, "sleep", sleeps.append)
    result = store.import_new_concepts([record("One"), record("Two")], "corpus")
    assert result["inserted"] == 2 and len(sleeps) == 1
    assert store.concepts.count_documents({}) == store.versions.count_documents({}) == 2
    assert store.receipts.count_documents({}) == 1


@pytest.mark.parametrize("document", [
    {"name": "One", "claims": [{"text": "Claim"}]},
    {"name": "One", "source_refs": [{"source_id": "source"}]},
    {"name": "One", "artifact_proof": None}, {"name": "One", "parent_id": None},
    {"name": "One", "related_ids": []}, {"name": "One", "state": "complete"},
])
def test_bulk_excludes_claim_evidence_family_and_publication_paths(store, document):
    with pytest.raises(ValueError):
        store.import_new_concepts([{"document": document, "source_sha256": digest(document)}], "corpus")
    assert store.concepts.count_documents({}) == 0


def test_bulk_bounds_exact_hash_and_provisioned_alias_index_are_required(store, monkeypatch):
    with pytest.raises(ValueError, match="1..100"):
        store.import_new_concepts([record(str(i)) for i in range(101)], "corpus")
    with pytest.raises(ValueError, match="exact concept"):
        store.import_new_concepts([{**record("One"), "source_sha256": "0" * 64}], "corpus")
    monkeypatch.setattr(store_module, "MAX_IMPORT_BATCH_BYTES", 10)
    with pytest.raises(ValueError, match="byte limit"):
        store.import_new_concepts([record("One")], "corpus")
    monkeypatch.undo()
    store.concepts.drop_index("research_alias_identity_v1")
    with pytest.raises(RuntimeError, match="unique research alias index"):
        store.import_new_concepts([record("One")], "corpus")
    assert store.concepts.count_documents({}) == 0


def test_hundred_record_batch_uses_constant_database_calls_and_bulk_writes(store, monkeypatch):
    counts = Counter()
    original = Collection.__getattr__

    def observed(collection, name):
        method = original(collection, name)
        if not callable(method):
            return method
        def call(*args, **kwargs):
            counts[(collection.name, name)] += 1
            return method(*args, **kwargs)
        return call

    monkeypatch.setattr(Collection, "__getattr__", observed)
    result = store.import_new_concepts([record(f"Concept {i}") for i in range(100)], "corpus")
    assert result["inserted"] == 100
    assert counts[(store.concepts.name, "find_one")] == 2
    assert counts[(store.leases.name, "find_one")] == 2
    assert counts[(store.concepts.name, "insert_many")] == counts[(store.versions.name, "insert_many")] == 1
    assert counts[(store.concepts.name, "insert_one")] == counts[(store.versions.name, "insert_one")] == 0


def test_new_queue_batch_matches_single_and_has_no_concept_or_lease_mutations(store):
    store.import_new_concepts([record("One"), record("Two")], "corpus")
    records = [queue_record("c:one", stop=True, cvs=0, reason="Retained STOP"),
               queue_record("c:two", status="done")]
    single = LibraryStore(Database(), clock=lambda: 1000)
    for row in store.concepts.find():
        single.concepts.insert_one(copy.deepcopy(row))
    for entry in records:
        single.import_queue(entry["concept_id"], entry["record"], "corpus", entry["source_sha256"])
    before = [list(collection.find()) for collection in (store.concepts, store.versions, store.leases)]
    result = store.import_new_queues(records, "corpus")
    assert result["inserted"] == 2 and result["revisions"] == {"c:one": 1, "c:two": 1}
    assert result["projection_only"] and not result["dispatched"] and not result["affected_concepts"]
    assert list(store.queue.find().sort("_id")) == list(single.queue.find().sort("_id"))
    assert store.queue.find_one({"_id": "c:one"})["stop"]
    assert store.queue.find_one({"_id": "c:one"})["status"] == "paused"
    assert before == [list(collection.find()) for collection in (store.concepts, store.versions, store.leases)]
    replay = store.import_new_queues(records, "corpus")
    assert replay["inserted"] == 0 and replay["unchanged"]
    assert set(replay["skipped_ids"]) == {"c:one", "c:two"}


@pytest.mark.parametrize("collision", ["existing-stop", "foreign", "missing", "foreign-concept"])
def test_new_queue_batch_never_overwrites_holds_foreign_rows_or_missing_concepts(store, collision):
    store.import_new_concepts([record("One"), record("Two")], "corpus")
    if collision == "existing-stop":
        store.queue.insert_one({"_id": "c:one", "managed_by": MANAGED_BY, "stop": True, "status": "paused"})
    elif collision == "foreign":
        store.queue.insert_one({"_id": "foreign", "managed_by": "other"})
    elif collision == "missing":
        store.concepts.delete_one({"_id": "c:two"})
    else:
        store.concepts.update_one({"_id": "c:two"}, {"$set": {"managed_by": "other"}})
    before = list(store.queue.find())
    with pytest.raises(Conflict):
        store.import_new_queues([queue_record("c:one"), queue_record("c:two")], "corpus")
    assert before == list(store.queue.find())


def test_queue_receipt_failure_rolls_back_and_replay_preserves_manual_stop(store):
    store.import_new_concepts([record("One"), record("Two")], "corpus")
    records = [queue_record("c:one"), queue_record("c:two")]
    store.database.fail = lambda name, method: name == store.receipts.name and method == "insert_one"
    with pytest.raises(RuntimeError):
        store.import_new_queues(records, "corpus")
    assert store.queue.count_documents({}) == 0
    store.database.fail = None
    store.import_new_queues(records, "corpus")
    store.queue.update_one({"_id": "c:one"}, {"$set": {"stop": True, "status": "paused"}, "$inc": {"revision": 1}})
    before = list(store.queue.find().sort("_id"))
    with pytest.raises(Conflict, match="locally edited"):
        store.import_new_queues(records, "corpus")
    assert before == list(store.queue.find().sort("_id"))


@pytest.mark.parametrize("operation", ["import_new_concepts", "import_new_queues"])
def test_bulk_import_operations_are_not_remote_dispatch_capabilities(store, operation):
    service = Service(store=store, config={}, bridge={})
    with pytest.raises(ValueError, match="Unsupported research operation"):
        service.dispatch(operation, {"records": [], "source_identity": "corpus"}, role="admin")
