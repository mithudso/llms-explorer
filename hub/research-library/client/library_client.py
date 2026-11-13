#!/usr/bin/env python3
"""Read hosted skill and research MCP services with Python 3.11+ and no dependencies.

Credentials come from SKILL_MCP_TOKEN / RESEARCH_MCP_TOKEN unless --codex-home
explicitly selects that directory's config.toml. This client never loads a local
backend, writes library records, or invokes research/judge LLMs. Semantic searches
use the hosted services' Voyage embedding retrieval.
"""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import math
import os
import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_REQUEST_BYTES = 128 * 1024
PROTOCOL_VERSION = "2025-06-18"
SUPPORTED_PROTOCOLS = {"2024-11-05", "2025-03-26", PROTOCOL_VERSION, "2025-11-25"}
SERVICES = {
    "skills": ("skills_mongodb", "https://skills-mcp.llms-explorer.com/mcp", "SKILL_MCP"),
    "research": ("research-library", "https://research-mcp.llms-explorer.com/mcp", "RESEARCH_MCP"),
}
READ_TOOLS = {
    "skills": frozenset({
        "skill_search", "skill_catalog", "skill_get", "skill_resource", "skills_status",
    }),
    "research": frozenset({
        "research_status", "research_concept_get", "research_concept_list", "research_history",
        "research_search", "research_related", "research_frontier", "research_incomplete",
        "research_peer_seeds", "research_source_lookup", "research_source_get",
        "research_queue_list", "research_lease_list", "research_publication_status",
        "research_run_get", "research_run_list", "research_run_ledger",
        "research_artifact_get", "research_artifact_list", "research_artifact_search",
    }),
}
_HEADER_NAME = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+\Z")
_ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class ClientError(Exception):
    """A fixed, public diagnostic that contains no remote or credential content."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ClientError("MCP redirects are refused; verify the configured endpoint")


def _valid_url(url):
    try:
        parsed = urlsplit(url)
        host = parsed.hostname
        loopback = host == "localhost"
        if host and not loopback:
            try:
                loopback = ipaddress.ip_address(host).is_loopback
            except ValueError:
                pass
        if (not isinstance(url, str) or not host or parsed.username is not None
                or parsed.password is not None or parsed.fragment or "#" in url
                or any(ord(c) <= 32 or ord(c) == 127 for c in url)
                or (parsed.scheme != "https" and not (parsed.scheme == "http" and loopback))):
            raise ValueError
        parsed.port
    except Exception:
        raise ClientError("Use an HTTPS endpoint, or HTTP on loopback, without userinfo or fragment") \
            from None
    return url


def _headers(values):
    if not isinstance(values, dict):
        raise ClientError("MCP headers must be a table of literal strings")
    clean = {}
    for name, value in values.items():
        if (not isinstance(name, str) or not _HEADER_NAME.fullmatch(name)
                or not isinstance(value, str) or not value
                or any(ord(c) < 32 or ord(c) == 127 or ord(c) > 255 for c in value)):
            raise ClientError("MCP headers require valid names and nonempty single-line values")
        lowered = name.lower()
        if (lowered in {"host", "content-length", "content-type", "accept", "connection",
                        "transfer-encoding", "proxy-authorization", "proxy-connection"}
                or lowered.startswith("mcp-") or lowered in clean):
            raise ClientError("MCP configuration contains a duplicate or reserved header")
        clean[lowered] = value
    return clean


def connection_settings(service, codex_home=None, *, environ=None):
    """Select only the requested config; never infer another user's Codex home."""
    if service not in SERVICES:
        raise ClientError("Choose the skills or research service")
    environ = os.environ if environ is None else environ
    entry_name, default_url, prefix = SERVICES[service]
    if codex_home is None:
        token = environ.get(prefix + "_TOKEN", "")
        if not token:
            raise ClientError("Set the selected service's MCP token environment variable")
        return _valid_url(environ.get(prefix + "_URL", default_url)), _headers({
            "Authorization": "Bearer " + token,
        })
    try:
        path = Path(codex_home) / "config.toml"
        with path.open("rb") as source:
            raw = source.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError
        config = tomllib.loads(raw.decode("utf-8"))
        entry = config["mcp_servers"][entry_name]
        if not isinstance(entry, dict) or entry.get("enabled") is False:
            raise ValueError
        url = entry["url"]
    except Exception:
        raise ClientError("Cannot read the selected hosted MCP entry from config.toml") from None
    values = _headers(entry.get("http_headers", {}))
    env_values = entry.get("env_http_headers", {})
    if not isinstance(env_values, dict):
        raise ClientError("MCP environment headers must be a table")
    for name, variable in env_values.items():
        if not isinstance(variable, str) or not _ENV_NAME.fullmatch(variable):
            raise ClientError("MCP credential environment variable names are invalid")
        header = _headers({name: environ.get(variable, "")})
        if values.keys() & header.keys():
            raise ClientError("MCP configuration contains duplicate authentication headers")
        values.update(header)
    variable = entry.get("bearer_token_env_var")
    if variable is not None:
        if not isinstance(variable, str) or not _ENV_NAME.fullmatch(variable):
            raise ClientError("MCP bearer environment variable name is invalid")
        if "authorization" in values:
            raise ClientError("MCP configuration contains duplicate authentication headers")
        token = environ.get(variable, "")
        if not token:
            raise ClientError("The configured MCP credential environment variable is unset")
        values.update(_headers({"Authorization": "Bearer " + token}))
    if not values:
        raise ClientError("The selected hosted MCP entry has no authentication headers")
    return _valid_url(url), values


class HostedClient:
    """Bounded stateless Streamable HTTP JSON transport, with no redirect following."""

    def __init__(self, service, url, headers, *, timeout=30.0, opener=None):
        if service not in SERVICES:
            raise ClientError("Choose the skills or research service")
        if (isinstance(timeout, bool) or not isinstance(timeout, (int, float))
                or not math.isfinite(timeout) or not 0.1 <= timeout <= 60):
            raise ClientError("MCP timeout must be between 0.1 and 60 seconds")
        self.service = service
        self.url = _valid_url(url)
        self.headers = _headers(headers)
        self.timeout = float(timeout)
        self._opener = opener or build_opener(_NoRedirect())
        self.protocol = None
        self._next_id = 0

    def _request(self, method, params, *, notification=False):
        self._next_id += 1
        request_id = self._next_id
        packet = {"jsonrpc": "2.0", "method": method, "params": params}
        if not notification:
            packet["id"] = request_id
        try:
            data = json.dumps(packet, allow_nan=False).encode("utf-8")
            if len(data) > MAX_REQUEST_BYTES:
                raise ClientError("MCP request exceeds the client byte limit")
            request = Request(self.url, method="POST", data=data, headers={
                **self.headers, "Content-Type": "application/json",
                "User-Agent": self.headers.get("user-agent", "hosted-library-client/1.0"),
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": self.protocol or PROTOCOL_VERSION,
            })
            with self._opener.open(request, timeout=self.timeout) as response:
                if response.status not in ({200, 202, 204} if notification else {200}):
                    raise ClientError("MCP HTTP request failed; check endpoint access")
                length = response.headers.get("Content-Length")
                if length is not None and (int(length) < 0 or int(length) > MAX_RESPONSE_BYTES):
                    raise ClientError("MCP response exceeds the client byte limit")
                body = response.read(MAX_RESPONSE_BYTES + 1)
                if len(body) > MAX_RESPONSE_BYTES:
                    raise ClientError("MCP response exceeds the client byte limit")
            if notification:
                return None
            payload = json.loads(body)
            if (not isinstance(payload, dict) or payload.get("jsonrpc") != "2.0"
                    or type(payload.get("id")) is not int or payload["id"] != request_id
                    or "error" in payload or not isinstance(payload.get("result"), dict)):
                raise ClientError("MCP returned an invalid or unsuccessful JSON-RPC response")
            return payload["result"]
        except ClientError:
            raise
        except Exception:
            # Exceptions may contain URLs, response bodies, credentials, or server traces.
            raise ClientError("MCP request failed; check credentials, endpoint access, and JSON HTTP") \
                from None

    def initialize(self):
        if self.protocol is None:
            result = self._request("initialize", {
                "protocolVersion": PROTOCOL_VERSION, "capabilities": {},
                "clientInfo": {"name": "hosted-library-client", "version": "1"},
            })
            protocol = result.get("protocolVersion")
            if not isinstance(protocol, str) or protocol not in SUPPORTED_PROTOCOLS:
                raise ClientError("MCP server selected an unsupported protocol version")
            self.protocol = protocol
            try:
                self._request("notifications/initialized", {}, notification=True)
            except ClientError:
                self.protocol = None
                raise

    def tools(self):
        self.initialize()
        tools, seen, cursor = [], set(), None
        for _ in range(32):
            result = self._request("tools/list", {"cursor": cursor} if cursor else {})
            page = result.get("tools")
            if not isinstance(page, list) or any(
                not isinstance(tool, dict) or not isinstance(tool.get("name"), str)
                for tool in page
            ):
                raise ClientError("MCP returned an invalid tool inventory")
            tools.extend(page)
            if len(tools) > 1000:
                raise ClientError("MCP tool inventory exceeds the client limit")
            cursor = result.get("nextCursor")
            if not cursor:
                return tools
            if not isinstance(cursor, str) or cursor in seen:
                raise ClientError("MCP returned an invalid tool pagination cursor")
            seen.add(cursor)
        raise ClientError("MCP tool inventory exceeds the client page limit")

    def call(self, name, arguments):
        # The caller's writer token and server annotations cannot expand this surface.
        if not isinstance(name, str) or name not in READ_TOOLS[self.service]:
            raise ClientError("This client permits only explicitly allowlisted read-only tools")
        if not isinstance(arguments, dict):
            raise ClientError("MCP tool arguments must be a JSON object")
        self.initialize()
        result = self._request("tools/call", {"name": name, "arguments": arguments})
        if result.get("isError"):
            raise ClientError("MCP read-only tool failed")
        structured = result.get("structuredContent")
        if structured is not None:
            if not isinstance(structured, dict):
                raise ClientError("MCP returned invalid structured tool content")
            return structured
        try:
            blocks = result["content"]
            if not isinstance(blocks, list):
                raise ValueError
            text = next(block["text"] for block in blocks if block.get("type") == "text")
            value = json.loads(text)
            if not isinstance(value, dict):
                raise ValueError
            return value
        except Exception:
            raise ClientError("MCP returned invalid JSON tool content") from None


def require_semantic(result):
    """Exact-name hits alone cannot prove the semantic channel is available."""
    try:
        healthy = (result["semantic"] is True and result.get("degraded") is False
                   and result["diagnostics"]["channels"]["semantic"]["ok"] is True)
    except (KeyError, TypeError):
        healthy = False
    if not healthy:
        raise ClientError("Semantic retrieval was not confirmed; fallback results are insufficient")


def _hits(result):
    hits = result.get("hits", result.get("results", []))
    if not isinstance(hits, list) or any(not isinstance(hit, dict) for hit in hits):
        raise ClientError("MCP returned invalid search hits")
    return hits


def smoke_test(skills, research, *, skills_query="research-library-mongodb",
               research_query="MongoDB Atlas vector search", require_sk=False):
    """Exercise both hosted services; emit metadata only and never call mutations."""
    skill_tools, research_tools = skills.tools(), research.tools()
    if len(skill_tools) < 5 or len(research_tools) < 27:
        raise ClientError("Hosted tool inventories do not meet the expected minimum counts")
    status = research.call("research_status", {})
    searches = [skills.call("skill_search", {"query": skills_query, "mode": mode, "top": 5})
                for mode in ("hybrid", "semantic")]
    for result in searches:
        require_semantic(result)
    research_result = research.call("research_search", {
        "query": research_query, "mode": "semantic", "top": 5, "breadth": "broad",
    })
    require_semantic(research_result)
    candidates = _hits(searches[0])
    if not candidates or candidates[0].get("name") != skills_query:
        raise ClientError("The smoke-test guide was not the first exact-name skill hit")
    hit = candidates[0]
    skill_id, pin = hit.get("id", hit.get("skill_id")), hit.get("release_sha256")
    if (not isinstance(skill_id, str) or not skill_id
            or not isinstance(pin, str) or not _SHA256.fullmatch(pin)):
        raise ClientError("The smoke-test skill did not provide a complete release pin")
    guide = skills.call("skill_get", {"skill_id": skill_id, "expected_sha256": pin,
                                      "max_chars": 32000})
    resource = skills.call("skill_resource", {"skill_id": skill_id, "path": "SKILL.md",
                                              "expected_sha256": pin, "max_chars": 32000})
    for result in (guide, resource):
        if (result.get("release_sha256") != pin or result.get("truncated") is not False
                or result.get("next_offset") is not None
                or not isinstance(result.get("text"), str) or not result["text"]):
            raise ClientError("The pinned smoke-test guide read was incomplete or mismatched")
    if guide["text"] != resource["text"]:
        raise ClientError("The pinned smoke-test guide and resource did not match")
    guide_sha256 = hashlib.sha256(guide["text"].encode("utf-8")).hexdigest()
    for expected in (hit.get("sha256"), guide.get("sha256"), resource.get("resource_sha256")):
        if expected is not None and (not isinstance(expected, str)
                                     or not _SHA256.fullmatch(expected)
                                     or expected != guide_sha256):
            raise ClientError("The full smoke-test guide failed its SHA256 integrity check")
    run_probe = None
    if require_sk:
        required = {"research_run_get", "research_run_list", "research_run_ledger",
                    "research_artifact_get", "research_artifact_list", "research_artifact_search",
                    "research_run_create", "research_run_checkpoint", "research_run_item_put",
                    "research_run_lease", "research_artifact_put", "research_artifact_index",
                    "research_compile"}
        if not required <= {tool["name"] for tool in research_tools}:
            raise ClientError("The research server does not expose the sk run and artifact API")
        run_probe = research.call("research_run_list", {"limit": 1})
        if not isinstance(run_probe.get("runs"), list):
            raise ClientError("The sk run inventory did not return a valid metadata page")
    result = {
        "verdict": "passed", "native_startup_tested": False, "record_writes": 0,
        "research_provider_calls": 0, "llm_research_turns": 0,
        "skills": {"tool_count": len(skill_tools), "hybrid_hits": len(candidates),
                   "semantic_hits": len(_hits(searches[1])), "semantic": True,
                   "release_sha256": pin, "guide_sha256": guide_sha256, "pinned_guide_read": True,
                   "pinned_resource_read": True},
        "research": {"tool_count": len(research_tools), "status_read": isinstance(status, dict),
                     "semantic_hits": len(_hits(research_result)), "semantic": True},
    }
    if require_sk:
        result["sk"] = {"run_api": True, "artifact_api": True, "run_inventory_read": True}
    return result


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        # argparse normally echoes invalid user values, which can contain credentials.
        raise ClientError("Invalid command line; use --help for accepted arguments")


def parser():
    root = _Parser(description=__doc__)
    root.add_argument("--codex-home", metavar="DIR",
                      help="Explicitly use DIR/config.toml hosted MCP entries")
    root.add_argument("--timeout", type=float, default=30.0, help="Per-request seconds, 0.1..60")
    commands = root.add_subparsers(dest="command", required=True)
    for service in SERVICES:
        group = commands.add_parser(service)
        actions = group.add_subparsers(dest="action", required=True)
        search = actions.add_parser("search")
        search.add_argument("query")
        search.add_argument("--mode", default="hybrid", choices=(
            "semantic", "hybrid", "lexical" if service == "skills" else "keyword"))
        search.add_argument("--top", type=int, default=5)
        search.add_argument("--require-semantic", action="store_true")
        if service == "research":
            search.add_argument("--topic-id", default="")
            search.add_argument("--breadth", choices=("broad", "narrow"), default="broad")
    tools = commands.add_parser("tools")
    tools.add_argument("--service", required=True, choices=tuple(SERVICES))
    call = commands.add_parser("call", help="Call one explicitly allowlisted read-only MCP tool")
    call.add_argument("--service", required=True, choices=tuple(SERVICES))
    call.add_argument("tool")
    call.add_argument("--arguments", help="JSON object; otherwise read a bounded object from stdin")
    smoke = commands.add_parser("smoke-test")
    smoke.add_argument("--skills-query", default="research-library-mongodb")
    smoke.add_argument("--research-query", default="MongoDB Atlas vector search")
    smoke.add_argument("--require-sk", action="store_true",
                       help="Also require the run/artifact API and read its run inventory")
    return root


def main(argv=None, *, client_factory=None, input_stream=None):
    try:
        args = parser().parse_args(argv)

        def connect(service):
            url, headers = connection_settings(service, args.codex_home)
            return (client_factory or HostedClient)(service, url, headers, timeout=args.timeout)

        if args.command == "smoke-test":
            result = smoke_test(connect("skills"), connect("research"),
                                skills_query=args.skills_query, research_query=args.research_query,
                                require_sk=args.require_sk)
        elif args.command == "tools":
            result = {"tools": connect(args.service).tools()}
        elif args.command == "call":
            if args.tool not in READ_TOOLS[args.service]:
                raise ClientError("This client permits only explicitly allowlisted read-only tools")
            raw = args.arguments
            if raw is None:
                raw = (input_stream or sys.stdin).read(MAX_REQUEST_BYTES + 1)
            if len(raw.encode("utf-8")) > MAX_REQUEST_BYTES:
                raise ClientError("MCP request exceeds the client byte limit")
            try:
                arguments = json.loads(raw)
            except Exception:
                raise ClientError("Tool arguments must be a valid JSON object") from None
            result = connect(args.service).call(args.tool, arguments)
        else:
            if not args.query.strip() or len(args.query) > 2000 or not 1 <= args.top <= 20:
                raise ClientError("Search requires a query of 1..2000 characters and top 1..20")
            arguments = {"query": args.query, "mode": args.mode, "top": args.top}
            if args.command == "research":
                if args.breadth == "narrow" and not args.topic_id:
                    raise ClientError("A narrow search requires --topic-id")
                arguments.update(topic_id=args.topic_id, breadth=args.breadth)
            result = connect(args.command).call(
                "skill_search" if args.command == "skills" else "research_search", arguments)
            if args.mode == "semantic" or args.require_semantic:
                require_semantic(result)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except ClientError as exc:
        print(json.dumps({"error": "HostedClientError", "message": str(exc)}), file=sys.stderr)
        return 2
    except Exception:
        print(json.dumps({"error": "HostedClientError", "message": "Hosted MCP operation failed"}),
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
