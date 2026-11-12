"""Bounded discovery over the MongoDB working research library.

Search results and peer packets are discovery leads. Neither index presence nor
an inherited qualification grants new factual evidence to another concept.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import math
import re
import time
import unicodedata
from collections import Counter, deque
from datetime import UTC, datetime, timedelta

MANAGED_BY = "research-library/v1"
MODEL = "voyage-4"
VECTOR_INDEX = "research_library_voyage4_v1"
TEXT_INDEX = "research_library_text_v1"
MAX_INVENTORY = 100_000
MAX_SCOPE = 10_000
MAX_PEER_BYTES = 512 * 1024
VECTOR_DEFINITION = {"fields": [
    {"type": "autoEmbed", "modality": "text", "path": "search_text", "model": MODEL},
    {"type": "filter", "path": "managed_by"},
    {"type": "filter", "path": "active"},
    {"type": "filter", "path": "slug"},
]}
TEXT_DEFINITION = {"mappings": {"dynamic": False, "fields": {
    "name": {"type": "string"},
    "aliases": {"type": "string"},
    "terms": {"type": "string"},
    "description": {"type": "string"},
    "search_text": {"type": "string"},
    "managed_by": {"type": "token"},
    "active": {"type": "boolean"},
    "slug": {"type": "token"},
}}}
_GRAPH_FIELDS = {
    key: 1 for key in (
        "_id", "slug", "name", "aliases", "terms", "description", "revision", "state",
        "active", "deleted", "parent_id", "children_ids", "related_ids", "adjacent_ids",
        "prerequisite_ids", "dependent_ids", "cvs", "cvs_axes", "cvs_decision",
        "cvs_rationale", "incomplete_reasons", "completion", "source_refs", "metadata",
        "managed_by", "updated_at",
    )
}


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), default=_json_default).encode()


def _json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError("Unsupported metadata value")


def _digest(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _terms(value):
    return set(re.findall(r"[^\W_]+", unicodedata.normalize("NFKC", value).casefold()))


def _strings(value):
    return [x for x in value if isinstance(x, str)] if isinstance(value, list) else []


def _live(doc):
    return (doc.get("managed_by") == MANAGED_BY and doc.get("active") is not False
            and not doc.get("deleted") and doc.get("state") != "archived")


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be {low}..{high}")
    return value


def _axis_values(value):
    if not isinstance(value, dict):
        return None
    aliases = {"relevance": ("relevance", "rel"), "usefulness": ("usefulness", "use"),
               "novelty": ("novelty", "nov"), "interest": ("interest", "int"),
               "viability": ("viability", "via")}
    folded = {str(key).casefold(): item for key, item in value.items()}
    result = {}
    for key, names in aliases.items():
        item = next((folded[name] for name in names if name in folded), None)
        if (isinstance(item, bool) or not isinstance(item, (int, float))
                or not math.isfinite(item) or not 0 <= item <= 5):
            return None
        result[key] = float(item)
    return result


def _summary(doc):
    keys = ("slug", "name", "aliases", "terms", "revision", "state", "cvs", "cvs_axes",
            "cvs_decision", "cvs_rationale", "incomplete_reasons", "completion", "source_refs")
    value = {key: copy.deepcopy(doc[key]) for key in keys if key in doc}
    value.update(id=doc["_id"], concept_id=doc["_id"], candidate_only=True)
    value["description"] = str(doc.get("description", ""))[:1200]
    value["qualification"] = (doc.get("completion") or {}).get("status", "unreviewed")
    return value


def _page(rows, after, limit, scope):
    """Bind continuation to scope and selected row revisions, not offsets."""
    _integer(limit, 1, 200, "limit")
    if not isinstance(after, str) or len(after) > 4000:
        raise ValueError("Invalid continuation cursor")
    rows = sorted(rows, key=lambda row: row["id"])
    census = _digest(rows)
    scope_hash = _digest(scope)
    last = ""
    if after:
        try:
            if not after.startswith("pg1:"):
                raise ValueError
            raw = base64.urlsafe_b64decode(after[4:] + "=" * (-len(after[4:]) % 4))
            cursor = json.loads(raw)
            if cursor["scope"] != scope_hash or cursor["census"] != census:
                raise ValueError("PAGINATION_CONFLICT: inventory changed; restart enumeration")
            last = cursor["last"]
            if not isinstance(last, str):
                raise ValueError
        except (KeyError, TypeError, json.JSONDecodeError, UnicodeError) as exc:
            raise ValueError("Invalid continuation cursor") from exc
    remaining = [row for row in rows if row["id"] > last]
    selected = remaining[:limit]
    more = len(remaining) > limit
    next_cursor = ""
    if more:
        payload = {"scope": scope_hash, "census": census, "last": selected[-1]["id"]}
        next_cursor = "pg1:" + base64.urlsafe_b64encode(_canonical(payload)).decode().rstrip("=")
    return {"items": selected, "total": len(rows), "has_more": more,
            "next_after": next_cursor, "next_cursor": next_cursor,
            "census_sha256": census, "scope": scope, "complete_page": not more}


def provision_search_indexes(store, wait_seconds=0):
    """Provision only this subsystem's named native indexes."""
    _integer(wait_seconds, 0, 600, "wait_seconds")
    from pymongo.operations import SearchIndexModel

    wanted = {
        VECTOR_INDEX: ("vectorSearch", VECTOR_DEFINITION),
        TEXT_INDEX: ("search", TEXT_DEFINITION),
    }
    existing = {row["name"]: row for row in store.concepts.list_search_indexes()}
    changes = []
    for name, (kind, definition) in wanted.items():
        if name not in existing:
            store.concepts.create_search_index(SearchIndexModel(
                name=name, type=kind, definition=definition))
            changes.append({"name": name, "action": "created"})
        else:
            current = existing[name].get("latestDefinition", existing[name].get("definition"))
            if current is not None and current != definition:
                store.concepts.update_search_index(name, definition)
                changes.append({"name": name, "action": "updated"})
    deadline = time.monotonic() + wait_seconds
    while True:
        indexes = [{key: row[key] for key in ("name", "type", "status", "queryable")
                    if key in row} for row in store.concepts.list_search_indexes()
                   if row.get("name") in wanted]
        ready = {row["name"] for row in indexes
                 if row.get("queryable") is True and row.get("status") == "READY"}
        if set(wanted) <= ready or time.monotonic() >= deadline:
            return {"changes": changes, "indexes": indexes,
                    "ready": set(wanted) <= ready, "model": MODEL,
                    "embedding_scope": "new managed research concept text only"}
        time.sleep(min(1, max(0, deadline - time.monotonic())))


class LibraryQueries:
    def __init__(self, store):
        self.store = store
        self.collection = store.concepts

    def _inventory(self):
        rows = list(self.collection.find(
            {"managed_by": MANAGED_BY}, _GRAPH_FIELDS).limit(MAX_INVENTORY + 1))
        if len(rows) > MAX_INVENTORY:
            raise ValueError("Inventory exceeds request safety bound; use an operator export")
        return {row["_id"]: row for row in rows if _live(row)}

    @staticmethod
    def _children(inventory, concept_id):
        result = set(_strings(inventory[concept_id].get("children_ids")))
        result.update(row["_id"] for row in inventory.values()
                      if row.get("parent_id") == concept_id)
        return result & inventory.keys()

    def _descendants(self, inventory, concept_id):
        if concept_id not in inventory:
            raise KeyError("No such active concept")
        seen, todo = set(), [concept_id]
        while todo:
            current = todo.pop()
            if current in seen:
                continue
            seen.add(current)
            todo.extend(self._children(inventory, current) - seen)
        return seen

    def _scope(self, inventory, topic_id="", scope_ids=None, breadth="broad"):
        if breadth not in {"broad", "narrow"}:
            raise ValueError("breadth must be broad or narrow")
        if not isinstance(topic_id, str) or len(topic_id) > 250:
            raise ValueError("Invalid topic identity")
        if scope_ids is not None:
            if (not isinstance(scope_ids, list) or len(scope_ids) > MAX_SCOPE
                    or any(not isinstance(x, str) or len(x) > 250 for x in scope_ids)):
                raise ValueError("scope_ids must be a bounded list of concept IDs")
            missing = set(scope_ids) - inventory.keys()
            if missing:
                raise KeyError("A scope concept is missing or inactive")
            selected = set(scope_ids)
        elif breadth == "narrow":
            if not topic_id:
                raise ValueError("A narrow search requires topic_id or explicit scope_ids")
            selected = self._descendants(inventory, topic_id)
        else:
            if topic_id and topic_id not in inventory:
                raise KeyError("No such active topic")
            selected = set(inventory)
        if breadth == "narrow" or scope_ids is not None:
            if len(selected) > MAX_SCOPE:
                raise ValueError("Narrow scope exceeds safety bound; select a smaller subtopic")
        return selected

    def search(self, query, mode="hybrid", scope_ids=None, topic_id="", breadth="broad", top=10):
        if not isinstance(query, str) or not 1 <= len(query.strip()) <= 2000:
            raise ValueError("query must contain 1..2000 characters")
        if mode not in {"hybrid", "semantic", "keyword", "lexical"}:
            raise ValueError("mode must be hybrid, semantic or keyword")
        _integer(top, 1, 20, "top")
        mode = "keyword" if mode == "lexical" else mode
        inventory = self._inventory()
        selected = self._scope(inventory, topic_id, scope_ids, breadth)
        scoped = scope_ids is not None or breadth == "narrow"
        response_scope = {"breadth": breadth, "topic_id": topic_id or None,
                          "explicit_ids": scope_ids, "concept_count": len(selected),
                          "descendants_included": breadth == "narrow" and scope_ids is None}
        if not selected:
            return {"hits": [], "mode": mode, "semantic": False, "degraded": False,
                    "diagnostics": {"channels": {}, "scope": response_scope},
                    "candidate_only": True}
        eligible = {"managed_by": MANAGED_BY, "active": True}
        bson = dict(eligible)
        vector_filter = dict(eligible)
        filters = [{"equals": {"path": key, "value": value}} for key, value in eligible.items()]
        if scoped:
            ids = sorted(selected)
            slugs = sorted(inventory[x]["slug"] for x in selected)
            bson["_id"] = {"$in": ids}
            vector_filter["slug"] = {"$in": slugs}
            filters.append({"in": {"path": "slug", "value": slugs}})
        folded = unicodedata.normalize("NFKC", query.strip()).casefold()
        exact = [row for row in inventory.values() if row["_id"] in selected and
                 folded in {unicodedata.normalize("NFKC", value).casefold()
                            for value in [row["_id"], row.get("slug", ""), row.get("name", ""),
                                          *_strings(row.get("aliases"))]}]
        channels = {"exact": {"ok": True, "count": len(exact)}}
        batches = [("exact", exact)]
        cap = min(100, max(20, 5 * top))
        native_failed = False
        if mode != "keyword":
            pipeline = [{"$vectorSearch": {"index": VECTOR_INDEX, "path": "search_text",
                         "query": {"text": query}, "model": MODEL, "limit": cap,
                         "numCandidates": 20 * cap, "filter": vector_filter}},
                        {"$match": bson}, {"$set": {"score": {"$meta": "vectorSearchScore"}}}]
            try:
                rows = list(self.collection.aggregate(pipeline, maxTimeMS=15000))
                batches.append(("semantic", rows))
                channels["semantic"] = {"ok": True, "count": len(rows), "model": MODEL,
                                        "native_auto_embedding": True}
            except Exception as exc:
                native_failed = True
                channels["semantic"] = {"ok": False, "error_type": type(exc).__name__}
        if mode != "semantic":
            should = [{"text": {"query": query, "path": field,
                                "score": {"boost": {"value": weight}}}}
                      for field, weight in (("name", 6), ("aliases", 5), ("terms", 4),
                                            ("description", 3), ("search_text", 1))]
            pipeline = [{"$search": {"index": TEXT_INDEX, "compound": {
                "filter": filters, "should": should, "minimumShouldMatch": 1}}},
                {"$match": bson}, {"$limit": cap},
                {"$set": {"score": {"$meta": "searchScore"}}}]
            try:
                rows = list(self.collection.aggregate(pipeline, maxTimeMS=15000))
                channels["keyword"] = {"ok": True, "atlas": True, "count": len(rows)}
            except Exception as exc:
                native_failed = True
                rows = self._keyword_fallback(query, selected, cap)
                channels["keyword"] = {"ok": True, "atlas": False, "fallback": True,
                                       "count": len(rows), "error_type": type(exc).__name__}
            batches.append(("keyword", rows))
        merged = {}
        for channel, rows in batches:
            for rank, row in enumerate(rows, 1):
                concept_id = row.get("_id")
                if concept_id not in selected or not _live(row):
                    continue
                # Native indexes are asynchronous. Re-read authoritative state;
                # do not trust a cached/indexed eligibility bit or revision.
                current = self.collection.find_one({"_id": concept_id, "managed_by": MANAGED_BY})
                if current is None or not _live(current):
                    continue
                hit = merged.setdefault(concept_id, {"doc": current, "score": 0.0, "channels": {}})
                weight = 1.2 if channel == "semantic" else 1.0
                hit["score"] += weight / (60 + rank)
                if channel == "exact":
                    hit["score"] += 1
                hit["channels"][channel] = {"rank": rank, "score": row.get("score")}
        query_terms = _terms(query)
        for hit in merged.values():
            doc = hit["doc"]
            positive = _terms(" ".join([str(doc.get("name", "")), str(doc.get("description", "")),
                                        *_strings(doc.get("aliases")), *_strings(doc.get("terms"))]))
            hit["intent_overlap"] = len(query_terms & positive)
            hit["score"] += 0.04 * len(query_terms & positive) / max(1, len(query_terms))
        ranked = sorted(merged.values(), key=lambda hit: (-hit["score"], hit["doc"]["_id"]))
        hits = [{**_summary(hit["doc"]), "score": round(hit["score"], 8),
                 "channels": hit["channels"], "intent_overlap": hit["intent_overlap"]}
                for hit in ranked[:top]]
        return {"hits": hits, "mode": mode,
                "semantic": channels.get("semantic", {}).get("ok", False),
                "degraded": native_failed,
                "diagnostics": {"channels": channels, "scope": response_scope,
                                "per_channel_candidate_limit": cap,
                                "ranked_result_limit": top,
                                "enumeration": False},
                "candidate_only": True}

    def _keyword_fallback(self, query, selected, cap):
        terms = _terms(query)
        rows = []
        projection = {**_GRAPH_FIELDS, "search_text": 1}
        for doc in self.collection.find({"managed_by": MANAGED_BY, "_id": {"$in": sorted(selected)}},
                                        projection):
            if not _live(doc):
                continue
            counts = Counter(re.findall(r"[^\W_]+", unicodedata.normalize(
                "NFKC", " ".join([str(doc.get("name", "")), str(doc.get("description", "")),
                                  str(doc.get("search_text", "")),
                                  *_strings(doc.get("aliases")), *_strings(doc.get("terms"))])
            ).casefold()))
            score = sum(1 + math.log(counts[term]) for term in terms if counts[term])
            if score:
                rows.append({**doc, "score": score})
        return sorted(rows, key=lambda row: (-row["score"], row["_id"]))[:cap]

    def related(self, concept_id, depth=2, after="", limit=100):
        _integer(depth, 0, 20, "depth")
        inventory = self._inventory()
        if concept_id not in inventory:
            raise KeyError("No such active concept")
        found = {concept_id: {"depth": 0, "via": ["self"]}}
        todo = deque([concept_id])
        while todo:
            current = todo.popleft()
            distance = found[current]["depth"]
            if distance >= depth:
                continue
            doc = inventory[current]
            edges = []
            if doc.get("parent_id") in inventory:
                edges.append((doc["parent_id"], "parent"))
            edges.extend((x, "child") for x in self._children(inventory, current))
            for field, kind in (("related_ids", "related"), ("adjacent_ids", "adjacent"),
                                ("prerequisite_ids", "prerequisite"),
                                ("dependent_ids", "dependent")):
                edges.extend((x, kind) for x in _strings(doc.get(field)) if x in inventory)
            parent = doc.get("parent_id")
            if parent in inventory:
                edges.extend((x, "sibling") for x in self._children(inventory, parent) - {current})
            for target, kind in sorted(edges):
                if target not in found:
                    found[target] = {"depth": distance + 1, "via": [kind]}
                    todo.append(target)
                elif found[target]["depth"] == distance + 1:
                    found[target]["via"] = sorted(set(found[target]["via"]) | {kind})
        rows = [{**_summary(inventory[cid]), **navigation}
                for cid, navigation in found.items()]
        result = _page(rows, after, limit, {"operation": "related", "topic_id": concept_id,
                                          "max_depth": depth})
        result["depth_limited"] = any(row["depth"] == depth for row in rows)
        result["neighbors_are_not_factual_support"] = True
        return result

    def _holds(self, inventory=None):
        result = {}
        leases = getattr(self.store, "leases", None)
        if leases is not None:
            for row in leases.find({"managed_by": MANAGED_BY}):
                concept_id = row.get("concept_id", row.get("_id"))
                expires = _instant(row.get("expires_at"))
                if (row.get("status", "held") == "held" and row.get("released") is not True
                        and expires and expires > datetime.now(UTC)):
                    result[concept_id] = {"owner": row.get("owner"), "run_id": row.get("run_id"),
                                          "expires_at": expires.isoformat(), "kind": "lease"}
        queue = getattr(self.store, "queue", None)
        if queue is not None:
            for row in queue.find({"managed_by": MANAGED_BY}):
                if (row.get("stop") or row.get("state", row.get("status")) in {
                        "paused", "held", "stopped", "blocked"}):
                    concept_id = row.get("concept_id", row.get("_id"))
                    result[concept_id] = {"owner": row.get("owner"),
                                          "kind": "stopped" if row.get("stop") else row.get(
                                              "state", row.get("status")),
                                          "continuation": row.get("continuation")}
        provider = getattr(self.store, "reservation_provider", None)
        if provider is not None:
            ids = sorted(inventory or self._inventory())
            held = provider(ids, "library-reader", "")
            if isinstance(held, dict):
                for concept_id, value in held.items():
                    if concept_id not in ids:
                        continue
                    safe = ({key: copy.deepcopy(value[key]) for key in (
                        "owner", "run_id", "status", "paused", "stop", "source",
                        "provenance", "continuation") if key in value}
                        if isinstance(value, dict) else {"owner": str(value)})
                    result[concept_id] = {**safe, "kind": "legacy-reservation"}
        return result

    @staticmethod
    def _score(doc):
        value = doc.get("cvs")
        if (isinstance(value, bool) or not isinstance(value, (float, int))
                or not math.isfinite(value) or not 0 <= value <= 5):
            return None
        return float(value)

    def frontier(self, topic_id="", scored="all", after="", limit=100):
        if scored not in {"all", "scored", "unscored"}:
            raise ValueError("scored must be all, scored or unscored")
        inventory = self._inventory()
        selected = self._descendants(inventory, topic_id) if topic_id else set(inventory)
        holds = self._holds(inventory)
        rows = []
        for concept_id in selected:
            doc = inventory[concept_id]
            metadata = doc.get("metadata") or {}
            coverage = metadata.get("coverage")
            if doc.get("state") not in {"frontier", "draft"} and coverage not in {
                    "frontier", "container-review", "refresh-review"}:
                continue
            value = self._score(doc)
            if (scored == "scored" and value is None) or (scored == "unscored" and value is not None):
                continue
            decision = doc.get("cvs_decision")
            axes = _axis_values(doc.get("cvs_axes"))
            hard_gate = axes is not None and (
                axes["viability"] <= 1 or axes["novelty"] == 0)
            if concept_id in holds:
                eligibility = "held"
            elif value is None:
                eligibility = "needs-scoring"
            elif hard_gate or decision == "SKIP":
                eligibility = "hard-gated-review"
            elif metadata.get("score_only_review") or axes is None or decision not in {
                    "RESEARCH", "REFRESH"}:
                eligibility = "review"
            elif value < 3.2:
                eligibility = "below-threshold"
            else:
                eligibility = "ready"
            rows.append({**_summary(doc), "cvs": value, "eligibility": eligibility,
                         "holder": holds.get(concept_id), "coverage": coverage or "frontier"})
        result = _page(rows, after, limit, {"operation": "frontier", "topic_id": topic_id,
                                          "scored": scored})
        result.update(all_scores_retained=True, score_threshold=3.2,
                      unscored_is_null=True, dispatch_authorized=False)
        return result

    def incomplete(self, topic_id="", after="", limit=100):
        inventory = self._inventory()
        selected = self._descendants(inventory, topic_id) if topic_id else set(inventory)
        holds = self._holds(inventory)
        rows = []
        for concept_id in selected:
            doc = inventory[concept_id]
            reasons = list(_strings(doc.get("incomplete_reasons")))
            completion = doc.get("completion") or {}
            if doc.get("state") != "complete":
                reasons.append("not-completed")
            if completion.get("status") not in {"complete", "verified", "accepted"}:
                reasons.append("missing-current-gate-and-projection-proof")
            if completion.get("stale"):
                reasons.append("stale-gate-binding")
            if concept_id in holds:
                reasons.append("held-or-in-progress")
            if reasons:
                rows.append({**_summary(doc), "incomplete_reasons": sorted(set(reasons)),
                             "holder": holds.get(concept_id)})
        return _page(rows, after, limit, {"operation": "incomplete", "topic_id": topic_id})

    def peer_seeds(self, concept_id, limit=8):
        _integer(limit, 1, 8, "limit")
        inventory = self._inventory()
        if concept_id not in inventory:
            raise KeyError("No such active concept")
        target = inventory[concept_id]
        parent_id = target.get("parent_id")
        peers = set()
        if parent_id in inventory:
            peers |= self._children(inventory, parent_id) - {concept_id}
            peers.add(parent_id)
        peers |= set(_strings(target.get("related_ids")))
        peers |= set(_strings(target.get("adjacent_ids")))
        packets, fresh_sources, candidates = [], [], []
        omitted = 0
        for peer_id in sorted(peers & inventory.keys())[:limit]:
            doc = self.collection.find_one({"_id": peer_id, "managed_by": MANAGED_BY})
            if not doc or not _live(doc):
                continue
            claims = []
            original_versions = (doc.get("metadata") or {}).get("canonical_claim_versions") or []
            if not isinstance(original_versions, list):
                original_versions = []
            for claim in list(doc.get("claims") or [])[:4]:
                if not isinstance(claim, dict):
                    continue
                candidate = {key: copy.deepcopy(claim[key]) for key in (
                    "lineage_id", "claim_id", "version_id", "text", "evidence", "sources",
                    "qualification", "validation_status", "temporal", "conflict")
                    if key in claim}
                text_sha = hashlib.sha256(str(claim.get("text", "")).encode()).hexdigest()
                provenance = [row for row in original_versions if isinstance(row, dict)
                              and row.get("statement_sha256") == text_sha]
                if provenance:
                    candidate["canonical_provenance"] = copy.deepcopy(provenance)
                claims.append(candidate)
            refs = copy.deepcopy(list(doc.get("source_refs") or [])[:16])
            pinned = {(row.get("source_id"), row.get("snapshot_sha256"), row.get("url"))
                      for row in refs if isinstance(row, dict)}
            for claim in claims:
                for span in claim.get("evidence") or []:
                    if not isinstance(span, dict) or not all(span.get(key) for key in (
                            "source_id", "snapshot_sha256", "url")):
                        continue
                    key = (span["source_id"], span["snapshot_sha256"], span["url"])
                    if key not in pinned and len(refs) < 16:
                        refs.append({k: span[k] for k in ("source_id", "snapshot_sha256", "url")})
                        pinned.add(key)
            sources = getattr(self.store, "sources", None)
            current_sources = {}
            if sources is not None:
                ids = sorted({ref.get("source_id") for ref in refs
                              if isinstance(ref, dict) and isinstance(ref.get("source_id"), str)})
                current_sources = {row["_id"]: row for row in sources.find(
                    {"managed_by": MANAGED_BY, "_id": {"$in": ids}, "deleted": {"$ne": True}},
                    {"_id": 1, "url": 1, "snapshot_sha256": 1, "metadata.fetched_at": 1})}
            for ref in refs:
                if not isinstance(ref, dict) or ref.get("fetched_at") or ref.get("retrieved_at"):
                    continue
                source = current_sources.get(ref.get("source_id"), {})
                if (source.get("snapshot_sha256") == ref.get("snapshot_sha256")
                        and source.get("url") == ref.get("url")):
                    stamp = (source.get("metadata") or {}).get("fetched_at")
                    if stamp:
                        ref["fetched_at"] = stamp
            packet = {**_summary(doc), "canonical_wording": doc.get("name"),
                      "vocabulary": _strings(doc.get("terms"))[:64],
                      "aliases": _strings(doc.get("aliases"))[:32],
                      "claim_candidates": claims, "source_candidates": refs,
                      "claim_candidates_truncated": len(doc.get("claims") or []) > 4,
                      "open_questions": copy.deepcopy((doc.get("metadata") or {}).get(
                          "open_questions", []))[:16],
                      "seed_use": "Check relevance and version before citing; revalidate for this concept"}
            if len(_canonical([*packets, packet])) > MAX_PEER_BYTES:
                omitted += 1
                continue
            packets.append(packet)
            for ref in refs:
                if not isinstance(ref, dict):
                    continue
                stamp = _instant(ref.get("fetched_at") or ref.get("retrieved_at"))
                now = datetime.now(UTC)
                entry = {**ref, "peer_id": peer_id, "peer_revision": doc.get("revision"),
                         "freshness": "unknown" if stamp is None or stamp > now + timedelta(
                             minutes=5) else ("fresh" if stamp >= now - timedelta(days=30)
                                              else "stale")}
                candidates.append(entry)
                if entry["freshness"] == "fresh" and len(fresh_sources) < 8:
                    key = (entry.get("source_id"), entry.get("snapshot_sha256"), entry.get("url"))
                    if key not in {(x.get("source_id"), x.get("snapshot_sha256"), x.get("url"))
                                   for x in fresh_sources}:
                        fresh_sources.append(entry)
        return {"concept_id": concept_id, "concept_revision": target.get("revision"),
                "parent_id": parent_id, "peers": packets, "source_candidates": candidates[:64],
                "fresh_source_seeds": fresh_sources, "omitted_oversized_peers": omitted,
                "truncated": len(peers) > limit or bool(omitted),
                "independent_origins_not_multiplied": True,
                "verified_claims_inherited": False,
                "instruction": "Use peer wording and source leads for broad and narrow dedup. "
                               "Read pinned snapshots and independently gate each new concept's claims."}


def _instant(value):
    if isinstance(value, (float, int)) and not isinstance(value, bool):
        try:
            return datetime.fromtimestamp(value, UTC) if math.isfinite(value) else None
        except (ValueError, OverflowError, OSError):
            return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
        except ValueError:
            return None
    return None
