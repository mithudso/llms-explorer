import json

from hub_manager import core, queue_model


def test_add_urls_creates_state_and_seed_list(hub_tmp):
    n = queue_model.add_urls(["https://a.example/", "https://b.example/", " "])
    assert n == 2
    items = queue_model.load_items()
    assert {i.url for i in items} == {"https://a.example/", "https://b.example/"}
    assert all(i.status == "pending" for i in items)
    seeds = core.DOCS_LIST.read_text().splitlines()
    assert seeds == ["https://a.example/", "https://b.example/"]


def test_add_urls_is_idempotent_on_seed_list(hub_tmp):
    queue_model.add_urls(["https://a.example/"])
    queue_model.add_urls(["https://a.example/"])
    assert core.DOCS_LIST.read_text().splitlines() == ["https://a.example/"]


def test_retry_all_requeues_only_failed(hub_tmp):
    core.QUEUE_STATE.write_text(json.dumps({"items": {
        "u1": {"status": "failed", "attempts": 3, "error": "boom"},
        "u2": {"status": "done"},
        "u3": {"status": "pending"},
    }}))
    assert queue_model.retry() == 1
    items = {i.url: i for i in queue_model.load_items()}
    assert items["u1"].status == "pending"
    assert items["u1"].attempts == 0
    assert items["u1"].error == ""
    assert items["u2"].status == "done"


def test_retry_explicit_requeues_any_state(hub_tmp):
    core.QUEUE_STATE.write_text(json.dumps({"items": {
        "u1": {"status": "done"},
        "u2": {"status": "done"},
    }}))
    assert queue_model.retry(["u1"]) == 1
    items = {i.url: i for i in queue_model.load_items()}
    assert items["u1"].status == "pending"
    assert items["u2"].status == "done"


def test_remove_deletes_state_and_seed(hub_tmp):
    queue_model.add_urls(["https://a.example/", "https://b.example/"])
    assert queue_model.remove("https://a.example/") is True
    assert queue_model.remove("https://a.example/") is False
    assert [i.url for i in queue_model.load_items()] == ["https://b.example/"]
    assert core.DOCS_LIST.read_text().splitlines() == ["https://b.example/"]


def test_summary_counts(hub_tmp):
    core.QUEUE_STATE.write_text(json.dumps({"items": {
        "u1": {"status": "done"}, "u2": {"status": "done"},
        "u3": {"status": "failed"},
    }}))
    assert queue_model.summary() == {"done": 2, "failed": 1}


def test_manager_pid_none_without_lock(hub_tmp):
    assert queue_model.manager_pid() is None


def test_manager_pid_stale_lock(hub_tmp):
    core.QUEUE_LOCK.write_text("999999")  # beyond macOS pid range
    assert queue_model.manager_pid() is None


def test_manager_pid_live_lock(hub_tmp):
    import os
    core.QUEUE_LOCK.write_text(str(os.getpid()))
    assert queue_model.manager_pid() == os.getpid()


def test_load_items_handles_corrupt_state(hub_tmp):
    core.QUEUE_STATE.write_text("{not json")
    assert queue_model.load_items() == []


def test_stage_progress_pending():
    it = queue_model.QueueItem(url="https://a.example/", status="pending")
    step, note = queue_model.stage_progress(it)
    assert step == "queued"
    assert "3/3 left" in note


def test_stage_progress_running_next_stage():
    it = queue_model.QueueItem(url="https://a.example/", status="running",
                               stage_done=["mirror"])
    step, note = queue_model.stage_progress(it)
    assert step == "refine"
    assert "2/3 left" in note


def test_stage_progress_done():
    it = queue_model.QueueItem(url="https://a.example/", status="done",
                               stage_done=["mirror", "refine", "index"])
    step, note = queue_model.stage_progress(it)
    assert step == "done"
    assert note == "-"


def test_legacy_distill_items_need_refine():
    """Items finished before 2026-08-30 carry `distill`; refine is what's left."""
    it = queue_model.QueueItem(url="https://a.example/", status="done",
                               stage_done=["distill", "index", "mirror"])
    assert it.remaining_stages == ["refine"]


def test_stage_progress_failed_notes_failure():
    it = queue_model.QueueItem(url="https://a.example/", status="failed",
                               stage_done=["mirror"])
    step, note = queue_model.stage_progress(it)
    assert step == "refine"
    assert "failed" in note


def test_stage_progress_uses_live_crawl_activity():
    it = queue_model.QueueItem(url="https://docs.example.com/x", status="running")
    activity = [{"host": "docs.example.com", "crawled": 12, "queued": 4,
                "updated": 0.0}]
    step, note = queue_model.stage_progress(it, activity)
    assert step == "mirror"
    assert note == "12p crawled, 4 queued"


def test_build_item_report_running_item(monkeypatch, tmp_path):
    """Regression: the report used to call pipeline_manager._shard_out_path,
    removed with the shard/Syncthing design, and crashed the whole TUI."""
    import pipeline_manager as pm

    mirror = tmp_path / "docs.example.com.md"
    mirror.write_text("URL: https://docs.example.com/a\nbody\n"
                      "URL: https://docs.example.com/b\nbody\n")
    ref = tmp_path / "docs.example.com.reference"
    ref.mkdir()
    (ref / "pages.json").write_text("[]")
    (ref / "._hidden").write_text("appledouble")
    (ref / "units.state.json").write_text(json.dumps(
        {"https://docs.example.com/a": {"ok": True}, "https://docs.example.com/b": {"ok": False}}))
    (ref / "summary.json").write_text(json.dumps(
        {"units": 3, "units_by_origin": {"code": 2, "llm": 1}}))
    monkeypatch.setattr(pm, "mirror_path_for", lambda url: mirror)

    it = queue_model.QueueItem(url="https://docs.example.com/", status="running",
                               stage_done=["mirror"], updated="2026-08-29T20:28:01",
                               boxes_used=["local", "192.168.4.75"])
    report = queue_model.build_item_report(it)

    assert "Artifacts" in report
    assert "3 file(s)" in report           # AppleDouble sidecar not counted
    assert "3 units" in report and "code 2, llm 1" in report
    assert "Refine budget" in report and "1 page(s) done, 1 failed" in report
    assert "shard" not in report.lower()
