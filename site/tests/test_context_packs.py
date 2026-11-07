"""Only published references enter portable packs; all members bind to hashes."""

import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import gen_context_packs as packs


def test_public_archive_is_reproducible_and_hash_bound():
    facts = "# Example\n\n- Fact — [source](https://example.test/original)\n"
    args = ("example", facts, "Example", "2026-11-07", "https://llmsx.org")
    raw = packs.archive(*args)
    assert raw == packs.archive(*args)
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        manifest = json.loads(zf.read("example.llms/manifest.json"))
        assert "private" not in zf.namelist()
        assert zf.read("example.llms/llms-facts.txt").decode() == facts
        assert len(zf.namelist()) == 7
        for name, meta in manifest["files"].items():
            member = zf.read("example.llms/" + name)
            assert meta["bytes"] == len(member)
            assert meta["sha256"] == hashlib.sha256(member).hexdigest()
            assert meta["tokens"] == len(member.decode()) // 4


def test_export_uses_only_context_inventory_with_readable_references(tmp_path):
    facts = tmp_path / "facts"
    facts.mkdir()
    concepts = tmp_path / "concepts"
    concepts.mkdir()
    (tmp_path / "tree.json").write_text(json.dumps({"generated": "today", "nodes": {}}))
    (tmp_path / "context.json").write_text(
        json.dumps({"roots": [{"concepts": [{"slug": "published"}, {"slug": "empty"}]}]})
    )
    for slug in ("published", "empty", "not-in-inventory"):
        (facts / (slug + ".md")).write_text("# " + slug)
        (concepts / (slug + ".json")).write_text(
            json.dumps(
                {
                    "summary": "Example",
                    "facets": [
                        {
                            "facts": []
                            if slug == "empty"
                            else [{"text": "fact", "source": "https://example.test/source"}]
                        }
                    ],
                }
            )
        )
    index = packs.build(facts, tmp_path / "tree.json", tmp_path / "out", "https://llmsx.org")
    assert [p["slug"] for p in index["packs"]] == ["published"]
    raw = (tmp_path / "out/published.llms.zip").read_bytes()
    assert index["packs"][0]["sha256"] == hashlib.sha256(raw).hexdigest()
