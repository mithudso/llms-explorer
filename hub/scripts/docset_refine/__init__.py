"""docset_refine — turn a web-text-mirror docset into a source-anchored fact layer.

Pipeline (each step idempotent, each writes under `<stem>.reference/`):

  clean    strip cross-page boilerplate, triage pages, drop marketing/index
  extract  deterministic units: code snippets, table rows, definitions, changes
  units    LLM units for prose pages on the local Ollama pool (resumable)
  polish   optional `claude -p` pass over the LLM units
  render   reference.md + summary.json; all_units.jsonl for the facts index

Every unit carries `source_url` (+ `anchor`) — provenance is never dropped.
"""

from __future__ import annotations

import re
from pathlib import Path

UNIT_TYPES = ("concept", "fact", "actionable", "question", "problem", "statement",
              "quote", "idea", "snippet", "parameter", "definition", "change")
ORIGINS = ("code", "table", "heading", "changelog", "llm")


def reference_dir(mirror: Path) -> Path:
    """`<mirror.parent>/<stem>.reference/`, created on demand."""
    d = Path(mirror).parent / f"{Path(mirror).stem}.reference"
    d.mkdir(parents=True, exist_ok=True)
    return d


def clean_mirror_path(mirror: Path) -> Path:
    return Path(mirror).parent / f"{Path(mirror).stem}.clean.md"


def new_unit(seq: int, *, type: str, text: str, source_url: str, origin: str,
             anchor: str = "", page_class: str = "", keywords=None, code=None) -> dict:
    if type not in UNIT_TYPES:
        raise ValueError(f"unknown unit type {type!r}")
    if origin not in ORIGINS:
        raise ValueError(f"unknown origin {origin!r}")
    return {"id": f"u{seq:06d}", "type": type, "text": text.strip(),
            "source_url": source_url, "anchor": anchor, "page_class": page_class,
            "keywords": list(keywords or []), "code": code, "origin": origin}


def slug(text: str) -> str:
    """Heading → anchor slug the way docs sites do it (lowercase, hyphens)."""
    s = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[\s_-]+", "-", s)
