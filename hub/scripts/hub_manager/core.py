"""core.py — shared paths, env resolution, and small helpers for hub_manager.

Everything targets the *live* hub runtime dir (HUB_DIR, default
~/.global-ai-hub) regardless of where the code checkout lives, so the TUI
always operates on real queue/index state.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HUB_DIR = Path(os.environ.get("HUB_DIR", Path.home() / ".global-ai-hub")).expanduser()
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
VENV_PY = HUB_DIR / ".venv" / "bin" / "python"

# scripts/ is not a package; make its flat modules (embed_core,
# pipeline_manager) importable exactly once — repeated inserts would grow
# sys.path unboundedly under the 30s health refresh.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# pipeline / queue
QUEUE_STATE = HUB_DIR / "pipeline_queue.json"
QUEUE_LOCK = HUB_DIR / "pipeline_queue.lock"
DOCS_LIST = HUB_DIR / "docslist.textmirror"
PIPELINE_SCRIPT = SCRIPTS_DIR / "pipeline_manager.py"
PIPELINE_LOG = HUB_DIR / "pipeline_manager.log"

# stage tooling (mirrors pipeline_manager.py's layout)
MIRROR_SKILL_DIR = Path.home() / ".claude" / "skills" / "web-text-mirror" / "scripts"
MIRROR_SCRIPT = MIRROR_SKILL_DIR / "text_mirror.py"
MIRROR_OUT_DIR = MIRROR_SKILL_DIR.parent / "text-mirror"
_DISTILLERS_DIR = Path(os.environ.get("DISTILLERS_DIR",
                                       Path.home() / "dev" / "distillers"))
DISTILL_SCRIPT = _DISTILLERS_DIR / "distill_offline.py"
INDEXER_SCRIPT = SCRIPTS_DIR / "docset_indexer.py"

# indexes / registries
HUB_DB = HUB_DIR / "hub.db"
CHROMA_DIR = HUB_DIR / ".chroma-docsets"
# docsets.db lives inside CHROMA_DIR (not HUB_DIR directly) so the single
# Syncthing folder shared for CHROMA_DIR carries the registry alongside the
# vectors it describes — HUB_DOCSET_DB still overrides for anyone who wants
# a different location.
DOCSETS_DB = Path(os.environ.get("HUB_DOCSET_DB", CHROMA_DIR / "docsets.db")).expanduser()
WATCH_DIRS = HUB_DIR / "watch_dirs.txt"

# MCP server — mcp-server/ is committed repo source (sibling of scripts/),
# not runtime state, so this is checkout-relative, not HUB_DIR-relative
# (HUB_DIR is the runtime data dir and need not be the checkout on every box).
MCP_SERVER = SCRIPTS_DIR.parent / "mcp-server" / "hub_mcp_server.py"
MCP_PORT = int(os.environ.get("HUB_MCP_PORT", "8787"))

# web-text-mirror --serve API (Chrome extension backend)
EXT_API_PORT = int(os.environ.get("HUB_EXT_API_PORT", "8765"))

LOG_FILES = {
    "pipeline_manager": PIPELINE_LOG,
    "hub-daemon": HUB_DIR / "hub-daemon.log",
    "idle-indexer": HUB_DIR / "idle-indexer.log",
    "hub-manager": HUB_DIR / "hub-manager.log",
}


def python_for_hub() -> str:
    """The interpreter hub scripts should run under (venv if present)."""
    return str(VENV_PY) if VENV_PY.exists() else sys.executable


def pid_alive(pid: int | str | None) -> bool:
    try:
        os.kill(int(pid), 0)  # type: ignore[arg-type]
        return True
    except (OSError, TypeError, ValueError):
        return False


def pgrep(pattern: str) -> list[int]:
    """PIDs whose full command line matches pattern (empty list on none)."""
    try:
        out = subprocess.run(["pgrep", "-f", pattern], capture_output=True,
                             text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [int(p) for p in out.stdout.split() if p.strip().isdigit()]


def disk_free_gb(path: Path | None = None) -> float:
    # HUB_DIR read here, not as a default-arg value — a default arg binds at
    # def-time and would go stale under tests that monkeypatch core.HUB_DIR.
    usage = shutil.disk_usage(path if path is not None else HUB_DIR)
    return usage.free / (1024 ** 3)


def dir_size_mb(path: Path) -> float:
    if not path.exists():
        return 0.0
    total = 0
    for p in path.rglob("*"):
        try:
            if p.is_file():
                total += p.stat().st_size
        except OSError:
            continue
    return total / (1024 ** 2)


def age_str(ts: float) -> str:
    delta = max(0, time.time() - ts)
    for unit, secs in (("d", 86400), ("h", 3600), ("m", 60)):
        if delta >= secs:
            return f"{delta / secs:.0f}{unit} ago"
    return f"{delta:.0f}s ago"


def tail_file(path: Path, lines: int = 200) -> str:
    """Last N lines of a text file without loading the whole thing."""
    if not path.exists():
        return f"({path} does not exist yet)"
    try:
        with path.open("rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            block = min(size, max(4096, lines * 200))
            fh.seek(size - block)
            data = fh.read().decode("utf-8", errors="replace")
    except OSError as exc:
        return f"(cannot read {path}: {exc})"
    return "\n".join(data.splitlines()[-lines:])


def ollama_hosts() -> list[tuple[str, int]]:
    """Weighted host pool, exactly as embed_core resolves it."""
    import embed_core  # lazy: cheap after first import via sys.modules
    return embed_core._parse_hosts()


def embed_model() -> str:
    import embed_core
    return os.environ.get("HUB_EMBED_MODEL", embed_core.DEFAULT_MODEL)
