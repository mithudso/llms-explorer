"""Owner-local administration and an allowlisted JSON request transport."""

from __future__ import annotations

import argparse
import json
import sys

from .environment import load_environment
from .service import MAX_REQUEST_BYTES, Service, public_error


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--env-file")
    root.add_argument("--role", choices=("read", "write", "admin"), default="admin",
                      help="Local capability; OS access to this CLI is trusted")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    provision = commands.add_parser("provision")
    provision.add_argument("--wait", type=int, default=0)
    search = commands.add_parser("search")
    search.add_argument("query")
    search.add_argument("--mode", choices=("hybrid", "semantic", "keyword", "lexical"),
                        default="hybrid")
    search.add_argument("--top", type=int, default=10)
    search.add_argument("--topic-id", default="")
    search.add_argument("--scope-id", action="append")
    search.add_argument("--breadth", choices=("broad", "narrow"), default="broad")
    ingest = commands.add_parser("import")
    ingest.add_argument("--tree", action="append", default=[])
    ingest.add_argument("--queue", action="append")
    ingest.add_argument("--scores", action="append")
    ingest.add_argument("--artifact", action="append")
    ingest.add_argument("--repo")
    ingest.add_argument("--source-library",
                        help="Owner-local source snapshot library; never a remote MCP path")
    ingest.add_argument("--dry-run", action="store_true")
    ingest.add_argument("--replace-import", action="store_true")
    request = commands.add_parser("request")
    request.add_argument("operation", nargs="?",
                         help="Optional allowlisted operation; otherwise stdin envelope names it")
    serve = commands.add_parser("serve")
    serve.add_argument("--transport", choices=("stdio", "streamable-http"),
                       default="streamable-http")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8767)
    serve.add_argument("--allow-remote", action="store_true")
    serve.add_argument("--stdio-role", choices=("read", "write"), default="read")
    return root


def _request(args, stream):
    raw = stream.read(MAX_REQUEST_BYTES + 1)
    if len(raw.encode() if isinstance(raw, str) else raw) > MAX_REQUEST_BYTES:
        raise ValueError("Research request byte limit exceeded")
    packet = json.loads(raw)
    if not isinstance(packet, dict):
        raise ValueError("Research request must be an object")
    if args.operation:
        return args.operation, packet
    if set(packet) - {"operation", "arguments"}:
        raise ValueError("Unexpected request envelope field")
    if not isinstance(packet.get("operation"), str):
        raise ValueError("An operation is required")
    return packet["operation"], packet.get("arguments", {})


def main(argv=None, *, service=None, input_stream=None) -> int:
    args = parser().parse_args(argv)
    try:
        load_environment(args.env_file)
        if args.command == "serve":
            from .mcp_server import run_server
            run_server(env_file=args.env_file, transport=args.transport, host=args.host,
                       port=args.port, allow_remote=args.allow_remote, role=args.stdio_role)
            return 0
        service = service or Service()
        if args.command == "request":
            operation, arguments = _request(args, input_stream or sys.stdin)
        elif args.command == "provision":
            operation, arguments = "provision", {"wait_seconds": args.wait}
        elif args.command == "search":
            operation, arguments = "search", {
                "query": args.query, "mode": args.mode, "top": args.top,
                "topic_id": args.topic_id, "scope_ids": args.scope_id, "breadth": args.breadth,
            }
        elif args.command == "import":
            operation, arguments = "import", {
                "tree_paths": args.tree, "queue_paths": args.queue,
                "score_paths": args.scores, "artifact_paths": args.artifact,
                "repo": args.repo, "dry_run": args.dry_run,
                "source_library_path": args.source_library,
                "replace_import": args.replace_import,
            }
        else:
            operation, arguments = args.command, {}
        result = service.dispatch(operation, arguments, role=args.role, actor="local-" + args.role)
        print(json.dumps(result, ensure_ascii=False, default=str), flush=True)
        return 0
    except Exception as exc:
        # Never print a raw connection/driver exception or source text.
        print(json.dumps({"error": type(exc).__name__, "message": public_error(exc)}),
              file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
