#!/usr/bin/env python3
"""Install an already provisioned skill store as private user launchd services.

Run with the installed skill-registry Python. Cloudflare provisioning and database
ingestion are separate explicit operations. Existing client hooks are preserved.
"""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path


def save(path: Path, data: bytes, backup: Path) -> None:
    if path.exists() and path.read_bytes() == data:
        return
    if path.exists():
        backup.mkdir(parents=True, exist_ok=True, mode=0o700)
        shutil.copy2(path, backup / (path.name + "." + str(time.time_ns())))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".skill-registry-tmp")
    temporary.write_bytes(data)
    temporary.chmod(0o600)
    temporary.replace(path)


def install(args) -> dict:
    home = Path.home()
    state = home / ".local/share/skill-registry"
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    state.chmod(0o700)
    backup = state / "installation-backups"
    env_file = args.env_file.expanduser().resolve(strict=True)
    python = str(Path(sys.executable).absolute())
    environment = {"SKILL_REGISTRY_ENV_FILE": str(env_file)}
    jobs = {
        "com.llms-explorer.skills-mcp": [python, "-m", "skill_registry.mongo_mcp",
            "--transport", "streamable-http", "--host", "127.0.0.1", "--port", str(args.port)],
    }
    if not args.no_sync:
        jobs["com.llms-explorer.skills-sync"] = [python, "-m", "skill_registry.cli",
            "--env-file", str(env_file), "mongo", "watch", "--interval", "60",
            "--refresh-hook-cache"]
    if args.tunnel_token_file:
        token_file = args.tunnel_token_file.expanduser().resolve(strict=True)
        cloudflared = shutil.which("cloudflared")
        if not cloudflared:
            raise ValueError("Install cloudflared before installing its service")
        jobs["com.llms-explorer.skills-tunnel"] = [cloudflared, "--no-autoupdate", "tunnel",
            "run", "--token-file", str(token_file)]
    installed = []
    for label, command in jobs.items():
        path = home / "Library/LaunchAgents" / (label + ".plist")
        definition = {"Label": label, "ProgramArguments": command,
            "EnvironmentVariables": environment, "RunAtLoad": True, "KeepAlive": True,
            "ThrottleInterval": 15, "Umask": 0o077,
            "StandardOutPath": str(state / (label + ".out.log")),
            "StandardErrorPath": str(state / (label + ".err.log"))}
        save(path, plistlib.dumps(definition), backup)
        if args.start:
            domain = "gui/" + str(os.getuid())
            # Restart only these task-owned services; never touch other daemons.
            subprocess.run(["launchctl", "bootout", domain + "/" + label],
                capture_output=True, check=False)
            subprocess.run(["launchctl", "bootstrap", domain, str(path)], check=True)
        installed.append(label)
    if args.hooks:
        hook_env = (args.hook_env_file or env_file).expanduser().resolve(strict=True)
        hook = " ".join(shlex.quote(x) for x in [python, "-m", "skill_registry.prompt_hook",
            "--env-file", str(hook_env)])
        for path in [home / ".claude/settings.json", home / ".codex/hooks.json"]:
            config = json.loads(path.read_text()) if path.exists() else {}
            entries = config.setdefault("hooks", {}).setdefault("UserPromptSubmit", [])
            present = False
            for entry in entries:
                for item in entry.get("hooks", []):
                    if "skill_registry.prompt_hook" in item.get("command", ""):
                        item.update(command=hook, timeout=5)
                        present = True
            if not present:
                entries.append({"hooks": [{"type": "command", "command": hook, "timeout": 5}]})
            save(path, (json.dumps(config, indent=2) + "\n").encode(), backup)
    return {"services": installed, "started": args.start, "hooks": args.hooks,
        "backups": str(backup)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--hook-env-file", type=Path)
    parser.add_argument("--tunnel-token-file", type=Path)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--hooks", action="store_true")
    parser.add_argument("--no-sync", action="store_true")
    parser.add_argument("--start", action="store_true")
    args = parser.parse_args()
    if sys.platform != "darwin":
        parser.error("This installer requires macOS user launchd")
    print(json.dumps(install(args), indent=2))


if __name__ == "__main__":
    main()
