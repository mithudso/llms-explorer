#!/usr/bin/env python3
"""Archive oversized workflow logs and retain their newest complete version sections."""

import argparse
import logging
import os
import re
import stat
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_DIR = ROOT / "docs" / "archive"
MAX_BYTES = 200 * 1024
LOGGER = logging.getLogger(__name__)
VERSION_HEADER = re.compile(r"^## (?:Prompt v|v)\d")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def _retained_text(text: str) -> str:
    """Keep the preamble and newest sections, leaving room for future entries."""
    starts = []
    offset = 0
    fence = None
    for line in text.splitlines(keepends=True):
        marker = FENCE.match(line)
        if fence:
            if (marker and marker[1][0] == fence[0]
                    and len(marker[1]) >= fence[1] and not marker[2].strip()):
                fence = None
        elif marker:
            fence = (marker[1][0], len(marker[1]))
        elif VERSION_HEADER.match(line):
            starts.append(offset)
        offset += len(line)
    if not starts:
        raise ValueError("No versioned sections; refusing to truncate the log")
    sections = [text[start:end] for start, end in zip(starts, starts[1:] + [len(text)])]
    retained = text[:starts[0]] + sections[0]
    if len(retained.encode("utf-8")) > MAX_BYTES:
        raise ValueError("Newest version section exceeds the limit; preserving the log")
    for section in sections[1:]:
        if len((retained + section).encode("utf-8")) > MAX_BYTES // 2:
            break
        retained += section
    return retained


def _check_editor_files(filename: str) -> None:
    swaps = list(ROOT.glob(f".{filename}.sw?")) + list(ROOT.glob(f"{filename}.sw?"))
    locks = [ROOT / f".#{filename}", ROOT / f"#{filename}#"]
    if swaps or any(os.path.lexists(path) for path in locks):
        raise RuntimeError("An editor swap or lock file exists; refusing rotation")


def rotate_if_needed(filename: str) -> None:
    """Save an exclusive full preimage before atomically shortening one known log."""
    temporary = None
    lock = None
    try:
        if filename not in {"memory.md", "prompts.md"}:
            raise ValueError("Only memory.md and prompts.md can be rotated")
        path = ROOT / filename
        if path.is_symlink():
            raise ValueError("Refusing to rotate a symlink")
        if not path.exists() or path.stat().st_size <= MAX_BYTES:
            return
        _check_editor_files(filename)
        lock_path = ROOT / f".{filename}.rotate.lock"
        try:
            lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise RuntimeError("Another workflow log rotation is active") from None
        lock = lock_path
        os.close(lock_fd)
        original = path.read_bytes()
        retained = _retained_text(original.decode("utf-8")).encode("utf-8")
        mode = stat.S_IMODE(path.stat().st_mode)
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=f"{path.stem}_{timestamp}_", suffix=path.suffix,
            dir=ARCHIVE_DIR, delete=False,
        ) as archive:
            archive_path = Path(archive.name)
            os.fchmod(archive.fileno(), mode)
            archive.write(original)
            archive.flush()
            os.fsync(archive.fileno())
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=f".{filename}.", suffix=".tmp", dir=ROOT, delete=False,
        ) as output:
            temporary = Path(output.name)
            os.fchmod(output.fileno(), mode)
            output.write(retained)
            output.flush()
            os.fsync(output.fileno())
        _check_editor_files(filename)
        if path.is_symlink() or path.read_bytes() != original:
            raise RuntimeError("The workflow log changed during rotation; preserving it")
        os.replace(temporary, path)
        LOGGER.info("workflow_log_rotated log=%s archive=%s bytes_before=%d bytes_after=%d",
                    filename, archive_path.relative_to(ROOT), len(original), len(retained))
    except (OSError, ValueError, RuntimeError) as error:
        LOGGER.error("workflow_log_rotation_failed log=%s error=%s reason=%s",
                     filename, type(error).__name__, error)
        raise
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        if lock is not None:
            lock.unlink(missing_ok=True)


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        rotate_if_needed("memory.md")
        rotate_if_needed("prompts.md")
    except (OSError, ValueError, RuntimeError):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
