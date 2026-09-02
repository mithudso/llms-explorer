"""`optimizers.CATALOGUE` is component 18 §7, as data — and this file proves it.

The point of the module is :func:`test_the_catalogue_matches_the_spoke`: it parses
the table out of `docs/site/components/18-optimizer-catalogue.md` §7 and asserts
every transcribed field came from there. Edit one without the other and CI fails
here, where the difference is a diff.

The parser is written *here* and not imported from `optimizers.py` on purpose: a
drift guard that shares its reading of the document with the code it checks guards
nothing. That is the same reasoning `api/tests/test_plans.py` records for 15 §5.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from llmsx import optimizers

REPO_ROOT = Path(__file__).resolve().parents[2]
SPOKE = REPO_ROOT / "docs" / "site" / "components" / "18-optimizer-catalogue.md"

#: Fields §7's table carries. Everything else on the record — skill, artifacts,
#: summary, surface — is the module's own and is checked by shape, not by drift.
TABLE_FIELDS = ("id", "name", "alias", "passes", "hosted", "gate", "domain")


def _table_rows(marker: str) -> list[list[str]]:
    """Cells of the markdown table whose header row contains ``marker``."""
    lines = SPOKE.read_text(encoding="utf-8").splitlines()
    start = next(
        (n for n, line in enumerate(lines) if line.startswith("|") and marker in line),
        None,
    )
    if start is None:  # pragma: no cover - the spoke lost its table
        raise AssertionError(f"no table headed {marker!r} in {SPOKE}")
    rows = []
    for line in lines[start:]:
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(set(c) <= {"-", ":"} for c in cells):  # the |---|---| rule
            continue
        rows.append(cells)
    return rows


def _unbacktick(cell: str) -> str:
    """``` `ldo` ``` → ``ldo``.

    The table code-quotes ids, aliases, filenames and operators, because those
    read wrong in prose otherwise. Backticks are markdown, not data, so every
    text cell is stripped of them before comparison — a record that carried them
    would put backticks into JSON, into six client libraries, and onto a page
    that renders markdown nowhere.
    """
    return cell.replace("`", "").strip()


def parse_spoke() -> list[dict[str, object]]:
    """§7's table as a list of dicts, in document order."""
    rows = _table_rows("| id | name | alias |")
    header = [c.strip() for c in rows[0]]
    assert header[: len(TABLE_FIELDS)] == list(TABLE_FIELDS), header
    out = []
    for cells in rows[1:]:
        record = dict(zip(header, cells, strict=True))
        out.append(
            {
                "id": _unbacktick(record["id"]),
                "name": _unbacktick(record["name"]),
                "alias": _unbacktick(record["alias"]),
                "passes": int(record["passes"]),
                # "yes"/"no" reads better in a table than true/false, and the
                # only two values it may take are asserted below.
                "hosted": {"yes": True, "no": False}[record["hosted"].lower()],
                "gate": _unbacktick(record["gate"]),
                "domain": _unbacktick(record["domain"]),
            }
        )
    return out


# --- the drift guard ---------------------------------------------------------


def test_the_spoke_still_has_the_table_this_test_reads():
    """Guard the guard: a silent parse of nothing would pass everything."""
    spoke = parse_spoke()
    assert len(spoke) == 9, f"18 §7 lists {len(spoke)} optimizers, expected 9"
    assert {r["id"] for r in spoke} == set(optimizers.BY_ID)


def test_the_catalogue_matches_the_spoke():
    """Field by field, in document order. Any drift fails here."""
    spoke = parse_spoke()
    code = optimizers.all_optimizers()
    assert [r["id"] for r in spoke] == [o.id for o in code], "order differs"
    for expected, got in zip(spoke, code, strict=True):
        for field_name in TABLE_FIELDS:
            assert getattr(got, field_name) == expected[field_name], (
                f"{got.id}.{field_name}: code {getattr(got, field_name)!r} "
                f"!= spoke {expected[field_name]!r}"
            )


def test_the_hosted_row_names_a_surface_the_spoke_also_names():
    """18 §10: `hosted` must never be optimistic."""
    text = SPOKE.read_text(encoding="utf-8")
    hosted = list(optimizers.hosted())
    assert hosted, "the catalogue claims to host nothing; §7 says it hosts ldo"
    for o in hosted:
        assert o.surface, f"{o.id} is hosted with no surface"
        assert o.surface in text, f"§7 does not name {o.surface} for {o.id}"


# --- the shape of the module itself ------------------------------------------


def test_ids_are_url_safe_and_unique():
    ids = [o.id for o in optimizers.CATALOGUE]
    assert len(ids) == len(set(ids))
    for optimizer_id in ids:
        assert re.fullmatch(r"[a-z][a-z0-9]*", optimizer_id), optimizer_id


def test_the_alias_is_the_slash_command_for_the_id():
    for o in optimizers.CATALOGUE:
        assert o.alias == f"/{o.id}"
        assert o.route == f"/optimizers/{o.id}/"


def test_every_record_carries_prose_and_a_skill():
    """The three fields the table does not carry are still required: a page with
    no summary is a row, and a reader who cannot find the skill is stuck."""
    for o in optimizers.CATALOGUE:
        assert o.skill, o.id
        assert len(o.summary.split()) >= 25, f"{o.id}: summary is a stub"
        assert o.artifacts, o.id


def test_an_unknown_id_is_an_error_not_a_default():
    with pytest.raises(optimizers.UnknownOptimizer):
        optimizers.get("nope")


def test_records_round_trip_as_json_types():
    import json

    payload = json.dumps(optimizers.as_records())
    back = json.loads(payload)
    assert len(back) == 9
    assert back[0]["id"] == "ldo" and back[0]["route"] == "/optimizers/ldo/"
    assert isinstance(back[0]["artifacts"], list)


def test_validate_refuses_a_hosted_record_with_no_surface():
    """The invariant that stops the catalogue advertising a product that is not
    built. Constructed by hand rather than mutating CATALOGUE, which is frozen."""
    bad = optimizers.Optimizer(
        id="x", name="x", alias="/x", passes=1, hosted=True, gate="g",
        domain="d", skill="s", summary="s" * 200, artifacts=("a",), surface=None,
    )
    with pytest.raises(AssertionError, match="no surface"):
        optimizers.validate([bad])
