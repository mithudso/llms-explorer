"""search-index.bin and search-meta.json must stay row-aligned with the concept packs.

SearchBox.astro refuses to run when the vector count and the meta count differ,
so a hand edit to one file (e.g. scrubbing an entry from the meta only) breaks
search on every /tree/ page. Regenerate both with tools/gen_search_index.mjs.
"""
import json
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
META = json.loads((SITE / "src/data/search-meta.json").read_text())
BIN = SITE / "public/search-index.bin"


def test_vector_file_matches_meta_count():
    floats = BIN.stat().st_size // 4
    assert floats == META["count"] * META["dim"], (
        f"search-index.bin holds {floats // META['dim']} vectors, meta says {META['count']}")
    assert len(META["items"]) == META["count"]


def test_meta_covers_exactly_the_committed_concept_packs():
    packs = {p.stem for p in (SITE / "src/data/concepts").glob("*.json")}
    slugs = {item["slug"] for item in META["items"]}
    assert slugs == packs, {"missing": sorted(packs - slugs), "extra": sorted(slugs - packs)}
