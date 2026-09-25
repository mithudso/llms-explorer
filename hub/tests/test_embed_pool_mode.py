"""Tests for the persisted embedding-pool mode (embed_core pool local|lan|custom).

The switch exists for travel: off the LAN every unreachable pool host costs a
10s+ timeout on every embedding call. An exported HUB_OLLAMA_URLS cannot serve
that purpose, because the launchd agents that do most of the embedding do not
inherit a shell's environment — hence a file.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


@pytest.fixture
def ec(monkeypatch, tmp_path):
    """embed_core with its mode file redirected into tmp_path, and both env
    overrides cleared so the file is what decides."""
    spec = importlib.util.spec_from_file_location(
        "embed_core_pool_mode", SCRIPTS / "embed_core.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["embed_core_pool_mode"] = mod
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "POOL_MODE_PATH", tmp_path / "pool_mode.json")
    monkeypatch.delenv("HUB_OLLAMA_URLS", raising=False)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    # box_schedule would otherwise drop the laptop from the pool inside its
    # quiet hours, which would make these assertions depend on the clock.
    monkeypatch.setattr(mod, "_quiet", lambda url: False)
    return mod


def test_default_is_the_lan_pool(ec):
    assert ec.pool_mode() == ("lan", ec.LAN_URLS)
    assert [u for u, _w in ec._parse_hosts()] == [
        "http://192.0.2.10:11434",
        "http://laptop.test:11434",
        "http://localhost:11434",
    ]


def test_local_mode_collapses_the_pool_to_this_machine(ec):
    ec.set_pool_mode("local")
    assert ec.pool_mode()[0] == "local"
    assert [u for u, _w in ec._parse_hosts()] == ["http://localhost:11434"]


def test_lan_mode_restores_the_full_pool(ec):
    ec.set_pool_mode("local")
    ec.set_pool_mode("lan")
    assert len(ec._parse_hosts()) == 3


def test_custom_mode_keeps_its_urls(ec):
    ec.set_pool_mode("custom", "http://203.0.113.9:11434=2,http://localhost:11434=1")
    mode, urls = ec.pool_mode()
    assert mode == "custom"
    assert urls.startswith("http://203.0.113.9:11434=2")
    assert [w for _u, w in ec._parse_hosts()] == [2, 1]


def test_custom_mode_without_urls_is_refused(ec):
    with pytest.raises(ValueError):
        ec.set_pool_mode("custom", "  ")
    with pytest.raises(ValueError):
        ec.set_pool_mode("sideways")


def test_env_still_wins_over_the_mode_file(ec, monkeypatch):
    ec.set_pool_mode("local")
    monkeypatch.setenv("HUB_OLLAMA_URLS", "http://192.0.2.10:11434=1")
    assert [u for u, _w in ec._parse_hosts()] == ["http://192.0.2.10:11434"]


def test_a_corrupt_mode_file_falls_back_to_the_lan_pool(ec):
    # A truncated write must never leave the hub with no embedding host.
    ec.POOL_MODE_PATH.write_text('{"mode": "loc')
    assert ec.pool_mode() == ("lan", ec.LAN_URLS)
    assert ec._parse_hosts()


def test_unknown_mode_in_the_file_falls_back(ec):
    ec.POOL_MODE_PATH.write_text(json.dumps({"mode": "aeroplane"}))
    assert ec.pool_mode() == ("lan", ec.LAN_URLS)


def test_write_is_atomic_leaving_no_tmp_behind(ec):
    ec.set_pool_mode("local")
    leftovers = list(ec.POOL_MODE_PATH.parent.glob("*.tmp"))
    assert leftovers == []
