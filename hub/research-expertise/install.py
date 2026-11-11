#!/usr/bin/env python3
"""Install a stable user-local application with recoverable upgrades."""

from __future__ import annotations

import argparse
import fcntl
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile
import tomllib
from uuid import uuid4


ENTRIES = ("research-expertise", "research-expertise-mcp")


def _check_link(link, destination):
    if link.is_symlink():
        if link.resolve() != destination.resolve():
            raise FileExistsError(f"Refusing to replace another executable link: {link}")
    elif link.exists():
        raise FileExistsError(f"Refusing to replace existing executable: {link}")


def _install(source, home, *, schedule):
    state = home / ".local/share/research-expertise"
    target = state / "app"
    binary = home / ".local/bin"
    if target.is_symlink() or (target.exists() and not target.is_dir()):
        raise FileExistsError(f"Refusing to replace an unowned application path: {target}")
    if target.exists() and any(target.iterdir()):
        try:
            owned = tomllib.loads((target / "pyproject.toml").read_text())["project"]["name"]
        except (OSError, ValueError, KeyError, TypeError):
            owned = None
        if owned != "research-expertise":
            raise FileExistsError(
                f"Existing application has no expertise ownership marker: {target}"
            )
    if schedule and shutil.which("launchctl") is None:
        raise FileNotFoundError("--schedule requires macOS launchctl; omit it on other hosts")
    if shutil.which("uv") is None:
        raise FileNotFoundError("uv is required; install it from https://docs.astral.sh/uv/")
    links = {binary / name: target / ".venv/bin" / name for name in ENTRIES}
    for link, destination in links.items():
        _check_link(link, destination)
    old_links = {link: os.readlink(link) if link.is_symlink() else None for link in links}
    label = "com.global-ai-hub.research-expertise"
    plist = home / "Library/LaunchAgents" / f"{label}.plist"
    if schedule and plist.is_symlink():
        raise FileExistsError(f"Refusing to overwrite a symlinked launch agent: {plist}")
    old_plist = plist.read_bytes() if schedule and plist.exists() else None
    if old_plist is not None and plistlib.loads(old_plist).get("Label") != label:
        raise FileExistsError(f"Refusing to replace another launch agent: {plist}")
    history = state / "install-history" / uuid4().hex
    previous = history / "previous-app"
    stage = Path(tempfile.mkdtemp(prefix=".app-stage-", dir=state))
    activated, changed_links, schedule_changed = False, [], False
    try:
        for name in ("pyproject.toml", "uv.lock", "README.md", "MCP.md"):
            shutil.copy2(source / name, stage / name)
        shutil.copytree(source / "src", stage / "src", ignore=shutil.ignore_patterns("__pycache__"))
        history.mkdir(parents=True, mode=0o700)
        if target.exists():
            target.rename(previous)
        stage.rename(target)
        activated = True
        # Build at the final path: uv entrypoint shebangs and editable metadata
        # must not point at a staging directory that will disappear.
        subprocess.run(
            ["uv", "sync", "--directory", str(target), "--python", "3.14", "--frozen", "--no-dev"],
            check=True,
        )
        binary.mkdir(parents=True, exist_ok=True)
        for link, destination in links.items():
            _check_link(link, destination)
            pending = binary / ("." + link.name + "." + uuid4().hex)
            try:
                pending.symlink_to(destination)
                pending.replace(link)
                changed_links.append(link)
            finally:
                pending.unlink(missing_ok=True)
        if schedule:
            plist.parent.mkdir(parents=True, exist_ok=True)
            if old_plist is not None:
                (history / "previous-launch-agent.plist").write_bytes(old_plist)
                subprocess.run(
                    ["launchctl", "bootout", f"gui/{os.getuid()}", str(plist)],
                    check=False,
                    capture_output=True,
                )
            content = {
                "Label": label,
                "ProgramArguments": [str(target / ".venv/bin/research-expertise"), "ingest"],
                "StartInterval": 3600,
                "RunAtLoad": False,
                "LowPriorityIO": True,
                "ProcessType": "Background",
                "StandardOutPath": str(state / "refresh.log"),
                "StandardErrorPath": str(state / "refresh-error.log"),
            }
            schedule_changed = True
            plist.write_bytes(plistlib.dumps(content))
            subprocess.run(["launchctl", "bootstrap", f"gui/{os.getuid()}", str(plist)], check=True)
    except BaseException:
        # Keep both versions for inspection; restoring the prior app also
        # restores its complete venv at the absolute path its scripts expect.
        if activated:
            target.rename(history / "failed-app")
        if previous.exists():
            previous.rename(target)
        for link in reversed(changed_links):
            _check_link(link, links[link])
            link.unlink(missing_ok=True)
            if old_links[link] is not None:
                link.symlink_to(old_links[link])
        if schedule_changed:
            subprocess.run(
                ["launchctl", "bootout", f"gui/{os.getuid()}", str(plist)],
                check=False,
                capture_output=True,
            )
            if old_plist is None:
                plist.unlink(missing_ok=True)
            else:
                plist.write_bytes(old_plist)
                restored = subprocess.run(
                    ["launchctl", "bootstrap", f"gui/{os.getuid()}", str(plist)],
                    check=False,
                    capture_output=True,
                )
                if restored.returncode:
                    print(
                        f"Prior app restored; launch agent reload failed. Inspect {plist}",
                        file=sys.stderr,
                    )
        raise
    finally:
        if stage.exists():
            history.mkdir(parents=True, exist_ok=True, mode=0o700)
            stage.rename(history / "unpublished-stage")
    if previous.exists():
        print(f"Previous installation retained at {previous}", file=sys.stderr)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schedule", action="store_true", help="Refresh only this corpus hourly")
    args = parser.parse_args()
    home = Path.home()
    state = home / ".local/share/research-expertise"
    state.mkdir(parents=True, exist_ok=True)
    with (state / "ingest.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.exit(
                3,
                f"Expertise ingestion or installation owns {state / 'ingest.lock'}; "
                "retry after it finishes.\n",
            )
        target = _install(Path(__file__).resolve().parent, home, schedule=args.schedule)
    print(target)


if __name__ == "__main__":
    main()
