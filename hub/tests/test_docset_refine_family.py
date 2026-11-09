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


def test_family_default_mixed_output_matches_legacy_snapshot(tmp_path):
    index = _concept_pack(tmp_path)
    mirror = _legacy_mirror(tmp_path)
    out = tmp_path / "family" / "llms.txt"

    export_llms.family([mirror, index], "Manufacturing", "Production.", out)

    assert out.read_bytes() == (
        b"# Manufacturing\n\n> Production.\n\n"
        b"Each member below has its own llms.txt; this file links member indexes, not content.\n\n"
        b"## Products\n\n"
        b"- [Press documentation](../press.example.llms/llms.txt): 3 pages, ~6 tokens index\n\n"
        b"## Concepts\n\n"
        b"- [Card printing](../card-printing.llms/llms.txt): 17 units, 2 source hosts, "
        b"~26 tokens index, ~9 tokens full\n\n"
        b"## Facts\n\n"
        b"- [Card printing facts](../card-printing.llms/llms-facts.txt): 17 units, ~9 tokens\n"
    )


def test_family_v3_single_rollup_keeps_member_sitemaps_and_resources_on_regeneration(tmp_path):
    single = _concept_pack(tmp_path, "single", "Single member")
    manifest_path = single.with_name("manifest.json")
    manifest = json.loads(manifest_path.read_text())
    for filename in ("llms-full.txt", "llms-facts.txt"):
        del manifest["files"][filename]
        single.with_name(filename).unlink()
    single.write_text("# Single member\n\n> Bounded reference.\n\n## Facts\n\nCited units.\n")
    manifest["files"]["llms.txt"] = {"tokens": len(single.read_text()) // 4}
    manifest_path.write_text(json.dumps(manifest))
    # An undeclared leftover must not enter the member sitemap.
    single.with_name("llms-sitemap.txt").write_text("Unrelated leftover.\n")
    family_member = _concept_pack(tmp_path, "larger", "Family member")
    family_manifest = family_member.with_name("manifest.json")
    manifest = json.loads(family_manifest.read_text())
    sitemap = family_member.with_name("llms-sitemap.txt")
    sitemap.write_text("# Member sitemap\n")
    manifest["files"][sitemap.name] = {"tokens": 4}
    family_manifest.write_text(json.dumps(manifest))
    before = {p: p.read_bytes() for p in (manifest_path, family_manifest, single, family_member)}
    out = tmp_path / "rollup" / "llms.txt"
    resources = {
        "Related files": [f"- {tmp_path / 'tree.json'} — concept tree (unverified)"],
        "Skills": ["- `trading-and-investing` — researched guide owner"],
        "Agents and tools": ["- `/lca` and `/ldo` — compiler and rollup delegates"],
        "Websites": ["- https://docs.example/llms.txt — scout discovery index (unverified)"],
    }

    first = export_llms.family(
        [single, family_member, single], "Suite", "Qualified members.", out,
        include_facts=False, resources=resources,
    )
    text = out.read_text()
    export_llms.family(
        [single, family_member, single], "Suite", "Qualified members.", out,
        include_facts=False, resources=resources,
    )

    assert out.read_text() == text
    assert first["shape"] == "single" and first["entries"] == 3
    assert "Mode: single-file" in text and "## Facts\n\n## Sitemap" in text
    sitemap_lines = text.split("## Sitemap\n\n", 1)[1].split("\n\n## Resources", 1)[0].splitlines()
    assert sitemap_lines == [
        "- ../single.llms/llms.txt — Single member",
        "- ../larger.llms/llms.txt — Family member",
        "- ../larger.llms/llms-sitemap.txt — Family member sitemap",
    ]
    assert "llms-facts.txt" not in text
    assert "[Single member](../single.llms/llms.txt): 17 units, 2 source hosts" in text
    assert "[Family member](../larger.llms/llms.txt): 17 units, 2 source hosts" in text
    for category, rows in resources.items():
        assert f"### {category}\n\n" in text
        assert all(row in text for row in rows)
    assert all(path.read_bytes() == raw for path, raw in before.items())


@pytest.mark.parametrize("resources", [
    [], {}, {"Skills": []}, {"Unknown": ["- target — reason"]}, {"Skills": "- target — reason"},
    {"Skills": [3]}, {"Skills": ["- target - reason"]}, {"Skills": ["- target — reason\nnext"]},
])
def test_family_v3_rejects_malformed_resources_without_replacing_output(tmp_path, resources):
    index = _concept_pack(tmp_path)
    out = tmp_path / "llms.txt"
    out.write_text("Existing rollup.\n")

    with pytest.raises(ValueError, match="[Rr]esources"):
        export_llms.family([index], "Suite", "Summary.", out, resources=resources)

    assert out.read_text() == "Existing rollup.\n"


@pytest.mark.parametrize("include_facts", [False, True])
def test_family_v3_preserves_qualified_assertions_and_ordered_citations(tmp_path, include_facts):
    index = _concept_pack(tmp_path)
    out = tmp_path / "rollup" / "llms.txt"
    rows = [
        "- `alpha`  preserves punctuation — and Unicode. [src: https://one.example/paper#proof]",
        "- Limits require stated assumptions. "
        "[src: https://one.example/paper, http://two.example/details?x=1&y=2]",
    ]
    before = rows.copy()

    export_llms.family(
        [index], "Suite", "Qualified members.", out, include_facts=include_facts,
        resources={"Other": ["- source — verified source record"]}, qualified_facts=rows,
    )

    text = out.read_text()
    assert "## Facts\n\n" + "\n".join(rows) + "\n" in text
    assert ("[Card printing facts]" in text) is include_facts
    assert rows == before
    assert "caller-supplied qualified assertions" in text


@pytest.mark.parametrize("rows", [
    [], "- assertion [src: https://one.example]", [None],
    ["- assertion"], ["-  [src: https://one.example]"],
    ["- assertion [src: relative]"], ["- assertion [src: https://]"],
    ["- assertion [src: https://one.example, file:///private/source]"],
    ["- assertion [src: https://one.example]\n- inserted assertion"],
    ["- assertion [src: https://one.example] "], ["- assertion [src: https://[invalid]"],
])
def test_family_v3_rejects_malformed_qualified_facts_without_replacing_output(tmp_path, rows):
    index = _concept_pack(tmp_path)
    out = tmp_path / "llms.txt"
    out.write_text("Existing rollup.\n")

    with pytest.raises(ValueError, match="qualified_facts"):
        export_llms.family(
            [index], "Suite", "Summary.", out, qualified_facts=rows,
            resources={"Other": ["- source — verified source record"]},
        )

    assert out.read_text() == "Existing rollup.\n"


def test_family_qualified_facts_requires_explicit_v3_opt_in(tmp_path):
    index = _concept_pack(tmp_path)
    out = tmp_path / "llms.txt"
    out.write_text("Existing rollup.\n")

    with pytest.raises(ValueError, match="qualified_facts requires resources"):
        export_llms.family([index], "Suite", "Summary.", out,
                           qualified_facts=["- Exact assertion. [src: https://one.example]"])

    assert out.read_text() == "Existing rollup.\n"


def test_family_v3_rejects_missing_declared_sitemap_without_replacing_output(tmp_path):
    index = _concept_pack(tmp_path)
    path = index.with_name("manifest.json")
    manifest = json.loads(path.read_text())
    manifest["files"]["llms-sitemap.txt"] = {"tokens": 1}
    path.write_text(json.dumps(manifest))
    out = tmp_path / "llms.txt"
    out.write_text("Existing rollup.\n")

    with pytest.raises(ValueError, match="Missing declared member sitemap"):
        export_llms.family([index], "Suite", "Summary.", out,
                           resources={"Other": ["- source — reason"]})

    assert out.read_text() == "Existing rollup.\n"


def test_family_v3_rejects_oversize_utf8_output_without_replacing_output(tmp_path):
    index = _concept_pack(tmp_path)
    out = tmp_path / "llms.txt"
    out.write_text("Existing rollup.\n")

    with pytest.raises(ValueError, match="32,000 bytes"):
        export_llms.family([index], "Suite", "Summary.", out,
                           resources={"Other": ["- source — " + "é" * 16_000]})

    assert out.read_text() == "Existing rollup.\n"


def test_family_v3_rejects_more_than_200_sitemap_entries_without_replacing_output(tmp_path):
    indexes = [_concept_pack(tmp_path, str(i), str(i)) for i in range(201)]
    out = tmp_path / "llms.txt"
    out.write_text("Existing rollup.\n")

    with pytest.raises(ValueError, match="200 sitemap entries"):
        export_llms.family(indexes, "Suite", "Summary.", out, include_facts=False,
                           resources={"Other": ["- source — reason"]})

    assert out.read_text() == "Existing rollup.\n"


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
