"""queue_model.py — read/mutate the pipeline queue and control the manager.

Speaks the same on-disk schema as scripts/pipeline_manager.py
(pipeline_queue.json + pipeline_queue.lock + docslist.textmirror), so the TUI
and the CLI manager stay interchangeable. Mutations are atomic-rename writes,
matching the manager's own save path.
"""

from __future__ import annotations

import contextlib
import datetime
import json
import os
import signal
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from . import core  # noqa: F401  (also puts scripts/ on sys.path)
import pipeline_manager as _pm  # shared schema: new_item, state_write_lock, STAGES

STAGES = _pm.STAGES


class QueueStateError(RuntimeError):
    """pipeline_queue.json is unreadable; mutation refused to avoid wiping it."""


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


@dataclass
class QueueItem:
    url: str
    status: str = "pending"
    stage_done: list[str] = field(default_factory=list)
    attempts: int = 0
    error: str = ""
    updated: str = ""
    mirror: str = ""
    boxes_used: list[str] = field(default_factory=list)

    @property
    def stages(self) -> str:
        return ",".join(self.stage_done) or "-"

    @property
    def remaining_stages(self) -> list[str]:
        return [s for s in STAGES if s not in self.stage_done]


def load_items() -> list[QueueItem]:
    if not core.QUEUE_STATE.exists():
        return []
    try:
        raw = json.loads(core.QUEUE_STATE.read_text())
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(raw, dict) or not isinstance(raw.get("items"), dict):
        return []  # wrong-shaped file must not crash the 3s refresh loop
    items = []
    for url, it in raw.get("items", {}).items():
        items.append(QueueItem(
            url=url,
            status=it.get("status", "?"),
            stage_done=list(it.get("stage_done", [])),
            attempts=it.get("attempts", 0),
            error=it.get("error", ""),
            updated=it.get("updated", ""),
            mirror=it.get("mirror", ""),
            boxes_used=list(it.get("boxes_used", [])),
        ))
    return items


def summary(items: list[QueueItem] | None = None) -> dict[str, int]:
    items = load_items() if items is None else items
    counts: dict[str, int] = {}
    for it in items:
        counts[it.status] = counts.get(it.status, 0) + 1
    return counts


def summary_line(counts: dict[str, int]) -> str:
    """One canonical rendering of the status counts (shared by TUI + health)."""
    return " ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "queue empty"


def stage_progress(item: QueueItem, activity: list[dict] | None = None) -> tuple[str, str]:
    """(current step, remaining note) for one queue item, for the Queue tab's
    "step"/"left" columns. When the item is mid-mirror and `activity` (from
    extension_activity()) has a live crawl for its host, the note reports
    real crawled/queued counts instead of just a stage tally."""
    remaining = item.remaining_stages
    if item.status == "done":
        return "done", "-"
    if item.status == "pending":
        return "queued", f"{len(STAGES)}/{len(STAGES)} left"
    cur = remaining[0] if remaining else STAGES[-1]
    note = f"{len(remaining)}/{len(STAGES)} left"
    if item.status == "failed":
        note += " (failed)"
    elif cur == "mirror" and activity:
        from urllib.parse import urlparse
        host = urlparse(item.url).hostname or ""
        for act in activity:
            if host and (act["host"] in host or host in act["host"]):
                note = f"{act['crawled']}p crawled, {act['queued']} queued"
                break
    return cur, note


def machines_for(item: QueueItem) -> str:
    """Which boxes have contributed to this item.

    Read straight off the queue entry: pipeline_manager records each box as
    it starts a stage there. The previous version inferred it from shard
    files left on disk, which only worked while a single crawl was split
    across boxes and Syncthing replicated the pieces back -- neither is true
    now that whole items are placed on one box and results return by rsync.
    Still a pure local read, no ssh per row per refresh."""
    if item.status not in ("running", "done"):
        return "-"
    return ", ".join(item.boxes_used) if item.boxes_used else "local"


def _fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def _fmt_secs(secs: float) -> str:
    secs = max(0, secs)
    if secs < 60:
        return f"{secs:.0f}s"
    if secs < 3600:
        return f"{secs / 60:.0f}m"
    return f"{secs / 3600:.1f}h"


def build_item_report(item: QueueItem) -> str:
    """Full per-item report for the Queue tab's row-expand view: stage
    checklist, on-disk artifact evidence, and a time budget/estimate for
    whichever stage is in flight. Pure-local so it's safe to call from a
    background worker thread without touching the network (box/Ollama health
    is layered on separately by the caller)."""
    lines = [f"[b]{item.url}[/b]", f"status: {item.status}  ·  attempts: {item.attempts}"]
    try:
        updated_ts = datetime.datetime.fromisoformat(item.updated).timestamp()
        lines.append(f"last updated: {item.updated} ({core.age_str(updated_ts)})")
    except (ValueError, TypeError):
        lines.append(f"last updated: {item.updated or '-'}")
    if item.error:
        lines.append(f"[red]last error:[/red] {item.error}")

    lines.append("")
    lines.append("[b]Stages[/b]")
    done = set(item.stage_done)
    cur_step, cur_left = stage_progress(item)
    for stage in STAGES:
        if stage in done:
            lines.append(f"  [green]✓[/green] {stage} — done")
        elif stage == cur_step:
            lines.append(f"  [yellow]▶[/yellow] {stage} — running ({cur_left})")
        else:
            lines.append(f"  · {stage} — pending")

    lines.append("")
    lines.append(f"[b]Machines[/b]: {machines_for(item)}")

    mirror = _pm.mirror_path_for(item.url)
    clean = mirror.parent / f"{mirror.stem}.clean.md"
    ref_dir = mirror.parent / f"{mirror.stem}.reference"
    summary = ref_dir / "summary.json"

    artifacts = [("mirror", mirror), ("clean mirror", clean), ("reference", ref_dir),
                 ("summary", summary)]
    if any(path.exists() for _, path in artifacts):
        lines.append("")
        lines.append("[b]Artifacts[/b] (local disk; a remote stage rsyncs its "
                     "results back here)")
        for label, path in artifacts:
            if not path.exists():
                lines.append(f"  {label}: [dim]not yet[/dim]")
            elif path.is_dir():
                n = sum(1 for p in path.iterdir() if not p.name.startswith("._"))
                lines.append(f"  {label}: {n} file(s), "
                             f"{core.age_str(path.stat().st_mtime)}")
            else:
                st = path.stat()
                lines.append(f"  {label}: {_fmt_bytes(st.st_size)}, "
                             f"{core.age_str(st.st_mtime)}")

    if cur_step == "mirror":
        cap = _pm.max_pages_for(item.url, 5000)
        fetched = _pm._count_mirror_pages(mirror) if mirror.exists() else 0
        lines.append("")
        lines.append(f"[b]Mirror progress[/b]: {fetched}/{cap} pages")

    if cur_step == "refine":
        lines.append("")
        lines.append(f"[b]Refine budget[/b]: {_fmt_secs(_pm.refine_timeout_for(mirror))}"
                     f" (page-count scaled, floor "
                     f"{_fmt_secs(_pm.STAGE_TIMEOUT['refine'])})")
        state = ref_dir / "units.state.json"
        if state.exists():
            try:
                with open(state) as f:
                    st = json.load(f)
                done = sum(1 for v in st.values() if v.get("ok"))
                failed = sum(1 for v in st.values() if not v.get("ok"))
            except (OSError, ValueError, json.JSONDecodeError):
                lines.append("  LLM pass: state unreadable")
            else:
                lines.append(f"  LLM pass: {done} page(s) done, {failed} failed")
    if summary.exists():
        try:
            with open(summary) as f:
                sm = json.load(f)
        except (OSError, ValueError, json.JSONDecodeError):
            lines.append("  summary unreadable")
        else:
            by = sm.get("units_by_origin", {})
            lines.append("")
            lines.append(f"[b]Fact layer[/b]: {sm.get('units', 0)} units — "
                         + ", ".join(f"{k} {v}" for k, v in sorted(by.items()))
                         + (f" (~{_fmt_secs(sm.get('units', 0) * _pm.SECONDS_PER_UNIT)}"
                            f" to embed)" if cur_step == "index" else ""))

    return "\n".join(lines)


@contextlib.contextmanager
def _write_lock():
    """Cross-process flock guarding pipeline_queue.json read-modify-write.
    Same file pipeline_manager.state_write_lock uses in production; derived
    from core.QUEUE_STATE so tests lock inside their tmp dir."""
    lock_path = core.QUEUE_STATE.with_suffix(".flock")
    with lock_path.open("a") as fh:
        import fcntl
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def _mutate(fn, seed_edit=None) -> None:
    """Load raw state, apply fn(raw), write back atomically under the
    cross-process lock; seed_edit (if given) runs inside the same lock so
    docslist edits can't interleave with a starting manager. Refuses to
    proceed when the existing state file is corrupt or wrong-shaped —
    overwriting it would silently wipe the whole queue."""
    with _write_lock():
        raw = {"items": {}}
        if core.QUEUE_STATE.exists():
            try:
                raw = json.loads(core.QUEUE_STATE.read_text())
            except (OSError, json.JSONDecodeError) as exc:
                raise QueueStateError(
                    f"refusing to overwrite unreadable {core.QUEUE_STATE}: {exc}"
                ) from exc
            if not isinstance(raw, dict) or not isinstance(raw.get("items"), dict):
                raise QueueStateError(
                    f"refusing to overwrite wrong-shaped {core.QUEUE_STATE} "
                    "(expected an object with an 'items' object)")
        fn(raw)
        fd, tmp = tempfile.mkstemp(dir=str(core.QUEUE_STATE.parent),
                                   suffix=".queue.tmp")
        try:
            with os.fdopen(fd, "w") as fh:
                json.dump(raw, fh, indent=2)
            os.replace(tmp, core.QUEUE_STATE)
        except OSError:
            with contextlib.suppress(OSError):
                os.unlink(tmp)
            raise
        if seed_edit is not None:
            seed_edit()


def _write_seed_list(lines: list[str]) -> None:
    """Atomic docslist rewrite (plain write_text could be read truncated)."""
    fd, tmp = tempfile.mkstemp(dir=str(core.DOCS_LIST.parent),
                               suffix=".seeds.tmp")
    with os.fdopen(fd, "w") as fh:
        fh.write("\n".join(lines) + ("\n" if lines else ""))
    os.replace(tmp, core.DOCS_LIST)


def add_urls(urls: list[str]) -> int:
    """Queue new docset URLs: state entry + docslist line (the manager's `run`
    only processes URLs present in the seed list, so both must be updated).
    Raises ValueError for non-http(s) input — queue entries become positional
    argv to the stage tools, so option-shaped tokens must never enter."""
    urls = [u.strip() for u in urls if u.strip()]
    if not urls:
        return 0
    bad = [u for u in urls if not _pm.valid_seed_url(u)]
    if bad:
        raise ValueError(f"not http(s)://host/... URLs: {', '.join(bad)}")

    def apply(raw: dict) -> None:
        for url in urls:
            raw["items"].setdefault(url, {**_pm.new_item(), "updated": _now()})

    def seed_append() -> None:
        existing = []
        if core.DOCS_LIST.exists():
            existing = [ln.strip() for ln in
                        core.DOCS_LIST.read_text().splitlines() if ln.strip()]
        merged = existing + [u for u in urls if u not in set(existing)]
        _write_seed_list(merged)

    _mutate(apply, seed_edit=seed_append)
    return len(urls)


def retry(urls: list[str] | None = None) -> int:
    """Requeue failed items (all failed when urls is None)."""
    count = 0

    def apply(raw: dict) -> None:
        nonlocal count
        for url, it in raw["items"].items():
            # explicit selection may rerun any state; blanket retry only failed
            requeue = it.get("status") == "failed" if urls is None else url in urls
            if requeue:
                it.update(status="pending", attempts=0, error="", updated=_now())
                count += 1
    _mutate(apply)
    return count


def remove(url: str) -> bool:
    removed = False

    def apply(raw: dict) -> None:
        nonlocal removed
        removed = raw["items"].pop(url, None) is not None

    def seed_drop() -> None:
        if core.DOCS_LIST.exists():
            lines = [ln for ln in core.DOCS_LIST.read_text().splitlines()
                     if ln.strip() != url]
            _write_seed_list(lines)

    _mutate(apply, seed_edit=seed_drop)
    return removed


def recrawl(urls: list[str] | None = None) -> int:
    """Reset items for a FULL second round — clears every completed stage so
    mirror/distill/index all rerun (the crawler is resumable, so a higher
    max-pages setting extends the existing mirror instead of restarting it).
    urls=None resets every `done` item."""
    count = 0

    def apply(raw: dict) -> None:
        nonlocal count
        for url, it in raw["items"].items():
            # blanket 2nd round targets done items; explicit picks any state
            hit = it.get("status") == "done" if urls is None else url in urls
            if hit:
                it.update(status="pending", stage_done=[], attempts=0,
                          error="", updated=_now())
                count += 1
    _mutate(apply)
    return count


# --------------------------------------------------------------------------- #
# chrome-extension / crawler live activity
# --------------------------------------------------------------------------- #

def serve_alive(timeout: float = 1.0) -> bool:
    """Is the web-text-mirror --serve API (Chrome extension backend) up?"""
    try:
        urllib.request.urlopen(
            f"http://127.0.0.1:{core.EXT_API_PORT}/", timeout=timeout)
        return True
    except urllib.error.HTTPError:
        return True  # any HTTP response (404 on /) means a live listener
    except OSError:
        return False


def extension_activity(window_secs: int = 900) -> list[dict]:
    """Crawls active in the last `window_secs`, from the per-host
    *_state.json files the crawler/extension server maintains. Covers both
    CLI crawls and Chrome-extension /save-/crawl-driven pulls."""
    rows: list[dict] = []
    now = time.time()
    seen: set[str] = set()
    for d in (core.MIRROR_OUT_DIR, core.MIRROR_SKILL_DIR / "text-mirror"):
        if not d.is_dir():
            continue
        for sf in d.glob("*_state.json"):
            host = sf.name.removesuffix("_state.json")
            if host in seen:
                continue
            try:
                mtime = sf.stat().st_mtime
                if now - mtime > window_secs:
                    continue
                raw = json.loads(sf.read_text())
                rows.append({"host": host,
                             "crawled": len(raw.get("crawled", {})),
                             "queued": len(raw.get("queue", [])),
                             "updated": mtime})
                seen.add(host)
            except (OSError, json.JSONDecodeError):
                continue
    rows.sort(key=lambda r: -r["updated"])
    return rows


# --------------------------------------------------------------------------- #
# manager process control
# --------------------------------------------------------------------------- #

def manager_pid() -> int | None:
    """PID of a live pipeline manager, from its lock file."""
    try:
        pid = core.QUEUE_LOCK.read_text().strip()
    except OSError:  # vanished between checks (manager just exited) or unreadable
        return None
    return int(pid) if pid.isdigit() and core.pid_alive(pid) else None


def start_manager(max_pages: int = 300, crawlers: int = 3,
                  env: dict | None = None, local_only: bool = True) -> int | str:
    """Spawn `pipeline_manager.py run` detached, logging to PIPELINE_LOG.
    `env` carries overrides (e.g. settings.stage_env() — the manager is the
    main consumer of HUB_OLLAMA_URLS). Returns the new PID or an error
    string.

    stdin is /dev/null on purpose: the manager inherits the TUI's tty
    otherwise, and once that terminal closes every stage subprocess it
    spawns dies at startup with `init_sys_streams: can't initialize sys
    standard streams` (seen 2026-08-30 — 11 items failed 3/3 that way)."""
    pid = manager_pid()
    if pid:
        return f"already running (pid {pid})"
    argv = [core.python_for_hub(), str(core.PIPELINE_SCRIPT), "run",
            "--max-pages", str(max_pages), "--crawlers", str(crawlers)]
    if local_only:
        argv.append("--local-only")
    try:
        with core.PIPELINE_LOG.open("a") as log:  # child dups the fd; parent's closes
            log.write(f"\n===== hub-manager start {_now()} =====\n")
            log.flush()
            proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=log,
                                    stderr=subprocess.STDOUT, start_new_session=True,
                                    env={**os.environ, **(env or {})})
    except OSError as exc:
        return f"spawn failed: {exc}"
    return proc.pid


def stop_manager() -> str:
    pid = manager_pid()
    if not pid:
        return "not running"
    try:
        # killpg only when the manager leads its own group (TUI-spawned via
        # start_new_session ⇒ pgid == pid); an externally launched manager may
        # share a group with unrelated processes.
        if os.getpgid(pid) == pid:
            os.killpg(pid, signal.SIGTERM)
        else:
            os.kill(pid, signal.SIGTERM)
    except OSError:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError as exc:
            return f"failed: {exc}"
    return f"sent SIGTERM to pid {pid}"
