"""llms_serve: root index over hub exports + the llms-full mirror, per-file routes, headers."""

import json
import threading
import urllib.request

import pytest

import llms_serve
from hub_manager import core

FULL = (
    "# Hooks\nSource: https://ex.dev/hooks\n\nHooks run at lifecycle points. More words here.\n\n"
    "# Auth\nSource: https://ex.dev/auth\n\nCreate an API key first. Then rotate it.\n"
)


def _setup(hub_tmp, monkeypatch):
    # a hub export
    d = core.MIRROR_OUT_DIR / "ex.dev.llms"
    d.mkdir(parents=True)
    (d / "llms.txt").write_text(
        "# Ex docs\n\n> Ex.\n\n## Overview\n\n- [Hooks](https://ex.dev/hooks.md): Hooks.\n"
    )
    (d / "llms-full.txt").write_text(FULL)
    (d / "manifest.json").write_text(
        json.dumps(
            {
                "title": "Ex docs",
                "pages": 2,
                "units": 5,
                "files": {
                    "llms.txt": {"bytes": 60, "tokens": 15},
                    "llms-full.txt": {"bytes": 150, "tokens": 37},
                    "llms-facts.txt": {"bytes": 10, "tokens": 2},
                },
            }
        )
    )
    # a mirrored llms-full.txt
    base = hub_tmp / "llms-full"
    (base / "files").mkdir(parents=True)
    f = base / "files" / "vendor.io.txt"
    f.write_text(FULL)
    (base / "manifest.json").write_text(
        json.dumps(
            {
                "vendor.io": {
                    "key": "vendor.io",
                    "url": "https://vendor.io/llms-full.txt",
                    "name": "Vendor",
                    "site": "https://vendor.io",
                    "category": "developer tools",
                    "status": "ok",
                    "bytes": len(FULL),
                    "pages": 2,
                    "file": str(f),
                }
            }
        )
    )
    (base / "catalog.json").write_text("[]")
    monkeypatch.setattr(llms_serve.llms_full_catalog, "BASE_DIR", base)
    srv = llms_serve.serve("127.0.0.1", 0, mirror_dir=core.MIRROR_OUT_DIR)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, dict(r.headers), r.read().decode()


def test_root_index_lists_exports_and_mirrors(hub_tmp, monkeypatch):
    srv, base = _setup(hub_tmp, monkeypatch)
    try:
        status, h, body = _get(f"{base}/llms.txt")
        assert status == 200 and h["Content-Type"].startswith("text/markdown")
        assert body.startswith("# Global AI Hub — llms.txt\n\n> ")
        assert (
            f"- [Ex docs]({base}/d/ex.dev/llms.txt): 2 pages, ~15 tokens index, "
            "~37 tokens full, 5 facts" in body
        )
        assert "## Mirrored: developer tools" in body
        assert f"- [Vendor]({base}/m/vendor.io/llms.txt): https://vendor.io — 2 pages" in body
        assert int(h["X-Markdown-Tokens"]) >= 1
        _, _, idx = _get(f"{base}/index.json")
        j = json.loads(idx)
        assert j["docsets"][0]["stem"] == "ex.dev" and j["mirrors"][0]["key"] == "vendor.io"
    finally:
        srv.shutdown()


def test_docset_and_mirror_routes_with_describedby(hub_tmp, monkeypatch):
    srv, base = _setup(hub_tmp, monkeypatch)
    try:
        status, h, body = _get(f"{base}/d/ex.dev/llms-full.txt")
        assert status == 200 and body == FULL
        assert h["Link"] == f'<{base}/d/ex.dev/llms.txt>; rel="describedby"'
        status, h, body = _get(f"{base}/m/vendor.io/llms.txt")
        assert (
            "# Vendor" in body
            and "- [Hooks](https://ex.dev/hooks): Hooks run at lifecycle points." in body
        )
        assert f"[Whole file]({base}/m/vendor.io/llms-full.txt)" in body
        status, h, body = _get(f"{base}/m/vendor.io/pages/2.md")
        assert body.startswith("# Auth\nSource: https://ex.dev/auth\n")
        assert h["Link"] == f'<{base}/m/vendor.io/llms.txt>; rel="describedby"'
        status, _, body = _get(f"{base}/m/vendor.io/llms-full.txt")
        assert body == FULL
        _, h, _ = _get(f"{base}/d/ex.dev/manifest.json")
        assert h["Content-Type"].startswith("application/json")
    finally:
        srv.shutdown()


def test_unknown_and_unsafe_paths_are_404(hub_tmp, monkeypatch):
    srv, base = _setup(hub_tmp, monkeypatch)
    try:
        for path in (
            "/d/ex.dev/../../etc/passwd",
            "/d/ex.dev/nope.txt",
            "/m/nope/llms.txt",
            "/m/vendor.io/pages/9.md",
            "/x",
        ):
            try:
                urllib.request.urlopen(f"{base}{path}", timeout=5)
                raise AssertionError(f"{path} should 404")
            except urllib.error.HTTPError as e:
                assert e.code == 404, path
    finally:
        srv.shutdown()


def test_topical_route_and_root_topics(hub_tmp, monkeypatch):
    srv, base = _setup(hub_tmp, monkeypatch)
    srv.shutdown()
    tdir = hub_tmp / "llms-topical" / "llms-txt.llms"
    tdir.mkdir(parents=True)
    (tdir / "llms.txt").write_text("# llms.txt topical\n\n> T.\n\n## Spec\n\n- [Facts](x): y\n")
    (tdir / "llms-facts.txt").write_text(
        "# llms.txt topical — facts\n\n- [statement] a — https://s\n"
    )
    (tdir / "llms-vocabulary.txt").write_text(
        "# llms.txt topical — vocabulary\n\n## Terms\n\n- **x**\n"
    )
    (tdir / "manifest.json").write_text(
        json.dumps(
            {
                "title": "llms.txt topical",
                "units": 12,
                "sources": 4,
                "sections": {"Spec": {}, "Grammars": {}},
                "files": {"llms-facts.txt": {"bytes": 40, "tokens": 10}},
            }
        )
    )
    srv = llms_serve.serve(
        "127.0.0.1", 0, mirror_dir=core.MIRROR_OUT_DIR, topical_dir=hub_tmp / "llms-topical"
    )
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        _, _, body = _get(f"{base}/llms.txt")
        assert "## Topics" in body
        assert (
            f"- [llms.txt topical]({base}/t/llms-txt/llms.txt): 12 facts from 4 sources, "
            "2 sections, ~10 tokens facts"
        ) in body
        status, h, body = _get(f"{base}/t/llms-txt/llms-facts.txt")
        assert status == 200 and body.startswith("# llms.txt topical — facts")
        assert h["Link"] == f'<{base}/t/llms-txt/llms.txt>; rel="describedby"'
        status, h, body = _get(f"{base}/t/llms-txt/manifest.json")
        assert h["Content-Type"].startswith("application/json")
        status, h, body = _get(f"{base}/t/llms-txt/llms-vocabulary.txt")
        assert status == 200 and "## Terms" in body and "describedby" in h["Link"]
        import urllib.error

        with pytest.raises(urllib.error.HTTPError):
            _get(f"{base}/t/llms-txt/llms-full.txt")
        with pytest.raises(urllib.error.HTTPError):
            _get(f"{base}/t/../etc/llms.txt")
    finally:
        srv.shutdown()


def test_split_index_section_route(hub_tmp, monkeypatch):
    srv, base = _setup(hub_tmp, monkeypatch)
    sec = next(hub_tmp.rglob("ex.dev.llms")) / "getting-started"
    sec.mkdir()
    (sec / "llms.txt").write_text(
        "# Ex docs — getting-started\n\n> 1 page.\n\n## getting-started\n\n"
        "- [A](https://ex.dev/a.md): a\n"
    )
    try:
        status, h, body = _get(f"{base}/d/ex.dev/getting-started/llms.txt")
        assert status == 200 and body.startswith("# Ex docs — getting-started")
        assert h["Link"] == f'<{base}/d/ex.dev/llms.txt>; rel="describedby"'
        for bad in (
            "/d/ex.dev/nope/llms.txt",
            "/d/ex.dev/getting-started/manifest.json",
            "/d/ex.dev/getting-started/../llms-full.txt",
        ):
            try:
                urllib.request.urlopen(f"{base}{bad}", timeout=5)
                raise AssertionError(f"{bad} should 404")
            except urllib.error.HTTPError as e:
                assert e.code == 404, bad
    finally:
        srv.shutdown()


def test_concept_route_and_root_concepts(hub_tmp, monkeypatch):
    """/c/<slug>/… serves a concept pack (llms-concept-abstractor) and the root lists it."""
    srv, base = _setup(hub_tmp, monkeypatch)
    srv.shutdown()
    cdir = hub_tmp / "llms-concepts" / "prompt-caching.llms"
    cdir.mkdir(parents=True)
    (cdir / "llms.txt").write_text("# Prompt caching — concept pack\n\n> P.\n\n## Read first\n\n- [Full](llms-full.txt): x\n")
    (cdir / "llms-full.txt").write_text(
        "# Prompt caching — concept pack\n\n## Definitions\n\n- [definition] a — https://s\n"
    )
    (cdir / "manifest.json").write_text(
        json.dumps(
            {
                "kind": "concept", "concept": "Prompt caching", "slug": "prompt-caching",
                "kept_units": 194, "sources": {"platform.claude.com": 164, "openrouter.ai": 30},
                "facets": {"definition": 4, "parameters": 73},
                "files": {"llms-small.txt": {"bytes": 1, "tokens": 8201}}, "children": {},
            }
        )
    )
    srv = llms_serve.serve(
        "127.0.0.1", 0, mirror_dir=core.MIRROR_OUT_DIR, topical_dir=hub_tmp / "llms-topical",
        concept_dir=hub_tmp / "llms-concepts",
    )
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        _, _, body = _get(f"{base}/llms.txt")
        assert "## Concepts" in body
        assert (
            f"- [Prompt caching]({base}/c/prompt-caching/llms.txt): 194 units from 2 sources, "
            "2 facets, ~8201 tokens small"
        ) in body
        status, h, body = _get(f"{base}/c/prompt-caching/llms-full.txt")
        assert status == 200 and body.startswith("# Prompt caching — concept pack")
        assert h["Link"] == f'<{base}/c/prompt-caching/llms.txt>; rel="describedby"'
        status, h, body = _get(f"{base}/c/prompt-caching/manifest.json")
        assert h["Content-Type"].startswith("application/json")
        status, _, body = _get(f"{base}/index.json")
        assert json.loads(body)["concepts"][0]["slug"] == "prompt-caching"
        import urllib.error

        with pytest.raises(urllib.error.HTTPError):
            _get(f"{base}/c/prompt-caching/pool.jsonl")
        with pytest.raises(urllib.error.HTTPError):
            _get(f"{base}/c/../etc/llms.txt")
    finally:
        srv.shutdown()
