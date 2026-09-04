"""llms_full_library.py: the private aggregator-discovery queue —
add → check → incorporate → stale/requeue-stale, and the never-published
guarantee (files/ is only ever read by this module)."""

import llms_full_catalog as catalog
import llms_full_library as lib

DIRECTORY_PAGE = """<html><body>
<p>Some directory of docs. See https://one.example/llms-full.txt and
https://two.example/deep/llms-full.txt for more.</p>
</body></html>"""


def test_add_link_is_idempotent_by_key(tmp_path):
    base = tmp_path / "private"
    first = lib.add_link("https://directory.example/", base=base)
    second = lib.add_link("https://directory.example/", base=base)
    assert first == second
    assert first["status"] == "pending"
    assert len(lib.load_queue(base)) == 1


def test_check_downloads_pending_items_and_sweeps_for_site_urls(tmp_path):
    base = tmp_path / "private"
    lib.add_link("https://directory.example/", base=base)

    def fake_get(url, max_bytes=0):
        assert url == "https://directory.example/"
        return DIRECTORY_PAGE.encode("utf-8"), "text/html", ""

    counts = lib.check(base=base, get=fake_get, log=lambda *_: None)
    assert counts == {"downloaded": 1, "rejected": 0}

    items = lib.load_queue(base)
    entry = next(iter(items.values()))
    assert entry["status"] == "downloaded"
    assert entry["discovered"] == ["https://one.example/llms-full.txt",
                                   "https://two.example/deep/llms-full.txt"]
    # the archived page is private: nothing but this module's own files/ dir
    archived = lib.files_dir(base) / f"{entry['key']}.txt"
    assert archived.is_file()
    assert archived.read_text(encoding="utf-8") == DIRECTORY_PAGE


def test_check_marks_a_fetch_failure_as_rejected_not_a_crash(tmp_path):
    base = tmp_path / "private"
    lib.add_link("https://dead.example/", base=base)

    def fake_get(url, max_bytes=0):
        return None, "", "HTTP 404"

    counts = lib.check(base=base, get=fake_get, log=lambda *_: None)
    assert counts == {"downloaded": 0, "rejected": 1}
    entry = next(iter(lib.load_queue(base).values()))
    assert entry["status"] == "rejected"
    assert entry["reason"] == "HTTP 404"


def test_incorporate_adds_discovered_urls_to_the_public_catalog_only(tmp_path):
    """The aggregator's own page content must never reach the public
    catalog — only the site URLs a sweep discovered inside it."""
    private_base = tmp_path / "private"
    catalog_base = tmp_path / "llms-full"
    lib.add_link("https://directory.example/", base=private_base)
    lib.check(base=private_base,
              get=lambda url, max_bytes=0: (DIRECTORY_PAGE.encode(), "text/html", ""),
              log=lambda *_: None)

    result = lib.incorporate(base=private_base, catalog_base=catalog_base,
                             log=lambda *_: None)
    assert result == {"items": 1, "urls_added": 2}

    cat = catalog.load_catalog(catalog_base)
    assert {r["url"] for r in cat} == {"https://one.example/llms-full.txt",
                                       "https://two.example/deep/llms-full.txt"}
    assert all(r["sources"] == ["manual"] for r in cat)   # added via add_seed

    entry = next(iter(lib.load_queue(private_base).values()))
    assert entry["status"] == "incorporated"
    assert "incorporated_at" in entry


def test_incorporate_only_touches_downloaded_items(tmp_path):
    base = tmp_path / "private"
    lib.add_link("https://still-pending.example/", base=base)   # never checked
    result = lib.incorporate(base=base, catalog_base=tmp_path / "llms-full",
                             log=lambda *_: None)
    assert result == {"items": 0, "urls_added": 0}
    assert next(iter(lib.load_queue(base).values()))["status"] == "pending"


def test_stale_finds_old_checks_and_requeue_stale_resets_them(tmp_path):
    base = tmp_path / "private"
    lib.add_link("https://old.example/", base=base)
    items = lib.load_queue(base)
    key = next(iter(items))
    items[key].update(status="incorporated", checked_at="2000-01-01T00:00:00+00:00")
    lib._save_queue(items, base)

    stale = lib.stale(base=base, max_age_days=30)
    assert [e["key"] for e in stale] == [key]

    n = lib.requeue_stale(base=base, max_age_days=30)
    assert n == 1
    assert lib.load_queue(base)[key]["status"] == "pending"


def test_stale_ignores_items_never_checked(tmp_path):
    base = tmp_path / "private"
    lib.add_link("https://never-checked.example/", base=base)
    assert lib.stale(base=base, max_age_days=0) == []


def test_list_items_filters_by_status(tmp_path):
    base = tmp_path / "private"
    lib.add_link("https://a.example/", base=base)
    lib.add_link("https://b.example/", base=base)
    items = lib.load_queue(base)
    key_b = next(k for k, e in items.items() if e["url"] == "https://b.example/")
    items[key_b]["status"] = "rejected"
    lib._save_queue(items, base)

    assert len(lib.list_items(base=base, status="all")) == 2
    assert [e["url"] for e in lib.list_items(base=base, status="pending")] == \
        ["https://a.example/"]
    assert [e["url"] for e in lib.list_items(base=base, status="rejected")] == \
        ["https://b.example/"]
