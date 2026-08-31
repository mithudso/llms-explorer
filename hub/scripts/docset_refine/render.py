"""render — reference.md + summary.json + all_units.jsonl from the unit files.

reference.md is for humans (the Docsets tab links it); all_units.jsonl is
what `docset_indexer index --units` embeds as `<key>__facts`.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from . import mirror_io, reference_dir

TYPE_ORDER = ("definition", "concept", "fact", "actionable", "parameter", "snippet", "problem",
              "question", "statement", "quote", "idea", "change")


def load_units(ref: Path) -> list[dict]:
    """structured.jsonl + the best available LLM units (polished wins)."""
    units = mirror_io.read_jsonl(ref / "structured.jsonl")
    for name in ("units.polished.jsonl", "units.jsonl"):
        if (ref / name).exists():
            units += mirror_io.read_jsonl(ref / name)
            break
    # The two files number independently from u000001; the merged list must
    # not (chroma rejects duplicate ids within a batch and silently drops
    # them across batches). Re-id here only — units.jsonl keeps its ids, which
    # polish.state.json refers to.
    for n, u in enumerate(units, 1):
        u["id"] = f"u{n:06d}"
    return units


def _line(u: dict) -> str:
    where = f"{u.get('source_url', '')}{u.get('anchor', '')}"
    if u.get("code"):
        code = u["code"]
        return (f"- **{u['text']}** — {where}\n\n  ```{code.get('lang', '')}\n"
                + "\n".join("  " + ln for ln in code.get("body", "").splitlines())
                + "\n  ```\n")
    return f"- {u['text']} — {where}"


def render_markdown(pages: list[dict], units: list[dict], name: str) -> str:
    by_page: dict[str, list[dict]] = {}
    for u in units:
        by_page.setdefault(u.get("source_url", ""), []).append(u)
    order = [p["url"] for p in pages] + [u for u in by_page if u not in {p["url"] for p in pages}]
    titles = {p["url"]: p.get("title") or p["url"] for p in pages}
    out = [f"# {name} — reference", "",
           f"{len(units)} units over {len(by_page)} pages. Each line ends in its source.", ""]
    for url in order:
        us = by_page.get(url)
        if not us:
            continue
        out.append(f"## {titles.get(url, url)}")
        out.append(f"<{url}>")
        out.append("")
        for t in TYPE_ORDER:
            group = [u for u in us if u.get("type") == t]
            if not group:
                continue
            out.append(f"### {t}")
            out.extend(_line(u) for u in group)
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def run(mirror: Path) -> dict:
    mirror = Path(mirror)
    ref = reference_dir(mirror)
    pages = mirror_io.load_json(ref / "pages.json", default=[])
    units = load_units(ref)
    (ref / "reference.md").write_text(render_markdown(pages, units, mirror.stem), encoding="utf-8")
    mirror_io.write_jsonl(units, ref / "all_units.jsonl")
    summary = {"docset": mirror.stem, "pages": len(pages), "units": len(units),
               "units_by_origin": dict(Counter(u.get("origin", "?") for u in units)),
               "units_by_type": dict(Counter(u.get("type", "?") for u in units)),
               "reference_md": str(ref / "reference.md"),
               "all_units": str(ref / "all_units.jsonl")}
    mirror_io.save_json(summary, ref / "summary.json")
    return summary
