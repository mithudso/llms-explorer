"""Small private-file and content identity primitives."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(prefix=".registry-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def read_bounded(path: Path, limit: int) -> bytes:
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"File exceeds {limit} bytes: {path}")
    return data


def validate_workspace(workspace: Path, expected: str | Path | None = None) -> Path:
    """Keep candidate and original roots within the job's immutable canonical base."""
    canonical_base = Path(expected) if expected else workspace.resolve(strict=True)
    if workspace.is_symlink() or workspace.resolve(strict=True) != canonical_base:
        raise ValueError("Optimization workspace changed its canonical location")
    for name in ("original", "candidate"):
        root = workspace / name
        if root.is_symlink() or not root.is_dir() or root.resolve(strict=True) != canonical_base / name:
            raise ValueError(f"Optimization {name} root escaped its canonical workspace")
    return canonical_base
