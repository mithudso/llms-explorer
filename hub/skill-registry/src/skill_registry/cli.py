"""Local/offline registry and explicit trusted-worker commands."""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import threading
import time
from pathlib import Path

from .environment import load_environment
from .jobs import OPTIMIZERS
from .service import Service
from .worker import codex_command, run_one


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--state", type=Path)
    root.add_argument("--env-file", type=Path,
                      help="Explicit environment file; never searched or shell-evaluated")
    root.add_argument("--root", action="append", type=Path,
                      help="Trusted local skill root (repeatable; overrides configured roots)")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    commands.add_parser("refresh")
    lookup = commands.add_parser("lookup")
    lookup.add_argument("query")
    lookup.add_argument("--top", type=int, default=5)
    load = commands.add_parser("load")
    load.add_argument("skill_id")
    load.add_argument("--sha256", default="")
    package = commands.add_parser("package")
    package.add_argument("skill_id")
    for name in ("namespace", "name", "version"):
        package.add_argument("--" + name, required=True)
    publish = commands.add_parser("publish")
    publish.add_argument("sha256")
    remote_search = commands.add_parser("remote-search")
    remote_search.add_argument("query")
    fetch = commands.add_parser("fetch")
    fetch.add_argument("namespace")
    fetch.add_argument("name")
    fetch.add_argument("version")
    fetch.add_argument("--sha256", required=True)
    install = commands.add_parser("install")
    install.add_argument("sha256")
    install.add_argument("destination", type=Path)
    optimize = commands.add_parser("optimize")
    optimize.add_argument("kind", choices=OPTIMIZERS)
    inputs = optimize.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--skill-id")
    inputs.add_argument("--file", type=Path)
    inputs.add_argument("--text")
    optimize.add_argument("--sha256", default="")
    optimize.add_argument("--timeout", type=int, default=600)
    optimize.add_argument("--max-iter", type=int, default=3)
    policy = commands.add_parser("policy")
    policy.add_argument("skill_id")
    group = policy.add_mutually_exclusive_group(required=True)
    group.add_argument("--enable", action="store_true")
    group.add_argument("--disable", action="store_true")
    policy.add_argument("--interval", type=int, default=86400)
    policy.add_argument("--timeout", type=int, default=600)
    policy.add_argument("--max-iter", type=int, default=3)
    job = commands.add_parser("job")
    job.add_argument("id", nargs="?")
    cancel = commands.add_parser("cancel")
    cancel.add_argument("id")
    retry = commands.add_parser("retry")
    retry.add_argument("id")
    for name in ("work", "watch"):
        command = commands.add_parser(name)
        command.add_argument("--backend", choices=("configured", "codex"), default="configured")
        command.add_argument("--max-jobs", type=int, default=1)
        if name == "watch":
            command.add_argument("--interval", type=int, default=30)
            command.add_argument("--auto-optimize", action="store_true")
            command.add_argument("--once", action="store_true")
    remote_optimize = commands.add_parser("remote-optimize")
    remote_optimize.add_argument("kind", choices=OPTIMIZERS)
    remote_optimize.add_argument("--text", required=True)
    remote_optimize.add_argument("--timeout", type=int, default=600)
    remote_optimize.add_argument("--max-iter", type=int, default=3)
    remote_job = commands.add_parser("remote-job")
    remote_job.add_argument("id")
    remote_work = commands.add_parser("remote-work")
    remote_work.add_argument("id")
    remote_work.add_argument("--backend", choices=("configured", "codex"), default="configured")
    mongo = commands.add_parser("mongo", help="MongoDB skill distribution (MONGODB_URI2)")
    mongo_commands = mongo.add_subparsers(dest="mongo_command", required=True)
    setup = mongo_commands.add_parser("provision")
    setup.add_argument("--wait", type=int, default=0, help="Seconds to wait for search indexes")
    mongo_commands.add_parser("status")
    mongo_commands.add_parser("ingest")
    cache = mongo_commands.add_parser("cache-hook")
    cache.add_argument("--output", type=Path)
    cache.add_argument("--remote", action="store_true",
                       help="Fetch metadata over MCP using SKILL_MCP_URL and token only")
    search = mongo_commands.add_parser("search")
    search.add_argument("query")
    search.add_argument("--top", type=int, default=5)
    search.add_argument("--mode", choices=("hybrid", "semantic", "lexical"), default="hybrid")
    for name in ("load", "resource"):
        read = mongo_commands.add_parser(name)
        read.add_argument("skill_id")
        if name == "resource":
            read.add_argument("path")
        read.add_argument("--sha256", default="")
        read.add_argument("--offset", type=int, default=0)
        read.add_argument("--max-chars", type=int, default=16000)
    mongo_watch = mongo_commands.add_parser("watch")
    mongo_watch.add_argument("--interval", type=int, default=60)
    mongo_watch.add_argument("--once", action="store_true")
    mongo_watch.add_argument("--refresh-hook-cache", action="store_true",
                             help="Refresh metadata-only hook cache at startup and every 15 minutes")
    return root


def _print(value):
    print(json.dumps(value, indent=2, ensure_ascii=False))


def main():
    command_parser = parser()
    args = command_parser.parse_args()
    stop_event = threading.Event()
    received_signal = []
    previous_handlers = {}

    def stop(signum, _frame):
        if not received_signal:
            received_signal.append(signum)
        stop_event.set()

    if args.command in {"work", "watch", "remote-work"} or (
            args.command == "mongo" and args.mongo_command == "watch"):
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[signum] = signal.signal(signum, stop)
    try:
        load_environment(args.env_file)
        service = Service(args.state)
        if args.root:
            config = {**service.config, "roots": [
                {"path": str(p.expanduser().absolute()), "label": "CLI root", "writable": True}
                for p in args.root]}
            service = Service(args.state, config)
        catalog, jobs = service.catalog, service.jobs
        name = args.command
        if name == "mongo":
            action = args.mongo_command
            if action == "cache-hook" and args.remote:
                from .prompt_hook import HTTPStore
                store = HTTPStore(os.environ.get("SKILL_MCP_URL", ""),
                                  os.environ.get("SKILL_MCP_TOKEN", ""))
            else:
                store = service.mongo()
            if action == "cache-hook":
                from .hook_cache import refresh_cache
                value = refresh_cache(store, args.output)
            elif action == "provision":
                value = store.provision(wait_seconds=args.wait)
            elif action == "status":
                value = store.status()
            elif action == "ingest":
                value = store.ingest(catalog)
            elif action == "search":
                value = store.search(args.query, top=args.top, mode=args.mode)
            elif action == "load":
                value = store.load(args.skill_id, args.sha256, offset=args.offset,
                                   max_chars=args.max_chars)
            elif action == "resource":
                value = store.resource(args.skill_id, args.path, args.sha256, offset=args.offset,
                                       max_chars=args.max_chars)
            elif action == "watch":
                if not 5 <= args.interval <= 86400:
                    raise ValueError("watch interval must be 5..86400 seconds")
                next_cache_refresh = 0.0
                while not stop_event.is_set():
                    try:
                        value = store.ingest(catalog)
                        if args.refresh_hook_cache and time.monotonic() >= next_cache_refresh:
                            from .hook_cache import refresh_cache
                            value["hook_cache"] = refresh_cache(store)
                            next_cache_refresh = time.monotonic() + 900
                    except Exception as exc:
                        # Preserve the last published projection and retry; driver
                        # error strings can contain private connection details.
                        value = {"status": "retry_pending", "error_type": type(exc).__name__}
                    _print(value)
                    if args.once or stop_event.wait(args.interval):
                        break
            else:
                raise ValueError("Unsupported MongoDB command")
        elif name == "status":
            value = catalog.status()
        elif name == "refresh":
            value = catalog.refresh()
        elif name == "lookup":
            value = catalog.lookup(args.query, args.top)
        elif name == "load":
            value = catalog.load(args.skill_id, args.sha256)
        elif name == "package":
            value = service.package(args.skill_id, args.namespace, args.name, args.version)
        elif name == "publish":
            value = service.remote().publish(service.cached_bundle(args.sha256))
        elif name == "remote-search":
            value = service.remote().search(args.query)
        elif name == "fetch":
            value = service.remote().fetch(args.namespace, args.name, args.version, args.sha256)
        elif name == "install":
            value = service.install(args.sha256, args.destination)
        elif name == "optimize":
            if args.file:
                value = jobs.enqueue(args.kind, target=args.file, expected_sha256=args.sha256,
                                     max_iterations=args.max_iter, timeout_seconds=args.timeout,
                                     definition=service.definition(args.kind))
            else:
                value = service.submit(args.kind, skill_id=args.skill_id or "", input_text=args.text,
                                       expected_sha256=args.sha256, max_iterations=args.max_iter,
                                       timeout_seconds=args.timeout)
        elif name == "policy":
            catalog.load(args.skill_id)
            value = jobs.policy(args.skill_id, enabled=args.enable, interval_seconds=args.interval,
                                timeout_seconds=args.timeout, max_iterations=args.max_iter)
        elif name == "job":
            value = jobs.get(args.id) if args.id else jobs.list()
        elif name == "cancel":
            value = jobs.cancel(args.id)
        elif name == "retry":
            value = jobs.retry(args.id)
        elif name == "remote-optimize":
            value = service.remote().create_job(args.kind, input_text=args.text,
                timeout_seconds=args.timeout, max_iterations=args.max_iter)
        elif name == "remote-job":
            value = service.remote().job(args.id)
        elif name == "remote-work":
            from .remote_worker import run_remote
            command = codex_command() if args.backend == "codex" else service.config.get("worker_command")
            if not command:
                raise ValueError("Configure trusted worker_command argv or choose --backend codex")
            value = run_remote(service, args.id, command, stop_event=stop_event)
        elif name in ("work", "watch"):
            if not 1 <= args.max_jobs <= 10:
                raise ValueError("max-jobs must be 1..10")
            worker_command = codex_command() if args.backend == "codex" else service.config.get("worker_command")
            if name == "work":
                if not worker_command:
                    raise ValueError("Configure trusted worker_command argv or choose --backend codex")
                value = []
                for _ in range(args.max_jobs):
                    result = run_one(jobs, worker_command,
                                     check_commands=service.config.get("check_commands", []),
                                     stop_event=stop_event)
                    if result is None:
                        break
                    value.append(result)
            else:
                if not 5 <= args.interval <= 86400:
                    raise ValueError("watch interval must be 5..86400 seconds")
                while not stop_event.is_set():
                    value = {"refresh": catalog.refresh()}
                    if args.auto_optimize:
                        value["schedule"] = jobs.schedule(catalog, max_jobs=args.max_jobs)
                        value["executed"] = []
                        if worker_command:
                            for _ in range(args.max_jobs):
                                result = run_one(jobs, worker_command,
                                                 check_commands=service.config.get("check_commands", []),
                                                 stop_event=stop_event)
                                if result is None:
                                    break
                                value["executed"].append(result)
                        else:
                            value["execution"] = "Queued only: configure trusted worker_command or --backend codex"
                    _print(value)
                    if args.once or stop_event.wait(args.interval):
                        break
        else:
            raise ValueError("Unsupported command")
        if name != "watch" and not (name == "mongo" and args.mongo_command == "watch"):
            _print(value)
        if received_signal:
            raise SystemExit(128 + received_signal[0])
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except (OSError, ValueError, KeyError) as exc:
        print(f"skill-registry: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
    except Exception as exc:
        if args.command != "mongo":
            raise
        print(f"skill-registry: MongoDB operation failed ({type(exc).__name__})", file=sys.stderr)
        raise SystemExit(2) from None
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)


if __name__ == "__main__":
    main()
