"""mcp_demo.py — representative live demos for each hub MCP tool.

build(tool) returns (description, argv | None): argv runs the SAME code path
the MCP server exposes (its module functions / the CLIs it shells to) against
live hub data. Mutating tools (index, non-stats distill) return argv=None
plus the exact command they WOULD run — the demo never mutates state.
"""

from __future__ import annotations

import json
import subprocess

from . import core

# python -c stub that calls a hub_mcp_server tool function directly; FastMCP's
# decorator may wrap the callable, so unwrap via .fn when present.
_SERVER_CALL = (
    "import sys; "
    "sys.path.insert(0, '{scripts}'); sys.path.insert(0, '{server_dir}'); "
    "import hub_mcp_server as s; "
    "f = getattr(s.{func}, 'fn', s.{func}); "
    "print(f({args}))"
)


def _server_argv(func: str, args: str) -> list[str]:
    code = _SERVER_CALL.format(scripts=core.SCRIPTS_DIR,
                               server_dir=core.MCP_SERVER.parent,
                               func=func, args=args)
    return [core.python_for_hub(), "-c", code]


def _first_docset() -> str | None:
    try:
        out = subprocess.run(
            [core.python_for_hub(), str(core.INDEXER_SCRIPT), "list"],
            capture_output=True, text=True, timeout=60)
        entries = json.loads(out.stdout or "[]")
        return entries[0]["docset"] if entries else None
    except (OSError, subprocess.TimeoutExpired, ValueError,
            KeyError, IndexError):
        return None


def _first_mirror() -> str | None:
    for d in (core.MIRROR_OUT_DIR, core.MIRROR_SKILL_DIR / "text-mirror"):
        if d.is_dir():
            for f in sorted(d.glob("*.md")):
                return str(f)
    return None


DEMO_QUERY = "how do I install and configure this"


def build(tool: str) -> tuple[str, list[str] | None]:
    """(description, argv) for a live demo; argv None = shown-only command."""
    if tool == "hub_list_docsets":
        return ("list every indexed docset (live registry)",
                [core.python_for_hub(), str(core.INDEXER_SCRIPT), "list"])

    if tool == "hub_query_docset":
        docset = _first_docset()
        if not docset:
            return ("no docsets indexed yet — index a mirror first", None)
        return (f"semantic query against live docset '{docset}': "
                f"\"{DEMO_QUERY}\"",
                [core.python_for_hub(), str(core.INDEXER_SCRIPT), "query",
                 docset, DEMO_QUERY, "--top", "3"])

    if tool == "hub_llms_full_list":
        return ("list the local llms-full.txt mirror, filtered to 'docs'",
                _server_argv("hub_llms_full_list", "'docs', limit=20"))

    if tool == "hub_llms_full_read":
        return ("first 2000 chars of the first mirrored llms-full.txt",
                [core.python_for_hub(), "-c",
                 f"import sys; sys.path.insert(0, {str(core.SCRIPTS_DIR)!r}); "
                 "import llms_full_catalog as c; "
                 "rows = c.list_entries(); "
                 "print(c.read_entry(rows[0]['key'], limit=2000) if rows "
                 "else 'no llms-full files downloaded yet')"])

    if tool == "hub_search_codebase":
        return ("semantic search over the hub.db file index for "
                "'embedding pool health check'",
                _server_argv("hub_search_codebase",
                             "'embedding pool health check', n_results=5"))

    if tool == "hub_memory_search":
        return ("substring search of the llm-memory-pyramid for 'pipeline'",
                _server_argv("hub_memory_search", "'pipeline'"))

    if tool == "hub_memory_stats":
        return ("memory pyramid context-budget stats",
                _server_argv("hub_memory_stats", ""))

    if tool == "hub_distill_run":
        mirror = _first_mirror()
        if not mirror:
            return ("no mirror files found to run stats against", None)
        return (f"distiller stats (read-only) for {mirror}",
                _server_argv("hub_distill_run",
                             f"{mirror!r}, action='stats'"))

    if tool == "hub_index_docset":
        mirror = _first_mirror() or "<mirror.md>"
        cmd = (f"{core.python_for_hub()} {core.INDEXER_SCRIPT} index {mirror}")
        return ("MUTATING tool — not executed by the demo. It would run:\n"
                f"  {cmd}\n(use the Index tab to run it for real)", None)

    if tool == "hub_delete_docset":
        return ("MUTATING tool — not executed by the demo. Without "
                "confirm=true it is a dry run that reports what would be "
                "dropped; with it the docset's vectors, stored pages and "
                "registry row go (the mirror file stays).\n"
                "(use d on the Docsets tab to delete for real)", None)

    return (f"no demo wired for {tool}", None)
