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


@pytest.mark.parametrize("approval", ["identifier", "url"])
def test_public_citation_email_identifiers_keep_their_allowlisted_urls(approval):
    message = "20240429191821.691726-1-helgaas@kernel.org"
    url = "https://lore.kernel.org/linux-pci/" + message + "/"
    allowed = {message if approval == "identifier" else url}
    private = "person@" + "research-customer.dev"
    text = f"Read {url} and contact {private}."
    cleaned = scrub.scrub_public_text(text, allowed=allowed)
    assert url in cleaned
    assert private not in cleaned
    assert "user@example.test" in cleaned
    assert scrub.scrub_public_text(cleaned, allowed=allowed) == cleaned


def test_allowlisted_message_does_not_approve_a_different_email_identifier():
    message = "20240429191821.691726-1-helgaas@kernel.org"
    different = "not-approved-" + message
    url = "https://lore.kernel.org/linux-pci/" + different + "/"
    cleaned = scrub.scrub_public_text(url, allowed={message})
    assert different not in cleaned
    assert cleaned == "https://lore.kernel.org/linux-pci/user@example.test/"


def _findings(text: str, rel: str = "hub/scripts/x.py", deny=()):
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
        return [(name, val) for _, _, name, val, _ in gate.scan([str(p)], deny, gate.allowlist())]
    finally:
        p.unlink()
        for d in reversed(made):
            d.rmdir()


# ---- gate ---------------------------------------------------------------

HELP_ARTICLES = [
    "https://help.drivethrucards.com/hc/en-us/articles/"
    "12780748203543-Specifications-for-Print-Cards",
    "https://help.drivethrucards.com/hc/en-us/articles/"
    "12775347188759-Common-Card-Order-Questions-Answers",
]
SYNTHETIC_DOC_ID = "1" + "AbCdEf0123" * 4 + "AbC"
PUBLISHED_ID_FIXTURE = "outputs/google-doc-id-fixture.txt"


@pytest.mark.parametrize("url", HELP_ARTICLES)
@pytest.mark.parametrize("delimiter", ["", ",", ";"])
def test_help_article_path_slug_is_not_a_google_document_id(url, delimiter):
    assert _findings(url + delimiter, rel=PUBLISHED_ID_FIXTURE) == []


@pytest.mark.parametrize("url", HELP_ARTICLES)
def test_bare_article_shaped_identifiers_are_not_globally_exempt(url):
    hits = _findings(url.rsplit("/", 1)[-1], rel=PUBLISHED_ID_FIXTURE)
    assert [name for name, _ in hits] == ["google doc id"]


@pytest.mark.parametrize("text", [
    SYNTHETIC_DOC_ID,
    "https://docs.google.com/document/d/" + SYNTHETIC_DOC_ID + "/edit",
])
def test_real_google_document_shapes_remain_detected(text):
    assert ("google doc id", SYNTHETIC_DOC_ID) in _findings(text, rel=PUBLISHED_ID_FIXTURE)


@pytest.mark.parametrize("suffix", [
    "?document=" + SYNTHETIC_DOC_ID,
    "#" + SYNTHETIC_DOC_ID,
    "/" + SYNTHETIC_DOC_ID + "/edit",
    " and " + SYNTHETIC_DOC_ID,
])
def test_help_article_does_not_hide_another_identifier(suffix):
    hits = _findings(HELP_ARTICLES[0] + suffix, rel=PUBLISHED_ID_FIXTURE)
    assert ("google doc id", SYNTHETIC_DOC_ID) in hits


def test_help_article_does_not_exempt_mixed_alphanumeric_slug():
    url = "https://support.example.com/hc/en-us/articles/1234567890123-" + SYNTHETIC_DOC_ID
    assert any(name == "google doc id" for name, _ in _findings(url, rel=PUBLISHED_ID_FIXTURE))


def test_help_article_keeps_other_privacy_rules_and_denylist_active():
    text = HELP_ARTICLES[0] + " 192.168.77.75 /Users/synthetic/Documents sensitive-placeholder"  # privacy-ok: synthetic fixture address
    hits = _findings(text, rel=PUBLISHED_ID_FIXTURE, deny=("sensitive-placeholder",))
    names = {name for name, _ in hits}
    assert {"private network address", "operator home path", "denylisted term"} <= names


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


def test_withheld_tracker_key_does_not_redact_a_longer_public_key():
    public = "Public issue SERVER-12345: https://jira.mongodb.org/browse/SERVER-12345"
    assert not scrub._matches(public, ["SERVER-123"])
    assert scrub.scrub_addresses(public, ["SERVER-123"]) == (public, 0)
    assert scrub.scrub_public_text(public, ["SERVER-123"], {"SERVER-12345"}) == public


def test_withheld_tracker_key_redacts_exact_keys_and_derived_fragments():
    private = "SERVER-123 and https://jira.mongodb.org/browse/SERVER-123#comment-1"
    assert scrub._matches(private, ["SERVER-123"])
    assert scrub._matches("server-123-commentary", ["SERVER-123"])
    output = scrub.scrub_public_text(private, ["SERVER-123"], {"SERVER-12345"})
    assert "SERVER-123" not in output
    assert "https://example.test/withheld-reference" in output
    assert scrub.scrub_public_text(output, ["SERVER-123"], {"SERVER-12345"}) == output
    assert scrub.scrub_addresses("SecretHostSuffix", ["SecretHost"])[0] == "[redacted]Suffix"


def test_scrub_rewrites_denylisted_mdns_host_in_code():
    src = 'QUIET = {"SecretHost.local": {}}\nassert x.endswith("secrethost.local")\nmy_SecretHost.local_var = 1\n'
    out, n = scrub.scrub_addresses(src, ["SecretHost"], prose=False)
    assert out == 'QUIET = {"box.test": {}}\nassert x.endswith("box.test")\nmy_SecretHost.local_var = 1\n'
    assert n == 2
    assert scrub.scrub_addresses(out, ["SecretHost"], prose=False)[1] == 0, "idempotent"


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
