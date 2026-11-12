"""Every selected input must have a body-free, root-qualified disposition."""
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path

SOURCE = Path(os.environ.get("SKO_TEST_SOURCE_ROOT", Path(__file__).parent))
spec = importlib.util.spec_from_file_location("ledger_normaliser", SOURCE / "notes_normalise.py")
nn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nn)


def test_source_statuses_cover_omissions_and_duplicate_identity(tmp_path, monkeypatch):
    root = tmp_path / "approved"
    root.mkdir()
    body = "# Fixture\n\nThis original fixture claim has enough content to be retained.\n"
    (root / "a.md").write_text(body)
    (root / "b.md").write_text(body)
    (root / "empty.md").write_text("")
    (root / "unsupported.pdf").write_bytes(b"%PDF original fixture")
    (root / "unreadable.md").write_text(body + "unreadable fixture marker")
    outside = tmp_path / "outside.md"
    outside.write_text(body + "OUTSIDE")
    (root / "escape.md").symlink_to(outside)
    original_read = nn._read
    monkeypatch.setattr(nn, "_read", lambda p: None if p.name == "unreadable.md" else original_read(p))
    pages, report = nn.normalise([root], project="fixture")
    ledger = report["source_statuses"]
    assert Counter(r["status"] for r in ledger) == {
        "kept": 1, "duplicate": 1, "empty": 1, "unsupported": 1,
        "unreadable": 1, "outside-root": 1,
    }
    assert len({r["source_id"] for r in ledger}) == 6
    assert all(r["source_id"].startswith("approved-") for r in ledger)
    kept = next(r for r in ledger if r["status"] == "kept")
    duplicate = next(r for r in ledger if r["status"] == "duplicate")
    assert duplicate["path"] == "b.md"
    assert duplicate["duplicate_of"] == kept["source_id"]
    assert next(r for r in ledger if r["status"] == "empty")["path"] == "empty.md"
    assert len(pages) == 1 and "OUTSIDE" not in pages[0]["text"]
    assert "fixture claim" not in json.dumps(report), "the omission ledger must not copy note bodies"


def test_inventory_keeps_the_per_source_statuses(tmp_path):
    root = tmp_path / "notes"
    root.mkdir()
    body = "# Fixture\n\nThis original fixture content is kept once and has a source.\n"
    (root / "a.md").write_text(body)
    (root / "b.md").write_text(body)
    (root / "empty.md").write_text("")
    out = tmp_path / "build"
    assert nn.main([str(root), "--project", "fixture", "--out", str(out)]) == 0
    report = json.loads((out / "fixture.pages.json").read_text())["report"]
    assert len(report["source_statuses"]) == 3
    assert {r["path"] for r in report["source_statuses"]} == {"a.md", "b.md", "empty.md"}
