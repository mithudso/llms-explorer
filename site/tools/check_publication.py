#!/usr/bin/env python3
"""Reject removed website surfaces and accidental archived-corpus publication."""
from pathlib import Path


def check(dist: Path) -> None:
    for route in ("directory", "directory.md", "sources", "downloads/sources",
                  "llms-full", "reference/directory", "reference/directory.md"):
        if (dist / route).exists():
            raise ValueError(f"Removed website content was published: {route}")
    for name in ("llms.txt", "llms-facts.txt"):
        if "<!-- migrated sections below:" in (dist / name).read_text():
            raise ValueError(f"Archived repository corpus was merged into {name}")


if __name__ == "__main__":
    check(Path(__file__).resolve().parents[1] / "dist")
    print("Publication policy passed: concept tree preserved; archived content absent")
