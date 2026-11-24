#!/usr/bin/env python3
"""Check or apply the additive SKaaS hostname mapping using an authenticated Cloudflare CLI."""

import argparse
import json
import subprocess
from pathlib import Path


def cf(*args):
    result = subprocess.run(["cf", *args], capture_output=True, check=False, text=True)
    if result.returncode:
        raise SystemExit(f"Cloudflare command {' '.join(args[:3])} failed ({result.returncode})")
    response = json.loads(result.stdout)
    return response.get("result", response) if isinstance(response, dict) else response


def records(zone, name):
    return cf("dns", "records", "list", "--zone", zone, "--name", name)


def is_tunnel_cname(rows, target):
    return (len(rows) == 1 and rows[0]["type"] == "CNAME" and rows[0]["proxied"]
            and rows[0]["content"].rstrip(".") == target)


def plan_config(config, rules):
    """Add only the requested routes when the existing dedicated tunnel matches its contract."""
    ingress = config["ingress"]
    if not ingress or ingress[-1] != {"service": "http_status:404"}:
        raise ValueError("Unexpected tunnel fallback rule")
    missing = []
    for rule in rules:
        label = rule["hostname"].split(".", 1)[0]
        legacy = [r for r in ingress if r.get("hostname") == f"{label}.llms-explorer.com"]
        if (len(legacy) != 1 or legacy[0].get("service") != rule["service"]
                or legacy[0].get("path") != "^/mcp/?$" or legacy[0].get("originRequest")):
            raise ValueError(f"Existing {label} ingress differs from its verified origin")
        existing = [r for r in ingress if r.get("hostname") == rule["hostname"]]
        if existing and existing != [rule]:
            raise ValueError(f"Conflicting ingress for {rule['hostname']}")
        if not existing:
            missing.append(rule)
    return {**config, "ingress": [*missing, *ingress]}


def publish(rules, apply):
    zones = {}
    for zone in ("skaas.io", "llms-explorer.com"):
        matches = cf("zones", "list", "--name", zone)
        if len(matches) != 1 or matches[0]["status"] != "active":
            raise ValueError(f"Cannot verify active {zone} zone")
        zones[zone] = matches[0]
    if len({z["account"]["id"] for z in zones.values()}) != 1:
        raise ValueError("The zones belong to different accounts")
    tunnels = [t for t in cf("tunnels", "list", "--name", "skill-registry-mongo")
               if t.get("name") == "skill-registry-mongo" and t.get("status") == "healthy"
               and t.get("config_src") == "cloudflare" and not t.get("deleted_at")]
    if len(tunnels) != 1 or tunnels[0]["account_tag"] != zones["skaas.io"]["account"]["id"]:
        raise ValueError("Cannot verify the healthy remotely managed tunnel in this account")
    tunnel_id = tunnels[0]["id"]
    target = f"{tunnel_id}.cfargotunnel.com"
    missing = []
    for rule in rules:
        name = rule["hostname"]
        legacy = name.removesuffix(".skaas.io") + ".llms-explorer.com"
        if not is_tunnel_cname(records("llms-explorer.com", legacy), target):
            raise ValueError(f"Cannot verify existing tunnel DNS for {legacy}")
        existing = records("skaas.io", name)
        if existing and not is_tunnel_cname(existing, target):
            raise ValueError(f"Conflicting DNS for {name}")
        if not existing:
            missing.append(name)

    snapshot = cf("tunnels", "config", "get", tunnel_id)
    config = plan_config(snapshot["config"], rules)
    changed = config != snapshot["config"]
    print(f"Tunnel ingress change: {changed}. DNS records to add: {missing}.")
    if not apply:
        return
    if changed:
        if cf("tunnels", "config", "get", tunnel_id) != snapshot:
            raise ValueError("Tunnel configuration changed during planning; rerun")
        cf("tunnels", "config", "update", tunnel_id, "--body", json.dumps({"config": config}))
    if cf("tunnels", "config", "get", tunnel_id)["config"] != config:
        raise ValueError("Tunnel config read-back failed")
    for name in missing:
        body = {"type": "CNAME", "name": name, "content": target, "ttl": 1, "proxied": True}
        cf("dns", "records", "create", "--zone", "skaas.io", "--body", json.dumps(body))
    for rule in rules:
        if not is_tunnel_cname(records("skaas.io", rule["hostname"]), target):
            raise ValueError(f"DNS read-back failed for {rule['hostname']}")
    print("Verified the tunnel ingress and both proxied DNS records.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="apply and verify the additions")
    args = parser.parse_args()
    rules_path = Path(__file__).resolve().parents[1] / "deploy" / "skaas-ingress.json"
    publish(json.loads(rules_path.read_text()), args.apply)
