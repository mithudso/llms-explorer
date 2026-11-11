"""Durable local optimization requests and explicit bounded scheduling policies."""

from __future__ import annotations

import json
import secrets
import shutil
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from .bundles import MAX_FILE_BYTES, _metadata
from .util import atomic, canonical, read_bounded, sha

OPTIMIZERS = {"skill": "skill-optimizer", "code": "code-deep-optimizer",
              "document": "ddo", "query": "deep-query-optimizer",
              "prompt": "prompt-deep-optimizer", "agent": "agent-deep-optimizer"}


def artifact_snapshot(kind: str, target: Path | None, input_text: str | None):
    """Bind a skill's complete approved tree, or a generic artifact's exact bytes."""
    if kind not in OPTIMIZERS or (target is None) == (input_text is None):
        raise ValueError("Supply a supported kind and exactly one target or input_text")
    if target is not None:
        target = Path(target).expanduser().resolve(strict=True)
        raw = read_bounded(target, MAX_FILE_BYTES)
        filename = target.name
    else:
        if not isinstance(input_text, str):
            raise ValueError("input_text must be a UTF-8 string")
        raw = input_text.encode()
        filename = "SKILL.md" if kind == "skill" else "artifact.txt"
    if not raw or len(raw) > MAX_FILE_BYTES:
        raise ValueError("Optimizer input must be nonempty and at most 2 MiB")
    raw.decode("utf-8")
    if kind == "skill" and target is not None:
        if filename != "SKILL.md":
            raise ValueError("A skill target must be its SKILL.md entrypoint")
        from .bundles import build_bundle, validate_bundle
        manifest, archive = build_bundle(target.parent, "local", "optimization-input", "0.0.0")
        _, files = validate_bundle(archive)
        return filename, files, manifest["release_sha256"]
    if kind == "skill":
        # Text-only skill requests have no supporting resources. The inventory
        # still uses the same explicit tree identity rather than a file hash.
        _metadata(raw)
        return filename, {filename: raw}, sha(canonical({filename: sha(raw)}))
    return filename, {filename: raw}, sha(raw)


def snapshot_identity(kind: str, root: Path, filename: str, *, text_only=False) -> str:
    if kind == "skill" and not text_only:
        from .bundles import build_bundle
        return build_bundle(root, "local", "optimization-input", "0.0.0")[0]["release_sha256"]
    raw = read_bounded(root / filename, MAX_FILE_BYTES)
    return sha(canonical({filename: sha(raw)})) if kind == "skill" else sha(raw)


class Jobs:
    def __init__(self, state: Path):
        self.state = Path(state).expanduser().absolute()
        self.state.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.database = self.state / "jobs.sqlite3"
        with self.connect() as db:
            db.executescript("""
              CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, kind TEXT NOT NULL, target TEXT, input_sha256 TEXT NOT NULL,
                params TEXT NOT NULL, status TEXT NOT NULL, created_at REAL NOT NULL,
                worker TEXT, lease_token TEXT, lease_until REAL, result TEXT, cancel_requested INTEGER DEFAULT 0);
              CREATE TABLE IF NOT EXISTS policies (
                skill_id TEXT PRIMARY KEY, enabled INTEGER NOT NULL, interval_seconds INTEGER NOT NULL,
                max_iterations INTEGER NOT NULL, timeout_seconds INTEGER NOT NULL);
              CREATE UNIQUE INDEX IF NOT EXISTS one_active_skill_job
                ON jobs(json_extract(params,'$.skill_id'))
                WHERE kind='skill' AND status IN ('queued','running','interrupted')
                AND json_extract(params,'$.skill_id')!='';
            """)
        self.database.chmod(0o600)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.database, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def enqueue(self, kind: str, *, target: Path | None = None, input_text: str | None = None,
                expected_sha256: str = "", timeout_seconds: int = 600, max_iterations: int = 3,
                skill_id: str = "", definition: Path | None = None) -> dict:
        if kind not in OPTIMIZERS:
            raise ValueError("Unsupported artifact kind")
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 3600:
            raise ValueError("timeout_seconds must be 1..3600")
        if type(max_iterations) is not int or not 1 <= max_iterations <= 5:
            raise ValueError("max_iterations must be 1..5")
        filename, files, digest = artifact_snapshot(kind, target, input_text)
        target = Path(target).expanduser().resolve(strict=True) if target is not None else None
        if expected_sha256 and digest != expected_sha256:
            raise ValueError("REVISION_CONFLICT: input no longer matches the requested version")
        jid = uuid.uuid4().hex
        workspace = self.state / "runs" / jid
        workspace.mkdir(parents=True, mode=0o700)
        for path, raw in files.items():
            atomic(workspace / "original" / path, raw)
            atomic(workspace / "candidate" / path, raw)
            if target is not None and kind == "skill" and (target.parent / path).stat().st_mode & 0o111:
                (workspace / "original" / path).chmod(0o700)
                (workspace / "candidate" / path).chmod(0o700)
        params = {"schema": "optimization-job/v1", "optimizer_id": OPTIMIZERS[kind],
                  "filename": filename, "timeout_seconds": timeout_seconds,
                  "max_iterations": max_iterations, "skill_id": skill_id,
                  "text_only": target is None,
                  "workspace": str(workspace.resolve()),
                  "snapshot_files": {p: sha(b) for p, b in sorted(files.items())},
                  "definition": str(Path(definition).resolve(strict=True)) if definition else None}
        try:
            with self.connect() as db:
                db.execute("INSERT INTO jobs(id,kind,target,input_sha256,params,status,created_at) "
                           "VALUES (?,?,?,?,?,'queued',?)", (jid, kind, str(target) if target else None,
                           digest, json.dumps(params), time.time()))
        except sqlite3.IntegrityError:
            shutil.rmtree(workspace)
            raise ValueError("A job for this skill is already queued, running or interrupted") from None
        return self.get(jid)

    def get(self, jid: str, *, include_lease: bool = False) -> dict:
        with self.connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
        if row is None:
            raise KeyError("No such optimization job")
        record = dict(row)
        record["params"] = json.loads(record["params"])
        record["result"] = json.loads(record["result"]) if record["result"] else None
        if not include_lease:
            record.pop("lease_token")
        return record

    def list(self, limit: int = 20) -> list[dict]:
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("limit must be 1..100")
        with self.connect() as db:
            ids = [r[0] for r in db.execute("SELECT id FROM jobs ORDER BY created_at DESC LIMIT ?",
                                          (limit,))]
        return [self.get(jid) for jid in ids]

    def claim(self, worker: str, jid: str | None = None) -> dict | None:
        if not isinstance(worker, str) or not 1 <= len(worker) <= 100:
            raise ValueError("worker must be 1..100 characters")
        now = time.time()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            # Expired execution is uncertain, not proof that running side effects
            # stopped. Require recovery to inspect its private workspace explicitly.
            db.execute("UPDATE jobs SET status='interrupted',lease_token=NULL WHERE status='running' "
                       "AND lease_until<?", (now,))
            row = db.execute("SELECT id,params FROM jobs WHERE status='queued' "
                             "AND (? IS NULL OR id=?) ORDER BY created_at LIMIT 1", (jid, jid)).fetchone()
            if row is None:
                return None
            timeout = json.loads(row["params"])["timeout_seconds"]
            token = secrets.token_urlsafe(32)
            db.execute("UPDATE jobs SET status='running',worker=?,lease_token=?,lease_until=? WHERE id=?",
                       (worker, token, now + timeout + 60, row["id"]))
            jid = row["id"]
        return self.get(jid, include_lease=True)

    def complete(self, jid: str, worker: str, lease_token: str, result: dict,
                 *, status: str = "executed") -> dict:
        if status not in {"executed", "failed", "cancelled"}:
            raise ValueError("Invalid completion status")
        if not isinstance(result, dict) or len(canonical(result)) > 128 * 1024:
            raise ValueError("Invalid or oversized optimizer result")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
            if (row is None or row["status"] != "running" or row["worker"] != worker
                    or not secrets.compare_digest(row["lease_token"] or "", lease_token)
                    or (row["lease_until"] < time.time() and status not in {"failed", "cancelled"})):
                raise ValueError("Optimizer lease is missing, expired or owned by another worker")
            if result.get("input_sha256") != row["input_sha256"]:
                raise ValueError("Optimizer result does not bind the original input")
            if row["cancel_requested"]:
                status = "cancelled"
                result = dict(result, cancelled=True, candidate_ready=False,
                              cancellation_outcome="accepted-before-completion")
            db.execute("UPDATE jobs SET status=?,result=?,lease_token=NULL,lease_until=NULL WHERE id=?",
                       (status, json.dumps(result), jid))
        return self.get(jid)

    def cancel(self, jid: str) -> dict:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status FROM jobs WHERE id=?", (jid,)).fetchone()
            if row is None:
                raise KeyError("No such optimization job")
            if row[0] == "queued":
                db.execute("UPDATE jobs SET status='cancelled',cancel_requested=1 WHERE id=?", (jid,))
            elif row[0] == "running":
                db.execute("UPDATE jobs SET cancel_requested=1 WHERE id=?", (jid,))
            accepted = row[0] in {"queued", "running"}
        return dict(self.get(jid), cancel_outcome="accepted" if accepted else "too_late")

    def retry(self, jid: str) -> dict:
        """Explicit recovery creates a new workspace and preserves the prior attempt."""
        record = self.get(jid)
        if record["status"] not in {"failed", "cancelled", "interrupted"}:
            raise ValueError("Only failed, cancelled or interrupted attempts can be retried")
        if record["status"] == "interrupted":
            with self.connect() as db:
                db.execute("UPDATE jobs SET status='cancelled',cancel_requested=1,lease_token=NULL "
                           "WHERE id=? AND status='interrupted'", (jid,))
        original = self.state / "runs" / jid / "original" / record["params"]["filename"]
        if snapshot_identity(record["kind"], original.parent, original.name,
                text_only=record["params"]["text_only"]) != record["input_sha256"]:
            raise ValueError("Original snapshot changed; cannot recover this input")
        # A new workspace isolates any uncertain old worker. No replay shares a
        # mutable candidate directory or overwrites the source installation.
        arguments = ({"input_text": original.read_text()} if record["params"]["text_only"]
                     else {"target": original})
        new = self.enqueue(record["kind"], **arguments,
                           timeout_seconds=record["params"]["timeout_seconds"],
                           max_iterations=record["params"]["max_iterations"],
                           skill_id=record["params"]["skill_id"],
                           definition=Path(record["params"]["definition"]) if record["params"]["definition"] else None)
        with self.connect() as db:
            params = dict(new["params"], retry_of=jid, source_target=record["target"])
            db.execute("UPDATE jobs SET params=? WHERE id=?", (json.dumps(params), new["id"]))
        return self.get(new["id"])

    def policy(self, skill_id: str, *, enabled: bool, interval_seconds: int = 86400,
               max_iterations: int = 3, timeout_seconds: int = 600) -> dict:
        if (not isinstance(skill_id, str) or len(skill_id) > 100 or type(enabled) is not bool
                or type(interval_seconds) is not int or not 60 <= interval_seconds <= 31_536_000
                or type(max_iterations) is not int or not 1 <= max_iterations <= 5
                or type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 3600):
            raise ValueError("Invalid bounded automatic optimization policy")
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO policies VALUES (?,?,?,?,?)",
                       (skill_id, int(enabled), interval_seconds, max_iterations, timeout_seconds))
        return {"skill_id": skill_id, "enabled": enabled, "interval_seconds": interval_seconds,
                "max_iterations": max_iterations, "timeout_seconds": timeout_seconds}

    def schedule(self, catalog, *, max_jobs: int = 1) -> dict:
        if type(max_jobs) is not int or not 1 <= max_jobs <= 10:
            raise ValueError("max_jobs must be 1..10")
        catalog.refresh()
        with self.connect() as db:
            policies = [dict(row) for row in db.execute("SELECT * FROM policies WHERE enabled=1")]
            history = [dict(row) for row in db.execute("SELECT input_sha256,params,status,created_at FROM jobs")]
        queued, skipped, errors = [], [], []
        for policy in policies:
            if len(queued) >= max_jobs:
                break
            sid = policy["skill_id"]
            try:
                skill = catalog.load(sid)
                if not any(a["writable"] for a in skill["installations"]):
                    raise ValueError("Read-only plugin sources are not automatic rewrite targets")
                previous = [r for r in history if json.loads(r["params"]).get("skill_id") == sid]
                if any(r["status"] in {"queued", "running", "interrupted"} for r in previous):
                    skipped.append(sid)
                    continue
                latest = max(previous, key=lambda r: r["created_at"]) if previous else None
                identity = artifact_snapshot("skill", Path(skill["path"]), None)[2]
                if (latest and latest["input_sha256"] == identity
                        and time.time() - latest["created_at"] < policy["interval_seconds"]):
                    skipped.append(sid)
                    continue
                exact = catalog.resolve_exact(OPTIMIZERS["skill"], refresh=False)
                definition = Path(exact["path"]) if exact else None
                if definition is None:
                    raise ValueError("Installed skill-optimizer definition is required")
                job = self.enqueue("skill", target=Path(skill["path"]),
                                   expected_sha256=identity,
                                   timeout_seconds=policy["timeout_seconds"],
                                   max_iterations=policy["max_iterations"], skill_id=sid,
                                   definition=definition)
                queued.append(job["id"])
            except (ValueError, KeyError, OSError) as exc:
                errors.append({"skill_id": sid, "error": str(exc)})
        return {"queued": queued, "skipped": skipped, "errors": errors,
                "limit": max_jobs, "execution": "Use an explicitly configured trusted local worker"}

    def structural_check(self, record: dict) -> dict:
        path = self.state / "runs" / record["id"] / "candidate" / record["params"]["filename"]
        data = read_bounded(path, MAX_FILE_BYTES)
        if not data.strip():
            raise ValueError("Optimizer produced an empty candidate")
        data.decode("utf-8")
        if record["kind"] == "skill":
            _metadata(data)
        return {"name": "nonempty-utf8-and-skill-frontmatter", "exit_code": 0,
                "scope": "structural; does not establish native optimizer convergence"}
