"""Coordinate maintained research adapters with an explicitly enabled Mongo library.

This bridge never removes STOP markers or resumes a run. The caller's requested
init/research/gate/finish operation remains responsible for that decision.
"""
from __future__ import annotations

import json
import os
import subprocess
import threading
from contextlib import contextmanager
from pathlib import Path


def config() -> dict | None:
    path = Path(os.environ.get(
        "RESEARCH_LIBRARY_COORDINATION_CONFIG",
        "~/.config/research-library/coordination.json")).expanduser()
    if not path.exists():
        return None
    if path.stat().st_size > 65536:
        raise ValueError("research library coordination configuration is oversized")
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError("invalid research library coordination configuration")  # noqa: TRY004
    if value.get("enabled") is not True:
        return None
    for key in ("python", "env_file"):
        item = value.get(key)
        if not isinstance(item, str) or not Path(item).is_absolute():
            raise ValueError("coordination requires absolute Python and environment paths")
    return value


def request(settings: dict, operation: str, arguments: dict) -> dict:
    command = [settings["python"], "-m", "research_library_service.cli",
               "--env-file", settings["env_file"], "request"]
    payload = json.dumps({"operation": operation, "arguments": arguments})
    if len(payload.encode()) > 1024 * 1024:
        raise ValueError("research library coordination request is oversized")
    try:
        result = subprocess.run(command, input=payload, text=True,
            capture_output=True, timeout=45, check=False)
    except (OSError, subprocess.SubprocessError):
        raise ValueError("research library coordination transport is unavailable") from None
    if result.returncode or len(result.stdout) > 4 * 1024 * 1024:
        # Child diagnostics may include private concept/source text.
        raise ValueError("research library coordination unavailable or ownership denied")
    try:
        value = json.loads(result.stdout)
    except ValueError:
        raise ValueError("research library coordination returned an invalid receipt") from None
    if not isinstance(value, dict) or value.get("ok") is False or value.get("error"):
        raise ValueError("research library coordination denied the operation")
    return value


def _state(shared, slug: str) -> Path:
    shared.check_slug(slug)
    return Path(shared.RESEARCH_DIR) / ".library-coordination" / (slug + ".json")


def _load(shared, slug: str) -> dict | None:
    path = _state(shared, slug)
    return json.loads(path.read_text()) if path.is_file() else None


def _save(shared, slug: str, value: dict) -> None:
    path = _state(shared, slug)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_suffix(".tmp." + str(os.getpid()))
    try:
        temporary.write_text(json.dumps(value) + "\n")
        temporary.chmod(0o600)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _names(shared, args, slug: str, *, initializing=False) -> list[str]:
    names = []
    if initializing:
        names.append(args.topic)
        names.extend(x.strip() for x in (getattr(args, "concepts", None) or "").split(",")
                     if x.strip())
    path = shared.run_dir(slug) / "manifest.json"
    if path.is_file():
        manifest = shared.load_manifest(slug)
        names.append(manifest["topic"])
        names.extend(c["name"] for c in manifest.get("concepts", [])
                     if c.get("status") not in ("done", "complete"))
    return list(dict.fromkeys(n for n in names if isinstance(n, str) and n.strip()))


def _acquire(shared, args, settings, slug: str, initializing=False):
    previous = _load(shared, slug)
    value = request(settings, "coordinate", {
        "action": "acquire", "run_id": slug,
        "names": _names(shared, args, slug, initializing=initializing),
        "bundle": previous, "ttl_seconds": 900,
    })
    _save(shared, slug, value)
    return value


def _release(shared, settings, slug: str, bundle: dict):
    request(settings, "coordinate", {
        "action": "release", "run_id": slug, "bundle": bundle})
    _state(shared, slug).unlink(missing_ok=True)


@contextmanager
def _heartbeat(settings, slug, bundle):
    stopped, errors = threading.Event(), []

    def beat():
        while not stopped.wait(60):
            try:
                request(settings, "coordinate", {
                    "action": "renew", "run_id": slug, "bundle": bundle,
                    "ttl_seconds": 900})
            except (OSError, ValueError, subprocess.SubprocessError):
                errors.append(True)
                return

    thread = threading.Thread(target=beat, daemon=True, name="research-library-heartbeat")
    thread.start()
    def checkpoint():
        if errors:
            raise ValueError("research library lease heartbeat failed; completion is withheld")
        request(settings, "coordinate", {
            "action": "renew", "run_id": slug, "bundle": bundle,
            "ttl_seconds": 900})
    try:
        yield checkpoint
        checkpoint()
    finally:
        stopped.set()
        thread.join(timeout=46)


def install(shared) -> None:
    """Guard new/resumed init and every maintained work/finalization entrypoint."""
    if getattr(shared, "_research_library_coordination_installed", False):
        return
    shared._research_library_coordination_installed = True
    original_init = getattr(shared, "cmd_init", None)
    if callable(original_init):
        def guarded_init(args):
            settings = config()
            if not settings or getattr(args, "dry_run", False):
                return original_init(args)
            slug = shared.check_slug(args.slug) if args.slug else shared.slugify(args.topic)
            previous = _load(shared, slug)
            bundle = _acquire(shared, args, settings, slug, initializing=True)
            try:
                return original_init(args)
            except BaseException:
                # Keep a resumed run's prior reservation. Release a fresh init
                # only when no manifest was created by the attempted operation.
                if previous is None and not (shared.run_dir(slug) / "manifest.json").exists():
                    _release(shared, settings, slug, bundle)
                raise
        shared.cmd_init = guarded_init

    for symbol in ("cmd_research", "cmd_gate", "cmd_finish"):
        original = getattr(shared, symbol, None)
        if not callable(original):
            continue

        def wrap(function, operation):
            def guarded(args):
                settings = config()
                if not settings or getattr(args, "dry_run", False):
                    return function(args)
                # Failure/blocked bookkeeping does not start research or publish.
                if operation == "cmd_finish" and args.status not in (
                        "COMPLETED", "BUDGET_EXHAUSTED"):
                    return function(args)
                slug = shared.check_slug(args.slug)
                bundle = _acquire(shared, args, settings, slug)
                with _heartbeat(settings, slug, bundle) as checkpoint:
                    previous = getattr(shared, "_research_library_lease_checkpoint", None)
                    shared._research_library_lease_checkpoint = checkpoint
                    try:
                        checkpoint()
                        result = function(args)
                    finally:
                        shared._research_library_lease_checkpoint = previous
                if operation == "cmd_finish" and args.status == "COMPLETED" and result == 0:
                    _release(shared, settings, slug, bundle)
                return result
            return guarded
        setattr(shared, symbol, wrap(original, symbol))
