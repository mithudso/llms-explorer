"""Versioned MongoDB working research, fenced coordination and reciprocal graph edits."""
from __future__ import annotations

import copy
import hmac
import os
import re
import secrets
import sys
import time
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime

from .models import (
    CHUNK_BYTES,
    MANAGED_BY,
    MAX_CLAIMS,
    MAX_CONCEPT_BYTES,
    MAX_SOURCE_BYTES,
    RELATION_FIELDS,
    SCHEMA,
    Conflict,
    LeaseConflict,
    OwnershipError,
    canonical,
    checked_url,
    concept_id,
    digest,
    fold,
    json_value,
    normalize_url,
    revision,
    score_axes,
    search_text_projection,
    slugify,
    source_id,
    strings,
    text,
)
from .models import (
    claim_identity as default_claim_identity,
)

SUMMARY_FIELDS = ("_id", "slug", "name", "description", "aliases", "terms", "revision", "state",
                  "active", "deleted", "parent_id", "cvs", "cvs_axes", "cvs_decision", "cvs_rationale",
                  "incomplete_reasons", "completion", "qualification", "created_at", "updated_at",
                  "search_text_truncated")
MAX_PAGE_BYTES = 2 * 1024 * 1024
TX_MAX_ATTEMPTS = 8
TX_RETRY_SECONDS = 30
MAX_IMPORT_BATCH = 100
MAX_IMPORT_BATCH_BYTES = 8 * 1024 * 1024
MAX_EVIDENCE_CACHE_BYTES = 32 * 1024 * 1024
MAX_EVIDENCE_CACHE_ENTRIES = 256
_CACHE_MISSING = object()


def _evidence_cache_size(value, seen=None):
    """Conservative retained-memory accounting, including UTF-8 payload sizes."""
    seen = set() if seen is None else seen
    if id(value) in seen:
        return 0
    seen.add(id(value))
    size = sys.getsizeof(value)
    if isinstance(value, str):
        size += len(value.encode("utf-8"))
    elif isinstance(value, dict):
        size += sum(_evidence_cache_size(key, seen) + _evidence_cache_size(item, seen)
                    for key, item in value.items())
    elif isinstance(value, (tuple, list)):
        size += sum(_evidence_cache_size(item, seen) for item in value)
    return size


class LibraryStore:
    managed_by = MANAGED_BY

    def __init__(self, database=None, *, uri=None, prefix="research_",
                 reservation_provider=None, completion_verifier=None, clock=None,
                 claim_identity=None):
        if not isinstance(prefix, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,47}", prefix):
            raise ValueError("Invalid operator collection prefix")
        if database is None:
            from pymongo import MongoClient
            connection = uri or os.environ.get("MONGODB_URI2")
            if not connection:
                raise ValueError("MONGODB_URI2 is required")
            client = MongoClient(connection, appname="research-library", serverSelectionTimeoutMS=8000,
                                 connectTimeoutMS=8000, socketTimeoutMS=30000, timeoutMS=30000,
                                 retryReads=False, retryWrites=False)
            database = client["ESRE-TAM"]
        self.database, self.prefix = database, prefix
        for name in ("concepts", "versions", "sources", "snapshots", "snapshot_chunks", "leases",
                     "queue", "receipts", "meta", "claim_versions", "source_versions"):
            setattr(self, name, database[prefix + name])
        self.reservation_provider = reservation_provider
        self.completion_verifier = completion_verifier
        self.clock = clock or time.time
        self.claim_identity = claim_identity or default_claim_identity
        self._import_context = ContextVar("research_import_scope_" + str(id(self)), default=None)
        self._evidence_context = ContextVar("research_evidence_scope_" + str(id(self)), default=None)

    def _now(self):
        return float(self.clock())

    def _date(self):
        return datetime.fromtimestamp(self._now(), UTC).isoformat()

    def _owned(self, extra=None):
        return {"managed_by": MANAGED_BY, **(extra or {})}

    def _evidence_cache_get(self, key, session):
        frame = self._evidence_context.get()
        if session is None or frame is None or frame["session"] is not session:
            return _CACHE_MISSING
        value = frame["entries"].get(key, _CACHE_MISSING)
        return value if value is _CACHE_MISSING else copy.deepcopy(value)

    def _evidence_cache_put(self, key, value, session):
        frame = self._evidence_context.get()
        if session is None or frame is None or frame["session"] is not session:
            return
        entries = frame["entries"]
        if key in entries or len(entries) >= MAX_EVIDENCE_CACHE_ENTRIES:
            return
        # Include the key/container and per-entry map overhead. Immutable strings
        # are shared on deepcopy; mutable metadata is copied before retention.
        size = _evidence_cache_size((key, value)) + 128
        if frame["bytes"] + size > MAX_EVIDENCE_CACHE_BYTES:
            return
        entries[key] = copy.deepcopy(value)
        frame["bytes"] += size

    @staticmethod
    def _public(value):
        if isinstance(value, dict):
            hidden = set()
            if {"fence", "owner", "expires_at"} <= value.keys():
                hidden.update({"token_hash", "nonce"})
            if value.get("_id") == "lease-token-key":
                hidden.add("secret")
            return {k: LibraryStore._public(v) for k, v in value.items() if k not in hidden}
        if isinstance(value, list):
            return [LibraryStore._public(v) for v in value]
        return copy.deepcopy(value)

    def _tx(self, callback):
        """Bound retries; real writes always require a session transaction."""
        from pymongo.errors import DuplicateKeyError, PyMongoError
        from pymongo.read_concern import ReadConcern
        from pymongo.write_concern import WriteConcern
        started = time.monotonic()
        for attempt in range(TX_MAX_ATTEMPTS):
            if attempt and time.monotonic() - started >= TX_RETRY_SECONDS:
                raise Conflict("Concurrent research transaction conflict; retry with the same request ID")
            try:
                with self.database.client.start_session() as session:
                    token = self._evidence_context.set({"session": session, "entries": {}, "bytes": 0})
                    try:
                        with session.start_transaction(read_concern=ReadConcern("snapshot"),
                                write_concern=WriteConcern("majority"), max_commit_time_ms=30000):
                            return callback(session)
                    finally:
                        # Commit, abort and retry all discard this attempt's cache.
                        self._evidence_context.reset(token)
            except (NotImplementedError, AttributeError) as exc:
                raise RuntimeError("MongoDB transactions are required for research mutations") from exc
            except DuplicateKeyError as exc:
                raise Conflict("Concurrent research identity or idempotency conflict") from exc
            except PyMongoError as exc:
                details = getattr(exc, "details", None)
                errors = details.get("writeErrors", []) if isinstance(details, dict) else []
                codes = {getattr(exc, "code", None)} | {
                    row.get("code") for row in errors if isinstance(row, dict)}
                if codes & {11000, 11001}:
                    raise Conflict("Concurrent research identity or idempotency conflict") from None
                # Atlas mongos can report WriteConflict (112) without the label.
                # Restart the entire transaction after its context has aborted.
                retryable = (112 in codes
                             or exc.has_error_label("TransientTransactionError")
                             or exc.has_error_label("UnknownTransactionCommitResult"))
                if not retryable:
                    raise
                remaining = TX_RETRY_SECONDS - (time.monotonic() - started)
                if attempt == TX_MAX_ATTEMPTS - 1 or remaining <= 0:
                    raise Conflict("Concurrent research transaction conflict; retry with the same request ID") from None
                delay = min(remaining, min(0.025 * 2 ** attempt, 0.5)
                            + secrets.randbelow(26) / 1000)
                time.sleep(delay)
        raise RuntimeError("Research transaction did not complete")

    def _mutate(self, operation, payload, actor, request_id, callback, *, raw=False):
        actor = text(actor, "actor", 128)
        request_id = text(request_id, "request ID", 128) if request_id else secrets.token_hex(16)
        key = "op:" + digest([actor, request_id])
        fingerprint = digest({"operation": operation, "payload": payload})
        def execute(session):
            prior = self.receipts.find_one(self._owned({"_id": key}), session=session)
            if prior:
                if prior["request_sha256"] != fingerprint:
                    raise Conflict("Request ID was reused for a different operation")
                return copy.deepcopy(prior["result"])
            result = callback(session)
            result = {**result, "request_id": request_id}
            if len(canonical(result)) > MAX_CONCEPT_BYTES + 100000:
                raise ValueError("Research mutation response exceeds its byte limit")
            self.receipts.insert_one({"_id": key, "managed_by": MANAGED_BY,
                "actor": actor, "operation": operation, "request_id": request_id,
                "request_sha256": fingerprint, "at": self._date(), "result": result}, session=session)
            return result
        result = self._tx(execute)
        return result if raw else self._public(result)

    def _get(self, cid, session=None, *, deleted=False):
        cid = concept_id(cid)
        doc = self.concepts.find_one(self._owned({"_id": cid}), session=session)
        if doc is None or (doc.get("deleted") and not deleted):
            raise KeyError("No such managed concept")
        return doc

    def _source(self, sid, session=None, *, deleted=False):
        if not isinstance(sid, str) or not re.fullmatch(r"src:[0-9a-f]{16}", sid):
            raise ValueError("Invalid source identity")
        key = ("source", sid)
        doc = self._evidence_cache_get(key, session)
        if doc is _CACHE_MISSING:
            doc = self.sources.find_one(self._owned({"_id": sid}), session=session)
        if doc is None or (doc.get("deleted") and not deleted):
            raise KeyError("No such managed source")
        self._evidence_cache_put(key, doc, session)
        return doc

    def _check_lease(self, cid, token, session):
        if not isinstance(token, str) or len(token) > 256:
            raise LeaseConflict("An owned active research lease is required")
        lease = self.leases.find_one(self._owned({"_id": cid}), session=session)
        if (lease is None or lease.get("status") != "held" or lease["expires_at"] <= self._now()
                or not hmac.compare_digest(lease["token_hash"], digest(token.encode()))):
            raise LeaseConflict("The research lease is missing, expired, or no longer owned")
        # A transactional write fences concurrent expiry takeover/renewal against this edit.
        changed = self.leases.update_one(self._owned({"_id": cid, "fence": lease["fence"],
            "token_hash": lease["token_hash"], "status": "held", "expires_at": {"$gt": self._now()}}),
            {"$inc": {"uses": 1}}, session=session)
        if changed.matched_count != 1:
            raise LeaseConflict("The research lease changed during this operation")
        return lease

    def _edit(self, cid, expected, token, session):
        expected = revision(expected)
        doc = self._get(cid, session)
        if doc["revision"] != expected:
            raise Conflict("Concept revision conflict; refresh before editing")
        self._check_lease(doc["_id"], token, session)
        return copy.deepcopy(doc)

    def _prepare_save(self, doc, previous, actor, *, invalidate=True):
        """Derive one bounded revision without reading or writing the database."""
        doc = copy.deepcopy(doc)
        doc["revision"] = previous["revision"] + 1 if previous else 1
        doc["updated_at"] = self._date()
        doc.setdefault("created_at", doc["updated_at"])
        doc["managed_by"], doc["schema"] = MANAGED_BY, SCHEMA
        doc["name_folded"] = fold(doc["name"])
        doc["alias_keys"] = sorted({fold(v) for v in [doc["name"], *doc.get("aliases", [])]})
        doc["active"] = not doc.get("deleted", False) and doc["state"] != "archived"
        if invalidate:
            doc["completion"] = {"status": "unverified", "reason": "working revision changed"}
            if doc["state"] == "complete":
                doc["state"] = "incomplete"
            reasons = list(doc.get("incomplete_reasons", []))
            if doc.get("claims") and "verification-required" not in reasons:
                reasons.append("verification-required")
            doc["incomplete_reasons"] = reasons
        doc.update(search_text_projection(doc))
        imported = doc.get("import_provenance")
        if imported and self._import_context.get() == imported.get("source_identity"):
            imported["managed_revision"] = doc["revision"]
        if len(canonical(doc)) > MAX_CONCEPT_BYTES:
            raise ValueError("Concept document exceeds its byte limit")
        return doc

    @staticmethod
    def _version_snapshot(doc, actor):
        return {**copy.deepcopy(doc), "_id": f"{doc['_id']}@{doc['revision']}",
                "concept_id": doc["_id"], "actor": actor, "content_sha256": digest(doc)}

    def _save(self, doc, previous, actor, session, *, invalidate=True):
        doc = self._prepare_save(doc, previous, actor, invalidate=invalidate)
        if previous:
            result = self.concepts.replace_one(self._owned({"_id": doc["_id"],
                "revision": previous["revision"]}), doc, session=session)
            if result.matched_count != 1:
                raise Conflict("Concept revision conflict; refresh before editing")
        else:
            if self.concepts.find_one({"_id": doc["_id"]}, session=session):
                raise OwnershipError("Concept identity is already owned")
            self.concepts.insert_one(doc, session=session)
        self.versions.insert_one(self._version_snapshot(doc, actor), session=session)
        return doc

    @staticmethod
    def _response(doc, *, invalidated=True):
        return {**doc, "id": doc["_id"], "affected_concepts": [
            {"concept_id": doc["_id"], "revision": doc["revision"]}],
            "verification_invalidated": invalidated}

    def provision(self, wait_seconds=0):
        for name in ("concepts", "versions", "sources", "snapshots", "snapshot_chunks", "leases",
                     "queue", "receipts", "meta", "claim_versions", "source_versions"):
            collection = getattr(self, name)
            # Create namespaces before transactions (including sharded deployments).
            if collection.name not in self.database.list_collection_names():
                try:
                    self.database.create_collection(collection.name)
                except Exception:
                    if collection.name not in self.database.list_collection_names():
                        raise
        self.concepts.create_index([("managed_by", 1), ("alias_keys", 1)], unique=True,
                                   name="research_alias_identity_v1",
                                   partialFilterExpression={"managed_by": MANAGED_BY})
        self.concepts.create_index([("managed_by", 1), ("state", 1), ("_id", 1)])
        self.versions.create_index([("managed_by", 1), ("concept_id", 1), ("revision", 1)],
                                   unique=True, partialFilterExpression={"managed_by": MANAGED_BY})
        self.sources.create_index([("managed_by", 1), ("url", 1)], unique=True,
                                  partialFilterExpression={"managed_by": MANAGED_BY})
        self.claim_versions.create_index([("managed_by", 1), ("concept_id", 1), ("lineage_id", 1)])
        self.leases.create_index([("managed_by", 1), ("status", 1), ("expires_at", 1)])
        self.queue.create_index([("managed_by", 1), ("status", 1), ("_id", 1)])
        search = {"configured": False}
        try:
            from .queries import provision_search_indexes
            search = provision_search_indexes(self, wait_seconds=wait_seconds)
        except ImportError:
            pass
        return {"database": self.database.name, "prefix": self.prefix,
                "managed_by": MANAGED_BY, "search": search}

    def status(self):
        graph = self.meta.find_one(self._owned({"_id": "graph"}), {"revision": 1})
        return {"database": self.database.name, "prefix": self.prefix, "managed_by": MANAGED_BY,
                "schema": SCHEMA, "counts": {name: getattr(self, name).count_documents(self._owned())
                    for name in ("concepts", "versions", "sources", "snapshots", "queue")},
                "active_leases": self.leases.count_documents(self._owned({"status": "held",
                    "expires_at": {"$gt": self._now()}})), "graph_revision": (graph or {}).get("revision", 0)}

    def concept_get(self, concept_id, revision=None):
        cid = globals()["concept_id"](concept_id)
        if revision is None:
            return self._public(self._get(cid, deleted=True))
        globals()["revision"](revision)
        doc = self.versions.find_one(self._owned({"_id": f"{cid}@{revision}"}))
        if doc is None:
            raise KeyError("No such managed concept revision")
        return self._public(doc)

    def resolve_concept(self, name_or_id):
        value = text(name_or_id, "concept lookup", 500)
        query = self._owned({"$or": [{"_id": value}, {"slug": value}, {"alias_keys": fold(value)}]})
        rows = list(self.concepts.find(query).limit(2))
        if not rows:
            raise KeyError("No such managed concept")
        if len(rows) != 1:
            raise Conflict("Concept identity is ambiguous")
        return self._public(rows[0])

    def concept_list(self, filters=None, after="", limit=100):
        query = self._concept_filter(filters)
        return self._page(self.concepts, query, after, limit, "concepts",
                          projection={field: 1 for field in SUMMARY_FIELDS})

    def concept_history(self, concept_id, after="", limit=100):
        cid = globals()["concept_id"](concept_id)
        return self._page(self.versions, self._owned({"concept_id": cid}), after, limit, "versions",
                          projection={field: 1 for field in (*SUMMARY_FIELDS, "concept_id", "actor", "content_sha256")})

    def _concept_filter(self, filters):
        if filters is None:
            filters = {}
        if not isinstance(filters, dict) or set(filters) - {"state", "active", "parent_id", "cvs_scored", "deleted"}:
            raise ValueError("Unsupported concept filter")
        query = self._owned()
        for key, value in filters.items():
            if key == "state":
                if value not in {"frontier", "draft", "incomplete", "complete", "archived"}:
                    raise ValueError("Invalid concept state")
                query[key] = value
            elif key == "parent_id":
                query[key] = concept_id(value) if value else None
            elif key == "cvs_scored":
                if type(value) is not bool:
                    raise ValueError("Invalid score filter")
                query["cvs"] = {"$ne": None} if value else None
            else:
                if type(value) is not bool:
                    raise ValueError("Invalid Boolean filter")
                query[key] = value
        return query

    def _page(self, collection, query, after, limit, key, projection=None):
        if type(limit) is not int or not 1 <= limit <= 200 or not isinstance(after, str) or len(after) > 256:
            raise ValueError("Invalid pagination bounds")
        if after:
            query = {**query, "_id": {"$gt": after}}
        rows, consumed, more = [], 0, False
        # Compatibility collections and `items` serialize the same rows twice.
        budget = (MAX_PAGE_BYTES - 4096) // 2
        for record in collection.find(query, projection).sort("_id", 1).limit(limit + 1):
            row = self._public(record)
            size = len(canonical(row))
            if size > budget:
                row = {field: row[field] for field in ("_id", "slug", "name", "revision", "state",
                    "concept_id", "active", "deleted", "status", "stop", "cvs", "cvs_decision") if field in row}
                row.update(details_omitted=True, detail_operation="concept_get")
                size = len(canonical(row))
            if len(rows) >= limit or consumed + size > budget:
                more = True
                break
            rows.append(row)
            consumed += size
        return {key: rows, "items": copy.deepcopy(rows),
                "next_cursor": rows[-1]["_id"] if more and rows else None,
                "has_more": more, "truncated": more,
                "metadata_only": projection is not None, "max_response_bytes": MAX_PAGE_BYTES}

    def concept_create(self, name, slug=None, description="", aliases=None, terms=None,
                       request_id="", actor="agent"):
        name = text(name, "concept name", 500)
        cid = concept_id(slug or slugify(name))
        description = text(description, "description", 16000, empty=True)
        aliases = strings(aliases or [], "aliases")
        terms = strings(terms or [], "terms", maximum=256)
        payload = dict(name=name, slug=cid[2:], description=description, aliases=aliases, terms=terms)
        def create(session):
            aliases_keys = list({fold(v) for v in [name, *aliases]})
            if self.concepts.find_one(self._owned({"alias_keys": {"$in": aliases_keys}}), session=session):
                raise Conflict("A concept with this name or alias already exists")
            doc = {"_id": cid, **payload, "state": "frontier", "claims": [], "source_refs": [],
                   "parent_id": None, **{key: [] for key in RELATION_FIELDS}, "cvs": None,
                   "cvs_axes": None, "cvs_decision": "REVIEW", "incomplete_reasons": ["unresearched"],
                   "deleted": False, "open_questions": [], "scope": {}}
            return self._response(self._save(doc, None, actor, session))
        return self._mutate("concept_create", payload, actor, request_id, create)

    def _patch(self, doc, patch):
        allowed = {"name", "description", "aliases", "terms", "state", "cvs", "cvs_axes",
                   "cvs_rationale", "cvs_decision", "open_questions", "scope", "incomplete_reasons",
                   "metadata", "summary", "disagreements", "telemetry", "scope_assessment"}
        if not isinstance(patch, dict) or set(patch) - allowed:
            raise ValueError("Unsupported concept edit or caller-supplied authority")
        changed = copy.deepcopy(doc)
        for key, value in patch.items():
            if key in {"name", "description", "cvs_rationale"}:
                changed[key] = text(value, key, 16000 if key != "name" else 500, empty=key != "name")
            elif key in {"aliases", "terms", "incomplete_reasons"}:
                changed[key] = strings(value, key, 256, 2000)
            elif key == "state":
                if value not in {"frontier", "draft", "incomplete", "archived"}:
                    raise ValueError("Completion requires a trusted publication verifier")
                changed[key] = value
            elif key in {"scope", "metadata", "telemetry", "scope_assessment"}:
                if not isinstance(value, dict):
                    raise ValueError("Scope must be an object")
                changed[key] = json_value(value)
            elif key == "summary":
                changed[key] = text(value, "summary", 64000, empty=True)
            elif key in {"open_questions", "disagreements"}:
                if not isinstance(value, list) or len(value) > 256:
                    raise ValueError("Invalid factual prose list")
                changed[key] = json_value(value)
        if "cvs_axes" in patch and patch["cvs_axes"] is not None:
            changed.update(score_axes(patch["cvs_axes"]))
        elif "cvs" in patch:
            value = patch["cvs"]
            if value is not None and (type(value) not in (int, float) or not 0 <= value <= 5):
                raise ValueError("CVS must be null or 0..5")
            changed.update(cvs=value, cvs_axes=None, cvs_decision="REVIEW")
        elif "cvs_axes" in patch:
            # Explicitly clearing axes alone also clears the derived scalar.
            # A supplied legacy scalar with null axes remains an unqualified score.
            changed.update(score_axes(None))
        if "cvs_decision" in patch:
            value = patch["cvs_decision"]
            if value not in {"RESEARCH", "REFRESH", "SKIP", "REVIEW"}:
                raise ValueError("Invalid CVS decision")
            if value in {"RESEARCH", "REFRESH"} and (not changed.get("cvs_axes")
                    or score_axes(changed["cvs_axes"])["cvs_decision"] != "RESEARCH"):
                raise ValueError("Research CVS decision requires qualifying axis evidence")
            changed["cvs_decision"] = value
        if "name" in patch and changed["name"] != doc["name"]:
            changed["aliases"] = list(dict.fromkeys([*changed.get("aliases", []), doc["name"]]))
        return changed

    def concept_update(self, concept_id, patch, expected_revision, lease_token,
                       actor="agent", request_id=""):
        cid = globals()["concept_id"](concept_id)
        payload = dict(concept_id=cid, patch=patch, expected_revision=expected_revision, lease_token=lease_token)
        def edit(session):
            old = self._edit(cid, expected_revision, lease_token, session)
            doc = self._patch(old, patch)
            keys = [fold(v) for v in [doc["name"], *doc.get("aliases", [])]]
            if self.concepts.find_one(self._owned({"_id": {"$ne": cid}, "alias_keys": {"$in": keys}}), session=session):
                raise Conflict("The new concept name or alias is already owned")
            return self._response(self._save(doc, old, actor, session))
        return self._mutate("concept_update", payload, actor, request_id, edit)

    def concept_delete(self, concept_id, expected_revision, lease_token, actor="agent", request_id=""):
        cid = globals()["concept_id"](concept_id)
        def remove(session):
            old = self._edit(cid, expected_revision, lease_token, session)
            if old.get("parent_id") or any(old.get(k) for k in RELATION_FIELDS):
                raise Conflict("Unlink family relationships before archiving this concept")
            doc = {**old, "deleted": True, "state": "archived"}
            return self._response(self._save(doc, old, actor, session))
        return self._mutate("concept_delete", locals_payload(cid, expected_revision, lease_token),
                            actor, request_id, remove)

    def _snapshot_text(self, sid, checksum, session=None):
        if not isinstance(checksum, str) or not re.fullmatch(r"[0-9a-f]{64}", checksum):
            raise ValueError("A pinned source snapshot hash is required")
        key = ("snapshot", sid, checksum)
        cached = self._evidence_cache_get(key, session)
        if cached is not _CACHE_MISSING:
            return cached
        snapshot = self.snapshots.find_one(self._owned({"_id": sid + "@" + checksum}), session=session)
        if snapshot is None:
            raise KeyError("No such source snapshot")
        parts = []
        for number in range(snapshot["chunks"]):
            row = self.snapshot_chunks.find_one(self._owned({"_id": f"{sid}@{checksum}:{number}"}), session=session)
            if row is None:
                raise ValueError("Source snapshot is incomplete")
            parts.append(bytes(row["data"]))
        raw = b"".join(parts)
        if len(raw) != snapshot["bytes"] or digest(raw) != checksum:
            raise ValueError("Source snapshot integrity check failed")
        result = raw.decode("utf-8"), snapshot
        self._evidence_cache_put(key, result, session)
        return result

    def _claim(self, slug, supplied, session, lineage):
        if not isinstance(supplied, dict) or set(supplied) - {"text", "sources", "confidence", "verified_as_of",
                "volatile", "temporal", "evidence", "conflict", "lineage_id"}:
            raise ValueError("Unsupported claim fields or caller-authored verification")
        claim = json_value(supplied, maximum=256 * 1024)
        claim.pop("lineage_id", None)
        claim["text"] = text(claim.get("text"), "claim text", 32000)
        claim["sources"] = strings(claim.get("sources", []), "claim sources", 64, 4096)
        for url in claim["sources"]:
            checked_url(url)
        confidence = claim.get("confidence", "unreviewed")
        if not (isinstance(confidence, str) and 0 < len(confidence) <= 100) and not (
                type(confidence) in (int, float) and 0 <= confidence <= 1):
            raise ValueError("Invalid claim confidence")
        claim["confidence"] = confidence
        if "volatile" in claim and type(claim["volatile"]) is not bool:
            raise ValueError("Volatile must be a Boolean")
        evidence = claim.get("evidence", [])
        if not isinstance(evidence, list) or len(evidence) > 128:
            raise ValueError("Invalid claim evidence")
        for span in evidence:
            if not isinstance(span, dict) or set(span) != {"url", "source_id", "snapshot_sha256", "start", "end", "quote", "extraction_status"}:
                raise ValueError("Evidence requires exact source identity and Unicode spans")
            if span["url"] not in claim["sources"]:
                raise ValueError("Evidence URL is not among the claim sources")
            source = self._source(span["source_id"], session, deleted=True)
            if normalize_url(source["url"]) != normalize_url(span["url"]):
                raise ValueError("Evidence belongs to a different source URL")
            body, _ = self._snapshot_text(span["source_id"], span["snapshot_sha256"], session)
            a, b, quote = span["start"], span["end"], span["quote"]
            if (type(a) is not int or type(b) is not int or not 0 <= a < b <= len(body)
                    or not isinstance(quote, str) or body[a:b] != quote
                    or span["extraction_status"] != "complete"):
                raise ValueError("Evidence quotation does not match its pinned source span")
        immutable = self.claim_identity(slug, claim)
        return {**claim, "lineage_id": lineage, "claim_id": "clm:" + digest(immutable),
                "identity": immutable, "qualification": "unreviewed", "deleted": False}

    def claim_mutate(self, concept_id, action, claim=None, lineage_id="", expected_revision=None,
                     lease_token="", actor="agent", request_id=""):
        cid = globals()["concept_id"](concept_id)
        if action not in {"add", "update", "replace", "remove"}:
            raise ValueError("Unsupported claim action")
        lineage_id = text(lineage_id, "claim lineage", 128) if lineage_id else "lineage:" + (
            digest([actor, request_id, cid])[:32] if request_id else secrets.token_hex(16))
        payload = dict(concept_id=cid, action=action, claim=claim, lineage_id=lineage_id,
                       expected_revision=expected_revision, lease_token=lease_token)
        def change(session):
            old = self._edit(cid, expected_revision, lease_token, session)
            claims = copy.deepcopy(old["claims"])
            position = next((i for i, item in enumerate(claims) if item["lineage_id"] == lineage_id), None)
            if action == "add" and position is not None:
                raise Conflict("Claim lineage already exists")
            if action != "add" and (position is None or claims[position].get("deleted")):
                raise KeyError("No such current claim lineage")
            if action == "remove":
                current = {**claims[position], "deleted": True, "qualification": "unreviewed"}
            else:
                supplied = claim
                if action == "update":
                    prior = {k: v for k, v in claims[position].items()
                             if k not in {"lineage_id", "claim_id", "identity", "qualification", "deleted", "evidence_integrity",
                                           "canonical_claim_id", "identity_slug"}}
                    if not isinstance(claim, dict):
                        raise ValueError("Claim update must be an object")
                    supplied = {**prior, **claim}
                current = self._claim(old["slug"], supplied, session, lineage_id)
                if any(c["claim_id"] == current["claim_id"] and c["lineage_id"] != lineage_id
                       and not c.get("deleted") for c in claims):
                    raise Conflict("Exact claim version already exists in this concept")
            if position is None:
                if len(claims) >= MAX_CLAIMS:
                    raise ValueError("Concept claim limit exceeded")
                claims.append(current)
            else:
                claims[position] = current
            version_id = digest([cid, lineage_id, current["claim_id"], bool(current.get("deleted"))])
            self.claim_versions.update_one(self._owned({"_id": version_id}), {"$setOnInsert": {
                "_id": version_id, "managed_by": MANAGED_BY, "concept_id": cid,
                **current, "created_at": self._date(), "actor": actor}}, upsert=True, session=session)
            doc = {**old, "claims": claims, "state": "draft"}
            saved = self._save(doc, old, actor, session)
            result = self._response(saved)
            result["claim"] = current
            return result
        return self._mutate("claim_mutate", payload, actor, request_id, change)

    def source_put(self, url, text=None, metadata=None, expected_revision=None,
                   actor="agent", request_id="", make_current=True):
        url = normalize_url(url)
        if type(make_current) is not bool:
            raise ValueError("make_current must be a Boolean")
        sid = source_id(url)
        if text is not None and (not isinstance(text, str) or len(text.encode()) > MAX_SOURCE_BYTES):
            raise ValueError("Source snapshot exceeds its byte limit")
        metadata = json_value(metadata or {})
        if not isinstance(metadata, dict):
            raise ValueError("Source metadata must be an object")
        def put(session):
            prior = self.sources.find_one({"_id": sid}, session=session)
            if prior and prior.get("managed_by") != MANAGED_BY:
                raise OwnershipError("Source identity belongs to another producer")
            if prior:
                if prior["url"] != url:
                    raise Conflict("Source identity collision; existing URL is preserved")
                if make_current and revision(expected_revision) != prior["revision"]:
                    raise Conflict("Source revision conflict")
            elif expected_revision not in (None, 0):
                raise Conflict("New source must not have a current revision")
            checksum = digest(text.encode()) if text is not None else (prior or {}).get("snapshot_sha256")
            if checksum is None:
                raise ValueError("A new source requires an immutable text snapshot")
            if text is not None:
                raw = text.encode()
                chunks = max(1, (len(raw) + CHUNK_BYTES - 1) // CHUNK_BYTES)
                snap = {"_id": sid + "@" + checksum, "managed_by": MANAGED_BY, "source_id": sid,
                        "url": url, "snapshot_sha256": checksum, "bytes": len(raw),
                        "chunks": chunks, "created_at": self._date()}
                for number in range(chunks):
                    key = f"{sid}@{checksum}:{number}"
                    self.snapshot_chunks.update_one(self._owned({"_id": key}), {"$setOnInsert": {
                        "_id": key, "managed_by": MANAGED_BY, "data": raw[number * CHUNK_BYTES:(number + 1) * CHUNK_BYTES]}},
                        upsert=True, session=session)
                self.snapshots.update_one(self._owned({"_id": snap["_id"]}), {"$setOnInsert": snap}, upsert=True, session=session)
            if prior and not make_current:
                return {**prior, "imported_snapshot_sha256": checksum, "current_unchanged": True}
            doc = {"_id": sid, "source_id": sid, "managed_by": MANAGED_BY, "url": url,
                   "revision": (prior or {}).get("revision", 0) + 1, "snapshot_sha256": checksum,
                   "metadata": metadata, "deleted": False, "updated_at": self._date(),
                   "created_at": (prior or {}).get("created_at", self._date())}
            self.sources.replace_one(self._owned({"_id": sid}), doc, upsert=True, session=session)
            self.source_versions.insert_one({**doc, "_id": f"{sid}@revision:{doc['revision']}"}, session=session)
            return {**doc, "source_id": sid}
        return self._mutate("source_put", dict(url=url, text=text, metadata=metadata,
                            expected_revision=expected_revision, make_current=make_current), actor, request_id, put)

    def source_get(self, source_id, snapshot_sha256="", offset=0, max_chars=16000):
        source = self._source(source_id, deleted=True)
        if type(offset) is not int or offset < 0 or type(max_chars) is not int or not 1 <= max_chars <= 32000:
            raise ValueError("Invalid source page")
        body, snapshot = self._snapshot_text(source_id, snapshot_sha256 or source["snapshot_sha256"])
        if offset > len(body):
            raise ValueError("Source offset exceeds text length")
        end = min(len(body), offset + max_chars)
        return {**self._public(source), "source": self._public(source), "snapshot": self._public(snapshot),
                "text": body[offset:end], "offset": offset,
                "next_offset": end if end < len(body) else None, "snapshot_sha256": snapshot["snapshot_sha256"]}

    def source_lookup(self, url):
        """Find an exact normalized cache identity without returning source text."""
        url = normalize_url(url)
        sid = source_id(url)
        source = self.sources.find_one(self._owned({"_id": sid}))
        available = False
        if source:
            if source["url"] != url:
                raise Conflict("Source identity collision; existing URL is preserved")
            try:
                self._snapshot_text(sid, source.get("snapshot_sha256"))
                available = True
            except (KeyError, ValueError):
                # Metadata remains useful when an archive is missing or damaged.
                pass
        return {"found": source is not None, "source_id": sid, "url": url,
                "source": self._public(source), "snapshot_available": available}

    def source_delete(self, source_id, expected_revision, actor="agent", request_id=""):
        def remove(session):
            prior = self._source(source_id, session)
            if revision(expected_revision) != prior["revision"]:
                raise Conflict("Source revision conflict")
            candidates = self.concepts.find(self._owned({"active": True, "$or": [
                {"source_refs.source_id": source_id}, {"claims.evidence.source_id": source_id},
                {"claims.sources": prior["url"]}]}), session=session)
            for candidate in candidates:
                linked = any(ref.get("source_id") == source_id for ref in candidate.get("source_refs", []))
                cited = any(not claim.get("deleted") and (
                    any(span.get("source_id") == source_id for span in claim.get("evidence", []))
                    or any(normalize_url(url) == prior["url"] for url in claim.get("sources", [])))
                    for claim in candidate.get("claims", []))
                if linked or cited:
                    raise Conflict("Unlink active concept and claim references before archiving this source")
            doc = {**prior, "deleted": True, "revision": prior["revision"] + 1, "updated_at": self._date()}
            self.sources.replace_one(self._owned({"_id": source_id, "revision": prior["revision"]}), doc, session=session)
            self.source_versions.insert_one({**doc, "_id": f"{source_id}@revision:{doc['revision']}"}, session=session)
            return doc
        return self._mutate("source_delete", dict(source_id=source_id, expected_revision=expected_revision),
                            actor, request_id, remove)

    def source_link(self, concept_id, action, source_ref, expected_revision, lease_token,
                    actor="agent", request_id=""):
        cid = globals()["concept_id"](concept_id)
        if action not in {"add", "update", "remove"} or not isinstance(source_ref, dict):
            raise ValueError("Invalid concept source action")
        if set(source_ref) - {"source_id", "snapshot_sha256", "rationale"}:
            raise ValueError("Invalid source reference")
        sid = source_ref.get("source_id")
        def change(session):
            old = self._edit(cid, expected_revision, lease_token, session)
            source = self._source(sid, session, deleted=action == "remove")
            ref = {"source_id": sid, "url": source["url"],
                   "snapshot_sha256": source_ref.get("snapshot_sha256") or source["snapshot_sha256"],
                   "rationale": text(source_ref.get("rationale", ""), "source rationale", 2000, empty=True)}
            self._snapshot_text(sid, ref["snapshot_sha256"], session)
            refs = copy.deepcopy(old["source_refs"])
            position = next((i for i, r in enumerate(refs) if r["source_id"] == sid), None)
            if action == "add" and position is not None:
                raise Conflict("Source is already linked")
            if action != "add" and position is None:
                raise KeyError("No such concept source link")
            if action == "remove":
                if any(not c.get("deleted") and (any(e["source_id"] == sid for e in c.get("evidence", []))
                       or any(normalize_url(url) == source["url"] for url in c.get("sources", [])))
                       for c in old["claims"]):
                    raise Conflict("Remove or replace bound claim evidence before unlinking this source")
                refs.pop(position)
            elif position is None:
                refs.append(ref)
            else:
                refs[position] = ref
            return self._response(self._save({**old, "source_refs": refs}, old, actor, session))
        return self._mutate("source_link", dict(concept_id=cid, action=action, source_ref=source_ref,
            expected_revision=expected_revision, lease_token=lease_token), actor, request_id, change)

    def _key(self, session):
        self.meta.update_one(self._owned({"_id": "lease-token-key"}), {"$setOnInsert": {
            "_id": "lease-token-key", "managed_by": MANAGED_BY, "secret": secrets.token_hex(32)}},
            upsert=True, session=session)
        return self.meta.find_one(self._owned({"_id": "lease-token-key"}), session=session)["secret"]

    @staticmethod
    def _token(row, key):
        value = canonical([row["_id"], row["owner"], row["fence"], row["nonce"]])
        return "rl:" + hmac.digest(bytes.fromhex(key), value, "sha256").hex()

    @staticmethod
    def _ids(values):
        if not isinstance(values, list) or not 1 <= len(values) <= 100:
            raise ValueError("Require 1..100 concept identities")
        return sorted({concept_id(v) for v in values})

    @staticmethod
    def _ttl(value):
        if type(value) is not int or not 30 <= value <= 3600:
            raise ValueError("Lease TTL must be 30..3600 seconds")
        return value

    def _reservations(self, ids, owner, run_id):
        if self.reservation_provider:
            held = self.reservation_provider(ids, owner, run_id)
            if held:
                raise LeaseConflict("A legacy active, paused, or STOP reservation holds this concept")

    def lease_acquire(self, concept_ids, owner, ttl_seconds=900, run_id="", request_id="", actor="agent"):
        ids, owner, ttl = self._ids(concept_ids), text(owner, "lease owner", 200), self._ttl(ttl_seconds)
        run_id = text(run_id, "run identity", 256, empty=True)
        self._reservations(ids, owner, run_id)
        def acquire(session):
            self._reservations(ids, owner, run_id)
            key, rows = self._key(session), []
            for cid in ids:
                self._get(cid, session)
                held_queue = self.queue.find_one(self._owned({"_id": cid}), session=session)
                if held_queue and (held_queue.get("stop") or held_queue.get("status") in {"paused", "held"}):
                    raise LeaseConflict("The queue is paused, held, or stopped; explicit operator recovery is required")
                prior = self.leases.find_one(self._owned({"_id": cid}), session=session)
                if prior and prior.get("status") == "held" and prior["expires_at"] > self._now():
                    raise LeaseConflict("Concept is already leased; only its owner can renew it")
                row = {"_id": cid, "managed_by": MANAGED_BY, "concept_id": cid,
                       "owner": owner, "run_id": run_id, "status": "held",
                       "fence": (prior or {}).get("fence", 0) + 1,
                       "nonce": secrets.token_hex(16), "acquired_at": self._now(),
                       "expires_at": self._now() + ttl, "uses": 0}
                row["token_hash"] = digest(self._token(row, key).encode())
                self.leases.replace_one(self._owned({"_id": cid}), row, upsert=True, session=session)
                rows.append(row)
            return {"leases": rows}
        result = self._mutate("lease_acquire", dict(concept_ids=ids, owner=owner, ttl_seconds=ttl, run_id=run_id),
                              actor, request_id, acquire, raw=True)
        keyrow = self.meta.find_one(self._owned({"_id": "lease-token-key"}))
        public = self._public(result)
        public["tokens"] = {r["_id"]: self._token(r, keyrow["secret"]) for r in result["leases"]}
        public["fences"] = {r["_id"]: r["fence"] for r in result["leases"]}
        for row in public["leases"]:
            row["token"] = public["tokens"][row["_id"]]
        return public

    def lease_renew(self, concept_ids, tokens, owner, ttl_seconds=900, actor="agent", request_id=""):
        ids, ttl = self._ids(concept_ids), self._ttl(ttl_seconds)
        owner = text(owner, "lease owner", 200)
        if not isinstance(tokens, dict):
            raise ValueError("Owned lease tokens are required")
        def renew(session):
            rows = []
            for cid in ids:
                row = self._check_lease(cid, tokens.get(cid, ""), session)
                if row["owner"] != owner:
                    raise LeaseConflict("Lease owner does not match")
                self._reservations([cid], owner, row.get("run_id", ""))
                self.leases.update_one(self._owned({"_id": cid, "fence": row["fence"]}),
                    {"$set": {"expires_at": self._now() + ttl}}, session=session)
                rows.append({"concept_id": cid, "fence": row["fence"], "expires_at": self._now() + ttl})
            return {"leases": rows}
        return self._mutate("lease_renew", dict(concept_ids=ids, tokens=tokens, owner=owner, ttl_seconds=ttl),
                            actor, request_id, renew)

    def lease_release(self, concept_ids, tokens, owner, actor="agent", request_id=""):
        ids, owner = self._ids(concept_ids), text(owner, "lease owner", 200)
        if not isinstance(tokens, dict):
            raise ValueError("Owned lease tokens are required")
        def release(session):
            for cid in ids:
                row = self._check_lease(cid, tokens.get(cid, ""), session)
                if row["owner"] != owner:
                    raise LeaseConflict("Lease owner does not match")
                self.leases.update_one(self._owned({"_id": cid, "fence": row["fence"]}),
                    {"$set": {"status": "released", "expires_at": self._now()}}, session=session)
            return {"released": ids}
        return self._mutate("lease_release", dict(concept_ids=ids, tokens=tokens, owner=owner),
                            actor, request_id, release)

    def lease_delegate(self, concept_ids, tokens, owner, new_owner, ttl_seconds=900,
                       actor="trusted-publisher", request_id=""):
        ids, ttl = self._ids(concept_ids), self._ttl(ttl_seconds)
        owner, new_owner = text(owner, "lease owner", 200), text(new_owner, "new lease owner", 200)
        if not isinstance(tokens, dict):
            raise ValueError("Owned lease tokens are required")
        def delegate(session):
            key, rows = self._key(session), []
            for cid in ids:
                old = self._check_lease(cid, tokens.get(cid, ""), session)
                if old["owner"] != owner:
                    raise LeaseConflict("Lease owner does not match")
                row = {**old, "owner": new_owner, "fence": old["fence"] + 1,
                       "nonce": secrets.token_hex(16), "acquired_at": self._now(),
                       "expires_at": self._now() + ttl}
                row["token_hash"] = digest(self._token(row, key).encode())
                self.leases.replace_one(self._owned({"_id": cid, "fence": old["fence"]}), row, session=session)
                rows.append(row)
            return {"leases": rows}
        result = self._mutate("lease_delegate", dict(concept_ids=ids, tokens=tokens, owner=owner,
            new_owner=new_owner, ttl_seconds=ttl), actor, request_id, delegate, raw=True)
        key = self.meta.find_one(self._owned({"_id": "lease-token-key"}))["secret"]
        public = self._public(result)
        public["tokens"] = {r["_id"]: self._token(r, key) for r in result["leases"]}
        public["fences"] = {r["_id"]: r["fence"] for r in result["leases"]}
        return public

    def lease_list(self):
        rows = list(self.leases.find(self._owned({"status": "held", "expires_at": {"$gt": self._now()}}),
                                    {"token_hash": 0, "nonce": 0}).sort("_id", 1).limit(1001))
        return {"leases": self._public(rows[:1000]), "truncated": len(rows) > 1000}

    def relation_mutate(self, concept_id, target_id, relation, action, expected_revisions,
                        lease_tokens, actor="agent", request_id=""):
        cid, tid = globals()["concept_id"](concept_id), globals()["concept_id"](target_id)
        if cid == tid:
            raise ValueError("A concept cannot relate to itself")
        if action not in {"add", "remove", "update", "replace"} or relation not in {
                "parent", "child", "related", "adjacent", "prerequisite", "dependent"}:
            raise ValueError("Unsupported family relation or action")
        if not isinstance(expected_revisions, dict) or not isinstance(lease_tokens, dict):
            raise ValueError("All affected endpoint revisions and leases are required")
        def change(session):
            self.meta.update_one(self._owned({"_id": "graph"}), {"$inc": {"revision": 1},
                "$setOnInsert": {"managed_by": MANAGED_BY}}, upsert=True, session=session)
            child, parent = (cid, tid) if relation == "parent" else (tid, cid)
            loaded = {cid: self._get(cid, session), tid: self._get(tid, session)}
            if relation in {"parent", "child"}:
                old_parent = loaded[child].get("parent_id")
                if old_parent:
                    loaded.setdefault(old_parent, self._get(old_parent, session))
            for key in list(loaded):
                loaded[key] = self._edit(key, expected_revisions.get(key), lease_tokens.get(key, ""), session)
            original = copy.deepcopy(loaded)
            if relation in {"parent", "child"} and self._import_context.get() is None:
                # An explicit working choice supersedes the canonical read lead.
                # Imported family projections keep their separate candidate status.
                loaded[child]["family_override"] = True
            def link(a, field, b, add):
                values = loaded[a].setdefault(field, [])
                if add and b not in values:
                    values.append(b)
                    values.sort()
                elif not add and b in values:
                    values.remove(b)
            if relation in {"parent", "child"}:
                prior = loaded[child].get("parent_id")
                if action == "remove":
                    if prior != parent:
                        raise Conflict("The requested parent relation does not exist")
                    loaded[child]["parent_id"] = None
                    link(parent, "children_ids", child, False)
                else:
                    if prior and prior != parent and action == "add":
                        raise Conflict("Concept already has a parent; use an explicit reparent update")
                    visited, current = {child}, parent
                    while current:
                        if current in visited:
                            raise Conflict("Family relationship would introduce a cycle")
                        visited.add(current)
                        current = (loaded[current] if current in loaded else self._get(current, session)).get("parent_id")
                        if len(visited) > 10000:
                            raise ValueError("Family ancestry limit exceeded")
                    if prior and prior != parent:
                        link(prior, "children_ids", child, False)
                    loaded[child]["parent_id"] = parent
                    link(parent, "children_ids", child, True)
            else:
                fields = {"related": ("related_ids", "related_ids"),
                          "adjacent": ("adjacent_ids", "adjacent_ids"),
                          "prerequisite": ("prerequisite_ids", "dependent_ids"),
                          "dependent": ("dependent_ids", "prerequisite_ids")}[relation]
                if action == "remove" and tid not in loaded[cid].get(fields[0], []):
                    raise Conflict("The requested relation does not exist")
                link(cid, fields[0], tid, action != "remove")
                link(tid, fields[1], cid, action != "remove")
            saved = []
            for key, doc in loaded.items():
                if doc != original[key]:
                    saved.append(self._save(doc, original[key], actor, session))
            return {"concepts": [self._public(d) for d in saved], "unchanged": not saved,
                    "affected_concepts": [{"concept_id": d["_id"], "revision": d["revision"]} for d in saved],
                    "verification_invalidated": bool(saved)}
        return self._mutate("relation_mutate", dict(concept_id=cid, target_id=tid, relation=relation,
            action=action, expected_revisions=expected_revisions, lease_tokens=lease_tokens), actor, request_id, change)

    def queue_put(self, concept_id, action="enqueue", metadata=None, expected_revision=None,
                  lease_token="", actor="agent", request_id=""):
        cid = globals()["concept_id"](concept_id)
        states = {"enqueue": "queued", "pause": "paused", "hold": "held", "resume": "queued",
                  "cancel": "cancelled", "remove": "cancelled", "stop": "paused"}
        if action not in states or not isinstance(metadata or {}, dict):
            raise ValueError("Unsupported queue operation")
        metadata = json_value(metadata or {})
        if set(metadata) - {"priority", "reason", "provenance", "continuation", "scope", "requested_by"}:
            raise ValueError("Unsupported queue metadata")
        def change(session):
            old = self._edit(cid, expected_revision, lease_token, session)
            prior = self.queue.find_one(self._owned({"_id": cid}), session=session)
            if prior and prior.get("stop") and action in {"resume", "enqueue"}:
                raise LeaseConflict("The queue STOP marker requires explicit operator recovery")
            saved = self._save(old, old, actor, session, invalidate=False)
            row = {"_id": cid, "managed_by": MANAGED_BY, "concept_id": cid,
                   "revision": (prior or {}).get("revision", 0) + 1,
                   "concept_revision": saved["revision"], "status": states[action],
                   "stop": bool((prior or {}).get("stop") or action == "stop"),
                   "metadata": {**(prior or {}).get("metadata", {}), **metadata},
                   "updated_at": self._date(), "actor": actor,
                   "cvs": saved.get("cvs"), "cvs_decision": saved.get("cvs_decision")}
            self.queue.replace_one(self._owned({"_id": cid}), row, upsert=True, session=session)
            return {**row, "affected_concepts": [{"concept_id": cid, "revision": saved["revision"]}],
                    "dispatched": False}
        return self._mutate("queue_put", dict(concept_id=cid, action=action, metadata=metadata,
            expected_revision=expected_revision, lease_token=lease_token), actor, request_id, change)

    def import_queue(self, concept_id, record, source_identity, source_sha256):
        """Owner-local projection of all legacy queue rows, including held work."""
        cid = globals()["concept_id"](concept_id)
        if not isinstance(record, dict):
            raise ValueError("Imported queue record must be an object")
        record = json_value(record)
        source_identity = text(source_identity, "queue import identity", 2000)
        if not re.fullmatch(r"[0-9a-f]{64}", source_sha256 or ""):
            raise ValueError("Queue import requires a source hash")
        def protected(old):
            provenance = (old or {}).get("import_provenance", {})
            if old and (provenance.get("source_identity") != source_identity
                        or provenance.get("managed_revision") != old["revision"]):
                raise Conflict("A locally edited queue row cannot be replaced by import")
        current_queue = self.queue.find_one(self._owned({"_id": cid}))
        protected(current_queue)
        if current_queue and current_queue.get("import_provenance", {}).get("source_sha256") == source_sha256:
            return {**self._public(current_queue), "unchanged": True,
                    "projection_only": True, "dispatched": False}
        def load(session):
            self._get(cid, session)
            old = self.queue.find_one(self._owned({"_id": cid}), session=session)
            protected(old)
            if old and old.get("import_provenance", {}).get("source_sha256") == source_sha256:
                return {**old, "unchanged": True, "projection_only": True, "dispatched": False}
            row = self._prepare_import_queue(cid, record, source_identity, source_sha256, old)
            self.queue.replace_one(self._owned({"_id": cid}), row, upsert=True, session=session)
            return {**row, "projection_only": True, "dispatched": False}
        return self._mutate("import_queue", dict(concept_id=cid, record=record,
            source_identity=source_identity, source_sha256=source_sha256), "canonical-import",
            digest(["queue", cid, source_identity, source_sha256, record]), load)

    def _prepare_import_queue(self, cid, record, source_identity, source_sha256, previous=None):
        status = record.get("status", record.get("state", "queued"))
        if not isinstance(status, str):
            raise ValueError("Imported queue status must be text")
        status = {"pending": "queued", "stopped": "paused", "STOP": "paused", "done": "completed"}.get(status, status)
        if status not in {"queued", "paused", "held", "cancelled", "completed"}:
            status = "held" if record.get("held") else "queued"
        stopped = bool(record.get("stop") or record.get("STOP") or (previous or {}).get("stop"))
        if previous and previous.get("status") in {"paused", "held"}:
            status = previous["status"]
        if stopped:
            status = "paused"
        next_revision = (previous or {}).get("revision", 0) + 1
        return {"_id": cid, "managed_by": MANAGED_BY, "concept_id": cid,
                "revision": next_revision, "status": status, "stop": stopped,
                "metadata": copy.deepcopy(record), "updated_at": self._date(), "actor": "canonical-import",
                "import_provenance": {"source_identity": source_identity,
                    "source_sha256": source_sha256, "managed_revision": next_revision}}

    def import_new_queues(self, records, source_identity):
        """Owner-local new-only queue projection; never resumes or dispatches work."""
        self._import_batch_records(records, {"concept_id", "record", "source_sha256"})
        source_identity = text(source_identity, "queue import identity", 2000)
        rows, identities = [], {}
        for entry in records:
            cid = concept_id(entry["concept_id"])
            record, checksum = entry["record"], entry["source_sha256"]
            if not isinstance(record, dict):
                raise ValueError("Imported queue record must be an object")
            record = json_value(record)
            if not isinstance(checksum, str) or not re.fullmatch(r"[0-9a-f]{64}", checksum) or digest(record) != checksum:
                raise ValueError("Import hash must match the exact queue record")
            if cid in identities:
                raise Conflict("Duplicate queue concept identity in import batch")
            identities[cid] = checksum
            rows.append(self._prepare_import_queue(cid, record, source_identity, checksum))
        rows.sort(key=lambda row: row["_id"])
        if len(canonical(rows)) > MAX_IMPORT_BATCH_BYTES:
            raise ValueError("Prepared queue import exceeds the batch byte limit")
        ids = list(identities)
        def concepts_exist(session):
            found = list(self.concepts.find({"_id": {"$in": ids}},
                {"_id": 1, "managed_by": 1, "deleted": 1}, session=session))
            if len(found) != len(ids) or any(row.get("managed_by") != MANAGED_BY or row.get("deleted") for row in found):
                raise Conflict("Queue batch requires existing managed current concepts")
        def guard(session):
            concepts_exist(session)
            if self.queue.find_one({"$or": [{"_id": {"$in": ids}},
                    {"managed_by": {"$ne": MANAGED_BY}}]}, {"_id": 1}, session=session):
                raise Conflict("An existing queue row or producer already owns this queue batch")
        def replay():
            concepts_exist(None)
            current = list(self.queue.find({"_id": {"$in": ids}}, {
                "_id": 1, "managed_by": 1, "revision": 1, "import_provenance": 1}).sort("_id", 1))
            if len(current) != len(ids):
                raise Conflict("Imported queue batch no longer has its original current rows")
            for row in current:
                provenance = row.get("import_provenance", {})
                if (row.get("managed_by") != MANAGED_BY or provenance.get("source_identity") != source_identity
                        or provenance.get("source_sha256") != identities[row["_id"]]
                        or provenance.get("managed_revision") != row.get("revision")):
                    raise Conflict("A locally edited queue row cannot be replaced by import replay")
            return self._import_batch_summary(current, replay=True)
        payload = {"source_identity": source_identity, "records": [
            {"concept_id": cid, "source_sha256": identities[cid]} for cid in sorted(identities)]}
        return self._import_batch_execute("import_new_queues", payload, rows,
            self.queue, guard, replay, extra={"projection_only": True, "dispatched": False,
                                            "affected_concepts": []})

    def queue_recover(self, concept_id, expected_queue_revision, reason,
                      actor="local-admin", request_id=""):
        """Operator-local recovery; never clears a filesystem STOP or legacy hold."""
        cid = globals()["concept_id"](concept_id)
        expected = revision(expected_queue_revision)
        reason = text(reason, "operator recovery reason", 2000)
        def recover(session):
            old = self.queue.find_one(self._owned({"_id": cid}), session=session)
            if old is None:
                raise KeyError("No such research queue entry")
            if old["revision"] != expected:
                raise Conflict("Queue revision conflict; refresh before recovery")
            if old.get("status") not in {"paused", "held"} and not old.get("stop"):
                raise Conflict("Only a held, paused, or stopped queue entry needs recovery")
            doc = {**old, "revision": expected + 1, "status": "queued", "stop": False,
                   "updated_at": self._date(), "actor": actor,
                   "recovery": {"reason": reason, "actor": actor, "at": self._date(),
                                "previous_status": old["status"], "previous_stop": old.get("stop", False)}}
            result = self.queue.replace_one(self._owned({"_id": cid, "revision": expected}), doc, session=session)
            if result.matched_count != 1:
                raise Conflict("Queue changed during operator recovery")
            return {**doc, "dispatched": False, "filesystem_stop_unchanged": True}
        return self._mutate("queue_recover", dict(concept_id=cid, expected_queue_revision=expected,
            reason=reason), actor, request_id, recover)

    def queue_list(self, filters=None, after="", limit=100):
        filters = filters or {}
        if not isinstance(filters, dict) or set(filters) - {"status", "stop"}:
            raise ValueError("Unsupported queue filter")
        query = self._owned()
        if "status" in filters:
            if filters["status"] not in {"queued", "paused", "held", "cancelled", "completed"}:
                raise ValueError("Invalid queue state")
            query["status"] = filters["status"]
        if "stop" in filters:
            if type(filters["stop"]) is not bool:
                raise ValueError("Invalid STOP filter")
            query["stop"] = filters["stop"]
        result = self._page(self.queue, query, after, limit, "queue")
        for row in result["queue"]:
            doc = self._get(row["concept_id"], deleted=True)
            lease = self.leases.find_one(self._owned({"_id": row["concept_id"], "status": "held",
                "expires_at": {"$gt": self._now()}}), {"owner": 1, "expires_at": 1, "fence": 1})
            row["concept"] = {k: doc.get(k) for k in ("name", "state", "revision", "cvs", "cvs_decision", "incomplete_reasons")}
            row["lease"] = self._public(lease)
            row["eligible"] = (row["status"] == "queued" and not row.get("stop")
                and doc.get("cvs_decision") in {"RESEARCH", "REFRESH"} and not lease
                and doc.get("state") not in {"complete", "archived"} and not doc.get("deleted"))
        result["items"] = result["queue"]
        return result

    def complete(self, concept_id, expected_revision, lease_token, receipt,
                 actor="agent", request_id=""):
        cid = globals()["concept_id"](concept_id)
        if not self.completion_verifier:
            raise ValueError("Trusted canonical publication verifier is unavailable")
        current = self._get(cid)
        if current["revision"] != revision(expected_revision):
            raise Conflict("Concept revision conflict")
        proof = self.completion_verifier(copy.deepcopy(current), copy.deepcopy(receipt))
        if not isinstance(proof, dict) or not proof:
            raise ValueError("Trusted publication proof was not accepted")
        json_value(proof)
        def finish(session):
            old = self._edit(cid, expected_revision, lease_token, session)
            if digest(old) != digest(current):
                raise Conflict("Concept changed after publication verification")
            claims = [c for c in old["claims"] if not c.get("deleted")]
            if not claims:
                raise ValueError("Completion requires factual claims")
            for claim in claims:
                if not claim.get("evidence"):
                    raise ValueError("Completion requires exact evidence for every claim")
                self._claim(old["slug"], {k: v for k, v in claim.items()
                    if k not in {"lineage_id", "claim_id", "identity", "qualification", "deleted", "evidence_integrity",
                                           "canonical_claim_id", "identity_slug"}}, session, claim["lineage_id"])
            doc = {**old, "state": "complete", "qualification": "verified",
                   "claims": [{**c, "qualification": "SUPPORTED"} if not c.get("deleted") else c
                              for c in old["claims"]],
                   "completion": {**proof, "status": "verified"}, "incomplete_reasons": []}
            saved = self._save(doc, old, actor, session, invalidate=False)
            self.queue.update_one(self._owned({"_id": cid}), {"$set": {
                "status": "completed", "concept_revision": saved["revision"], "updated_at": self._date()},
                "$inc": {"revision": 1}}, session=session)
            return self._response(saved, invalidated=False)
        return self._mutate("complete", dict(concept_id=cid, expected_revision=expected_revision,
            lease_token=lease_token, receipt=receipt), actor, request_id, finish)

    @contextmanager
    def importing(self, source_identity):
        token = self._import_context.set(text(source_identity, "import source identity", 2000))
        try:
            yield self
        finally:
            self._import_context.reset(token)

    @staticmethod
    def _import_batch_records(records, keys):
        if not isinstance(records, list) or not 1 <= len(records) <= MAX_IMPORT_BATCH:
            raise ValueError("Import batch must contain 1..100 records")
        if any(not isinstance(row, dict) or set(row) != keys for row in records):
            raise ValueError("Import batch record fields do not match the contract")
        if len(canonical(records)) > MAX_IMPORT_BATCH_BYTES:
            raise ValueError("Import batch exceeds its byte limit")

    @staticmethod
    def _import_batch_summary(rows, *, replay=False):
        ids = [row["_id"] for row in rows]
        return {"inserted": 0 if replay else len(rows), "inserted_ids": [] if replay else ids,
                "skipped_ids": ids if replay else [], "unchanged": replay,
                "revisions": {row["_id"]: row["revision"] for row in rows},
                "affected_concepts": [] if replay else [
                    {"concept_id": row["_id"], "revision": row["revision"]} for row in rows]}

    def _import_batch_execute(self, operation, payload, rows, collection, guard, replay,
                              *, versions=None, extra=None):
        """One summary receipt and two bounded writes, with no per-record I/O."""
        actor = "canonical-import"
        request_id = digest([operation, payload])
        key = "op:" + digest([actor, request_id])
        fingerprint = digest({"operation": operation, "payload": payload})
        prior = self.receipts.find_one({"_id": key})
        if prior:
            if prior.get("managed_by") != MANAGED_BY:
                raise OwnershipError("Import receipt identity belongs to another producer")
            if prior.get("request_sha256") != fingerprint:
                raise Conflict("Import receipt does not match this batch")
            return {**replay(), **(extra or {}), "request_id": request_id}
        guard(None)
        execution = secrets.token_hex(16)
        def insert(session):
            guard(session)
            collection.insert_many(copy.deepcopy(rows), ordered=True, session=session)
            if versions is not None:
                self.versions.insert_many(copy.deepcopy(versions), ordered=True, session=session)
            return {**self._import_batch_summary(rows), **(extra or {}), "_batch_execution": execution}
        result = self._mutate(operation, payload, actor, request_id, insert, raw=True)
        if result.pop("_batch_execution", None) != execution:
            # Another caller may have committed this same receipt after preflight.
            # Re-read current metadata rather than returning stale revision-one state.
            return {**replay(), **(extra or {}), "request_id": request_id}
        return self._public(result)

    def import_new_concepts(self, records, source_identity):
        """Owner-local new-only read projection; never grants research ownership.

        Like import_concept, a canonical inventory projection may describe a
        filesystem-held concept. Subsequent research/family lease acquisition
        still checks that hold. Any existing or orphan Mongo lease blocks a new
        projection, and no existing concept or alias is ever replaced here.
        """
        self._import_batch_records(records, {"document", "source_sha256"})
        source_identity = text(source_identity, "import source identity", 2000)
        allowed = {"_id", "slug", "name", "description", "aliases", "terms", "state", "cvs", "cvs_axes",
                   "cvs_rationale", "cvs_decision", "open_questions", "scope", "incomplete_reasons",
                   "metadata", "summary", "disagreements", "telemetry", "scope_assessment", "claims",
                   "source_refs", "qualification", "legacy_qualification"}
        documents, snapshots, identities, aliases = [], [], {}, set()
        for record in records:
            document, checksum = record["document"], record["source_sha256"]
            if not isinstance(document, dict) or set(document) - allowed:
                raise ValueError("New concept batch cannot contain family edits or publication proofs")
            if not isinstance(checksum, str) or not re.fullmatch(r"[0-9a-f]{64}", checksum) or digest(document) != checksum:
                raise ValueError("Import hash must match the exact concept document")
            if document.get("claims", []) != [] or document.get("source_refs", []) != []:
                raise ValueError("New concept batch must not contain claims or source references")
            if document.get("state", "frontier") not in {"frontier", "draft", "incomplete"}:
                raise ValueError("New concept batch cannot grant completion authority")
            name = text(document.get("name"), "concept name", 500)
            cid = concept_id(document.get("_id") or document.get("slug") or slugify(name))
            if document.get("slug") and concept_id(document["slug"]) != cid:
                raise ValueError("Imported slug and concept identity differ")
            if cid in identities:
                raise Conflict("Duplicate concept identity in import batch")
            doc = {"_id": cid, "slug": cid[2:], "name": name, "state": "frontier", "claims": [],
                   "source_refs": [], "parent_id": None, **{field: [] for field in RELATION_FIELDS},
                   "cvs": None, "cvs_axes": None, "cvs_decision": "REVIEW", "deleted": False,
                   "open_questions": [], "scope": {}, "description": "", "aliases": [], "terms": []}
            patch = {key: document[key] for key in allowed - {
                "_id", "slug", "state", "claims", "source_refs", "qualification", "legacy_qualification",
                "cvs_decision"} if key in document}
            doc = self._patch(doc, patch)
            doc.update(state=document.get("state", "frontier"), qualification="unreviewed",
                legacy_qualification=json_value(document.get("qualification", document.get("legacy_qualification", "unknown"))),
                import_provenance={"source_identity": source_identity, "source_sha256": checksum, "managed_revision": 1})
            doc = self._prepare_save(doc, None, "canonical-import")
            keys = set(doc["alias_keys"])
            if aliases & keys:
                raise Conflict("Duplicate concept name or alias in import batch")
            aliases.update(keys)
            identities[cid] = checksum
            documents.append(doc)
            snapshots.append(self._version_snapshot(doc, "canonical-import"))
        documents.sort(key=lambda doc: doc["_id"])
        snapshots.sort(key=lambda doc: doc["_id"])
        if len(canonical([documents, snapshots])) > MAX_IMPORT_BATCH_BYTES:
            raise ValueError("Prepared import revisions exceed the batch byte limit")
        index = self.concepts.index_information().get("research_alias_identity_v1", {})
        if (list(index.get("key", [])) != [("managed_by", 1), ("alias_keys", 1)]
                or index.get("unique") is not True
                or index.get("partialFilterExpression") != {"managed_by": MANAGED_BY}):
            raise RuntimeError("Provisioned unique research alias index is required for bulk import")
        ids = list(identities)
        version_ids = [row["_id"] for row in snapshots]
        def guard(session):
            if self.concepts.find_one({"$or": [{"_id": {"$in": ids}},
                    {"alias_keys": {"$in": sorted(aliases)}}, {"managed_by": {"$ne": MANAGED_BY}}]},
                    {"_id": 1}, session=session):
                raise Conflict("A concept identity, alias, or producer already owns this import batch")
            if self.leases.find_one({"_id": {"$in": ids}}, {"_id": 1}, session=session):
                raise LeaseConflict("An existing or orphan Mongo lease blocks this new concept batch")
            if self.versions.find_one({"_id": {"$in": version_ids}}, {"_id": 1}, session=session):
                raise Conflict("An immutable concept revision already owns this import batch")
        def replay():
            current = list(self.concepts.find({"_id": {"$in": ids}}, {
                "_id": 1, "managed_by": 1, "revision": 1, "import_provenance": 1}).sort("_id", 1))
            if len(current) != len(ids):
                raise Conflict("Imported concept batch no longer has its original current records")
            for row in current:
                provenance = row.get("import_provenance", {})
                if (row.get("managed_by") != MANAGED_BY or provenance.get("source_identity") != source_identity
                        or provenance.get("source_sha256") != identities[row["_id"]]
                        or provenance.get("managed_revision") != row.get("revision")):
                    raise Conflict("A locally edited concept cannot be replaced by import replay")
            if self.leases.find_one({"_id": {"$in": ids}, "status": "held",
                    "expires_at": {"$gt": self._now()}}, {"_id": 1}):
                raise LeaseConflict("An actively leased concept blocks this import replay")
            return self._import_batch_summary(current, replay=True)
        payload = {"source_identity": source_identity, "records": [
            {"concept_id": cid, "source_sha256": identities[cid]} for cid in sorted(identities)]}
        return self._import_batch_execute("import_new_concepts", payload, documents,
            self.concepts, guard, replay, versions=snapshots,
            extra={"qualification": "unreviewed", "dispatch_authorized": False})

    def import_concept(self, document, source_identity, source_sha256, artifact_proof=None,
                       replace_import=False):
        """Owner-local import; never exposed as a remote concept patch."""
        if not isinstance(document, dict):
            raise ValueError("Imported concept must be an object")
        source_identity = text(source_identity, "import source identity", 2000)
        if not re.fullmatch(r"[0-9a-f]{64}", source_sha256 or ""):
            raise ValueError("Import requires a source content hash")
        name = text(document.get("name"), "concept name", 500)
        cid = concept_id(document.get("_id") or document.get("slug") or slugify(name))
        # Imports are ownership-sensitive reconciliations, not blind replays of an old receipt.
        # Check live local edits/holds even if this exact source was imported previously.
        existing = self.concepts.find_one(self._owned({"_id": cid}))
        imported = (existing or {}).get("import_provenance", {})
        if existing and (imported.get("source_identity") != source_identity
                or imported.get("managed_revision") != existing["revision"]):
            raise Conflict("A locally edited concept cannot be replaced by import")
        lease_query = {"_id": cid}
        if existing:
            lease_query.update(status="held", expires_at={"$gt": self._now()})
        if self.leases.find_one(lease_query):
            raise LeaseConflict("An actively leased concept cannot be replaced by import")
        if existing and imported.get("source_sha256") == source_sha256 and not replace_import:
            return {**self._public(existing), "id": cid, "unchanged": True,
                    "affected_concepts": [], "verification_invalidated": False}
        payload = dict(concept_id=cid, source_identity=source_identity, source_sha256=source_sha256,
                       document=document, artifact_proof=artifact_proof, replace_import=bool(replace_import))
        with self.importing(source_identity):
            def load(session):
                old = self.concepts.find_one(self._owned({"_id": cid}), session=session)
                lease_query = {"_id": cid}
                if old:
                    lease_query.update(status="held", expires_at={"$gt": self._now()})
                lease = self.leases.find_one(lease_query, session=session)
                if lease:
                    raise LeaseConflict("An actively leased concept cannot be replaced by import")
                if old:
                    prior = old.get("import_provenance", {})
                    if prior.get("source_identity") != source_identity or prior.get("managed_revision") != old["revision"]:
                        raise Conflict("A locally edited concept cannot be replaced by import")
                    if prior.get("source_sha256") == source_sha256 and not replace_import:
                        return {**self._public(old), "unchanged": True}
                doc = copy.deepcopy(old) if old else {"_id": cid, "slug": cid[2:], "name": name,
                    "state": "frontier", "claims": [], "source_refs": [], "parent_id": None,
                    **{key: [] for key in RELATION_FIELDS}, "cvs": None, "cvs_axes": None,
                    "cvs_decision": "REVIEW", "deleted": False, "open_questions": [], "scope": {}}
                patch = {k: document[k] for k in ("name", "description", "aliases", "terms", "cvs", "cvs_axes",
                    "cvs_rationale", "open_questions", "scope", "incomplete_reasons", "metadata",
                    "summary", "disagreements", "telemetry", "scope_assessment") if k in document}
                doc.setdefault("description", "")
                doc.setdefault("aliases", [])
                doc.setdefault("terms", [])
                doc = self._patch(doc, patch)
                if "source_refs" in document:
                    refs = document["source_refs"]
                    if not isinstance(refs, list) or len(refs) > 1024:
                        raise ValueError("Imported source references exceed their bounds")
                    accepted = []
                    for ref in refs:
                        if not isinstance(ref, dict) or set(ref) - {"source_id", "snapshot_sha256", "url", "rationale"}:
                            raise ValueError("Imported source references require exact identities")
                        url = checked_url(ref.get("url"))
                        sid, checksum = ref.get("source_id"), ref.get("snapshot_sha256")
                        if sid != source_id(url) or not re.fullmatch(r"[0-9a-f]{64}", checksum or ""):
                            raise ValueError("Imported source reference identity does not match its URL")
                        available = False
                        try:
                            source = self._source(sid, session, deleted=True)
                            if normalize_url(source["url"]) != normalize_url(url):
                                raise ValueError("Imported source URL does not match its stored identity")
                            self._snapshot_text(sid, checksum, session)
                            available = True
                        except KeyError:
                            pass
                        accepted.append({**copy.deepcopy(ref), "snapshot_available": available})
                    doc["source_refs"] = accepted
                doc["state"] = "incomplete" if document.get("state") in {"complete", "completed", "incomplete"} else (
                    "draft" if document.get("state") == "draft" else "frontier")
                doc["qualification"] = "unreviewed"
                doc["legacy_qualification"] = json_value(document.get("qualification", document.get("legacy_qualification", "unknown")))
                doc["import_provenance"] = {"source_identity": source_identity,
                    "source_sha256": source_sha256, "managed_revision": (old or {}).get("revision", 0) + 1}
                if document.get("claims"):
                    claims = []
                    for item in document["claims"]:
                        lineage = item.get("lineage_id", "lineage:" + digest([cid, item.get("text", "")])[:32])
                        clean = {k: v for k, v in item.items() if k in {"text", "sources", "confidence", "verified_as_of", "volatile", "temporal", "evidence", "conflict"}}
                        try:
                            claims.append(self._claim(doc["slug"], clean, session, lineage))
                        except (KeyError, ValueError):
                            # Historical text is preserved as unqualified import, never fabricated evidence.
                            clean.setdefault("confidence", "unreviewed")
                            clean.setdefault("sources", [])
                            clean["text"] = text(clean.get("text"), "claim text", 32000)
                            claims.append({**clean, "lineage_id": lineage,
                                "claim_id": "clm:" + digest(self.claim_identity(doc["slug"], clean)),
                                "qualification": "unreviewed", "evidence_integrity": "unverified", "deleted": False})
                    if len(claims) > MAX_CLAIMS:
                        raise ValueError("Concept claim limit exceeded")
                    doc["claims"] = claims
                if artifact_proof and self.completion_verifier:
                    proof = self.completion_verifier(copy.deepcopy(doc), artifact_proof)
                    if isinstance(proof, dict) and proof:
                        integrity_ready = bool(doc["claims"]) and all(
                            claim.get("evidence") and claim.get("evidence_integrity") != "unverified"
                            for claim in doc["claims"] if not claim.get("deleted"))
                        if integrity_ready:
                            doc["completion"] = {**proof, "status": "verified"}
                            doc["state"] = "complete"
                            doc["qualification"] = "verified"
                            doc["claims"] = [{**claim, "qualification": "SUPPORTED"}
                                             for claim in doc["claims"]]
                            doc["incomplete_reasons"] = []
                        else:
                            doc["legacy_publication_proof"] = proof
                            doc["state"] = "incomplete"
                            doc["incomplete_reasons"] = list(dict.fromkeys([
                                *doc.get("incomplete_reasons", []), "source-snapshot-unavailable"]))
                return self._response(self._save(doc, old, "canonical-import", session,
                    invalidate=doc.get("state") != "complete"), invalidated=doc.get("state") != "complete")
            return self._mutate("import_concept", payload, "canonical-import",
                digest([cid, source_identity, source_sha256, digest(document), bool(replace_import)]), load)


def locals_payload(cid, expected_revision, lease_token):
    return dict(concept_id=cid, expected_revision=expected_revision, lease_token=lease_token)
