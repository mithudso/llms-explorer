"""Capability-separated research MCP over stdio or authenticated Streamable HTTP."""

from __future__ import annotations

import argparse
import asyncio
import inspect
import ipaddress
import os
import secrets
from contextvars import ContextVar
from dataclasses import dataclass
from functools import wraps
from typing import Any

try:
    from mcp.server import MCPServer
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServer

from .environment import load_environment
from .service import MAX_REQUEST_BYTES, Service, public_error


@dataclass(frozen=True)
class Principal:
    role: str
    actor: str


AUTH: ContextVar[Principal | None] = ContextVar("research_library_auth", default=None)


def _remote_owner(arguments: dict) -> dict:
    """Remote holders cannot impersonate trusted local legacy reservations."""
    arguments = dict(arguments)
    if "owner" in arguments:
        owner = arguments["owner"]
        if not isinstance(owner, str) or not owner.strip() or len(owner) > 200:
            raise ValueError("A bounded research owner label is required")
        arguments["owner"] = owner if owner.startswith("mcp:") else "mcp:" + owner
    return arguments


def create_server(service=None, default_role: str = "read"):
    if default_role not in {"read", "write"}:
        raise ValueError("MCP role must be read or write")
    server = MCPServer("mongodb-research-library", instructions=(
        "Search the library broadly and narrowly before new research. Read exact concepts, "
        "frontiers, sources and peer seeds; preserve their qualification and provenance. "
        "Mutations require a write capability, current revisions and owned research leases. "
        "Keep lease tokens private. Use the same owner label on acquire, renew, release and "
        "finalize; remote owners are namespaced mcp:. CRUD success is draft persistence, "
        "not publication. Finalization uses the trusted existing research evidence/gate/"
        "projection path. Caller-authored SUPPORTED or COMPLETED labels are not authority. "
        "No tool accepts shell commands, local file paths or raw MongoDB pipelines."
    ))
    state = service

    def backend():
        nonlocal state
        if state is None:
            state = Service()
        return state

    def invoke(operation: str, arguments: dict) -> dict:
        principal = AUTH.get() or Principal(default_role, "stdio-" + default_role)
        return backend().dispatch(operation, _remote_owner(arguments),
                                  role=principal.role, actor=principal.actor)

    def tool(*, read_only=True, destructive=False):
        def register(function):
            @wraps(function)
            async def call(*args, **kwargs):
                try:
                    return await asyncio.to_thread(function, *args, **kwargs)
                except Exception as exc:
                    raise ValueError(public_error(exc)) from None
            return server.tool(structured_output=True, annotations={
                "readOnlyHint": read_only, "destructiveHint": destructive,
                "idempotentHint": read_only,
            })(call)
        return register

    @tool()
    def research_status() -> dict[str, Any]:
        """Report managed corpus counts, graph revision and active lease count."""
        return invoke("status", {})

    @tool()
    def research_concept_get(concept_id: str, revision: int | None = None) -> dict[str, Any]:
        """Read one current concept or an immutable historical revision."""
        return invoke("concept_get", {"concept_id": concept_id, "revision": revision})

    @tool()
    def research_concept_list(filters: dict | None = None, after: str = "",
                              limit: int = 100) -> dict[str, Any]:
        """Page the complete concept inventory without a hidden score floor."""
        return invoke("concept_list", {"filters": filters, "after": after, "limit": limit})

    @tool()
    def research_history(concept_id: str, after: str = "", limit: int = 100) -> dict[str, Any]:
        """Page immutable concept revision metadata."""
        return invoke("concept_history", {"concept_id": concept_id, "after": after, "limit": limit})

    @tool()
    def research_search(query: str, mode: str = "hybrid", scope_ids: list[str] | None = None,
                        topic_id: str = "", breadth: str = "broad",
                        top: int = 10) -> dict[str, Any]:
        """Find duplicate/related work with broad or narrow semantic and keyword retrieval."""
        return invoke("search", {"query": query, "mode": mode, "scope_ids": scope_ids,
                                "topic_id": topic_id, "breadth": breadth, "top": top})

    @tool()
    def research_related(concept_id: str, depth: int = 2, after: str = "",
                         limit: int = 100) -> dict[str, Any]:
        """Traverse a bounded topic neighborhood with explicit pagination."""
        return invoke("related", {"concept_id": concept_id, "depth": depth,
                                 "after": after, "limit": limit})

    @tool()
    def research_frontier(topic_id: str = "", scored: str = "all", after: str = "",
                          limit: int = 100) -> dict[str, Any]:
        """Page scored, unscored, skipped and held frontier concepts."""
        return invoke("frontier", {"topic_id": topic_id, "scored": scored,
                                  "after": after, "limit": limit})

    @tool()
    def research_incomplete(topic_id: str = "", after: str = "",
                            limit: int = 100) -> dict[str, Any]:
        """Page incomplete concepts with explicit evidence/scope/projection reasons."""
        return invoke("incomplete", {"topic_id": topic_id, "after": after, "limit": limit})

    @tool()
    def research_peer_seeds(concept_id: str, limit: int = 8) -> dict[str, Any]:
        """Get terminology-rich peer leads with exact revisions and source qualification."""
        return invoke("peer_seeds", {"concept_id": concept_id, "limit": limit})

    @tool()
    def research_source_lookup(url: str) -> dict[str, Any]:
        """Resolve one exact normalized URL to source metadata/revision without a body or write."""
        return invoke("source_lookup", {"url": url})

    @tool()
    def research_source_get(source_id: str, snapshot_sha256: str = "", offset: int = 0,
                            max_chars: int = 16000) -> dict[str, Any]:
        """Read bounded source metadata or a pinned immutable text snapshot."""
        return invoke("source_get", {"source_id": source_id, "snapshot_sha256": snapshot_sha256,
                                    "offset": offset, "max_chars": max_chars})

    @tool()
    def research_queue_list(filters: dict | None = None, after: str = "",
                            limit: int = 100) -> dict[str, Any]:
        """List research queue state, including ownership, holds and continuation."""
        return invoke("queue_list", {"filters": filters, "after": after, "limit": limit})

    @tool()
    def research_lease_list() -> dict[str, Any]:
        """Inspect holders and fences without exposing lease tokens or token hashes."""
        return invoke("lease_list", {})

    @tool(read_only=False)
    def research_concept_create(name: str, slug: str | None = None, description: str = "",
                                aliases: list[str] | None = None, terms: list[str] | None = None,
                                request_id: str = "") -> dict[str, Any]:
        """Create an unverified concept/frontier record after deduplication."""
        return invoke("concept_create", {"name": name, "slug": slug, "description": description,
                                        "aliases": aliases, "terms": terms, "request_id": request_id})

    @tool(read_only=False)
    def research_concept_update(concept_id: str, patch: dict, expected_revision: int,
                                lease_token: str, request_id: str = "") -> dict[str, Any]:
        """CAS-update an owned draft; changed facts invalidate stale qualification."""
        return invoke("concept_update", {"concept_id": concept_id, "patch": patch,
                                        "expected_revision": expected_revision,
                                        "lease_token": lease_token, "request_id": request_id})

    @tool(read_only=False, destructive=True)
    def research_concept_delete(concept_id: str, expected_revision: int, lease_token: str,
                                request_id: str = "") -> dict[str, Any]:
        """Create a versioned tombstone; linked endpoints must first be safely unlinked."""
        return invoke("concept_delete", {"concept_id": concept_id,
                                        "expected_revision": expected_revision,
                                        "lease_token": lease_token, "request_id": request_id})

    @tool(read_only=False, destructive=True)
    def research_claim_mutate(concept_id: str, action: str, claim: dict | None = None,
                              lineage_id: str = "", expected_revision: int | None = None,
                              lease_token: str = "", request_id: str = "") -> dict[str, Any]:
        """Add/update/replace/remove a claim while retaining lineage and immutable versions."""
        return invoke("claim_mutate", {"concept_id": concept_id, "action": action, "claim": claim,
                                      "lineage_id": lineage_id,
                                      "expected_revision": expected_revision,
                                      "lease_token": lease_token, "request_id": request_id})

    @tool(read_only=False)
    def research_source_put(url: str, text: str | None = None, metadata: dict | None = None,
                            expected_revision: int | None = None,
                            request_id: str = "") -> dict[str, Any]:
        """Version source metadata/text; retain all pinned prior snapshots."""
        return invoke("source_put", {"url": url, "text": text, "metadata": metadata,
                                     "expected_revision": expected_revision,
                                     "request_id": request_id})

    @tool(read_only=False, destructive=True)
    def research_source_delete(source_id: str, expected_revision: int,
                               request_id: str = "") -> dict[str, Any]:
        """Retire a source without erasing evidence snapshots referenced by research."""
        return invoke("source_delete", {"source_id": source_id,
                                        "expected_revision": expected_revision,
                                        "request_id": request_id})

    @tool(read_only=False, destructive=True)
    def research_source_link(concept_id: str, action: str, source_ref: dict,
                             expected_revision: int, lease_token: str,
                             request_id: str = "") -> dict[str, Any]:
        """Add/update/remove a concept source link with claim invalidation."""
        return invoke("source_link", {"concept_id": concept_id, "action": action,
                                      "source_ref": source_ref,
                                      "expected_revision": expected_revision,
                                      "lease_token": lease_token, "request_id": request_id})

    @tool(read_only=False, destructive=True)
    def research_relation_mutate(concept_id: str, target_id: str, relation: str, action: str,
                                 expected_revisions: dict, lease_tokens: dict,
                                 request_id: str = "") -> dict[str, Any]:
        """Atomically edit reciprocal family relations under all affected leases/revisions."""
        return invoke("relation_mutate", {"concept_id": concept_id, "target_id": target_id,
                                          "relation": relation, "action": action,
                                          "expected_revisions": expected_revisions,
                                          "lease_tokens": lease_tokens, "request_id": request_id})

    @tool(read_only=False)
    def research_lease_acquire(concept_ids: list[str], owner: str, ttl_seconds: int = 900,
                               run_id: str = "", request_id: str = "") -> dict[str, Any]:
        """Atomically reserve concepts; heartbeat and preserve returned private tokens."""
        return invoke("lease_acquire", {"concept_ids": concept_ids, "owner": owner,
                                        "ttl_seconds": ttl_seconds, "run_id": run_id,
                                        "request_id": request_id})

    @tool(read_only=False)
    def research_lease_renew(concept_ids: list[str], tokens: dict, owner: str,
                             ttl_seconds: int = 900, request_id: str = "") -> dict[str, Any]:
        """Renew only matching live owners/tokens, retaining fencing checks."""
        return invoke("lease_renew", {"concept_ids": concept_ids, "tokens": tokens,
                                      "owner": owner, "ttl_seconds": ttl_seconds,
                                      "request_id": request_id})

    @tool(read_only=False)
    def research_lease_release(concept_ids: list[str], tokens: dict,
                               owner: str, request_id: str = "") -> dict[str, Any]:
        """Release only the caller's matching concept leases."""
        return invoke("lease_release", {"concept_ids": concept_ids, "tokens": tokens, "owner": owner,
                                        "request_id": request_id})

    @tool(read_only=False, destructive=True)
    def research_queue_put(concept_id: str, action: str = "enqueue",
                            metadata: dict | None = None, expected_revision: int | None = None,
                            lease_token: str = "", request_id: str = "") -> dict[str, Any]:
        """Version queue changes without dispatching research or clearing protected STOP holds."""
        return invoke("queue_put", {"concept_id": concept_id, "action": action,
                                    "metadata": metadata, "expected_revision": expected_revision,
                                    "lease_token": lease_token, "request_id": request_id})

    @tool(read_only=False)
    def research_finalize(concept_id: str, expected_revision: int, lease_token: str,
                           owner: str, request_id: str = "") -> dict[str, Any]:
        """Submit owned work to the trusted independent gate and canonical completion path."""
        return invoke("publish", {"concept_id": concept_id, "expected_revision": expected_revision,
                                  "lease_token": lease_token, "owner": owner,
                                  "request_id": request_id})

    @tool()
    def research_publication_status(job_id: str) -> dict[str, Any]:
        """Read redacted status of a trusted publication job."""
        return invoke("publication_status", {"job_id": job_id})

    return server


class BearerAuth:
    """Authenticate before body parsing; bind each request's read/write context."""

    def __init__(self, app, read_token: str = "", write_token: str = ""):
        pairs = [(read_token, Principal("read", "mcp-reader")),
                 (write_token, Principal("write", "mcp-writer"))]
        if not any(token for token, _ in pairs):
            raise ValueError("HTTP requires research-library capability tokens")
        self.tokens = []
        for token, principal in pairs:
            if not token:
                continue
            if (not isinstance(token, str) or not 32 <= len(token) <= 1024
                    or any(not 33 <= ord(c) <= 126 for c in token)):
                raise ValueError("Capability tokens must contain 32..1024 printable ASCII characters")
            self.tokens.append((("Bearer " + token).encode(), principal))
        if read_token and read_token == write_token:
            raise ValueError("Read and write capability tokens must differ")
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        supplied = headers.get(b"authorization", b"")
        principal = None
        for expected, candidate in self.tokens:
            if secrets.compare_digest(supplied, expected):
                principal = candidate
        if principal is None:
            await self._reject(send, 401, b'{"error":"unauthorized"}')
            return
        # Authenticate before reading and cap memory before MCP JSON decoding.
        body, total = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            value = message.get("body", b"")
            total += len(value)
            if total > MAX_REQUEST_BYTES:
                await self._reject(send, 413, b'{"error":"request too large"}')
                return
            body.append(value)
            if not message.get("more_body", False):
                break
        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {"type": "http.request", "body": b"".join(body), "more_body": False}

        async def protected_send(message):
            if message["type"] == "http.response.start":
                message = {**message, "headers": [*message.get("headers", []),
                    (b"cache-control", b"no-store"), (b"x-content-type-options", b"nosniff")]}
            await send(message)

        context = AUTH.set(principal)
        try:
            await self.app(scope, bounded_receive, protected_send)
        finally:
            AUTH.reset(context)

    @staticmethod
    async def _reject(send, status, body):
        await send({"type": "http.response.start", "status": status, "headers": [
            (b"content-type", b"application/json"), (b"www-authenticate", b"Bearer"),
            (b"cache-control", b"no-store"), (b"x-content-type-options", b"nosniff"),
        ]})
        await send({"type": "http.response.body", "body": body})


def http_app(server, read_token="", write_token="", host="127.0.0.1",
             allowed_hosts=None, allowed_origins=None):
    from mcp.server.transport_security import TransportSecuritySettings
    security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts or ["127.0.0.1", "localhost", "[::1]",
                                       "127.0.0.1:*", "localhost:*", "[::1]:*"],
        allowed_origins=allowed_origins or [],
    )
    if "stateless_http" in inspect.signature(server.streamable_http_app).parameters:
        app = server.streamable_http_app(stateless_http=True, json_response=True,
                                         host=host, transport_security=security)
    else:
        server.settings.stateless_http = True
        server.settings.json_response = True
        server.settings.transport_security = security
        app = server.streamable_http_app()
    return BearerAuth(app, read_token, write_token)


def run_server(*, env_file=None, transport="stdio", host="127.0.0.1", port=8767,
               allow_remote=False, role="read"):
    load_environment(env_file)
    server = create_server(default_role=role)
    if transport == "stdio":
        server.run(transport="stdio")
        return
    try:
        loopback = host == "localhost" or ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = False
    if not loopback and not allow_remote:
        raise ValueError("Non-loopback binding requires --allow-remote and a protected TLS endpoint")
    hosts = [x.strip() for x in os.environ.get("RESEARCH_LIBRARY_ALLOWED_HOSTS", "").split(",")
             if x.strip()]
    origins = [x.strip() for x in os.environ.get("RESEARCH_LIBRARY_ALLOWED_ORIGINS", "").split(",")
               if x.strip()]
    app = http_app(server, os.environ.get("RESEARCH_LIBRARY_READ_TOKEN", ""),
                   os.environ.get("RESEARCH_LIBRARY_WRITE_TOKEN", ""), host,
                   hosts or None, origins)
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="warning", access_log=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file")
    parser.add_argument("--transport", choices=("stdio", "streamable-http"), default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--allow-remote", action="store_true")
    parser.add_argument("--role", choices=("read", "write"), default="read",
                        help="Stdio capability only; HTTP capability comes from its token")
    args = parser.parse_args()
    try:
        run_server(**vars(args))
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
