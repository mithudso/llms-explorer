# global-ai-hub MCP server

The hub's MCP tool surface. See `docs/MCP.md` for the tool inventory and
config env vars.

## Run

```bash
# stdio (normal — clients spawn it via .mcp.json at the hub root)
~/.global-ai-hub/.venv/bin/python ~/.global-ai-hub/mcp-server/hub_mcp_server.py

# HTTP (optional local daemon, 127.0.0.1:8787)
~/.global-ai-hub/.venv/bin/python ~/.global-ai-hub/mcp-server/hub_mcp_server.py --http
```

## Restart runbook (HTTP mode)

The HTTP listener runs under launchd as `com.global-ai-hub.mcp-http` (see
docs/MCP.md). Restart it — e.g. after a code change — with:

```bash
launchctl kickstart -k gui/$(id -u)/com.global-ai-hub.mcp-http
lsof -nP -iTCP:8787 -sTCP:LISTEN   # should list a fresh python pid
```

Ad-hoc, without launchd (a box where the agent is not installed):

```bash
lsof -ti :8787 | xargs kill
~/.global-ai-hub/.venv/bin/python ~/.global-ai-hub/mcp-server/hub_mcp_server.py --http &
```

stdio mode needs no lifecycle management at all.

## Setup

```bash
python3 -m venv ~/.global-ai-hub/.venv
~/.global-ai-hub/.venv/bin/pip install -r ~/.global-ai-hub/mcp-server/requirements.txt
```

## Smoke test

```bash
~/.global-ai-hub/.venv/bin/python -c "import sys; sys.path.insert(0, '$HOME/.global-ai-hub/mcp-server'); import hub_mcp_server; print('ok')"
```
Then call each tool once over stdio (an MCP client session) — the build's
smoke harness lives in the distillers STATUS.md history.
