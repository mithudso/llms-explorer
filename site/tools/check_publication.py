#!/usr/bin/env python3
"""Reject removed website surfaces and accidental archived-corpus publication."""
from pathlib import Path

from publication import is_published, metadata, review_assets, verify_research_review
from twins import route_of


def contains_assets(path: Path) -> bool:
    return path.is_file() or path.is_symlink() or any(
        item.is_file() or item.is_symlink() for item in path.rglob("*")
    )


def check(dist: Path, *, site: Path | None = None) -> None:
    site = site or Path(__file__).resolve().parents[1]
    blog = site / "src/content/blog"
    for source in blog.rglob("*.md"):
        relative = source.relative_to(blog)
        data = metadata(source.read_text(encoding="utf-8"))
        route = dist / route_of(Path("blog") / relative).strip("/")
        if not is_published(data):
            if route.exists() or route.with_suffix(".md").exists():
                raise ValueError(f"Unpublished article leaked into the build: {relative}")
            if relative.parts[0] == "research" or data.get("category") == "research":
                if relative.parts[0] != "research" or data.get("category") != "research":
                    raise ValueError("Research articles require category research "
                                     "and the research/ directory")
                assets = Path("research") / relative.relative_to("research").with_suffix("")
                if (contains_assets(site / "public/downloads" / assets)
                        or contains_assets(dist / "downloads" / assets)):
                    raise ValueError(f"Unpublished research images leaked: {relative}")
            continue
        if relative.parts[0] == "research" or data.get("category") == "research":
            if relative.parts[0] != "research" or data.get("category") != "research":
                raise ValueError("Research articles require category research "
                                 "and the research/ directory")
            paper = relative.relative_to("research")
            review = verify_research_review(site, paper, source)
            for _, asset, row in review_assets(site, paper, review):
                built = dist / "downloads" / row["path"]
                if (not asset.is_file() or not built.is_file()
                        or built.read_bytes() != asset.read_bytes()):
                    raise ValueError("Published research image is absent or differs in the build")
    scheduled = site / "scheduled-posts"
    for source in scheduled.rglob("*.md") if scheduled.is_dir() else []:
        if source.name.endswith(".ddo-report.md"):
            continue
        relative = source.relative_to(scheduled)
        data = metadata(source.read_text(encoding="utf-8"))
        if data.get("draft", "false").lower() != "true" and (
                relative.parts[0] == "research" or data.get("category") == "research"):
            if relative.parts[0] != "research" or data.get("category") != "research":
                raise ValueError("Scheduled research requires category research "
                                 "and the research/ directory")
            verify_research_review(site, relative.relative_to("research"), source)
        route = dist / route_of(Path("blog") / relative).strip("/")
        if route.exists() or route.with_suffix(".md").exists():
            raise ValueError(f"Scheduled article leaked into the build: {relative}")
        if relative.parts[0] == "research":
            assets = Path("research") / relative.relative_to("research").with_suffix("")
            if (contains_assets(site / "public/downloads" / assets)
                    or contains_assets(dist / "downloads" / assets)):
                raise ValueError(f"Scheduled research images leaked before publication: {relative}")
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
    root = site.parent
    for path in (root / "ads.txt", root / "site/public/ads.txt", dist / "ads.txt"):
        if not path.is_file() or path.read_bytes() != seller:
            raise ValueError(f"Missing or incorrect Google seller record: {path}")


if __name__ == "__main__":
    check(Path(__file__).resolve().parents[1] / "dist")
    print("Publication policy passed: research reviews current; "
          "scheduled and archived content absent")
