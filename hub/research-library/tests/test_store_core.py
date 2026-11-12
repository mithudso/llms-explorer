import copy
import importlib.util
import json
import threading
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import mongomock
import pytest
from pymongo.errors import OperationFailure

import research_library_service.store as store_module
from research_library_service.models import MANAGED_BY, digest, normalize_url, source_id
from research_library_service.queries import LibraryQueries
from research_library_service.store import Conflict, LeaseConflict, LibraryStore


class Collection:
    def __init__(self, database, name):
        self.database, self.name = database, name

    def __getattr__(self, name):
        method = getattr(self.database.raw[self.name], name)
        if not callable(method):
            return method

        def call(*args, **kwargs):
            kwargs.pop("session", None)
            if self.database.fail and self.database.fail(self.name, name):
                raise RuntimeError("injected write failure")
            return method(*args, **kwargs)
        return call


class Database:
    def __init__(self):
        self.raw = mongomock.MongoClient().test_research_library
        self.name = self.raw.name
        self.client = self
        self.guard = threading.RLock()
        self.fail = None

    def __getitem__(self, name):
        return Collection(self, name)

    def list_collection_names(self):
        return self.raw.list_collection_names()

    def create_collection(self, name):
        return self.raw.create_collection(name)

    @contextmanager
    def start_session(self):
        yield self

    @contextmanager
    def start_transaction(self, **kwargs):
        with self.guard:
            before = {name: list(self.raw[name].find()) for name in self.raw.list_collection_names()}
            try:
                yield self
            except BaseException:
                for name in self.raw.list_collection_names():
                    self.raw[name].delete_many({})
                for name, rows in before.items():
                    if rows:
                        self.raw[name].insert_many(copy.deepcopy(rows))
                raise


@pytest.fixture
def clock():
    return [1000.0]


@pytest.fixture
def store(clock):
    return LibraryStore(Database(), clock=lambda: clock[0])


def make(store, *names):
    return [store.concept_create(name) for name in names]


def lease(store, docs, owner="agent-a"):
    return store.lease_acquire([doc["_id"] for doc in docs], owner)


def revisions(store, *docs):
    return {doc["_id"]: store.concept_get(doc["_id"])["revision"] for doc in docs}


def evidence_fixture(store):
    body = "A snapshot is immutable. Unicode: 🐘."
    source = store.source_put("https://example.org/reference", body)
    quote = "Unicode: 🐘."
    start = body.index(quote)
    claim = {"text": "The source contains a Unicode elephant.",
             "sources": [source["url"]], "confidence": "high",
             "verified_as_of": "2026-11-12", "volatile": False,
             "evidence": [{"url": source["url"], "source_id": source["_id"],
                "snapshot_sha256": source["snapshot_sha256"], "start": start,
                "end": start + len(quote), "quote": quote, "extraction_status": "complete"}]}
    return source, claim


def test_version_conflict_and_owned_lease(store):
    doc, = make(store, "Snapshot Isolation")
    granted = lease(store, [doc])
    token = granted["tokens"][doc["_id"]]
    updated = store.concept_update(doc["_id"], {"description": "Working knowledge"}, 1, token)
    assert updated["revision"] == 2
    assert store.concept_get(doc["_id"], 1)["description"] == ""
    with pytest.raises(Conflict):
        store.concept_update(doc["_id"], {"description": "Lost update"}, 1, token)
    with pytest.raises(LeaseConflict):
        store.concept_update(doc["_id"], {"description": "Stolen"}, 2, "wrong")
    assert store.concept_get(doc["_id"])["description"] == "Working knowledge"


def test_mutation_idempotency_binds_full_request(store):
    doc = store.concept_create("Idempotency", request_id="create-one")
    assert store.concept_create("Idempotency", request_id="create-one") == doc
    assert store.versions.count_documents({}) == 1
    with pytest.raises(Conflict):
        store.concept_create("Different", request_id="create-one")
    granted = store.lease_acquire([doc["_id"]], "a", request_id="claim-one")
    again = store.lease_acquire([doc["_id"]], "a", request_id="claim-one")
    assert granted == again
    # No plaintext lease token is written to receipts or the lease collection.
    token = granted["tokens"][doc["_id"]]
    assert token not in repr(list(store.receipts.find()))
    assert token not in repr(list(store.leases.find()))


def test_atomic_multi_acquire_no_partial_leases(store):
    a, b = make(store, "A", "B")
    lease(store, [b], "other")
    with pytest.raises(LeaseConflict):
        lease(store, [a, b])
    assert store.leases.find_one({"_id": a["_id"]}) is None


def test_expiry_and_fence_prevent_stale_owner_commit(store, clock):
    doc, = make(store, "Fencing")
    first = store.lease_acquire([doc["_id"]], "first", ttl_seconds=30)
    clock[0] += 31
    second = store.lease_acquire([doc["_id"]], "second", ttl_seconds=30)
    assert second["fences"][doc["_id"]] > first["fences"][doc["_id"]]
    with pytest.raises(LeaseConflict):
        store.concept_update(doc["_id"], {"name": "Old owner"}, 1,
                             first["tokens"][doc["_id"]])
    assert store.concept_update(doc["_id"], {"description": "new"}, 1,
                                second["tokens"][doc["_id"]])["revision"] == 2


def test_real_thread_race_only_one_owner(store):
    doc, = make(store, "Concurrent Work")
    start = threading.Barrier(3)
    results = []

    def acquire(owner):
        start.wait()
        try:
            store.lease_acquire([doc["_id"]], owner)
            results.append("acquired")
        except LeaseConflict:
            results.append("held")

    threads = [threading.Thread(target=acquire, args=(str(i),)) for i in range(2)]
    for thread in threads:
        thread.start()
    start.wait()
    for thread in threads:
        thread.join()
    assert sorted(results) == ["acquired", "held"]


def test_renew_release_and_delegate_require_token_and_owner(store):
    doc, = make(store, "Lease Delegation")
    granted = lease(store, [doc])
    with pytest.raises(LeaseConflict):
        store.lease_renew([doc["_id"]], granted["tokens"], "different")
    delegated = store.lease_delegate([doc["_id"]], granted["tokens"], "agent-a", "publisher")
    with pytest.raises(LeaseConflict):
        store.lease_release([doc["_id"]], granted["tokens"], "agent-a")
    store.lease_renew([doc["_id"]], delegated["tokens"], "publisher")
    listed = store.lease_list()
    assert "token" not in repr(listed) and "nonce" not in repr(listed)
    store.lease_release([doc["_id"]], delegated["tokens"], "publisher")
    assert store.lease_list()["leases"] == []


def test_legacy_reservation_provider_is_respected(store):
    doc, = make(store, "Paused Work")
    calls = []

    def held(ids, owner, run_id):
        calls.append((ids, owner, run_id))
        return [{"reason": "paused suite"}]

    store.reservation_provider = held
    with pytest.raises(LeaseConflict):
        store.lease_acquire([doc["_id"]], "agent", run_id="test-run")
    assert calls and store.leases.count_documents({}) == 0


def test_claim_identity_matches_repository_and_edits_version(store):
    module_path = Path(__file__).resolve().parents[3] / "scripts/research_claims.py"
    spec = importlib.util.spec_from_file_location("test_claim_contract", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    doc, = make(store, "Unicode Claims")
    granted = lease(store, [doc])
    _, claim = evidence_fixture(store)
    first = store.claim_mutate(doc["_id"], "add", claim, expected_revision=1,
        lease_token=granted["tokens"][doc["_id"]], request_id="add-claim")
    assert first["claim"]["claim_id"] == "clm:" + digest(module.claim_identity(doc["slug"], claim))
    assert store.claim_mutate(doc["_id"], "add", claim, expected_revision=1,
        lease_token=granted["tokens"][doc["_id"]], request_id="add-claim") == first
    second = store.claim_mutate(doc["_id"], "update", {"confidence": "medium"},
        lineage_id=first["claim"]["lineage_id"], expected_revision=2,
        lease_token=granted["tokens"][doc["_id"]])
    assert first["claim"]["claim_id"] != second["claim"]["claim_id"]
    assert first["claim"]["lineage_id"] == second["claim"]["lineage_id"]
    assert store.claim_versions.count_documents({}) == 2
    assert second["completion"]["status"] == "unverified"


def test_wrong_quote_wrong_source_and_utf8_byte_offsets_are_rejected(store):
    doc, = make(store, "Evidence Checks")
    granted = lease(store, [doc])
    _, claim = evidence_fixture(store)
    bad = copy.deepcopy(claim)
    bad["evidence"][0]["quote"] = "invented"
    with pytest.raises(ValueError):
        store.claim_mutate(doc["_id"], "add", bad, expected_revision=1,
                           lease_token=granted["tokens"][doc["_id"]])
    bad = copy.deepcopy(claim)
    bad["evidence"][0]["end"] += 3
    with pytest.raises(ValueError):
        store.claim_mutate(doc["_id"], "add", bad, expected_revision=1,
                           lease_token=granted["tokens"][doc["_id"]])
    assert store.concept_get(doc["_id"])["revision"] == 1


def test_source_snapshots_history_never_downgrade_current(store):
    first = store.source_put("HTTPS://Example.org/path/?utm_source=x#part", "First body")
    assert first["_id"] == source_id("https://example.org/path")
    assert normalize_url("HTTPS://Example.org/path/?utm_source=x#part") == "https://example.org/path"
    current = store.source_put(first["url"], "Current body", expected_revision=1)
    archived = store.source_put(first["url"], "Older immutable body", make_current=False)
    assert archived["current_unchanged"]
    assert store.source_get(first["_id"])["text"] == "Current body"
    assert store.source_get(first["_id"], first["snapshot_sha256"])["text"] == "First body"
    assert store.source_get(first["_id"], archived["imported_snapshot_sha256"])["text"] == "Older immutable body"
    assert current["revision"] == 2
    with pytest.raises(Conflict):
        store.source_put(first["url"], "Lost update", expected_revision=1)


def test_source_remove_respects_current_claims_then_tombstones(store):
    doc, = make(store, "Source Lifecycle")
    granted = lease(store, [doc])
    source, claim = evidence_fixture(store)
    added = store.claim_mutate(doc["_id"], "add", claim, expected_revision=1,
                               lease_token=granted["tokens"][doc["_id"]])
    with pytest.raises(Conflict):
        store.source_delete(source["_id"], 1)
    store.claim_mutate(doc["_id"], "remove", lineage_id=added["claim"]["lineage_id"],
                       expected_revision=2, lease_token=granted["tokens"][doc["_id"]])
    removed = store.source_delete(source["_id"], 1)
    assert removed["deleted"]
    assert store.source_get(source["_id"], source["snapshot_sha256"])["text"]


def test_parent_reparent_and_symmetric_relationships_are_reciprocal(store):
    a, b, child = make(store, "Parent A", "Parent B", "Child")
    granted = lease(store, [a, b, child])
    store.relation_mutate(child["_id"], a["_id"], "parent", "add",
                         revisions(store, a, child), granted["tokens"])
    assert store.concept_get(a["_id"])["children_ids"] == [child["_id"]]
    store.relation_mutate(child["_id"], b["_id"], "parent", "update",
                         revisions(store, a, b, child), granted["tokens"])
    assert store.concept_get(a["_id"])["children_ids"] == []
    assert store.concept_get(b["_id"])["children_ids"] == [child["_id"]]
    assert store.concept_get(child["_id"])["parent_id"] == b["_id"]
    store.relation_mutate(a["_id"], b["_id"], "related", "add",
                         revisions(store, a, b), granted["tokens"])
    assert store.concept_get(a["_id"])["related_ids"] == [b["_id"]]
    assert store.concept_get(b["_id"])["related_ids"] == [a["_id"]]


def test_cycle_and_missing_endpoint_fail_without_partial_graph_updates(store):
    a, b = make(store, "Ancestor", "Descendant")
    granted = lease(store, [a, b])
    store.relation_mutate(b["_id"], a["_id"], "parent", "add",
                         revisions(store, a, b), granted["tokens"])
    before = revisions(store, a, b)
    with pytest.raises(Conflict):
        store.relation_mutate(a["_id"], b["_id"], "parent", "add", before, granted["tokens"])
    assert revisions(store, a, b) == before
    with pytest.raises(KeyError):
        store.relation_mutate(a["_id"], "c:missing", "related", "add", before, granted["tokens"])


def test_transaction_rollback_prevents_half_edges_and_snapshots(store):
    a, b = make(store, "Left", "Right")
    granted = lease(store, [a, b])
    calls = []

    def fail(collection, method):
        if collection.endswith("versions") and method == "insert_one":
            calls.append(1)
            return len(calls) == 2
        return False

    store.database.fail = fail
    with pytest.raises(RuntimeError, match="injected"):
        store.relation_mutate(a["_id"], b["_id"], "related", "add",
                             revisions(store, a, b), granted["tokens"])
    store.database.fail = None
    assert store.concept_get(a["_id"])["related_ids"] == []
    assert store.concept_get(b["_id"])["related_ids"] == []
    assert store.versions.count_documents({}) == 2


def test_completed_state_cannot_be_self_attested(store):
    doc, = make(store, "Gate Authority")
    granted = lease(store, [doc])
    with pytest.raises(ValueError):
        store.concept_update(doc["_id"], {"state": "complete"}, 1, granted["tokens"][doc["_id"]])
    with pytest.raises(ValueError):
        store.claim_mutate(doc["_id"], "add", {"text": "Unsupported", "qualification": "SUPPORTED"},
                           expected_revision=1, lease_token=granted["tokens"][doc["_id"]])
    with pytest.raises(ValueError):
        store.complete(doc["_id"], 1, granted["tokens"][doc["_id"]], {"SUPPORTED": True})


def test_trusted_completion_then_mutation_invalidates_gate(store):
    doc, = make(store, "Verified Research")
    granted = lease(store, [doc])
    _, claim = evidence_fixture(store)
    store.claim_mutate(doc["_id"], "add", claim, expected_revision=1,
                       lease_token=granted["tokens"][doc["_id"]])
    store.completion_verifier = lambda current, receipt: {"artifact_sha256": digest(current), "gate": "v4"}
    completed = store.complete(doc["_id"], 2, granted["tokens"][doc["_id"]], {"trusted": "reference"})
    assert completed["state"] == "complete"
    assert completed["claims"][0]["qualification"] == "SUPPORTED"
    updated = store.concept_update(doc["_id"], {"summary": "New assertion"}, 3,
                                   granted["tokens"][doc["_id"]])
    assert updated["state"] == "incomplete" and updated["completion"]["status"] == "unverified"


def test_cvs_null_hard_gates_and_queue_stop_are_preserved(store):
    doc, = make(store, "Scored Frontier")
    assert doc["cvs"] is None
    granted = lease(store, [doc])
    updated = store.concept_update(doc["_id"], {"cvs_axes": {"Rel": 5, "Use": 5, "Nov": 0, "Int": 5, "Via": 5}},
                                   1, granted["tokens"][doc["_id"]])
    assert updated["cvs"] == 4 and updated["cvs_decision"] == "SKIP"
    queue = store.queue_put(doc["_id"], "stop", expected_revision=2,
                            lease_token=granted["tokens"][doc["_id"]])
    assert queue["stop"] and not queue["dispatched"]
    with pytest.raises(LeaseConflict):
        store.queue_put(doc["_id"], "resume", expected_revision=3,
                         lease_token=granted["tokens"][doc["_id"]])
    assert not store.queue_list()["queue"][0]["eligible"]


def test_real_importer_retains_scalar_cvs_including_zero_with_null_axes(store, tmp_path):
    from research_library_service.importer import import_library, read_inventory

    tree = tmp_path / "scalar-frontier.json"
    tree.write_text(json.dumps([
        {"concept": "Zero Score", "slug": "zero-score", "cvs": 0},
        {"concept": "Scalar Score", "slug": "scalar-score", "cvs": 3.5},
        {"concept": "Unscored", "slug": "unscored"},
    ]))
    inventory = read_inventory([tree])
    assert {doc["name"]: doc["cvs"] for doc in inventory["concepts"]} == {
        "Zero Score": 0, "Scalar Score": 3.5, "Unscored": None}
    assert all(doc["cvs_axes"] is None for doc in inventory["concepts"])
    receipt = import_library(store, tree_paths=[tree])
    assert receipt["imported"] == 3 and not receipt["partial"]
    for cid, expected in (("c:zero-score", 0), ("c:scalar-score", 3.5), ("c:unscored", None)):
        current = store.concept_get(cid)
        assert current["cvs"] == expected
        assert current["cvs_axes"] is None and current["cvs_decision"] == "REVIEW"
        assert current["completion"]["status"] == "unverified"
    queries = LibraryQueries(store)
    scored = {doc["id"]: doc for doc in queries.frontier(scored="scored")["items"]}
    assert set(scored) == {"c:zero-score", "c:scalar-score"}
    assert all(doc["eligibility"] == "review" for doc in scored.values())
    assert {doc["id"] for doc in queries.frontier(scored="unscored")["items"]} == {"c:unscored"}
    before = {cid: store.concept_get(cid)["revision"] for cid in scored}
    again = import_library(store, tree_paths=[tree])
    assert again["unchanged"] == 3 and again["imported"] == 0
    assert before == {cid: store.concept_get(cid)["revision"] for cid in scored}


def test_explicit_null_axes_alone_clear_derived_score_but_scalar_with_null_axes_is_retained(store):
    doc, = make(store, "Clear Derived Score")
    token = lease(store, [doc])["tokens"][doc["_id"]]
    scored = store.concept_update(doc["_id"], {"cvs_axes": {
        "Rel": 4, "Use": 4, "Nov": 4, "Int": 4, "Via": 4}}, 1, token)
    assert scored["cvs"] == 4 and scored["cvs_decision"] == "RESEARCH"
    cleared = store.concept_update(doc["_id"], {"cvs_axes": None}, 2, token)
    assert cleared["cvs"] is None and cleared["cvs_axes"] is None
    assert cleared["cvs_decision"] == "REVIEW"
    assert store.concept_get(doc["_id"], 2)["cvs"] == 4
    scalar = store.concept_update(doc["_id"], {"cvs": 0, "cvs_axes": None}, 3, token)
    assert scalar["cvs"] == 0 and scalar["cvs_axes"] is None
    assert scalar["cvs_decision"] == "REVIEW"
    expect_revision = scalar["revision"]
    with pytest.raises(ValueError, match="qualifying axis evidence"):
        store.concept_update(doc["_id"], {"cvs_decision": "RESEARCH"}, expect_revision, token)
    assert store.concept_get(doc["_id"])["revision"] == expect_revision


@pytest.mark.parametrize("axes,expected,decision", [
    ({"Rel": 4, "Use": 4, "Nov": 4, "Int": 4, "Via": 4}, 4, "RESEARCH"),
    ({"Rel": 5, "Use": 5, "Nov": 0, "Int": 5, "Via": 5}, 4, "SKIP"),
    ({"Rel": 5, "Use": 5, "Nov": 5, "Int": 5, "Via": 1}, 4.4, "SKIP"),
])
def test_numeric_axes_override_supplied_scalar_and_preserve_hard_gates(store, axes, expected, decision):
    doc, = make(store, "Axes Authority")
    token = lease(store, [doc])["tokens"][doc["_id"]]
    updated = store.concept_update(doc["_id"], {"cvs": 0, "cvs_axes": axes}, 1, token)
    assert updated["cvs"] == pytest.approx(expected)
    assert updated["cvs_decision"] == decision and updated["cvs_axes"] is not None
    if decision == "SKIP":
        with pytest.raises(ValueError, match="qualifying axis evidence"):
            store.concept_update(doc["_id"], {"cvs_decision": "RESEARCH"}, 2, token)
        assert store.concept_get(doc["_id"])["revision"] == 2


def test_pagination_alias_lookup_and_tombstone_history(store):
    docs = make(store, "One", "Two", "Three")
    page = store.concept_list(limit=2)
    assert page["has_more"] and len(page["items"]) == 2
    second = store.concept_list(after=page["next_cursor"], limit=2)
    assert len(second["items"]) == 1
    assert {d["_id"] for d in page["items"] + second["items"]} == {d["_id"] for d in docs}
    doc = docs[0]
    granted = lease(store, [doc])
    renamed = store.concept_update(doc["_id"], {"name": "Renamed"}, 1, granted["tokens"][doc["_id"]])
    assert store.resolve_concept("One")["_id"] == doc["_id"]
    removed = store.concept_delete(doc["_id"], 2, granted["tokens"][doc["_id"]])
    assert removed["deleted"] and not removed["active"]
    assert store.concept_get(doc["_id"], renamed["revision"])["name"] == "Renamed"


def test_import_is_idempotent_and_refuses_to_replace_local_edits(store):
    imported = store.import_concept({"name": "Imported", "slug": "imported", "metadata": {"coverage": "frontier"}},
                                    "canonical-corpus", digest(b"first"))
    again = store.import_concept({"name": "Imported", "slug": "imported", "metadata": {"coverage": "frontier"}},
                                 "canonical-corpus", digest(b"first"))
    assert again["unchanged"] and again["revision"] == imported["revision"]
    granted = lease(store, [imported])
    store.concept_update(imported["_id"], {"description": "Local work"}, 1,
                         granted["tokens"][imported["_id"]])
    store.lease_release([imported["_id"]], granted["tokens"], "agent-a")
    with pytest.raises(Conflict):
        store.import_concept({"name": "Imported", "slug": "imported"}, "canonical-corpus", digest(b"second"))


def test_import_context_marks_only_owned_reciprocal_changes(store):
    a = store.import_concept({"name": "Import A", "slug": "import-a"}, "corpus", digest(b"A"))
    b = store.import_concept({"name": "Import B", "slug": "import-b"}, "corpus", digest(b"B"))
    granted = lease(store, [a, b])
    with store.importing("corpus"):
        store.relation_mutate(a["_id"], b["_id"], "related", "add",
                             revisions(store, a, b), granted["tokens"])
    assert store.concept_get(a["_id"])["import_provenance"]["managed_revision"] == 2
    store.lease_release([a["_id"], b["_id"]], granted["tokens"], "agent-a")
    refreshed = store.import_concept({"name": "Import A", "slug": "import-a"}, "corpus", digest(b"A2"))
    assert refreshed["revision"] == 3


def test_transactionless_backend_fails_closed():
    raw = mongomock.MongoClient().test_transactions
    store = LibraryStore(raw)
    with pytest.raises(RuntimeError, match="transactions are required"):
        store.concept_create("No transaction")
    assert raw.research_concepts.count_documents({}) == 0


def test_authored_metadata_is_not_silently_stripped(store):
    doc, = make(store, "Metadata Identity")
    granted = lease(store, [doc])
    updated = store.concept_update(doc["_id"], {"metadata": {"nonce": "a documented term", "secret": "concept name"}},
                                   1, granted["tokens"][doc["_id"]])
    assert updated["metadata"]["nonce"] == "a documented term"
    assert updated["metadata"]["secret"] == "concept name"
    assert updated["managed_by"] == MANAGED_BY


@pytest.mark.parametrize("action", ["pause", "hold", "stop"])
def test_new_leases_never_steal_mongo_queue_holds_after_expiry(store, clock, action):
    doc, = make(store, "Held Queue " + action)
    granted = lease(store, [doc])
    entry = store.queue_put(doc["_id"], action, expected_revision=1,
                            lease_token=granted["tokens"][doc["_id"]])
    # A live owner can renew while preserving the pause.
    store.lease_renew([doc["_id"]], granted["tokens"], "agent-a", ttl_seconds=30)
    clock[0] += 31
    with pytest.raises(LeaseConflict, match="operator recovery"):
        store.lease_acquire([doc["_id"]], "new-agent")
    with pytest.raises(Conflict):
        store.queue_recover(doc["_id"], entry["revision"] + 1, "explicit operator decision")
    recovered = store.queue_recover(doc["_id"], entry["revision"], "explicit operator decision")
    assert recovered["filesystem_stop_unchanged"] and not recovered["dispatched"]
    assert recovered["recovery"]["previous_status"] in {"paused", "held"}
    assert store.lease_acquire([doc["_id"]], "new-agent")["leases"]


def test_completion_updates_queue_atomically(store):
    doc, = make(store, "Queued Completion")
    granted = lease(store, [doc])
    _, claim = evidence_fixture(store)
    store.claim_mutate(doc["_id"], "add", claim, expected_revision=1,
                       lease_token=granted["tokens"][doc["_id"]])
    queued = store.queue_put(doc["_id"], expected_revision=2,
                             lease_token=granted["tokens"][doc["_id"]])
    store.completion_verifier = lambda doc, receipt: {"artifact": "trusted"}
    completed = store.complete(doc["_id"], 3, granted["tokens"][doc["_id"]], {"ref": "bound"})
    queue = store.queue_list()["queue"][0]
    assert queue["status"] == "completed"
    assert queue["revision"] == queued["revision"] + 1
    assert queue["concept_revision"] == completed["revision"]
    assert not queue["eligible"]


def test_exact_import_replay_after_local_edit_is_not_reported_as_authority(store):
    original = {"name": "Guarded Import", "slug": "guarded-import"}
    imported = store.import_concept(original, "corpus", digest(b"same"))
    granted = lease(store, [imported])
    store.concept_update(imported["_id"], {"summary": "new local research"}, 1,
                         granted["tokens"][imported["_id"]])
    store.lease_release([imported["_id"]], granted["tokens"], "agent-a")
    with pytest.raises(Conflict, match="locally edited"):
        store.import_concept(original, "corpus", digest(b"same"))


def test_queue_import_preserves_holds_and_refuses_local_recovery_overwrite(store):
    doc, = make(store, "Imported Queue Hold")
    held = store.import_queue(doc["_id"], {"status": "paused", "STOP": True,
        "reason": "user pause"}, "legacy-queue", digest(b"held"))
    assert held["projection_only"] and not held["dispatched"]
    newer = store.import_queue(doc["_id"], {"status": "queued"}, "legacy-queue", digest(b"newer"))
    assert newer["status"] == "paused" and newer["stop"]
    store.queue_recover(doc["_id"], newer["revision"], "owner explicitly resumed DB queue")
    with pytest.raises(Conflict, match="locally edited"):
        store.import_queue(doc["_id"], {"status": "queued"}, "legacy-queue", digest(b"newer"))


def test_imported_proof_cannot_substitute_for_missing_bound_snapshot(store):
    store.completion_verifier = lambda doc, receipt: {"artifact": "previously-verified"}
    claim = {"text": "A historical assertion.", "sources": ["https://example.org/missing"],
             "confidence": "high", "evidence": [{"url": "https://example.org/missing",
                "source_id": source_id("https://example.org/missing"),
                "snapshot_sha256": digest(b"missing"), "start": 0, "end": 7,
                "quote": "missing", "extraction_status": "complete"}]}
    imported = store.import_concept({"name": "Missing Evidence", "slug": "missing-evidence",
        "state": "complete", "claims": [claim]}, "corpus", digest(b"source"),
        artifact_proof={"trusted_path_reference": "existing"})
    assert imported["state"] == "incomplete"
    assert imported["qualification"] == "unreviewed"
    assert imported["legacy_publication_proof"]["artifact"] == "previously-verified"
    assert "source-snapshot-unavailable" in imported["incomplete_reasons"]


def test_injected_claim_identity_is_used_for_current_immutable_versions(store):
    calls = []

    def identity(slug, claim):
        calls.append(slug)
        return {"concept_slug": slug, "text": claim["text"], "adapter": "maintained"}

    store.claim_identity = identity
    doc, = make(store, "Identity Adapter")
    granted = lease(store, [doc])
    added = store.claim_mutate(doc["_id"], "add", {"text": "Draft fact", "sources": []},
                               expected_revision=1, lease_token=granted["tokens"][doc["_id"]])
    assert calls == ["identity-adapter"]
    assert added["claim"]["claim_id"] == "clm:" + digest({
        "concept_slug": "identity-adapter", "text": "Draft fact", "adapter": "maintained"})


def test_lists_are_metadata_only_and_byte_bounded_without_skipping_rows(store):
    ids = []
    for index in range(5):
        doc = store.concept_create("Large Metadata " + str(index))
        ids.append(doc["_id"])
        # Use valid maximum metadata plus heavy claim text; the list must not return claims.
        store.concepts.update_one({"_id": doc["_id"]}, {"$set": {
            "terms": [str(i) + "t" * 1990 for i in range(256)],
            "claims": [{"text": "x" * 32000} for _ in range(100)]}})
    seen, cursor = [], ""
    while True:
        page = store.concept_list(after=cursor, limit=200)
        assert len(__import__("json").dumps(page).encode()) < 2 * 1024 * 1024
        assert all("claims" not in row and "search_text" not in row for row in page["items"])
        seen.extend(row["_id"] for row in page["items"])
        if not page["has_more"]:
            break
        assert page["next_cursor"] == page["items"][-1]["_id"]
        cursor = page["next_cursor"]
    assert seen == sorted(ids) and len(set(seen)) == 5


def test_oversized_metadata_is_an_explicit_stub_not_a_skipped_concept(store):
    doc, = make(store, "Oversized List Record")
    # Even an operator-written legacy record beyond the normal input bounds cannot inflate a list.
    store.concepts.update_one({"_id": doc["_id"]}, {"$set": {"description": "x" * 3_000_000}})
    page = store.concept_list()
    assert page["items"][0]["_id"] == doc["_id"]
    assert page["items"][0]["details_omitted"]
    assert not page["has_more"]


def test_import_source_refs_preserve_pins_and_report_snapshot_availability(store):
    source = store.source_put("https://example.org/imported-ref", "Reference body")
    ref = {"url": source["url"], "source_id": source["_id"],
           "snapshot_sha256": source["snapshot_sha256"]}
    imported = store.import_concept({"name": "Source Seeds", "slug": "source-seeds", "source_refs": [ref]},
                                    "corpus", digest(b"source-seeds"))
    assert imported["source_refs"][0]["snapshot_available"]
    assert imported["source_refs"][0]["snapshot_sha256"] == source["snapshot_sha256"]
    absent = {"url": "https://example.org/absent", "source_id": source_id("https://example.org/absent"),
              "snapshot_sha256": digest(b"absent")}
    other = store.import_concept({"name": "Absent Seeds", "source_refs": [absent]},
                                 "corpus", digest(b"absent-seeds"))
    assert not other["source_refs"][0]["snapshot_available"]
    assert other["qualification"] == "unreviewed"


def test_unlabelled_mongos_write_conflict_retries_whole_transaction_once_per_commit(
        store, monkeypatch):
    original = store.versions.insert_one
    writes, sleeps = [], []
    failure = OperationFailure("WriteConflict from mongos", code=112)
    assert not failure.has_error_label("TransientTransactionError")

    def version_write(*arguments, **keywords):
        # Failure after two writes proves the retry rolls the transaction back.
        assert store.concepts.count_documents({}) == 1
        assert store.versions.count_documents({}) == 0
        result = original(*arguments, **keywords)
        writes.append(True)
        if len(writes) < 3:
            raise failure
        return result

    monkeypatch.setattr(store.versions, "insert_one", version_write)
    monkeypatch.setattr(store_module.time, "sleep", sleeps.append)
    monkeypatch.setattr(store_module.secrets, "randbelow", lambda upper: upper - 1)
    created = store.concept_create("Mongos Retry", request_id="mongos-retry")
    assert created["revision"] == 1
    assert len(writes) == 3 and len(sleeps) == 2
    assert sleeps == pytest.approx([0.050, 0.075])
    assert store.concepts.count_documents({}) == 1
    assert store.versions.count_documents({}) == 1
    assert store.receipts.count_documents({}) == 1
    assert store.concept_create("Mongos Retry", request_id="mongos-retry") == created
    assert len(writes) == 3


def test_write_conflict_exhaustion_is_bounded_sanitized_and_has_no_partial_writes(
        store, monkeypatch):
    attempts, sleeps = [], []

    def conflict(session):
        assert store.meta.count_documents({}) == 0
        store.meta.insert_one({"_id": "partial", "secret": "private-diagnostic"}, session=session)
        attempts.append(True)
        raise OperationFailure("WriteConflict private-diagnostic", code=112)

    monkeypatch.setattr(store_module.time, "sleep", sleeps.append)
    monkeypatch.setattr(store_module.secrets, "randbelow", lambda upper: upper - 1)
    with pytest.raises(Conflict, match="retry with the same request ID") as failure:
        store._tx(conflict)
    assert "private-diagnostic" not in str(failure.value)
    assert len(attempts) == store_module.TX_MAX_ATTEMPTS
    assert len(sleeps) == store_module.TX_MAX_ATTEMPTS - 1
    assert all(0 < delay <= 0.525 for delay in sleeps)
    assert store.meta.count_documents({}) == 0


def test_transaction_retry_deadline_stops_before_another_attempt(store, monkeypatch):
    now, attempts = [0.0], []
    monkeypatch.setattr(store_module.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(store_module.time, "sleep", lambda delay: now.__setitem__(0, 31))

    def conflict(session):
        attempts.append(True)
        raise OperationFailure("WriteConflict", code=112)

    with pytest.raises(Conflict, match="transaction conflict"):
        store._tx(conflict)
    assert len(attempts) == 1


def test_nonretryable_mongo_errors_are_not_swallowed_or_retried(store, monkeypatch):
    attempts, sleeps = [], []
    monkeypatch.setattr(store_module.time, "sleep", sleeps.append)
    error = OperationFailure("Authorization failed", code=13)

    def denied(session):
        attempts.append(True)
        raise error

    with pytest.raises(OperationFailure) as failure:
        store._tx(denied)
    assert failure.value is error
    assert len(attempts) == 1 and not sleeps


def test_source_lookup_is_exact_read_only_metadata_with_current_archive_status(store):
    url = "HTTPS://Example.org/source/?keep=yes&utm_campaign=tracking#section"
    before = {name: list(store.database.raw[name].find()) for name in store.database.list_collection_names()}
    absent = store.source_lookup(url)
    assert absent == {"found": False, "source_id": source_id(url),
                      "url": "https://example.org/source?keep=yes", "source": None,
                      "snapshot_available": False}
    assert before == {name: list(store.database.raw[name].find())
                      for name in store.database.list_collection_names()}
    first = store.source_put(url, "old private source body")
    current = store.source_put(url, "current private source body", metadata={"title": "Source title"},
                               expected_revision=1)
    store.source_put(url, "older imported body", make_current=False)
    before = {name: list(store.database.raw[name].find()) for name in store.database.list_collection_names()}
    found = store.source_lookup(url)
    assert found["found"] and found["snapshot_available"]
    assert found["source"]["revision"] == 2
    assert found["source"]["snapshot_sha256"] == current["snapshot_sha256"]
    assert found["source"]["snapshot_sha256"] != first["snapshot_sha256"]
    assert "private source body" not in repr(found) and "older imported body" not in repr(found)
    assert before == {name: list(store.database.raw[name].find())
                      for name in store.database.list_collection_names()}
    store.snapshot_chunks.delete_one({"_id": current["_id"] + "@" + current["snapshot_sha256"] + ":0"})
    damaged = store.source_lookup(url)
    assert damaged["found"] and not damaged["snapshot_available"]
    assert damaged["source"]["revision"] == 2
    assert damaged["source"]["snapshot_sha256"] == current["snapshot_sha256"]


def test_source_lookup_distinguishes_retired_source_and_rejects_collision(store):
    source = store.source_put("https://example.org/retired", "Archived evidence")
    store.source_delete(source["_id"], 1)
    retired = store.source_lookup(source["url"])
    assert retired["found"] and retired["source"]["deleted"]
    assert retired["source"]["revision"] == 2 and retired["snapshot_available"]
    store.sources.update_one({"_id": source["_id"]}, {"$set": {"url": "https://example.org/collision"}})
    with pytest.raises(Conflict, match="identity collision"):
        store.source_lookup(source["url"])


@pytest.fixture
def live_check_module():
    path = Path(__file__).resolve().parents[1] / "scripts/live_check.py"
    spec = importlib.util.spec_from_file_location("isolated_live_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_live_synthetic_fixture_exercises_public_store_interfaces_without_atlas(store, live_check_module):
    check = live_check_module.LiveCheck()
    check.store = store
    check.records()
    assert store.status()["counts"]["concepts"] == 4
    assert store.status()["active_leases"] == 0
    assert "simultaneous_leases_exactly_one_winner" in check.checks
    assert "queue_hold_stop_recovery_and_frontier_accounting" in check.checks


def test_live_index_diagnostics_do_not_print_credentials_hosts_or_signed_details(live_check_module):
    error = OperationFailure("do not print this full error", code=508, details={
        "errmsg": "Temporary limit at shard.example.mongodb.net: mongodb+srv://user:private@cluster/db token=private",
        "$clusterTime": {"signature": {"hash": "private signature"}}})
    message = live_check_module.index_error_message(error)
    assert message.startswith("Temporary limit")
    assert all(value not in message for value in ("private", "user:", "mongodb.net", "clusterTime", "signature"))


@pytest.mark.parametrize("failed", [False, True])
def test_live_cleanup_uses_only_exact_creation_ledger_and_continues_after_drop_failure(
        live_check_module, failed):
    check = live_check_module.LiveCheck()
    owned = [check.prefix + "concepts", check.prefix + "versions"]
    check.expected, check.created = set(owned), list(owned)
    remaining, dropped, closed = {"research_concepts", "skills", *owned}, [], []

    def drop(name):
        dropped.append(name)
        if failed and name == owned[-1]:
            raise RuntimeError("temporarily unavailable")
        remaining.remove(name)

    check.store = SimpleNamespace(database=SimpleNamespace(
        drop_collection=drop, list_collection_names=lambda: list(remaining),
        client=SimpleNamespace(close=lambda: closed.append(True))))
    check.cleanup()
    assert dropped == list(reversed(owned))
    assert {"research_concepts", "skills"} <= remaining
    assert check.report["cleanup_verified"] is not failed
    assert check.report["collections_removed"] == (1 if failed else 2)
    assert closed == [True]
