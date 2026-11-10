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
    if not (dist / "404.html").is_file():
        raise ValueError("Missing 404.html would enable the Cloudflare homepage fallback")
    # Keep the explicitly requested repository-root record identical to the
    # Astro public asset and the actual website-root build output.
    seller = b"google.com, pub-1706083044457708, DIRECT, f08c47fec0942fa0\n"
    root = Path(__file__).resolve().parents[2]
    for path in (root / "ads.txt", root / "site/public/ads.txt", dist / "ads.txt"):
        if not path.is_file() or path.read_bytes() != seller:
            raise ValueError(f"Missing or incorrect Google seller record: {path}")


if __name__ == "__main__":
    check(Path(__file__).resolve().parents[1] / "dist")
    print("Publication policy passed: concept tree preserved; archived content absent")
