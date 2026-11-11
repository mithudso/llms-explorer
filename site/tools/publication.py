"""Publication dates and exact editorial review bindings for authored research."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from zoneinfo import ZoneInfo

TIMEZONE = "America/New_York"
FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", re.S)
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def publication_day(now: dt.datetime | None = None) -> dt.date:
    now = now or dt.datetime.now(dt.UTC)
    if now.tzinfo is None:
        raise ValueError("Publication clock must have a timezone")
    return now.astimezone(ZoneInfo(TIMEZONE)).date()


def metadata(text: str) -> dict[str, str]:
    """Read publication-owned scalar fields only from YAML frontmatter.

    Authoring uses single-line scalar title/date/category fields. Astro still
    validates the complete YAML document during the build.
    """
    match = FRONTMATTER.match(text)
    if not match:
        return {}
    result = {}
    for name in ("title", "date", "category", "draft"):
        values = re.findall(rf"^{name}:\s*([^\r\n]*?)\s*$", match[1], re.M)
        if len(values) > 1:
            raise ValueError(f"Duplicate publication field: {name}")
        if values:
            value = values[0]
            if value.startswith('"'):
                value = json.loads(value)
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1].replace("''", "'")
            else:
                value = value.split(" #", 1)[0].strip()
            if not isinstance(value, str):
                raise ValueError(f"Publication field must be a scalar: {name}")
            result[name] = value
    return result


def is_published(data: dict, today: dt.date | None = None) -> bool:
    if str(data.get("draft", "false")).lower() == "true":
        return False
    date = data.get("date")
    return not date or dt.date.fromisoformat(date) <= (today or publication_day())


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review_assets(site: Path, relative: Path, review: dict) -> list[tuple[Path, Path, dict]]:
    """Resolve only the paper's pinned image assets, held outside public until release."""
    rows = review.get("assets", [])
    if not isinstance(rows, list) or len(rows) > 32:
        raise ValueError("Research review assets must be a bounded list")
    prefix = ("research", *relative.with_suffix("").parts)
    seen, result = set(), []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            raise ValueError("Research image asset needs a relative path")
        raw = row["path"]
        path = PurePosixPath(raw)
        if (path.is_absolute() or path.as_posix() != raw or "\\" in raw
                or any(part in {".", ".."} for part in path.parts)
                or path.parts[:len(prefix)] != prefix or len(path.parts) <= len(prefix)
                or path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}
                or raw in seen):
            raise ValueError("Research image asset must stay in its own paper directory")
        seen.add(raw)
        if (not isinstance(row.get("sha256"), str) or not SHA256.fullmatch(row["sha256"])
                or type(row.get("bytes")) is not int or not 0 < row["bytes"] <= 8 * 1024 * 1024):
            raise ValueError("Research image asset needs bounded byte/hash bindings")
        scheduled = site / "scheduled-assets" / Path(*path.parts)
        published = site / "public/downloads" / Path(*path.parts)
        present = False
        for base, candidate in ((site / "scheduled-assets", scheduled),
                                (site / "public/downloads", published)):
            if not candidate.resolve().is_relative_to(base.resolve()):
                raise ValueError("Research image asset escapes its asset root")
            if candidate.exists() or candidate.is_symlink():
                if (not candidate.is_file() or candidate.is_symlink()
                        or candidate.stat().st_size != row["bytes"]
                        or digest(candidate) != row["sha256"]):
                    raise ValueError("Research image asset differs from its reviewed bytes")
                present = True
        if not present:
            raise ValueError("Reviewed research image asset is missing")
        result.append((scheduled, published, row))
    return result


def verify_research_review(site: Path, relative: Path, document: Path) -> dict:
    """Bind a research file to its full editorial review and retained report."""
    review_path = site / "research-reviews" / relative.with_suffix(".json")
    if not review_path.is_file() or review_path.is_symlink():
        raise ValueError(f"Missing regular research review: {review_path}")
    review = json.loads(review_path.read_text(encoding="utf-8"))
    if (review.get("schema") != "research-publication-review/v1"
            or review.get("status") != "approved" or review.get("depth") != "full"):
        raise ValueError(f"Research review is not approved at full depth: {review_path}")
    unresolved = review.get("unresolved", {})
    if any(type(unresolved.get(key)) is not int or unresolved[key] != 0
           for key in ("blocking", "major", "medium")):
        raise ValueError(f"Research review has unresolved findings: {review_path}")
    try:
        stamp = dt.datetime.fromisoformat(review["reviewed_at"].replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            raise ValueError("reviewed_at requires a timezone")
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid research review timestamp: {review_path}") from exc
    if (not isinstance(review.get("document_sha256"), str)
            or not SHA256.fullmatch(review["document_sha256"])
            or review["document_sha256"] != digest(document)):
        raise ValueError(f"Research document changed after review: {document}")
    report_relative = Path(review.get("report_path", ""))
    root = site.parent.resolve()
    report = (root / report_relative).resolve()
    if (not report_relative.parts or report_relative.is_absolute()
            or not report.is_relative_to(root) or not report.is_file()):
        raise ValueError(f"Research report must be a regular repository file: {review_path}")
    if (not isinstance(review.get("report_sha256"), str)
            or not SHA256.fullmatch(review["report_sha256"])
            or review["report_sha256"] != digest(report)):
        raise ValueError(f"Research report changed after approval: {report}")
    review_assets(site, relative, review)
    return review
