"""Durable orchestration records. Run leases never grant concept research authority."""
from __future__ import annotations

import base64
import copy
import hmac
import json
import math
import re
import secrets

from .models import (
    CHUNK_BYTES,
    MANAGED_BY,
    Conflict,
    LeaseConflict,
    OwnershipError,
    canonical,
    digest,
    json_value,
    revision,
    score_axes,
    text,
)

RUN_MODES = frozenset({"dr", "cfe", "rabbithole", "full-suite", "queue", "frontier"})
RUN_STATES = frozenset({"planned", "running", "paused", "blocked", "finished", "failed"})
ITEM_KINDS = frozenset({"coverage", "pass", "round", "attempt", "question", "deliverable", "selection"})
MAX_RUN_BYTES = 256 * 1024
MAX_ITEM_BYTES = 256 * 1024
MAX_ARTIFACT_BYTES = 8 * 1024 * 1024
MAX_PAGE_BYTES = 2 * 1024 * 1024
MAX_ARTIFACT_HEAD_SCAN = 1000
RUN_SCHEMA = "research-run/v1"
COLLECTIONS = ("runs", "run_versions", "run_items", "item_versions", "run_leases",
               "artifacts", "artifact_chunks", "artifact_heads")
UNVERIFIED = {"status": "unverified", "authority": "client",
              "reason": "Orchestration records do not establish research qualification"}


def _identity(value, prefix):
    if not isinstance(value, str) or not re.fullmatch(re.escape(prefix) + r"[0-9a-f]{64}", value):
        raise ValueError("Invalid " + prefix.rstrip(":") + " identity")
    return value


def _object(value, name, maximum):
    if not isinstance(value, dict):
        raise ValueError(name + " must be an object")
    value = json_value(value, maximum=maximum)
    def bson_values(item):
        if isinstance(item, dict):
            for key, val in item.items():
                if "\x00" in key:
                    raise ValueError("Invalid MongoDB JSON field")
                bson_values(val)
        elif isinstance(item, list):
            for val in item:
                bson_values(val)
        elif type(item) is int and not -(2 ** 63) <= item < 2 ** 63:
            raise ValueError("JSON integers must fit MongoDB signed 64-bit values")
    bson_values(value)
    return value


def _options(value):
    value = _object(value, "Run options", 64 * 1024)
    # Values are inert JSON. Explicitly reject operator execution/location options.
    def check(item):
        if isinstance(item, dict):
            for key, val in item.items():
                if (key.lower() in {"shell", "command", "cmd", "executable", "cwd", "directory"}
                        or re.search(r"(^|_)(path|paths|dir|shell|command|executable)($|_)", key.lower())):
                    raise ValueError("Run options cannot select local paths or commands")
                check(val)
        elif isinstance(item, list):
            for val in item:
                check(val)
    check(value)
    thresholds = [value[k] for k in ("threshold", "cvs_threshold") if k in value]
    if any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 5
           for v in thresholds) or len(set(thresholds)) > 1:
        raise ValueError("Run CVS threshold must be one number in 0..5")
    return value


def _page_limit(value):
    if type(value) is not int or not 1 <= value <= 100:
        raise ValueError("Page limit must be 1..100")
    return value


class ResearchRunStore:
    """Compose with the configured LibraryStore; never open a second Mongo connection."""

    def __init__(self, store):
        self.store = store
        for name in COLLECTIONS:
            setattr(self, name, store.database[store.prefix + name])

    def _owned(self, extra=None):
        return self.store._owned(extra)

    def _claim(self, collection, key, session):
        row = collection.find_one({"_id": key}, session=session)
        if row is not None and row.get("managed_by") != MANAGED_BY:
            raise OwnershipError("Run storage identity is already owned")
        return row

    def provision(self):
        """Operator-only namespace/index creation; readers do not call this method."""
        for name in COLLECTIONS:
            collection = getattr(self, name)
            if collection.name not in self.store.database.list_collection_names():
                try:
                    self.store.database.create_collection(collection.name)
                except Exception:
                    if collection.name not in self.store.database.list_collection_names():
                        raise
        for collection, fields in (
            (self.runs, [("mode", 1), ("state", 1), ("_id", 1)]),
            (self.run_versions, [("run_id", 1), ("revision", 1)]),
            (self.run_items, [("run_id", 1), ("kind", 1), ("_id", 1)]),
            (self.item_versions, [("run_id", 1), ("key", 1), ("revision", 1)]),
            (self.run_leases, [("status", 1), ("expires_at", 1)]),
            (self.artifacts, [("run_id", 1), ("kind", 1), ("_id", 1)]),
            (self.artifact_heads, [("run_id", 1), ("name", 1)]),
        ):
            collection.create_index([("managed_by", 1), *fields])
        def marker(session):
            key = "run-storage/v1"
            if self._claim(self.store.meta, key, session) is None:
                self.store.meta.insert_one({"_id": key, "managed_by": MANAGED_BY,
                    "schema": RUN_SCHEMA}, session=session)
            return {"schema": RUN_SCHEMA, "collections": list(COLLECTIONS)}
        return self.store._tx(marker)

    def _get(self, run_id, session=None):
        rid = _identity(run_id, "run:")
        row = self.runs.find_one(self._owned({"_id": rid}), session=session)
        if row is None:
            raise KeyError("No such managed research run")
        return row

    def _catalog(self, session=None):
        row = self.store.meta.find_one(self._owned({"_id": "run-catalog"}), session=session)
        return (row or {}).get("revision", 0)

    def _increment_catalog(self, session):
        self._claim(self.store.meta, "run-catalog", session)
        self.store.meta.update_one(self._owned({"_id": "run-catalog"}),
            {"$setOnInsert": {"managed_by": MANAGED_BY}, "$inc": {"revision": 1}},
            upsert=True, session=session)

    def _reserve_catalog_revision(self, rid, session):
        # Reserve the existing increment before the authorized write's body work.
        # The transaction still commits it atomically with the matching run save.
        # Per-attempt credits disappear on abort/retry with the store's frame.
        frame = self.store._evidence_context.get()
        if frame is not None and frame.get("session") is session:
            self._increment_catalog(session)
            credits = frame.setdefault("run_catalog_credits", {})
            credits[rid] = credits.get(rid, 0) + 1

    def _save(self, row, previous, actor, session):
        row = copy.deepcopy(row)
        rid = row["_id"]
        frame = self.store._evidence_context.get()
        credits = (frame.get("run_catalog_credits", {}) if frame is not None
                   and frame.get("session") is session else {})
        if credits.get(rid, 0):
            credits[rid] -= 1
        else:
            # Take the shared catalog write before run/version writes establish a
            # longer conflict window. The outer transaction rolls everything back.
            self._increment_catalog(session)
        row.update(managed_by=MANAGED_BY, schema=RUN_SCHEMA,
                   revision=(previous or {}).get("revision", 0) + 1,
                   updated_at=self.store._date(), qualification=copy.deepcopy(UNVERIFIED))
        row.setdefault("created_at", row["updated_at"])
        if len(canonical(row)) > MAX_RUN_BYTES:
            raise ValueError("Run document exceeds its byte limit")
        if previous is None:
            self._claim(self.runs, rid, session)
            self.runs.insert_one(row, session=session)
        else:
            changed = self.runs.replace_one(self._owned({"_id": rid,
                "revision": previous["revision"]}), row, session=session)
            if changed.matched_count != 1:
                raise Conflict("Run revision conflict; refresh before editing")
        self.run_versions.insert_one({**copy.deepcopy(row), "_id": f"{rid}@{row['revision']}",
            "run_id": rid, "actor": actor, "content_sha256": digest(row)}, session=session)
        return row

    def _token(self, lease, secret):
        value = canonical(["run-lease/v1", lease["_id"], lease["owner"],
                           lease["fence"], lease["nonce"]])
        return "rr:" + hmac.digest(bytes.fromhex(secret), value, "sha256").hex()

    def _new_lease(self, rid, owner, ttl, session):
        old = self._claim(self.run_leases, rid, session)
        if old and old.get("status") == "held" and old["expires_at"] > self.store._now():
            raise LeaseConflict("Run is already leased; only its owner can renew it")
        row = {"_id": rid, "managed_by": MANAGED_BY, "run_id": rid, "owner": owner,
               "status": "held", "fence": (old or {}).get("fence", 0) + 1,
               "nonce": secrets.token_hex(16), "acquired_at": self.store._now(),
               "expires_at": self.store._now() + ttl, "uses": 0}
        row["token_hash"] = digest(self._token(row, self.store._key(session)).encode())
        self.run_leases.replace_one(self._owned({"_id": rid}), row, upsert=True, session=session)
        return row

    def _check_lease(self, rid, token, owner, session):
        lease = self.run_leases.find_one(self._owned({"_id": rid}), session=session)
        if (not isinstance(token, str) or len(token) > 256 or lease is None
                or lease.get("status") != "held" or lease["owner"] != owner
                or lease["expires_at"] <= self.store._now()
                or not hmac.compare_digest(lease["token_hash"], digest(token.encode()))):
            raise LeaseConflict("The run lease is missing, expired, or no longer owned")
        changed = self.run_leases.update_one(self._owned({"_id": rid, "owner": owner,
            "fence": lease["fence"], "token_hash": lease["token_hash"], "status": "held",
            "expires_at": {"$gt": self.store._now()}}), {"$inc": {"uses": 1}}, session=session)
        if changed.matched_count != 1:
            raise LeaseConflict("The run lease changed during this operation")
        return lease

    def _edit(self, rid, expected, token, owner, session):
        expected = revision(expected)
        row = self._get(rid, session)
        if row["revision"] != expected:
            raise Conflict("Run revision conflict; refresh before editing")
        self._check_lease(rid, token, owner, session)
        return row

    def _with_token(self, result):
        public = self.store._public(result)
        lease = result.get("lease")
        if lease and lease.get("status") == "held":
            key = self.store.meta.find_one(self._owned({"_id": "lease-token-key"}))
            public["lease_token"] = self._token(lease, key["secret"])
        return public

    @staticmethod
    def _fenced_payload(lease_token, **fields):
        # Receipts fingerprint the credential without retaining the raw token.
        if not isinstance(lease_token, str) or len(lease_token) > 256:
            raise LeaseConflict("An owned active run lease is required")
        return {**fields, "lease_token_sha256": digest(lease_token.encode())}

    def run_create(self, mode, subject, prompt, owner, options=None, scope=None, request_id="",
                   actor="agent"):
        if not isinstance(mode, str) or mode not in RUN_MODES:
            raise ValueError("Invalid research run mode")
        subject, prompt = text(subject, "run subject", 2000), text(prompt, "run prompt", 65536)
        owner = text(owner, "run owner", 200)
        options = _options(options if options is not None else {})
        scope = _object(scope if scope is not None else {}, "Run scope", 64 * 1024)
        def create(session):
            rid = "run:" + secrets.token_hex(32)
            row = self._save({"_id": rid, "mode": mode, "subject": subject, "prompt": prompt,
                "owner": owner, "options": options, "scope": scope, "checkpoint": {},
                "state": "planned"}, None, actor, session)
            return {"run": row, "lease": self._new_lease(rid, owner, 900, session)}
        result = self.store._mutate("run_create", dict(mode=mode, subject=subject, prompt=prompt,
            owner=owner, options=options, scope=scope), actor, request_id, create, raw=True)
        return self._with_token(result)

    def run_get(self, run_id, revision=None):
        rid = _identity(run_id, "run:")
        if revision is None:
            return self.store._public(self._get(rid))
        globals()["revision"](revision)
        row = self.run_versions.find_one(self._owned({"_id": f"{rid}@{revision}"}))
        if row is None:
            raise KeyError("No such managed research run revision")
        return self.store._public(row)

    @staticmethod
    def _cursor(scope, generation, last):
        return base64.urlsafe_b64encode(canonical({"scope": digest(scope), "revision": generation,
                                                  "last": last})).decode().rstrip("=")

    @staticmethod
    def _after(after, scope, generation):
        if not isinstance(after, str) or len(after) > 2048:
            raise ValueError("Invalid run cursor")
        if not after:
            return ""
        try:
            value = json.loads(base64.b64decode(after + "=" * (-len(after) % 4),
                                               altchars=b"-_", validate=True))
            if (not isinstance(value, dict) or set(value) != {"scope", "revision", "last"}
                    or value["scope"] != digest(scope) or not isinstance(value["last"], str)):
                raise ValueError
        except (ValueError, TypeError, UnicodeError) as exc:
            raise ValueError("Invalid or differently scoped run cursor") from exc
        if value["revision"] != generation:
            raise Conflict("Run listing changed; restart pagination")
        return value["last"]

    def _page(self, collection, query, scope, generation, after, limit, label, current):
        limit = _page_limit(limit)
        last = self._after(after, scope, generation)
        if last:
            query = {**query, "_id": {"$gt": last}}
        rows, used, more = [], 0, False
        for row in collection.find(query).sort("_id", 1).limit(limit + 1):
            size = len(canonical(row))
            if len(rows) >= limit or used + size > MAX_PAGE_BYTES:
                more = True
                break
            rows.append(self.store._public(row))
            used += size
        if current() != generation:
            raise Conflict("Run listing changed; restart pagination")
        return {label: rows, "next_after": self._cursor(scope, generation, rows[-1]["_id"])
                if more and rows else "", "revision": generation}

    def run_list(self, mode="", status="", after="", limit=100):
        if (not isinstance(mode, str) or not isinstance(status, str)
                or mode and mode not in RUN_MODES or status and status not in RUN_STATES):
            raise ValueError("Invalid run listing filter")
        query = self._owned()
        if mode:
            query["mode"] = mode
        if status:
            query["state"] = status
        return self._page(self.runs, query, ["runs", mode, status], self._catalog(), after,
                          limit, "runs", self._catalog)

    def run_checkpoint(self, run_id, patch, expected_revision, lease_token, owner, request_id="",
                       actor="agent"):
        rid, owner = _identity(run_id, "run:"), text(owner, "run owner", 200)
        patch = _object(patch, "Run patch", MAX_RUN_BYTES)
        if not patch or set(patch) - {"prompt", "scope", "options", "checkpoint", "state"}:
            raise ValueError("Invalid run patch fields")
        if "prompt" in patch:
            text(patch["prompt"], "run prompt", 65536)
        if "state" in patch and (not isinstance(patch["state"], str)
                                 or patch["state"] not in RUN_STATES):
            raise ValueError("Invalid research run state")
        for field, maximum in (("scope", 64 * 1024), ("checkpoint", 128 * 1024)):
            if field in patch:
                _object(patch[field], "Run " + field, maximum)
        if "options" in patch:
            patch["options"] = _options(patch["options"])
        def change(session):
            old = self._edit(rid, expected_revision, lease_token, owner, session)
            self._reserve_catalog_revision(rid, session)
            return {"run": self._save({**old, **patch}, old, actor, session)}
        return self.store._mutate("run_checkpoint", self._fenced_payload(lease_token,
            run_id=rid, patch=patch, expected_revision=expected_revision, owner=owner),
            actor, request_id, change)

    def run_lease(self, run_id, action, owner, token="", ttl_seconds=900,
                  expected_revision=None, request_id="", actor="agent"):
        rid, owner = _identity(run_id, "run:"), text(owner, "run owner", 200)
        if not isinstance(action, str) or action not in {"acquire", "renew", "release"}:
            raise ValueError("Invalid run lease action")
        ttl = self.store._ttl(ttl_seconds)
        if expected_revision is not None:
            revision(expected_revision)
        def change(session):
            row = self._get(rid, session)
            if expected_revision is not None and row["revision"] != expected_revision:
                raise Conflict("Run revision conflict; refresh before editing")
            if action == "acquire":
                lease = self._new_lease(rid, owner, ttl, session)
            else:
                lease = self._check_lease(rid, token, owner, session)
                lease = {**lease, "expires_at": self.store._now() + ttl if action == "renew"
                         else self.store._now(), "status": "held" if action == "renew" else "released",
                         "uses": lease.get("uses", 0) + 1}
                changed = self.run_leases.replace_one(self._owned({"_id": rid,
                    "fence": lease["fence"], "token_hash": lease["token_hash"]}), lease, session=session)
                if changed.matched_count != 1:
                    raise LeaseConflict("The run lease changed during this operation")
            return {"run": row, "lease": lease}
        result = self.store._mutate("run_lease", self._fenced_payload(token, run_id=rid,
            action=action, owner=owner, ttl_seconds=ttl, expected_revision=expected_revision),
            actor, request_id, change, raw=True)
        return self._with_token(result)

    @staticmethod
    def _assessment(data, options):
        if "cvs_axes" not in data and "axes" not in data:
            return None
        score = score_axes(data.get("cvs_axes", data.get("axes")))
        threshold = options.get("threshold", options.get("cvs_threshold", 3.2))
        worthwhile = (score["cvs"] is not None and score["cvs_decision"] != "SKIP"
                      and score["cvs"] >= threshold)
        return {**score, "threshold": threshold, "worthwhile": worthwhile,
                "run_decision": "RESEARCH" if worthwhile else
                ("SKIP" if score["cvs_decision"] == "SKIP" else "REVIEW")}

    def run_item_put(self, run_id, key, kind, data, expected_revision, lease_token, owner,
                     request_id="", actor="agent"):
        rid, owner = _identity(run_id, "run:"), text(owner, "run owner", 200)
        key = text(key, "ledger key", 500)
        if not isinstance(kind, str) or kind not in ITEM_KINDS:
            raise ValueError("Invalid run ledger kind")
        data = _object(data, "Ledger data", MAX_ITEM_BYTES - 8192)
        def change(session):
            old = self._edit(rid, expected_revision, lease_token, owner, session)
            iid = "item:" + digest([rid, key])
            prior = self._claim(self.run_items, iid, session)
            if prior and prior["kind"] != kind:
                raise Conflict("A ledger key cannot change its kind")
            row = {"_id": iid, "managed_by": MANAGED_BY, "run_id": rid, "key": key,
                   "kind": kind, "data": data, "revision": (prior or {}).get("revision", 0) + 1,
                   "run_revision": old["revision"] + 1, "updated_at": self.store._date(),
                   "qualification": copy.deepcopy(UNVERIFIED)}
            row["created_at"] = (prior or {}).get("created_at", row["updated_at"])
            assessment = self._assessment(data, old["options"]) if kind in {"coverage", "selection"} else None
            if assessment is not None:
                row["assessment"] = assessment
            if len(canonical(row)) > MAX_ITEM_BYTES:
                raise ValueError("Run ledger row exceeds its byte limit")
            if prior:
                changed = self.run_items.replace_one(self._owned({"_id": iid,
                    "revision": prior["revision"]}), row, session=session)
                if changed.matched_count != 1:
                    raise Conflict("Run ledger revision conflict")
            else:
                self.run_items.insert_one(row, session=session)
            self.item_versions.insert_one({**copy.deepcopy(row), "_id": f"{iid}@{row['revision']}",
                "item_id": iid, "actor": actor, "content_sha256": digest(row)}, session=session)
            return {"item": row, "run": self._save(old, old, actor, session)}
        return self.store._mutate("run_item_put", self._fenced_payload(lease_token,
            run_id=rid, key=key, kind=kind, data=data, expected_revision=expected_revision, owner=owner),
            actor, request_id, change)

    def run_ledger(self, run_id, kind="", after="", limit=100):
        rid = _identity(run_id, "run:")
        if not isinstance(kind, str) or kind and kind not in ITEM_KINDS:
            raise ValueError("Invalid run ledger kind")
        generation = self._get(rid)["revision"]
        query = self._owned({"run_id": rid, **({"kind": kind} if kind else {})})
        return self._page(self.run_items, query, ["ledger", rid, kind], generation, after,
                          limit, "items", lambda: self._get(rid)["revision"])

    @staticmethod
    def _artifact_input(name, kind, body, metadata):
        name = text(name, "artifact name", 200)
        if "/" in name or "\\" in name or name in {".", ".."}:
            raise ValueError("Artifact names cannot be file paths")
        kind = text(kind, "artifact kind", 100)
        if not re.fullmatch(r"[a-z][a-z0-9_-]{0,99}", kind):
            raise ValueError("Invalid artifact kind")
        body = text(body, "artifact text", MAX_ARTIFACT_BYTES, empty=True)
        raw = body.encode("utf-8")
        if len(raw) > MAX_ARTIFACT_BYTES:
            raise ValueError("Artifact UTF-8 text exceeds its byte limit")
        return name, kind, raw, _object(metadata if metadata is not None else {},
                                       "Artifact metadata", 32 * 1024)

    def _store_artifact(self, old, name, kind, raw, metadata, provenance, actor, session):
        self._reserve_catalog_revision(old["_id"], session)
        sha = digest(raw)
        identity = {"run_id": old["_id"], "name": name, "kind": kind,
                    "body_utf8_sha256": sha, "metadata": metadata,
                    "trusted_provenance": provenance}
        aid = "art:" + digest(identity)
        # Reserve the shared catalog before transferring artifact chunks. A late
        # catalog write can lose to unrelated runs for the entire upload window.
        # All writes still commit or roll back in this same transaction.
        saved = self._save(old, old, actor, session)
        prior = self._claim(self.artifacts, aid, session)
        chunks, expected = [], {}
        for start in range(0, len(raw), CHUNK_BYTES):
            chunk = raw[start:start + CHUNK_BYTES]
            cid = "chunk:" + digest(chunk)
            expected[cid] = {"_id": cid, "managed_by": MANAGED_BY,
                "data": chunk, "byte_count": len(chunk), "sha256": digest(chunk)}
            chunks.append(cid)
        # An artifact has at most sixteen bounded chunks. Read them together,
        # including foreign collisions, before inserting only missing bodies.
        found = {}
        existing_chunks = (self.artifact_chunks.find({"_id": {"$in": list(expected)}}, session=session)
                           if expected else ())
        for existing in existing_chunks:
            cid = existing.get("_id")
            if cid not in expected or cid in found:
                raise Conflict("Unexpected stored artifact chunk identity")
            if existing.get("managed_by") != MANAGED_BY:
                raise OwnershipError("Run storage identity is already owned")
            wanted = expected[cid]
            if (bytes(existing.get("data", b"")) != wanted["data"]
                    or existing.get("sha256") != wanted["sha256"]
                    or existing.get("byte_count") != wanted["byte_count"]):
                raise Conflict("Stored artifact chunk checksum mismatch")
            found[cid] = existing
        missing = [value for cid, value in expected.items() if cid not in found]
        if missing:
            try:
                self.artifact_chunks.insert_many(missing, ordered=True, session=session)
            except Exception as exc:
                from pymongo.errors import BulkWriteError, DuplicateKeyError, OperationFailure
                details = getattr(exc, "details", None)
                errors = details.get("writeErrors", []) if isinstance(details, dict) else []
                codes = {getattr(exc, "code", None)} | {
                    row.get("code") for row in errors if isinstance(row, dict)}
                if isinstance(exc, (BulkWriteError, DuplicateKeyError)) and codes & {11000, 11001}:
                    # Restart the fenced transaction and validate the winner.
                    raise OperationFailure("Concurrent immutable artifact insertion", code=112) from None
                raise
        manifest = {**identity, "_id": aid, "managed_by": MANAGED_BY, "encoding": "utf-8",
                    "byte_count": len(raw), "chunks": chunks, "created_at": self.store._date(),
                    "qualification": copy.deepcopy(UNVERIFIED) if provenance is False else
                    {"status": "trusted-archive", "authority": "trusted-publisher"}}
        if prior is None:
            self.artifacts.insert_one(manifest, session=session)
        else:
            if ({key: val for key, val in prior.items() if key != "created_at"}
                    != {key: val for key, val in manifest.items() if key != "created_at"}):
                raise Conflict("Stored artifact manifest checksum mismatch")
            manifest = prior
        hid = "head:" + digest([old["_id"], name])
        self._claim(self.artifact_heads, hid, session)
        self.artifact_heads.replace_one(self._owned({"_id": hid}), {"_id": hid,
            "managed_by": MANAGED_BY, "run_id": old["_id"], "name": name, "artifact_id": aid,
            "kind": kind, "body_utf8_sha256": sha,
            "run_revision": old["revision"] + 1}, upsert=True, session=session)
        return {"artifact": manifest, "run": saved}

    def artifact_put(self, run_id, name, kind, text, expected_revision, lease_token, owner,
                     metadata=None, request_id="", actor="agent"):
        rid, owner = _identity(run_id, "run:"), globals()["text"](owner, "run owner", 200)
        name, kind, raw, metadata = self._artifact_input(name, kind, text, metadata)
        def change(session):
            old = self._edit(rid, expected_revision, lease_token, owner, session)
            return self._store_artifact(old, name, kind, raw, metadata, False, actor, session)
        return self.store._mutate("artifact_put", self._fenced_payload(lease_token, run_id=rid,
            name=name, kind=kind, body_utf8_sha256=digest(raw), metadata=metadata,
            expected_revision=expected_revision, owner=owner), actor, request_id, change)

    def _archive_artifact(self, run_id, name, kind, text, *, provenance, metadata=None,
                          owner="trusted-publisher", request_id="", actor="trusted-publisher",
                          expected_revision=None, lease_token=None, lease_owner=None,
                          precondition=None):
        """Trusted in-process publisher only. This method must never be remotely allowlisted."""
        rid = _identity(run_id, "run:")
        owner = globals()["text"](owner, "archive owner", 200)
        provenance = _object(provenance, "Trusted artifact provenance", 32 * 1024)
        if not provenance:
            raise ValueError("Trusted archive provenance is required")
        if precondition is not None and not callable(precondition):
            raise ValueError("Trusted archive precondition must be callable")
        guarded = any(value is not None for value in (expected_revision, lease_token, lease_owner))
        if guarded:
            if any(value is None for value in (expected_revision, lease_token, lease_owner)):
                raise ValueError("Trusted archive requires all three run lease preconditions")
            revision(expected_revision)
            lease_owner = globals()["text"](lease_owner, "run lease owner", 200)
            self._fenced_payload(lease_token)
        name, kind, raw, metadata = self._artifact_input(name, kind, text, metadata)
        def change(session):
            old = (self._edit(rid, expected_revision, lease_token, lease_owner, session)
                   if guarded else self._get(rid, session))
            if precondition is not None:
                precondition(session)
            return self._store_artifact(old, name, kind, raw, metadata,
                                        provenance, actor, session)
        payload = dict(run_id=rid, name=name, kind=kind, body_utf8_sha256=digest(raw),
                       metadata=metadata, provenance=provenance, owner=owner)
        if guarded:
            payload = self._fenced_payload(lease_token, **payload,
                expected_revision=expected_revision, lease_owner=lease_owner)
        return self.store._mutate("trusted_artifact_archive", payload, actor, request_id, change)

    def _artifact_manifest(self, artifact_id, session=None):
        """Verify bounded manifest metadata without materializing its body chunks."""
        aid = _identity(artifact_id, "art:")
        manifest = self.artifacts.find_one(self._owned({"_id": aid}), session=session)
        if manifest is None:
            raise KeyError("No such managed research artifact")
        if (manifest.get("encoding") != "utf-8" or type(manifest.get("byte_count")) is not int
                or not 0 <= manifest["byte_count"] <= MAX_ARTIFACT_BYTES
                or not isinstance(manifest.get("chunks"), list)
                or len(manifest["chunks"]) > (MAX_ARTIFACT_BYTES + CHUNK_BYTES - 1) // CHUNK_BYTES):
            raise Conflict("Invalid stored artifact manifest")
        try:
            identity = {key: manifest[key] for key in ("run_id", "name", "kind", "body_utf8_sha256",
                                                      "metadata", "trusted_provenance")}
            _identity(identity["run_id"], "run:")
            _identity("chunk:" + identity["body_utf8_sha256"], "chunk:")
            self._artifact_input(identity["name"], identity["kind"], "", identity["metadata"])
            if identity["trusted_provenance"] is not False:
                if not _object(identity["trusted_provenance"], "Trusted artifact provenance", 32 * 1024):
                    raise ValueError("Missing trusted provenance")
            for cid in manifest["chunks"]:
                _identity(cid, "chunk:")
            if len(canonical(manifest)) > MAX_ITEM_BYTES:
                raise ValueError("Oversized artifact manifest")
        except (KeyError, TypeError, ValueError) as exc:
            raise Conflict("Invalid stored artifact manifest") from exc
        if "art:" + digest(identity) != aid:
            raise Conflict("Stored artifact manifest checksum mismatch")
        return manifest

    def _artifact_text(self, artifact_id, session=None):
        """Read and verify the whole immutable body for trusted in-process consumers."""
        manifest = self._artifact_manifest(artifact_id, session=session)
        identities = set(manifest["chunks"])
        found = {}
        stored_chunks = (self.artifact_chunks.find({"_id": {"$in": list(identities)}}, session=session)
                         if identities else ())
        for chunk in stored_chunks:
            cid = chunk.get("_id")
            if cid not in identities or cid in found:
                raise Conflict("Unexpected stored artifact chunk identity")
            if chunk.get("managed_by") != MANAGED_BY:
                raise Conflict("Stored artifact chunk is missing or invalid")
            found[cid] = chunk
        blocks = []
        for cid in manifest["chunks"]:
            _identity(cid, "chunk:")
            chunk = found.get(cid)
            if chunk is None or not isinstance(chunk.get("data"), bytes):
                raise Conflict("Stored artifact chunk is missing or invalid")
            raw = bytes(chunk["data"])
            if (len(raw) > CHUNK_BYTES or chunk.get("byte_count") != len(raw)
                    or chunk.get("sha256") != digest(raw) or cid != "chunk:" + digest(raw)):
                raise Conflict("Stored artifact chunk checksum mismatch")
            blocks.append(raw)
        raw = b"".join(blocks)
        if len(raw) != manifest["byte_count"] or digest(raw) != manifest["body_utf8_sha256"]:
            raise Conflict("Stored artifact body checksum mismatch")
        try:
            body = raw.decode("utf-8")
        except UnicodeError as exc:
            raise Conflict("Stored artifact is not valid UTF-8") from exc
        return manifest, body

    def artifact_get(self, artifact_id, offset=0, max_chars=16000):
        if (type(offset) is not int or not 0 <= offset <= MAX_ARTIFACT_BYTES
                or type(max_chars) is not int or not 1 <= max_chars <= 16000):
            raise ValueError("Invalid artifact text window")
        manifest, body = self._artifact_text(artifact_id)
        return {"artifact": self.store._public(manifest), "text": body[offset:offset + max_chars],
                "offset": offset, "next_offset": min(offset + max_chars, len(body)),
                "total_chars": len(body), "done": offset + max_chars >= len(body)}

    def artifact_list(self, run_id, kind="", after="", limit=100):
        rid = _identity(run_id, "run:")
        if not isinstance(kind, str):
            raise ValueError("Invalid artifact kind")
        if kind:
            text(kind, "artifact kind", 100)
        limit = _page_limit(limit)
        generation = self._get(rid)["revision"]
        scope = ["artifact-heads/v1", rid, kind]
        last = self._after(after, scope, generation)
        if last:
            _identity(last, "head:")
        query = self._owned({"run_id": rid, **({"_id": {"$gt": last}} if last else {})})
        rows, used, scanned, more = [], 0, 0, False
        for head in self.artifact_heads.find(query).sort("_id", 1).limit(MAX_ARTIFACT_HEAD_SCAN + 1):
            if scanned >= MAX_ARTIFACT_HEAD_SCAN:
                more = True
                break
            try:
                name = text(head["name"], "artifact head name", 200)
                if (head["_id"] != "head:" + digest([rid, name])
                        or type(head["run_revision"]) is not int
                        or not 1 <= head["run_revision"] <= generation):
                    raise ValueError("Invalid head identity or revision")
                manifest = self._artifact_manifest(head["artifact_id"])
            except (KeyError, TypeError, ValueError) as exc:
                raise Conflict("Current artifact head or manifest is invalid") from exc
            if (manifest["run_id"] != rid or manifest["name"] != name
                    or head.get("kind", manifest["kind"]) != manifest["kind"]
                    or head.get("body_utf8_sha256", manifest["body_utf8_sha256"])
                    != manifest["body_utf8_sha256"]):
                raise Conflict("Current artifact head does not match its manifest")
            if not kind or manifest["kind"] == kind:
                size = len(canonical(manifest))
                if len(rows) >= limit or used + size > MAX_PAGE_BYTES:
                    more = True
                    break
                rows.append(self.store._public(manifest))
                used += size
            last, scanned = head["_id"], scanned + 1
        if self._get(rid)["revision"] != generation:
            raise Conflict("Run listing changed; restart pagination")
        return {"artifacts": rows, "next_after": self._cursor(scope, generation, last)
                if more and last else "", "revision": generation}
