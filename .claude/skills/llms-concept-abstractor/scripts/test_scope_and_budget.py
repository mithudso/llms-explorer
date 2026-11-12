"""Counterexamples use only original temporary files and private compilation."""
from argparse import Namespace
from collections import Counter
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path

import pytest

SOURCE = Path(os.environ.get("SKO_TEST_SOURCE_ROOT", Path(__file__).parent))
spec = importlib.util.spec_from_file_location("scope_budget_lca", SOURCE / "concept_abstract.py")
lca = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lca)


@pytest.mark.parametrize("use_glob", [False, True])
def test_discovered_symlink_stays_inside_approved_root(tmp_path, use_glob):
    root = tmp_path / "approved"
    root.mkdir()
    (root / "inside.md").write_text("# Fixture\n\nFixture INSIDE is original content under the approved root.\n")
    outside = tmp_path / "outside.md"
    outside.write_text("# Fixture\n\nFixture OUTSIDE is original content that was not approved.\n")
    (root / "external.md").symlink_to(outside)
    paths = [str(root / "*.md")] if use_glob else [str(root)]
    rows = [(p, list(units)) for p, units in lca.iter_inputs(paths)]
    assert not any("OUTSIDE" in u["text"] for _, units in rows for u in units)
    assert len(rows) == 1
    ledger = []
    list(lca.iter_inputs(paths, ledger=ledger))
    assert Counter(r["status"] for r in ledger) == {"kept": 1, "outside-root": 1}


def test_aliases_deduplicate_resolved_files(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    target = root / "a.md"
    target.write_text("# Fixture\n\nFixture content belongs to the selected source and is long enough.\n")
    (root / "b.md").symlink_to(target)
    assert len(list(lca.iter_inputs([str(root)]))) == 1
    ledger = []
    list(lca.iter_inputs([str(root)], ledger=ledger))
    assert Counter(r["status"] for r in ledger) == {"kept": 1, "duplicate": 1}
    duplicate = next(r for r in ledger if r["status"] == "duplicate")
    assert duplicate["duplicate_of"] == next(r["source_id"] for r in ledger if r["status"] == "kept")


def unit(i, facet, text):
    row = lca._unit(f"s01u{i:06d}", "definition" if facet == "definition" else "statement",
                    text, "https://source.fixture.invalid/fixture", "#fixture")
    row.update(matched=["fixture"], relation="about", score=1.0, facet=facet, keep=True)
    return row


def compile_private(out, rows, budget):
    out.mkdir(exist_ok=True)
    (out / "pool.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    args = Namespace(out=str(out), concept="Fixture", lexicon=None, classified=None,
                     keep_lead_ins=True, rights="quote", base_url=None,
                     summary="Original fixture catalogue.", budget_tokens=budget,
                     max_related=20, private=True)
    with contextlib.redirect_stdout(io.StringIO()):
        lca.compile_pack(args)


def test_oversized_mandatory_definition_is_a_bounded_error(tmp_path):
    out = tmp_path / "pack"
    text = "Fixture is an original synthetic concept. " + "Its original source states this property. " * 120
    with pytest.raises(ValueError, match="small budget.*too small"):
        compile_private(out, [unit(1, "definition", text)], 100)
    assert not (out / "manifest.json").exists()
    assert not (out / "llms-small.txt").exists()


def test_rendered_small_budget_includes_all_overhead(tmp_path):
    out = tmp_path / "pack"
    rows = [unit(i, facet, f"Fixture {i} is an original {facet} statement. " + "A source qualifier stays intact. " * 2)
            for i, facet in enumerate(["definition"] * 4 + ["parameters"] * 4 + ["problems"] * 4, 1)]
    compile_private(out, rows, 400)
    text = (out / "llms-small.txt").read_text()
    manifest = json.loads((out / "manifest.json").read_text())
    assert len(text) <= 400 * lca.CHARS_PER_TOKEN
    assert manifest["files"]["llms-small.txt"]["bytes"] == len(text.encode())
    assert all(lca.FACETS[facet] in text for facet in {r["facet"] for r in rows})
    for line in text.splitlines():
        if line.startswith("- ["):
            assert any(lca._line(r, False) == line for r in rows)


def test_budget_error_preserves_existing_compiled_files(tmp_path):
    out = tmp_path / "pack"
    out.mkdir()
    (out / "llms-small.txt").write_text("prior checked small output\n")
    (out / "manifest.json").write_text('{"prior": true}\n')
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    with pytest.raises(ValueError, match="small budget.*too small"):
        compile_private(out, [unit(1, "definition", "Fixture source text. " * 200)], 50)
    assert all((out / name).read_bytes() == value for name, value in before.items())


def test_complete_short_facet_can_cost_less_than_its_omission_notice(tmp_path):
    rows = [unit(i, "definition", f"Fixture {i} is a tiny thing.") for i in (1, 2)]
    for row in rows:
        row.update(source_url="/f", anchor="")
    roomy = tmp_path / "roomy"
    compile_private(roomy, rows, 500)
    exact_budget = (len((roomy / "llms-small.txt").read_text()) + 3) // 4
    tight = tmp_path / "tight"
    compile_private(tight, rows, exact_budget)
    text = (tight / "llms-small.txt").read_text()
    assert len(text) <= exact_budget * 4
    assert text.count("- [definition]") == 2
