# scripts/tests/test_privacy_addresses.py — the network-address rules and the scrub
# that satisfies them. Every literal here is an RFC 5737 / RFC 1918 shape chosen
# for the test, never a real box.
import importlib.util
import os
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import check_publish_privacy as gate
import publish_scrub as scrub


def _findings(text: str, rel: str = "hub/scripts/x.py"):
    """Scan `text` as if it sat at `rel` inside the repo, leaving no trace."""
    p = Path(gate.REPO) / rel
    made = []
    for d in reversed(p.parents):
        if d == Path(gate.REPO) or d.exists():
            continue
        d.mkdir()
        made.append(d)
    assert not p.exists(), f"fixture path collides with a real file: {rel}"
    p.write_text(text)
    try:
        return [(name, val) for _, _, name, val, _ in gate.scan([str(p)], [], gate.allowlist())]
    finally:
        p.unlink()
        for d in reversed(made):
            d.rmdir()


# ---- gate ---------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "HUB_OLLAMA_URLS=http://192.168.77.75:11434=4",       # privacy-ok
    "the gateway is 192.168.77.1 on en15",                # privacy-ok
    "tailnet peer 100.100.7.2 answers",                   # privacy-ok
    "ssh user@10.1.2.3",                                  # privacy-ok
    "curl http://172.16.5.9:8080/",                       # privacy-ok
    "ssh root@gpu-box.local",                             # privacy-ok
    "http://laptop-7.local:11434",                        # privacy-ok
])
def test_operator_addresses_are_flagged_outside_published_paths(text):
    names = {n for n, _ in _findings(text)}
    assert names & {"private network address", "mDNS host as a target"}, text


@pytest.mark.parametrize("text", [
    "route_table_cidr_block = \"10.0.0.0/16\"",           # VPC example, not a target
    "atlas accessLists create --ip 10.0.0.0/8",
    "value > '172.20.1.5'",                                # a bare 172.x in prose
    "example 192.0.2.75 and 198.51.100.117 and 203.0.113.9",  # RFC 5737
    "chrome.storage.local and .claude/settings.local.json and MongoDB.local",
    "base_url=\"https://hub.local/llms\"",   # privacy-ok — a target shape, expected to hit
])
def test_documentation_shapes_do_not_trip_the_address_rule(text):
    # the `https://<name>.local/llms` base_url IS a URL target and is meant to be
    # caught; every other line here must pass clean. Keep the one hit explicit.
    hits = _findings(text)
    if "hub.local" in text:  # privacy-ok
        assert [n for n, _ in hits] == ["mDNS host as a target"]
    else:
        assert hits == [], hits


def test_allowlisted_docs_example_passes():
    assert "192.168.1.10:27021" in gate.allowlist()
    assert _findings('baseURL: "http://192.168.1.10:27021"') == []


def test_identity_rules_stay_scoped_to_published_paths():
    """A home path in hub code is noise the gate has never flagged; only the
    address rules widen to the whole tree."""
    assert _findings("cfg = '/Users/someone/.global-ai-hub'") == []
    assert [n for n, _ in _findings("cfg = '/Users/someone/x'", rel=".claude/skills/t/SKILL.md")] == ["operator home path"]


def test_wide_roots_cover_hub_docs_logs_and_root_files():
    wide = {os.path.relpath(p, gate.REPO) for p in gate.wide_files()}
    assert any(p.startswith("hub/scripts/") for p in wide)
    assert any(p.startswith("hub/tests/") for p in wide)
    assert any(p.startswith("docs/") for p in wide)
    assert "memory.md" in wide and ".mcp.json" in wide
    if (Path(gate.REPO) / "logs" / "memory-hub.md").exists():
        assert "logs/memory-hub.md" in wide


# ---- scrub --------------------------------------------------------------

def test_scrub_keeps_the_last_octet_and_lands_in_rfc5737():
    src = ("pool http://192.168.77.75:11434=4,http://192.168.77.113:11434=3 · tailnet 100.100.7.117 "  # privacy-ok
           "· gateway 192.168.77.0/24 · ssh someone.else@192.168.77.113 · user@10.1.2.3")  # privacy-ok
    out, n = scrub.scrub_addresses(src)
    assert out == ("pool http://192.0.2.75:11434=4,http://192.0.2.113:11434=3 · tailnet 198.51.100.117 "
                   "· gateway 192.0.2.0/24 · ssh user@192.0.2.113 · user@203.0.113.3")
    assert n == 7, "two LAN, one tailnet, one CIDR, one ssh host, one ssh user, one target"
    assert scrub.scrub_addresses(out)[1] == 0, "idempotent"


def test_scrub_rewrites_mdns_targets_and_leaves_storage_local_alone():
    out, _ = scrub.scrub_addresses("http://M-ABC123.local:11434 and root@nuc.local, chrome.storage.local")  # privacy-ok
    assert out == "http://box.test:11434 and user@box.test, chrome.storage.local"


def test_scrub_redacts_denylist_terms_in_prose_only():
    assert scrub.scrub_addresses("box 203.0.113.9 aka SecretHost", ["SecretHost"], prose=True)[0] == "box 203.0.113.9 aka [redacted]"
    assert scrub.scrub_addresses("HOST = 'SecretHost'", ["SecretHost"], prose=False)[0] == "HOST = 'SecretHost'"


def test_scrub_files_touch_code_and_prose_but_not_mirrors(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "REPO", str(tmp_path))
    (tmp_path / "hub").mkdir()
    (tmp_path / "hub" / "a.py").write_text('URL = "http://192.168.9.9:11434"\n')  # privacy-ok
    (tmp_path / "hub" / "b.md").write_text("see 192.168.9.9 on Box9\n")  # privacy-ok
    mirror = tmp_path / "outputs" / "llms-full" / "files"
    mirror.mkdir(parents=True)
    (mirror / "vendor.txt").write_text("their example 192.168.9.9\n")  # privacy-ok
    done = scrub.scrub_address_files([str(tmp_path / "hub"), str(mirror)], ["Box9"])
    assert {os.path.basename(p) for p, _ in done} == {"a.py", "b.md"}
    assert (tmp_path / "hub" / "a.py").read_text() == 'URL = "http://192.0.2.9:11434"\n'
    assert (tmp_path / "hub" / "b.md").read_text() == "see 192.0.2.9 on [redacted]\n"
    assert "192.168.9.9" in (mirror / "vendor.txt").read_text()  # privacy-ok


def test_the_committed_tree_is_clean():
    """The whole point: nothing committed names the operator's network."""
    paths = sorted(set(gate.published_files()) | set(gate.wide_files()))
    findings = [f for f in gate.scan(paths, [], gate.allowlist())
                if f[2] in ("private network address", "mDNS host as a target")]
    assert findings == [], findings[:10]


def test_runbook_is_import_safe():
    spec = importlib.util.spec_from_file_location("g", SCRIPTS / "check_publish_privacy.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.WIDE_RULES
