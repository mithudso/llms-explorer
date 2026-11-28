"""Owner-local administration and an allowlisted JSON request transport."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from .environment import load_environment
from .service import MAX_REQUEST_BYTES, Service, public_error


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--env-file")
    root.add_argument("--role", choices=("read", "write", "admin"), default="admin",
                      help="Local capability; OS access to this CLI is trusted")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    prepare = commands.add_parser("writer-prepare", help="Create a private recipient token file")
    prepare.add_argument("--token-file", required=True)
    grant = commands.add_parser("writer-grant", help="Enroll a named writer's public fingerprint")
    grant.add_argument("name")
    grant.add_argument("credential_id")
    grant.add_argument("--valid-days", type=int, default=7)
    revoke = commands.add_parser("writer-revoke", help="Revoke an individual writer credential")
    revoke.add_argument("credential_id")
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
    purge = commands.add_parser(
        "purge-concepts",
        help="Erase concepts with every stored revision; owner-local, a dry run unless --apply")
    purge.add_argument("--ids-file", required=True,
                       help="One concept identity per line, at most 100")
    purge.add_argument("--apply", action="store_true")
    purge.add_argument("--include-held", action="store_true",
                       help="Also erase a concept that a lease or a legacy reservation holds")
    find = commands.add_parser(
        "find-terms",
        help="Read every stored row for private phrases; owner-local, writes its report to files")
    find.add_argument("--terms-file", required=True, help="One private phrase per line")
    find.add_argument("--out-dir", required=True,
                      help="Private directory for report.json, concept-ids.txt and concepts/")
    find.add_argument("--bodies", action="store_true",
                      help="Also read source snapshot and artifact bodies, which takes longer")
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


def _find_terms(service, args):
    """Run the phrase search and keep its findings in private files. Only counts are printed."""
    with open(args.terms_file, encoding="utf-8") as source:
        terms = [line.strip() for line in source if line.strip()]
    report = service.dispatch("find_terms", {"terms": terms, "include_bodies": args.bodies},
                              role="admin", actor="local-admin")
    out = Path(args.out_dir)
    (out / "concepts").mkdir(parents=True, exist_ok=True)
    os.chmod(out, 0o700)
    os.chmod(out / "concepts", 0o700)

    def private(path, text):
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as target:
            target.write(text)

    existing = [entry["id"] for entry in report["concepts"] if entry["exists"]]
    private(out / "report.json", json.dumps(report, ensure_ascii=False, indent=1, default=str))
    private(out / "concept-ids.txt", "".join(f"{cid}\n" for cid in existing))
    for cid in existing:
        document = service.store.concepts.find_one(service.store._owned({"_id": cid}))
        name = re.sub(r"[^a-z0-9-]+", "_", cid)
        private(out / "concepts" / f"{name}.json",
                json.dumps(document, ensure_ascii=False, indent=1, default=str))
    return {"rows_read": sum(report["rows_read"].values()),
            "rows_with_a_phrase": report["rows_with_a_phrase"],
            "concepts_with_a_phrase": len(report["concepts"]),
            "of_them_still_stored": len(existing), "not_read": report["not_read"],
            "written_to": str(out)}


def main(argv=None, *, service=None, input_stream=None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "writer-prepare":
            from .writer_request import prepare_writer
            print(json.dumps(prepare_writer(args.token_file)), flush=True)
            return 0
        load_environment(args.env_file)
        if args.command == "serve":
            from .mcp_server import run_server
            run_server(env_file=args.env_file, transport=args.transport, host=args.host,
                       port=args.port, allow_remote=args.allow_remote, role=args.stdio_role)
            return 0
        service = service or Service()
        if args.command == "find-terms":
            print(json.dumps(_find_terms(service, args)), flush=True)
            return 0
        if args.command == "request":
            operation, arguments = _request(args, input_stream or sys.stdin)
        elif args.command == "writer-grant":
            operation, arguments = "writer_grant", {"name": args.name,
                "credential_id": args.credential_id, "valid_days": args.valid_days}
        elif args.command == "writer-revoke":
            operation, arguments = "writer_revoke", {"credential_id": args.credential_id}
        elif args.command == "purge-concepts":
            with open(args.ids_file, encoding="utf-8") as source:
                wanted = [line.strip() for line in source if line.strip()]
            operation, arguments = "purge_concepts", {
                "concept_ids": wanted, "apply": args.apply, "include_held": args.include_held}
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
