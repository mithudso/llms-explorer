#!/usr/bin/env python3
"""Preview or install SK through native plugin CLIs and a collision-safe router."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Keep an extracted, exact-inventory kit unchanged when loading its contract.
sys.dont_write_bytecode = True
from package_contract import FORMAT, MARKETPLACE, PACKAGE_FILES, ROUTER, ROUTER_FILES  # noqa: E402


def reject_symlinks(path: Path) -> None:
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ValueError("Symlinks are not allowed in package or installation paths")


def verify_bundle(bundle: Path) -> dict:
    """Verify a fixed inventory; the manifest never supplies copy instructions."""
    reject_symlinks(bundle)
    expected = PACKAGE_FILES | {"manifest.json"}
    actual = set()
    for path in bundle.rglob("*"):
        reject_symlinks(path)
        if path.is_file():
            actual.add(path.relative_to(bundle).as_posix())
        elif not path.is_dir():
            raise ValueError("Package contains a nonregular file")
    if actual != expected:
        raise ValueError("Package does not match the exact public file allowlist")
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format") != FORMAT:
        raise ValueError("Unsupported package manifest")
    entries = manifest.get("files")
    if not isinstance(entries, list) or any(not isinstance(row, dict) for row in entries):
        raise ValueError("Invalid package manifest entries")
    paths = [row.get("path") for row in entries]
    if any(not isinstance(path, str) for path in paths):
        raise ValueError("Invalid package path")
    if len(paths) != len(set(paths)) or set(paths) != PACKAGE_FILES:
        raise ValueError("Manifest does not match the exact public file allowlist")
    for row in entries:
        path = bundle / row["path"]
        if path.stat().st_size > 512 * 1024:
            raise ValueError("Package file exceeds the size limit")
        content = path.read_bytes()
        if (len(content) != row.get("bytes")
                or hashlib.sha256(content).hexdigest() != row.get("sha256")):
            raise ValueError(f"Package integrity mismatch: {row['path']}")
    return manifest


def install_router(bundle: Path, skills_dir: Path, *, preview: bool = True) -> dict:
    """Copy only sk, reserving its name before moving staged content into place."""
    verify_bundle(bundle)
    reject_symlinks(skills_dir)
    destination = skills_dir / "sk"
    if os.path.lexists(destination):
        raise ValueError("Existing sk skill; nothing overwritten")
    result = {"destination": str(destination), "preview": preview}
    if preview:
        return result
    target_existed = skills_dir.exists()
    created = False
    staging = None
    try:
        skills_dir.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".sk-install-", dir=skills_dir))
        for name in ROUTER_FILES:
            target = staging / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(bundle / str(ROUTER) / name, target)
        destination.mkdir()
        created = True
        for child in staging.iterdir():
            os.replace(child, destination / child.name)
    except BaseException:
        if created:
            shutil.rmtree(destination)
        raise
    finally:
        if staging is not None:
            shutil.rmtree(staging)
        if not target_existed and skills_dir.exists() and not any(skills_dir.iterdir()):
            skills_dir.rmdir()
    return result


def commands(bundle: Path, client: str) -> list[list[str]]:
    result = []
    if client in ("codex", "both"):
        result.extend([
            ["codex", "plugin", "marketplace", "add", str(bundle), "--json"],
            ["codex", "plugin", "add", f"sk@{MARKETPLACE}", "--json"],
        ])
    if client in ("claude", "both"):
        result.extend([
            ["claude", "plugin", "marketplace", "add", str(bundle), "--scope", "user"],
            ["claude", "plugin", "install", f"sk@{MARKETPLACE}", "--scope", "user"],
        ])
    return result


def _contains_sk(value) -> bool:
    """Treat any installed sk identity as a collision, regardless of its source."""
    if isinstance(value, str):
        return value == "sk" or value.startswith("sk@")
    if isinstance(value, dict):
        return any(_contains_sk(item) for item in (*value.keys(), *value.values()))
    if isinstance(value, list):
        return any(_contains_sk(item) for item in value)
    return False


def install(bundle: Path, *, client: str, skills_dir: Path, codex_home: Path | None = None,
            apply: bool = False, router_only: bool = False, plugin_only: bool = False,
            runner=subprocess.run) -> dict:
    verify_bundle(bundle)
    if client not in {"codex", "claude", "both"} or (router_only and plugin_only):
        raise ValueError("Invalid client or installation selection")
    router = client in {"codex", "both"} and not plugin_only
    if router_only and not router:
        raise ValueError("The fallback router requires the Codex client")
    if codex_home is not None:
        reject_symlinks(codex_home)
    if router:
        install_router(bundle, skills_dir, preview=True)
    planned = [] if router_only else commands(bundle, client)
    result = {"preview": not apply, "client": client, "plugin_commands": planned,
              "router_destination": str(skills_dir / "sk") if router else None,
              "codex_home": str(codex_home) if codex_home else None,
              "configuration_method": "native-plugin-cli" if planned else "none",
              "mcp_configuration_changed": False, "research_started": False}
    if not apply:
        return result
    environ = dict(os.environ)
    if codex_home is not None:
        environ["CODEX_HOME"] = str(codex_home)
    # Complete every read-only preflight before the first install command.
    clients = list(dict.fromkeys(command[0] for command in planned))
    for name in clients:
        if shutil.which(name) is None:
            raise ValueError(f"Required native CLI is unavailable: {name}")
        try:
            response = runner([name, "plugin", "list", "--json"], env=environ,
                              capture_output=True, text=True, check=True, timeout=60)
            installed = json.loads(response.stdout)
        except (subprocess.SubprocessError, OSError, ValueError):
            raise ValueError(f"Cannot verify installed {name} plugins; nothing installed") from None
        if _contains_sk(installed):
            raise ValueError(f"Existing sk plugin in {name}; nothing overwritten")
    completed = []
    for command in planned:
        try:
            runner(command, env=environ, capture_output=True, text=True, check=True, timeout=60)
        except (subprocess.SubprocessError, OSError):
            raise ValueError(
                f"Native {command[0]} installation stopped after {len(completed)} commands. "
                "Inspect the native plugin list before retrying; no existing skill was replaced."
            ) from None
        completed.append(command)
    if router:
        install_router(bundle, skills_dir, preview=False)
    result["completed_plugin_commands"] = completed
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", choices=("codex", "claude", "both"), default="codex")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--apply", action="store_true", help="Perform the displayed installation")
    action.add_argument("--preview", "--dry-run", action="store_true", help="Preview only (default)")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--router-only", action="store_true", help="Install only the $sk fallback")
    selection.add_argument("--plugin-only", action="store_true", help="Install only native plugins")
    parser.add_argument("--skills-dir", type=Path, default=Path.home() / ".agents/skills")
    parser.add_argument("--codex-home", type=Path,
                        help="Select this local Codex home through CODEX_HOME for native commands")
    args = parser.parse_args(argv)
    try:
        result = install(Path(__file__).absolute().parent, client=args.client,
                         skills_dir=args.skills_dir.expanduser().absolute(),
                         codex_home=args.codex_home.expanduser().absolute()
                         if args.codex_home else None,
                         apply=args.apply, router_only=args.router_only,
                         plugin_only=args.plugin_only)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"Installation stopped: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
