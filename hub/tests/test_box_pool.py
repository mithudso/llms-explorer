"""Tests for item-level work placement (pipeline_manager.BoxPool) and the
remote-path guards that replaced the Syncthing-mediated shard dispatcher."""

import importlib.util
import sys
import threading
import time
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


@pytest.fixture
def pm(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location(
        "pipeline_manager_boxpool", SCRIPTS / "pipeline_manager.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["pipeline_manager_boxpool"] = mod
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "MIRROR_OUT_DIR", tmp_path / "text-mirror")
    (tmp_path / "text-mirror").mkdir()
    return mod


# --------------------------------------------------------------------------- #
# remote path safety — the bug class that stranded 237MB of crawl output
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("name", ["mongodb.com.md", "docs.aws.amazon.com.md",
                                  "a-b_c.1.md", "x.md"])
def test_safe_leaf_accepts_real_hostnames(pm, name):
    assert pm.safe_leaf(name) == name


@pytest.mark.parametrize("name", [
    "host:8080.md",        # a colon makes rsync read the path as host:path
    "a b.md",              # unquoted split on a box without --protect-args
    "../escape.md",
    "$(id).md",
    "-rf.md",              # leading dash reads as an option
    "",
])
def test_safe_leaf_rejects_shell_hostile_names(pm, name):
    with pytest.raises(pm.UnsafeRemoteName):
        pm.safe_leaf(name)


def test_work_path_is_absolute_and_tilde_free(pm):
    """The retired dispatcher shlex.quote()d a ~-prefixed path, so the remote
    shell never expanded it and every crawl landed in a literal `~` dir."""
    box = pm.Box("nuc", "user@nuc", "/home/user")
    path = box.work_path("mongodb.com.md")
    assert path.startswith("/home/user/")
    assert "~" not in path


def test_remote_safe_falls_back_for_hostile_name(pm, capsys):
    box = pm.Box("nuc", "user@nuc", "/home/user")
    assert pm.remote_safe(box, Path("/x/mongodb.com.md")) is True
    assert pm.remote_safe(box, Path("/x/host:8080.md")) is False


def test_stage_mirror_stays_local_when_name_is_unsafe(pm, monkeypatch):
    calls = {}

    def fake_run_stage(*a, **k):
        calls["local"] = True
        return True, "ok"

    monkeypatch.setattr(pm, "_run_stage", fake_run_stage)
    monkeypatch.setattr(pm, "_remote_mirror",
                        lambda *a, **k: pytest.fail("must not dispatch remotely"))
    monkeypatch.setattr(pm, "mirror_path_for",
                        lambda url: pm.MIRROR_OUT_DIR / "host:8080.md")
    (pm.MIRROR_OUT_DIR / "host:8080.md").write_text("x" * 2000)
    box = pm.Box("nuc", "user@nuc", "/home/user")
    ok, _ = pm.stage_mirror("https://host:8080/", 100, box)
    assert ok and calls["local"]


def test_mirror_artifact_filters_cover_dotfile_sidecars(pm):
    """`<stem>*` does not match a dot-prefixed sidecar; without its own rule
    it never comes back and the next run redoes the work."""
    filters = pm._mirror_artifact_filters("mongodb.com")
    assert "--include=.mongodb.com*" in filters
    assert "--include=mongodb.com*/**" in filters   # the .pages/ tree
    assert filters[-1] == "--exclude=*"


# --------------------------------------------------------------------------- #
# BoxPool
# --------------------------------------------------------------------------- #

def _pool(pm, n=3, slots=2):
    boxes = [pm.Box("local", None, "/home/me")]
    boxes += [pm.Box(f"r{i}", f"u@r{i}", f"/home/r{i}") for i in range(1, n)]
    return pm.BoxPool(boxes, slots=slots)


def test_capacity_is_boxes_times_slots(pm):
    assert _pool(pm, n=3, slots=2).capacity == 6


def test_acquire_spreads_across_boxes_before_doubling_up(pm):
    pool = _pool(pm, n=3, slots=2)
    got = [pool.acquire().label for _ in range(3)]
    assert sorted(got) == ["local", "r1", "r2"]


def test_acquire_blocks_when_every_slot_is_taken(pm):
    pool = _pool(pm, n=1, slots=1)
    pool.acquire()
    done = threading.Event()

    def waiter():
        pool.acquire()
        done.set()

    threading.Thread(target=waiter, daemon=True).start()
    assert not done.wait(timeout=0.5)


def test_release_wakes_a_waiter(pm):
    pool = _pool(pm, n=1, slots=1)
    box = pool.acquire()
    done = threading.Event()

    def waiter():
        pool.acquire()
        done.set()

    threading.Thread(target=waiter, daemon=True).start()
    time.sleep(0.1)
    pool.release(box)
    assert done.wait(timeout=5)


def test_benched_box_is_skipped(pm):
    pool = _pool(pm, n=2, slots=1)
    remote = next(b for b in pool.boxes if not b.is_local)
    pool.bench(remote)
    assert pool.acquire().label == "local"


def test_empty_box_list_is_refused(pm):
    with pytest.raises(SystemExit):
        pm.BoxPool([], slots=1)


# --------------------------------------------------------------------------- #
# discovery
# --------------------------------------------------------------------------- #

def test_local_only_never_probes_remotes(pm, monkeypatch):
    monkeypatch.setattr(pm, "remote_targets",
                        lambda: pytest.fail("must not enumerate remotes"))
    boxes = pm.discover_boxes(allow_remote=False)
    assert [b.label for b in boxes] == ["local"]
    assert boxes[0].is_local


def test_unprobeable_remote_is_dropped(pm, monkeypatch):
    monkeypatch.setattr(pm, "remote_targets", lambda: [("r1", "u@r1"), ("r2", "u@r2")])
    monkeypatch.setattr(pm, "probe_box", lambda t: "/home/r1" if t == "u@r1" else None)
    monkeypatch.setattr(pm, "_hm_remotes", lambda: None)
    assert [b.label for b in pm.discover_boxes()] == ["local", "r1"]


# --------------------------------------------------------------------------- #
# cmd_run: continuous feed, not a batch barrier
# --------------------------------------------------------------------------- #

class _Args:
    def __init__(self, list_path):
        self.list = str(list_path)
        self.max_pages = 10
        self.crawlers = 4
        self.slots_per_box = 4
        self.local_only = True
        self.digest = False


def _seed(pm, tmp_path, urls):
    """Point pipeline_manager's whole runtime footprint at tmp_path."""
    listing = tmp_path / "docslist"
    listing.write_text("\n".join(urls) + "\n")
    for attr, value in (("HUB_DIR", tmp_path),
                        ("STATE_PATH", tmp_path / "pipeline_queue.json"),
                        ("LOCK_PATH", tmp_path / "pipeline_queue.lock"),
                        ("WRITE_LOCK_PATH", tmp_path / "pipeline_queue.flock")):
        setattr(pm, attr, value)
    return listing


def test_slow_item_does_not_block_the_rest_of_the_queue(pm, monkeypatch, tmp_path):
    """The retired loop submitted a batch then waited for ALL of it before
    re-reading state, so one long item left every other slot idle. Here a
    slow item must not delay the fast ones.
    """
    urls = ["https://slow.example/", "https://a.example/",
            "https://b.example/", "https://c.example/"]
    listing = _seed(pm, tmp_path, urls)
    release_slow = threading.Event()
    finished: list[str] = []

    def fake_process_item(url, state, pool, crawl_sem, max_pages, boxes=None):
        if "slow" in url:
            release_slow.wait(timeout=10)
        finished.append(url)
        pm.update_item(state, url, status="done")

    monkeypatch.setattr(pm, "process_item", fake_process_item)
    monkeypatch.setattr(pm, "HostPool", lambda: type(
        "P", (), {"hosts": [("http://h", 1)], "acquire": lambda s: "http://h",
                  "release": lambda s, h: None, "bench": lambda s, h: None})())
    monkeypatch.setattr(pm, "cmd_status", lambda args: 0)
    monkeypatch.setattr(pm, "_replicate_docsets", lambda: None)  # no ssh in tests

    done = threading.Event()
    threading.Thread(target=lambda: (pm.cmd_run(_Args(listing)), done.set()),
                     daemon=True).start()

    deadline = time.time() + 10
    while time.time() < deadline and len(finished) < 3:
        time.sleep(0.05)
    assert sorted(finished) == sorted(urls[1:]), \
        "fast items must finish while the slow one is still running"

    release_slow.set()
    assert done.wait(timeout=10)
    assert len(finished) == 4


def test_item_added_mid_run_is_picked_up(pm, monkeypatch, tmp_path):
    """The seed list is re-read every pass, so a URL queued from the TUI while
    the manager is running starts without waiting for a batch to drain."""
    listing = _seed(pm, tmp_path, ["https://first.example/"])
    hold = threading.Event()
    finished: list[str] = []

    def fake_process_item(url, state, pool, crawl_sem, max_pages, boxes=None):
        if "first" in url:
            hold.wait(timeout=10)
        finished.append(url)
        pm.update_item(state, url, status="done")

    monkeypatch.setattr(pm, "process_item", fake_process_item)
    monkeypatch.setattr(pm, "HostPool", lambda: type(
        "P", (), {"hosts": [("http://h", 1)], "acquire": lambda s: "http://h",
                  "release": lambda s, h: None, "bench": lambda s, h: None})())
    monkeypatch.setattr(pm, "cmd_status", lambda args: 0)
    monkeypatch.setattr(pm, "_replicate_docsets", lambda: None)  # no ssh in tests

    done = threading.Event()
    threading.Thread(target=lambda: (pm.cmd_run(_Args(listing)), done.set()),
                     daemon=True).start()
    time.sleep(0.3)
    listing.write_text("https://first.example/\nhttps://late.example/\n")

    deadline = time.time() + 10
    while time.time() < deadline and "https://late.example/" not in finished:
        time.sleep(0.05)
    assert "https://late.example/" in finished
    hold.set()
    assert done.wait(timeout=10)


def test_queue_run_replicates_docsets_when_it_drains(pm, monkeypatch, tmp_path):
    """The index stage only ever runs on this box, so the other boxes' docset
    copies go stale the moment anything is indexed. Syncthing used to carry
    that; a drained queue must now push it explicitly."""
    listing = _seed(pm, tmp_path, ["https://only.example/"])
    calls = []

    def fake_process_item(url, state, pool, crawl_sem, max_pages, boxes=None):
        pm.update_item(state, url, status="done")

    monkeypatch.setattr(pm, "process_item", fake_process_item)
    monkeypatch.setattr(pm, "HostPool", lambda: type(
        "P", (), {"hosts": [("http://h", 1)], "acquire": lambda s: "http://h",
                  "release": lambda s, h: None, "bench": lambda s, h: None})())
    monkeypatch.setattr(pm, "cmd_status", lambda args: 0)
    monkeypatch.setattr(pm, "_replicate_docsets", lambda: calls.append("pushed"))

    pm.cmd_run(_Args(listing))
    assert calls == ["pushed"]


def test_replication_failure_does_not_fail_the_run(pm, monkeypatch, tmp_path):
    """A box being off must not turn a completed queue run into a failure."""
    listing = _seed(pm, tmp_path, ["https://only.example/"])

    def boom():
        raise OSError("box is off")

    monkeypatch.setattr(pm, "process_item",
                        lambda url, state, *a, **k: pm.update_item(state, url, status="done"))
    monkeypatch.setattr(pm, "HostPool", lambda: type(
        "P", (), {"hosts": [("http://h", 1)], "acquire": lambda s: "http://h",
                  "release": lambda s, h: None, "bench": lambda s, h: None})())
    monkeypatch.setattr(pm, "cmd_status", lambda args: 0)
    import replicate_docsets
    monkeypatch.setattr(replicate_docsets, "main", lambda argv: boom())

    assert pm.cmd_run(_Args(listing)) == 0


# --------------------------------------------------------------------------- #
# refine budget scales with the crawl
# --------------------------------------------------------------------------- #

def _mirror_with_pages(pm, n):
    out = pm.MIRROR_OUT_DIR / "sized.md"
    out.write_text("".join(f"URL: https://x/{i}\nbody\n" for i in range(n)))
    return out


def test_small_docset_keeps_the_flat_default(pm):
    mirror = _mirror_with_pages(pm, 50)
    assert pm.refine_timeout_for(mirror) == pm.STAGE_TIMEOUT["refine"]


def test_large_docset_gets_more_time(pm):
    """A flat 90 minutes killed every big docset mid-distill after the salvage
    grew several mirrors 2-3x (mongodb.com 5067 -> 13613 pages)."""
    mirror = _mirror_with_pages(pm, 1000)
    budget = pm.refine_timeout_for(mirror)
    assert budget > pm.STAGE_TIMEOUT["refine"]
    assert budget == int(1000 * pm.SECONDS_PER_PAGE)
    # and the biggest salvaged mirror lands on the cap, not on 150 hours
    assert pm.refine_timeout_for(_mirror_with_pages(pm, 13613)) == pm.REFINE_TIMEOUT_CAP


def test_budget_is_capped(pm):
    mirror = _mirror_with_pages(pm, 10_000_000)
    assert pm.refine_timeout_for(mirror) == pm.REFINE_TIMEOUT_CAP


def test_missing_mirror_still_gets_the_default(pm):
    assert pm.refine_timeout_for(pm.MIRROR_OUT_DIR / "nope.md") == \
        pm.STAGE_TIMEOUT["refine"]
