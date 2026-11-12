from copy import deepcopy
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import mongomock
import pytest

from research_library_service.queries import (
    MANAGED_BY,
    MODEL,
    TEXT_DEFINITION,
    TEXT_INDEX,
    VECTOR_INDEX,
    LibraryQueries,
    provision_search_indexes,
)


def concept(key, **fields):
    return {"_id": "c:" + key, "slug": key, "name": key, "description": key,
            "managed_by": MANAGED_BY, "active": True, "state": "frontier",
            "revision": 1, "aliases": [], "terms": [], "children_ids": [],
            "cvs": None, "completion": {"status": "draft"}, **fields}


@pytest.fixture
def store():
    db = mongomock.MongoClient().research
    return SimpleNamespace(database=db, concepts=db.concepts, leases=db.leases,
                           queue=db.queue, prefix="research_", managed_by=MANAGED_BY)


def test_hybrid_scopes_both_native_channels_and_rechecks_stale_rows(store, monkeypatch):
    root = concept("root", children_ids=["c:child"])
    child = concept("child", parent_id="c:root")
    other = concept("other")
    archived = concept("archived", active=False, state="archived")
    store.concepts.insert_many([root, child, other, archived])
    pipelines = []

    def aggregate(pipeline, **kwargs):
        pipelines.append(pipeline)
        assert kwargs["maxTimeMS"] == 15000
        stale = {**archived, "active": True, "state": "frontier"}
        return [{**stale, "score": 0.99}, {**other, "score": 0.98}, {**child, "score": 0.8}]

    monkeypatch.setattr(store.concepts, "aggregate", aggregate)
    result = LibraryQueries(store).search("child workflow", topic_id="c:root", breadth="narrow")
    assert [row["id"] for row in result["hits"]] == ["c:child"]
    assert result["semantic"] and not result["degraded"]
    assert pipelines[0][0]["$vectorSearch"]["model"] == MODEL
    assert pipelines[0][0]["$vectorSearch"]["filter"]["slug"]["$in"] == ["child", "root"]
    assert pipelines[0][1]["$match"]["_id"]["$in"] == ["c:child", "c:root"]
    assert {"in": {"path": "slug", "value": ["child", "root"]}} in (
        pipelines[1][0]["$search"]["compound"]["filter"])


def test_keyword_fallback_is_reported_as_degraded_not_native_semantics(store, monkeypatch):
    store.concepts.insert_one(concept("cache", search_text="cache pressure eviction"))

    def fail(*args, **kwargs):
        raise RuntimeError("mongodb://secret:credential@private-host")

    monkeypatch.setattr(store.concepts, "aggregate", fail)
    result = LibraryQueries(store).search("cache pressure")
    assert result["hits"][0]["id"] == "c:cache"
    assert result["degraded"] and not result["semantic"]
    assert result["diagnostics"]["channels"]["keyword"]["fallback"]
    assert "secret" not in str(result) and "private-host" not in str(result)
    result = LibraryQueries(store).search("unmatched", mode="semantic")
    assert result["hits"] == [] and result["degraded"] and not result["semantic"]


@pytest.mark.parametrize("kwargs", [
    {"query": ""}, {"query": {}}, {"query": "x", "top": True},
    {"query": "x", "mode": "raw"}, {"query": "x", "breadth": "narrow"},
    {"query": "x", "scope_ids": {"$ne": []}},
])
def test_retrieval_rejects_unbounded_or_unstructured_options(store, kwargs):
    with pytest.raises(ValueError):
        LibraryQueries(store).search(**kwargs)


def test_broad_search_does_not_silently_limit_to_topic_subtree(store, monkeypatch):
    store.concepts.insert_many([concept("root"), concept("other", description="shared concept")])
    monkeypatch.setattr(store.concepts, "aggregate", lambda *a, **kw: [])
    result = LibraryQueries(store).search("other", topic_id="c:root", breadth="broad", mode="keyword")
    assert result["hits"][0]["id"] == "c:other"
    assert result["diagnostics"]["scope"]["concept_count"] == 2
    with pytest.raises(KeyError):
        LibraryQueries(store).search("x", scope_ids=["c:missing"])


def test_related_graph_is_cycle_safe_paginated_and_derives_siblings(store):
    store.concepts.insert_many([
        concept("root", children_ids=["c:a", "c:b"]),
        concept("a", parent_id="c:root", related_ids=["c:c"]),
        concept("b", parent_id="c:root"),
        concept("c", related_ids=["c:a"]),
    ])
    query = LibraryQueries(store)
    first = query.related("c:a", depth=2, limit=2)
    assert first["total"] == 4 and first["has_more"]
    second = query.related("c:a", depth=2, limit=2, after=first["next_after"])
    assert not second["has_more"]
    rows = first["items"] + second["items"]
    assert len({row["id"] for row in rows}) == 4
    assert next(row for row in rows if row["id"] == "c:b")["via"] == ["sibling"]
    assert query.related("c:a", depth=0)["total"] == 1
    store.concepts.update_one({"_id": "c:a"}, {"$inc": {"revision": 1}})
    with pytest.raises(ValueError, match="PAGINATION_CONFLICT"):
        query.related("c:a", depth=2, limit=2, after=first["next_after"])


def test_frontier_paging_keeps_null_zero_low_scores_and_holds(store):
    axes = dict.fromkeys(["relevance", "usefulness", "novelty", "interest", "viability"], 4)
    rows = [concept(f"item-{i:03}") for i in range(305)]
    rows[0].update(cvs=0, cvs_axes={**axes, "novelty": 0}, cvs_decision="SKIP")
    rows[1].update(cvs=4, cvs_axes=axes, cvs_decision="RESEARCH")
    rows[2].update(cvs=2, cvs_axes=axes, cvs_decision="RESEARCH")
    rows[3].update(cvs=4, cvs_decision="RESEARCH")  # Imported scalar needs review.
    store.concepts.insert_many(rows)
    store.leases.insert_one({"_id": rows[1]["_id"], "managed_by": MANAGED_BY,
                             "owner": "another-agent", "token_hash": "do-not-leak",
                             "expires_at": datetime.now(UTC) + timedelta(minutes=2)})
    store.queue.insert_one({"_id": rows[2]["_id"], "managed_by": MANAGED_BY,
                            "state": "paused", "owner": "paused-suite"})
    query = LibraryQueries(store)
    seen, cursor = [], ""
    while True:
        result = query.frontier(after=cursor, limit=100)
        seen.extend(result["items"])
        cursor = result["next_after"]
        if not cursor:
            break
    assert len(seen) == len({row["id"] for row in seen}) == 305
    by_id = {row["id"]: row for row in seen}
    assert by_id[rows[0]["_id"]]["cvs"] == 0
    assert by_id[rows[0]["_id"]]["eligibility"] == "hard-gated-review"
    assert by_id[rows[1]["_id"]]["eligibility"] == "held"
    assert by_id[rows[2]["_id"]]["holder"]["kind"] == "paused"
    assert by_id[rows[3]["_id"]]["eligibility"] == "review"
    assert "do-not-leak" not in str(seen)
    assert query.frontier(scored="unscored")["total"] == 301
    assert query.frontier(scored="scored")["total"] == 4


def test_incomplete_reports_gate_scope_and_active_holds_separately(store):
    store.concepts.insert_many([
        concept("accepted", state="complete", completion={"status": "verified"}),
        concept("stale", state="complete", completion={"status": "verified", "stale": True}),
        concept("draft", incomplete_reasons=["missing-source-snapshot"]),
    ])
    result = LibraryQueries(store).incomplete()
    assert result["total"] == 2
    by_id = {row["id"]: row for row in result["items"]}
    assert "stale-gate-binding" in by_id["c:stale"]["incomplete_reasons"]
    assert "missing-source-snapshot" in by_id["c:draft"]["incomplete_reasons"]


def test_peer_packet_preserves_wording_pins_and_does_not_inherit_support(store):
    now = datetime.now(UTC).isoformat()
    old = (datetime.now(UTC) - timedelta(days=35)).isoformat()
    claim = {"lineage_id": "l1", "claim_id": "clm:pinned", "text": "Use planCacheKey exactly.",
             "evidence": [{"quote": "planCacheKey", "source_id": "src:pinned",
                           "snapshot_sha256": "a" * 64, "start": 0, "end": 12}],
             "qualification": "SUPPORTED"}
    store.concepts.insert_many([
        concept("parent", children_ids=["c:target", "c:peer"]),
        concept("target", parent_id="c:parent"),
        concept("peer", parent_id="c:parent", terms=["planCacheKey"], aliases=["Plan cache key"],
                claims=[claim], source_refs=[
                    {"url": "https://docs.example/current", "source_id": "src:pinned",
                     "snapshot_sha256": "a" * 64, "fetched_at": now},
                    {"url": "https://docs.example/old", "fetched_at": old}]),
    ])
    result = LibraryQueries(store).peer_seeds("c:target")
    peer = next(p for p in result["peers"] if p["id"] == "c:peer")
    assert peer["claim_candidates"][0] == claim
    assert peer["vocabulary"] == ["planCacheKey"]
    assert result["verified_claims_inherited"] is False
    assert len(result["fresh_source_seeds"]) == 1
    assert any(x["freshness"] == "stale" for x in result["source_candidates"])
    assert result["independent_origins_not_multiplied"]


def test_oversized_peer_is_omitted_not_silently_truncated_into_a_different_claim(store):
    store.concepts.insert_many([
        concept("p", children_ids=["c:t", "c:big"]),
        concept("t", parent_id="c:p"),
        concept("big", parent_id="c:p", claims=[{"text": "X" * (600 * 1024)}]),
    ])
    result = LibraryQueries(store).peer_seeds("c:t")
    assert result["truncated"] and result["omitted_oversized_peers"] == 1


def test_provision_only_changes_owned_named_indexes(store, monkeypatch):
    existing = [{"name": "foreign-search", "status": "READY", "queryable": True},
                {"name": TEXT_INDEX, "latestDefinition": deepcopy(TEXT_DEFINITION),
                 "status": "READY", "queryable": True}]
    created, updated = [], []
    monkeypatch.setattr(store.concepts, "list_search_indexes", lambda: deepcopy(existing))
    monkeypatch.setattr(store.concepts, "create_search_index", lambda model: created.append(model.document))
    monkeypatch.setattr(store.concepts, "update_search_index",
                        lambda name, definition: updated.append((name, definition)))
    result = provision_search_indexes(store)
    assert [row["name"] for row in created] == [VECTOR_INDEX]
    assert not updated
    assert result["ready"] is False
    assert result["model"] == MODEL


def test_epoch_leases_and_legacy_holds_are_visible_without_secrets(store):
    store.concepts.insert_many([concept("live"), concept("expired"), concept("legacy")])
    stamp = datetime.now(UTC).timestamp()
    store.leases.insert_many([
        {"_id": "c:live", "managed_by": MANAGED_BY, "status": "held", "owner": "worker",
         "expires_at": stamp + 120, "token_hash": "never-show-this"},
        {"_id": "c:expired", "managed_by": MANAGED_BY, "status": "held", "owner": "old",
         "expires_at": stamp - 120},
    ])
    store.reservation_provider = lambda ids, owner, run: {
        "c:legacy": {"owner": "legacy-run", "stop": True, "token": "private-token"}}
    rows = {row["id"]: row for row in LibraryQueries(store).frontier()["items"]}
    assert rows["c:live"]["eligibility"] == "held"
    assert rows["c:expired"]["eligibility"] == "needs-scoring"
    assert rows["c:legacy"]["holder"]["kind"] == "legacy-reservation"
    assert "private-token" not in str(rows) and "never-show-this" not in str(rows)


def test_peer_source_freshness_binds_current_metadata_to_exact_snapshot(store):
    import hashlib
    store.sources = store.database.sources
    text = "Use exact API wording."
    sha = hashlib.sha256(text.encode()).hexdigest()
    evidence = [
        {"source_id": "src:current", "snapshot_sha256": "a" * 64,
         "url": "https://docs.example/current"},
        {"source_id": "src:history", "snapshot_sha256": "b" * 64,
         "url": "https://docs.example/history"},
    ]
    store.concepts.insert_many([
        concept("p", children_ids=["c:t", "c:peer"]), concept("t", parent_id="c:p"),
        concept("peer", parent_id="c:p", claims=[{"text": text, "evidence": evidence}],
                metadata={"canonical_claim_versions": [{"canonical_claim_id": "clm:original",
                    "identity_slug": "original-slug", "statement_sha256": sha}]}),
    ])
    store.sources.insert_many([
        {"_id": "src:current", "managed_by": MANAGED_BY, "snapshot_sha256": "a" * 64,
         "url": evidence[0]["url"], "metadata": {"fetched_at": datetime.now(UTC).isoformat()}},
        {"_id": "src:history", "managed_by": MANAGED_BY, "snapshot_sha256": "c" * 64,
         "url": evidence[1]["url"], "metadata": {"fetched_at": datetime.now(UTC).isoformat()}},
    ])
    result = LibraryQueries(store).peer_seeds("c:t")
    assert [x["source_id"] for x in result["fresh_source_seeds"]] == ["src:current"]
    assert next(x for x in result["source_candidates"] if x["source_id"] == "src:history")[
        "freshness"] == "unknown"
    peer = next(x for x in result["peers"] if x["id"] == "c:peer")
    assert peer["claim_candidates"][0]["canonical_provenance"][0][
        "canonical_claim_id"] == "clm:original"
    assert result["verified_claims_inherited"] is False


def test_large_metadata_pages_preserve_all_ids_and_bound_mcp_compatibility_serialization(store):
    import json

    from research_library_service.queries import MAX_METADATA_BYTES

    rows = [concept(f"large-{i:03}", cvs_rationale="r" * 20000) for i in range(90)]
    rows[0]["source_refs"] = [{"source_id": f"src:{i:016x}", "url": "x" * 3000}
                              for i in range(1024)]
    store.concepts.insert_many(rows)
    store.queue.insert_one({"_id": rows[1]["_id"], "managed_by": MANAGED_BY,
                            "status": "held", "continuation": "c" * (3 * 1024 * 1024)})
    query, after, found, pages = LibraryQueries(store), "", [], 0
    while True:
        page = query.frontier(limit=200, after=after)
        # Model the SDK's structured output plus text compatibility result.
        wire = {"structuredContent": page,
                "content": [{"type": "text", "text": json.dumps(page, indent=2)}]}
        assert len(json.dumps(wire).encode()) < MAX_METADATA_BYTES
        found.extend(page["items"])
        pages += 1
        if not page["has_more"]:
            assert page["complete_page"]
            break
        assert not page["complete_page"] and page["next_cursor"]
        after = page["next_cursor"]
    assert pages > 1 and len(found) == len({x["id"] for x in found}) == 90
    first = next(x for x in found if x["id"] == rows[0]["_id"])
    held = next(x for x in found if x["id"] == rows[1]["_id"])
    assert first["source_ref_count"] == 1024 and first["details_omitted"]
    assert "source_refs" not in first
    assert held["eligibility"] == "held" and held["details_omitted"]


def test_pending_canonical_family_keeps_held_node_in_scope_without_changing_physical_parent(store, monkeypatch):
    store.concepts.insert_many([
        concept("root"),
        concept("held", parent_id=None, metadata={"owner_import": {"canonical_parent_id": "c:root"}}),
    ])
    store.queue.insert_one({"_id": "c:held", "managed_by": MANAGED_BY, "status": "held"})
    monkeypatch.setattr(store.concepts, "aggregate", lambda *args, **kwargs: [])
    query = LibraryQueries(store)
    hit = query.search("held", mode="keyword", breadth="narrow", topic_id="c:root")["hits"][0]
    assert hit["parent_id"] is None and hit["pending_parent_id"] == "c:root"
    assert hit["family_reconciliation_pending"]
    child = next(x for x in query.related("c:root", depth=1)["items"] if x["id"] == "c:held")
    parent = next(x for x in query.related("c:held", depth=1)["items"] if x["id"] == "c:root")
    assert child["via"] == ["pending-child"] and parent["via"] == ["pending-parent"]
    frontier = next(x for x in query.frontier(topic_id="c:root")["items"] if x["id"] == "c:held")
    assert frontier["eligibility"] == "held" and frontier["cvs"] is None
    incomplete = next(x for x in query.incomplete(topic_id="c:root")["items"] if x["id"] == "c:held")
    assert "canonical-family-pending" in incomplete["incomplete_reasons"]
    peers = query.peer_seeds("c:held")
    assert peers["parent_id"] is None and peers["peer_selection_includes_pending_family"]
    assert store.concepts.find_one({"_id": "c:held"})["parent_id"] is None


def test_real_working_reparent_and_detach_do_not_resurrect_old_imported_family_candidate():
    from test_store_core import Database

    from research_library_service.models import digest
    from research_library_service.store import LibraryStore

    store = LibraryStore(Database())
    for name, metadata in [("Root", {}), ("Other", {}), ("Child", {
            "owner_import": {"canonical_parent_id": "c:root"}})]:
        document = {"name": name, "metadata": metadata}
        store.import_concept(document, "corpus", digest(document))
    query = LibraryQueries(store)
    assert query.related("c:root", depth=1)["total"] == 2
    ids = ["c:root", "c:other", "c:child"]
    grants = store.lease_acquire(ids, "editor")
    revisions = {cid: store.concept_get(cid)["revision"] for cid in ids}
    store.relation_mutate("c:child", "c:other", "parent", "add", revisions, grants["tokens"])
    assert query.related("c:root", depth=1)["total"] == 1
    assert store.concept_get("c:child")["family_override"] is True
    revisions = {cid: store.concept_get(cid)["revision"] for cid in ids}
    store.relation_mutate("c:child", "c:other", "parent", "remove", revisions, grants["tokens"])
    assert query.related("c:root", depth=1)["total"] == 1
    child = next(x for x in query.incomplete()["items"] if x["id"] == "c:child")
    assert "canonical-family-pending" not in child["incomplete_reasons"]
    assert "pending_parent_id" not in child


def test_late_active_claims_remain_keyword_discoverable_after_semantic_input_truncation(store, monkeypatch):
    store.concepts.insert_many([
        concept("long", search_text="prefix " * 4000, search_text_truncated=True,
                claims=[{"text": "RareLateClaimMarker", "deleted": False},
                        {"text": "RemovedClaimMarker", "deleted": True}]),
        concept("legacy"),
    ])
    def native_unavailable(*args, **kwargs):
        raise RuntimeError("Fixture native index unavailable")
    monkeypatch.setattr(store.concepts, "aggregate", native_unavailable)
    query = LibraryQueries(store)
    found = query.search("RareLateClaimMarker", mode="keyword")
    assert [x["id"] for x in found["hits"]] == ["c:long"]
    assert found["hits"][0]["semantic_text_truncated"] is True
    assert found["diagnostics"]["channels"]["keyword"]["full_claim_text"]
    assert found["degraded"] and found["diagnostics"]["semantic_truncated_hits"] == 1
    assert not query.search("RemovedClaimMarker", mode="keyword")["hits"]
    legacy = query.search("legacy", mode="keyword")
    assert legacy["hits"][0]["semantic_text_truncated"] is None


def test_search_batches_fresh_candidates_and_returns_current_revision_after_index_changes(store, monkeypatch):
    kept, deleted = concept("kept", description="old"), concept("deleted")
    store.concepts.insert_many([kept, deleted])
    original_find, batch_reads = store.concepts.find, []

    def native_index(*args, **kwargs):
        store.concepts.update_one({"_id": "c:kept"}, {
            "$set": {"revision": 9, "description": "current working revision"}})
        store.concepts.update_one({"_id": "c:deleted"}, {"$set": {"deleted": True}})
        return [{**kept, "score": 0.9}, {**deleted, "score": 0.8}]

    def find(query, projection=None, *args, **kwargs):
        if isinstance(query.get("_id"), dict) and "$in" in query["_id"]:
            batch_reads.append((query, projection))
        return original_find(query, projection, *args, **kwargs)

    monkeypatch.setattr(store.concepts, "aggregate", native_index)
    monkeypatch.setattr(store.concepts, "find", find)
    result = LibraryQueries(store).search("different semantic wording", mode="semantic")
    assert len(batch_reads) == 1
    assert batch_reads[0][0]["_id"]["$in"] == ["c:deleted", "c:kept"]
    assert "claims" not in batch_reads[0][1]
    assert len(result["hits"]) == 1 and result["hits"][0]["id"] == "c:kept"
    assert result["hits"][0]["revision"] == 9
    assert result["hits"][0]["description"] == "current working revision"
