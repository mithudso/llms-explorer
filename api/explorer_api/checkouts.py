"""Which concepts are checked out: held by a research run that has not finished.

The `/tree/` facts panel offers "Research this concept" only for a concept no
run already holds. API jobs are one source (`explorer_api.research`). The
others are research runs started outside the API, on this same machine, and
recorded only in files:

* a `/dr` run: ``$HUB_DIR/research/<slug>/manifest.json`` with status
  ``researching``. It holds its topic and every concept it lists.
* an llmsx explorer frontier batch: ``$LLMSX_HOME/jobs/batches/*/run.json``
  with status ``in-progress``. It holds each concept without a row in its
  ``results.jsonl``.
* a research suite run: ``$HUB_DIR/research/.pipeline/<run>/batches.json``.
  It holds each concept whose batch has not finished its last stage
  (``register``), including a paused batch: the run resumes it and a second
  run would duplicate the work.

A `/dr` manifest that has said ``researching`` for more than
:data:`DR_STALE_HOURS` is treated as abandoned. Suite batches have no such
cutoff, because a paused suite is resumed by hand days later.

The scan reads a few hundred small files, so its result is cached for
:data:`CACHE_SECONDS`. Suites with handoff receipts are revalidated on every
scan request because their reservations depend on a separate target plan.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import os
import re
import time
from pathlib import Path
from typing import Any

CACHE_SECONDS = 60
DR_STALE_HOURS = 24
SUITE_LAST_STAGE = "register"

_cache: tuple[float, list[dict[str, Any]], dict[str, str]] | None = None
_cache_handoffs = False
_handoffs: Any = None


def hub_dir() -> Path:
    return Path(os.environ.get("HUB_DIR") or Path.home() / ".global-ai-hub")


def llmsx_home() -> Path:
    return Path(os.environ.get("LLMSX_HOME") or Path.home() / ".llmsx")


def _key(name: str) -> str:
    return " ".join(name.split()).casefold()


def _json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _iso(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts, dt.UTC).isoformat(timespec="seconds")


def _mtime(path: Path) -> float | None:
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def _run(source: str, name: str, state: str, held: list[str], total: int,
         started: Any, updated: float | None) -> dict[str, Any]:
    return {"source": source, "name": name, "state": state, "pending": held,
            "total": total, "started": started if isinstance(started, str) else None,
            "updated": _iso(updated) if updated else None}


def _dr() -> list[dict[str, Any]]:
    cutoff = time.time() - DR_STALE_HOURS * 3600
    runs = []
    for path in (hub_dir() / "research").glob("*/manifest.json"):
        m = _json(path)
        if not isinstance(m, dict) or m.get("status") != "researching":
            continue
        updated = _mtime(path)
        if updated is None or updated < cutoff:
            continue
        concepts = [c for c in m.get("concepts") or [] if isinstance(c, dict)]
        names = [m.get("topic")] + [c.get("name") for c in concepts
                                    if c.get("status") not in ("done", "complete")]
        held = [n for n in names if isinstance(n, str) and n.strip()]
        runs.append(_run("dr", str(m.get("slug") or path.parent.name), "researching",
                         held, len(concepts) or 1, m.get("started"), updated))
    return runs


def _llmsx_batches() -> list[dict[str, Any]]:
    runs = []
    for path in (llmsx_home() / "jobs" / "batches").glob("*/run.json"):
        m = _json(path)
        if not isinstance(m, dict) or m.get("status") != "in-progress":
            continue
        finished: set[str] = set()
        results = path.parent / "results.jsonl"
        try:
            for line in results.read_text(encoding="utf-8").splitlines():
                row = json.loads(line) if line.strip() else None
                if isinstance(row, dict) and isinstance(row.get("concept"), str):
                    finished.add(_key(row["concept"]))
        except (OSError, ValueError):
            pass
        names = [n for n in m.get("concepts") or [] if isinstance(n, str)]
        held = [n for n in names if _key(n) not in finished]
        updated = max(filter(None, (_mtime(path), _mtime(results))), default=None)
        runs.append(_run("explorer-batch", str(m.get("root") or path.parent.name), "in-progress",
                         held, len(names), None, updated))
    return runs


def _suite_transfers(source: Path) -> set[str]:
    """Load the shared validator even for standalone spec_from_file_location imports."""
    global _handoffs
    if not (source / "handoffs.json").exists():
        return set()
    try:
        if _handoffs is None:
            path = Path(__file__).resolve().parents[2] / "hub/scripts/research_handoffs.py"
            spec = importlib.util.spec_from_file_location("_checkout_research_handoffs", path)
            if spec is None or spec.loader is None:
                return set()
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            _handoffs = module
        return _handoffs.validate_handoffs(source)
    except (ImportError, OSError, ValueError, TypeError):
        # Invalid or unavailable proof never weakens a reservation.
        return set()


def _suites() -> list[dict[str, Any]]:
    runs = []
    for listing in (hub_dir() / "research" / ".pipeline").glob("*/batches.json"):
        batches = _json(listing)
        if not isinstance(batches, list):
            continue
        transferred = _suite_transfers(listing.parent)
        held: list[str] = []
        total = 0
        newest = None
        for batch in batches:
            if not isinstance(batch, dict):
                continue
            names = [n for n in batch.get("concepts") or [] if isinstance(n, str)]
            total += len(names)
            state_file = listing.parent / "batches" / str(batch.get("id")) / "state.json"
            state = _json(state_file)
            stages = state.get("stages") if isinstance(state, dict) else None
            last = stages.get(SUITE_LAST_STAGE) if isinstance(stages, dict) else None
            if isinstance(last, dict) and last.get("status") == "done":
                continue
            held.extend(n for n in names if n not in transferred)
            newest = max(filter(None, (newest, _mtime(state_file))), default=None)
        if not held:
            continue
        # The suite records no "running" flag; a batch written in the last ten
        # minutes is the only evidence a worker is on it right now.
        live = newest is not None and time.time() - newest < 600
        meta = _json(listing.parent / "run.json")
        runs.append(_run("suite", listing.parent.name, "running" if live else "paused", held,
                         total, meta.get("started") if isinstance(meta, dict) else None, newest))
    return runs


def runs() -> list[dict[str, Any]]:
    """Every unfinished research run recorded in files on this machine."""
    found: list[dict[str, Any]] = []
    for source in (_dr, _llmsx_batches, _suites):
        try:
            found.extend(source())
        except OSError:
            # An unreadable tree of run files hides that source's runs; it
            # must not take the status endpoints down with it.
            continue
    return found


LABELS = {"dr": "a /dr run", "explorer-batch": "an explorer frontier batch",
          "suite": "the research suite run"}


def label(run: dict[str, Any]) -> str:
    return f"{LABELS.get(run['source'], run['source'])} {run['name']}"


def _scan() -> tuple[list[dict[str, Any]], dict[str, str]]:
    found = runs()
    held: dict[str, str] = {}
    for run in found:
        for name in run["pending"]:
            held.setdefault(_key(name), label(run))
    return found, held


def snapshot() -> tuple[list[dict[str, Any]], dict[str, str]]:
    """``(runs, {normalised concept: holder label})``, cached for
    :data:`CACHE_SECONDS`."""
    global _cache, _cache_handoffs
    now = time.monotonic()
    # A transferred reservation depends on a separate mutable plan. Recheck
    # each time so a missing/changed plan cannot remain released in the cache.
    handoffs = any((hub_dir() / "research" / ".pipeline").glob("*/handoffs.json"))
    if _cache is None or _cache_handoffs or handoffs or now - _cache[0] > CACHE_SECONDS:
        _cache = (now, *_scan())
        _cache_handoffs = handoffs
    return _cache[1], _cache[2]


def held_by(concept: str) -> str | None:
    """Who holds ``concept``, or None."""
    return snapshot()[1].get(_key(concept))


def now_iso() -> str:
    return _iso(time.time())


QUEUE_ROW = re.compile(
    r"^\s*-\s*\[(?P<done>[ xX])\]\s*Concept:\s*"
    r"(?P<ticks>`+)(?!`)(?P<concept>.+?)(?<!`)(?P=ticks)(?!`)(?=\s*(?:\||$))(?P<tags>.*)$")
QUEUE_TAG = re.compile(
    r"\|\s*(?P<tag>[^:|]+):\s*(?P<ticks>`+)(?!`)"
    r"(?P<value>.*?)(?<!`)(?P=ticks)(?!`)(?=\s*(?:\||$))")


def _queue_unquote(value: str, ticks: str) -> str:
    # The inventory writer pads names that start/end with a backtick so the
    # name's ticks stay separate from its longer Markdown delimiter.
    if len(ticks) > 1 and value.startswith(" ") and value.endswith(" "):
        return value[1:-1]
    return value


def research_queue(repo: Path, show: int = 25) -> dict[str, Any]:
    """Counts and the next rows of ``concept-tree/RESEARCH_QUEUE.md``: the
    backlog nothing has checked out yet. Accept ordinary single-backtick
    labels and the inventory writer's longer delimiters for embedded ticks."""
    path = repo / "concept-tree" / "RESEARCH_QUEUE.md"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {"pending": 0, "done": 0, "next": [], "available": False}
    pending, done, nxt = 0, 0, []
    held = snapshot()[1]
    for line in lines:
        m = QUEUE_ROW.match(line)
        if not m:
            continue
        if m["done"] != " ":
            done += 1
            continue
        pending += 1
        concept = _queue_unquote(m["concept"], m["ticks"])
        if len(nxt) < show and _key(concept) not in held:
            tags = {tag["tag"].strip().casefold(): _queue_unquote(tag["value"], tag["ticks"])
                    for tag in QUEUE_TAG.finditer(m["tags"])}
            nxt.append({"concept": concept, "parent": tags.get("parent") or None,
                        "cluster": tags.get("cluster") or None})
    return {"pending": pending, "done": done, "next": nxt, "available": True}


def clear_cache() -> None:
    global _cache, _cache_handoffs
    _cache = None
    _cache_handoffs = False
