# api/tests/test_plans.py
"""`plans.PLANS` is component 15 §5, as data — and this file proves it.

The point of this module is :func:`test_the_plans_match_the_spoke`: it parses
the feature table out of `docs/site/components/15-accounts-and-billing.md` §5
and asserts every number in :data:`explorer_api.plans.PLANS` came from there.
Edit the spoke without editing the code (or the reverse) and CI fails here,
where the difference is a diff, rather than in production, where the difference
is money.

The parser is deliberately written *here* and not imported from `plans.py`:
a drift guard that shares its reading of the document with the code it checks
guards nothing.
"""

from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import select

from explorer_api import models as m
from explorer_api import plans

REPO_ROOT = Path(__file__).resolve().parents[2]
SPOKE = REPO_ROOT / "docs" / "site" / "components" / "15-accounts-and-billing.md"

DASH = "—"          # — , the "not available" cell
TICK = "✓"          # ✓ , the "included" cell
LEQ = "≤"           # ≤ , as in "files ≤ 64 KB"


# --- reading the spoke -------------------------------------------------------


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
        if all(set(c) <= {"-", ":"} for c in cells):      # the |---|---| rule
            continue
        rows.append(cells)
    return rows


def _plan_header(cells: list[str]) -> list[tuple[str, Decimal]]:
    """``Starter ($9/mo)`` → ``("starter", Decimal("9"))``, in column order."""
    out = []
    for cell in cells[1:-1]:                              # drop Feature / Metered unit
        name = cell.split("(")[0].strip()
        price = re.search(r"\$([\d.]+)/mo", cell)
        out.append((name.lower(), Decimal(price.group(1)) if price else Decimal("0")))
    return out


# --- cell parsers, one per row of the §5 table -------------------------------


def _count(cell: str) -> int | None:
    """``200/day`` → 200 · ``5k/day`` → 5000 · ``unlimited`` → None."""
    if "unlimited" in cell:
        return None
    match = re.search(r"(\d+)\s*(k?)", cell)
    assert match, cell
    return int(match.group(1)) * (1000 if match.group(2) else 1)


def _bytes(cell: str) -> int:
    """``64 KB`` → 65536. Byte sizes are binary; see :func:`_gigabytes`."""
    match = re.search(r"(\d+)\s*KB", cell)
    assert match, cell
    return int(match.group(1)) * 1024


def _gigabytes(cell: str) -> Decimal:
    """``200 MB`` → ``0.2`` · ``5 GB`` → ``5``.

    Storage is quoted decimally (200 MB *is* 0.2 GB in the spoke's own seed),
    unlike the binary KB of :func:`_bytes`. Both conventions are the spoke's.
    """
    match = re.search(r"([\d.]+)\s*(MB|GB)", cell)
    assert match, cell
    value = Decimal(match.group(1))
    return value / 1000 if match.group(2) == "MB" else value


def _flag(cell: str) -> bool:
    """A dash is "no"; anything else in a yes/no row is "yes"."""
    return cell != DASH


def _lint_deterministic(cell: str) -> dict[str, object]:
    if "unlimited" in cell:
        return {"lint_max_bytes": None, "lint_per_day": None}
    return {"lint_max_bytes": _bytes(cell), "lint_per_day": _count(cell.split(",")[-1])}


def _index_a_docset(cell: str) -> dict[str, object]:
    units = re.search(rf"{LEQ}\s*(\d+)k units", cell)
    return {
        "indexes": int(re.match(r"(\d+)", cell).group(1)),
        "index_max_units": int(units.group(1)) * 1000 if units else None,
        "storage_gb": _gigabytes(cell),
    }


def _corpus(cell: str) -> dict[str, object]:
    """``25k tokens/run, 5/day`` → both quotas · ``unlimited`` → both unlimited.

    One table cell, two quota keys, exactly like the lint row: the spoke states
    a per-request size and a per-day count in the same breath because that is
    how a user thinks about it, and 19 §8 splits them into a `cap` and a
    `counter` because that is how enforcement works.
    """
    if "unlimited" in cell:
        return {"corpus_max_tokens": None, "corpus_per_day": None}
    tokens, per_day = cell.split(",", 1)
    return {"corpus_max_tokens": _count(tokens), "corpus_per_day": _count(per_day)}


def _semantic(cell: str) -> str:
    return "demo-only" if "demo" in cell else "credits"


def _overage(cell: str) -> object:
    return False if cell == DASH else "opt-in"


def _money(cell: str) -> Decimal:
    return Decimal(cell.lstrip("$"))


#: Row label prefix → the quota keys it sets. Rows the table carries for the
#: reader but that set no quota (the always-free surfaces, the credit-metered
#: producers) are absent on purpose: they are features, not limits.
ROW_PARSERS = {
    "Lint, deterministic passes": _lint_deterministic,
    "Lint, model passes": lambda c: {"lint_model_passes": _flag(c)},
    "Keyword queries": lambda c: {"keyword_queries_per_day": _count(c)},
    "Semantic / hybrid queries": lambda c: {"semantic_queries": _semantic(c)},
    "Index a docset": _index_a_docset,
    "Corpus synthesis": _corpus,
    "Private trees": lambda c: {"private_trees": _count(c)},
    "Publish to shared catalogue": lambda c: {"publish": _flag(c)},
    "Overage": lambda c: {"overage": _overage(c)},
}


def parse_spoke() -> dict[str, dict[str, object]]:
    """The §5 table as ``{plan_id: {"price_usd", "included_credit_usd", "quotas"}}``."""
    rows = _table_rows("| Feature |")
    header = _plan_header(rows[0])
    parsed: dict[str, dict[str, object]] = {
        plan_id: {"price_usd": price, "included_credit_usd": None, "quotas": {}}
        for plan_id, price in header
    }
    for cells in rows[1:]:
        label, values = cells[0], cells[1:-1]
        if label.startswith("Monthly included credits"):
            for (plan_id, _), cell in zip(header, values, strict=True):
                parsed[plan_id]["included_credit_usd"] = _money(cell)
            continue
        for prefix, parser in ROW_PARSERS.items():
            if label.startswith(prefix):
                for (plan_id, _), cell in zip(header, values, strict=True):
                    parsed[plan_id]["quotas"].update(parser(cell))
                break
    return parsed


# --- the drift guard ---------------------------------------------------------


def test_the_spoke_still_has_the_table_this_test_reads():
    """Guard the guard: a silent parse of nothing would pass everything."""
    spoke = parse_spoke()
    assert set(spoke) == {"free", "starter", "pro"}
    assert len(spoke["free"]["quotas"]) == len(plans.QUOTA_FEATURES)


def test_the_plans_match_the_spoke():
    """`PLANS` is 15 §5. Any drift between the doc and the code fails here."""
    spoke = parse_spoke()
    assert list(plans.PLANS) == ["free", "starter", "pro"]
    for plan_id, expected in spoke.items():
        plan = plans.PLANS[plan_id]
        assert plan.price_usd == expected["price_usd"], plan_id
        assert plan.included_credit_usd == expected["included_credit_usd"], plan_id
        for feature, value in expected["quotas"].items():
            got = plan.quotas[feature]
            assert got == value, f"{plan_id}.{feature}: code {got!r} != spoke {value!r}"
        assert set(plan.quotas) == set(expected["quotas"]), plan_id


def test_the_prices_match_the_spoke():
    """`ledger.DEFAULT_PRICES` is 15 §3's price list, for the priced rows."""
    from explorer_api import ledger

    rows = _table_rows("| Model / unit |")
    quoted: dict[str, tuple[Decimal, Decimal]] = {}
    for cells in rows[1:]:
        cost = re.search(r"\$([\d.]+)", cells[1])
        price = re.search(r"\$([\d.]+)", cells[2])
        if cost and price:                                # skip "API list price"/"list × 3"
            quoted[cells[0]] = (Decimal(cost.group(1)), Decimal(price.group(1)))
    assert quoted, "15 §3's price list lost its numbers"

    by_model = {(p.model, p.kind): p for p in ledger.DEFAULT_PRICES}
    for label, (cost, price) in quoted.items():
        model = re.search(r"`([^`]+)`", label)
        key = (model.group(1) if model else "storage",
               "storage_mb_month" if "Storage" in label
               else "embedding" if "embed" in label else "input")
        assert key in by_model, f"15 §3 prices {label!r}; DEFAULT_PRICES has no {key}"
        assert by_model[key].unit_cost_usd == cost, key
        assert by_model[key].price_usd == price, key


def test_the_margin_multiple_is_the_one_the_spoke_states():
    """§8: "target price ≥ 3× marginal cost"; §3: Claude is "list × 3"."""
    from explorer_api import ledger

    text = SPOKE.read_text(encoding="utf-8")
    assert f"{ledger.MARGIN_MULTIPLE}× marginal cost" in text
    for price in ledger.DEFAULT_PRICES:
        assert price.price_usd >= price.unit_cost_usd * ledger.MARGIN_MULTIPLE


# --- the shape of the module itself ------------------------------------------


def test_every_quota_feature_is_classified():
    """`check_quota` dispatches on the kind; an unclassified feature is a hole."""
    assert set(plans.FEATURE_KINDS) == set(plans.QUOTA_FEATURES)
    assert set(plans.FEATURE_KINDS.values()) <= {"flag", "choice", "cap", "counter"}


def test_an_unknown_plan_is_an_error_not_a_default():
    with pytest.raises(plans.UnknownPlan):
        plans.get("enterprise")
    with pytest.raises(plans.UnknownPlan):
        plans.quota("enterprise", "publish")


def test_quota_reads_a_feature_off_the_plan():
    assert plans.quota("free", "private_trees") == 1
    assert plans.quota("pro", "private_trees") == 20
    assert plans.quota("starter", "lint_per_day") is plans.UNLIMITED


def test_an_unknown_feature_is_an_error_not_none():
    """Silently returning None would read as "unlimited" and give the farm away."""
    with pytest.raises(plans.UnknownFeature):
        plans.quota("free", "unlimited_everything")


def test_the_upgrade_target_is_the_cheapest_plan_that_lifts_the_limit():
    assert plans.upgrade_target("free", "private_trees").id == "starter"
    assert plans.upgrade_target("starter", "private_trees").id == "pro"
    assert plans.upgrade_target("pro", "private_trees") is None
    assert plans.upgrade_target("free", "publish").id == "starter"


def test_the_upgrade_url_names_the_plan_to_buy():
    url = plans.upgrade_url("free", "private_trees")
    assert url.startswith("https://") and "starter" in url
    assert plans.upgrade_url("pro", "private_trees") is None


# --- code vs database --------------------------------------------------------


async def test_the_seeded_rows_match_the_module(session):
    """Task 2 seeded `plans`; this module is the authority. They must agree."""
    rows = (await session.execute(select(m.Plan))).scalars().all()
    assert {r.id for r in rows} == set(plans.PLANS)
    for row in rows:
        plan = plans.PLANS[row.id]
        assert row.price_usd == plan.price_usd
        assert row.included_credit_usd == plan.included_credit_usd
        for feature, value in plan.quotas.items():
            seeded = row.quotas[feature]
            if isinstance(value, Decimal):
                seeded = Decimal(str(seeded))
            assert seeded == value, f"{row.id}.{feature}: db {seeded!r} != code {value!r}"
