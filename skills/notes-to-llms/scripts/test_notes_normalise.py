"""Contract tests for `notes_normalise.py`.

The script's whole job is to make unsourced notes *gate-passing*, so the tests
are written against the two findings that job exists to prevent: P7 C6 (a unit
line with no source `llms_lint.py` accepts) and P7 R3 (an anchor that does not
resolve). Three of them assert against `llms_lint.py` and `docset_refine`
directly rather than against a restatement of their rules, because every bug
this file has caught was a place where the restatement was wrong.

Run:  python -m pytest skills/notes-to-llms/scripts/test_notes_normalise.py -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import notes_normalise as nn  # noqa: E402

HUB = Path(__file__).resolve().parents[3] / "hub" / "scripts"

LIMITS = """---
title: Rate limits
tag: api
---

# Rate limits

The gateway allows 60 requests per minute per key.

## Burst

Bursts of 10 are absorbed by a token bucket that refills every second.

## Burst

A duplicate heading, to prove a repeated slug is flagged rather than suffixed.
"""

SETEXT = """Setup
=====

Run the bootstrap script first, otherwise the virtualenv will not exist.

Details
-------

It installs pinned dependencies and then runs a subset of the test suite.

```
Not a heading
=============
```

- List item
---
"""

HTML = (
    "<html><head><style>a{color:red}</style></head><body>"
    "<h1>Errors</h1><p>Code 429 means the token bucket is empty.</p>"
    "</body></html>"
)

LOOSE = "A wall of text with no headings at all, long enough to clear the minimum page size.\n"


def _hub(module: str):
    sys.path.insert(0, str(HUB))
    if not (HUB / "llms_lint.py").exists():  # pragma: no cover
        pytest.skip("hub checkout not present")
    return __import__(module)


@pytest.fixture
def notes(tmp_path: Path) -> Path:
    root = tmp_path / "notes"
    (root / "sub").mkdir(parents=True)
    (root / "limits.md").write_text(LIMITS)
    (root / "loose.txt").write_text(LOOSE)
    (root / "dupe.txt").write_text(LOOSE)          # byte-identical to loose.txt
    (root / "empty.md").write_text("")             # under MIN_PAGE_CHARS
    (root / "thing.pdf").write_text("not text")    # unsupported suffix
    (root / ".hidden.md").write_text(LOOSE)        # dotfile, never walked
    (root / "sub" / "setup.md").write_text(SETEXT)
    (root / "sub" / "errors.html").write_text(HTML)
    return root


# --- the two gate findings -------------------------------------------------


def test_every_page_source_is_one_llms_lint_accepts(notes: Path) -> None:
    """`llms_lint.py` counts a unit as unsourced unless its source starts with
    `http`, `/` or `.`. A custom scheme like `upload://` is a High, so the
    default must be root-relative."""
    pages, _ = nn.normalise([notes], project="my-notes")
    assert pages, "expected pages"
    for page in pages:
        url = page["url"]
        assert url.startswith(("http", "/", ".")), url
        assert url.startswith("/my-notes/"), url


def test_every_recorded_anchor_resolves_through_llms_lint(notes: Path, tmp_path: Path) -> None:
    """The P7 R3 contract, asserted against the linter's own mirror parser
    rather than against our idea of what it does."""
    lint = _hub("llms_lint")
    pages, _ = nn.normalise([notes], project="n")
    mirror = tmp_path / "n.md"
    nn.write_mirror(pages, mirror)

    heads = lint._mirror_headings(mirror)
    assert heads, "the linter found no pages in the mirror"
    for page in pages:
        found = heads[page["url"].rstrip("/")]
        for heading in page["headings"]:
            assert f"#{heading['anchor']}" in found, (page["path"], heading)


def test_a_unit_built_from_the_inventory_lints_clean(notes: Path, tmp_path: Path) -> None:
    """End to end: build facts lines the way the skill says to, and assert
    `pass_facts` returns no High. This is the check that caught `upload://`."""
    lint = _hub("llms_lint")
    pages, _ = nn.normalise([notes], project="n")
    mirror = tmp_path / "n.md"
    nn.write_mirror(pages, mirror)

    lines = ["# n — facts", "", "> Units from the notes.", ""]
    for page in pages:
        lines.append(f"## {page['title']}")
        if page["headings"]:
            for h in page["headings"]:
                lines.append(
                    f"- [statement] Claim under {h['title']} — {page['url']}#{h['anchor']}"
                )
        else:
            # No headings means no anchor at all; `#top` would be unresolved.
            lines.append(f"- [statement] Claim from an unheaded note — {page['url']}")
    facts = tmp_path / "llms-facts.txt"
    facts.write_text("\n".join(lines) + "\n")

    findings = lint.pass_facts(facts.read_text(), facts, mirror)
    highs = [f for f in findings if f["severity"] == "high"]
    assert not highs, highs


# --- normalisation behaviour ----------------------------------------------


def test_setext_headings_are_rewritten_to_atx(notes: Path) -> None:
    """`llms_lint._mirror_headings` is ATX-only, so setext must be converted or
    its anchors do not exist."""
    pages, _ = nn.normalise([notes], project="n")
    setup = next(p for p in pages if p["path"].endswith("setup.md"))
    assert setup["text"].startswith("# Setup")
    assert "## Details" in setup["text"]
    assert [(h["level"], h["anchor"]) for h in setup["headings"]] == [(1, "setup"), (2, "details")]
    assert setup["title"] == "Setup"


def test_setext_conversion_leaves_fenced_blocks_and_lists_alone(notes: Path) -> None:
    pages, _ = nn.normalise([notes], project="n")
    setup = next(p for p in pages if p["path"].endswith("setup.md"))
    assert "# Not a heading" not in setup["text"], "converted inside a code fence"
    assert "# List item" not in setup["text"], "converted a list item"
    assert "Not a heading\n=============" in setup["text"]


def test_repeated_headings_share_one_anchor_and_are_flagged(notes: Path) -> None:
    """A `-2` suffix would be unresolvable: the linter collects anchors into a
    set and never disambiguates."""
    pages, report = nn.normalise([notes], project="n")
    limits = next(p for p in pages if p["path"] == "limits.md")
    assert [h["anchor"] for h in limits["headings"]] == ["rate-limits", "burst", "burst"]
    assert [h["duplicate"] for h in limits["headings"]] == [False, False, True]
    assert report["duplicate_anchors"] == [{"path": "limits.md", "anchor": "burst"}]


def test_base_url_replaces_the_root_relative_default(notes: Path) -> None:
    pages, _ = nn.normalise([notes], project="my-notes", base_url="https://ex.com/u/me/")
    assert "https://ex.com/u/me/limits.md" in {p["url"] for p in pages}
    assert not any(p["url"].startswith("/") for p in pages)


def test_frontmatter_is_stripped_but_its_title_is_kept(notes: Path) -> None:
    pages, _ = nn.normalise([notes], project="n")
    limits = next(p for p in pages if p["path"] == "limits.md")
    assert limits["title"] == "Rate limits"
    assert "tag: api" not in limits["text"]
    assert limits["text"].startswith("# Rate limits")


def test_html_keeps_its_headings_and_loses_its_tags(notes: Path) -> None:
    pages, _ = nn.normalise([notes], project="n")
    errors = next(p for p in pages if p["path"].endswith("errors.html"))
    assert [h["anchor"] for h in errors["headings"]] == ["errors"]
    assert "<p>" not in errors["text"] and "color:red" not in errors["text"]
    assert "429" in errors["text"]


def test_empty_and_duplicate_and_unsupported_are_dropped_and_counted(notes: Path) -> None:
    pages, report = nn.normalise([notes], project="n")
    paths = {p["path"] for p in pages}
    assert "empty.md" not in paths and "thing.pdf" not in paths
    assert (".hidden.md" not in paths) and len({"loose.txt", "dupe.txt"} & paths) == 1
    assert report["dropped_empty_pages"] == 1
    assert report["dropped_duplicates"] == 1
    assert [s["path"] for s in report["skipped_unreadable"]] == ["thing.pdf"]


def test_headingless_pages_are_reported_not_hidden(notes: Path) -> None:
    """Their units must carry the bare page URL; the caller has to be told.

    The surviving copy of the `loose.txt`/`dupe.txt` pair is `dupe.txt`: the
    walk is sorted, so the first path wins and the same input always produces
    the same mirror, which is what makes regeneration byte-stable (P15).
    """
    _, report = nn.normalise([notes], project="n")
    assert report["pages_without_headings"] == ["dupe.txt"]


def test_duplicate_resolution_is_deterministic(notes: Path) -> None:
    first = [p["path"] for p in nn.normalise([notes], project="n")[0]]
    second = [p["path"] for p in nn.normalise([notes], project="n")[0]]
    assert first == second == sorted(first)
    assert "dupe.txt" in first and "loose.txt" not in first


# --- interop with the hub --------------------------------------------------


def test_mirror_round_trips_through_the_hub_parser(notes: Path, tmp_path: Path) -> None:
    """The mirror is only useful if `docset_refine` can read it back."""
    pages, _ = nn.normalise([notes], project="n")
    mirror = tmp_path / "n.md"
    nn.write_mirror(pages, mirror)
    if not (HUB / "docset_refine" / "mirror_io.py").exists():  # pragma: no cover
        pytest.skip("hub checkout not present")
    sys.path.insert(0, str(HUB))
    from docset_refine import mirror_io  # noqa: PLC0415

    parsed = mirror_io.parse_mirror(mirror.read_text())
    assert [p["url"] for p in parsed] == [p["url"] for p in pages]
    assert parsed[0]["text"].strip() == pages[0]["text"].strip()


def test_slug_matches_the_hub_implementation() -> None:
    """Drift here silently breaks every anchor this script writes."""
    if not (HUB / "docset_refine" / "__init__.py").exists():  # pragma: no cover
        pytest.skip("hub checkout not present")
    sys.path.insert(0, str(HUB))
    import docset_refine  # noqa: PLC0415

    for text in ["Rate limits", "  Spaced  Out  ", "C++ & you!", "Tabs\tand_underscores", "429s"]:
        assert nn.slug(text) == docset_refine.slug(text), text


def test_the_mirror_stem_is_what_docset_refine_expects(notes: Path, tmp_path: Path) -> None:
    """`<project>.mirror.md` would make `docset_refine` write
    `<project>.mirror.reference/` and `<project>.mirror.llms/`."""
    out = tmp_path / "build"
    assert nn.main([str(notes), "--project", "My Notes", "--out", str(out)]) == 0
    mirror = out / "my-notes.md"
    assert mirror.exists()
    if not (HUB / "docset_refine" / "__init__.py").exists():  # pragma: no cover
        pytest.skip("hub checkout not present")
    sys.path.insert(0, str(HUB))
    import docset_refine  # noqa: PLC0415

    assert docset_refine.reference_dir(mirror).name == "my-notes.reference"
    assert docset_refine.clean_mirror_path(mirror).name == "my-notes.clean.md"


# --- CLI -------------------------------------------------------------------


def test_cli_writes_both_files_and_omits_bodies_from_the_inventory(
    notes: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "build"
    assert nn.main([str(notes), "--project", "My Notes", "--out", str(out)]) == 0
    inventory = out / "my-notes.pages.json"
    assert (out / "my-notes.md").exists() and inventory.exists()
    data = json.loads(inventory.read_text())
    assert data["report"]["pages"] == len(data["pages"]) == 4
    assert all("text" not in p for p in data["pages"]), "bodies belong in the mirror only"
    printed = capsys.readouterr().out
    assert "no headings" in printed and "share an anchor" in printed


def test_no_readable_pages_is_an_error_not_an_empty_file(tmp_path: Path) -> None:
    (tmp_path / "only.pdf").write_text("x")
    assert nn.main([str(tmp_path), "--project", "p", "--out", str(tmp_path / "o")]) == 1
    assert not (tmp_path / "o" / "p.md").exists()
