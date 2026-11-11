#!/usr/bin/env python3
"""Install the checked-in expertise application into a stable user-local directory."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import plistlib
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schedule", action="store_true", help="Refresh only this corpus hourly")
    args = parser.parse_args()
    source = Path(__file__).resolve().parent
    home = Path.home()
    target = home / ".local/share/research-expertise/app"
    target.mkdir(parents=True, exist_ok=True)
    for name in ("pyproject.toml", "uv.lock", "README.md", "MCP.md"):
        shutil.copy2(source / name, target / name)
    shutil.copytree(
        source / "src",
        target / "src",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    subprocess.run(["uv", "sync", "--directory", str(target), "--frozen", "--no-dev"], check=True)
    binary = home / ".local/bin"
    binary.mkdir(parents=True, exist_ok=True)
    for name in ("research-expertise", "research-expertise-mcp"):
        link = binary / name
        dest = target / ".venv/bin" / name
        if link.exists() and not link.is_symlink():
            raise FileExistsError(f"Refusing to replace existing executable: {link}")
        link.unlink(missing_ok=True)
        link.symlink_to(dest)
    if args.schedule:
        state = target.parent
        label = "com.global-ai-hub.research-expertise"
        plist = home / "Library/LaunchAgents" / f"{label}.plist"
        plist.parent.mkdir(parents=True, exist_ok=True)
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
        if plist.exists():
            shutil.copy2(plist, plist.with_suffix(".plist.backup"))
            subprocess.run(
                ["launchctl", "bootout", f"gui/{os.getuid()}", str(plist)],
                check=False,
                capture_output=True,
            )
        plist.write_bytes(plistlib.dumps(content))
        subprocess.run(["launchctl", "bootstrap", f"gui/{os.getuid()}", str(plist)], check=True)
    print(target)


if __name__ == "__main__":
    main()
