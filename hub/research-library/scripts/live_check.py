#!/usr/bin/env python3
"""Owner-local synthetic Atlas verification; removes only its newly created namespaces.

Run with: uv run --project hub/research-library python \
  hub/research-library/scripts/live_check.py --env-file /absolute/private/mongo.env
No credentials, source text, lease tokens, customer data, or server diagnostics
are printed. Native auto-embedding applies only to this check's synthetic text.
"""
from __future__ import annotations

import argparse
import json
import re
import secrets
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from pymongo.errors import OperationFailure

from research_library_service.environment import load_environment
from research_library_service.models import MANAGED_BY
from research_library_service.queries import (
    TEXT_INDEX,
    VECTOR_INDEX,
    LibraryQueries,
)
from research_library_service.service import Service
from research_library_service.store import Conflict, LeaseConflict, LibraryStore


def emit(value):
    print(json.dumps(value, sort_keys=True), flush=True)


def require(value, check):
    if not value:
        raise AssertionError(check)


def expect(error, function):
    try:
        function()
    except error:
        return
    raise AssertionError("expected_rejection_missing")


def index_error_message(error):
    """Only index-management errmsg; never emit the full signed driver document."""
    value = (getattr(error, "details", None) or {}).get("errmsg", "")
    if not isinstance(value, str):
        return ""
    value = re.sub(r"(?:mongodb(?:\+srv)?|https?)://[^\s,;]+", "[connection redacted]", value,
                   flags=re.IGNORECASE)
    value = re.sub(r"\b[a-z0-9-]+(?:\.[a-z0-9-]+)+\b", "[host redacted]", value,
                   flags=re.IGNORECASE)
    value = re.sub(r"(?:password|secret|token|credential|api[_-]?key)\s*[:=]\s*[^\s,;]+",
                   "[credential redacted]", value, flags=re.IGNORECASE)
    return value[:500]


class LiveCheck:
    def __init__(self, wait_seconds=600):
        self.wait_seconds = wait_seconds
        self.prefix = f"research_check_{int(time.time())}_{secrets.token_hex(6)}_"
        self.store = None
        self.created = []
        self.checks = []
        self.stage = "connection"
        self.report = {"ok": False, "cleanup_verified": False, "checks": self.checks}

    def passed(self, name):
        self.checks.append(name)
        emit({"event": "check_passed", "check": name, "passed": len(self.checks)})

    def run(self):
        try:
            self.store = LibraryStore(prefix=self.prefix)
            hello = self.store.database.client.admin.command("hello")
            require(hello.get("logicalSessionTimeoutMinutes") is not None, "sessions_unavailable")
            self.report["deployment"] = {"mongos_router": hello.get("msg") == "isdbgrid",
                                         "sessions": True}
            self.prepare()
            self.transactions()
            self.records()
            self.retrieval()
            self.report["ok"] = True
        except Exception as error:
            # Driver messages can contain hostnames, credentials or private diagnostics.
            self.report["error"] = {"stage": self.stage, "type": type(error).__name__}
            if type(getattr(error, "code", None)) is int:
                self.report["error"]["code"] = error.code
            if isinstance(error, AssertionError):
                self.report["error"]["check"] = str(error)
        finally:
            self.cleanup()
        self.report["passed"] = len(self.checks)
        emit(self.report)
        return 0 if self.report["ok"] and self.report["cleanup_verified"] else 1

    def prepare(self):
        self.stage = "isolated_namespace_creation"
        require(re.fullmatch(r"research_check_[0-9]+_[0-9a-f]{12}_", self.prefix), "unsafe_prefix")
        names = ("concepts", "versions", "sources", "snapshots", "snapshot_chunks", "leases",
                 "queue", "receipts", "meta", "claim_versions", "source_versions")
        self.expected = {self.prefix + name for name in names}
        present = set(self.store.database.list_collection_names())
        require(not any(name.startswith(self.prefix) for name in present), "namespace_already_exists")
        # Keep an exact creation ledger. Never discover cleanup targets by prefix.
        for name in sorted(self.expected):
            self.store.database.create_collection(name)
            self.created.append(name)
        self.stage = "index_provisioning"
        deadline = time.monotonic() + 120
        for attempt in range(8):
            try:
                result = self.store.provision(wait_seconds=0)
                break
            except OperationFailure as error:
                if error.code != 508:
                    raise
                # Atlas index-management requests can be temporarily throttled.
                # Retain this one exact fixture namespace while retrying it.
                emit({"event": "index_management_retry", "attempt": attempt + 1,
                      "code": 508, "message": index_error_message(error)})
                remaining = deadline - time.monotonic()
                if attempt == 7 or remaining <= 0:
                    raise
                time.sleep(min(10, 2 ** attempt, remaining))
        require(result["prefix"] == self.prefix, "wrong_index_scope")
        self.report["collections_created"] = len(self.created)
        self.passed("isolated_namespaces_and_indexes")

    def transactions(self):
        self.stage = "transaction_commit_and_rollback"
        self.store._tx(lambda session: self.store.meta.insert_one(
            {"_id": "commit-probe", "managed_by": MANAGED_BY}, session=session))
        require(self.store.meta.count_documents({"_id": "commit-probe"}) == 1, "commit_missing")

        class RollbackProbe(RuntimeError):
            pass

        def abort(session):
            self.store.meta.insert_one({"_id": "rollback-probe", "managed_by": MANAGED_BY}, session=session)
            raise RollbackProbe

        expect(RollbackProbe, lambda: self.store._tx(abort))
        require(self.store.meta.count_documents({"_id": "rollback-probe"}) == 0, "rollback_failed")
        self.passed("real_snapshot_majority_commit_and_rollback")

    def records(self):
        self.stage = "synthetic_concepts"
        fixtures = [
            ("Distributed Coordination Systems", "coordination-systems",
             "Coordination protects research work across independent agents and machines.",
             ["distributed coordination"], ["ownership", "concurrency"]),
            ("Fenced Research Leases", "fenced-research-leases",
             "Monotonically increasing fencing tokens prevent stale research workers from saving "
             "changes after another worker takes ownership of a concept.",
             ["Lease fencing"], ["fencing", "stale workers", "ownership"]),
            ("Recoverable Research Journals", "recoverable-research-journals",
             "A journal preserves file preimages and restores earlier projections when publication "
             "fails. Recovery rolls back partially written research outputs.",
             ["Publication recovery"], ["journal", "rollback", "recovery"]),
            ("Culinary Fermentation", "culinary-fermentation",
             "Yeast fermentation converts sugars into carbon dioxide for bread making.",
             ["Bread fermentation"], ["yeast", "bread", "fermentation"]),
        ]
        docs = [self.store.concept_create(name, slug=slug, description=description,
            aliases=aliases, terms=terms, actor="live-check")
            for name, slug, description, aliases, terms in fixtures]
        self.ids = [doc["_id"] for doc in docs]
        self.root, self.child, self.peer, self.unrelated = self.ids
        self.concurrent_leases()
        self.stage = "idempotency_cas_and_fencing"
        self.owner = "live-check-owner"
        bundle = self.store.lease_acquire(self.ids, self.owner, request_id="owned-bundle")
        require(self.store.lease_acquire(self.ids, self.owner, request_id="owned-bundle") == bundle,
                "lease_replay_changed")
        delegated = self.store.lease_delegate(self.ids, bundle["tokens"], self.owner,
                                              "live-check-delegate", request_id="delegate")
        self.owner, self.tokens = "live-check-delegate", delegated["tokens"]
        require(all(delegated["fences"][cid] > bundle["fences"][cid] for cid in self.ids),
                "delegation_not_fenced")
        expect(LeaseConflict, lambda: self.store.concept_update(self.child,
            {"description": "stale owner attempted edit"}, self.revision(self.child), bundle["tokens"][self.child]))
        previous = self.store.concept_get(self.child)
        patch = {"description": previous["description"] + " Fences isolate concurrent owners."}
        updated = self.store.concept_update(self.child, patch, previous["revision"],
                                           self.tokens[self.child], request_id="cas-edit")
        require(self.store.concept_update(self.child, patch, previous["revision"],
            self.tokens[self.child], request_id="cas-edit") == updated, "edit_replay_changed")
        expect(Conflict, lambda: self.store.concept_update(self.child, {"description": "stale"},
            previous["revision"], self.tokens[self.child]))
        require(self.store.concept_get(self.child, previous["revision"])["description"]
                == previous["description"], "immutable_revision_changed")
        require(self.revision(self.child) == updated["revision"], "failed_cas_changed_revision")
        self.passed("idempotent_requests_cas_and_delegated_fences")
        self.graph()
        self.sources_and_claims()
        self.late_keyword_fixture()
        self.queue_and_capabilities()
        self.store.lease_release(self.ids, self.tokens, self.owner)
        self.passed("owned_bundle_release")

    def revision(self, cid):
        return self.store.concept_get(cid)["revision"]

    def concurrent_leases(self):
        self.stage = "simultaneous_lease_acquisition"
        ready = threading.Barrier(2)

        def acquire(owner):
            ready.wait(timeout=10)
            try:
                return self.store.lease_acquire([self.child], owner)
            except LeaseConflict:
                return None

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(acquire, owner) for owner in ("live-race-a", "live-race-b")]
            results = [future.result(timeout=60) for future in futures]
        winners = [result for result in results if result is not None]
        require(len(winners) == 1, "simultaneous_acquisition_not_single_winner")
        winner = winners[0]
        self.store.lease_release([self.child], winner["tokens"], winner["leases"][0]["owner"])
        self.passed("simultaneous_leases_exactly_one_winner")

    def relation(self, cid, tid, relation, action):
        return self.store.relation_mutate(cid, tid, relation, action,
            {key: self.revision(key) for key in self.ids}, self.tokens, actor="live-check")

    def graph(self):
        self.stage = "reciprocal_family_and_cycle_rollback"
        self.relation(self.child, self.root, "parent", "add")
        self.relation(self.peer, self.root, "parent", "add")
        self.relation(self.child, self.peer, "related", "add")
        self.relation(self.child, self.peer, "prerequisite", "add")
        require(self.store.concept_get(self.child)["parent_id"] == self.root, "parent_missing")
        require(self.child in self.store.concept_get(self.root)["children_ids"], "child_backlink_missing")
        require(self.child in self.store.concept_get(self.peer)["related_ids"], "related_backlink_missing")
        require(self.child in self.store.concept_get(self.peer)["dependent_ids"], "dependency_backlink_missing")
        before = {key: self.store.concept_get(key) for key in self.ids}
        versions = self.store.versions.count_documents({})
        graph_revision = self.store.status()["graph_revision"]
        expect(Conflict, lambda: self.relation(self.root, self.child, "parent", "add"))
        require(before == {key: self.store.concept_get(key) for key in self.ids}, "cycle_left_partial_edge")
        require(self.store.versions.count_documents({}) == versions, "cycle_left_partial_revision")
        require(self.store.status()["graph_revision"] == graph_revision, "cycle_serialization_not_rolled_back")
        self.passed("reciprocal_graph_and_cycle_transaction_rollback")

    def sources_and_claims(self):
        self.stage = "unicode_snapshot_and_claim_lineage"
        body = "Fencing tokens isolate research owners.\nUnicode 🐘 preserves complete evidence spans.\n"
        source = self.store.source_put("HTTPS://Example.invalid/research/?utm_source=live#evidence", body,
            metadata={"fetched_at": datetime.now(UTC).isoformat(), "tier": "docs"}, actor="live-check")
        quote = "Unicode 🐘 preserves complete evidence spans."
        start = body.index(quote)
        claim = {"text": quote, "sources": [source["url"]], "confidence": "high",
                 "evidence": [{"url": source["url"], "source_id": source["_id"],
                    "snapshot_sha256": source["snapshot_sha256"], "start": start,
                    "end": start + len(quote), "quote": quote, "extraction_status": "complete"}]}
        added = self.store.claim_mutate(self.child, "add", claim, expected_revision=self.revision(self.child),
                                       lease_token=self.tokens[self.child])
        lineage, original_id = added["claim"]["lineage_id"], added["claim"]["claim_id"]
        changed = self.store.claim_mutate(self.child, "update", {"confidence": "medium"}, lineage,
            self.revision(self.child), self.tokens[self.child])
        require(changed["claim"]["lineage_id"] == lineage, "lineage_changed")
        require(changed["claim"]["claim_id"] != original_id, "claim_identity_not_versioned")
        before = self.revision(self.child)
        invalid = {**claim, "evidence": [{**claim["evidence"][0], "quote": "wrong span"}]}
        expect(ValueError, lambda: self.store.claim_mutate(self.child, "add", invalid,
            expected_revision=before, lease_token=self.tokens[self.child]))
        require(self.revision(self.child) == before, "invalid_evidence_changed_revision")
        current = self.store.source_put(source["url"], body + "New snapshot metadata.\n",
                                        expected_revision=source["revision"], actor="live-check")
        require(self.store.source_get(source["_id"], source["snapshot_sha256"])["text"] == body,
                "historical_snapshot_changed")
        lookup = self.store.source_lookup(source["url"])
        require(lookup["snapshot_available"] and lookup["source"]["snapshot_sha256"]
                == current["snapshot_sha256"], "source_lookup_not_current")
        self.stage = "source_links_and_completion_boundary"
        self.store.source_link(self.child, "add", {"source_id": source["_id"],
            "snapshot_sha256": source["snapshot_sha256"]}, self.revision(self.child), self.tokens[self.child])
        expect(ValueError, lambda: self.store.complete(self.child, self.revision(self.child),
            self.tokens[self.child], {"status": "SUPPORTED"}))
        require(self.store.concept_get(self.child)["completion"]["status"] == "unverified",
                "caller_completed_without_verifier")
        self.passed("unicode_evidence_immutable_snapshots_and_claim_versions")
        self.passed("caller_cannot_self_certify_completion")

    def late_keyword_fixture(self):
        self.stage = "bounded_semantic_coverage_full_keyword_fixture"
        self.late_marker = "VoyageLateKeywordSkink2026"
        for claim in ("Synthetic padding. " * 1600,
                      self.late_marker + " is a synthetic late claim marker."):
            self.store.claim_mutate(self.root, "add", {"text": claim},
                expected_revision=self.revision(self.root), lease_token=self.tokens[self.root])
        current = self.store.concept_get(self.root)
        require(current.get("search_text_truncated") is True, "semantic_coverage_not_marked")
        require(self.late_marker not in current["search_text"], "late_marker_not_beyond_budget")
        require(any(self.late_marker in claim["text"] for claim in current["claims"]),
                "late_claim_not_preserved_for_keyword")
        self.passed("bounded_semantic_projection_preserves_full_late_claim")

    def queue_and_capabilities(self):
        self.stage = "queue_holds_explicit_recovery_and_read_capability"
        for action in ("hold", "stop"):
            row = self.store.queue_put(self.peer, action, expected_revision=self.revision(self.peer),
                                       lease_token=self.tokens[self.peer])
            self.store.lease_renew([self.peer], self.tokens, self.owner)
            self.store.lease_release([self.peer], self.tokens, self.owner)
            expect(LeaseConflict, lambda: self.store.lease_acquire([self.peer], self.owner))
            self.store.queue_recover(self.peer, row["revision"], "Synthetic check explicit recovery",
                                     actor="local-live-check")
            acquired = self.store.lease_acquire([self.peer], self.owner)
            self.tokens[self.peer] = acquired["tokens"][self.peer]
        self.store.concept_update(self.peer, {"cvs_axes": {"relevance": 4, "usefulness": 4,
            "novelty": 4, "interest": 4, "viability": 4}}, self.revision(self.peer), self.tokens[self.peer])
        queries = LibraryQueries(self.store)
        scored, unscored = queries.frontier(scored="scored"), queries.frontier(scored="unscored")
        require(self.peer in {row["id"] for row in scored["items"]}, "scored_frontier_missing")
        require(self.root in {row["id"] for row in unscored["items"]}, "unscored_frontier_missing")
        require(len(queries.incomplete()["items"]) == len(self.ids), "incomplete_inventory_missing")
        seeds = queries.peer_seeds(self.peer)
        require(self.child in {row["id"] for row in seeds["peers"]}, "peer_seed_missing")
        require(seeds["source_candidates"] and not seeds["verified_claims_inherited"],
                "peer_seed_inherited_qualification")
        service = Service(store=self.store, queries=queries, config={}, bridge={})
        before = self.store.status()["counts"]["concepts"]
        expect(PermissionError, lambda: service.dispatch("concept_create", {"name": "Not authorized"}, role="read"))
        expect(ValueError, lambda: service.dispatch("concept_list", {"filters": {"$where": "unsafe"}}, role="read"))
        require(self.store.status()["counts"]["concepts"] == before, "denied_read_capability_wrote")
        self.passed("queue_hold_stop_recovery_and_frontier_accounting")
        self.passed("peer_seed_provenance_and_read_capability_rejection")

    def retrieval(self):
        self.stage = "native_indexes_ready"
        deadline, last_progress = time.monotonic() + self.wait_seconds, 0
        wanted = {TEXT_INDEX, VECTOR_INDEX}
        while True:
            rows = list(self.store.concepts.list_search_indexes())
            safe = [{key: row[key] for key in ("name", "status", "queryable", "type") if key in row}
                    for row in rows if row.get("name") in wanted]
            require(not any(row.get("status") == "FAILED" for row in safe), "native_index_failed")
            ready = {row["name"] for row in safe if row.get("status") == "READY" and row.get("queryable")}
            if wanted <= ready:
                self.report["indexes"] = safe
                break
            require(time.monotonic() < deadline, "native_index_ready_timeout")
            if time.monotonic() - last_progress >= 5:
                emit({"event": "waiting_for_native_indexes", "ready": len(ready), "wanted": len(wanted)})
                last_progress = time.monotonic()
            time.sleep(2)
        self.passed("native_voyage4_and_keyword_indexes_ready")
        self.stage = "native_hybrid_semantic_keyword_retrieval"
        queries = LibraryQueries(self.store)
        paraphrase = "prevent outdated workers from saving changes after another worker takes ownership"
        # A READY index can still be catching up with the latest transaction.
        last_progress = 0
        while True:
            keyword = queries.search("fencing", mode="keyword", top=4)
            semantic = queries.search(paraphrase, mode="semantic", top=4)
            late = queries.search(self.late_marker, mode="keyword", top=4)
            channels = keyword["diagnostics"]["channels"]
            if (channels.get("keyword", {}).get("atlas") is True and not keyword["degraded"]
                    and self.child in {row["id"] for row in keyword["hits"]}
                    and semantic["semantic"] and not semantic["degraded"]
                    and self.child in {row["id"] for row in semantic["hits"]}
                    and late["diagnostics"]["channels"].get("keyword", {}).get("atlas") is True
                    and not late["degraded"] and self.root in {row["id"] for row in late["hits"]}):
                break
            require(time.monotonic() < deadline, "native_retrieval_catchup_timeout")
            if time.monotonic() - last_progress >= 5:
                emit({"event": "waiting_for_native_retrieval", "keyword_hits": len(keyword["hits"]),
                      "semantic_hits": len(semantic["hits"]), "semantic_available": semantic["semantic"],
                      "late_claim_keyword_hits": len(late["hits"])})
                last_progress = time.monotonic()
            time.sleep(2)
        hybrid = queries.search("fencing research ownership", mode="hybrid", top=4)
        require(hybrid["semantic"] and not hybrid["degraded"], "hybrid_degraded")
        require(hybrid["diagnostics"]["channels"]["keyword"].get("atlas") is True, "keyword_fallback_used")
        narrow = queries.search(paraphrase, mode="semantic", topic_id=self.root, breadth="narrow", top=4)
        require(narrow["semantic"] and not narrow["degraded"], "narrow_semantic_degraded")
        require(self.child in {row["id"] for row in narrow["hits"]}, "narrow_semantic_missing")
        require(all(row["id"] in {self.root, self.child, self.peer} for row in narrow["hits"]),
                "narrow_semantic_scope_leaked")
        exact = queries.search(paraphrase, mode="hybrid", scope_ids=[self.child], top=4)
        require(exact["semantic"] and not exact["degraded"], "explicit_scope_degraded")
        require([row["id"] for row in exact["hits"]] == [self.child], "explicit_scope_leaked")
        broad_food = queries.search("fermentation", mode="keyword", top=4)
        narrow_food = queries.search("fermentation", mode="keyword", topic_id=self.root, breadth="narrow", top=4)
        require(self.unrelated in {row["id"] for row in broad_food["hits"]}, "broad_keyword_missing")
        require(not narrow_food["hits"] and not narrow_food["degraded"], "narrow_keyword_scope_leaked")
        self.report["retrieval"] = {"keyword_hits": len(keyword["hits"]),
            "semantic_hits": len(semantic["hits"]), "hybrid_hits": len(hybrid["hits"]),
            "narrow_semantic_hits": len(narrow["hits"]), "explicit_scope_hits": len(exact["hits"]),
            "native_auto_embedding": True, "fallback_used": False,
            "late_claim_keyword_hits": len(late["hits"]), "semantic_projection_truncated": True}
        self.passed("native_semantic_keyword_hybrid_broad_narrow_and_explicit_scope")
        self.passed("native_keyword_recovers_claim_beyond_semantic_byte_budget")
        self.report["counts"] = self.store.status()["counts"]

    def cleanup(self):
        if self.store is None:
            return
        removed, failures = 0, []
        try:
            for name in reversed(self.created):
                require(name in self.expected and name.startswith(self.prefix), "cleanup_ownership_mismatch")
                try:
                    self.store.database.drop_collection(name)
                    removed += 1
                except Exception as error:
                    failures.append(type(error).__name__)
            remaining = set(self.store.database.list_collection_names()) & set(self.created)
            self.report["cleanup_verified"] = not remaining
            self.report["collections_removed"] = removed
            if remaining:
                self.report["cleanup_error"] = {"type": "RemainingOwnedCollections", "count": len(remaining),
                                                "drop_error_types": failures}
        except Exception as error:
            self.report["cleanup_error"] = {"type": type(error).__name__, "removed": removed}
        finally:
            self.store.database.client.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", required=True, help="Owner-local environment file; never printed")
    parser.add_argument("--wait", type=int, default=600, help="Native index/retrieval readiness deadline")
    options = parser.parse_args(argv)
    if not 1 <= options.wait <= 900:
        parser.error("--wait must be 1..900 seconds")
    try:
        load_environment(options.env_file)
    except Exception as error:
        emit({"ok": False, "error": {"stage": "environment", "type": type(error).__name__}})
        return 1
    return LiveCheck(options.wait).run()


if __name__ == "__main__":
    raise SystemExit(main())
