---
title: "MCP Server Development"
description: "MCP uses JSON-RPC 2.0 with a three-layer model: Host (AI application) → Client (stateful session manager) → Server (exposes tools, resources, prompts)."
---

# MCP Server Development

## Architecture

MCP uses JSON-RPC 2.0 with a three-layer model: **Host** (AI application) → **Client** (stateful session manager) → **Server** (exposes tools, resources, prompts).

### Three server primitives

| Primitive | Direction | Purpose |
|-----------|-----------|---------|
| **Tools** | Client → Server | Executable functions the LLM can invoke |
| **Resources** | Client → Server | Read-only contextual data (URI-based) |
| **Prompts** | Client → Server | Reusable interaction templates |

## Building servers in Python (FastMCP 3.x)

```python
from fastmcp import FastMCP
mcp = FastMCP("my-server")

@mcp.tool
def search(query: str) -> str:
    """Search the database."""
    return do_search(query)

@mcp.resource("config://app")
def get_config() -> str:
    """Application configuration."""
    return json.dumps(config)
```

## Transport protocols

### stdio
- Communication via stdin/stdout of a child process
- Zero network overhead, inherently single-client
- Default for local developer tools and desktop integrations

### Streamable HTTP (introduced March 2026, replaces deprecated SSE)
- POST for client→server requests
- GET for SSE notifications (server→client)
- DELETE to terminate sessions

## Security: OAuth 2.1 + PKCE

Mandatory for public remote MCP servers since November 2025.

- **Resource indicators (RFC 8707):** bind tokens to one server — blocks cross-server replay
- **Refresh rotation:** for public clients, rotate refresh tokens on each use
- **NEVER** forward client tokens to backend services

## Best practices checklist

- [ ] Zod/Pydantic input validation — never trust raw LLM arguments
- [ ] Health checks for production deployments
- [ ] OAuth 2.1 + PKCE for any public-facing remote server
- [ ] Streamable HTTP (not deprecated SSE) for all new remote servers
- [ ] Structured logging and telemetry for production observability
