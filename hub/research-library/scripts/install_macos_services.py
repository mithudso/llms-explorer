#!/usr/bin/env python3
"""Install only the research MCP launchd job from a permanent installed runtime.

Database/index initialization, tunnel routing and client MCP registration are
separate owner operations. No secret value is copied into this plist.
"""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import shutil
import subprocess
import sys
import time
from pathlib import Path

LABEL = "com.llms-explorer.research-library-mcp"


def save(path: Path, data: bytes, backup: Path):
    if path.exists() and path.read_bytes() == data:
        path.chmod(0o600)
        return
    if path.exists():
        backup.mkdir(parents=True, exist_ok=True, mode=0o700)
        shutil.copy2(path, backup / (path.name + "." + str(time.time_ns())))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".research-library-tmp")
    temporary.write_bytes(data)
    temporary.chmod(0o600)
    temporary.replace(path)


def install(args, *, home=None, python=None):
    home = Path(home or Path.home())
    state = home / ".local/share/research-library"
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    state.chmod(0o700)
    backup = state / "installation-backups"
    env_file = args.env_file.expanduser().resolve(strict=True)
    if env_file.stat().st_mode & 0o077:
        raise ValueError("Restrict the server environment file to owner-only permissions")
    executable = str(Path(python or sys.executable).absolute())
    environment = {
        "RESEARCH_LIBRARY_ENV_FILE": str(env_file),
        "PYTHONUNBUFFERED": "1",
        "PATH": os.pathsep.join(dict.fromkeys([
            str(Path(executable).parent), str(home / ".local/bin"), "/opt/homebrew/bin",
            "/usr/local/bin", "/usr/bin", "/bin", "/usr/sbin", "/sbin",
        ])),
    }
    definition = {
        "Label": LABEL,
        "ProgramArguments": [executable, "-m", "research_library_service.mcp_server",
                             "--transport", "streamable-http", "--host", "127.0.0.1",
                             "--port", str(args.port)],
        "EnvironmentVariables": environment,
        "RunAtLoad": True, "KeepAlive": True, "ThrottleInterval": 15, "Umask": 0o077,
        "StandardOutPath": str(state / (LABEL + ".out.log")),
        "StandardErrorPath": str(state / (LABEL + ".err.log")),
    }
    path = home / "Library/LaunchAgents" / (LABEL + ".plist")
    save(path, plistlib.dumps(definition), backup)
    if args.start:
        domain = "gui/" + str(os.getuid())
        subprocess.run(["launchctl", "bootout", domain + "/" + LABEL],
                       capture_output=True, check=False)
        subprocess.run(["launchctl", "bootstrap", domain, str(path)], check=True)
    return {"service": LABEL, "started": args.start, "plist": str(path),
            "backups": str(backup), "secrets_in_plist": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--start", action="store_true")
    args = parser.parse_args()
    if sys.platform != "darwin":
        parser.error("This installer requires macOS user launchd")
    if not 1 <= args.port <= 65535:
        parser.error("Port must be 1..65535")
    print(json.dumps(install(args), indent=2))


if __name__ == "__main__":
    main()
