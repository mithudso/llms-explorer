"""Family indexes consume native concept packs without fabricating page counts."""

import json
from pathlib import Path

import pytest

from docset_refine import export_llms


def _concept_pack(tmp_path):
    pack = tmp_path / "card-printing.llms"
    pack.mkdir()
    files = {}
    for name, text in (
        ("llms.txt", "# Card printing\n\n> Production workflow.\n"),
        ("llms-full.txt", "# Card printing\n\nComplete reference.\n"),
        ("llms-facts.txt", "# Card printing facts\n\nCited units.\n"),
    ):
        (pack / name).write_text(text)
        files[name] = {"bytes": len(text.encode()), "tokens": len(text) // 4}
    manifest = {
        "kind": "concept",
        "concept": "Card printing",
        "slug": "card-printing",
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
