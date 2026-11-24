"""The public hostname migration is additive and refuses conflicting ingress or DNS."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("publish_skaas_domains",
                                              ROOT / "scripts" / "publish_skaas_domains.py")
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)
RULES = json.loads((ROOT / "deploy" / "skaas-ingress.json").read_text())


def current_config():
    return {
        "warp-routing": {"enabled": False},
        "ingress": [
            {"hostname": r["hostname"].replace(".skaas.io", ".llms-explorer.com"),
             "service": r["service"], "path": "^/mcp/?$"} for r in RULES
        ] + [{"service": "http_status:404"}],
    }


def test_add_preserves_original_routes_and_other_settings_and_can_be_repeated():
    config = current_config()
    result = deploy.plan_config(config, RULES)
    assert result["ingress"] == RULES + config["ingress"]
    assert result["warp-routing"] == config["warp-routing"]
    assert deploy.plan_config(result, RULES) == result


def test_reject_existing_or_changed_origin():
    config = current_config()
    config["ingress"].insert(0, {**RULES[0], "service": "http://wrong.example.com"})
    with pytest.raises(ValueError, match="Conflicting ingress"):
        deploy.plan_config(config, RULES)
    config = current_config()
    config["ingress"][0]["service"] = "http://wrong.example.com"
    with pytest.raises(ValueError, match="verified origin"):
        deploy.plan_config(config, RULES)


def test_dns_requires_one_proxied_record_for_the_exact_tunnel():
    row = {"type": "CNAME", "content": "tunnel.example.com.", "proxied": True}
    assert deploy.is_tunnel_cname([row], "tunnel.example.com")
    assert not deploy.is_tunnel_cname([row], "other.example.com")
    assert not deploy.is_tunnel_cname([row, row], "tunnel.example.com")
    assert not deploy.is_tunnel_cname([{**row, "proxied": False}], "tunnel.example.com")
