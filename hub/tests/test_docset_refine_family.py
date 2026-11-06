"""Family indexes consume native concept packs without fabricating page counts."""

import json
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from docset_refine import export_llms


def _concept_pack(tmp_path, slug="card-printing", concept="Card printing"):
    pack = tmp_path / f"{slug}.llms"
    pack.mkdir()
    files = {}
    for name, text in (
        ("llms.txt", "# Card printing\n\n> Production workflow.\n\n## Contents\n\n"
         "- [Facts](llms-facts.txt): Cited production units.\n"),
        ("llms-full.txt", "# Card printing\n\nComplete reference.\n"),
        ("llms-facts.txt", "# Card printing facts\n\nCited units.\n"),
    ):
        (pack / name).write_text(text)
        files[name] = {"bytes": len(text.encode()), "tokens": len(text) // 4}
    manifest = {
        "kind": "concept",
        "concept": concept,
        "slug": slug,
        "kept_units": 17,
        "sources": {"one.example": {}, "two.example": {}},
        "facets": {"procedure": 17},
        "files": files,
    }
    (pack / "manifest.json").write_text(json.dumps(manifest))
    return pack / "llms.txt"


def _legacy_mirror(tmp_path):
    mirror = tmp_path / "press.example.md"
    mirror.write_text("Legacy mirror source.\n")
    pack = tmp_path / "press.example.llms"
    pack.mkdir()
    (pack / "llms.txt").write_text("# Press documentation\n")
    (pack / "manifest.json").write_text(json.dumps({
        "title": "Press documentation",
        "pages": 3,
        "units": 9,
        "files": {"llms.txt": {"tokens": 6}},
    }))
    return mirror


def test_family_native_pack_counts_links_and_unchanged_manifest(tmp_path):
    index = _concept_pack(tmp_path)
    manifest = index.with_name("manifest.json")
    before = manifest.read_bytes()
    out = tmp_path / "family" / "llms.txt"

    result = export_llms.family([index], "Manufacturing", "Game production.", out)

    text = out.read_text()
    assert "## Concepts\n" in text
    assert "[Card printing](../card-printing.llms/llms.txt): 17 units, 2 source hosts" in text
    assert "pages" not in text
    assert "[Card printing facts](../card-printing.llms/llms-facts.txt): 17 units" in text
    assert result["products"] == 1
    assert manifest.read_bytes() == before
    for name in ("llms.txt", "llms-facts.txt"):
        assert (out.parent / "../card-printing.llms" / name).resolve().is_file()


def test_family_mixed_native_and_legacy_base_url(tmp_path):
    index = _concept_pack(tmp_path)
    mirror = _legacy_mirror(tmp_path)
    out = tmp_path / "family" / "llms.txt"

    result = export_llms.family(
        [mirror, index], "Manufacturing", "Game production.", out,
        base_url="https://docs.example/packs/",
    )

    text = out.read_text()
    assert "## Products\n" in text and "## Concepts\n" in text
    assert "https://docs.example/packs/press.example.llms/llms.txt): 3 pages, ~6" in text
    assert "https://docs.example/packs/card-printing.llms/llms.txt): 17 units" in text
    assert "https://docs.example/packs/card-printing.llms/llms-facts.txt" in text
    assert "llms.llms" not in text
    assert result["products"] == 2


def test_family_relative_input_and_output_paths(tmp_path, monkeypatch):
    index = _concept_pack(tmp_path)
    monkeypatch.chdir(tmp_path)
    out = Path("family/llms.txt")

    export_llms.family([index.relative_to(tmp_path)], "Manufacturing", "Summary.", out)

    assert "(../card-printing.llms/llms.txt)" in out.read_text()


def test_family_cli_accepts_native_index(tmp_path, capsys):
    from docset_refine.__main__ import main

    index = _concept_pack(tmp_path)
    out = tmp_path / "family" / "llms.txt"

    assert main([
        "family", str(index), "--name", "Manufacturing", "--summary", "Production.",
        "--out", str(out),
    ]) == 0

    assert json.loads(capsys.readouterr().out)["products"] == 1
    assert "[Card printing](../card-printing.llms/llms.txt)" in out.read_text()


def test_family_default_facts_output_is_unchanged(tmp_path):
    index = _concept_pack(tmp_path)
    default = tmp_path / "family" / "default.txt"
    explicit = default.with_name("explicit.txt")

    export_llms.family([index], "Manufacturing", "Production.", default)
    export_llms.family([index], "Manufacturing", "Production.", explicit, include_facts=True)

    assert default.read_bytes() == explicit.read_bytes()
    assert "## Facts\n" in default.read_text()


def test_family_index_only_api_preserves_mixed_member_links_and_manifests(tmp_path):
    from llms_txt.lint import parse_index

    index = _concept_pack(tmp_path)
    mirror = _legacy_mirror(tmp_path)
    manifest = index.with_name("manifest.json")
    before = manifest.read_bytes()
    full = tmp_path / "family" / "default.txt"
    only = full.with_name("indexes.txt")
    base_url = "https://docs.example/packs"

    old = export_llms.family([mirror, index], "Manufacturing", "Summary.", full, base_url)
    new = export_llms.family(
        [mirror, index], "Manufacturing", "Summary.", only, base_url, include_facts=False,
    )

    member_entries = [e for e in parse_index(full.read_text())["entries"]
                      if e["url"].endswith("/llms.txt")]
    assert parse_index(only.read_text())["entries"] == member_entries
    assert old["products"] == new["products"] == 2
    assert "## Facts" not in only.read_text()
    assert "llms-facts.txt" not in only.read_text()
    assert manifest.read_bytes() == before


def test_family_index_only_cli_keeps_all_26_members_and_detects_as_family(tmp_path, capsys):
    from docset_refine.__main__ import main
    from llms_txt.lint import check, detect_kind, parse_index

    indexes = [_concept_pack(tmp_path, f"topic-{i}", f"Printing topic {i}") for i in range(26)]
    before = {p: p.read_bytes() for index in indexes
              for p in (index, index.with_name("manifest.json"), index.with_name("llms-facts.txt"))}
    default = tmp_path / "family" / "default.txt"
    only = default.with_name("llms-public.txt")
    summary = "Production.\n\n<!-- generated by docset_refine family -->"
    base_url = "https://docs.example/packs"
    export_llms.family(indexes, "Manufacturing", summary, default, base_url)

    assert main([
        "family", *map(str, indexes), "--name", "Manufacturing", "--summary", summary,
        "--out", str(only), "--base-url", base_url, "--index-only",
    ]) == 0

    assert json.loads(capsys.readouterr().out)["products"] == 26
    default_members = [e for e in parse_index(default.read_text())["entries"]
                       if e["url"].endswith("/llms.txt")]
    entries = parse_index(only.read_text())["entries"]
    assert entries == default_members
    assert len(entries) == len({e["url"] for e in entries}) == 26
    assert "## Facts" not in only.read_text()
    assert detect_kind(only.read_text(), only.name)[0] == "family"
    assert check(only)["counts"]["high"] == 0
    assert only.stat().st_size < 10_000
    by_directory = {index.parent.name: index for index in indexes}
    for entry in entries:
        member = by_directory[Path(urlsplit(entry["url"]).path).parent.name]
        facts = [member.parent / e["url"] for e in parse_index(member.read_text())["entries"]
                 if e["url"] == "llms-facts.txt"]
        assert facts and all(path.is_file() for path in facts)  # Family -> index -> facts.
    assert all(p.read_bytes() == raw for p, raw in before.items())


@pytest.mark.parametrize("change", [
    {"concept": ""},
    {"kind": "unknown"},
    {"kept_units": -1},
    {"kept_units": True},
    {"sources": []},
    {"files": {"llms.txt": {"tokens": "unknown"}}},
    {"files": {}},
])
def test_family_rejects_invalid_native_pack_without_replacing_output(tmp_path, change):
    index = _concept_pack(tmp_path)
    path = index.with_name("manifest.json")
    manifest = json.loads(path.read_text())
    manifest.update(change)
    path.write_text(json.dumps(manifest))
    out = tmp_path / "llms.txt"
    out.write_text("Existing family.\n")

    with pytest.raises(ValueError, match="concept.*manifest|concept pack"):
        export_llms.family([_legacy_mirror(tmp_path), index], "Family", "Summary.", out)

    assert out.read_text() == "Existing family.\n"


@pytest.mark.parametrize("missing", ["manifest.json", "llms.txt", "llms-facts.txt"])
def test_family_rejects_missing_explicit_pack_artifacts(tmp_path, missing):
    index = _concept_pack(tmp_path)
    index.with_name(missing).unlink()
    out = tmp_path / "family" / "llms.txt"

    with pytest.raises(ValueError, match="concept"):
        export_llms.family([index], "Family", "Summary.", out)

    assert not out.exists()


def test_family_legacy_missing_export_still_skips(tmp_path):
    out = tmp_path / "llms.txt"
    result = export_llms.family([tmp_path / "not-exported.md"], "Family", "Summary.", out)
    assert result["products"] == 0
