"""`POST /mcp` — the hosted Model Context Protocol endpoint, and its REST twins.

Thin, like every module in `routes/`: it reads the HTTP request, hands the
JSON-RPC message to :class:`explorer_api.gateway.Gateway`, and renders whatever
comes back. Every policy decision — which tools exist, which scope reaches them,
which namespace an argument may name, what a call costs — lives in
`explorer_api.gateway`.

Two HTTP details worth stating, because both are deliberate:

* **Refusals carry a real HTTP status** as well as a JSON-RPC error body. A
  hosted MCP endpoint sits behind ordinary infrastructure — tunnels, proxies,
  client retry logic — and a 200 carrying "you are not allowed" is invisible to
  all of it. The body stays a valid JSON-RPC error so a strict MCP client still
  parses it.
* **`GET /mcp` is 405, not an SSE stream.** The gateway opens no server-initiated
  streams, and advertising one it will never write to just leaves clients
  hanging.

`POST /api/mcp/{tool}` is the REST twin 13 §5 asks for so the CLI
(`llmsx mcp call …`) and the web playground share this exact code path rather
than a second, drifting implementation of the policy.
"""

from __future__ import annotations

import json
import uuid
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import APIRouter, Depends, Header, Request, Response, status
from fastapi.responses import JSONResponse

from .. import gateway as gw
from ..db import get_session

if TYPE_CHECKING:  # pragma: no cover - typing only
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["mcp"])

#: The header an MCP client sends back after `initialize`. The gateway is
#: stateless — the API key is the session — so the id is issued, echoed and
#: otherwise unused; it exists because clients expect it.
SESSION_HEADER = "Mcp-Session-Id"


def get_hub_client(request: Request) -> gw.HubClient:
    """The one long-lived client to the hub's loopback MCP server.

    Built on first use and cached on `app.state` rather than in the app factory,
    so `main.py` needs no knowledge of the gateway and a test can override this
    dependency with a fake hub.
    """
    client = getattr(request.app.state, "hub_client", None)
    if client is None:
        settings = request.app.state.settings
        client = gw.HttpHubClient(settings.hub_mcp_url)
        request.app.state.hub_client = client
    return client


def get_catalogue(request: Request) -> gw.Catalogue:
    """The cached docset registry every namespacing check reads."""
    catalogue = getattr(request.app.state, "hub_catalogue", None)
    if catalogue is None:
        catalogue = gw.Catalogue(get_hub_client(request))
        request.app.state.hub_catalogue = catalogue
    return catalogue


Session = Annotated["AsyncSession", Depends(get_session)]
Hub = Annotated[gw.HubClient, Depends(get_hub_client)]
Cat = Annotated[gw.Catalogue, Depends(get_catalogue)]


def _client_ip(request: Request) -> str:
    """The address the public tier is rate-limited by.

    Behind the Cloudflare Tunnel every request arrives from loopback, so the
    edge's `CF-Connecting-IP` is the only real address; it is trusted precisely
    because nothing but the tunnel can reach this process.
    """
    for header in ("cf-connecting-ip", "x-forwarded-for"):
        value = request.headers.get(header)
        if value:
            return value.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def _read_message(request: Request) -> Any:
    raw = await request.body()
    if not raw:
        raise gw.BadRequest("the request body is empty")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise gw.BadRequest("the request body is not JSON") from exc


def _render(result: gw.RpcResult, *, session_id: str | None = None) -> Response:
    headers = dict(result.headers)
    if session_id:
        headers[SESSION_HEADER] = session_id
    if result.payload is None:
        return Response(status_code=result.status_code, headers=headers)
    return JSONResponse(status_code=result.status_code, content=result.payload,
                        headers=headers)


def _refusal_response(refusal: gw.GatewayRefusal, message_id: Any = None) -> Response:
    headers = {}
    if isinstance(refusal, gw.RateLimited):
        headers["Retry-After"] = str(refusal.retry_after)
    return JSONResponse(
        status_code=refusal.status_code,
        content=gw.rpc_error(message_id, refusal),
        headers=headers,
    )


@router.post("/mcp", summary="Hosted MCP endpoint (Streamable HTTP)")
async def mcp_endpoint(
    request: Request,
    session: Session,
    hub: Hub,
    catalogue: Cat,
    authorization: Annotated[str | None, Header()] = None,
) -> Response:
    settings = request.app.state.settings
    message: Any = None
    try:
        message = await _read_message(request)
        principal = await gw.authenticate(session, authorization,
                                          ip=_client_ip(request))
        result = await gw.Gateway(settings, hub, catalogue).handle(
            session, principal, message
        )
    except gw.GatewayRefusal as refusal:
        # Echo the id when the envelope had a readable one; a body we could not
        # parse has none, and JSON-RPC says `null` is the right answer then.
        message_id = message.get("id") if isinstance(message, dict) else None
        return _refusal_response(refusal, message_id)
    session_id = None
    if isinstance(message, dict) and message.get("method") == "initialize":
        session_id = f"sess_{uuid.uuid4().hex}"
    return _render(result, session_id=session_id)


@router.get("/mcp", include_in_schema=False)
@router.delete("/mcp", include_in_schema=False)
async def mcp_no_stream() -> Response:
    """No server-initiated stream, and no session state to delete."""
    return Response(status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                    headers={"Allow": "POST"})


@router.post("/api/mcp/{tool}", summary="REST twin of one MCP tool (13 §5)")
async def mcp_rest_twin(
    tool: str,
    request: Request,
    session: Session,
    hub: Hub,
    catalogue: Cat,
    authorization: Annotated[str | None, Header()] = None,
) -> Response:
    """`POST /api/mcp/<tool>` with the tool's arguments as the JSON body.

    Exactly the same policy path as `/mcp`; only the envelope differs, so the
    CLI and the playground cannot drift away from what an agent gets.
    """
    settings = request.app.state.settings
    try:
        arguments = await _read_message(request) if await request.body() else {}
        if not isinstance(arguments, dict):
            raise gw.InvalidParams("the body must be a JSON object of arguments")
        principal = await gw.authenticate(session, authorization,
                                          ip=_client_ip(request))
        result = await gw.Gateway(settings, hub, catalogue).handle(
            session,
            principal,
            {"jsonrpc": gw.JSONRPC, "id": 1, "method": "tools/call",
             "params": {"name": tool, "arguments": arguments}},
        )
    except gw.GatewayRefusal as refusal:
        return _refusal_response(refusal)
    payload = result.payload or {}
    if "error" in payload:
        return JSONResponse(status_code=result.status_code, content=payload,
                            headers=dict(result.headers))
    return JSONResponse(status_code=result.status_code,
                        content=payload.get("result"), headers=dict(result.headers))


__all__ = ["get_catalogue", "get_hub_client", "router"]
