"""Native keyword and semantic discovery over verified, immutable artifact text units."""
from __future__ import annotations

import copy
import re
import time

from .models import MANAGED_BY, Conflict, digest, text
from .queries import MODEL
from .runs import MAX_ARTIFACT_BYTES, _identity

VECTOR_INDEX = "research_artifact_voyage4_v1"
TEXT_INDEX = "research_artifact_text_v1"
UNIT_BYTES = 16000
MAX_ARTIFACTS = 16
MAX_BATCH_BYTES = MAX_ARTIFACT_BYTES
MAX_CENSUS_GROUP = 500
MAX_FALLBACK_UNITS = 1000
MAX_VALIDATION_BYTES = 32 * 1024 * 1024
UNIT_SCHEMA = "research-artifact-unit/v1"
FILTER_FIELDS = ("managed_by", "active", "run_id", "artifact_id", "unit_id")
VECTOR_DEFINITION = {"fields": [
    {"type": "autoEmbed", "modality": "text", "path": "search_text", "model": MODEL},
    *[{"type": "filter", "path": key} for key in FILTER_FIELDS],
]}
TEXT_DEFINITION = {"mappings": {"dynamic": False, "fields": {
    "search_text": {"type": "string"}, "name": {"type": "string"},
    **{key: {"type": "boolean" if key == "active" else "token"} for key in FILTER_FIELDS},
}}}


def _wait(value):
    if type(value) is not int or not 0 <= value <= 30:
        raise ValueError("Artifact index wait must be 0..30 seconds")
    return value


class ArtifactSearch:
    def __init__(self, runstore):
        self.runs, self.store = runstore, runstore.store
        self.collection = self.store.database[self.store.prefix + "artifact_units"]

    def provision(self, wait_seconds=0):
        """Operator-only indexes for new derived units; never mutate old vectors or indexes."""
        _wait(wait_seconds)
        from pymongo.operations import SearchIndexModel

        if self.collection.name not in self.store.database.list_collection_names():
            try:
                self.store.database.create_collection(self.collection.name)
            except Exception:
                if self.collection.name not in self.store.database.list_collection_names():
                    raise
        def marker(session):
            key = "artifact-search/v1"
            if self.runs._claim(self.store.meta, key, session) is None:
                self.store.meta.insert_one({"_id": key, "managed_by": MANAGED_BY,
                    "schema": UNIT_SCHEMA, "model": MODEL}, session=session)
        self.store._tx(marker)
        self.collection.create_index([("managed_by", 1), ("run_id", 1), ("artifact_id", 1)])
        existing = {row["name"]: row for row in self.collection.list_search_indexes()}
        wanted = {VECTOR_INDEX: ("vectorSearch", VECTOR_DEFINITION),
                  TEXT_INDEX: ("search", TEXT_DEFINITION)}
        changes = []
        for name, (kind, definition) in wanted.items():
            if name in existing:
                current = existing[name].get("latestDefinition", existing[name].get("definition"))
                if current != definition or existing[name].get("type", kind) != kind:
                    raise Conflict("Artifact search index definition is not owned by this schema")
            else:
                self.collection.create_search_index(SearchIndexModel(
                    name=name, type=kind, definition=copy.deepcopy(definition)))
                changes.append({"name": name, "action": "created"})
        deadline = time.monotonic() + wait_seconds
        while True:
            rows = [{key: row[key] for key in ("name", "type", "status", "queryable") if key in row}
                    for row in self.collection.list_search_indexes() if row.get("name") in wanted]
            ready = {row["name"] for row in rows
                     if row.get("queryable") is True and row.get("status") == "READY"}
            if set(wanted) <= ready or time.monotonic() >= deadline:
                return {"changes": changes, "indexes": rows, "ready": set(wanted) <= ready,
                        "coverage_verified": False, "model": MODEL,
                        "embedding_scope": "new immutable artifact units only"}
            time.sleep(min(1, max(0, deadline - time.monotonic())))

    @staticmethod
    def _ids(values):
        if not isinstance(values, list) or not 1 <= len(values) <= MAX_ARTIFACTS:
            raise ValueError("Require 1..16 artifact identities")
        return sorted({_identity(value, "art:") for value in values})

    @staticmethod
    def _units(manifest, body):
        units, start, byte_start = [], 0, 0
        # Characters never split between units. UTF-8 size, not character count, bounds each unit.
        while start < len(body):
            candidate = body[start:start + UNIT_BYTES]
            raw = candidate.encode("utf-8")
            if len(raw) > UNIT_BYTES:
                candidate = raw[:UNIT_BYTES].decode("utf-8", "ignore")
                raw = candidate.encode("utf-8")
            index = len(units)
            sha = digest(raw)
            uid = "unit:" + digest([UNIT_SCHEMA, MODEL, manifest["_id"], index, sha])
            units.append({"_id": uid, "unit_id": uid, "managed_by": MANAGED_BY,
                "schema": UNIT_SCHEMA, "model": MODEL, "active": True,
                "run_id": manifest["run_id"], "artifact_id": manifest["_id"],
                "name": manifest["name"], "kind": manifest["kind"], "unit_index": index,
                "char_offset": start, "char_count": len(candidate), "byte_offset": byte_start,
                "byte_count": len(raw), "unit_utf8_sha256": sha,
                "body_utf8_sha256": manifest["body_utf8_sha256"], "search_text": candidate})
            start += len(candidate)
            byte_start += len(raw)
        return units

    def _prepare(self, ids, session, run_id=""):
        units, total = [], 0
        for aid in ids:
            manifest, body = self.runs._artifact_text(aid, session=session)
            if run_id and manifest["run_id"] != run_id:
                raise ValueError("Artifact does not belong to the selected run")
            self.runs._get(manifest["run_id"], session)
            total += manifest["byte_count"]
            if total > MAX_BATCH_BYTES:
                raise ValueError("Artifact index batch exceeds its UTF-8 byte limit")
            units.extend(self._units(manifest, body))
        return units

    def _insert(self, units, session):
        for unit in units:
            old = self.runs._claim(self.collection, unit["_id"], session)
            if old is None:
                self.collection.insert_one(unit, session=session)
            elif old != unit:
                raise Conflict("Immutable artifact search unit checksum mismatch")

    def index_artifacts(self, artifact_ids, wait_seconds=0):
        """In-process indexing from verified Mongo bodies, without accepting caller text."""
        ids, wait_seconds = self._ids(artifact_ids), _wait(wait_seconds)
        def change(session):
            units = self._prepare(ids, session)
            self._insert(units, session)
            return {"artifact_ids": ids, "unit_ids": [row["unit_id"] for row in units]}
        result = self.store._tx(change)
        return {**result, "coverage": self._coverage(result["unit_ids"], wait_seconds)}

    def artifact_index(self, run_id, artifact_ids, expected_revision, lease_token, owner,
                       request_id="", actor="agent"):
        rid, ids = _identity(run_id, "run:"), self._ids(artifact_ids)
        owner = text(owner, "run owner", 200)
        def change(session):
            old = self.runs._edit(rid, expected_revision, lease_token, owner, session)
            units = self._prepare(ids, session, run_id=rid)
            self._insert(units, session)
            return {"run": self.runs._save(old, old, actor, session), "artifact_ids": ids,
                    "unit_ids": [row["unit_id"] for row in units]}
        result = self.store._mutate("artifact_index", self.runs._fenced_payload(lease_token,
            run_id=rid, artifact_ids=ids, expected_revision=expected_revision, owner=owner),
            actor, request_id, change)
        # Retry the same request ID to refresh native coverage without repeating the write.
        return {**result, "coverage": self._coverage(result["unit_ids"])}

    def _coverage(self, unit_ids, wait_seconds=0):
        """Count exact identities from both native indexes; READY is not a coverage claim."""
        expected = set(unit_ids)
        groups = [sorted(expected)[start:start + MAX_CENSUS_GROUP]
                  for start in range(0, len(expected), MAX_CENSUS_GROUP)]
        deadline = time.monotonic() + _wait(wait_seconds)
        while True:
            channels = {}
            for channel in ("keyword", "semantic"):
                seen, returned, errors = set(), 0, []
                for group in groups:
                    bson = {"managed_by": MANAGED_BY, "active": True, "unit_id": {"$in": group}}
                    if channel == "keyword":
                        stage = {"$search": {"index": TEXT_INDEX, "compound": {"filter": [
                            {"equals": {"path": "managed_by", "value": MANAGED_BY}},
                            {"equals": {"path": "active", "value": True}},
                            {"in": {"path": "unit_id", "value": group}},
                        ]}}}
                    else:
                        stage = {"$vectorSearch": {"index": VECTOR_INDEX, "path": "search_text",
                            "query": {"text": "research artifact index coverage"}, "model": MODEL,
                            "exact": True, "limit": len(group), "filter": bson}}
                    try:
                        rows = list(self.collection.aggregate([stage, {"$match": bson},
                            {"$limit": len(group)}, {"$project": {"_id": 1, "unit_id": 1}}],
                            maxTimeMS=5000))
                        returned += len(rows)
                        seen.update(row.get("unit_id") for row in rows)
                    except Exception as exc:
                        errors.append(type(exc).__name__)
                channels[channel] = {"complete": not errors and seen == expected
                    and returned == len(expected), "expected_count": len(expected),
                    "returned_count": returned, "matched_count": len(seen & expected),
                    "missing_unit_ids": sorted(expected - seen),
                    "unexpected_unit_ids": sorted(str(value) for value in seen - expected),
                    "errors": errors}
            complete = all(row["complete"] for row in channels.values())
            if complete or time.monotonic() >= deadline:
                return {"complete": complete, "model": MODEL,
                        "expected_count": len(expected), "expected_unit_ids": sorted(expected),
                        "unit_census_sha256": digest(sorted(expected)), "channels": channels,
                        "partial": not complete, "retry_without_research": not complete}
            time.sleep(min(1, max(0, deadline - time.monotonic())))

    def _fresh(self, unit, cache):
        """Treat search hits as identities and reconstruct content from current owned BSON."""
        if unit.get("managed_by") != MANAGED_BY or unit.get("active") is not True:
            return None
        aid = unit.get("artifact_id")
        try:
            _identity(aid, "art:")
        except ValueError:
            return None
        artifacts = cache["artifacts"]
        if aid not in artifacts:
            try:
                manifest = self.runs.artifacts.find_one(self.store._owned({"_id": aid}))
                if (manifest is None or type(manifest.get("byte_count")) is not int
                        or manifest["byte_count"] < 0):
                    artifacts[aid] = None
                    return None
                if cache["bytes"] + manifest["byte_count"] > MAX_VALIDATION_BYTES:
                    cache["budget_skips"] += 1
                    artifacts[aid] = None
                    return None
                cache["bytes"] += manifest["byte_count"]
                manifest, body = self.runs._artifact_text(aid)
                self.runs._get(manifest["run_id"])
                head = self.runs.artifact_heads.find_one(self.store._owned({
                    "_id": "head:" + digest([manifest["run_id"], manifest["name"]])}))
                artifacts[aid] = (manifest, {row["_id"]: row for row in self._units(manifest, body)}) \
                    if head and head.get("artifact_id") == aid else None
            except (ValueError, KeyError, TypeError):
                artifacts[aid] = None
        loaded = artifacts[aid]
        if loaded is None:
            return None
        manifest, expected = loaded
        if expected.get(unit.get("_id")) != unit:
            return None
        return manifest

    def artifact_search(self, query, mode="hybrid", run_id="", top=10):
        query = text(query, "artifact search query", 2000)
        if not isinstance(mode, str) or mode not in {"hybrid", "semantic", "keyword"}:
            raise ValueError("Artifact search mode must be hybrid, semantic or keyword")
        if type(top) is not int or not 1 <= top <= 20:
            raise ValueError("Artifact search top must be 1..20")
        if run_id:
            _identity(run_id, "run:")
            self.runs._get(run_id)
        elif not isinstance(run_id, str):
            raise ValueError("Invalid artifact search run scope")
        bson = {"managed_by": MANAGED_BY, "active": True}
        if run_id:
            bson["run_id"] = run_id
        filters = [{"equals": {"path": key, "value": value}} for key, value in bson.items()]
        cap = min(100, max(20, top * 5))
        batches, channels = [], {}
        for channel in ("semantic", "keyword"):
            if mode != "hybrid" and mode != channel:
                continue
            if channel == "semantic":
                stage = {"$vectorSearch": {"index": VECTOR_INDEX, "path": "search_text",
                    "query": {"text": query}, "model": MODEL, "limit": cap,
                    "numCandidates": 20 * cap, "filter": bson}}
                score = "vectorSearchScore"
            else:
                stage = {"$search": {"index": TEXT_INDEX, "compound": {"filter": filters,
                    "must": [{"text": {"query": query, "path": ["search_text", "name"]}}]}}}
                score = "searchScore"
            try:
                rows = list(self.collection.aggregate([stage, {"$match": bson}, {"$limit": cap},
                    {"$project": {"_id": 1, "score": {"$meta": score}}}], maxTimeMS=15000))
                channels[channel] = {"ok": True, "native": True, "count": len(rows)}
            except Exception as exc:
                rows = []
                channels[channel] = {"ok": False, "native": False, "count": 0,
                                     "error_type": type(exc).__name__}
                if channel == "keyword":
                    terms = list(dict.fromkeys(re.findall(r"\w+", query.casefold())))[:32]
                    if terms:
                        fallback_query = {**bson, "search_text": {"$regex": "|".join(
                            re.escape(term) for term in terms), "$options": "i"}}
                        rows = list(self.collection.find(fallback_query).limit(MAX_FALLBACK_UNITS))
                    channels[channel].update(fallback=True, count=len(rows))
            batches.append((channel, rows))
        ids = sorted({row.get("_id") for _, rows in batches for row in rows
                      if isinstance(row.get("_id"), str)})
        current = {row["_id"]: row for row in self.collection.find({**bson, "_id": {"$in": ids}})}
        merged, cache = {}, {"artifacts": {}, "bytes": 0, "budget_skips": 0}
        for channel, rows in batches:
            for rank, row in enumerate(rows, 1):
                uid = row.get("_id")
                unit = current.get(uid)
                manifest = self._fresh(unit, cache) if unit else None
                if manifest is None:
                    continue
                result = merged.setdefault(uid, {"id": uid, "unit_id": uid,
                    "run_id": manifest["run_id"], "artifact_id": manifest["_id"],
                    "name": manifest["name"], "kind": manifest["kind"],
                    "qualification": copy.deepcopy(manifest["qualification"]),
                    "trusted_provenance": copy.deepcopy(manifest["trusted_provenance"]),
                    "body_utf8_sha256": manifest["body_utf8_sha256"],
                    "unit_utf8_sha256": unit["unit_utf8_sha256"],
                    "char_offset": unit["char_offset"], "char_count": unit["char_count"],
                    "text": unit["search_text"][:2000], "score": 0.0, "channels": {},
                    "candidate_only": True})
                result["score"] += 1 / (60 + rank)
                result["channels"][channel] = {"rank": rank, "score": row.get("score")}
        hits = sorted(merged.values(), key=lambda row: (-row["score"], row["unit_id"]))[:top]
        return {"hits": hits, "mode": mode, "run_id": run_id,
                "semantic": channels.get("semantic", {}).get("ok", False),
                "degraded": any(not row["ok"] for row in channels.values()) or cache["budget_skips"] > 0,
                "diagnostics": {"channels": channels,
                    "validation_budget_skips": cache["budget_skips"]}, "candidate_only": True}
