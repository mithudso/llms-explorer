"""doctor.py — per-subsystem diagnostics and remediation for the Health tab.

Every health check with a check_id maps to a doctor entry:
  diagnose(check_id)  -> list[str] report lines (deep checks, log forensics)
  remedies(check_id)  -> which of start/stop apply
  start(check_id)     -> spawn/restart the subsystem (detached, logged)
  stop(check_id)      -> SIGTERM the subsystem's process(es)

All functions are worker-thread safe: bounded timeouts, no UI access.
"""

from __future__ import annotations

import json
import os
import re
import signal
import sqlite3
import subprocess
import time
import urllib.request
from dataclasses import dataclass

from . import core, queue_model, settings

DAEMONS = {
    "idle-indexer": core.SCRIPTS_DIR / "idle-indexer.py",
    "hub-daemon": core.SCRIPTS_DIR / "hub-daemon.py",
}


@dataclass
class Remedy:
    action: str  # "start" | "stop"
    label: str


def _line(ok: bool | None, text: str) -> str:
    icon = {True: "✅", False: "❌"}.get(ok, "ℹ️")
    return f"  {icon} {text}"


def _log_forensics(name: str, lines: list[str]) -> None:
    """Log freshness + last error lines for a subsystem's log file."""
    log = core.LOG_FILES.get(name)
    if not log or not log.exists():
        lines.append(_line(None, f"no log file yet ({log})"))
        return
    age = core.age_str(log.stat().st_mtime)
    stale = time.time() - log.stat().st_mtime > 86400
    lines.append(_line(not stale, f"log last written {age} ({log})"))
    tail = core.tail_file(log, 100)
    errors = [ln for ln in tail.splitlines()
              if re.search(r"error|traceback|exception|failed", ln, re.I)]
    if errors:
        lines.append(_line(False, "last error lines in log:"))
        lines.extend(f"      {ln[:160]}" for ln in errors[-5:])
    else:
        lines.append(_line(True, "no error lines in recent log tail"))


def _probe_ollama(url: str, lines: list[str]) -> None:
    model = core.embed_model()
    started = time.monotonic()
    try:
        with urllib.request.urlopen(f"{url}/api/tags", timeout=4) as resp:
            tags = json.loads(resp.read().decode())
        ms = (time.monotonic() - started) * 1000
        names = [m.get("name", "") for m in tags.get("models", [])]
        lines.append(_line(True, f"reachable in {ms:.0f} ms, {len(names)} models"))
        has = any(n.startswith(model) for n in names)
        lines.append(_line(has, f"embed model {model} "
                                f"{'present' if has else 'MISSING — run: ollama pull ' + model}"))
    except (OSError, ValueError) as exc:
        lines.append(_line(False, f"unreachable: {exc}"))
        lines.append(_line(None, "if the box is up, check `ollama serve` and "
                                 "OLLAMA_HOST binding / firewall"))


def _sqlite_quick_check(path, lines: list[str]) -> None:
    if not path.exists():
        lines.append(_line(None, f"{path} missing (not yet built)"))
        return
    mb = path.stat().st_size / (1024 ** 2)
    lines.append(_line(True, f"{path.name}: {mb:.1f} MB, "
                             f"modified {core.age_str(path.stat().st_mtime)}"))
    try:
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as db:
            result = db.execute("PRAGMA quick_check").fetchone()[0]
        lines.append(_line(result == "ok", f"sqlite quick_check: {result}"))
    except sqlite3.Error as exc:
        lines.append(_line(False, f"sqlite quick_check failed: {exc}"))


def _common_env(lines: list[str]) -> None:
    lines.append(_line(core.VENV_PY.exists(), f"hub venv python: {core.VENV_PY}"))


# --------------------------------------------------------------------------- #
# diagnose
# --------------------------------------------------------------------------- #

def diagnose(check_id: str) -> list[str]:
    """Full diagnostic suite for one subsystem; returns report lines."""
    lines: list[str] = [f"=== diagnostics: {check_id} ==="]
    try:
        if check_id in DAEMONS:
            _diagnose_daemon(check_id, lines)
        elif check_id == "pipeline":
            _diagnose_pipeline(lines)
        elif check_id.startswith("ollama:"):
            _probe_ollama(check_id.split(":", 1)[1], lines)
        elif check_id == "mcp":
            _diagnose_mcp(lines)
        elif check_id in ("hub.db", "docsets.db"):
            path = core.HUB_DB if check_id == "hub.db" else core.DOCSETS_DB
            _sqlite_quick_check(path, lines)
        elif check_id == "chroma":
            _diagnose_chroma(lines)
        elif check_id == "misfiled":
            _diagnose_misfiled(lines)
        else:
            lines.append(_line(None, "no deep diagnostics for this check — "
                                     "detail row is authoritative"))
    except Exception as exc:  # noqa: BLE001 — a probe crash is itself a finding
        lines.append(_line(False, f"diagnostic crashed: {exc}"))
    _append_recall(lines)
    return lines


def _diagnose_misfiled(lines: list[str]) -> None:
    """Files whose content fits another indexed directory better than their own
    (semantic_ops.misfiled — reuses hub.db vectors, no embedding calls)."""
    from semantic_ops import misfiled
    hits = misfiled.outliers()
    if not hits:
        lines.append(_line(True, "no misfiled files detected in the hub.db corpus"))
        return
    lines.append(_line(None, f"{len(hits)} possible misfiled files "
                             "(advisory — semantic placement only):"))
    for h in hits[:10]:
        lines.append(f"      +{h.score:.2f}  {h.ref}")
        lines.append(f"        ↳ fits {h.meta['suggested_dir']} better than "
                     f"{h.meta['own_dir']}")


def _append_recall(lines: list[str]) -> None:
    """Failed checks get the most similar past incidents from the log corpus
    (semantic_ops.fix_recall), plus what happened in the hours after each —
    best-effort: recall being broken must never break diagnostics."""
    bad = [ln for ln in lines if "❌" in ln]
    if not bad:
        return
    try:
        from semantic_ops import fix_recall
        query = " ".join(ln.replace("❌", " ").strip() for ln in bad)[:500]
        hits = fix_recall.nearest_fixes(query, top_k=3)
    except Exception:
        return
    if not hits:
        return
    lines.append(_line(None, "similar past incidents (log corpus):"))
    for h in hits:
        when = time.strftime("%Y-%m-%d %H:%M", time.localtime(h.meta.get("ts", 0)))
        lines.append(f"      {h.score:.2f}  {when}  {h.snippet[:120]}")
        for fc in h.meta.get("fix_candidates", [])[:4]:
            lines.append(f"        ↳ then [{fc['kind']}]: {fc['text'][:110]}")


def _diagnose_daemon(name: str, lines: list[str]) -> None:
    script = DAEMONS[name]
    pids = core.pgrep(script.name)
    lines.append(_line(bool(pids),
                       f"process: {'pid ' + str(pids[0]) if pids else 'NOT RUNNING'}"))
    lines.append(_line(script.exists(), f"script: {script}"))
    _common_env(lines)
    _log_forensics(name, lines)
    if name == "idle-indexer":
        wd = core.WATCH_DIRS
        if wd.exists():
            dirs = [ln for ln in wd.read_text().splitlines() if ln.strip()]
            live = [d for d in dirs if os.path.isdir(d)]
            lines.append(_line(bool(live),
                               f"watch_dirs.txt: {len(live)}/{len(dirs)} entries exist"))
        else:
            lines.append(_line(None, "watch_dirs.txt missing — defaults to ~/dev"))
        try:
            load1 = os.getloadavg()[0]
            lines.append(_line(None, f"load average {load1:.1f} "
                                     "(indexer only works when idle)"))
        except OSError:
            pass
        lines.append(_line(core.HUB_DB.exists(),
                           f"hub.db {'present' if core.HUB_DB.exists() else 'missing'}"))
    if name == "hub-daemon":
        sock = core.HUB_DIR / "hub.sock"
        lines.append(_line(sock.exists() or None, f"hub.sock: "
                           f"{'present' if sock.exists() else 'absent'}"))
    if not pids:
        lines.append(_line(None, "remedy available: press t to start it"))


def _diagnose_pipeline(lines: list[str]) -> None:
    pid = queue_model.manager_pid()
    lines.append(_line(bool(pid) or None,
                       f"manager: {'pid ' + str(pid) if pid else 'not running'}"))
    if not pid and core.QUEUE_LOCK.exists():
        lines.append(_line(False, f"STALE lock file {core.QUEUE_LOCK} — "
                                  "start will clear it"))
    counts = queue_model.summary()
    lines.append(_line(None, f"queue: {queue_model.summary_line(counts)}"))
    failed = [i for i in queue_model.load_items() if i.status == "failed"]
    for it in failed[:5]:
        lines.append(f"      failed: {it.url} — {it.error[:100]}")
    _common_env(lines)
    _log_forensics("pipeline_manager", lines)


def _diagnose_mcp(lines: list[str]) -> None:
    from . import health
    check = health.check_mcp()
    lines.append(_line(check.ok, check.detail))
    pids = core.pgrep("hub_mcp_server.py")
    lines.append(_line(bool(pids) or None,
                       f"server process(es): {pids or 'none'} "
                       "(stdio instances are client-spawned)"))
    lines.append(_line(core.MCP_SERVER.exists(), f"server script: {core.MCP_SERVER}"))
    _common_env(lines)


def _diagnose_chroma(lines: list[str]) -> None:
    from . import health
    lines.append(_line(core.CHROMA_DIR.exists(), f"dir: {core.CHROMA_DIR}"))
    if core.CHROMA_DIR.exists():
        lines.append(_line(True, f"{health.count_docsets()} docsets registered"))
    _sqlite_quick_check(core.DOCSETS_DB, lines)


# --------------------------------------------------------------------------- #
# remedies
# --------------------------------------------------------------------------- #

def remedies(check_id: str) -> list[Remedy]:
    if check_id in DAEMONS:
        return [Remedy("start", f"start {check_id}"),
                Remedy("stop", f"stop {check_id}")]
    if check_id == "pipeline":
        return [Remedy("start", "start pipeline manager"),
                Remedy("stop", "stop pipeline manager")]
    if check_id == "mcp":
        return [Remedy("start", f"start MCP HTTP on :{core.MCP_PORT}"),
                Remedy("stop", "stop MCP HTTP server")]
    return []


def start(check_id: str) -> str:
    """Spawn the subsystem detached, appending to its log. Returns a status
    line for the UI."""
    if check_id in DAEMONS:
        if core.pgrep(DAEMONS[check_id].name):
            return f"{check_id} already running"
        log_path = core.LOG_FILES.get(check_id, core.HUB_DIR / f"{check_id}.log")
        argv = [core.python_for_hub(), str(DAEMONS[check_id])]
        try:
            with log_path.open("a") as log:
                proc = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT,
                                        start_new_session=True,
                                        env={**os.environ, **settings.stage_env()})
        except OSError as exc:
            return f"spawn failed: {exc}"
        return f"started {check_id} (pid {proc.pid}, log {log_path})"
    if check_id == "pipeline":
        if not queue_model.manager_pid() and core.QUEUE_LOCK.exists():
            try:
                core.QUEUE_LOCK.unlink()  # stale: owner is dead
            except OSError:
                pass
        opts = settings.load()
        result = queue_model.start_manager(max_pages=opts["max_pages"],
                                           crawlers=opts["crawlers"],
                                           env=settings.stage_env(opts))
        return result if isinstance(result, str) else f"started pipeline (pid {result})"
    if check_id == "mcp":
        if core.pgrep("hub_mcp_server.py --http"):
            return "MCP HTTP server already running"
        argv = [core.python_for_hub(), str(core.MCP_SERVER),
                "--http", str(core.MCP_PORT)]
        log_path = core.HUB_DIR / "hub-mcp-http.log"
        try:
            with log_path.open("a") as log:
                proc = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT,
                                        start_new_session=True)
        except OSError as exc:
            return f"spawn failed: {exc}"
        return f"started MCP HTTP :{core.MCP_PORT} (pid {proc.pid}, log {log_path})"
    return f"no start remedy for {check_id}"


def stop(check_id: str) -> str:
    if check_id == "pipeline":
        return f"pipeline manager: {queue_model.stop_manager()}"
    if check_id == "mcp":
        pattern = "hub_mcp_server.py --http"
    elif check_id in DAEMONS:
        pattern = DAEMONS[check_id].name
    else:
        return f"no stop remedy for {check_id}"
    pids = core.pgrep(pattern)
    if not pids:
        return f"{check_id}: nothing running"
    stopped = []
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
            stopped.append(pid)
        except OSError:
            continue
    return f"{check_id}: sent SIGTERM to {stopped or 'nothing'}"
