"""Semantic router over the local tool surface (idea #13).

Hundreds of MCP tools, dozens of agents, and a large skill library are more
than any prompt can hold. Embedding their names + descriptions turns "which
tool do I use for X?" into a local vector query — an offline ToolSearch that
also powers the TUI's ctrl+p palette.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import embed_core
import hub_lib

from semantic_ops.fuse import Hit
from semantic_ops.logs_corpus import hub_dir
from semantic_ops.sweep import _frontmatter
from semantic_ops.vecstore import VecStore

KINDS = ("skill", "agent", "mcp_tool")
_log = hub_lib.get_logger("semantic_ops")


def registry_db_path() -> Path:
    return Path(os.environ.get("HUB_REGISTRY_DB", str(hub_dir() / "registry.db")))


def skill_roots() -> list[Path]:
    roots = [hub_dir() / "skills", Path.home() / ".claude" / "skills"]
    cache = Path.home() / ".claude" / "plugins" / "cache"
    if cache.is_dir():
        roots += list(cache.glob("*/*/*/skills"))
    return [r for r in roots if r.is_dir()]


def agent_roots() -> list[Path]:
    roots = [Path.home() / ".claude" / "agents", hub_dir() / ".claude" / "agents"]
    cache = Path.home() / ".claude" / "plugins" / "cache"
    if cache.is_dir():
        roots += list(cache.glob("*/*/*/agents"))
    return [r for r in roots if r.is_dir()]


def mcp_registry_files() -> list[Path]:
    f = hub_dir() / "libraries" / "mcp-library" / "registry.json"
    return [f] if f.exists() else []


def _row(kind: str, name: str, desc: str, origin: str) -> dict:
    return {"kind": kind, "name": name, "desc": desc, "origin": origin,
            "text": f"{kind} {name}: {desc}"}


def collect_skills() -> list[dict]:
    rows, seen = [], set()
    for root in skill_roots():
        for skill_md in sorted(root.glob("*/SKILL.md")):
            fm = _frontmatter(skill_md.read_text(errors="ignore"))
            name = fm.get("name") or skill_md.parent.name
            desc = fm.get("description", "")
            if not desc or name in seen:
                continue
            seen.add(name)
            rows.append(_row("skill", name, desc, str(skill_md)))
    return rows


def collect_agents() -> list[dict]:
    rows, seen = [], set()
    for root in agent_roots():
        for md in sorted(root.glob("*.md")):
            fm = _frontmatter(md.read_text(errors="ignore"))
            name = fm.get("name") or md.stem
            desc = fm.get("description", "")
            if not desc or name in seen:
                continue
            seen.add(name)
            rows.append(_row("agent", name, desc, str(md)))
    return rows


def _walk_tools(obj, origin: str, rows: list[dict], seen: set[str]) -> None:
    """Tolerant walk: registry shapes vary, tools may be nested under servers."""
    if isinstance(obj, dict):
        name = obj.get("name") or obj.get("tool")
        desc = obj.get("description") or obj.get("what") or ""
        if (isinstance(name, str) and isinstance(desc, str) and desc
                and name not in seen and not obj.get("tools")):
            seen.add(name)
            rows.append(_row("mcp_tool", name, desc, origin))
        for v in obj.values():
            _walk_tools(v, origin, rows, seen)
    elif isinstance(obj, list):
        for v in obj:
            _walk_tools(v, origin, rows, seen)


def collect_mcp_tools() -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for f in mcp_registry_files():
        try:
            _walk_tools(json.loads(f.read_text(errors="ignore")), str(f), rows, seen)
        except ValueError as e:
            _log.warning("mcp registry unreadable (%s): %s", f, e)
    return rows


def collect_all(kinds: tuple[str, ...] = KINDS) -> list[dict]:
    rows: list[dict] = []
    if "skill" in kinds:
        rows += collect_skills()
    if "agent" in kinds:
        rows += collect_agents()
    if "mcp_tool" in kinds:
        rows += collect_mcp_tools()
    return rows


def build_registry(db_path: str | Path | None = None) -> int:
    """Embed every skill/agent/tool description; returns newly added rows."""
    rows = collect_all()
    if not rows:
        return 0
    for r in rows:
        r["id"] = "reg:" + hub_lib.compute_hash(r["text"], model="router")
    store = VecStore(db_path or registry_db_path())
    try:
        known = store.existing_ids([r["id"] for r in rows])
        fresh, seen = [], set()
        for r in rows:
            if r["id"] in known or r["id"] in seen:
                continue
            seen.add(r["id"])
            fresh.append(r)
        if not fresh:
            return 0
        try:
            vecs = embed_core.embed_texts([r["text"] for r in fresh])
        except embed_core.EmbeddingUnavailable as e:
            _log.warning("registry build skipped (embed pool down): %s", e)
            return 0
        model = embed_core.embed_model()
        return store.upsert([
            {"id": r["id"], "ref": f"{r['kind']}:{r['name']}", "ts": 0.0,
             "kind": r["kind"], "text": r["desc"], "vector": v, "model": model,
             "meta": {"name": r["name"], "origin": r["origin"]}}
            for r, v in zip(fresh, vecs, strict=True)
        ])
    finally:
        store.close()


def route(task: str, kinds: tuple[str, ...] = KINDS, top_k: int = 5,
          db_path: str | Path | None = None) -> list[Hit]:
    """Which skills/agents/MCP tools best fit this task."""
    path = Path(db_path) if db_path else registry_db_path()
    if not path.exists():
        return []
    try:
        qvec = embed_core.embed_texts([task])[0]
    except embed_core.EmbeddingUnavailable as e:
        _log.warning("route degraded (embed pool down): %s", e)
        return []
    store = VecStore(path)
    try:
        rows = store.query(qvec, top=top_k, kinds=tuple(kinds))
    finally:
        store.close()
    return [Hit("router", r["ref"], r["score"], r["text"][:400], dict(r["meta"]))
            for r in rows]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Semantic dispatch over local skills, agents and MCP tools")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="(re)build the registry index")
    r = sub.add_parser("route", help="rank the local tool surface for a task")
    r.add_argument("task")
    r.add_argument("--top", type=int, default=5)
    r.add_argument("--kinds", default=",".join(KINDS))
    args = ap.parse_args(argv)
    if args.cmd == "build":
        print(f"registry: {build_registry()} new entries -> {registry_db_path()}")
        return 0
    kinds = tuple(k.strip() for k in args.kinds.split(",") if k.strip())
    hits = route(args.task, kinds=kinds, top_k=args.top)
    for h in hits:
        print(f"{h.score:7.4f}  {h.ref}\n         {h.snippet[:110]}")
    if not hits:
        print("no matches (run `build` first? embed pool up?)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
