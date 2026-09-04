#!/usr/bin/env python3
"""pipeline_manager.py — work queue + router for the docs-to-skill pipeline.

Takes a list of docset seed URLs (one per line, e.g.
~/.global-ai-hub/docslist.textmirror) and runs the full pipeline on each:

    mirror (web-text-mirror crawl, or the site's llms-full.txt / llms.txt)
      ->  refine (docset_refine: clean, triage, snippets/tables/definitions,
                  LLM units for prose on the local Ollama pool, reference.md)
      ->  index  (docset_indexer -> raw layer from <stem>.clean.md and the
                  <key>__facts layer from <stem>.reference/all_units.jsonl)

The manager owns waiting, queuing, restarts, retries, and work distribution:

- Work is placed at ITEM granularity (BoxPool): a box runs the mirror stage
  for a whole URL, then rsyncs its artifacts back here over the same ssh used
  to dispatch it. Nothing rides on file-sync propagation.
- refine and index always run here: refine's LLM pass needs the fast local
  model (HUB_REFINE_LLM_URLS, default this box) and .chroma-docsets has
  exactly one writer by design, and that writer is this box.
- Embedding calls inside refine/index are separately routed to whichever box
  in the HUB_OLLAMA_URLS pool has a free slot (slots = the host's weight).
- Hosts and boxes are probed before assignment; a failing one is benched for
  60s and its work goes elsewhere.
- Crawls are network-bound — they also run under a global politeness
  semaphore (default 3 concurrent crawls).
- Every stage is resumable (the crawler keeps queue state, refine keeps
  per-page state under <stem>.reference/, indexing is idempotent). State lives in
  ~/.global-ai-hub/pipeline_queue.json: killing and rerunning the manager
  continues where it stopped; items failed 3x stay `failed` until
  `retry-failed`.

CLI:
  pipeline_manager.py run    [--list FILE] [--max-pages N] [--crawlers N]
                             [--slots-per-box N] [--local-only]
  pipeline_manager.py status
  pipeline_manager.py add URL...
  pipeline_manager.py retry-failed

Repo-index pipeline (hub-daemon file index + napmem usage predictor):
  pipeline_manager.py repo-status              health, counts, predictor state
  pipeline_manager.py index-repo PATH [--max N]  index a repo now via daemon
  pipeline_manager.py watch-repo PATH          add repo to idle-indexer watch list
Env: HUB_OLLAMA_URLS / HUB_EMBED_MODEL (see embed_core), HUB_DIR.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import datetime
import fcntl
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import embed_core  # noqa: E402

HUB_DIR = Path(os.environ.get("HUB_DIR", Path.home() / ".global-ai-hub")).expanduser()
STATE_PATH = HUB_DIR / "pipeline_queue.json"
LOCK_PATH = HUB_DIR / "pipeline_queue.lock"
WRITE_LOCK_PATH = HUB_DIR / "pipeline_queue.flock"
DEFAULT_LIST = HUB_DIR / "docslist.textmirror"

MIRROR_SKILL_DIR = Path.home() / ".claude" / "skills" / "web-text-mirror" / "scripts"
MIRROR_SCRIPT = MIRROR_SKILL_DIR / "text_mirror.py"
MIRROR_OUT_DIR = MIRROR_SKILL_DIR.parent / "text-mirror"
SCRIPTS_DIR = Path(__file__).resolve().parent
INDEXER_SCRIPT = SCRIPTS_DIR / "docset_indexer.py"
VENV_PY = str(HUB_DIR / ".venv" / "bin" / "python")

STAGES = ("mirror", "refine", "index")
STAGE_TIMEOUT = {"mirror": 45 * 60, "refine": 6 * 60 * 60, "index": 90 * 60}
LEGACY_STAGES = {"distill"}  # pre-2026-08-30 items carry this; it maps to nothing

# Where refine's LLM pass generates. Separate from the embedding pool on
# purpose: the 2026-08-30 benchmark put the M5 at 103 tok/s on qwen3.5:35b
# while the "GPU box" was running qwen3:8b on CPU (no device visible).
REFINE_LLM_URLS = os.environ.get("HUB_REFINE_LLM_URLS", "http://localhost:11434=1")
REFINE_LLM_MODEL = os.environ.get("HUB_REFINE_LLM_MODEL", "qwen3.5:35b")

# Refining scales with how much was crawled (the LLM pass is per page), so a
# flat timeout is wrong at both ends: generous for a 300-page docset, far too
# short for a big one. The salvage of 2026-08-27 grew several mirrors 2-3x
# (mongodb.com 5067 -> 13613 pages) and every one of them then died on the
# old flat 90-minute distill budget mid-run.
SECONDS_PER_PAGE = 40.0
REFINE_TIMEOUT_CAP = 24 * 60 * 60


def _count_mirror_pages(mirror: Path) -> int:
    """Pages in a mirror file, counted by its per-page URL header."""
    try:
        with mirror.open(errors="ignore") as fh:
            return sum(1 for line in fh if line.startswith("URL: "))
    except OSError:
        return 0


def refine_timeout_for(mirror: Path) -> int:
    """Page-count-scaled refine budget, floored at the flat default."""
    pages = _count_mirror_pages(mirror)
    return int(min(REFINE_TIMEOUT_CAP,
                   max(STAGE_TIMEOUT["refine"], pages * SECONDS_PER_PAGE)))
MAX_ATTEMPTS = 3
BENCH_SECONDS = 60

# Per-site page cap overrides for sites whose full docs tree is orders of
# magnitude bigger than everything else (docs.aws.amazon.com: 69k+ pages) --
# at that size the distiller's semantic embedding pass dominates the run
# regardless of timeouts, so cap the crawl instead of the clock.
MAX_PAGES_OVERRIDES = {
    "docs.aws.amazon.com": 800,
}


def max_pages_for(url: str, default: int) -> int:
    for host, cap in MAX_PAGES_OVERRIDES.items():
        if host in url:
            return min(default, cap)
    return default


# Measured: 359 units / 3 hosts in parallel -> 36s (~0.1s/unit). Use a 3x
# safety margin since real docsets contend with other queue items for the
# same hosts, unlike the isolated single-item test that measurement came from.
SECONDS_PER_UNIT = 0.3  # embedding cost per fact-layer unit, for the Queue tab's estimate
_UNIT_COUNT_RE = re.compile(r"Stage 1 Complete: (\d+) exact-unique units")

_state_lock = threading.Lock()


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


# --------------------------------------------------------------------------- #
# state
# --------------------------------------------------------------------------- #

def new_item() -> dict:
    """Canonical initial queue-entry shape — shared with hub_manager's TUI so
    the two writers can't drift on the schema."""
    return {"status": "pending", "stage_done": [], "attempts": 0, "boxes_used": []}


@contextlib.contextmanager
def state_write_lock():
    """OS advisory lock serializing pipeline_queue.json read-modify-write
    across processes (the manager and the hub-manager TUI)."""
    with WRITE_LOCK_PATH.open("a") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def load_state() -> dict:
    if STATE_PATH.exists():
        try:
            raw = json.loads(STATE_PATH.read_text())
            # valid JSON of the wrong shape must not crash every caller
            if isinstance(raw, dict) and isinstance(raw.get("items"), dict):
                return raw
        except (OSError, json.JSONDecodeError):
            pass
    return {"items": {}}


def _write_state(state: dict) -> None:
    """Atomic write via a unique temp file. Caller must hold state_write_lock
    (two writers on one shared tmp path would truncate each other)."""
    fd, tmp = tempfile.mkstemp(dir=str(HUB_DIR), suffix=".queue.tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(state, fh, indent=2)
        os.replace(tmp, STATE_PATH)
    except OSError:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def save_state(state: dict) -> None:
    with state_write_lock():
        _write_state(state)


def update_item(state: dict, url: str, **fields) -> None:
    """Update ONE item on disk: re-read under the lock and merge only this
    URL, so concurrent TUI mutations of other items (add/retry/remove) are
    never reverted by this process's stale in-memory copy."""
    with _state_lock:
        item = state["items"].setdefault(url, {})
        item.update(fields, updated=_now())
        with state_write_lock():
            disk = load_state()
            disk["items"][url] = dict(item)
            _write_state(disk)


# --------------------------------------------------------------------------- #
# host pool router
# --------------------------------------------------------------------------- #

class HostPool:
    """Slot-based router over the weighted Ollama pool. A host's weight is its
    concurrent-job capacity; acquire() hands out the least-loaded healthy host
    and blocks while every box is full."""

    def __init__(self):
        self.hosts = embed_core._parse_hosts()  # [(url, weight)] sorted by weight desc
        if not self.hosts:
            raise SystemExit("no Ollama hosts configured (HUB_OLLAMA_URLS)")
        self.in_use: dict[str, int] = {u: 0 for u, _ in self.hosts}
        self.benched: dict[str, float] = {}
        self.health_ttl: dict[str, float] = {}  # url -> cached-healthy-until
        self.cv = threading.Condition()

    def _healthy(self, url: str) -> bool:
        """Health with a TTL cache: acquire() runs this while holding self.cv,
        so a fresh 5s HTTP probe per host per acquisition would serialize all
        scheduling behind network I/O."""
        now = time.monotonic()
        # Quiet hours are checked per acquisition and ahead of the TTL cache:
        # a manager can run for hours and cross the boundary, and a cached
        # "healthy" must not keep sending embedding traffic to a box whose
        # owner has started their working day.
        if _is_quiet(url):
            return False
        if self.benched.get(url, 0) > now:
            return False
        if self.health_ttl.get(url, 0) > now:
            return True
        try:
            with urllib.request.urlopen(f"{url}/api/tags", timeout=5):
                self.health_ttl[url] = now + 30
                return True
        except OSError:
            self.benched[url] = now + BENCH_SECONDS
            return False

    def acquire(self) -> str:
        with self.cv:
            while True:
                candidates = []
                for url, weight in self.hosts:
                    free = weight - self.in_use[url]
                    if free > 0 and self._healthy(url):
                        candidates.append((free / weight, free, url))
                if candidates:
                    candidates.sort(reverse=True)  # most relative headroom first
                    url = candidates[0][2]
                    self.in_use[url] += 1
                    return url
                # Every host quiet or benched: fall back to a local one rather
                # than block the queue forever waiting for 17:00.
                local = [u for u, _w in self.hosts
                         if ("localhost" in u or "127.0.0.1" in u)
                         and self.in_use[u] < max(1, dict(self.hosts)[u])]
                if local:
                    self.in_use[local[0]] += 1
                    return local[0]
                self.cv.wait(timeout=10)

    def release(self, url: str) -> None:
        with self.cv:
            self.in_use[url] = max(0, self.in_use[url] - 1)
            self.cv.notify_all()

    def bench(self, url: str) -> None:
        with self.cv:
            self.benched[url] = time.monotonic() + BENCH_SECONDS
            self.health_ttl.pop(url, None)  # cached "healthy" no longer trusted
            self.cv.notify_all()


# --------------------------------------------------------------------------- #
# stages
# --------------------------------------------------------------------------- #

def _run_stage(argv: list[str], timeout: int, env: dict | None = None,
               cwd: Path | None = None) -> tuple[bool, str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    try:
        out = subprocess.run(argv, capture_output=True, text=True,
                             timeout=timeout, env=merged, cwd=cwd)
    except subprocess.TimeoutExpired:
        return False, f"timeout after {timeout}s"
    tail = (out.stdout + "\n" + out.stderr)[-2000:]
    return out.returncode == 0, tail


def mirror_path_for(url: str) -> Path:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return MIRROR_OUT_DIR / f"{host}.md"


DIGEST_AFTER_MIRROR = False  # set by cmd_run --digest
# Also write a browsable offline clone (HTML + images/CSS/JS) beside the
# markdown mirror. Env so the hub-manager Settings tab can drive it; the
# remote clone needs no rsync change because the clone dir is <stem>.site,
# which the existing <stem>*/ artifact filters already match.
MIRROR_CLONE = os.environ.get("HUB_MIRROR_CLONE", "").strip().lower() in (
    "1", "true", "yes", "on")


def _semantic_ops():
    """Import the digest module lazily; None when unavailable (optional dep)."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from semantic_ops import digest
        return digest
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# box pool — whole-item work placement across boxes
#
# Work is distributed at ITEM granularity: one box runs the mirror stage for
# a single URL end to end, then rsyncs its artifacts back here.
#
# The previous design sharded ONE crawl's pages across boxes and used Syncthing
# as the return path. That could not work, for two independent reasons:
#   * a BFS crawl's shards must exchange their discovered frontier live (a
#     shard that skips a page never sees that page's links), and the exchange
#     rode on file sync with a 3600s rescan interval; and
#   * the follower boxes are Syncthing `receiveonly` — the single-writer
#     topology that stopped the docset-registry conflict storm (docs/MCP.md) —
#     so a remote shard's output could never travel back here at all.
# Item-level placement needs no frontier exchange, and rsync-over-ssh returns
# results deterministically instead of betting on eventual consistency.
#
# The index stage stays local on purpose: .chroma-docsets has exactly one
# sendreceive writer by design, and that writer is this box.
# --------------------------------------------------------------------------- #

REMOTE_WORK_SUBDIR = ".hub-pipeline-work/text-mirror"
REMOTE_MIRROR_SUBDIR = ".claude/skills/web-text-mirror/scripts"
BOX_PROBE_TIMEOUT = 25
RSYNC_TIMEOUT = 30 * 60


def _local_ips() -> set[str]:
    """Every IP this box answers to, across all interfaces — a box can be
    reachable at several IPs (LAN, VPN, WAN passthrough) and ssh_targets is
    keyed by whichever one happens to be configured, so hostname-resolution
    alone (which only returns one) isn't enough to recognize "this is me"."""
    import socket
    ips = {"127.0.0.1", "localhost"}
    try:
        ips.add(socket.gethostbyname(socket.gethostname()))
    except OSError:
        pass
    try:
        ips.update(info[4][0] for info in socket.getaddrinfo(socket.gethostname(), None))
    except OSError:
        pass
    for argv in (["ifconfig"], ["ip", "-4", "addr"]):
        try:
            out = subprocess.run(argv, capture_output=True, text=True, timeout=5).stdout
        except (OSError, subprocess.TimeoutExpired):
            continue
        ips.update(re.findall(r"inet6?\s+(?:addr:)?([\da-fA-F.:]+)", out))
        break
    return ips


def _is_quiet(host: str) -> bool:
    """Whether a box is off-limits right now. Never fail the pipeline over the
    schedule: an unreadable policy means 'available', the previous behaviour."""
    try:
        import box_schedule
        return box_schedule.is_quiet(host)
    except Exception:  # noqa: BLE001
        return False


def remote_targets() -> list[tuple[str, str]]:
    """(host, user@host) pairs for the OTHER boxes, from hub-manager's
    ssh_targets settings (the same 3-box list embed_core's Ollama pool uses)
    — this machine's own entry is excluded since it works locally."""
    try:
        from hub_manager import settings as hm_settings
    except ImportError:
        return []
    local = _local_ips()
    out = []
    for pair in str(hm_settings.load().get("ssh_targets", "")).split(","):
        if "=" not in pair:
            continue
        host, target = (p.strip() for p in pair.split("=", 1))
        if target and host not in local:
            out.append((host, target))
    return out


_SAFE_LEAF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class UnsafeRemoteName(ValueError):
    """A mirror filename that must not be interpolated into a remote path."""


def safe_leaf(name: str) -> str:
    """Guard every URL-derived filename that reaches a remote command line.

    mirror_path_for() builds names from urlparse().netloc, which can carry a
    port or credentials (`host:8080`). A colon in an rsync path is parsed as a
    host separator, and the older rsync on some boxes cannot use
    --protect-args, so the remote shell sees these names directly. Hostnames
    from real docsets are alnum/dot/hyphen; anything else runs locally instead.
    """
    if not _SAFE_LEAF_RE.match(name):
        raise UnsafeRemoteName(name)
    return name


def _hm_remotes():
    try:
        from hub_manager import remotes as hm_remotes
        return hm_remotes
    except ImportError:
        return None


class Box:
    """One machine that can run pipeline stages.

    `home` is the box's ABSOLUTE home directory, resolved once by the
    capability probe. Every remote path this module builds is absolute for a
    reason: a ~-prefixed path cannot survive shlex.quote (quoting suppresses
    the remote shell's tilde expansion, which is how the old dispatcher ended
    up writing crawls into a literal directory named `~`), and rsync's
    --protect-args likewise blocks remote tilde expansion. Resolving $HOME up
    front lets every later path be quoted safely.
    """

    __slots__ = ("label", "target", "home", "protect_args")

    def __init__(self, label: str, target: str | None, home: str,
                 protect_args: bool = True):
        self.label = label
        self.target = target  # None == this box
        self.home = home
        self.protect_args = protect_args

    @property
    def is_local(self) -> bool:
        return self.target is None

    def work_dir(self) -> str:
        return f"{self.home}/{REMOTE_WORK_SUBDIR}"

    def work_path(self, leaf: str) -> str:
        return f"{self.work_dir()}/{safe_leaf(leaf)}"

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"Box({self.label})"


def probe_box(target: str) -> str | None:
    """The box's absolute $HOME if it can run pipeline work, else None.

    Checks the two things a dispatch actually needs — rsync and the crawler
    — instead of bare ssh reachability, so a box that is up but missing a
    tool is skipped rather than handed work it will fail. (The distiller is
    no longer a remote requirement: refine runs here.)
    """
    hm_remotes = _hm_remotes()
    if hm_remotes is None:
        return None
    cmd = ("command -v rsync >/dev/null && "
           f"test -f \"$HOME/{REMOTE_MIRROR_SUBDIR}/text_mirror.py\" && "
           f"mkdir -p \"$HOME/{REMOTE_WORK_SUBDIR}\" && echo \"$HOME\"")
    ok, out = hm_remotes.run_ssh(target, cmd, timeout=BOX_PROBE_TIMEOUT)
    if not ok or not out.strip():
        return None
    home = out.strip().splitlines()[-1].strip()
    return home if home.startswith("/") else None


def discover_boxes(allow_remote: bool = True) -> list[Box]:
    """This box plus every reachable, capable remote box that is not in its
    quiet hours (see box_schedule: a work laptop is not the hub's to
    saturate during its owner's working day)."""
    boxes = [Box("local", None, str(Path.home()))]
    if not allow_remote:
        return boxes
    hm_remotes = _hm_remotes()
    for host, target in remote_targets():
        if _is_quiet(host):
            print(f"[{_now()}] {host}: quiet hours, not recruiting", flush=True)
            continue
        home = probe_box(target)
        if not home:
            continue
        protect = (hm_remotes.rsync_supports_protect_args(target)
                   if hm_remotes is not None else False)
        boxes.append(Box(host, target, home, protect_args=protect))
    return boxes


class BoxPool:
    """Slot-based router over the boxes, same shape as HostPool but for whole
    items instead of Ollama calls. A box that fails a stage is benched so the
    retry lands somewhere else."""

    def __init__(self, boxes: list[Box], slots: int = 2):
        if not boxes:
            raise SystemExit("no boxes available (not even this one)")
        self.boxes = boxes
        self.slots = max(1, slots)
        self.in_use: dict[str, int] = {b.label: 0 for b in boxes}
        self.benched: dict[str, float] = {}
        self.cv = threading.Condition()

    @property
    def capacity(self) -> int:
        return self.slots * len(self.boxes)

    def acquire(self) -> Box:
        with self.cv:
            while True:
                now = time.monotonic()
                # re-checked per acquisition, not just at discovery: a
                # manager can run for hours and cross a quiet-hours boundary
                free = [b for b in self.boxes
                        if self.in_use[b.label] < self.slots
                        and self.benched.get(b.label, 0) <= now
                        and not (not b.is_local and _is_quiet(b.label))]
                if free:
                    # least-loaded first; ties keep the declared order, which
                    # puts this box first and remotes after it
                    free.sort(key=lambda b: self.in_use[b.label])
                    box = free[0]
                    self.in_use[box.label] += 1
                    return box
                # every box benched at once must not deadlock the queue
                if all(self.benched.get(b.label, 0) > now for b in self.boxes):
                    self.cv.wait(timeout=5)
                else:
                    self.cv.wait(timeout=10)

    def release(self, box: Box) -> None:
        with self.cv:
            self.in_use[box.label] = max(0, self.in_use[box.label] - 1)
            self.cv.notify_all()

    def bench(self, box: Box) -> None:
        with self.cv:
            self.benched[box.label] = time.monotonic() + BENCH_SECONDS
            self.cv.notify_all()


# --------------------------------------------------------------------------- #
# artifact transfer — rsync over the ssh we already use for dispatch
# --------------------------------------------------------------------------- #

def _mirror_artifact_filters(stem: str) -> list[str]:
    """rsync filters pulling back exactly one docset's mirror artifacts:
    <stem>.md, <stem>_state.json, the <stem>.pages/ or .site/ trees, and any
    dot-prefixed sidecar (a leading dot means <stem>* does not match it, so
    it needs its own rule)."""
    return [f"--include={stem}*/", f"--include={stem}*",
            f"--include={stem}*/**", f"--include=.{stem}*", "--exclude=*"]


def pull_artifacts(box: Box, stem: str, dest: Path) -> tuple[bool, str]:
    hm_remotes = _hm_remotes()
    if hm_remotes is None:
        return False, "hub_manager.remotes unavailable"
    dest.mkdir(parents=True, exist_ok=True)
    return hm_remotes.run_rsync(
        [*_mirror_artifact_filters(stem),
         f"{box.target}:{box.work_dir()}/", f"{dest}/"],
        timeout=RSYNC_TIMEOUT, protect_args=box.protect_args)


def push_mirror(box: Box, mirror: Path) -> tuple[bool, str]:
    """Put this box's copy of a mirror on the remote — needed when a later
    remote stage runs on a box other than the one that crawled it."""
    hm_remotes = _hm_remotes()
    if hm_remotes is None:
        return False, "hub_manager.remotes unavailable"
    ok, out = hm_remotes.run_ssh(
        box.target, f"mkdir -p {shlex.quote(box.work_dir())}", timeout=30)
    if not ok:
        return False, f"mkdir failed: {out}"
    return hm_remotes.run_rsync(
        [str(mirror), f"{box.target}:{box.work_path(mirror.name)}"],
        timeout=RSYNC_TIMEOUT, protect_args=box.protect_args)


# --------------------------------------------------------------------------- #
# stages
# --------------------------------------------------------------------------- #

def remote_safe(box: Box, mirror: Path) -> bool:
    """Whether this docset's filenames may be sent to `box` at all. A name the
    remote shell could misread runs here instead of failing the item."""
    try:
        safe_leaf(mirror.name)
        safe_leaf(mirror.stem)
    except UnsafeRemoteName:
        print(f"[{_now()}] {mirror.name}: unsafe remote name, staying local",
              file=sys.stderr, flush=True)
        return False
    return True


def stage_mirror(url: str, max_pages: int, box: Box | None = None) -> tuple[bool, str]:
    out = mirror_path_for(url)
    # Keep the pre-crawl copy so a recrawl can be diffed semantically
    # (semantic_ops.digest.recrawl). Best-effort: never fail a crawl over it.
    digest = _semantic_ops()
    if digest is not None:
        try:
            digest.snapshot_previous(out)
        except OSError:
            pass

    if box is None or box.is_local or not remote_safe(box, out):
        argv = [sys.executable, str(MIRROR_SCRIPT), url, "--out", str(out),
                "--max-pages", str(max_pages)]
        if MIRROR_CLONE:
            argv.append("--clone")
        ok, log = _run_stage(argv, STAGE_TIMEOUT["mirror"], cwd=MIRROR_SKILL_DIR)
    else:
        ok, log = _remote_mirror(url, box, out, max_pages)

    if ok and (not out.exists() or out.stat().st_size < 1000):
        return False, f"mirror produced no usable output at {out}\n{log}"
    if ok and DIGEST_AFTER_MIRROR and digest is not None:
        try:
            path = digest.recrawl(out)
            if path:
                log += f"\n[digest] {path}"
        except Exception as exc:  # digesting must never fail the pipeline
            log += f"\n[digest] skipped: {exc}"
    return ok, log


def _remote_mirror(url: str, box: Box, out: Path, max_pages: int) -> tuple[bool, str]:
    hm_remotes = _hm_remotes()
    if hm_remotes is None:
        return False, "hub_manager.remotes unavailable"
    remote_out = box.work_path(out.name)
    cmd = (f"mkdir -p {shlex.quote(box.work_dir())} && "
           f"cd {shlex.quote(box.home + '/' + REMOTE_MIRROR_SUBDIR)} && "
           f"python3 text_mirror.py {shlex.quote(url)} "
           f"--out {shlex.quote(remote_out)} --max-pages {max_pages}"
           + (" --clone" if MIRROR_CLONE else ""))
    ok, log = hm_remotes.run_ssh(box.target, cmd, timeout=STAGE_TIMEOUT["mirror"])
    if not ok:
        return False, f"[{box.label}] crawl failed: {log[-1500:]}"
    pulled, plog = pull_artifacts(box, out.stem, out.parent)
    if not pulled:
        return False, f"[{box.label}] crawl ok but rsync back failed: {plog[-800:]}"
    return True, f"[{box.label}] {log[-1200:]}\n[rsync] {plog[-400:]}"


def docset_key_for(mirror: Path) -> str:
    """The indexer's key for a mirror, derived the way `index` derives it
    (first page's host + file stem) so the clean mirror and the facts file
    land under the SAME key as the raw mirror would."""
    import docset_indexer
    try:
        with mirror.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if line.startswith("URL: "):
                    return docset_indexer.docset_key([{"url": line[5:].strip()}], str(mirror))
    except OSError:
        pass
    return docset_indexer.docset_key([], str(mirror))


def refine_argv(mirror: Path, polish: bool = False) -> list[str]:
    argv = [VENV_PY, "-m", "docset_refine", "all", str(mirror)]
    if polish:
        argv.append("--polish")
    return argv


def stage_refine(url: str, host: str, box: Box | None = None) -> tuple[bool, str]:
    """Always local: the LLM pass targets REFINE_LLM_URLS (the fast local
    model), embeddings for dedup go to the pool host handed in."""
    mirror = mirror_path_for(url)
    env = {"HUB_OLLAMA_URLS": REFINE_LLM_URLS if REFINE_LLM_URLS else f"{host}=1",
           "HUB_LLM_MODEL": REFINE_LLM_MODEL,
           "PYTHONPATH": str(SCRIPTS_DIR)}
    return _run_stage(refine_argv(mirror), refine_timeout_for(mirror), env=env)


def index_argvs(mirror: Path) -> list[list[str]]:
    """Raw layer from the clean mirror when refine produced one (else the
    raw mirror), then the facts layer from all_units.jsonl when present —
    both pinned to the raw mirror's key so they pair up. Each layer is
    followed by its FTS5 keyword index (no embedding call) so exact-token
    lookups work as soon as the vectors do."""
    key = docset_key_for(mirror)
    clean = mirror.parent / f"{mirror.stem}.clean.md"
    src = clean if clean.exists() and clean.stat().st_size > 0 else mirror
    argvs = [[VENV_PY, str(INDEXER_SCRIPT), "index", str(src), "--name", key],
             [VENV_PY, str(INDEXER_SCRIPT), "keyword-index", key, "--layer", "raw"]]
    units = mirror.parent / f"{mirror.stem}.reference" / "all_units.jsonl"
    if units.exists() and units.stat().st_size > 0:
        argvs.append([VENV_PY, str(INDEXER_SCRIPT), "index", str(units), "--units",
                      "--name", key])
        argvs.append([VENV_PY, str(INDEXER_SCRIPT), "keyword-index", key, "--layer", "facts"])
    return argvs


def stage_index(url: str, host: str) -> tuple[bool, str]:
    """Always local: .chroma-docsets has a single writer (this box), so
    indexing anywhere else would strand the collection there. Raw layer
    first, then the facts layer; the stage fails on either."""
    mirror = mirror_path_for(url)
    env = {"HUB_OLLAMA_URLS": f"{host}=1"}
    logs = []
    for argv in index_argvs(mirror):
        ok, log = _run_stage(argv, STAGE_TIMEOUT["index"], env=env)
        logs.append(log)
        if not ok:
            return False, "\n".join(logs)
    return True, "\n".join(logs)


# --------------------------------------------------------------------------- #
# worker
# --------------------------------------------------------------------------- #

def process_item(url: str, state: dict, pool: HostPool, crawl_sem: threading.Semaphore,
                 max_pages: int, boxes: BoxPool | None = None) -> None:
    item = state["items"][url]
    done = set(item.get("stage_done", []))
    max_pages = max_pages_for(url, max_pages)
    update_item(state, url, status="running", error="")

    done -= LEGACY_STAGES  # a pre-refine item reruns refine, not "distill"
    # Only hold a box while there is box-placeable work left; an item that
    # only needs refining/indexing must not tie up a remote machine to do nothing.
    needs_box = "mirror" not in done
    box = boxes.acquire() if (boxes is not None and needs_box) else None
    # Which boxes actually did the work, recorded as it happens. The Queue
    # tab used to infer this from shard files left on disk; item-level
    # placement leaves no such trace, and a recorded fact beats an inference.
    boxes_used = list(item.get("boxes_used", []))

    def _note_box(label: str) -> None:
        if label not in boxes_used:
            boxes_used.append(label)
            update_item(state, url, boxes_used=list(boxes_used))

    try:
        for stage in STAGES:
            if stage in done:
                continue
            if stage == "mirror":
                with crawl_sem:
                    where = box.label if box else "local"
                    _note_box(where)
                    print(f"[{_now()}] {url}: crawling on {where} (cap {max_pages})",
                          flush=True)
                    ok, log = stage_mirror(url, max_pages, box)
                host = None
                # mirror is the only box-placeable stage — free the machine
                # for the next queue item instead of holding it through
                # refine + index, which run here
                if ok and box is not None and boxes is not None:
                    boxes.release(box)
                    box = None
            else:
                host = pool.acquire()
                try:
                    _note_box("local")
                    print(f"[{_now()}] {url}: {stage} on local (embed {host})",
                          flush=True)
                    ok, log = (stage_refine(url, host, box) if stage == "refine"
                               else stage_index(url, host))
                finally:
                    pool.release(host)
                if not ok and ("unreachable" in log.lower() or "failed" in log.lower()):
                    pool.bench(host)  # give the next attempt a different box

            if not ok:
                if box is not None and not box.is_local:
                    boxes.bench(box)  # retry this item somewhere else
                attempts = item.get("attempts", 0) + 1
                status = "failed" if attempts >= MAX_ATTEMPTS else "pending"
                update_item(state, url, status=status, attempts=attempts,
                            stage_done=sorted(done), error=f"{stage}: {log[-500:]}")
                print(f"[{_now()}] {url}: {stage} FAILED on "
                      f"{box.label if box else 'local'} (attempt {attempts}/{MAX_ATTEMPTS})",
                      file=sys.stderr, flush=True)
                if status == "pending":
                    time.sleep(min(300, 30 * (2 ** (attempts - 1))))  # backoff
                return

            done.add(stage)
            update_item(state, url, stage_done=sorted(done), attempts=0)
    finally:
        if box is not None and boxes is not None:
            boxes.release(box)

    update_item(state, url, status="done", mirror=str(mirror_path_for(url)))
    print(f"[{_now()}] {url}: DONE", flush=True)


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #

def _read_seed_list(path: str) -> list[str]:
    """Seed URLs, filtered through valid_seed_url — a hand-edited docslist
    line must not bypass the argv-injection guard cmd_add/the TUI enforce."""
    try:
        lines = [ln.strip() for ln in Path(path).expanduser().read_text().splitlines()
                 if ln.strip() and not ln.strip().startswith("#")]
    except OSError:
        return []
    return [u for u in lines if valid_seed_url(u)]


def _acquire_run_lock() -> bool:
    """O_CREAT|O_EXCL claim of LOCK_PATH — check-then-write would let two
    racing `run` invocations both pass and double-process the queue."""
    for _ in range(2):  # second try after clearing a stale lock
        try:
            fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w") as fh:
                fh.write(str(os.getpid()))
            return True
        except FileExistsError:
            # Serialize stale-lock cleanup: without this, two racing runs can
            # both see a stale lock, and B's unlink deletes A's fresh lock.
            with state_write_lock():
                try:
                    pid = LOCK_PATH.read_text().strip()
                except OSError:
                    continue
                if pid and _pid_alive(pid):
                    print(f"ERROR: another manager (pid {pid}) holds {LOCK_PATH}",
                          file=sys.stderr)
                    return False
                with contextlib.suppress(OSError):
                    LOCK_PATH.unlink()  # stale: owner is dead
    return False


def cmd_run(args) -> int:
    if not _acquire_run_lock():
        return 2
    global DIGEST_AFTER_MIRROR, MIRROR_CLONE
    DIGEST_AFTER_MIRROR = bool(getattr(args, "digest", False))
    if getattr(args, "clone", False):
        MIRROR_CLONE = True
    try:
        with state_write_lock():
            state = load_state()
            urls = _read_seed_list(args.list)
            for url in urls:
                item = state["items"].setdefault(url, new_item())
                if item.get("status") == "running":  # stale from a killed run
                    item["status"] = "pending"
            _write_state(state)

        pool = HostPool()
        boxes = BoxPool(discover_boxes(allow_remote=not getattr(args, "local_only", False)),
                        slots=getattr(args, "slots_per_box", 2))
        crawl_sem = threading.Semaphore(args.crawlers)
        workers = max(args.crawlers, boxes.capacity, sum(w for _, w in pool.hosts)) + 1

        print(f"queue: {len(urls)} items | boxes: "
              f"{', '.join(b.label for b in boxes.boxes)} x{boxes.slots} slots | "
              f"embed hosts: {', '.join(f'{u} x{w}' for u, w in pool.hosts)} | "
              f"crawlers: {args.crawlers} | workers: {workers}", flush=True)

        # Continuous feed, NOT a batch barrier. The previous loop submitted a
        # batch and then waited for ALL of it before re-reading state, so one
        # slow item left every other slot idle and anything requeued or added
        # mid-cycle could not start until the batch drained. Here a slot is
        # refilled the moment any single item finishes.
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            inflight: dict[concurrent.futures.Future, str] = {}
            claimed_mirrors: dict[str, Path] = {}
            while True:
                urls = _read_seed_list(args.list) or urls
                state = load_state()
                # A URL appended to the seed list mid-run (by hand, or by any
                # writer that does not also touch the queue file) has no state
                # entry yet, so scanning state alone would never see it.
                fresh = [u for u in urls if u not in state["items"]]
                if fresh:
                    with state_write_lock():
                        disk = load_state()
                        for u in fresh:
                            disk["items"].setdefault(u, new_item())
                        _write_state(disk)
                    state = load_state()
                running = set(inflight.values())
                for u, it in state["items"].items():
                    if len(inflight) >= workers - 1:
                        break
                    if u not in urls or it.get("status") != "pending" or u in running:
                        continue
                    # two seeds can collapse to one mirror file (www./case
                    # variants) — running both concurrently would have two
                    # crawlers writing the same --out file
                    mirror = mirror_path_for(u)
                    if mirror in claimed_mirrors.values():
                        continue  # picked up once the holder finishes
                    claimed_mirrors[u] = mirror
                    fut = ex.submit(process_item, u, state, pool, crawl_sem,
                                    args.max_pages, boxes)
                    inflight[fut] = u
                    running.add(u)
                if not inflight:
                    break
                done, _ = concurrent.futures.wait(
                    inflight, timeout=5,
                    return_when=concurrent.futures.FIRST_COMPLETED)
                for fut in done:
                    url = inflight.pop(fut)
                    claimed_mirrors.pop(url, None)
                    exc = fut.exception()
                    if exc is not None:  # crash would leave the item "running"
                        print(f"[{_now()}] {url}: worker crashed: {exc}",
                              file=sys.stderr, flush=True)
                        update_item(state, url, status="failed",
                                    error=f"worker crashed: {exc}")
        _replicate_docsets()
        _refresh_snapshot()
        return cmd_status(args)
    finally:
        try:
            LOCK_PATH.unlink()
        except OSError:
            pass


def _replicate_docsets() -> None:
    """Push the docset store to the other boxes once the queue drains.

    The index stage only ever runs here, so the followers' copies go stale the
    moment anything is indexed. Syncthing used to carry this; it was removed
    (docs/MCP.md), and a one-way push from the single writer is both faster and
    incapable of the last-write-wins conflicts that once zeroed the registry.
    Best-effort: a queue run must not fail because a box is off.
    """
    try:
        import replicate_docsets
    except ImportError as exc:
        print(f"[{_now()}] docset replication unavailable: {exc}",
              file=sys.stderr, flush=True)
        return
    try:
        print(f"[{_now()}] replicating docsets to other boxes", flush=True)
        replicate_docsets.main(["push"])
    except Exception as exc:  # noqa: BLE001 — never fail a run over replication
        print(f"[{_now()}] docset replication failed: {exc}",
              file=sys.stderr, flush=True)


SNAPSHOT_REFRESH = Path(os.environ.get("LLMS_EXPLORER_DIR", Path.home() / "dev" / "llms-explorer")) / \
    "scripts" / "refresh_snapshot.sh"


def _refresh_snapshot() -> None:
    """Refresh the llms-explorer snapshot repo once the queue drains (new
    exports, facts, mirrors). The script lives in that repo and pushes;
    launchd `com.llms-explorer.snapshot-refresh` runs it daily as well.
    Best-effort, like replication: a queue run never fails over it."""
    if os.environ.get("LLMS_EXPLORER_REFRESH", "1") == "0" or not SNAPSHOT_REFRESH.is_file():
        return  # opt-out (the test suite sets it) or no snapshot repo on this box
    try:
        print(f"[{_now()}] refreshing llms-explorer snapshot", flush=True)
        subprocess.run(["/bin/sh", str(SNAPSHOT_REFRESH)], check=False, timeout=1800,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as exc:  # noqa: BLE001
        print(f"[{_now()}] snapshot refresh failed: {exc}", file=sys.stderr, flush=True)


def _pid_alive(pid: str) -> bool:
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False


def cmd_status(args) -> int:
    state = load_state()
    counts: dict[str, int] = {}
    for url, it in sorted(state["items"].items()):
        st = it.get("status", "?")
        counts[st] = counts.get(st, 0) + 1
        stages = ",".join(it.get("stage_done", [])) or "-"
        err = (" | " + it["error"][:80]) if it.get("error") else ""
        print(f"{st:8} [{stages:20}] {url}{err}")
    print("---")
    print(" ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "queue empty")
    return 0


def valid_seed_url(url: str) -> bool:
    """Only http(s) URLs with a host: queue entries become positional argv to
    the stage tools, so a '-'-prefixed token would inject options, and an
    empty host collapses mirror_path_for() to a bare '.md'."""
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def cmd_add(args) -> int:
    good = [u for u in args.urls if valid_seed_url(u)]
    for bad in set(args.urls) - set(good):
        print(f"skipping invalid URL (need http(s)://host/...): {bad}",
              file=sys.stderr)
    if not good:
        return 1
    with state_write_lock():
        state = load_state()
        for url in good:
            state["items"].setdefault(url, new_item())
        _write_state(state)
        # `run` only processes URLs present in the seed list — keep it in
        # sync, inside the lock so a concurrent TUI seed rewrite can't
        # clobber the append.
        existing = set(_read_seed_list(str(DEFAULT_LIST)))
        with DEFAULT_LIST.open("a") as fh:
            for url in good:
                if url not in existing:
                    fh.write(url + "\n")
    print(f"queued {len(good)} item(s)")
    return 0


def cmd_retry_failed(args) -> int:
    n = 0
    with state_write_lock():
        state = load_state()
        for it in state["items"].values():
            if it.get("status") == "failed":
                it.update(status="pending", attempts=0, error="")
                n += 1
        _write_state(state)
    print(f"requeued {n} failed item(s)")
    return 0


# ---------------------------------------------------------------------------
# Repo-index pipeline (hub-daemon file index + napmem usage predictor).
# View/manage surface for the always-on repo indexing loop: the hub-daemon
# indexes files POSTed by editor/session hooks, the napmem usage predictor
# submits what usage patterns say is likely needed next, and the daemon's
# idle thread sweeps watch_dirs.txt. These commands only observe and enqueue —
# the daemon owns all indexing work.
# ---------------------------------------------------------------------------

DAEMON_URL = "http://127.0.0.1:8000"
WATCH_DIRS_FILE = HUB_DIR / "watch_dirs.txt"
PREDICTOR_STATE = HUB_DIR / "predictor_state.json"
SPILLOVER = Path(os.path.expanduser("~/.napmem/cache/hub-index-spill.jsonl"))


def _daemon_call(endpoint: str, payload: dict | None = None, timeout: float = 10.0):
    req = urllib.request.Request(
        DAEMON_URL + endpoint,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json"},
        method="POST" if payload is not None else "GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def cmd_repo_status(args) -> int:
    print("=== repo-index pipeline ===")
    try:
        health = _daemon_call("/health", timeout=5)
        print(f"daemon    : UP  files={health.get('files')} "
              f"embeddings={health.get('embeddings')} model={health.get('model')} "
              f"uptime={health.get('uptime_s')}s")
    except Exception as exc:
        print(f"daemon    : DOWN ({exc}) — launchd job com.global-ai.hub-daemon")

    if WATCH_DIRS_FILE.exists():
        dirs = [l.strip() for l in WATCH_DIRS_FILE.read_text().splitlines() if l.strip()]
        print(f"watch dirs: {len(dirs)}")
        for d in dirs:
            print(f"  - {d}")
    else:
        print("watch dirs: (none)")

    if PREDICTOR_STATE.exists():
        try:
            ps = json.loads(PREDICTOR_STATE.read_text())
            age_min = int((time.time() - ps.get("ts", 0)) / 60)
            print(f"predictor : last run {age_min}m ago, submitted "
                  f"{ps.get('submitted', 0)} file(s), drained "
                  f"{ps.get('spill_drained', 0)} spillover")
            for repo, score in (ps.get("top_repos") or [])[:5]:
                print(f"  hot repo: {score:7.2f}  {repo}")
        except (ValueError, OSError) as exc:
            print(f"predictor : state unreadable ({exc})")
    else:
        print("predictor : never run")

    if SPILLOVER.exists():
        try:
            depth = sum(1 for _ in SPILLOVER.open())
            print(f"spillover : {depth} file(s) queued while daemon was down")
        except OSError:
            pass
    return 0


def cmd_index_repo(args) -> int:
    root = os.path.abspath(os.path.expanduser(args.path))
    if not os.path.isdir(root):
        print(f"not a directory: {root}", file=sys.stderr)
        return 1
    try:
        res = _daemon_call("/index-tree", {"root": root, "max_files": args.max})
    except Exception as exc:
        print(f"daemon unreachable ({exc}); adding to watch list for the idle "
              f"sweep instead", file=sys.stderr)
        return cmd_watch_repo(args)
    print(f"{res.get('status')}: queued {res.get('queued')} of "
          f"{res.get('found')} candidate file(s) under {root}")
    return 0 if res.get("status") == "accepted" else 1


def cmd_watch_repo(args) -> int:
    root = os.path.abspath(os.path.expanduser(args.path))
    if not os.path.isdir(root):
        print(f"not a directory: {root}", file=sys.stderr)
        return 1
    existing = []
    if WATCH_DIRS_FILE.exists():
        existing = [l.strip() for l in WATCH_DIRS_FILE.read_text().splitlines() if l.strip()]
    if root in existing or any(root.startswith(e + os.sep) for e in existing):
        print(f"already watched: {root}")
        return 0
    with WATCH_DIRS_FILE.open("a") as fh:
        fh.write(root + "\n")
    print(f"watching: {root}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Docs-to-skill pipeline queue manager")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="process the queue until empty")
    r.add_argument("--list", default=str(DEFAULT_LIST), help="seed-URL list file")
    r.add_argument("--max-pages", type=int, default=300, help="crawl page cap per docset (default 300)")
    r.add_argument("--crawlers", type=int, default=3, help="concurrent crawls (default 3)")
    r.add_argument("--slots-per-box", type=int, default=2,
                   help="concurrent items per box (default 2)")
    r.add_argument("--local-only", action="store_true",
                   help="do not recruit other boxes; run every stage here")
    r.add_argument("--digest", action="store_true",
                   help="after each recrawl, write a semantic change digest "
                        "to $HUB_DIR/digests (semantic_ops.digest)")
    r.add_argument("--clone", action="store_true",
                   help="also write a browsable offline clone (HTML + images, "
                        "CSS, JS) beside each markdown mirror")
    r.set_defaults(func=cmd_run)

    s = sub.add_parser("status", help="show queue state")
    s.set_defaults(func=cmd_status)

    a = sub.add_parser("add", help="queue more docset URLs")
    a.add_argument("urls", nargs="+")
    a.set_defaults(func=cmd_add)

    rf = sub.add_parser("retry-failed", help="requeue failed items")
    rf.set_defaults(func=cmd_retry_failed)

    rs = sub.add_parser("repo-status", help="repo-index pipeline health + predictor state")
    rs.set_defaults(func=cmd_repo_status)

    ir = sub.add_parser("index-repo", help="index a repo/dir now via the hub-daemon")
    ir.add_argument("path")
    ir.add_argument("--max", type=int, default=400, help="max files this call (default 400)")
    ir.set_defaults(func=cmd_index_repo)

    wr = sub.add_parser("watch-repo", help="add a repo/dir to the idle-indexer watch list")
    wr.add_argument("path")
    wr.set_defaults(func=cmd_watch_repo)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
