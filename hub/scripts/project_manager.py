#!/usr/bin/env python3
"""project_manager.py — the hub's project-registry data layer.

A master record of every project the hub/TAM tooling ecosystem touches:
repos, memory files, llms.txt exports, scripts, purpose, outstanding items,
and — the point of the whole thing — exactly how to activate each piece
(the command that starts the server / runs the pipeline / loads the agent).

One SQLite file (project_registry.db), five tables:
  projects        one row per tracked project (repo, skill, mcp-server, ...)
  project_files   memory files / llms.txt / key scripts / docs, per project
  activations     named ways to start/run/invoke a project (>=1 per project)
  outstanding     open issues/TODOs/risks, open or resolved
  activity_log    append-only record of actions taken on a project

CLI mirrors hub_lib's shape (argparse subcommands, JSON in/out) so both the
MCP tools and a human at a terminal can drive it. See hub_mcp_server.py's
hub_pm_* tools for the MCP surface.

Usage:
  ~/.global-ai-hub/.venv/bin/python scripts/project_manager.py <cmd> ...
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

HUB_DIR = Path(os.environ.get("HUB_DIR", Path.home() / ".global-ai-hub"))
DB_FILE = HUB_DIR / "project_registry.db"

VALID_KINDS = {
    "repo", "skill", "mcp-server", "agent", "extension", "app",
    "dashboard", "pipeline", "docset", "other",
}
VALID_FILE_TYPES = {"memory", "llms_txt", "script", "readme", "config", "doc", "other"}
VALID_STATUSES = {"active", "stable", "paused", "deprecated", "archived"}
VALID_OUTSTANDING_STATUS = {"open", "resolved", "wontfix"}
VALID_SEVERITY = {"critical", "high", "medium", "low"}
# Alphabetical ORDER BY severity puts "low" before "medium" — worst-first needs an
# explicit rank so the most urgent open items always surface at the top of a list.
_SEVERITY_ORDER_SQL = (
    "CASE severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 "
    "WHEN 'medium' THEN 2 WHEN 'low' THEN 3 ELSE 4 END"
)


@contextlib.contextmanager
def get_conn():
    """Yields a connection always closed on exit (see hub_sqlite.py's note on
    fd leaks from bare `with conn:` under a long-lived MCP server)."""
    HUB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                name        TEXT PRIMARY KEY,
                kind        TEXT NOT NULL DEFAULT 'repo',
                path        TEXT,
                remote      TEXT,
                purpose     TEXT,
                status      TEXT NOT NULL DEFAULT 'active',
                notes       TEXT,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS project_files (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                project     TEXT NOT NULL REFERENCES projects(name) ON DELETE CASCADE,
                file_type   TEXT NOT NULL DEFAULT 'other',
                path        TEXT NOT NULL,
                description TEXT,
                UNIQUE(project, path)
            );
            CREATE TABLE IF NOT EXISTS activations (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                project     TEXT NOT NULL REFERENCES projects(name) ON DELETE CASCADE,
                label       TEXT NOT NULL DEFAULT 'default',
                command     TEXT NOT NULL,
                description TEXT,
                UNIQUE(project, label)
            );
            CREATE TABLE IF NOT EXISTS outstanding (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                project     TEXT NOT NULL REFERENCES projects(name) ON DELETE CASCADE,
                description TEXT NOT NULL,
                severity    TEXT NOT NULL DEFAULT 'medium',
                status      TEXT NOT NULL DEFAULT 'open',
                created_at  TEXT NOT NULL,
                resolved_at TEXT
            );
            CREATE TABLE IF NOT EXISTS activity_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                project     TEXT NOT NULL REFERENCES projects(name) ON DELETE CASCADE,
                action      TEXT NOT NULL,
                detail      TEXT,
                ts          TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_files_project ON project_files(project);
            CREATE INDEX IF NOT EXISTS idx_activations_project ON activations(project);
            CREATE INDEX IF NOT EXISTS idx_outstanding_project ON outstanding(project, status);
            CREATE INDEX IF NOT EXISTS idx_activity_project ON activity_log(project, ts);
        """)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z"


def _check(value: str, allowed: set[str], field: str) -> str:
    if value not in allowed:
        raise ValueError(f"{field} must be one of {sorted(allowed)}, got {value!r}")
    return value


# --------------------------------------------------------------------------- #
# projects
# --------------------------------------------------------------------------- #

def upsert_project(name: str, kind: str = "repo", path: str = "", remote: str = "",
                    purpose: str = "", status: str = "active", notes: str = "") -> dict:
    """Create or update a project row. Only non-empty fields overwrite an
    existing row's values — an upsert that only wants to bump `status` should
    not have to re-type the purpose."""
    _check(kind, VALID_KINDS, "kind")
    _check(status, VALID_STATUSES, "status")
    init_db()
    now = _now()
    with get_conn() as conn:
        existing = conn.execute("SELECT * FROM projects WHERE name=?", (name,)).fetchone()
        if existing is None:
            conn.execute(
                "INSERT INTO projects (name, kind, path, remote, purpose, status, notes, "
                "created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (name, kind, path, remote, purpose, status, notes, now, now),
            )
            action = "created"
        else:
            merged = {
                "kind": kind or existing["kind"],
                "path": path or existing["path"],
                "remote": remote or existing["remote"],
                "purpose": purpose or existing["purpose"],
                "status": status or existing["status"],
                "notes": notes or existing["notes"],
            }
            conn.execute(
                "UPDATE projects SET kind=?, path=?, remote=?, purpose=?, status=?, notes=?, "
                "updated_at=? WHERE name=?",
                (*merged.values(), now, name),
            )
            action = "updated"
        conn.execute(
            "INSERT INTO activity_log (project, action, detail, ts) VALUES (?,?,?,?)",
            (name, f"project_{action}", "", now),
        )
    return {"name": name, "action": action}


def get_project(name: str) -> dict | None:
    """Full detail for one project: core row + files + activations +
    outstanding items + last 10 activity entries."""
    init_db()
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM projects WHERE name=?", (name,)).fetchone()
        if row is None:
            return None
        out = dict(row)
        out["files"] = [dict(r) for r in conn.execute(
            "SELECT file_type, path, description FROM project_files WHERE project=? "
            "ORDER BY file_type, path", (name,))]
        out["activations"] = [dict(r) for r in conn.execute(
            "SELECT label, command, description FROM activations WHERE project=? "
            "ORDER BY label", (name,))]
        out["outstanding"] = [dict(r) for r in conn.execute(
            "SELECT id, description, severity, status, created_at, resolved_at "
            "FROM outstanding WHERE project=? ORDER BY "
            f"(status='open') DESC, {_SEVERITY_ORDER_SQL}, created_at", (name,))]
        out["recent_activity"] = [dict(r) for r in conn.execute(
            "SELECT action, detail, ts FROM activity_log WHERE project=? "
            "ORDER BY ts DESC LIMIT 10", (name,))]
        return out


def list_projects(kind: str = "", query: str = "", status: str = "") -> list[dict]:
    init_db()
    sql = ("SELECT p.name, p.kind, p.path, p.status, p.purpose, p.updated_at, "
           "(SELECT COUNT(*) FROM outstanding o WHERE o.project=p.name AND o.status='open') "
           "AS open_items FROM projects p WHERE 1=1")
    args: list = []
    if kind:
        sql += " AND p.kind=?"
        args.append(kind)
    if status:
        sql += " AND p.status=?"
        args.append(status)
    if query:
        q = query.strip().lower()
        sql += (" AND (LOWER(p.name) LIKE ? OR LOWER(p.purpose) LIKE ? "
                "OR LOWER(p.path) LIKE ? OR LOWER(p.notes) LIKE ?)")
        args += [f"%{q}%"] * 4
    sql += " ORDER BY p.name"
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, args)]


def delete_project(name: str) -> bool:
    init_db()
    with get_conn() as conn:
        existed = conn.execute("SELECT 1 FROM projects WHERE name=?", (name,)).fetchone()
        conn.execute("DELETE FROM projects WHERE name=?", (name,))  # cascades
        return bool(existed)


def _normalize_remote(url: str) -> str:
    import re
    m = re.search(r"github\.com[:/]([^/]+/[^/.]+)", url or "")
    return f"github.com/{m.group(1)}" if m else (url or "")


def resolve_project(path: str = "", remote: str = "") -> str | None:
    """Best-effort project-name lookup for callers (e.g. a git hook) that only
    know a filesystem path and/or a remote URL, not the registry name. Exact
    path match wins; otherwise the project whose recorded path is a parent
    directory of `path`; otherwise a normalized-remote match (protocol- and
    .git-suffix-insensitive). Returns None rather than guessing on no match."""
    init_db()
    path = str(Path(path).resolve()) if path else ""
    remote_norm = _normalize_remote(remote)
    with get_conn() as conn:
        rows = conn.execute("SELECT name, path, remote FROM projects").fetchall()
    if path:
        for r in rows:
            if r["path"] and r["path"] == path:
                return r["name"]
        best = None
        for r in rows:
            if (r["path"] and (path == r["path"] or path.startswith(r["path"] + "/"))
                    and (best is None or len(r["path"]) > len(best["path"]))):
                best = r
        if best:
            return best["name"]
    if remote_norm:
        for r in rows:
            if _normalize_remote(r["remote"]) == remote_norm:
                return r["name"]
    return None


# --------------------------------------------------------------------------- #
# files (memory / llms.txt / scripts / docs)
# --------------------------------------------------------------------------- #

def add_file(project: str, path: str, file_type: str = "other", description: str = "") -> dict:
    _check(file_type, VALID_FILE_TYPES, "file_type")
    init_db()
    with get_conn() as conn:
        if not conn.execute("SELECT 1 FROM projects WHERE name=?", (project,)).fetchone():
            raise ValueError(f"no such project: {project!r} (upsert it first)")
        conn.execute(
            "INSERT INTO project_files (project, file_type, path, description) VALUES (?,?,?,?) "
            "ON CONFLICT(project, path) DO UPDATE SET file_type=excluded.file_type, "
            "description=excluded.description",
            (project, file_type, path, description),
        )
    return {"project": project, "path": path, "file_type": file_type}


# --------------------------------------------------------------------------- #
# activations — the whole point: how do I start this thing again?
# --------------------------------------------------------------------------- #

def set_activation(project: str, command: str, label: str = "default",
                    description: str = "") -> dict:
    init_db()
    with get_conn() as conn:
        if not conn.execute("SELECT 1 FROM projects WHERE name=?", (project,)).fetchone():
            raise ValueError(f"no such project: {project!r} (upsert it first)")
        conn.execute(
            "INSERT INTO activations (project, label, command, description) VALUES (?,?,?,?) "
            "ON CONFLICT(project, label) DO UPDATE SET command=excluded.command, "
            "description=excluded.description",
            (project, label, command, description),
        )
    return {"project": project, "label": label, "command": command}


def get_activations(project: str) -> list[dict]:
    init_db()
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT label, command, description FROM activations WHERE project=? ORDER BY label",
            (project,))]


# --------------------------------------------------------------------------- #
# outstanding items
# --------------------------------------------------------------------------- #

def add_outstanding(project: str, description: str, severity: str = "medium") -> dict:
    _check(severity, VALID_SEVERITY, "severity")
    init_db()
    now = _now()
    with get_conn() as conn:
        if not conn.execute("SELECT 1 FROM projects WHERE name=?", (project,)).fetchone():
            raise ValueError(f"no such project: {project!r} (upsert it first)")
        cur = conn.execute(
            "INSERT INTO outstanding (project, description, severity, status, created_at) "
            "VALUES (?,?,?, 'open', ?)",
            (project, description, severity, now),
        )
        conn.execute(
            "INSERT INTO activity_log (project, action, detail, ts) VALUES (?,?,?,?)",
            (project, "outstanding_added", description[:200], now),
        )
        return {"id": cur.lastrowid, "project": project, "status": "open"}


def resolve_outstanding(item_id: int, note: str = "") -> dict:
    init_db()
    now = _now()
    with get_conn() as conn:
        row = conn.execute("SELECT project, description FROM outstanding WHERE id=?",
                            (item_id,)).fetchone()
        if row is None:
            return {"id": item_id, "resolved": False, "error": "no such item"}
        conn.execute("UPDATE outstanding SET status='resolved', resolved_at=? WHERE id=?",
                     (now, item_id))
        conn.execute(
            "INSERT INTO activity_log (project, action, detail, ts) VALUES (?,?,?,?)",
            (row["project"], "outstanding_resolved", note or row["description"][:200], now),
        )
    return {"id": item_id, "resolved": True}


def list_outstanding(project: str = "", status: str = "open") -> list[dict]:
    init_db()
    sql = ("SELECT id, project, description, severity, status, created_at, resolved_at "
           "FROM outstanding WHERE 1=1")
    args: list = []
    if project:
        sql += " AND project=?"
        args.append(project)
    if status and status != "all":
        sql += " AND status=?"
        args.append(status)
    sql += f" ORDER BY (status='open') DESC, {_SEVERITY_ORDER_SQL}, created_at"
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, args)]


# --------------------------------------------------------------------------- #
# activity log — the master record of actions taken on a project
# --------------------------------------------------------------------------- #

def log_action(project: str, action: str, detail: str = "") -> dict:
    init_db()
    now = _now()
    with get_conn() as conn:
        if not conn.execute("SELECT 1 FROM projects WHERE name=?", (project,)).fetchone():
            raise ValueError(f"no such project: {project!r} (upsert it first)")
        conn.execute(
            "INSERT INTO activity_log (project, action, detail, ts) VALUES (?,?,?,?)",
            (project, action, detail, now),
        )
    return {"project": project, "action": action, "ts": now}


def get_activity(project: str, limit: int = 50) -> list[dict]:
    init_db()
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT action, detail, ts FROM activity_log WHERE project=? "
            "ORDER BY ts DESC LIMIT ?", (project, max(1, min(int(limit), 500))))]


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _print(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init")
    p.set_defaults(fn=lambda a: (init_db(), _print({"ok": True})))

    p = sub.add_parser("upsert")
    p.add_argument("name")
    p.add_argument("--kind", default="repo")
    p.add_argument("--path", default="")
    p.add_argument("--remote", default="")
    p.add_argument("--purpose", default="")
    p.add_argument("--status", default="active")
    p.add_argument("--notes", default="")
    p.set_defaults(fn=lambda a: _print(upsert_project(
        a.name, a.kind, a.path, a.remote, a.purpose, a.status, a.notes)))

    p = sub.add_parser("get")
    p.add_argument("name")
    p.set_defaults(fn=lambda a: _print(get_project(a.name) or {"error": "not found"}))

    p = sub.add_parser("list")
    p.add_argument("--kind", default="")
    p.add_argument("--query", default="")
    p.add_argument("--status", default="")
    p.set_defaults(fn=lambda a: _print(list_projects(a.kind, a.query, a.status)))

    p = sub.add_parser("delete")
    p.add_argument("name")
    p.set_defaults(fn=lambda a: _print({"deleted": delete_project(a.name)}))

    p = sub.add_parser("resolve")
    p.add_argument("--path", default="")
    p.add_argument("--remote", default="")
    p.set_defaults(fn=lambda a: _print({"name": resolve_project(a.path, a.remote)}))

    p = sub.add_parser("add-file")
    p.add_argument("project")
    p.add_argument("path")
    p.add_argument("--type", dest="file_type", default="other")
    p.add_argument("--description", default="")
    p.set_defaults(fn=lambda a: _print(add_file(a.project, a.path, a.file_type, a.description)))

    p = sub.add_parser("set-activation")
    p.add_argument("project")
    p.add_argument("command")
    p.add_argument("--label", default="default")
    p.add_argument("--description", default="")
    p.set_defaults(fn=lambda a: _print(set_activation(
        a.project, a.command, a.label, a.description)))

    p = sub.add_parser("activations")
    p.add_argument("project")
    p.set_defaults(fn=lambda a: _print(get_activations(a.project)))

    p = sub.add_parser("add-outstanding")
    p.add_argument("project")
    p.add_argument("description")
    p.add_argument("--severity", default="medium")
    p.set_defaults(fn=lambda a: _print(add_outstanding(a.project, a.description, a.severity)))

    p = sub.add_parser("resolve-outstanding")
    p.add_argument("id", type=int)
    p.add_argument("--note", default="")
    p.set_defaults(fn=lambda a: _print(resolve_outstanding(a.id, a.note)))

    p = sub.add_parser("outstanding")
    p.add_argument("--project", default="")
    p.add_argument("--status", default="open")
    p.set_defaults(fn=lambda a: _print(list_outstanding(a.project, a.status)))

    p = sub.add_parser("log")
    p.add_argument("project")
    p.add_argument("action")
    p.add_argument("--detail", default="")
    p.set_defaults(fn=lambda a: _print(log_action(a.project, a.action, a.detail)))

    p = sub.add_parser("activity")
    p.add_argument("project")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(fn=lambda a: _print(get_activity(a.project, a.limit)))

    args = ap.parse_args()
    try:
        args.fn(args)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
