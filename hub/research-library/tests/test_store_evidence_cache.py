import copy
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

import pytest
from pymongo.errors import OperationFailure
from test_store_core import Database, evidence_fixture

import research_library_service.store as store_module
from research_library_service.models import digest
from research_library_service.store import LibraryStore


@pytest.fixture
def store():
    return LibraryStore(Database(), clock=lambda: 1000)


def watch_evidence_reads(store, monkeypatch):
    counts, lock = Counter(), threading.Lock()
    for name in ("sources", "snapshots", "snapshot_chunks"):
        collection = getattr(store, name)
        original = collection.find_one

        def observed(*args, _name=name, _original=original, **kwargs):
            with lock:
                counts[_name] += 1
            return _original(*args, **kwargs)

        monkeypatch.setattr(collection, "find_one", observed)
    return counts


def test_many_claim_import_and_full_completion_read_each_pin_only_once(store, monkeypatch):
    _, claim = evidence_fixture(store)
    document = {"name": "Many Claims", "claims": [
        {**copy.deepcopy(claim), "text": f"Synthetic claim {i}"} for i in range(200)]}
    counts = watch_evidence_reads(store, monkeypatch)
    imported = store.import_concept(document, "corpus", digest(document))
    assert counts == {"sources": 1, "snapshots": 1, "snapshot_chunks": 1}
    assert store._evidence_context.get() is None
    held = store.lease_acquire([imported["_id"]], "publisher")
    store.completion_verifier = lambda doc, receipt: {"artifact_sha256": "a" * 64}
    counts.clear()
    completed = store.complete(imported["_id"], 1, held["tokens"][imported["_id"]], {})
    assert len(completed["claims"]) == 200
    assert all(row["qualification"] == "SUPPORTED" for row in completed["claims"])
    assert counts == {"sources": 1, "snapshots": 1, "snapshot_chunks": 1}
    assert store._evidence_context.get() is None


def test_transaction_retry_has_fresh_cache_and_rolls_back_prior_attempt(store, monkeypatch):
    _, claim = evidence_fixture(store)
    counts, frames = watch_evidence_reads(store, monkeypatch), []
    monkeypatch.setattr(store_module.time, "sleep", lambda delay: None)

    def attempt(session):
        frame = store._evidence_context.get()
        assert frame["entries"] == {} and frame["bytes"] == 0
        frames.append(frame)
        assert store.meta.count_documents({"_id": "attempt-probe"}) == 0
        for i in range(10):
            store._claim("retry", claim, session, "lineage")
        if len(frames) == 1:
            store.meta.insert_one({"_id": "attempt-probe"}, session=session)
            raise OperationFailure("WriteConflict", code=112)
        return "committed"

    assert store._tx(attempt) == "committed"
    assert len(frames) == 2 and frames[0] is not frames[1]
    assert counts == {"sources": 2, "snapshots": 2, "snapshot_chunks": 2}
    assert store.meta.count_documents({"_id": "attempt-probe"}) == 0
    assert store._evidence_context.get() is None


def test_new_transaction_detects_changed_source_metadata_and_cache_never_skips_url_validation(store):
    source, claim = evidence_fixture(store)
    store._tx(lambda session: store._claim("first", claim, session, "lineage"))
    store.sources.update_one({"_id": source["_id"]}, {"$set": {"url": "https://other.example/source"}})
    with pytest.raises(ValueError, match="different source URL"):
        store._tx(lambda session: store._claim("second", claim, session, "lineage"))
    assert store._evidence_context.get() is None


def test_new_transaction_and_nontransactional_reads_detect_snapshot_corruption(store):
    source, _ = evidence_fixture(store)
    sid, sha = source["_id"], source["snapshot_sha256"]
    store._tx(lambda session: store._snapshot_text(sid, sha, session))
    store.snapshot_chunks.update_one({"_id": f"{sid}@{sha}:0"}, {"$set": {"data": b"corrupted"}})
    with pytest.raises(ValueError, match="integrity check failed"):
        store._tx(lambda session: store._snapshot_text(sid, sha, session))
    with pytest.raises(ValueError, match="integrity check failed"):
        store.source_get(sid)
    assert store._evidence_context.get() is None


def test_bad_evidence_and_missing_pin_are_never_accepted_or_negatively_cached(store, monkeypatch):
    _, claim = evidence_fixture(store)
    counts = watch_evidence_reads(store, monkeypatch)

    def verify(session):
        store._claim("valid", claim, session, "lineage")
        wrong = copy.deepcopy(claim)
        wrong["evidence"][0]["quote"] = "Different quotation"
        with pytest.raises(ValueError, match="does not match"):
            store._claim("invalid", wrong, session, "lineage")
        for i in range(2):
            with pytest.raises(KeyError, match="No such source snapshot"):
                store._snapshot_text(claim["evidence"][0]["source_id"], "0" * 64, session)
        assert len(store._evidence_context.get()["entries"]) == 2

    store._tx(verify)
    assert counts == {"sources": 1, "snapshots": 3, "snapshot_chunks": 1}


def test_nontransactional_and_other_session_reads_bypass_active_cache(store, monkeypatch):
    source, _ = evidence_fixture(store)
    sid, sha = source["_id"], source["snapshot_sha256"]
    counts = watch_evidence_reads(store, monkeypatch)

    def read(session):
        for unused in range(2):
            store._source(sid)
            store._snapshot_text(sid, sha)
            store._source(sid, object())
            store._snapshot_text(sid, sha, object())
        assert store._evidence_context.get()["entries"] == {}
        for unused in range(2):
            store._source(sid, session)
            store._snapshot_text(sid, sha, session)

    store._tx(read)
    assert counts == {"sources": 5, "snapshots": 5, "snapshot_chunks": 5}
    assert store._evidence_context.get() is None


def test_cached_metadata_is_defensively_copied_and_deleted_access_stays_enforced(store):
    source, _ = evidence_fixture(store)
    store.sources.update_one({"_id": source["_id"]}, {"$set": {"deleted": True}})

    def read(session):
        original = store._source(source["_id"], session, deleted=True)
        original["url"] = "https://tampered.example/"
        original["metadata"]["injected"] = True
        cached = store._source(source["_id"], session, deleted=True)
        assert cached["url"] == source["url"] and "injected" not in cached["metadata"]
        with pytest.raises(KeyError):
            store._source(source["_id"], session, deleted=False)
        body, snapshot = store._snapshot_text(source["_id"], source["snapshot_sha256"], session)
        snapshot["bytes"] = 0
        repeated, untouched = store._snapshot_text(source["_id"], source["snapshot_sha256"], session)
        assert repeated == body and untouched["bytes"] == len(body.encode())

    store._tx(read)


@pytest.mark.parametrize("constraint", ["bytes", "entries"])
def test_budget_or_entry_overflow_skips_retention_without_skipping_validation(store, monkeypatch, constraint):
    _, claim = evidence_fixture(store)
    counts = watch_evidence_reads(store, monkeypatch)
    monkeypatch.setattr(store_module, "MAX_EVIDENCE_CACHE_BYTES" if constraint == "bytes"
                        else "MAX_EVIDENCE_CACHE_ENTRIES", 1)

    def validate(session):
        for i in range(3):
            store._claim("bounded", claim, session, "lineage")
        frame = store._evidence_context.get()
        assert frame["bytes"] <= store_module.MAX_EVIDENCE_CACHE_BYTES
        assert len(frame["entries"]) <= store_module.MAX_EVIDENCE_CACHE_ENTRIES

    store._tx(validate)
    assert counts["snapshots"] == counts["snapshot_chunks"] == 3
    assert counts["sources"] == (3 if constraint == "bytes" else 1)


def test_cache_budget_accounts_for_multibyte_payload_and_combines_all_entries(store, monkeypatch):
    ascii_source = store.source_put("https://example.org/a", "a" * 100)
    unicode_source = store.source_put("https://example.org/b", "🐘" * 100)
    key = ("snapshot", ascii_source["_id"], ascii_source["snapshot_sha256"])
    value = store._snapshot_text(ascii_source["_id"], ascii_source["snapshot_sha256"])
    ascii_size = store_module._evidence_cache_size((key, value)) + 128
    counts = watch_evidence_reads(store, monkeypatch)
    monkeypatch.setattr(store_module, "MAX_EVIDENCE_CACHE_BYTES", ascii_size + 10)

    def read(session):
        for i in range(2):
            store._snapshot_text(unicode_source["_id"], unicode_source["snapshot_sha256"], session)
        assert store._evidence_context.get()["entries"] == {}
        for i in range(2):
            store._snapshot_text(ascii_source["_id"], ascii_source["snapshot_sha256"], session)
        frame = store._evidence_context.get()
        assert len(frame["entries"]) == 1 and frame["bytes"] == ascii_size
        store._source(ascii_source["_id"], session)
        assert len(frame["entries"]) == 1 and frame["bytes"] <= store_module.MAX_EVIDENCE_CACHE_BYTES

    store._tx(read)
    assert counts["snapshot_chunks"] == 3


def test_concurrent_transaction_contexts_never_share_cache_or_mutable_results(store, monkeypatch):
    source, claim = evidence_fixture(store)
    counts, rendezvous = watch_evidence_reads(store, monkeypatch), threading.Barrier(2)

    @contextmanager
    def concurrent_read_transaction(**kwargs):
        # Read-only callbacks can overlap; no fake rollback or writes are needed.
        yield store.database

    monkeypatch.setattr(store.database, "start_transaction", concurrent_read_transaction)

    def worker():
        def validate(session):
            frame = store._evidence_context.get()
            assert frame["entries"] == {}
            store._claim("thread", claim, session, "lineage")
            rendezvous.wait(timeout=3)
            changed = store._source(source["_id"], session)
            changed["url"] = "https://thread-local.example/"
            store._claim("thread", claim, session, "lineage")
            return id(frame)
        identity = store._tx(validate)
        assert store._evidence_context.get() is None
        return identity

    with ThreadPoolExecutor(max_workers=2) as pool:
        identities = [future.result(timeout=5) for future in [pool.submit(worker), pool.submit(worker)]]
    assert len(set(identities)) == 2
    assert counts == {"sources": 2, "snapshots": 2, "snapshot_chunks": 2}
    assert store._evidence_context.get() is None
