#!/usr/bin/env python3
"""Deploy only the owned off-host monitoring Worker and its D1 history."""

import json
import os
import secrets
from pathlib import Path

from manage import ROOT, RUNTIME, cf, private_json, run


def deploy():
    os.umask(0o077)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).resolve().parent / "watchdog"
    dirty = run(
        "git",
        "-C",
        str(ROOT),
        "status",
        "--porcelain",
        "--",
        "ops/observability",
        capture_output=True,
        text=True,
    ).stdout
    if dirty:
        raise ValueError("commit observability source before deploying")
    sha = run(
        "git", "-C", str(ROOT), "rev-parse", "HEAD", capture_output=True, text=True
    ).stdout.strip()
    cf("zones", "list")
    account = json.loads(
        (Path.home() / "Library/Preferences/cloudflare/config/default.json").read_text()
    )
    env = {
        **os.environ,
        "CLOUDFLARE_API_TOKEN": account["oauth_token"],
        "CLOUDFLARE_ACCOUNT_ID": "b41ba4dc457dce7653c93af955ecc462",
        "WRANGLER_SEND_METRICS": "false",
    }
    name = "llmsx-fleet-watchdog"
    databases = [d for d in cf("d1", "list") if d["name"] == name]
    if not databases:
        body = RUNTIME / "watchdog-database-request.json"
        private_json(body, {"name": name})
        try:
            database = cf("d1", "create", "--body", "@" + str(body))
        finally:
            body.unlink(missing_ok=True)
    elif len(databases) == 1:
        database = databases[0]
    else:
        raise ValueError("duplicate watchdog databases")
    database_id = database.get("uuid") or database.get("id")
    cf("d1", "query", database_id, "--sql", (source / "schema.sql").read_text())
    token_path = RUNTIME / "watchdog-token"
    if not token_path.exists():
        token_path.write_text(secrets.token_urlsafe(32))
        token_path.chmod(0o600)
    config = json.loads((source / "wrangler.jsonc").read_text())
    config["main"] = str(source / "worker.mjs")
    config["d1_databases"][0]["database_id"] = database_id
    config["vars"] = {"RELEASE_SHA": sha}
    private_config = RUNTIME / "watchdog-wrangler.json"
    private_json(private_config, config)
    candidates = list(
        (Path.home() / ".npm/_npx").glob("*/node_modules/wrangler/bin/wrangler.js")
    )
    selected = None
    for path in candidates:
        package = json.loads((path.parent.parent / "package.json").read_text())
        if package["version"] == "4.127.1":
            selected = path
            break
    command = (
        ["node", str(selected)] if selected else ["npx", "--yes", "wrangler@4.127.1"]
    )
    run(*command, "deploy", "--config", str(private_config), env=env)
    run(
        *command,
        "secret",
        "put",
        "WATCHDOG_TOKEN",
        "--config",
        str(private_config),
        input=token_path.read_text(),
        text=True,
        env=env,
    )
    workers = cf("workers", "scripts", "search", "--name", name)
    worker = next(w for w in workers if w["script_name"] == name)
    app_name = "LLMSX fleet watchdog bearer API"
    apps = cf("zero-trust", "access", "applications", "list")
    if not any(a["name"] == app_name for a in apps):
        body = RUNTIME / "watchdog-access-request.json"
        private_json(
            body,
            {
                "name": app_name,
                "type": "self_hosted",
                "app_launcher_visible": False,
                "destinations": [{"type": "worker", "worker_id": worker["id"]}],
                "policies": [
                    {
                        "name": "Owned monitoring endpoints enforce bearer authentication",
                        "decision": "bypass",
                        "include": [{"everyone": {}}],
                        "precedence": 1,
                    }
                ],
            },
        )
        try:
            cf(
                "zero-trust",
                "access",
                "applications",
                "create",
                "--body",
                "@" + str(body),
            )
        finally:
            body.unlink(missing_ok=True)
    private_json(
        RUNTIME / "watchdog-deployment.json",
        {
            "source_revision": sha,
            "worker": name,
            "database_id": database_id,
            "url": "https://llmsx-fleet-watchdog.mitchphudson.workers.dev",
            "cron": "* * * * *",
        },
    )
    print(
        "Owned off-host watchdog deployed; metrics/history require the private token."
    )


if __name__ == "__main__":
    deploy()
