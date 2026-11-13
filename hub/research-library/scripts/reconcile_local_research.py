#!/usr/bin/env python3
"""Private owner-local source archive; no new research or paid judges."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path

from research_library_service import local_reconcile
from research_library_service.environment import load_environment


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--receipt-dir", type=Path, required=True)
    parser.add_argument("--parent-run")
    parser.add_argument("--owner", default="local-research-reconciliation")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--inventory", type=Path, required=True)
    prepare.add_argument("--denylist", type=Path, action="append", default=[])
    prepare.add_argument("--bundle-bytes", type=int, default=local_reconcile.BUNDLE_BYTES)
    delta = commands.add_parser("prepare-delta")
    delta.add_argument("--layer", type=Path, action="append", required=True)
    delta.add_argument("--current-inventory", type=Path, required=True)
    delta.add_argument("--scope-receipt", type=Path, action="append", default=[])
    delta.add_argument("--denylist", type=Path, action="append", default=[])
    delta.add_argument("--bundle-bytes", type=int, default=local_reconcile.BUNDLE_BYTES)
    delta.add_argument("--admission-ledger", type=Path)
    delta.add_argument("--admission-sha256")
    applying = commands.add_parser("apply")
    applying.add_argument("--resume", action="store_true",
                          help="Reuse frozen owned source checks and accepted artifact heads")
    verify = commands.add_parser("verify")
    verify.add_argument("--no-source-recheck", action="store_true")
    verify.add_argument("--current-inventory", type=Path,
                        help="Fresh full-root census; detects added and removed source paths")
    verify.add_argument("--scope-receipt", type=Path, action="append", default=[])
    composed = commands.add_parser("compose")
    composed.add_argument("--layer", type=Path, action="append", required=True)
    composed.add_argument("--current-inventory", type=Path, required=True)
    composed.add_argument("--scope-receipt", type=Path, action="append", default=[])
    composed.add_argument("--no-source-recheck", action="store_true")
    commands.add_parser("index")
    commands.add_parser("verify-index")
    commands.add_parser("finish")
    args = parser.parse_args(argv)
    os.umask(0o077)
    directory = local_reconcile.private_dir(args.receipt_dir)
    try:
        with (directory / "operation.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if args.command in {"prepare", "prepare-delta"}:
                terms, denylist_references = [], []
                for path in args.denylist:
                    reference = local_reconcile.input_reference(path)
                    terms.extend(line.strip() for line in path.read_text().splitlines()
                                 if line.strip() and not line.lstrip().startswith("#"))
                    local_reconcile.check_reference(reference)
                    denylist_references.append(reference)
                if args.command == "prepare":
                    result = local_reconcile.prepare(args.inventory, directory,
                        deny_terms=terms, maximum=args.bundle_bytes)
                else:
                    result = local_reconcile.prepare_delta(args.current_inventory, directory,
                        args.layer, deny_terms=terms, maximum=args.bundle_bytes,
                        scope_receipts=args.scope_receipt, admission_ledger=args.admission_ledger,
                        admission_sha256=args.admission_sha256,
                        denylist_sha256=denylist_references[0]["sha256"]
                            if len(denylist_references) == 1 else None)
                summary = {key: result[key] for key in ("schema", "source_count", "groups",
                    "counts", "bundle_count", "plan_sha256", "no_database_writes")}
            else:
                if not args.parent_run:
                    raise ValueError("An existing commissioned parent run is required")
                if args.command not in {"apply", "compose"} and not (
                        directory / "lease-state.json").exists():
                    raise ValueError("The source archive must exist before verification or indexing")
                load_environment(args.env_file)
                from research_library_service.service import Service
                session = local_reconcile.ArchiveSession(Service(), directory,
                    args.parent_run, args.owner)
                if args.command == "apply":
                    result = local_reconcile.apply(directory, session, resume=args.resume)
                elif args.command == "verify":
                    result = local_reconcile.verify(directory, session,
                        check_sources=not args.no_source_recheck,
                        current_inventory=args.current_inventory, scope_receipts=args.scope_receipt)
                elif args.command == "compose":
                    result = local_reconcile.compose(directory, session, args.layer,
                        args.current_inventory, scope_receipts=args.scope_receipt,
                        check_sources=not args.no_source_recheck)
                elif args.command == "finish":
                    result = session.finish()
                else:
                    result = local_reconcile.index(directory, session,
                        write=args.command == "index")
                summary = {key: result[key] for key in ("schema", "run_id", "source_counts",
                    "source_count", "storage_written_complete", "storage_verified",
                    "storage_complete", "reconciliation_complete", "fresh_inventory_compared",
                    "current_source_reconciliation_complete", "historical_retention_complete",
                    "historical_unretained_versions", "root_enumeration_evidence_bound",
                    "index_written_complete", "native_coverage_complete", "complete",
                    "counts", "reason") if key in result}
            print(json.dumps({**summary, "receipt_dir": str(directory)}, sort_keys=True))
            successful = result.get("reconciliation_complete", result.get("storage_written_complete",
                result.get("storage_complete", result.get("complete", True))))
            return 0 if successful else 3
    except Exception as exc:
        # Never echo arbitrary source text, credentials, or raw driver exceptions.
        print(json.dumps({"status": "failed", "error_type": type(exc).__name__,
                          "receipt_dir": str(directory)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
