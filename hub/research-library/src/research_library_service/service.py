"""One allowlisted policy and operation boundary shared by MCP and local CLI."""

from __future__ import annotations

import inspect
import json
import os
import re
import threading
from pathlib import Path
from typing import Any

from .environment import load_environment

MAX_REQUEST_BYTES = 8 * 1024 * 1024
READ_STORE = {
    "status", "concept_get", "concept_list", "source_get", "lease_list",
    "queue_list", "concept_history", "source_lookup",
}
READ_QUERIES = {"search", "related", "frontier", "incomplete", "peer_seeds"}
WRITE_STORE = {
    "concept_create", "concept_update", "concept_delete", "claim_mutate",
    "source_put", "source_delete", "source_link", "relation_mutate",
    "lease_acquire", "lease_renew", "lease_release", "queue_put",
}
ADMIN_STORE = {"provision", "complete", "queue_recover"}
ROLE_LEVELS = {"read": 0, "write": 1, "admin": 2}


def public_error(exc: Exception) -> str:
    """Keep trusted conflict classes useful without exposing driver or credential text."""
    if isinstance(exc, PermissionError):
        return "A research-library write capability is required"
    if isinstance(exc, KeyError):
        return "No such managed research library record"
    if (type(exc).__module__.startswith("research_library_service")
            and type(exc).__name__ in {"Conflict", "LeaseConflict", "OwnershipError"}):
        return str(exc)[:500]
    if isinstance(exc, (ValueError, TypeError)):
        return "Invalid research library request or unsupported operation"
    return "The research library is unavailable; retry later"


def validate_json(value: Any, depth: int = 0) -> None:
    if depth > 32:
        raise ValueError("Research request nesting limit exceeded")
    if isinstance(value, dict):
        if len(value) > 2048:
            raise ValueError("Too many request fields")
        for key, item in value.items():
            if not isinstance(key, str) or not key or key.startswith("$") or "." in key:
                raise ValueError("Unsafe request field name")
            validate_json(item, depth + 1)
    elif isinstance(value, list):
        if len(value) > 4096:
            raise ValueError("Too many request items")
        for item in value:
            validate_json(item, depth + 1)
    elif value is not None and not isinstance(value, (str, int, float, bool)):
        raise ValueError("Research requests must contain JSON values")


def validate_arguments(arguments: dict) -> None:
    if not isinstance(arguments, dict):
        raise ValueError("Operation arguments must be an object")
    validate_json(arguments)
    if len(json.dumps(arguments, ensure_ascii=False, allow_nan=False).encode()) > MAX_REQUEST_BYTES:
        raise ValueError("Research request byte limit exceeded")
    for key in ("top", "limit", "depth", "offset", "max_chars", "ttl_seconds",
                "expected_revision", "expected_queue_revision"):
        value = arguments.get(key)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError("Integer operation bounds are required")
        lower, upper = {
            "top": (1, 20), "limit": (1, 200), "depth": (0, 8),
            "offset": (0, 10**9), "max_chars": (1, 32000),
            "ttl_seconds": (30, 3600), "expected_revision": (0, 10**12),
            "expected_queue_revision": (0, 10**12),
        }[key]
        if not lower <= value <= upper:
            raise ValueError("Operation bound exceeded")
    for key in ("concept_ids", "scope_ids"):
        value = arguments.get(key)
        if value is not None and (
            not isinstance(value, list) or len(value) > 100
            or any(not isinstance(item, str) or not 1 <= len(item) <= 256 for item in value)
        ):
            raise ValueError("Concept scope must be a bounded list of identities")
    if "query" in arguments and (
        not isinstance(arguments["query"], str) or not 1 <= len(arguments["query"].strip()) <= 2000
    ):
        raise ValueError("Query must contain 1..2000 characters")
    if arguments.get("mode", "hybrid") not in {"hybrid", "semantic", "keyword", "lexical"}:
        raise ValueError("Unknown retrieval mode")
    if arguments.get("breadth", "broad") not in {"broad", "narrow"}:
        raise ValueError("Unknown retrieval breadth")
    if arguments.get("scored", "all") not in {"all", "scored", "unscored"}:
        raise ValueError("Unknown frontier score filter")


def _bridge_factory(config: dict) -> dict:
    try:
        from .canonical_bridge import make_bridge
    except ModuleNotFoundError as exc:
        if exc.name != "research_library_service.canonical_bridge":
            raise
        return {}
    bridge = make_bridge(config)
    if not isinstance(bridge, dict):
        raise ValueError("The trusted research bridge configuration is invalid")
    return bridge


class Service:
    def __init__(self, store=None, queries=None, config: dict | None = None, bridge=None):
        load_environment()
        if config is None:
            path = Path(os.environ.get(
                "RESEARCH_LIBRARY_CONFIG", "~/.config/research-library/config.json")).expanduser()
            if path.exists() and path.stat().st_size > 1024 * 1024:
                raise ValueError("The research library configuration is too large")
            config = json.loads(path.read_text()) if path.exists() else {}
        if not isinstance(config, dict):
            raise ValueError("The research library configuration must be an object")
        self.config = config
        self._store = store
        self._queries = queries
        self._bridge = bridge
        self._bridge_bound = False
        self._initialization_lock = threading.RLock()

    @property
    def bridge(self) -> dict:
        with self._initialization_lock:
            if self._bridge is None:
                self._bridge = _bridge_factory(self.config)
            return self._bridge

    @property
    def store(self):
        with self._initialization_lock:
            if self._store is None:
                from .store import LibraryStore
                prefix = self.config.get(
                    "prefix", os.environ.get("RESEARCH_LIBRARY_PREFIX", "research_"))
                if not isinstance(prefix, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,47}", prefix):
                    raise ValueError("Invalid operator collection prefix")
                self._store = LibraryStore(
                    prefix=prefix,
                    reservation_provider=self.bridge.get("reservation_provider"),
                    completion_verifier=self.bridge.get("completion_verifier"),
                    claim_identity=self.bridge.get("claim_identity"),
                )
            if not self._bridge_bound:
                if self.bridge.get("bind_store"):
                    self.bridge["bind_store"](self._store)
                self._bridge_bound = True
            return self._store

    @property
    def queries(self):
        with self._initialization_lock:
            if self._queries is None:
                from .queries import LibraryQueries
                self._queries = LibraryQueries(self.store)
            return self._queries

    def dispatch(self, operation: str, arguments: dict | None = None, *, role="read",
                 actor: str | None = None) -> dict:
        """Validate and authorize before lazy database creation or backend dispatch."""
        if role not in ROLE_LEVELS or not isinstance(operation, str):
            raise PermissionError("Unsupported research capability")
        if operation in READ_STORE | READ_QUERIES | {"publication_status"}:
            required = 0
        elif operation in WRITE_STORE | {"publish"}:
            required = 1
        elif operation in ADMIN_STORE | {"import", "coordinate"}:
            required = 2
        else:
            raise ValueError("Unsupported research operation")
        if ROLE_LEVELS[role] < required:
            raise PermissionError("A write capability is required")
        arguments = dict(arguments or {})
        validate_arguments(arguments)
        if operation in WRITE_STORE | {"complete", "publish", "coordinate", "queue_recover"}:
            arguments["actor"] = actor or f"local-{role}"
        if operation == "queue_recover" and not arguments["actor"].startswith("local-"):
            raise PermissionError("Queue recovery requires an owner-local invocation")
        if operation == "coordinate":
            if not arguments["actor"].startswith("local-"):
                raise PermissionError("Legacy coordination requires an owner-local invocation")
            function = self.bridge.get("coordinate")
            if function is None:
                raise ValueError("Trusted coordination bridge unavailable")
            return function(self.store, **arguments)
        if operation == "publish":
            function = self.bridge.get("publish")
            if function is None:
                raise ValueError("Trusted publication bridge unavailable")
            return function(self.store, **arguments)
        if operation == "publication_status":
            function = self.bridge.get("publication_status")
            if function is None:
                raise ValueError("Trusted publication bridge unavailable")
            return function(self.store, **arguments)
        if operation == "import":
            from .importer import import_library
            return import_library(self.store, **arguments)
        target = self.queries if operation in READ_QUERIES else self.store
        function = getattr(target, operation)
        # Signature binding rejects unknown options; remote callers cannot select methods.
        inspect.signature(function).bind(**arguments)
        result = function(**arguments)
        if not isinstance(result, dict):
            return {"items": result}
        return result
