"""Private MongoDB skill snapshots and native Voyage automated-embedding search.

Source files remain authoritative for installed skills. MongoDB holds complete,
hash-pinned distribution snapshots; no reader needs a source filesystem mount.
Only documents marked with ``MANAGED_BY`` belong to this subsystem.
"""

from __future__ import annotations

import base64
import copy
import math
import mimetypes
import os
import re
import stat
import threading
import time
import unicodedata
from collections import OrderedDict
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

from .catalog import Catalog, _codex_disabled, _frontmatter, _root_access, _unavailable_alias
from .routing_score import routing_score
from .util import canonical, read_bounded, sha

MANAGED_BY = "skill-registry/v1"
SCHEMA = "mongo-skill/v1"
DATABASE = "ESRE-TAM"
COLLECTION = "skills"
MODEL = "voyage-4"
VECTOR_INDEX = "skill_registry_voyage4_v1"
LEXICAL_INDEX = "skill_registry_text_v1"
MAX_GUIDE_BYTES = 2 * 1024 * 1024
MAX_RESOURCE_BYTES = 32 * 1024 * 1024
MAX_SKILL_BYTES = 256 * 1024 * 1024
MAX_RESOURCE_FILES = 4096
RESOURCE_CHUNK_BYTES = 512 * 1024
MAX_SEARCH_BYTES = 30000  # Conservative UTF-8 budget below the 32k-token model window.
MAX_QUERY_CHARS = 2000
MAX_PAGE_CHARS = 32000
MAX_DISCOVERY_DIRS = 20000
MAX_BULK_BYTES = 4 * 1024 * 1024
MAX_BULK_GUIDES = 100
MAX_RESOURCE_BULK_BYTES = 512 * 1024
MAX_CONTENT_CACHE_BYTES = 64 * 1024 * 1024

VECTOR_DEFINITION = {"fields": [
    {"type": "autoEmbed", "modality": "text", "path": "search_text", "model": MODEL},
    {"type": "filter", "path": "managed_by"},
    {"type": "filter", "path": "searchable"},
    {"type": "filter", "path": "active"},
]}
LEXICAL_DEFINITION = {"mappings": {"dynamic": False, "fields": {
    "name": {"type": "string", "analyzer": "lucene.standard"},
    "description": {"type": "string", "analyzer": "lucene.standard"},
    "search_text": {"type": "string", "analyzer": "lucene.standard"},
    "managed_by": {"type": "token"},
    "searchable": {"type": "boolean"},
    "active": {"type": "boolean"},
}}}
SEARCH_INDEXES = {
    VECTOR_INDEX: {"type": "vectorSearch", "definition": VECTOR_DEFINITION},
    LEXICAL_INDEX: {"type": "search", "definition": LEXICAL_DEFINITION},
}
_MISSING = object()
_GENERATED_FIELDS = {"managed_by", "schema", "sha256", "release_sha256", "guide", "resources",
    "distribution_sha256", "exclusions", "resource_complete", "search_text", "search_text_truncated",
    "active", "created_at", "updated_at", "embedding"}
_LOCAL_METADATA_FIELDS = ("name", "name_folded", "description", "version", "metadata",
                          "activation", "validation_error")


def _local_publication(existing: dict | None, doc: dict, files: list[dict], release: str) -> list[str]:
    """Keep DB edits, allow exact local ancestry or lossless legacy additions."""
    binding_fields = {"guide_sha256", "release_sha256", "metadata_sha256", "source_sha256"}
    source_input = {key: value for key, value in doc["source"].items() if key not in binding_fields}
    if existing is None:
        doc["source"].update(guide_sha256=files[0]["sha256"], release_sha256=release,
            metadata_sha256=sha(canonical({key: doc.get(key) for key in _LOCAL_METADATA_FIELDS})),
            source_sha256=sha(canonical(source_input)))
        return []
    reasons = []
    previous_source = existing.get("source", {})
    source = doc["source"]
    # Keep original alias records, including labels and harness controls. Add
    # newly discovered aliases without interpreting their presence as removal.
    aliases = list(existing.get("installations", []))
    paths = {alias.get("path") for alias in aliases}
    aliases.extend(alias for alias in doc.get("installations", []) if alias.get("path") not in paths)
    doc["installations"] = aliases
    for key, value in existing.items():
        if key not in _GENERATED_FIELDS and key not in doc:
            doc[key] = value
    previous_input = {key: value for key, value in previous_source.items() if key not in binding_fields}
    if (previous_input != source_input
            and previous_source.get("source_sha256") != sha(canonical(previous_input))):
        reasons.append("existing-local-source-override")
    if existing.get("sha256") == files[0]["sha256"]:
        if any(existing.get(key) != doc.get(key) for key in _LOCAL_METADATA_FIELDS):
            reasons.append("existing-local-metadata-override")
    else:
        if previous_source.get("guide_sha256") != existing.get("sha256"):
            reasons.append("existing-divergent-or-unbound-guide")
        previous_metadata = sha(canonical({key: existing.get(key) for key in _LOCAL_METADATA_FIELDS}))
        if previous_source.get("metadata_sha256") != previous_metadata:
            reasons.append("existing-divergent-or-unbound-metadata")
    if existing.get("release_sha256") != release:
        bound = previous_source.get("release_sha256") == existing.get("release_sha256")
        if not bound:
            candidate = {entry.get("path"): entry for entry in files}
            # Every old manifest member must survive byte-for-byte, including
            # path, hash, byte length, media type, chunking and executable bit.
            monotonic = (existing.get("sha256") == files[0]["sha256"]
                and bool(existing.get("resources"))
                and all(candidate.get(entry.get("path")) == entry
                        for entry in existing.get("resources", [])))
            if not monotonic:
                reasons.append("existing-divergent-or-unbound-resources")
        if not reasons:
            source.update(guide_sha256=files[0]["sha256"], release_sha256=release)
    else:
        # Do not turn unchanged legacy heads into a mass metadata migration.
        for key in binding_fields:
            if key in previous_source:
                source[key] = previous_source[key]
    if not reasons and (existing.get("release_sha256") != release
                        or "metadata_sha256" in previous_source):
        source["metadata_sha256"] = sha(canonical({key: doc.get(key) for key in _LOCAL_METADATA_FIELDS}))
        source["source_sha256"] = sha(canonical(source_input))
    return reasons

EXCLUDED_NAMES = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
    ".ruff_cache", ".cache", ".DS_Store", "dist", "build", "backups", ".trash",
    "credentials.json", "auth.json", "secrets.json", "token.json", "tokens.json",
    "id_rsa", "id_ed25519", "registry-manifest.json",
}
SECRET_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".keystore"}
_FIXTURE_DIRS = {"fixtures", "testdata", "test-data", "test_fixtures", "eval-fixtures"}
_DERIVED_INDEX_NAMES = {"skills-embeddings.json", "skills-index.json"}
_DERIVED_INDEX_SUFFIXES = {".faiss", ".hnsw", ".ann", ".annoy", ".idx", ".index", ".lmdb", ".mdb", ".duckdb"}
_DATED_RUN = re.compile(r"(?:physical-cold|feedback-corrected-terminal|run|session|benchmark)-20\d{2}-\d{2}-\d{2}")
_RUN_DATA_SUFFIXES = {".json", ".jsonl", ".txt", ".csv", ".gz", ".bin", ".npy", ".npz"}
SECRET_PATTERNS = [
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----[ \t\r\n]+"
               rb"[A-Za-z0-9+/=\r\n]{80,}"),
    re.compile(rb"\b(?:ghp_|github_pat_)[A-Za-z0-9_]{30,}\b"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
]
_URI_CREDENTIALS = re.compile(
    rb"\b(?:mongodb(?:\+srv)?|postgres(?:ql)?|mysql)://([^\s/:]+):([^\s/@]+)@([^\s/]+)")


class _IngestCancelled(Exception):
    pass


def _now():
    return datetime.now(UTC).isoformat()


def _metadata(value, depth=0):
    """YAML dates and sets are not BSON/JSON metadata; the guide preserves originals."""
    if depth > 20:
        return "[metadata depth limit]"
    if isinstance(value, dict):
        return {str(k): _metadata(v, depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_metadata(v, depth + 1) for v in value]
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    return str(value)


def _error(exc: Exception) -> dict:
    """Do not echo driver exceptions: they can include credentialed URIs."""
    value = {"error_type": type(exc).__name__}
    code = getattr(exc, "code", None)
    if isinstance(code, int):
        value["code"] = code
    return value


def _head_receipt(head: dict | None) -> dict | None:
    """Report a guard fingerprint without copying source metadata into logs."""
    if head is None:
        return None
    return {"sha256": sha(canonical(_metadata(head))),
            "managed_owner": head.get("managed_by") == MANAGED_BY,
            "active": head.get("active") if type(head.get("active")) is bool else None,
            "searchable": head.get("searchable")
            if type(head.get("searchable")) is bool else None}


def _head_guard(head: dict) -> dict:
    """Match the full observed BSON document, including unknown future fields."""
    return {"_id": head["_id"], "$expr": {"$eq": ["$$ROOT", {"$literal": head}]}}


def _safe_path(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 1000:
        raise ValueError("Resource path must contain 1..1000 characters")
    path = PurePosixPath(value)
    if (value != unicodedata.normalize("NFC", value) or path.is_absolute()
            or path.as_posix() != value or "\\" in value or ":" in value
            or any(ord(c) < 32 for c in value)
            or any(p in {"", ".", ".."} for p in value.split("/"))):
        raise ValueError("Resource path must be a normalized relative POSIX path")
    return value


def _excluded(path: PurePosixPath) -> str | None:
    if any(p in EXCLUDED_NAMES or p.startswith(".env") for p in path.parts):
        return "excluded-name"
    if path.suffix.lower() in SECRET_SUFFIXES:
        return "credential-file-type"
    if _FIXTURE_DIRS.intersection(part.lower() for part in path.parts):
        return None
    lower = path.name.lower()
    parts = {part.lower() for part in path.parts}
    if lower in _DERIVED_INDEX_NAMES:
        return "derived-skill-index-cache"
    if (re.search(r"\.(?:db|db3|sqlite|sqlite3)(?:-(?:wal|shm|journal))?$", lower)
            or path.suffix.lower() in {".wal", ".shm"} | _DERIVED_INDEX_SUFFIXES):
        return "derived-database-or-vector-index"
    if "raw-state" in parts:
        return "operational-raw-state"
    if lower.startswith("terminal-bundle.") or lower.endswith("-full-work-files.txt"):
        return "operational-terminal-or-workspace-dump"
    if re.search(r"\.log(?:\.(?:gz|xz|bz2|zst))?$", lower):
        return "operational-run-log"
    if re.search(r"(?:^|[._-])(?:stdout|stderr)\.(?:jsonl|json|txt)(?:\.(?:gz|xz|bz2|zst))?$", lower):
        return "operational-worker-output"
    if ("transcripts" in parts or "transcript" in parts
            or re.fullmatch(r"(?:.+[._-])?transcripts?\.(?:jsonl|json|txt|md)(?:\.gz)?", lower)):
        # Fetchers and other source code in a transcripts package remain usable.
        if path.suffix.lower() in {".json", ".jsonl", ".txt", ".md", ".gz"}:
            return "operational-transcript"
    if (any(_DATED_RUN.fullmatch(part) for part in path.parts)
            and path.suffix.lower() in _RUN_DATA_SUFFIXES):
        return "operational-dated-run-output"
    return None


def _has_secret(data: bytes) -> bool:
    if any(pattern.search(data) for pattern in SECRET_PATTERNS):
        return True
    for match in _URI_CREDENTIALS.finditer(data):
        password = unquote(match[2].decode("utf-8", "replace"))
        # Documentation placeholders do not carry credentials. Host names alone
        # never make a non-placeholder password safe to distribute.
        placeholder = (re.fullmatch(r"<[^<>]+>|\$\{[^{}]+\}|\{[^{}]+\}", password)
                       or password.lower() in {"password", "pass", "your_password", "your-password",
                                              "yourpassword", "mypassword", "example-password"}
                       or password in {".*", "***", "..."})
        if not placeholder:
            return True
    for key, value in os.environ.items():
        if (len(value) >= 20 and re.search(r"(?:TOKEN|SECRET|PASSWORD|API_KEY|MONGODB_URI)", key)
                and value.encode() in data):
            return True
    return False


def _page(text: str, offset: int, max_chars: int) -> dict:
    if (type(offset) is not int or offset < 0 or type(max_chars) is not int
            or not 1 <= max_chars <= MAX_PAGE_CHARS):
        raise ValueError("Require a nonnegative offset and 1..32000 max_chars")
    if offset > len(text):
        raise ValueError("Offset exceeds content length")
    end = min(len(text), offset + max_chars)
    return {"text": text[offset:end], "start": offset, "end": end,
            "total_chars": len(text), "truncated": end < len(text),
            "next_offset": end if end < len(text) else None}


class MongoStore:
    """The only default connection source is the secret ``MONGODB_URI2`` env var."""

    def __init__(self, client=None, database=None, collection=None, *,
                 database_name: str = DATABASE, collection_name: str = COLLECTION,
                 resource_roots: list[str | Path] | None = None):
        if collection is not None:
            database = collection.database if database is None else database
        if database is None:
            if client is None:
                uri = os.environ.get("MONGODB_URI2", "")
                if not uri:
                    raise ValueError("MONGODB_URI2 is required for MongoDB skill distribution")
                try:
                    from pymongo import MongoClient
                    client = MongoClient(uri, appname="skill-registry", serverSelectionTimeoutMS=8000,
                                         connectTimeoutMS=8000, socketTimeoutMS=30000,
                                         timeoutMS=30000, retryReads=False, retryWrites=False,
                                         compressors="zlib", zlibCompressionLevel=6)
                except Exception as exc:
                    raise RuntimeError("Cannot initialize the MongoDB skill connection") from exc
            database = client[database_name]
        self.database = database
        self.collection = collection if collection is not None else database[collection_name]
        self.resources = database[collection_name + "_resources"]
        self.versions = database[collection_name + "_versions"]
        self._blob_lock = threading.RLock()
        self._stored_blobs: set[str] = set()
        self._pending_blobs: set[str] = set()
        self._pending_chunks: list[dict] = []
        self._blob_cache_loaded = False
        self._progress = None
        self._resource_batches = self._resource_bytes = 0
        self._content_cache: OrderedDict[str, bytes] = OrderedDict()
        self._content_cache_bytes = 0
        self.resource_roots = {Path(root).expanduser().resolve() for root in (resource_roots or [])}
        if any(self._broad_root(root) for root in self.resource_roots):
            raise ValueError("Trusted resource roots cannot be the home directory or its ancestors")

    @staticmethod
    def _broad_root(path: Path) -> bool:
        home = Path.home().resolve()
        return path == home or path in home.parents

    def _trusted_base(self, base: Path, guide_parents: set[Path]) -> bool:
        resolved = base.expanduser().resolve()
        if self._broad_root(resolved):
            return False
        return any(resolved == root or resolved.is_relative_to(root)
                   for root in guide_parents | self.resource_roots)

    def _preload_blobs(self):
        if self._blob_cache_loaded:
            return
        # Current documents only cite fully committed resources. Reading their
        # content hashes avoids rewriting every resource on a watcher restart.
        for row in self.collection.find({"managed_by": MANAGED_BY}, {"resources.sha256": 1}):
            self._stored_blobs.update(resource["sha256"] for resource in row.get("resources", []))
        self._blob_cache_loaded = True

    def _flush_resources(self):
        with self._blob_lock:
            if not self._pending_chunks:
                return
            from pymongo import UpdateOne
            batch, size = [], 0

            def publish():
                self.resources.bulk_write([UpdateOne(
                    {"_id": row["_id"], "managed_by": MANAGED_BY},
                    {"$setOnInsert": row}, upsert=True) for row in batch], ordered=False)
                self._resource_batches += 1
                self._resource_bytes += sum(len(row["data"]) for row in batch)
                if self._progress and self._resource_batches % 10 == 0:
                    self._progress({"phase": "resources", "batches": self._resource_batches,
                                    "bytes": self._resource_bytes})

            for row in self._pending_chunks:
                row_size = len(row["data"]) + 512
                if batch and size + row_size > MAX_RESOURCE_BULK_BYTES:
                    publish()
                    batch, size = [], 0
                batch.append(row)
                size += row_size
            if batch:
                publish()
            self._stored_blobs.update(self._pending_blobs)
            self._pending_chunks.clear()
            self._pending_blobs.clear()

    def provision(self, wait_seconds: int = 0) -> dict:
        if type(wait_seconds) is not int or not 0 <= wait_seconds <= 300:
            raise ValueError("wait_seconds must be 0..300")
        self.collection.create_index([("managed_by", 1), ("name_folded", 1)],
                                     name="skill_registry_name_v1")
        self.collection.create_index([("managed_by", 1), ("sha256", 1)],
                                     name="skill_registry_hash_v1")
        self.collection.create_index([("managed_by", 1), ("active", 1), ("updated_at", -1)],
                                     name="skill_registry_updates_v1")
        self.versions.create_index([("managed_by", 1), ("skill_id", 1), ("created_at", -1)],
                                   name="skill_registry_versions_v1")
        self.resources.create_index([("managed_by", 1), ("sha256", 1), ("chunk", 1)],
                                    name="skill_registry_resources_v1")
        existing = {row["name"]: row for row in self.collection.list_search_indexes()}
        changes, errors = [], []
        for name, spec in SEARCH_INDEXES.items():
            try:
                if name not in existing:
                    from pymongo.operations import SearchIndexModel
                    self.collection.create_search_index(SearchIndexModel(name=name, **spec))
                    changes.append({"name": name, "action": "created"})
                elif existing[name].get("latestDefinition") != spec["definition"]:
                    self.collection.update_search_index(name, copy.deepcopy(spec["definition"]))
                    changes.append({"name": name, "action": "updated"})
            except Exception as exc:
                errors.append({"name": name, **_error(exc)})
        deadline = time.monotonic() + wait_seconds
        result = self.status()
        while wait_seconds and not result["search_ready"] and time.monotonic() < deadline:
            time.sleep(min(2, max(0, deadline - time.monotonic())))
            result = self.status()
        return {**result, "changes": changes, "provision_errors": errors}

    def status(self) -> dict:
        indexes, diagnostics = [], []
        try:
            for row in self.collection.list_search_indexes():
                if row.get("name") in SEARCH_INDEXES:
                    indexes.append({k: row[k] for k in ("name", "type", "status", "queryable", "numDocs")
                                    if k in row})
        except Exception as exc:
            diagnostics.append({"operation": "list_search_indexes", **_error(exc)})
        ready = {row["name"] for row in indexes if row.get("queryable") is True
                 and row.get("status") == "READY"}
        owned = {"managed_by": MANAGED_BY}
        return {"schema": SCHEMA, "database": self.database.name,
                "collection": self.collection.name, "model": MODEL,
                "embedding": "Atlas native autoEmbed; Voyage AI at index and query time",
                "counts": {"skills": self.collection.count_documents(owned),
                           "searchable": self.collection.count_documents({**owned, "searchable": True,
                                                                         "active": True}),
                           "versions": self.versions.count_documents(owned),
                           "resource_chunks": self.resources.count_documents(owned)},
                "indexes": indexes, "search_ready": set(SEARCH_INDEXES) <= ready,
                "semantic_ready": VECTOR_INDEX in ready,
                "lexical_ready": LEXICAL_INDEX in ready, "diagnostics": diagnostics}

    def _blob(self, data: bytes, path: str, executable: bool = False) -> dict:
        checksum = sha(data)
        chunks = max(1, (len(data) + RESOURCE_CHUNK_BYTES - 1) // RESOURCE_CHUNK_BYTES)
        with self._blob_lock:
            if checksum not in self._stored_blobs and checksum not in self._pending_blobs:
                self._pending_blobs.add(checksum)
                for number in range(chunks):
                    value = data[number * RESOURCE_CHUNK_BYTES:(number + 1) * RESOURCE_CHUNK_BYTES]
                    self._pending_chunks.append({"_id": f"{checksum}:{number}",
                        "managed_by": MANAGED_BY, "sha256": checksum, "chunk": number,
                        "chunks": chunks, "data": value, "created_at": _now()})
                if (len(self._pending_chunks) >= 500
                        or sum(len(row["data"]) + 512 for row in self._pending_chunks)
                        >= MAX_RESOURCE_BULK_BYTES):
                    self._flush_resources()
        return {"path": path, "sha256": checksum, "bytes": len(data), "chunks": chunks,
                "executable": bool(executable),
                "media_type": mimetypes.guess_type(path)[0] or "application/octet-stream"}

    def _collect(self, base: Path, guide: Path, stop_event=None) -> tuple[list[dict], list[dict]]:
        manifest, excluded = [], []
        total = directories = 0
        base = base.resolve(strict=True)
        for current, dirs, files in os.walk(base, followlinks=False):
            if stop_event is not None and stop_event.is_set():
                raise _IngestCancelled()
            directories += 1
            if directories > MAX_DISCOVERY_DIRS:
                excluded.append({"path": ".", "reason": "directory-limit"})
                break
            retained = []
            for name in sorted(dirs):
                source = Path(current) / name
                relative = source.relative_to(base).as_posix()
                reason = _excluded(PurePosixPath(relative))
                if source.is_symlink():
                    reason = "symlink-directory"
                if reason:
                    excluded.append({"path": relative, "reason": reason})
                else:
                    retained.append(name)
            dirs[:] = retained
            for name in sorted(files):
                if stop_event is not None and stop_event.is_set():
                    raise _IngestCancelled()
                source = Path(current) / name
                relative = source.relative_to(base).as_posix()
                reason = _excluded(PurePosixPath(relative))
                try:
                    _safe_path(relative)
                    if source.is_symlink():
                        reason = "symlink-file"
                    elif not stat.S_ISREG(source.stat().st_mode):
                        reason = "nonregular-file"
                    elif source.resolve() == guide.resolve():
                        continue
                    elif relative == "SKILL.md":
                        # A wrapper can point at another source's resource directory.
                        # Preserve that source's guide without shadowing this entrypoint.
                        relative = "_resource_source/SKILL.md"
                    if reason:
                        excluded.append({"path": relative, "reason": reason})
                        continue
                    if len(manifest) >= MAX_RESOURCE_FILES:
                        excluded.append({"path": relative, "reason": "file-count-limit"})
                        continue
                    data = read_bounded(source, MAX_RESOURCE_BYTES)
                    if total + len(data) > MAX_SKILL_BYTES:
                        excluded.append({"path": relative, "reason": "skill-byte-limit"})
                        continue
                    if _has_secret(data):
                        excluded.append({"path": relative, "reason": "secret-content"})
                        continue
                    total += len(data)
                    manifest.append(self._blob(data, relative, bool(source.stat().st_mode & 0o111)))
                except (OSError, ValueError) as exc:
                    excluded.append({"path": relative, "reason": "unreadable-or-oversized",
                                     **_error(exc)})
        return manifest, excluded

    def _write(self, doc: dict, guide: bytes, resources: list[dict], exclusions: list[dict], *,
               _existing=_MISSING, _batch: list | None = None,
               _local_ingest: bool = False) -> dict:
        if _has_secret(guide):
            raise ValueError("Guide contains credential material and cannot be distributed")
        guide_blob = self._blob(guide, "SKILL.md")
        files = [guide_blob, *sorted(resources, key=lambda r: r["path"])]
        release = sha(canonical({"schema": SCHEMA, "skill_id": doc["_id"], "files": files}))
        existing = _existing
        if existing is _MISSING:
            existing = self.collection.find_one({"_id": doc["_id"]})
        if existing is not None and existing.get("managed_by") != MANAGED_BY:
            raise ValueError("Skill identity belongs to another collection owner")
        local_conflicts = (_local_publication(existing, doc, files, release)
                           if _local_ingest else [])
        distribution = sha(canonical({"document": doc, "files": files, "exclusions": exclusions}))
        now = _now()
        text = guide.decode("utf-8")
        search_bytes = "\n".join([doc["name"], doc["description"], text]).encode("utf-8")
        search_text = search_bytes[:MAX_SEARCH_BYTES].decode("utf-8", "ignore")
        doc = {**doc, "managed_by": MANAGED_BY, "schema": SCHEMA, "sha256": sha(guide),
               "release_sha256": release, "guide": guide_blob, "resources": files,
               "distribution_sha256": distribution,
               "exclusions": exclusions, "resource_complete": not exclusions,
               "search_text": search_text if doc.get("searchable", True) else "",
               "search_text_truncated": len(search_bytes) > MAX_SEARCH_BYTES,
               "active": True, "created_at": (existing or {}).get("created_at", now),
               "updated_at": now, "embedding": {"provider": "voyage-ai", "model": MODEL,
                                                "mode": "atlas-autoEmbed", "field": "search_text"}}
        if not doc.get("searchable", True):
            # Missing fields are skipped by autoEmbed. Empty-string embedding
            # requests would spend work on archived/disabled/invalid guides.
            doc.pop("search_text", None)
        snapshot_id = sha(canonical([doc["_id"], release]))
        changed = (existing is None or existing.get("distribution_sha256") != distribution
                   or existing.get("active") is False)
        result = {"id": doc["_id"], "skill_id": doc["_id"], "name": doc["name"],
                  "sha256": doc["sha256"], "release_sha256": release, "changed": changed,
                  "resources": len(files), "exclusions": exclusions,
                  "resource_complete": not exclusions}
        preserved_state = local_conflicts
        if existing is not None:
            if existing.get("active") is not True:
                preserved_state.append("existing-inactive-or-unknown")
            if existing.get("searchable") is not True and doc.get("searchable", True):
                preserved_state.append("existing-nonrouting-or-unknown")
            if any(value not in doc.get("disabled_in", [])
                   for value in existing.get("disabled_in", [])):
                preserved_state.append("existing-explicit-disable")
        restrictive = None
        if (_local_ingest and existing is not None and preserved_state
                and any(value not in existing.get("disabled_in", [])
                        for value in doc.get("disabled_in", []))):
            # A new explicit local disable still takes effect when source
            # content conflicts. Keep the exact current guide/resources and
            # metadata; union disabled states and never reactivate the head.
            restrictive = copy.deepcopy(existing)
            restrictive["disabled_in"] = sorted(set(existing.get("disabled_in", []))
                                                 | set(doc.get("disabled_in", [])))
            restrictive.update(searchable=False, updated_at=now)
            restrictive.pop("search_text", None)
            inputs = {key: value for key, value in restrictive.items() if key not in _GENERATED_FIELDS}
            restrictive["distribution_sha256"] = sha(canonical({"document": inputs,
                "files": restrictive.get("resources", []), "exclusions": restrictive.get("exclusions", [])}))
        item = {"document": doc, "snapshot_id": snapshot_id, "result": result,
                "expected_head": copy.deepcopy(existing),
                "preserve_database_source": (existing is not None
                    and existing.get("source", {}).get("kind") == "database"
                    and doc.get("source", {}).get("kind") == "local"),
                "preserved_state": preserved_state,
                "restrictive_document": restrictive,
                "bytes": len(canonical(doc)) + len(canonical(_metadata(existing)))}
        if _batch is not None:
            _batch.append(item)
        elif self._flush_documents([item]):
            raise ValueError("REVISION_CONFLICT: current skill changed; candidate snapshot retained")
        return result

    def _flush_documents(self, batch: list):
        """Archive candidates, then conditionally publish without replacing a newer head."""
        if not batch:
            return []
        from pymongo import ReplaceOne, UpdateOne
        self._flush_resources()
        version_ops, current_ops = [], []
        for item in batch:
            if not item["result"]["changed"]:
                continue
            doc, snapshot_id = item["document"], item["snapshot_id"]
            version_ops.append(UpdateOne({"_id": snapshot_id, "managed_by": MANAGED_BY},
                {"$setOnInsert": {**doc, "_id": snapshot_id, "skill_id": doc["_id"]}}, upsert=True))
            if item["restrictive_document"] is not None:
                current_ops.append(ReplaceOne(_head_guard(item["expected_head"]),
                                              item["restrictive_document"], upsert=False))
                continue
            if item["preserve_database_source"] or item["preserved_state"]:
                continue
            expected = item["expected_head"]
            if expected is None:
                # An intervening insert, including another owner's identity,
                # must never be replaced by an initial-source ingestion.
                current_ops.append(UpdateOne({"_id": doc["_id"]},
                                             {"$setOnInsert": doc}, upsert=True))
            else:
                current_ops.append(ReplaceOne(_head_guard(expected),
                                              doc, upsert=False))
        if version_ops:
            self.versions.bulk_write(version_ops, ordered=False)
        if current_ops:
            self.collection.bulk_write(current_ops, ordered=False)
        heads = {row["_id"]: row for row in self.collection.find(
            {"_id": {"$in": [item["document"]["_id"] for item in batch]}})}
        conflicts = []
        for item in batch:
            doc, result = item["document"], item["result"]
            current = heads.get(doc["_id"])
            if (not item["preserved_state"] and not item["preserve_database_source"]
                    and current and current.get("managed_by") == MANAGED_BY
                    and {key: value for key, value in current.items()
                         if key not in {"created_at", "updated_at"}}
                    == {key: value for key, value in doc.items()
                        if key not in {"created_at", "updated_at"}}):
                if result["changed"] and current.get("updated_at") != doc["updated_at"]:
                    result.update(changed=False, concurrent_equivalent=True)
                continue
            # Unchanged inputs can also race. Retain their candidate snapshot
            # before reporting that a current MongoDB edit takes precedence.
            self.versions.update_one({"_id": item["snapshot_id"], "managed_by": MANAGED_BY},
                {"$setOnInsert": {**doc, "_id": item["snapshot_id"], "skill_id": doc["_id"]}},
                upsert=True)
            conflicts.append({"id": doc["_id"], "name": result["name"],
                "operation": "current-head-conflict", "candidate_retained": True,
                "current_preserved": True, "preserved_state": item["preserved_state"],
                "restrictive_disable_applied": (item["restrictive_document"] is not None
                    and current is not None and current.get("distribution_sha256")
                    == item["restrictive_document"]["distribution_sha256"]),
                "candidate_release_sha256": doc["release_sha256"],
                "candidate_snapshot_id": item["snapshot_id"],
                "expected_head": _head_receipt(item["expected_head"]),
                "observed_head": _head_receipt(current)})
        return conflicts

    def ingest(self, catalog: Catalog, progress=None, stop_event=None) -> dict:
        from .installation_state import InstallationResolver

        self._progress = progress
        self._resource_batches = self._resource_bytes = 0
        refresh = catalog.refresh()
        root_access = refresh.get("root_access") or _root_access(catalog.roots)
        with catalog.connect() as db:
            rows = [dict(r) for r in db.execute("SELECT * FROM skills ORDER BY id")]
        configured_roots = {Path(root["path"]).expanduser().resolve() for root in catalog.roots}
        parent_sources = {}
        for row in rows:
            guide = Path(row["path"]).resolve()
            parent_sources.setdefault(guide.parent, set()).add(guide)
        # A library-root SKILL.md or a flat directory of symlink targets does
        # not authorize uploading the whole sibling library as its resources.
        guide_parents = {parent for parent, guides in parent_sources.items()
                         if len(guides) == 1 and next(iter(guides)).name == "SKILL.md"
                         and parent not in configured_roots and not self._broad_root(parent)}
        # One bounded metadata cursor avoids one network read per installed skill.
        existing = {doc["_id"]: doc for doc in self.collection.find({"managed_by": MANAGED_BY})}
        self._preload_blobs()
        results, failed, batch = [], [], []
        fatal = None
        cancelled = stop_event is not None and stop_event.is_set()
        resolver = InstallationResolver()
        disabled_snapshot = _codex_disabled()

        def flush():
            nonlocal fatal
            try:
                conflicts = self._flush_documents(batch)
                failed.extend(conflicts)
                conflicted = {item["id"] for item in conflicts}
                results.extend(item["result"] for item in batch
                               if item["result"]["id"] not in conflicted)
            except Exception as exc:
                # Unordered bulk operations can partly succeed. Report the entire
                # batch as unverified so retries remain safe and accounting honest.
                failed.extend({"id": item["result"]["id"], "name": item["result"]["name"],
                               "operation": "bulk-publish", **_error(exc)} for item in batch)
                fatal = {"operation": "bulk-publish", **_error(exc)}
            batch.clear()
            if progress:
                progress({"phase": "skills", "ingested": len(results), "failed": len(failed),
                          "total": len(rows), "resource_batches": self._resource_batches,
                          "resource_bytes": self._resource_bytes})

        for row in rows:
            if stop_event is not None and stop_event.is_set():
                cancelled = True
                break
            try:
                source_path = Path(row["path"])
                source_stat = source_path.stat()
                guide = read_bounded(source_path, MAX_GUIDE_BYTES)
                if sha(guide) != row["sha256"]:
                    raise ValueError("REVISION_CONFLICT: source changed during ingestion")
                if source_path.stat() != source_stat:
                    raise ValueError("REVISION_CONFLICT: source changed during ingestion")
                with catalog.connect() as db:
                    display = catalog._row(db, row["id"], disabled=disabled_snapshot)
                try:
                    meta = _frontmatter(guide.decode())
                except ValueError:
                    meta = {}
                base = Path(row["resource_base"]).expanduser().resolve()
                source_parent = Path(row["path"]).parent.resolve()
                if stop_event is not None and stop_event.is_set():
                    raise _IngestCancelled()
                shared_base = (base in configured_roots or (base == source_parent
                               and source_parent not in guide_parents))
                trusted_base = not shared_base and self._trusted_base(base, guide_parents)
                if shared_base:
                    resources, excluded = [], [{"path": ".", "reason": "shared-resource-base"}]
                elif trusted_base:
                    resources, excluded = self._collect(Path(row["resource_base"]), Path(row["path"]),
                                                        stop_event=stop_event)
                else:
                    resources, excluded = [], [{"path": ".", "reason": "untrusted-resource-base"}]
                disabled_only = bool(display["installations"]) and all(
                    a["codex_activation"] == "explicitly-disabled" for a in display["installations"])
                eligibility = resolver.classify(row["path"], display["installations"])
                doc = {"_id": row["id"], "name": row["name"],
                       "name_folded": row["name"].casefold(), "description": row["description"],
                       "version": str(meta.get("version", "unversioned")), "metadata": _metadata(meta),
                       "source": {"kind": "local", "path": row["path"],
                                  "resource_base": row["resource_base"],
                                  "resource_base_trusted": trusted_base,
                                  "eligibility": eligibility["state"],
                                  "eligibility_reasons": eligibility["reasons"]},
                       "installations": eligibility["installations"],
                       "disabled_in": display["disabled_in"], "activation": "unknown",
                       "validation_error": row["error"],
                       "searchable": (not row["error"] and not disabled_only
                                      and eligibility["searchable"])}
                previous = existing.get(row["id"])
                self._write(doc, guide, resources, excluded,
                            _existing=previous, _batch=batch, _local_ingest=True)
                if (len(batch) >= MAX_BULK_GUIDES
                        or sum(item["bytes"] for item in batch) >= MAX_BULK_BYTES):
                    flush()
                    if fatal:
                        break
            except _IngestCancelled:
                cancelled = True
                break
            except Exception as exc:
                failed.append({"id": row["id"], "name": row["name"], **_error(exc)})
                from pymongo.errors import PyMongoError
                if isinstance(exc, PyMongoError):
                    fatal = {"operation": "resource-publish", **_error(exc)}
                    failed.extend({"id": item["result"]["id"], "name": item["result"]["name"],
                                   "operation": "aborted-resource-publish", **_error(exc)} for item in batch)
                    batch.clear()
                    break
        if not fatal:
            flush()
        if fatal or cancelled:
            # Never retry one failed network buffer once per remaining guide.
            self._pending_chunks.clear()
            self._pending_blobs.clear()
            self._blob_cache_loaded = False
        self._progress = None
        deactivated = 0
        preserved_unavailable = []
        deactivation_conflicts = []
        if not failed and not refresh.get("partial") and not cancelled:
            seen = {row["id"] for row in rows}
            roots = {str(Path(root["path"]).expanduser().absolute()) for root in catalog.roots}
            stale = [sid for sid, doc in existing.items() if sid not in seen
                     and doc.get("source", {}).get("kind") == "local"
                     and doc.get("active") is not False
                     and any(installation.get("root") in roots
                             for installation in doc.get("installations", []))]
            unavailable = {item["path"] for item in root_access if not item["available"]}
            for sid in stale:
                previous = existing[sid]
                if any(installation.get("root") in unavailable or _unavailable_alias(
                        installation["path"], installation["root"])
                       for installation in previous.get("installations", [])
                       if installation.get("root") in roots):
                    preserved_unavailable.append(sid)
                    continue
                timestamp = _now()
                self.collection.update_many(_head_guard(previous),
                    {"$set": {"active": False, "searchable": False, "updated_at": timestamp}})
                current = self.collection.find_one({"_id": sid})
                if (current and current.get("managed_by") == MANAGED_BY
                        and current.get("active") is False
                        and current.get("updated_at") == timestamp):
                    deactivated += 1
                else:
                    deactivation_conflicts.append({"id": sid,
                        "operation": "deactivation-head-conflict", "current_preserved": True})
        return {"schema": SCHEMA, "discovered": len(rows), "ingested": len(results),
                "changed": sum(r["changed"] for r in results), "failed": failed,
                "deactivated": deactivated,
                "aborted": fatal is not None, "infrastructure_failure": fatal,
                "cancelled": cancelled,
                "unattempted": len(rows) - len(results) - len(failed),
                "resource_batches": self._resource_batches, "resource_bytes": self._resource_bytes,
                "exclusion_count": sum(len(r["exclusions"]) for r in results),
                "partial": bool(failed or refresh.get("partial") or cancelled
                                or preserved_unavailable or deactivation_conflicts),
                "root_access": root_access, "preserved_unavailable_sources": preserved_unavailable,
                "conflicts": [item for item in failed if item.get("operation", "").endswith("head-conflict")]
                             + deactivation_conflicts,
                "refresh": refresh,
                "skills": results}

    def catalog(self, after: str = "", limit: int = 200) -> dict:
        """Page routing metadata for low-latency hooks without distributing guides."""
        if not isinstance(after, str) or len(after) > 200 or type(limit) is not int or not 1 <= limit <= 500:
            raise ValueError("Require a cursor up to 200 characters and limit 1..500")
        query = {"managed_by": MANAGED_BY, "active": True, "searchable": True}
        if after:
            query["_id"] = {"$gt": after}
        fields = {key: 1 for key in ("name", "description", "version", "sha256", "release_sha256",
                                    "metadata.triggers", "metadata.keywords", "metadata.whenToUse")}
        rows = list(self.collection.find(query, fields).sort("_id", 1).limit(limit + 1))
        skills = []
        for row in rows[:limit]:
            item = {key: row[key] for key in ("name", "description", "version", "sha256", "release_sha256")
                    if key in row}
            item["description"] = item.get("description", "")[:1200]
            item.update(id=row["_id"], skill_id=row["_id"], pin_sha256=row.get("release_sha256"))
            item["metadata"] = {key: row.get("metadata", {}).get(key, [])
                                for key in ("triggers", "keywords", "whenToUse")}
            skills.append(item)
        more = len(rows) > limit
        return {"skills": skills, "has_more": more,
                "next_after": skills[-1]["id"] if more else None,
                "semantic": False, "purpose": "Metadata-only lexical prompt routing cache"}

    def create(self, name: str, description: str, text: str, version: str = "1.0.0",
               resources: dict[str, str | bytes] | None = None) -> dict:
        """Create a DB-only skill, without materializing a local installation."""
        if (not isinstance(name, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,199}", name)
                or not isinstance(description, str) or not 1 <= len(description) <= 4000
                or not isinstance(text, str) or not text.strip()):
            raise ValueError("Require a slug name, description and nonempty guide text")
        guide = text.encode("utf-8")
        if len(guide) > MAX_GUIDE_BYTES:
            raise ValueError("Guide exceeds byte limit")
        meta = _frontmatter(text)
        if meta["name"] != name or meta["description"] != description:
            raise ValueError("Guide frontmatter must match the requested name and description")
        manifest = []
        total = len(guide)
        resources = resources or {}
        if not isinstance(resources, dict) or len(resources) > MAX_RESOURCE_FILES:
            raise ValueError("Too many resources")
        for path, value in sorted(resources.items()):
            _safe_path(path)
            data = value.encode() if isinstance(value, str) else value
            if (path == "SKILL.md" or _excluded(PurePosixPath(path)) or not isinstance(data, bytes)
                    or len(data) > MAX_RESOURCE_BYTES or _has_secret(data)):
                raise ValueError("Unsafe or oversized resource")
            total += len(data)
            if total > MAX_SKILL_BYTES:
                raise ValueError("Skill exceeds total byte limit")
            manifest.append(self._blob(data, path))
        return self._write({"_id": "db:" + sha(name.encode()), "name": name,
                           "name_folded": name.casefold(), "description": description,
                           "version": version, "metadata": _metadata(meta), "source": {"kind": "database"},
                           "installations": [], "disabled_in": [], "activation": "remote-only",
                           "validation_error": "", "searchable": True}, guide, manifest, [])

    @staticmethod
    def _display(doc: dict) -> dict:
        keys = ("name", "description", "version", "sha256", "release_sha256", "source",
                "installations", "disabled_in", "activation", "resource_complete", "exclusions",
                "search_text_truncated", "validation_error")
        result = {k: doc[k] for k in keys if k in doc}
        if "description" in result:
            result["description_truncated"] = len(result["description"]) > 1200
            result["description"] = result["description"][:1200]
        result.update(id=doc["_id"], skill_id=doc["_id"], routing_candidate_only=True)
        result["pin_sha256"] = doc.get("release_sha256")
        result["pin_instruction"] = "Pass release_sha256 to pin the guide and all resources together."
        return result

    def search(self, query: str, top: int = 5, mode: str = "hybrid") -> dict:
        if not isinstance(query, str) or not query.strip() or len(query) > MAX_QUERY_CHARS:
            raise ValueError("query must be 1..2000 characters")
        if type(top) is not int or not 1 <= top <= 20 or mode not in {"hybrid", "semantic", "lexical"}:
            raise ValueError("Require top 1..20 and hybrid, semantic or lexical mode")
        eligible = {"managed_by": MANAGED_BY, "active": True, "searchable": True}
        exact_filter = {**eligible, "$or": [{"name_folded": query.strip().casefold()},
                                           {"_id": query.strip()}]}
        exact = list(self.collection.find(exact_filter).limit(100))
        channels = {"exact": {"ok": True, "count": len(exact)}}
        batches = [("exact", exact)]
        limit = min(100, max(20, top * 5))
        projection = {"score": {"$meta": "vectorSearchScore"}}
        if mode != "lexical":
            pipeline = [{"$vectorSearch": {"index": VECTOR_INDEX, "path": "search_text",
                         "query": {"text": query}, "model": MODEL, "numCandidates": limit * 20,
                         "limit": limit, "filter": eligible}}, {"$match": eligible},
                        {"$set": projection}]
            try:
                rows = list(self.collection.aggregate(pipeline, maxTimeMS=15000))
                channels["semantic"] = {"ok": True, "count": len(rows), "model": MODEL,
                                        "native_auto_embedding": True}
                batches.append(("semantic", rows))
            except Exception as exc:
                channels["semantic"] = {"ok": False, **_error(exc)}
        if mode != "semantic":
            filters = [{"equals": {"path": key, "value": value}} for key, value in eligible.items()]
            should = [{"text": {"query": query, "path": field,
                                 "score": {"boost": {"value": weight}}}}
                      for field, weight in (("name", 6), ("description", 3), ("search_text", 1))]
            pipeline = [{"$search": {"index": LEXICAL_INDEX, "compound": {
                         "filter": filters, "should": should, "minimumShouldMatch": 1}}},
                        {"$match": eligible}, {"$limit": limit},
                        {"$set": {"score": {"$meta": "searchScore"}}}]
            try:
                rows = list(self.collection.aggregate(pipeline, maxTimeMS=15000))
                channels["lexical"] = {"ok": True, "count": len(rows)}
                batches.append(("lexical", rows))
            except Exception as exc:
                channels["lexical"] = {"ok": False, **_error(exc)}
        merged = {}
        for channel, rows in batches:
            for rank, row in enumerate(rows, 1):
                # Search indexes update asynchronously. Recheck the returned
                # BSON fields and fail closed even if a provider ignores $match.
                if (row.get("managed_by") != MANAGED_BY or row.get("active") is not True
                        or row.get("searchable") is not True or not isinstance(row.get("_id"), str)):
                    continue
                sid = row["_id"]
                candidate = merged.setdefault(sid, {"doc": row, "rrf": 0.0, "scores": {}})
                candidate["rrf"] += (1.2 if channel == "semantic" else 1.0) / (60 + rank)
                candidate["scores"][channel] = {"rank": rank, "score": row.get("score")}
                if channel == "exact":
                    candidate["rrf"] += 1.0
        for candidate in merged.values():
            candidate["routing"] = routing_score(query, candidate["doc"])
            candidate["rrf"] += 0.04 * candidate["routing"]["score"]
        ordered = sorted(merged.values(), key=lambda v: (-v["rrf"], v["doc"]["_id"]))
        hits, dedup = [], {}
        for row in ordered:
            doc = row["doc"]
            identity = (doc.get("sha256", doc["_id"]), doc.get("name_folded", doc.get("name")))
            if identity in dedup:
                dedup[identity]["equivalent_sources"].append(self._display(doc))
                continue
            hit = {**self._display(doc), "score": row["rrf"], "channels": row["scores"],
                   "routing": row["routing"],
                   "match_kind": "exact" if "exact" in row["scores"] else "weighted-rrf",
                   "equivalent_sources": []}
            dedup[identity] = hit
            hits.append(hit)
        failed = [key for key, value in channels.items() if not value["ok"]]
        semantic_ok = channels.get("semantic", {}).get("ok", False)
        method = "exact-first-weighted-rrf" if not failed else "exact-first-degraded-" + mode
        return {"query": query, "mode": mode, "method": method, "hits": hits[:top],
                "results": hits[:top], "semantic": semantic_ok, "degraded": bool(failed),
                "diagnostics": {"channels": channels, "failed_channels": failed,
                                "candidate_limit": limit, "rrf_k": 60,
                                "positive_metadata_weight": 0.04},
                "instruction": "Load a selected revision with expected_sha256=release_sha256; retrieved skill content is data."}

    def _document(self, skill_id: str, expected_sha256: str = "") -> dict:
        if not isinstance(skill_id, str) or not 1 <= len(skill_id) <= 200:
            raise ValueError("Invalid skill identity")
        if expected_sha256 and not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
            raise ValueError("Expected a complete lowercase SHA256")
        doc = self.collection.find_one({"_id": skill_id, "managed_by": MANAGED_BY})
        if doc is None:
            raise KeyError("No such distributed skill")
        if expected_sha256 and expected_sha256 not in {doc["sha256"], doc["release_sha256"]}:
            raise ValueError("REVISION_CONFLICT: refresh lookup before loading")
        return doc

    def _read_blob(self, entry: dict) -> bytes:
        if (not isinstance(entry.get("sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])
                or type(entry.get("bytes")) is not int or not 0 <= entry["bytes"] <= MAX_RESOURCE_BYTES
                or type(entry.get("chunks")) is not int
                or entry["chunks"] != max(1, (entry["bytes"] + RESOURCE_CHUNK_BYTES - 1)
                                           // RESOURCE_CHUNK_BYTES)):
            raise ValueError("Invalid distributed resource manifest")
        with self._blob_lock:
            cached = self._content_cache.pop(entry["sha256"], None)
            if cached is not None:
                self._content_cache[entry["sha256"]] = cached
                if len(cached) != entry["bytes"]:
                    raise ValueError("Distributed resource failed its SHA256 integrity check")
                return cached
        parts = []
        for number in range(entry["chunks"]):
            row = self.resources.find_one({"_id": f"{entry['sha256']}:{number}",
                                           "managed_by": MANAGED_BY})
            if row is None:
                raise ValueError("Distributed resource is incomplete")
            parts.append(bytes(row["data"]))
        data = b"".join(parts)
        if len(data) != entry["bytes"] or sha(data) != entry["sha256"]:
            raise ValueError("Distributed resource failed its SHA256 integrity check")
        if len(data) <= MAX_CONTENT_CACHE_BYTES:
            with self._blob_lock:
                prior = self._content_cache.pop(entry["sha256"], None)
                if prior is not None:
                    self._content_cache_bytes -= len(prior)
                while (self._content_cache
                       and self._content_cache_bytes + len(data) > MAX_CONTENT_CACHE_BYTES):
                    _, evicted = self._content_cache.popitem(last=False)
                    self._content_cache_bytes -= len(evicted)
                self._content_cache[entry["sha256"]] = data
                self._content_cache_bytes += len(data)
        return data

    def load(self, skill_id: str, expected_sha256: str = "", offset: int = 0,
             max_chars: int = 16000) -> dict:
        doc = self._document(skill_id, expected_sha256)
        text = self._read_blob(doc["guide"]).decode("utf-8")
        return {**self._display(doc), **_page(text, offset, max_chars), "current": True,
                "resource_base": "skill://" + skill_id + "/" + doc["release_sha256"] + "/",
                "resources": doc["resources"]}

    def resource(self, skill_id: str, path: str, expected_sha256: str = "", offset: int = 0,
                 max_chars: int = 16000) -> dict:
        _safe_path(path)
        doc = self._document(skill_id, expected_sha256)
        entry = next((r for r in doc["resources"] if r["path"] == path), None)
        if entry is None:
            raise KeyError("No such resource in this skill revision")
        data = self._read_blob(entry)
        try:
            text = data.decode("utf-8")
            encoding = "utf-8"
        except UnicodeDecodeError:
            text = base64.b64encode(data).decode("ascii")
            encoding = "base64"
        return {"id": skill_id, "skill_id": skill_id, "path": path, "sha256": doc["sha256"],
                "resource_sha256": entry["sha256"], "release_sha256": doc["release_sha256"],
                "encoding": encoding, "bytes": len(data), "media_type": entry["media_type"],
                "pin_instruction": "Use release_sha256 to pin both the guide and its resources.",
                **_page(text, offset, max_chars)}
