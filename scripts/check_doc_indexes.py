#!/usr/bin/env python3
"""Validate that files listed in high_signal_file_index.json exist."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_FILE = ROOT / "docs" / "high_signal_file_index.json"


def main() -> int:
    if not INDEX_FILE.exists():
        print(f"Error: {INDEX_FILE} does not exist.", file=sys.stderr)
        return 1

    with open(INDEX_FILE, encoding="utf-8") as f:
        data = json.load(f)

    files = data.get("files", [])
    missing = []
    for item in files:
        rel_path = item.get("path")
        if not (ROOT / rel_path).exists():
            missing.append(rel_path)

    if missing:
        print(f"Error: {len(missing)} indexed file(s) missing on disk:", file=sys.stderr)
        for path in missing:
            print(f"  - {path}", file=sys.stderr)
        return 1

    print(f"OK: All {len(files)} indexed files exist on disk.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
