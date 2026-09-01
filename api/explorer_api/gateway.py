"""The hosted MCP gateway: authenticate, apply tier policy, forward, meter.

The hub's own MCP server is unauthenticated on purpose — ``hub/docs/MCP.md``:
*"Localhost trust model; never expose off-box without adding auth."* This module
**is** that auth. It terminates the hosted MCP session, resolves the API key to a
user, applies :data:`TOOL_POLICY`, and only then forwards a call to
``settings.hub_mcp_url`` on loopback. The hub process never faces the tunnel.

Five rules it enforces, each of which is a way a hosted hub would otherwise leak:

1. **Absent means absent** (master D5). ``hub_ask``, ``hub_distill_run``,
   ``hub_memory_*`` and the hub-internal corpora tools are not hosted in v1. They
   are refused by name *before* scopes are even consulted, so a widened key can
   never reach them, and they are refused with the same message an unknown tool
   gets, so the hosted surface cannot be enumerated.
2. **Namespaces are walls** (13 §10). A docset key beginning ``u_`` belongs to
   exactly one user. Arguments are checked on the way out and the
   ``hub_list_docsets`` reply is filtered on the way back — a wall with one open
   side is not a wall.
3. **A path is not an argument.** ``hub_index_docset`` indexes any file the hub
   process can read, so an unconfined ``mirror_path`` from a hosted caller is a
   local-file-read primitive. Paths are resolved *inside* the caller's own store
   (master §5) and anything that escapes is refused.
4. **One limit, one place.** Every threshold comes from
   :func:`explorer_api.ledger.check_quota`; no tier number is written here.
5. **Metered work writes exactly one ledger row**, after the hub says the work
   happened — not before (billing for a failure) and not twice.

Third-party full text is never served hosted at all (master D8), so
``hub_llms_full_read`` is refused with that decision named until site claims
exist to authorise it.
"""

from __future__ import annotations

import json
import math
import re
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, Protocol

import httpx

from . import ledger
from . import models as m
from . import keys as keys_module

if TYPE_CHECKING:  # pragma: no cover - typing only
    from sqlalchemy.ext.asyncio import AsyncSession

    from .settings import Settings

# --- protocol ----------------------------------------------------------------

#: The Streamable HTTP revision this gateway speaks. Echoed on `initialize` and
#: sent upstream so the hub's FastMCP does not have to guess.
MCP_PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "llms-explorer"
#: FastMCP's streamable-http transport mounts the endpoint at `/mcp`.
HUB_ENDPOINT = "/mcp"

JSONRPC = "2.0"
#: JSON-RPC 2.0 reserved codes.
RPC_INVALID_REQUEST = -32600
RPC_METHOD_NOT_FOUND = -32601
RPC_INVALID_PARAMS = -32602
#: Application range (-32000..-32099) for everything this gateway decides.
RPC_UNAUTHORIZED = -32001
RPC_FORBIDDEN = -32002
RPC_QUOTA = -32003
RPC_RATE_LIMITED = -32004
RPC_UPSTREAM = -32005

# --- metering ----------------------------------------------------------------

#: 15 §3's ledger `component` for the MCP surface (13).
COMPONENT = "13"
#: The pool model every hosted embedding runs on (hub CLAUDE.md, `embed_core`).
EMBED_MODEL = "mxbai-embed-large"
#: Rough tokens-per-character for the query text an embedding call consumes.
#: Deliberately an estimate the *user* cannot inflate for free: it is derived
#: from the bytes they sent, not from anything the hub reports back.
CHARS_PER_TOKEN = 4

#: Unauthenticated public-tier budget, 13 §5 ("60 req/min per IP"). Enforced
#: per process — the tunnel fronts one API process today; a second one needs a
#: shared counter, which is a deployment change, not a policy change.
ANON_RATE_LIMIT = 60
ANON_RATE_WINDOW = 60.0

#: How long a `hub_list_docsets` snapshot is trusted as the public catalogue.
CATALOGUE_TTL = 30.0

#: Per-tool upstream timeouts. Indexing embeds a whole mirror through Ollama and
#: the hub allows itself 30 minutes for it (`SUBPROC_TIMEOUT`); a read that takes
#: a minute is already broken.
DEFAULT_HUB_TIMEOUT = 60.0
#: 13 §5 marks `hub_index_docset` as a *job*; until the job runner of master §4
#: exists the gateway forwards it synchronously, which is why this ceiling is
#: the hub's own and not a web timeout. A long index therefore holds one request
#: (and one database connection) for its duration — the reason the job hand-off
#: is the next thing this tool needs, not a bigger timeout.
HUB_TIMEOUTS: Mapping[str, float] = {
    "hub_index_docset": 60.0 * 30,
    "hub_delete_docset": 120.0,
    "hub_query_docset": 120.0,
}

#: Everything the hub registers that must not exist on the hosted server
#: (master D5, 13 §5). Absent is checked before scope, so no key reaches these.
ABSENT_TOOLS: frozenset[str] = frozenset({
    "hub_ask",              # D5 — local only in v1
    "hub_distill_run",      # D5 — runs the owner's distillers repo
    "hub_memory_search",    # D5 — the owner's memory pyramid
    "hub_memory_stats",     # D5
    "hub_search_codebase",  # 13 §5 — hub-internal corpora
    "hub_search_symbols",   # 13 §5
    "hub_route",            # 13 §5
})


# --- errors ------------------------------------------------------------------


class GatewayRefusal(Exception):
    """A refusal with both an HTTP status and a JSON-RPC error to render.

    Every message here is written to be safe to show a stranger: it names the
    decision (a document reference) and never an internal host, path or
    traceback.
    """

    status_code = 400
    rpc_code = RPC_INVALID_REQUEST
    code = "bad_request"

    def __init__(self, message: str, **data: Any) -> None:
        super().__init__(message)
        self.message = message
        self.data: dict[str, Any] = {"code": self.code, **data}


class BadRequest(GatewayRefusal):
    pass


class InvalidParams(GatewayRefusal):
    status_code = 400
    rpc_code = RPC_INVALID_PARAMS
    code = "invalid_params"


class NotHosted(GatewayRefusal):
    """An absent or unknown tool. Both get this, and the same wording."""

    status_code = 404
    rpc_code = RPC_METHOD_NOT_FOUND
    code = "not_hosted"


class Unauthorized(GatewayRefusal):
    status_code = 401
    rpc_code = RPC_UNAUTHORIZED
    code = "unauthorized"


class Forbidden(GatewayRefusal):
    status_code = 403
    rpc_code = RPC_FORBIDDEN
    code = "forbidden"


class QuotaExceeded(GatewayRefusal):
    status_code = 402
    rpc_code = RPC_QUOTA
    code = "quota"


class RateLimited(GatewayRefusal):
    status_code = 429
    rpc_code = RPC_RATE_LIMITED
    code = "rate_limited"

    def __init__(self, message: str, retry_after: int, **data: Any) -> None:
        super().__init__(message, retry_after=retry_after, **data)
        self.retry_after = retry_after


class HubUnavailable(GatewayRefusal):
    """The hub did not answer, or answered something this gateway cannot trust.

    Raised by the client *and* by the reply filters: a `hub_list_docsets` body
    we cannot parse is a body we cannot redact, and forwarding it unredacted
    would leak every user's namespace.
    """

    status_code = 502
    rpc_code = RPC_UPSTREAM
    code = "upstream_unavailable"


def unknown_tool(tool: str) -> NotHosted:
    """The one refusal an absent tool and a nonexistent tool both get.

    Telling them apart would let anyone map the hosted surface by probing.
    """
    return NotHosted(f"tool {tool!r} is not hosted on this server", tool=tool)


# --- namespaces --------------------------------------------------------------

#: `u_<user>__<name>` (13 §5/§10). The double underscore is the separator, which
#: is what stops one namespace being a prefix of another.
NAMESPACE_SEPARATOR = "__"
NAMESPACE_PREFIX = "u_"
_DOCSET_RE = re.compile(r"\A[A-Za-z0-9._-]+(?:__[A-Za-z0-9._-]+)*\Z")


def namespace_token(user: m.User) -> str:
    """The ``<user>`` half of ``u_<user>__``.

    Derived from the account id, which is stable, lowercase, unique and not
    user-chosen — so it cannot be picked to collide with a public docset key.
    15 §7 has no handle column yet; when it gains one this function is the only
    place that changes.
    """
    return user.id.removeprefix("usr_")


def namespace_for(user: m.User) -> str:
    """``u_<user>__`` — the prefix every docset key this user owns must carry."""
    return f"{NAMESPACE_PREFIX}{namespace_token(user)}{NAMESPACE_SEPARATOR}"


def is_namespaced(key: str) -> bool:
    return key.startswith(NAMESPACE_PREFIX)


# --- policy ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ToolPolicy:
    """One row of 13 §5's tool inventory, as the gateway enforces it."""

    name: str
    #: ``public`` needs no key; ``read``/``run`` need one carrying that scope.
    tier: str
    #: The scope a key must hold. ``None`` for the public tier.
    scope: str | None = None
    #: Docset keys that must already exist: the caller's own, or public.
    ref_args: tuple[str, ...] = ()
    #: Docset keys the call creates or destroys: the caller's own, only.
    own_args: tuple[str, ...] = ()
    #: Filesystem arguments, confined to the caller's store (master §5).
    path_args: tuple[str, ...] = ()
    #: The `plans` feature this call spends, checked before forwarding.
    quota_feature: str | None = None
    #: Write a ledger row after a successful call.
    metered: bool = False
    #: Charge the user for it. `False` still records the row — 15 §3 keeps the
    #: cost visible even when the user is not billed.
    billable: bool = True
    #: 15 §3's ledger `reason`, which is also how daily counters find the row.
    reason: str | None = None
    #: A flat refusal with the decision that requires it, or ``None``.
    refuse: str | None = None
    #: The argument whose value selects a variant (``mode`` on a query).
    variant_arg: str | None = None
    variant_default: str | None = None
    variants: Mapping[str, ToolPolicy] = field(default_factory=dict)

    @property
    def needs_key(self) -> bool:
        return self.tier != "public"


def _query(tier: str, scope: str, *, quota: str, metered: bool,
           billable: bool, reason: str | None) -> ToolPolicy:
    return ToolPolicy(
        name="hub_query_docset", tier=tier, scope=scope, ref_args=("docset",),
        quota_feature=quota, metered=metered, billable=billable, reason=reason,
    )


def _build_policy() -> dict[str, ToolPolicy]:
    keyword = _query("read", "read",
                     quota="keyword_queries_per_day", metered=True, billable=False,
                     reason=ledger.QUERY_REASON)
    embedded = _query("run", "run",
                      quota="semantic_queries", metered=True, billable=True,
                      reason=None)
    policies = [
        # --- public reads (13 §5) ------------------------------------------
        ToolPolicy("hub_llms_full_list", tier="public"),
        ToolPolicy("hub_list_docsets", tier="public"),
        ToolPolicy("hub_docset_index", tier="public", ref_args=("docset",)),
        ToolPolicy("hub_concept_tree", tier="public"),
        ToolPolicy("hub_concept_lookup", tier="public"),
        ToolPolicy("hub_concept_frontier", tier="public"),
        # 10 §5 / master §3a: a step-2 hub addition. Listed so the tier is
        # decided here rather than by whichever tool happens to exist upstream;
        # until the hub registers it, a call gets the hub's own "unknown tool".
        ToolPolicy("hub_directory_score", tier="public"),
        # --- refused outright ----------------------------------------------
        ToolPolicy(
            "hub_llms_full_read", tier="read", scope="read",
            refuse=(
                "mirrored third-party full text is not served by the hosted "
                "server (master D8) — follow the source's own URL from the "
                "directory. Pages are returned only to that site's claimed-site "
                "owner, and site claims are not implemented yet."
            ),
        ),
        ToolPolicy(
            "hub_concept_queue", tier="read", scope="publish",
            refuse=(
                "parking a concept on the public tree goes through the "
                "moderation queue (05 §4); the hosted queue endpoint lands with "
                "moderation, not with the gateway."
            ),
        ),
        # --- keyed reads ----------------------------------------------------
        ToolPolicy(
            "hub_query_docset", tier=keyword.tier, scope=keyword.scope,
            ref_args=("docset",), variant_arg="mode", variant_default="semantic",
            variants={"keyword": keyword, "semantic": embedded, "hybrid": embedded},
        ),
        # --- metered writes, own namespace only (D5) ------------------------
        ToolPolicy(
            "hub_index_docset", tier="run", scope="run",
            own_args=("name",), path_args=("mirror_path",),
            quota_feature="indexes", metered=True,
        ),
        ToolPolicy(
            "hub_delete_docset", tier="run", scope="run", own_args=("docset",),
        ),
    ]
    return {policy.name: policy for policy in policies}


#: 13 §5's inventory. Read tools are public where the spoke says public; the
#: two write tools are `run` and confined to the caller's own namespace (D5).
TOOL_POLICY: Mapping[str, ToolPolicy] = _build_policy()

#: Sanity: a tool cannot be both hosted and absent. Caught at import, not in prod.
assert not (set(TOOL_POLICY) & ABSENT_TOOLS), "a tool is both hosted and absent"


def resolve_policy(tool: object, arguments: Mapping[str, Any]) -> ToolPolicy:
    """The policy in force for this call, or :class:`NotHosted`.

    Absent tools are checked first and by name, so no scope, argument or
    variant can route around them.
    """
    if not isinstance(tool, str) or not tool:
        raise InvalidParams("params.name must be a tool name")
    if tool in ABSENT_TOOLS:
        raise unknown_tool(tool)
    base = TOOL_POLICY.get(tool)
    if base is None:
        raise unknown_tool(tool)
    if base.variant_arg is None:
        return base
    chosen = arguments.get(base.variant_arg, base.variant_default)
    variant = base.variants.get(chosen) if isinstance(chosen, str) else None
    if variant is None:
        allowed = ", ".join(sorted(base.variants))
        raise InvalidParams(
            f"{base.variant_arg} must be one of {allowed}", tool=tool
        )
    return variant


def visible_tools(scopes: frozenset[str]) -> frozenset[str]:
    """Which hosted tools a caller with ``scopes`` may actually call.

    `tools/list` is filtered through this: advertising a tool the caller will
    only ever be refused is both noise and a hint about the surface.
    """
    return frozenset(
        name
        for name, policy in TOOL_POLICY.items()
        if policy.refuse is None
        and (policy.scope is None or policy.scope in scopes)
    )


# --- principals --------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Principal:
    """Who is calling: a key's owner, or nobody (the public tier)."""

    user: m.User | None = None
    key: m.ApiKey | None = None
    scopes: frozenset[str] = frozenset()
    namespace: str | None = None
    ip: str = "unknown"

    @property
    def anonymous(self) -> bool:
        return self.user is None


_BEARER = re.compile(r"\ABearer\s+(?P<key>\S+)\Z", re.IGNORECASE)


async def authenticate(
    session: AsyncSession, authorization: str | None, *, ip: str = "unknown"
) -> Principal:
    """Resolve ``Authorization: Bearer …`` to a principal.

    No header at all is the anonymous public tier. A header that is present but
    does not resolve is an error, never a silent downgrade to anonymous — a
    revoked key must fail loudly rather than quietly lose its scopes.
    """
    if authorization is None or not authorization.strip():
        return Principal(ip=ip)
    match = _BEARER.match(authorization.strip())
    if match is None:
        raise Unauthorized("Authorization must be `Bearer <api key>`")
    row = await keys_module.authenticate(session, match.group("key"))
    if row is None:
        # One answer for malformed, unknown, wrong-secret and revoked, so the
        # four cannot be told apart from outside.
        raise Unauthorized("that API key is not valid")
    user = await session.get(m.User, row.user_id)
    if user is None or user.deleted_at is not None:  # pragma: no cover - FK guards it
        raise Unauthorized("that API key is not valid")
    return Principal(user=user, key=row, scopes=frozenset(row.scopes),
                     namespace=namespace_for(user), ip=ip)


# --- rate limiting -----------------------------------------------------------

_anon_hits: dict[str, deque[float]] = defaultdict(deque)


def reset_rate_limits() -> None:
    """Drop every window. For tests, and for a deliberate operator reset."""
    _anon_hits.clear()


def _check_anon_rate(ip: str, *, now: float | None = None) -> None:
    now = time.monotonic() if now is None else now
    window = _anon_hits[ip]
    cutoff = now - ANON_RATE_WINDOW
    while window and window[0] <= cutoff:
        window.popleft()
    if len(window) >= ANON_RATE_LIMIT:
        retry = max(1, math.ceil(window[0] + ANON_RATE_WINDOW - now))
        raise RateLimited(
            f"the public tier allows {ANON_RATE_LIMIT} requests per "
            f"{int(ANON_RATE_WINDOW)}s per address; use an API key for more",
            retry_after=retry,
        )
    window.append(now)


# --- the hub client ----------------------------------------------------------


class HubClient(Protocol):
    """What the gateway needs from the hub's MCP server."""

    async def list_tools(self) -> list[dict]: ...

    async def call_tool(
        self, name: str, arguments: Mapping[str, Any], *, timeout: float | None = None
    ) -> dict: ...


class HttpHubClient:
    """Streamable HTTP client for ``hub_mcp_server.py --http`` on loopback.

    Holds one MCP session for the process: `initialize`, then
    `notifications/initialized`, then calls carrying `Mcp-Session-Id`. A session
    the hub has forgotten (404/400 on a call) is re-established once and the
    call retried, because the hub restarts far more often than this gateway does.
    """

    def __init__(self, base_url: str, *, transport: httpx.BaseTransport | None = None,
                 timeout: float = DEFAULT_HUB_TIMEOUT) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            transport=transport,
            timeout=timeout,
            headers={"Accept": "application/json, text/event-stream",
                     "Content-Type": "application/json"},
        )
        self._session_id: str | None = None
        self._next_id = 0

    async def aclose(self) -> None:
        await self._client.aclose()

    # -- protocol plumbing ---------------------------------------------------

    def _id(self) -> int:
        self._next_id += 1
        return self._next_id

    def _headers(self) -> dict[str, str]:
        headers = {"MCP-Protocol-Version": MCP_PROTOCOL_VERSION}
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        return headers

    @staticmethod
    def _decode(response: httpx.Response) -> dict:
        """One JSON-RPC message, from either an SSE stream or a JSON body."""
        content_type = response.headers.get("content-type", "")
        text = response.text
        if content_type.startswith("text/event-stream"):
            for line in text.splitlines():
                if line.startswith("data:"):
                    try:
                        return json.loads(line[len("data:"):].strip())
                    except json.JSONDecodeError as exc:
                        raise HubUnavailable("the hub sent an unreadable event") from exc
            raise HubUnavailable("the hub sent an empty event stream")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise HubUnavailable("the hub sent an unreadable reply") from exc

    async def _post(self, payload: dict, *, timeout: float | None) -> httpx.Response:
        try:
            return await self._client.post(
                HUB_ENDPOINT, json=payload, headers=self._headers(),
                timeout=timeout if timeout is not None else self._client.timeout,
            )
        except httpx.HTTPError as exc:
            # The hub's address must never reach a caller, so the detail stays
            # in the chained exception (logs) and not in the message.
            raise HubUnavailable("the hub did not answer") from exc

    async def _initialize(self) -> None:
        response = await self._post(
            {
                "jsonrpc": JSONRPC, "id": self._id(), "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": SERVER_NAME, "version": "1"},
                },
            },
            timeout=DEFAULT_HUB_TIMEOUT,
        )
        if response.status_code >= 400:
            raise HubUnavailable("the hub refused the session")
        self._session_id = (
            response.headers.get("mcp-session-id")
            or response.headers.get("Mcp-Session-Id")
            or self._session_id
        )
        self._decode(response)
        await self._post(
            {"jsonrpc": JSONRPC, "method": "notifications/initialized"},
            timeout=DEFAULT_HUB_TIMEOUT,
        )

    async def _rpc(self, method: str, params: dict, *, timeout: float | None) -> Any:
        if self._session_id is None:
            await self._initialize()
        payload = {"jsonrpc": JSONRPC, "id": self._id(), "method": method,
                   "params": params}
        response = await self._post(payload, timeout=timeout)
        if response.status_code in (400, 404) and self._session_id is not None:
            # The hub restarted and forgot us. Re-handshake once, then retry.
            self._session_id = None
            await self._initialize()
            payload["id"] = self._id()
            response = await self._post(payload, timeout=timeout)
        if response.status_code >= 400:
            raise HubUnavailable("the hub refused the call")
        message = self._decode(response)
        if "error" in message:
            detail = message["error"]
            # The hub's own error text can carry box paths and interpreter
            # names, so it stays in the chained cause (logs) and out of the
            # reply. The caller learns that the hub failed, not how.
            raise HubUnavailable("the hub reported an error") from RuntimeError(
                str(detail.get("message", "unknown"))
            )
        return message.get("result")

    # -- the protocol the gateway uses --------------------------------------

    async def list_tools(self) -> list[dict]:
        result = await self._rpc("tools/list", {}, timeout=DEFAULT_HUB_TIMEOUT)
        tools = (result or {}).get("tools")
        if not isinstance(tools, list):
            raise HubUnavailable("the hub sent an unreadable tool list")
        return tools

    async def call_tool(self, name: str, arguments: Mapping[str, Any], *,
                        timeout: float | None = None) -> dict:
        result = await self._rpc("tools/call",
                                 {"name": name, "arguments": dict(arguments)},
                                 timeout=timeout)
        if not isinstance(result, dict):
            raise HubUnavailable("the hub sent an unreadable tool result")
        return result


# --- the public catalogue ----------------------------------------------------


async def call_hub(hub: HubClient, tool: str, arguments: Mapping[str, Any], *,
                   timeout: float | None = None) -> dict:
    """Call the hub, turning *any* failure into a 502 that names no internals.

    The :class:`HubClient` contract says failures arrive as
    :class:`HubUnavailable`, but a gateway that trusts a contract to hold is one
    stack trace away from returning a 500 with the hub's address in it.
    """
    try:
        result = await hub.call_tool(tool, arguments, timeout=timeout)
    except GatewayRefusal:
        raise
    except Exception as exc:
        raise HubUnavailable("the hub did not answer") from exc
    if not isinstance(result, Mapping):
        raise HubUnavailable("the hub sent an unreadable tool result")
    return dict(result)


async def list_hub_tools(hub: HubClient) -> list[dict]:
    """:meth:`HubClient.list_tools`, guarded the same way as :func:`call_hub`."""
    try:
        tools = await hub.list_tools()
    except GatewayRefusal:
        raise
    except Exception as exc:
        raise HubUnavailable("the hub did not answer") from exc
    if not isinstance(tools, list):
        raise HubUnavailable("the hub sent an unreadable tool list")
    return tools


class Catalogue:
    """The hub's docset registry, cached, split into public and per-user.

    Every namespacing decision reads this, so it is deliberately a short-lived
    snapshot rather than a long cache: a docset that has just been deleted must
    stop being referenceable in seconds, not minutes.
    """

    def __init__(self, hub: HubClient, ttl: float = CATALOGUE_TTL) -> None:
        self._hub = hub
        self._ttl = ttl
        self._entries: list[dict] | None = None
        self._expires = 0.0

    def invalidate(self) -> None:
        self._entries = None
        self._expires = 0.0

    async def entries(self) -> list[dict]:
        now = time.monotonic()
        if self._entries is None or now >= self._expires:
            self._entries = parse_docset_entries(
                await call_hub(self._hub, "hub_list_docsets", {})
            )
            self._expires = now + self._ttl
        return self._entries

    async def public_keys(self) -> frozenset[str]:
        return frozenset(
            key for key in (_entry_key(e) for e in await self.entries())
            if key and not is_namespaced(key)
        )

    async def count_owned(self, namespace: str) -> int:
        """How many docsets the namespace holds, ignoring the `__facts` twins.

        `docset_refine` writes a facts layer beside every raw layer under a
        derived key; counting both would charge a user twice for one index.
        """
        return sum(
            1
            for key in (_entry_key(e) for e in await self.entries())
            if key and key.startswith(namespace) and not key.endswith("__facts")
        )


def _entry_key(entry: object) -> str | None:
    if isinstance(entry, Mapping):
        value = entry.get("docset") or entry.get("key")
        return value if isinstance(value, str) else None
    return None


def result_text(result: Mapping[str, Any]) -> str:
    """The text of an MCP tool result, or :class:`HubUnavailable`."""
    content = result.get("content")
    if not isinstance(content, list):
        raise HubUnavailable("the hub sent a result with no content")
    parts = [
        block.get("text", "")
        for block in content
        if isinstance(block, Mapping) and block.get("type") == "text"
    ]
    if not parts:
        raise HubUnavailable("the hub sent a result with no text")
    return "".join(parts)


def parse_docset_entries(result: Mapping[str, Any]) -> list[dict]:
    """`hub_list_docsets`' JSON payload, as a list of rows.

    A payload we cannot parse is an error rather than a pass-through: an
    unparseable listing is one we cannot redact, and forwarding it unredacted
    would hand every namespace to every caller.
    """
    text = result_text(result)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise HubUnavailable("the hub sent an unreadable docset listing") from exc
    rows = payload.get("docsets") if isinstance(payload, Mapping) else payload
    if not isinstance(rows, list):
        raise HubUnavailable("the hub sent an unreadable docset listing")
    return [row for row in rows if isinstance(row, Mapping)]


# --- argument checking -------------------------------------------------------


def _string_arg(arguments: Mapping[str, Any], name: str) -> str | None:
    value = arguments.get(name)
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise InvalidParams(f"{name} must be a string")
    return value


def check_docset_name(value: str) -> str:
    """A docset key must look like one — no paths, no globs, no separators."""
    if not _DOCSET_RE.match(value) or ".." in value:
        raise InvalidParams("that is not a valid docset key")
    return value


async def check_namespacing(
    policy: ToolPolicy,
    arguments: Mapping[str, Any],
    principal: Principal,
    catalogue: Catalogue,
) -> None:
    """Refuse any docset argument the caller has no claim to.

    ``own_args`` create or destroy: they must sit in the caller's namespace.
    ``ref_args`` read something that exists: the caller's namespace, or the
    shared catalogue — and nothing else, so an unlisted or foreign key never
    reaches the hub, where the namespace convention has no meaning at all.
    """
    for name in policy.own_args:
        value = _string_arg(arguments, name)
        if value is None:
            raise InvalidParams(f"{name} is required")
        check_docset_name(value)
        if principal.namespace is None or not value.startswith(principal.namespace):
            raise Forbidden(
                f"{name} must be in your own namespace "
                f"({principal.namespace or 'sign in first'}…)",
                argument=name,
            )

    if not policy.ref_args:
        return
    public = None
    for name in policy.ref_args:
        value = _string_arg(arguments, name)
        if value is None:
            raise InvalidParams(f"{name} is required")
        check_docset_name(value)
        if is_namespaced(value):
            if principal.namespace is None or not value.startswith(principal.namespace):
                # 404 would be friendlier to the honest caller and worse for
                # everyone else: it would confirm which keys exist. One answer.
                raise Forbidden("no such docset, or it is not yours", argument=name)
            continue
        if public is None:
            public = await catalogue.public_keys()
        # The facts twin of a public docset is public too.
        if value not in public and value.removesuffix("__facts") not in public:
            raise Forbidden("no such docset, or it is not yours", argument=name)


def confine_path(stores_root: Path, user: m.User, value: str) -> str:
    """Resolve ``value`` **inside** the caller's own store, or refuse.

    `hub_index_docset` reads whatever path it is given, on the box, as the hub
    user. A hosted caller therefore never names an absolute path directly: a
    relative one is resolved under ``stores_root/<user id>/`` and an absolute
    one is accepted only if it is already inside it. Symlinks are resolved
    before the check, so a link planted inside the store cannot point out of it.
    """
    root = (stores_root / user.id).resolve()
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        # PurePosixPath keeps a client's `/`-separated path meaningful on any
        # server platform; `..` is still resolved (and caught) below.
        candidate = root / PurePosixPath(value)
    resolved = _resolve_without_requiring_existence(candidate)
    if resolved != root and root not in resolved.parents:
        raise Forbidden(
            "that path is outside your store; give a path relative to it",
            argument="path",
        )
    return str(resolved)


def _resolve_without_requiring_existence(path: Path) -> Path:
    """`Path.resolve()` semantics that do not care whether the file is there yet.

    The mirror may be uploaded moments before it is indexed, and a check that
    demanded existence would be a race rather than a rule.
    """
    return Path(path).resolve()


async def check_arguments(
    settings: Settings,
    policy: ToolPolicy,
    arguments: Mapping[str, Any],
    principal: Principal,
    catalogue: Catalogue,
) -> dict[str, Any]:
    """Everything that must be true of the arguments, and the rewrite they get."""
    outgoing = dict(arguments)
    await check_namespacing(policy, arguments, principal, catalogue)
    for name in policy.path_args:
        value = _string_arg(arguments, name)
        if value is None:
            raise InvalidParams(f"{name} is required")
        if principal.user is None:
            # Unreachable: every tool with a path argument is a keyed tier, so
            # the scope check refuses first. Kept as a raise rather than an
            # assert because `python -O` deletes asserts and this one guards a
            # filesystem boundary.
            raise Unauthorized(f"{policy.name} needs an API key")
        outgoing[name] = confine_path(settings.stores_root, principal.user, value)
    return outgoing


# --- quotas and metering -----------------------------------------------------


async def check_quota(
    session: AsyncSession, policy: ToolPolicy, principal: Principal,
    catalogue: Catalogue,
) -> None:
    """Ask :mod:`explorer_api.ledger` — the single place a limit is enforced."""
    if policy.quota_feature is None or principal.user is None:
        return
    used = None
    if policy.quota_feature == "indexes" and principal.namespace is not None:
        # Docsets live in the per-user store, not Postgres (master §5), so the
        # count comes from the store's own registry rather than a table.
        used = await catalogue.count_owned(principal.namespace)
    verdict = await ledger.check_quota(
        session, principal.user, policy.quota_feature, used=used
    )
    if not verdict.allowed:
        raise QuotaExceeded(
            f"your {verdict.tier} plan does not allow this call",
            **verdict.as_error(),
        )


def metered_units(policy: ToolPolicy, tool: str, arguments: Mapping[str, Any],
                  result: Mapping[str, Any]) -> int:
    """How many embedding units this call spent.

    Query embeddings are charged on the text the caller sent, which is the text
    that gets embedded and is the one number they cannot inflate for free.
    Indexing is charged on the chunk count the hub reports; a hub that reports
    none yields a zero-unit row — the call is still on the record, and 15 §3's
    correction path is another row, never an edit.
    """
    if not policy.billable:
        return 0
    if tool == "hub_query_docset":
        question = arguments.get("question")
        text = question if isinstance(question, str) else ""
        return max(1, math.ceil(len(text) / CHARS_PER_TOKEN))
    return _reported_units(result)


def _reported_units(result: Mapping[str, Any]) -> int:
    try:
        payload = json.loads(result_text(result))
    except (HubUnavailable, json.JSONDecodeError):
        return 0
    if not isinstance(payload, Mapping):
        return 0
    for name in ("units", "chunks", "embedded"):
        value = payload.get(name)
        if isinstance(value, int) and value >= 0:
            return value
    return 0


async def meter(
    session: AsyncSession, policy: ToolPolicy, principal: Principal, tool: str,
    arguments: Mapping[str, Any], result: Mapping[str, Any], call_id: str,
) -> None:
    """One ledger row for one successful metered call. Never before the work."""
    if not policy.metered or principal.user is None:
        return
    await ledger.record(
        session, principal.user, COMPONENT, "embedding", EMBED_MODEL,
        metered_units(policy, tool, arguments, result),
        call_id=call_id, billable=policy.billable, reason=policy.reason,
    )


# --- replies -----------------------------------------------------------------


def filter_reply(tool: str, principal: Principal, result: dict) -> dict:
    """Redact anything in a hub reply the caller is not entitled to see.

    Only `hub_list_docsets` carries other users' keys today; it is filtered
    rather than passed through, because a namespace wall that only checks the
    outgoing arguments is not a wall.
    """
    if tool != "hub_list_docsets":
        return result
    rows = parse_docset_entries(result)
    namespace = principal.namespace
    kept = [
        row for row in rows
        if (key := _entry_key(row)) is not None
        and (not is_namespaced(key) or (namespace and key.startswith(namespace)))
    ]
    return {"content": [{"type": "text", "text": json.dumps(kept, indent=2)}],
            "isError": bool(result.get("isError", False))}


# --- the gateway -------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RpcResult:
    """What the route should send back."""

    status_code: int
    payload: dict | None
    headers: dict[str, str] = field(default_factory=dict)


def rpc_error(message_id: Any, refusal: GatewayRefusal) -> dict:
    return {
        "jsonrpc": JSONRPC,
        "id": message_id,
        "error": {"code": refusal.rpc_code, "message": refusal.message,
                  "data": refusal.data},
    }


def rpc_ok(message_id: Any, result: Any) -> dict:
    return {"jsonrpc": JSONRPC, "id": message_id, "result": result}


class Gateway:
    """One request's worth of policy. Stateless; the caches live outside it."""

    def __init__(self, settings: Settings, hub: HubClient, catalogue: Catalogue) -> None:
        self.settings, self.hub, self.catalogue = settings, hub, catalogue

    async def handle(
        self, session: AsyncSession, principal: Principal, message: Any
    ) -> RpcResult:
        """Dispatch one JSON-RPC message. Refusals come back as errors, not raises."""
        if not isinstance(message, Mapping):
            raise BadRequest("the body must be a single JSON-RPC object; "
                             "batches are not supported")
        if message.get("jsonrpc") != JSONRPC:
            raise BadRequest("jsonrpc must be \"2.0\"")
        method = message.get("method")
        if not isinstance(method, str):
            raise BadRequest("method is required")
        message_id = message.get("id")
        params = message.get("params") or {}
        if not isinstance(params, Mapping):
            raise InvalidParams("params must be an object")

        if message_id is None:
            # A notification. Nothing here needs one; acknowledge and stop.
            return RpcResult(202, None)

        try:
            result = await self._method(session, principal, method, params)
        except GatewayRefusal as refusal:
            headers = {}
            if isinstance(refusal, RateLimited):
                headers["Retry-After"] = str(refusal.retry_after)
            return RpcResult(refusal.status_code, rpc_error(message_id, refusal),
                             headers)
        return RpcResult(200, rpc_ok(message_id, result))

    async def _method(
        self, session: AsyncSession, principal: Principal, method: str,
        params: Mapping[str, Any],
    ) -> Any:
        if method == "initialize":
            return self._initialize()
        if method == "ping":
            return {}
        if method == "tools/list":
            return await self._tools_list(principal)
        if method == "tools/call":
            return await self._tools_call(session, principal, params)
        raise NotHosted(f"method {method!r} is not supported by this gateway")

    def _initialize(self) -> dict:
        """The hosted session is terminated here, not proxied to the hub."""
        return {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "version": "1"},
            "instructions": (
                "Hosted LLMS-Explorer tools over the global AI hub. Public tools "
                "need no key; keyed tools take `Authorization: Bearer llmsx_…`. "
                "Your own docsets are named u_<you>__<name>."
            ),
        }

    async def _tools_list(self, principal: Principal) -> dict:
        allowed = visible_tools(principal.scopes)
        upstream = await list_hub_tools(self.hub)
        tools = [
            tool for tool in upstream
            if isinstance(tool, Mapping) and tool.get("name") in allowed
        ]
        # A hosted tool the hub has not registered yet (10 §5's
        # `hub_directory_score`) simply does not appear — the policy names the
        # tier, the hub decides what exists.
        return {"tools": tools}

    async def _tools_call(
        self, session: AsyncSession, principal: Principal, params: Mapping[str, Any]
    ) -> dict:
        arguments = params.get("arguments", {})
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, Mapping):
            raise InvalidParams("params.arguments must be an object")
        policy = resolve_policy(params.get("name"), arguments)
        tool = policy.name

        if policy.refuse is not None:
            raise Forbidden(policy.refuse, tool=tool)
        if policy.needs_key and principal.anonymous:
            raise Unauthorized(f"{tool} needs an API key with the "
                               f"{policy.scope!r} scope")
        if policy.scope is not None and policy.scope not in principal.scopes:
            raise Forbidden(
                f"{tool} needs the {policy.scope!r} scope; this key has "
                f"{sorted(principal.scopes)}",
                tool=tool, required_scope=policy.scope,
            )
        if principal.anonymous:
            _check_anon_rate(principal.ip)

        outgoing = await check_arguments(self.settings, policy, arguments, principal,
                                         self.catalogue)
        await check_quota(session, policy, principal, self.catalogue)

        call_id = f"mcp_{uuid.uuid4().hex}"
        result = await call_hub(
            self.hub, tool, outgoing,
            timeout=HUB_TIMEOUTS.get(tool, DEFAULT_HUB_TIMEOUT),
        )
        if policy.own_args:
            # The registry just changed under us; the next namespacing check
            # and the next quota count must not read a stale snapshot.
            self.catalogue.invalidate()

        await meter(session, policy, principal, tool, arguments, result, call_id)
        await session.commit()
        return filter_reply(tool, principal, result)


__all__ = [
    "ABSENT_TOOLS",
    "ANON_RATE_LIMIT",
    "ANON_RATE_WINDOW",
    "COMPONENT",
    "EMBED_MODEL",
    "HUB_TIMEOUTS",
    "MCP_PROTOCOL_VERSION",
    "TOOL_POLICY",
    "BadRequest",
    "Catalogue",
    "Forbidden",
    "Gateway",
    "GatewayRefusal",
    "HttpHubClient",
    "HubClient",
    "HubUnavailable",
    "InvalidParams",
    "NotHosted",
    "Principal",
    "QuotaExceeded",
    "RateLimited",
    "RpcResult",
    "ToolPolicy",
    "Unauthorized",
    "authenticate",
    "call_hub",
    "check_arguments",
    "check_namespacing",
    "check_quota",
    "confine_path",
    "filter_reply",
    "is_namespaced",
    "list_hub_tools",
    "meter",
    "namespace_for",
    "namespace_token",
    "parse_docset_entries",
    "reset_rate_limits",
    "resolve_policy",
    "result_text",
    "rpc_error",
    "rpc_ok",
    "visible_tools",
]
