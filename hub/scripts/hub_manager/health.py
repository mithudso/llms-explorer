"""health.py — health checks for every hub subsystem.

Each check returns a HealthCheck(name, ok, detail); ok is None for
informational rows. run_all() is safe to call from a worker thread — every
probe is bounded by a short timeout.
"""

from __future__ import annotations

import json
import sqlite3
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from . import core, queue_model

PROBE_TIMEOUT = 4
CHROMA_SIZE_TTL = 300  # rglob over the chroma tree is expensive; cache it
_chroma_size_cache: tuple[float, float] | None = None  # (measured_at, mb)


@dataclass
class HealthCheck:
    name: str
    ok: bool | None  # None = informational
    detail: str
    check_id: str = ""  # doctor-registry key; "" = no doctor actions

    @property
    def icon(self) -> str:
        return {"True": "✅", "False": "❌"}.get(str(self.ok), "ℹ️")


def _http_probe(url: str) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(url, timeout=PROBE_TIMEOUT) as resp:
            return True, f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        # Any HTTP response means a live listener (MCP streamable HTTP answers
        # 406/400 to plain GETs, for instance).
        return True, f"HTTP {exc.code} (listener up)"
    except OSError as exc:
        return False, str(exc)


def check_ollama_hosts() -> list[HealthCheck]:
    checks = []
    model = core.embed_model()
    for url, weight in core.ollama_hosts():
        try:
            with urllib.request.urlopen(f"{url}/api/tags", timeout=PROBE_TIMEOUT) as resp:
                tags = json.loads(resp.read().decode())
            names = [m.get("name", "") for m in tags.get("models", [])]
            has_model = any(n.startswith(model) for n in names)
            running = _running_models(url)
            detail = (f"weight {weight}, {len(names)} downloaded "
                      f"({', '.join(names) if names else 'none'})"
                      + ("" if has_model else f" — MISSING {model}")
                      + f"; running: {', '.join(running) if running else 'none'}")
            checks.append(HealthCheck(f"ollama {url}", has_model, detail,
                                      check_id=f"ollama:{url}"))
        except (OSError, ValueError) as exc:
            checks.append(HealthCheck(f"ollama {url}", False,
                                      f"weight {weight}, unreachable: {exc}",
                                      check_id=f"ollama:{url}"))
    return checks


def _running_models(url: str) -> list[str]:
    """Models currently loaded (resident) on a host, via /api/ps. Best-effort
    — a host that's up but doesn't answer /api/ps just reports no running
    models rather than failing the whole check."""
    try:
        with urllib.request.urlopen(f"{url}/api/ps", timeout=PROBE_TIMEOUT) as resp:
            ps = json.loads(resp.read().decode())
        return [m.get("name", "") for m in ps.get("models", [])]
    except (OSError, ValueError):
        return []


def check_mcp() -> HealthCheck:
    ok, detail = _http_probe(f"http://127.0.0.1:{core.MCP_PORT}/mcp")
    if ok:
        return HealthCheck("MCP server (HTTP)", True,
                           f"port {core.MCP_PORT}: {detail}", check_id="mcp")
    return HealthCheck("MCP server (HTTP)", None,
                       f"no listener on {core.MCP_PORT} — fine if clients spawn it over stdio",
                       check_id="mcp")


def check_daemons() -> list[HealthCheck]:
    checks = []
    for name, pattern in (("hub-daemon", "hub-daemon.py"),
                          ("idle-indexer", "idle-indexer.py")):
        pids = core.pgrep(pattern)
        log = core.LOG_FILES.get(name)
        log_note = ""
        if log and log.exists():
            log_note = f", log {core.age_str(log.stat().st_mtime)}"
        if pids:
            checks.append(HealthCheck(name, True, f"pid {pids[0]}{log_note}",
                                      check_id=name))
        else:
            checks.append(HealthCheck(name, None, f"not running{log_note}",
                                      check_id=name))
    return checks


def check_web_text_mirror() -> HealthCheck:
    """web-text-mirror --serve API (Chrome extension backend, port
    EXT_API_PORT). Distinct from check_daemons()'s hub-daemon/idle-indexer —
    this one has no watchdog process match, only the HTTP listener itself."""
    ok, detail = _http_probe(f"http://127.0.0.1:{core.EXT_API_PORT}/")
    return HealthCheck("web-text-mirror (Chrome ext. API)", ok,
                       f"port {core.EXT_API_PORT}: {detail}",
                       check_id="web-text-mirror")


def check_pipeline() -> HealthCheck:
    pid = queue_model.manager_pid()
    counts = queue_model.summary()
    counts_s = queue_model.summary_line(counts)
    if pid:
        return HealthCheck("pipeline manager", True, f"pid {pid} | {counts_s}",
                           check_id="pipeline")
    stale = core.QUEUE_LOCK.exists()
    note = " (stale lock file)" if stale else ""
    pending = counts.get("pending", 0) + counts.get("running", 0)
    ok = None if pending == 0 else False
    return HealthCheck("pipeline manager", ok, f"not running{note} | {counts_s}",
                       check_id="pipeline")


def check_stores() -> list[HealthCheck]:
    checks = []
    for name, path in (("hub.db (file index)", core.HUB_DB),
                       ("docsets.db (registry)", core.DOCSETS_DB)):
        if path.exists():
            mb = path.stat().st_size / (1024 ** 2)
            checks.append(HealthCheck(name, True,
                                      f"{mb:.1f} MB, {core.age_str(path.stat().st_mtime)}",
                                      check_id=path.name))
        else:
            checks.append(HealthCheck(name, None, "missing (not yet built)",
                                      check_id=path.name))
    if core.CHROMA_DIR.exists():
        checks.append(HealthCheck("chroma docsets", True,
                                  f"{_chroma_size_mb():.0f} MB, "
                                  f"{count_docsets()} docsets", check_id="chroma"))
    else:
        checks.append(HealthCheck("chroma docsets", None,
                                  "missing (no docsets indexed)", check_id="chroma"))
    return checks


def _chroma_size_mb() -> float:
    """dir_size_mb over .chroma-docsets, cached — the recursive walk of a
    multi-hundred-MB tree must not run on every 30s health refresh."""
    global _chroma_size_cache
    now = time.monotonic()
    if _chroma_size_cache and now - _chroma_size_cache[0] < CHROMA_SIZE_TTL:
        return _chroma_size_cache[1]
    mb = core.dir_size_mb(core.CHROMA_DIR)
    _chroma_size_cache = (now, mb)
    return mb


def count_docsets() -> int:
    if not core.DOCSETS_DB.exists():
        return 0
    try:
        with sqlite3.connect(core.DOCSETS_DB) as db:
            tables = [r[0] for r in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")]
            for table in ("docsets", "registry"):
                if table in tables:
                    return db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except sqlite3.Error:
        pass
    return 0


def check_tooling() -> list[HealthCheck]:
    checks = []
    for name, path in (("mirror script", core.MIRROR_SCRIPT),
                       ("distill script", core.DISTILL_SCRIPT),
                       ("docset indexer", core.INDEXER_SCRIPT),
                       ("hub venv python", core.VENV_PY)):
        checks.append(HealthCheck(name, path.exists(), str(path)))
    return checks


def check_disk() -> HealthCheck:
    free = core.disk_free_gb()
    return HealthCheck("disk free", free > 5, f"{free:.1f} GB on {core.HUB_DIR}")


def run_all(disabled: set[str] | None = None) -> list[HealthCheck]:
    """Every subsystem check; one raising probe must not abort the rest.
    Checks whose check_id is in `disabled` are skipped (user-muted)."""
    disabled = disabled or set()
    checks: list[HealthCheck] = []
    groups = (("pipeline", lambda: [check_pipeline()]),
              ("ollama", check_ollama_hosts),
              ("mcp", lambda: [check_mcp()]),
              ("daemons", check_daemons),
              ("web-text-mirror", lambda: [check_web_text_mirror()]),
              ("stores", check_stores),
              ("tooling", check_tooling),
              ("disk", lambda: [check_disk()]))
    for name, fn in groups:
        try:
            checks.extend(fn())
        except Exception as exc:  # noqa: BLE001 — degrade to a failed row
            checks.append(HealthCheck(f"{name} check", False, f"check crashed: {exc}"))
    kept = [c for c in checks if c.check_id not in disabled]
    hidden = len(checks) - len(kept)
    if hidden:
        kept.append(HealthCheck(f"{hidden} check(s) disabled", None,
                                "press u to restore all", check_id=""))
    return kept
