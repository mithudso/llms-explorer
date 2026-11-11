"""Save bounded, source-grounded research before refreshing its query projection.

Quotation matching is a mechanical integrity check, never semantic validation.
The canonical pack remains saved if graph or embedding refresh cannot finish.
"""

from __future__ import annotations

import contextlib
import ctypes
from datetime import datetime, UTC
import fcntl
import hashlib
import json
import logging
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
from urllib.parse import urlsplit
from uuid import uuid4

ROOT = Path.home() / ".global-ai-hub/llms-concepts"
CREATOR = "research-expertise-capture/1"
_RESERVED = {"draft", "drafts", "staging", "tmp", "temp", "backup", "backups"}
_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_SOURCE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,49}\Z")
_LOG = logging.getLogger(__name__)


def _bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _text(value, name, maximum, *, strip=True):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{name} must contain 1..{maximum} characters")
    return value.strip() if strip else value


def _object(value, keys, name):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f"{name} requires exactly: {', '.join(keys)}")


def _normalize(slug, title, question, summary, findings, sources):
    slug = _text(slug, "slug", 100)
    if slug in _RESERVED:
        raise ValueError("slug is reserved and excluded from the canonical corpus")
    if not _SLUG.fullmatch(slug):
        raise ValueError("slug must use lowercase letters, digits and single hyphens")
    title = _text(title, "title", 200)
    question = _text(question, "question", 2000)
    summary = _text(summary, "summary", 6000)
    if not isinstance(sources, list) or not 1 <= len(sources) <= 8:
        raise ValueError("sources must contain 1..8 source objects")
    if not isinstance(findings, list) or not 1 <= len(findings) <= 20:
        raise ValueError("findings must contain 1..20 finding objects")
    clean_sources, source_map, source_filenames = [], {}, set()
    for source in sources:
        _object(source, ("id", "url", "title", "content"), "source")
        sid = _text(source["id"], "source.id", 50)
        if not _SOURCE_ID.fullmatch(sid) or sid in source_map:
            raise ValueError(
                "source.id must be unique and use letters, digits, underscore or hyphen"
            )
        if sid.casefold() in source_filenames:
            raise ValueError("source.id must be unique on case-insensitive filesystems")
        source_filenames.add(sid.casefold())
        url = _text(source["url"], "source.url", 2048)
        try:
            parsed = urlsplit(url)
            valid = parsed.scheme in ("http", "https") and parsed.hostname
            valid = valid and not parsed.username and not parsed.password
        except ValueError:
            valid = False
        if not valid:
            raise ValueError("source.url must be an HTTP(S) URL without embedded credentials")
        cleaned = {
            "id": sid,
            "url": url,
            "title": _text(source["title"], "source.title", 300),
            "content": _text(source["content"], "source.content", 150000, strip=False),
        }
        source_map[sid] = cleaned
        clean_sources.append(cleaned)
    clean_findings, used = [], set()
    for finding in findings:
        _object(finding, ("text", "source_ids", "quotes"), "finding")
        text = _text(finding["text"], "finding.text", 3000)
        ids = finding["source_ids"]
        if (
            not isinstance(ids, list)
            or not 1 <= len(ids) <= 8
            or any(not isinstance(sid, str) or sid not in source_map for sid in ids)
            or len(set(ids)) != len(ids)
        ):
            raise ValueError("finding.source_ids must identify 1..8 unique supplied sources")
        quotes = finding["quotes"]
        if not isinstance(quotes, list) or not 1 <= len(quotes) <= 8:
            raise ValueError("finding.quotes must contain 1..8 quotation objects")
        clean_quotes, quoted = [], set()
        for quote in quotes:
            _object(quote, ("source_id", "quote"), "quotation")
            sid = quote["source_id"]
            if not isinstance(sid, str) or sid not in ids:
                raise ValueError("quotation.source_id must identify a source cited by its finding")
            text_quote = _text(quote["quote"], "quotation.quote", 4000, strip=False)
            if text_quote not in source_map[sid]["content"]:
                raise ValueError(f"Quotation does not match the supplied source snapshot: {sid}")
            quoted.add(sid)
            clean_quotes.append({"source_id": sid, "quote": text_quote})
        if quoted != set(ids):
            raise ValueError("Every source cited by a finding requires an exact quotation")
        used.update(ids)
        clean_findings.append({"text": text, "source_ids": ids, "quotes": clean_quotes})
    if used != set(source_map):
        raise ValueError("Every supplied source must support at least one finding")
    value = {
        "slug": slug,
        "title": title,
        "question": question,
        "summary": summary,
        "findings": clean_findings,
        "sources": clean_sources,
    }
    if len(_bytes(value)) > 1500000:
        raise ValueError("Research capture exceeds the 1,500,000-byte input limit")
    return value


def _safe_member(name):
    if not isinstance(name, str):
        raise ValueError("Manifest member names must be relative paths")
    path = PurePosixPath(name)
    if path.is_absolute() or not path.parts or any(p in (".", "..") for p in path.parts):
        raise ValueError("Manifest member escapes canonical pack")
    if str(path) != name or "\\" in name or name == "manifest.json":
        raise ValueError("Invalid manifest member path")
    return path


def _existing(pack):
    if pack.is_symlink() or not pack.is_dir():
        raise FileExistsError("Existing canonical pack is not an owned directory")
    paths = list(pack.rglob("*"))
    if any(p.is_symlink() for p in paths):
        raise ValueError("Canonical pack contains a symlink")
    manifest_path = pack / "manifest.json"
    if not manifest_path.is_file():
        raise FileExistsError("Refusing to overwrite an existing unowned canonical pack")
    raw = manifest_path.read_bytes()
    try:
        manifest = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("REVISION_CONFLICT: existing manifest is invalid") from exc
    if not isinstance(manifest, dict) or manifest.get("creator") != CREATOR:
        raise FileExistsError("Refusing to overwrite an existing unowned canonical pack")
    members = manifest.get("members")
    if not isinstance(members, dict) or not {"capture.json", "llms.txt", "llms-facts.txt"} <= set(
        members
    ):
        raise ValueError("REVISION_CONFLICT: capture manifest has no complete member inventory")
    actual = {p.relative_to(pack).as_posix() for p in paths if p.is_file()}
    if actual != set(members) | {"manifest.json"}:
        raise ValueError("REVISION_CONFLICT: canonical pack member inventory changed")
    for name, sha in members.items():
        relative = _safe_member(name)
        if _sha((pack / relative).read_bytes()) != sha:
            raise ValueError(f"REVISION_CONFLICT: canonical member changed: {name}")
    return manifest, _sha(raw)


def validate_capture_pack(pack):
    """Return the manifest/checksum only while every captured member is intact.

    Callers may treat ValueError/OSError as a stale capture. This function does
    not import Store and can be used by retrieval-time freshness checks.
    """
    return _existing(Path(pack))


class CaptureConflict(ValueError):
    """A conflicting revision remains preserved at retained_path."""

    def __init__(self, message, retained_path):
        self.retained_path = str(retained_path)
        super().__init__(f"REVISION_CONFLICT: {message}; retained_path={retained_path}")


def _kernel_rename(source, target, *, exchange=False):
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin":
        rename = libc.renamex_np
        rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        arguments = (os.fsencode(source), os.fsencode(target), 2 if exchange else 4)
    elif hasattr(libc, "renameat2"):
        rename = libc.renameat2
        rename.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        arguments = (-100, os.fsencode(source), -100, os.fsencode(target), 2 if exchange else 1)
    else:
        raise NotImplementedError("This host has no atomic directory publication primitive")
    rename.restype = ctypes.c_int
    if rename(*arguments) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(target))


def _atomic_publish(stage, target, expected_checksum):
    """Exchange complete revisions, or create with kernel no-clobber semantics."""
    if expected_checksum:
        _, checksum = _existing(target)
        if checksum != expected_checksum:
            raise ValueError("REVISION_CONFLICT: canonical manifest changed before publication")
    _kernel_rename(stage, target, exchange=bool(expected_checksum))


def _retain_revision(stage, state, slug):
    history = state / "capture-history" / slug
    for directory in (state / "capture-history", history):
        if directory.is_symlink():
            raise CaptureConflict("Revision history directory is a symlink", stage)
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    destination = history / uuid4().hex
    try:
        _kernel_rename(stage, destination)
    except OSError as exc:
        # Never copy and remove: a manual editor may still hold an open descriptor
        # to this directory's files. Keep that exact inode if archival cannot move.
        raise CaptureConflict("Previous revision could not move to history", stage) from exc
    return destination


def _confirm_indexed(store, pack, checksum):
    from .store import CORPUS

    manifest, current_checksum = validate_capture_pack(pack)
    if current_checksum != checksum:
        raise ValueError("Canonical capture changed during index refresh")
    rows = store.read(
        "MATCH (d:RXDocument {corpus:$corpus,active:true,path:$path,sha256:$sha,"
        "manifest_sha256:$manifest}) OPTIONAL MATCH (d)-[:RX_HAS_PASSAGE]->(p:RXPassage) "
        "RETURN d.id AS id,count(p) AS passages,count(p.embedding) AS vectors",
        corpus=CORPUS,
        path=str(pack / "llms-facts.txt"),
        sha=manifest["members"]["llms-facts.txt"],
        manifest=checksum,
    )
    if (
        len(rows) != 1
        or rows[0].get("passages", 0) < 1
        or rows[0].get("passages") != rows[0].get("vectors")
    ):
        raise RuntimeError("Saved canonical document was not confirmed in the graph")
    return rows[0]


def _render(payload, captured_at):
    sources = {source["id"]: source for source in payload["sources"]}
    lines = [
        f"# {payload['title']}",
        "",
        "> Qualification: unreviewed. Captured research; "
        "quotation matching does not establish semantic support.",
        "",
        f"Captured: {captured_at}",
        "",
        "## Question",
        "",
        payload["question"],
        "",
        "## Summary",
        "",
        payload["summary"],
        "",
        "## Findings",
        "",
    ]
    for number, finding in enumerate(payload["findings"], 1):
        urls = " ".join(f"[{sid}]({sources[sid]['url']})" for sid in finding["source_ids"])
        lines.extend([f"{number}. {finding['text']} {urls}", ""])
    lines.extend(["## Evidence quotations", ""])
    for number, finding in enumerate(payload["findings"], 1):
        for quote in finding["quotes"]:
            sid = quote["source_id"]
            source = sources[sid]
            lines.extend(
                [
                    f"### Finding {number} / {sid}",
                    "",
                    *["> " + line for line in quote["quote"].splitlines()],
                    "",
                    f"Source: {source['url']}",
                    f"Snapshot SHA256: {_sha(source['content'].encode())}",
                    "",
                ]
            )
    lines.extend(["## Sources", ""])
    for source in payload["sources"]:
        lines.extend([f"- {source['id']} — {source['title']}: {source['url']}", ""])
    body = "\n".join(lines) + "\n"
    if len(body) > 80000:
        raise ValueError("Rendered research exceeds the 80,000-character limit")
    index = (
        f"# {payload['title']}\n\n> {payload['summary']}\n\n## Research\n\n"
        "- [Research and evidence](llms-facts.txt): Findings, citations and exact quotations.\n"
        "- [Capture record](capture.json): Research inputs and source snapshot hashes.\n"
    )
    capture = {
        "schema": CREATOR,
        "captured_at": captured_at,
        "qualification": "unreviewed",
        **{k: v for k, v in payload.items() if k != "sources"},
        "sources": [
            {
                "id": source["id"],
                "url": source["url"],
                "title": source["title"],
                "path": f"sources/{source['id']}.txt",
                "sha256": _sha(source["content"].encode()),
            }
            for source in payload["sources"]
        ],
    }
    members = {
        "llms-facts.txt": body.encode(),
        "llms.txt": index.encode(),
        "capture.json": _bytes(capture),
    }
    for source in payload["sources"]:
        members[f"sources/{source['id']}.txt"] = source["content"].encode()
    return members


def save_research(
    store, slug, title, question, summary, findings, sources, expected_checksum="", *, root=ROOT
):
    """Persist canonical evidence, then index it. Never certify factual support."""
    payload = _normalize(slug, title, question, summary, findings, sources)
    if not isinstance(expected_checksum, str) or (
        expected_checksum and not re.fullmatch(r"[a-f0-9]{64}", expected_checksum)
    ):
        raise ValueError("expected_checksum must be empty or a lowercase SHA256")
    root = Path(root).expanduser()
    if root.is_symlink():
        raise ValueError("Canonical research root must not be a symlink")
    root.mkdir(parents=True, exist_ok=True)
    root = root.resolve(strict=True)
    pack = root / f"{payload['slug']}.llms"
    state = Path(store.state)
    state.mkdir(parents=True, exist_ok=True)
    lock_path = state / "capture.lock"
    lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(lock_fd, "a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        payload_sha = _sha(_bytes(payload))
        previous, checksum = None, ""
        if pack.exists() or pack.is_symlink():
            previous, checksum = _existing(pack)
            if expected_checksum and checksum != expected_checksum:
                raise ValueError("REVISION_CONFLICT: expected manifest checksum does not match")
        elif expected_checksum:
            raise ValueError("REVISION_CONFLICT: expected checksum supplied for a missing pack")
        unchanged = previous is not None and previous.get("payload_sha256") == payload_sha
        if previous is not None and not unchanged and not expected_checksum:
            raise ValueError("REVISION_CONFLICT: updating research requires expected_checksum")
        if not unchanged:
            captured_at = datetime.now(UTC).isoformat()
            members = _render(payload, captured_at)
            manifest = {
                "creator": CREATOR,
                "schema_version": 1,
                "concept": payload["title"],
                "slug": payload["slug"],
                "question": payload["question"],
                "qualification": "unreviewed",
                "research_status": "CAPTURED_UNREVIEWED",
                "captured_at": captured_at,
                "payload_sha256": payload_sha,
                "members": {name: _sha(data) for name, data in members.items()},
            }
            manifest_raw = _bytes(manifest)
            stage = Path(tempfile.mkdtemp(prefix=f".{payload['slug']}-capture-", dir=root))
            stage_identity = (stage.stat().st_dev, stage.stat().st_ino)
            retained = None
            try:
                for name, data in {**members, "manifest.json": manifest_raw}.items():
                    path = stage / name
                    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                    with path.open("xb") as handle:
                        os.chmod(path, 0o600)
                        handle.write(data)
                        handle.flush()
                        os.fsync(handle.fileno())
                _atomic_publish(stage, pack, checksum if previous else "")
                if previous is not None:
                    retained = _retain_revision(stage, state, payload["slug"])
                    try:
                        _, exchanged_checksum = _existing(retained)
                        if exchanged_checksum != checksum:
                            raise ValueError("Previous manifest changed during atomic exchange")
                    except (ValueError, OSError) as exc:
                        raise CaptureConflict(
                            "Concurrent edits detected after exchange", retained
                        ) from exc
                checksum = _sha(manifest_raw)
            finally:
                if stage.exists():
                    identity = (stage.lstat().st_dev, stage.lstat().st_ino)
                    if identity == stage_identity:
                        # This is our never-published candidate, not an old head.
                        shutil.rmtree(stage)
                    else:
                        # An exception or interrupt after exchange must not erase
                        # the exchanged-out revision or a manual editor's inode.
                        _retain_revision(stage, state, payload["slug"])
        result = {
            "slug": payload["slug"],
            "canonical_path": str(pack),
            "manifest_path": str(pack / "manifest.json"),
            "prose_path": str(pack / "llms-facts.txt"),
            "checksum": checksum,
            "payload_sha256": payload_sha,
            "qualification": "unreviewed",
            "created": previous is None,
            "updated": previous is not None and not unchanged,
            "unchanged": unchanged,
            "source_count": len(payload["sources"]),
            "finding_count": len(payload["findings"]),
        }
        if not unchanged and retained is not None:
            result["previous_revision_path"] = str(retained)
        try:
            # Ingestion progress belongs on stderr, never the MCP JSON-RPC stream.
            with contextlib.redirect_stdout(sys.stderr):
                result["index_result"] = store.ingest(root)
            result["indexed_document"] = _confirm_indexed(store, pack, checksum)
            result["indexed"] = True
        except Exception as exc:
            _LOG.warning(
                "research_capture_index_pending slug=%s error_type=%s",
                payload["slug"],
                type(exc).__name__,
                extra={"capture_slug": payload["slug"], "error_type": type(exc).__name__},
            )
            result.update(
                indexed=False,
                index_state="pending",
                index_error=type(exc).__name__,
                next_step="Retry this identical save or run explicit corpus ingestion",
            )
        return result
