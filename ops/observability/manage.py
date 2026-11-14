#!/usr/bin/env python3
"""Install committed monitoring releases and owned user LaunchAgents on macOS."""

import argparse
import base64
import io
import json
import os
import plistlib
import secrets
import subprocess
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = Path.home() / ".local/share/llmsx-observability"
ACCOUNT = "b41ba4dc457dce7653c93af955ecc462"


def run(*args, **kwargs):
    return subprocess.run(list(args), check=kwargs.pop("check", True), **kwargs)


def cf(*args):
    result = run(
        os.environ.get("CF_CLI", "/opt/homebrew/bin/cf"),
        *args,
        capture_output=True,
        text=True,
        timeout=60,
    )
    raw = result.stdout
    if raw.startswith("result_info:"):
        raw = raw.split("\n", 1)[1]
    return json.loads(raw)


def private_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")
    path.chmod(0o600)


def ensure_tunnel():
    """Create only this stack's tunnel and new hostname; preserve existing tunnels."""
    owned = [
        t
        for t in cf("tunnels", "list")
        if t["name"] == "llmsx-observability" and not t.get("deleted_at")
    ]
    credential = RUNTIME / "tunnel-credentials.json"
    if not owned:
        secret = base64.b64encode(secrets.token_bytes(32)).decode()
        body = RUNTIME / "tunnel-request.json"
        private_json(
            body,
            {
                "name": "llmsx-observability",
                "config_src": "local",
                "tunnel_secret": secret,
            },
        )
        try:
            tunnel = cf("tunnels", "create", "--body", "@" + str(body))
        finally:
            body.unlink(missing_ok=True)
        private_json(
            credential,
            {"AccountTag": ACCOUNT, "TunnelID": tunnel["id"], "TunnelSecret": secret},
        )
    elif len(owned) == 1 and credential.is_file():
        tunnel = owned[0]
        if json.loads(credential.read_text())["TunnelID"] != tunnel["id"]:
            raise ValueError("owned tunnel and credentials disagree")
    else:
        raise ValueError(
            "tunnel exists without local credentials or has duplicate names"
        )
    hostname = "ops.llmsx.org"
    records = cf("dns", "records", "list", "--zone", "llmsx.org", "--name", hostname)
    target = tunnel["id"] + ".cfargotunnel.com"
    if not records:
        body = RUNTIME / "dns-request.json"
        private_json(
            body,
            {
                "type": "CNAME",
                "name": hostname,
                "content": target,
                "proxied": True,
                "ttl": 1,
                "comment": "LLMSX fleet operations dashboard",
            },
        )
        try:
            cf(
                "dns",
                "records",
                "create",
                "--zone",
                "llmsx.org",
                "--body",
                "@" + str(body),
            )
        finally:
            body.unlink(missing_ok=True)
    elif len(records) != 1 or records[0]["content"] != target:
        raise ValueError("dashboard DNS hostname is already owned by another target")
    config = RUNTIME / "tunnel.json"
    private_json(
        config,
        {
            "tunnel": tunnel["id"],
            "credentials-file": str(credential),
            "ingress": [
                {"hostname": hostname, "service": "http://127.0.0.1:13031"},
                {"service": "http_status:404"},
            ],
        },
    )
    return config, tunnel["id"]


def launch(label, arguments, environment=None):
    directory = Path.home() / "Library/LaunchAgents"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (label + ".plist")
    body = {
        "Label": label,
        "ProgramArguments": arguments,
        "RunAtLoad": True,
        "KeepAlive": True,
        "ThrottleInterval": 15,
        "WorkingDirectory": str(RUNTIME),
        "StandardOutPath": str(RUNTIME / (label + ".stdout.log")),
        "StandardErrorPath": str(RUNTIME / (label + ".stderr.log")),
        "EnvironmentVariables": {
            "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin",
            **(environment or {}),
        },
    }
    path.write_bytes(plistlib.dumps(body))
    path.chmod(0o600)
    domain = f"gui/{os.getuid()}"
    # Reconfigure only this stack's owned agents; absent jobs are normal.
    run(
        "/bin/launchctl",
        "bootout",
        domain + "/" + label,
        check=False,
        capture_output=True,
    )
    run("/bin/launchctl", "bootstrap", domain, str(path))


def release(revision):
    if run(
        "git",
        "-C",
        str(ROOT),
        "status",
        "--porcelain",
        "--",
        "ops/observability",
        capture_output=True,
        text=True,
    ).stdout:
        raise ValueError("commit the reviewed observability files before installing")
    sha = run(
        "git", "-C", str(ROOT), "rev-parse", revision, capture_output=True, text=True
    ).stdout.strip()
    destination = RUNTIME / "releases" / sha
    if not destination.exists():
        raw = run(
            "git",
            "-C",
            str(ROOT),
            "archive",
            sha,
            "ops/observability",
            capture_output=True,
        ).stdout
        destination.mkdir(parents=True)
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            archive.extractall(destination, filter="data")
    return destination / "ops/observability", sha


def compose(source, *args):
    return run(
        "/usr/local/bin/docker",
        "compose",
        "--env-file",
        str(RUNTIME / "runtime.env"),
        "-f",
        str(source / "compose.yaml"),
        *args,
    )


def supervise(source):
    while True:
        try:
            compose(source, "up", "-d", "--remove-orphans")
        except subprocess.SubprocessError:
            pass
        time.sleep(60)


def install(revision, publish):
    os.umask(0o077)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    source, sha = release(revision)
    password = RUNTIME / "grafana-password"
    if not password.exists():
        password.write_text(secrets.token_urlsafe(32))
        password.chmod(0o600)
    (RUNTIME / "runtime.env").write_text(
        f"GRAFANA_PASSWORD_FILE={password}\nDASHBOARD_URL=https://ops.llmsx.org\nOBSERVABILITY_REVISION={sha}\n"
    )
    venv = RUNTIME / "venv"
    if not (venv / "bin/python").exists():
        run(sys.executable, "-m", "venv", str(venv))
    python = str(venv / "bin/python")
    run(
        python,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "-r",
        str(source / "requirements.txt"),
    )
    compose(source, "config", "--quiet")
    compose(source, "build")
    run(
        "/usr/local/bin/docker",
        "volume",
        "create",
        "llmsx-observability-credentials",
        capture_output=True,
    )
    init = run(
        "/usr/local/bin/docker",
        "create",
        "--user",
        "0",
        "--mount",
        "type=volume,source=llmsx-observability-credentials,target=/secrets",
        "--entrypoint",
        "/bin/sh",
        "prom/prometheus:v3.16.0",
        "-c",
        "chmod 0444 /secrets/grafana-password",
        capture_output=True,
        text=True,
    ).stdout.strip()
    try:
        run(
            "/usr/local/bin/docker",
            "cp",
            str(password),
            init + ":/secrets/grafana-password",
        )
        run("/usr/local/bin/docker", "start", "--attach", init)
        state = run(
            "/usr/local/bin/docker",
            "inspect",
            init,
            "--format",
            "{{.State.ExitCode}}",
            capture_output=True,
            text=True,
        ).stdout.strip()
        if state != "0":
            raise RuntimeError("credential volume initialization failed")
    finally:
        run("/usr/local/bin/docker", "rm", init, capture_output=True)
    compose(source, "up", "-d")
    launch(
        "com.llmsx.observability.collector",
        [python, str(source / "collector.py"), "--state", str(RUNTIME / "state")],
    )
    launch(
        "com.llmsx.observability.stack",
        [python, str(source / "manage.py"), "supervise", "--source", str(source)],
    )
    tunnel = None
    if publish:
        config, tunnel = ensure_tunnel()
        launch(
            "com.llmsx.observability.tunnel",
            [
                "/opt/homebrew/bin/cloudflared",
                "tunnel",
                "--config",
                str(config),
                "run",
                tunnel,
            ],
        )
    for _ in range(45):
        try:
            with urllib.request.urlopen(
                "http://127.0.0.1:9321/ready", timeout=2
            ) as response:
                if response.status == 200:
                    break
        except OSError:
            time.sleep(2)
    else:
        raise RuntimeError("collector never became ready; inspect private runtime logs")
    private_json(
        RUNTIME / "deployment.json",
        {
            "source_revision": sha,
            "source": str(source),
            "installed_at": time.time(),
            "dashboard_url": "https://ops.llmsx.org",
            "tunnel_id": tunnel,
        },
    )
    print(
        json.dumps(
            {
                "revision": sha,
                "dashboard": "https://ops.llmsx.org",
                "state": str(RUNTIME),
            }
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["install", "supervise"])
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Create owned tunnel/DNS and publish authenticated Grafana",
    )
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    if args.action == "supervise":
        if args.source is None:
            parser.error("supervise requires --source")
        supervise(args.source)
    else:
        install(args.revision, args.publish)


if __name__ == "__main__":
    main()
