"""llms.txt / llms-full.txt acquisition: the clean path around trafilatura."""

import llms_acquire as la

FULL = (
    """# Hooks reference
Source: https://code.claude.com/docs/en/hooks

Hooks are user-defined shell commands.

```bash
claude --version
```

# Overview
Source: https://code.claude.com/docs/en/overview

## Not a page start
Claude Code is a tool.
"""
    + "x" * 1100
)  # keep the fixture above the 1 KB "absent" floor

INDEX = """# Claude Code Docs
## Getting started
- [Overview](https://code.claude.com/docs/en/overview.md): Claude Code is…
- [Quickstart](https://code.claude.com/docs/en/quickstart.md): Welcome
"""


def test_split_llms_full_starts_pages_at_title_plus_source():
    pages = la.split_llms_full(FULL)
    assert [p["url"] for p in pages] == [
        "https://code.claude.com/docs/en/hooks",
        "https://code.claude.com/docs/en/overview",
    ]
    assert pages[0]["title"] == "Hooks reference"
    assert "```bash\nclaude --version\n```" in pages[0]["text"]  # code survives
    assert "## Not a page start" in pages[1]["text"]  # inner H2 is not a page


def test_split_llms_full_ignores_a_title_inside_a_fence():
    text = FULL + "\n```md\n# Not a page\nSource: https://x/y\n```\n"
    assert len(la.split_llms_full(text)) == 2


def test_parse_llms_index_keeps_md_links():
    assert la.parse_llms_index(INDEX) == [
        "https://code.claude.com/docs/en/overview.md",
        "https://code.claude.com/docs/en/quickstart.md",
    ]


def test_write_mirror_uses_the_banner_contract(tmp_path):
    out = tmp_path / "m.md"
    n = la.write_mirror([{"url": "https://h/a", "title": "A", "text": "body"}], str(out))
    text = out.read_text()
    assert n == 1
    assert "\n" + "=" * 90 + "\nURL: https://h/a\n" + "=" * 90 + "\n\n# A\n\nbody\n" in text


def test_acquire_prefers_llms_full_then_index_then_none(tmp_path):
    served = {
        "https://h/docs/llms-full.txt": FULL,
        "https://h/docs/llms.txt": INDEX.replace("code.claude.com", "h"),
        "https://h/docs/en/overview.md": "# Overview\n\ntext",
        "https://h/docs/en/quickstart.md": None,
    }  # None = fetch failure

    def fetch(url):
        return served.get(url)

    r = la.acquire("https://h/docs", str(tmp_path / "a.md"), fetch=fetch, log=lambda m: None)
    assert r == {"method": "llms-full", "pages": 2, "failed": 0}

    served["https://h/docs/llms-full.txt"] = "tiny"  # < 1 KB counts as absent
    r = la.acquire("https://h/docs", str(tmp_path / "b.md"), fetch=fetch, log=lambda m: None)
    assert r["method"] == "llms" and r["pages"] == 1 and r["failed"] == 1
    assert "URL: https://h/docs/en/overview\n" in (tmp_path / "b.md").read_text()  # .md stripped

    served["https://h/docs/llms.txt"] = None
    served["https://h/llms.txt"] = None
    r = la.acquire("https://h/docs", str(tmp_path / "c.md"), fetch=fetch, log=lambda m: None)
    assert r["method"] is None and not (tmp_path / "c.md").exists()


def test_probe_falls_back_to_the_site_root():
    served = {"https://h/llms.txt": INDEX}
    assert la.probe("https://h/docs/en/intro", fetch=served.get) == {
        "llms_full": None,
        "llms": "https://h/llms.txt",
    }


def test_acquire_respects_max_pages(tmp_path):
    def fetch(url):
        return FULL if url.endswith("llms-full.txt") else None

    r = la.acquire(
        "https://h/docs", str(tmp_path / "a.md"), max_pages=1, fetch=fetch, log=lambda m: None
    )
    assert r["pages"] == 1


def test_probe_rejects_a_full_file_that_is_really_an_index():
    """developer.paypal.com redirects llms-full.txt to its llms.txt: big enough
    to pass the size floor, but it has no `# Title` + `Source:` pages."""
    served = {"https://h/llms-full.txt": INDEX * 20, "https://h/llms.txt": INDEX}
    assert la.probe("https://h/", fetch=served.get) == {
        "llms_full": None,
        "llms": "https://h/llms.txt",
    }


def test_fetch_retries_once(monkeypatch):
    import urllib.error

    calls = []

    class R:
        headers = {"Content-Type": "text/plain"}

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b"ok"

    def fake_open(req, timeout=0):
        calls.append(req.full_url)
        if len(calls) == 1:
            raise urllib.error.URLError("flaky")
        return R()

    monkeypatch.setattr(la.urllib.request, "urlopen", fake_open)
    monkeypatch.setattr(la.time, "sleep", lambda s: None)
    assert la._fetch("https://h/llms.txt") == "ok" and len(calls) == 2


YAML_FULL = """# Anthropic docs

---

## Getting started
---
title: Quickstart
url: https://platform.claude.com/docs/en/quickstart
description: First call
---
Make your first API call.

## Errors
---
title: Errors
url: https://platform.claude.com/docs/en/errors
---
Every error code.
"""

CF_FULL = """---
description: Route traffic across the fastest paths.
title: Argo Smart Routing
image: https://developers.cloudflare.com/og-docs.png
---

[Skip to content](#main-content)

> Documentation Index
> Fetch the complete documentation index at: https://developers.cloudflare.com/argo-smart-routing/llms.txt
> Use this file to discover all available pages before exploring further.

# Argo Smart Routing

Last updated Aug 25, 2026|Copy as Markdown|[View as Markdown](https://developers.cloudflare.com/argo-smart-routing/index.md)
|[Agent setup](https://x)

Speed up your global traffic.
---
description: Second
title: Workers
---
# Workers
[View as Markdown](https://developers.cloudflare.com/workers/index.md)
Serverless.
"""

FC_FULL = """<|firecrawl-page-1-lllmstxt|>
# Page one
Body one.
<|firecrawl-page-2-lllmstxt|>
# Page two
Body two.
"""


def test_split_llms_full_reads_yaml_block_grammar():
    pages = la.split_llms_full(YAML_FULL)
    assert [(p["title"], p["url"]) for p in pages] == [
        ("Quickstart", "https://platform.claude.com/docs/en/quickstart"),
        ("Errors", "https://platform.claude.com/docs/en/errors"),
    ]
    assert pages[0]["description"] == "First call" and "first API call" in pages[0]["text"]


def test_split_llms_full_reads_cloudflare_frontmatter_and_view_as_markdown():
    pages = la.split_llms_full(CF_FULL)
    assert [p["url"] for p in pages] == [
        "https://developers.cloudflare.com/argo-smart-routing/",
        "https://developers.cloudflare.com/workers/",
    ]
    assert pages[0]["title"] == "Argo Smart Routing"
    assert "Documentation Index" not in pages[0]["text"]  # nav blockquote stripped
    assert "Speed up your global traffic." in pages[0]["text"]


def test_split_llms_full_reads_firecrawl_delimiters():
    pages = la.split_llms_full(FC_FULL)
    assert [(p["title"], p["url"]) for p in pages] == [
        ("Page one", "page-1"),
        ("Page two", "page-2"),
    ]


def test_strip_index_blockquote_only_touches_the_leading_one():
    text = ("> ## Documentation Index\n> Fetch the complete documentation index at: "
            "https://h/llms.txt\n\n# T\n\n> a real quote\n")
    assert la.strip_index_blockquote(text) == "# T\n\n> a real quote\n"
