#!/usr/bin/env python3
"""Rotate memory.md and prompts.md if they exceed 200KB."""

import shutil
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_DIR = ROOT / "docs" / "archive"
MAX_BYTES = 200 * 1024  # 200 KB


def rotate_if_needed(filename: str) -> None:
    path = ROOT / filename
    if not path.exists():
        return
    if path.stat().st_size > MAX_BYTES:
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        dest = ARCHIVE_DIR / f"{path.stem}_{ts}{path.suffix}"
        shutil.copy2(path, dest)
        print(f"Rotated {filename} to {dest.relative_to(ROOT)}")


def main() -> None:
    rotate_if_needed("memory.md")
    rotate_if_needed("prompts.md")


if __name__ == "__main__":
    main()
