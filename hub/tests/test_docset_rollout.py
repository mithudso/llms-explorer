"""docset_rollout: probe hosts, move mirrors aside + reset queue items, guarded cleanup."""

import json

import docset_rollout as dr
from hub_manager import core, queue_model


def _seed(hub_tmp):
    core.MIRROR_OUT_DIR.mkdir()
    queue_model.add_urls(["https://full.example/docs", "https://idx.example/",
                          "https://crawl.example/kb"])
    for stem in ("full.example", "idx.example", "crawl.example"):
        (core.MIRROR_OUT_DIR / f"{stem}.md").write_text("old trafilatura mirror")
        (core.MIRROR_OUT_DIR / f"{stem}_state.json").write_text("{}")


FULL = "# Page\nSource: https://full.example/docs/page\n\n" + "body text " * 200


def _fetch(url):
    return {"https://full.example/docs/llms-full.txt": FULL,
            "https://idx.example/llms.txt": "- [a](https://idx.example/a.md)"}.get(url)


def test_probe_classifies_hosts(hub_tmp):
    _seed(hub_tmp)
    rows = dr.probe(dr.queue_urls(), fetch=_fetch, log=lambda s: None)
    assert [(r["url"].split("//")[1].split("/")[0], r["method"]) for r in rows] == [
        ("full.example", "llms-full"), ("idx.example", "llms"), ("crawl.example", "crawl")]
    assert rows[0]["mirror_exists"] and rows[0]["acquired"] is None


def test_apply_moves_mirror_aside_and_resets_only_the_group(hub_tmp):
    _seed(hub_tmp)
    rows = dr.probe(dr.queue_urls(), fetch=_fetch, log=lambda s: None)
    dry = dr.apply(rows, group="llms-full", dry_run=True, log=lambda s: None)
    assert dry == {"group": "llms-full", "targets": 1, "moved": 2, "reset": 1, "dry_run": True}
    assert (core.MIRROR_OUT_DIR / "full.example.md").exists()        # dry run touched nothing
    r = dr.apply(rows, group="llms-full", log=lambda s: None)
    assert r["moved"] == 2 and r["reset"] == 1
    assert not (core.MIRROR_OUT_DIR / "full.example.md").exists()
    backups = list((core.MIRROR_OUT_DIR / "_oversized_backup").iterdir())
    assert {b.suffix for b in backups} == {".md", ".json"}
    assert all("pre-llms" in b.name for b in backups)
    items = {i.url: i for i in queue_model.load_items()}
    assert items["https://full.example/docs"].status == "pending"
    assert items["https://idx.example/"].stage_done == []              # untouched (other group)
    assert (core.MIRROR_OUT_DIR / "idx.example.md").exists()


def test_apply_skips_hosts_already_acquired_cleanly(hub_tmp):
    _seed(hub_tmp)
    (core.MIRROR_OUT_DIR / "full.example_state.json").write_text(
        json.dumps({"acquire": "llms-full"}))
    rows = dr.probe(dr.queue_urls(), fetch=_fetch, log=lambda s: None)
    assert dr.apply(rows, group="llms-full", log=lambda s: None)["targets"] == 0


def test_cleanup_only_where_a_fact_layer_exists(hub_tmp):
    core.MIRROR_OUT_DIR.mkdir()
    for stem, has_ref in (("done.example", True), ("todo.example", False)):
        pages = core.MIRROR_OUT_DIR / f"{stem}.pages"
        pages.mkdir()
        (pages / f"{stem}_master.md").write_text("m" * 100)
        (pages / f".{stem}_distill_index.json").write_text("{}")
        (pages / "001_page.md").write_text("keep")
        if has_ref:
            ref = core.MIRROR_OUT_DIR / f"{stem}.reference"
            ref.mkdir()
            (ref / "summary.json").write_text("{}")
    r = dr.cleanup(core.MIRROR_OUT_DIR, log=lambda s: None)
    assert r["deleted"] == 2 and r["skipped_docsets"] == 1
    assert not (core.MIRROR_OUT_DIR / "done.example.pages" / "done.example_master.md").exists()
    assert (core.MIRROR_OUT_DIR / "done.example.pages" / "001_page.md").exists()
    assert (core.MIRROR_OUT_DIR / "todo.example.pages" / "todo.example_master.md").exists()


def test_apply_skips_items_with_a_stage_running(hub_tmp):
    _seed(hub_tmp)
    import json as _json
    raw = _json.loads(core.QUEUE_STATE.read_text())
    raw["items"]["https://full.example/docs"]["status"] = "running"
    core.QUEUE_STATE.write_text(_json.dumps(raw))
    rows = dr.probe(dr.queue_urls(), fetch=_fetch, log=lambda s: None)
    assert dr.apply(rows, group="llms-full", log=lambda s: None)["targets"] == 0
    assert (core.MIRROR_OUT_DIR / "full.example.md").exists()
