#!/usr/bin/env python3
"""gen_plans — the price table, as build-time JSON.

`api/explorer_api/plans.py` is the one place tier numbers live (component 15 §5); this
script imports it directly and writes `src/data/plans.json` so the pricing page never
hand-transcribes a number the API itself might change. Pure static data, no network and
no database, so — like gen_tree.py — CI can regenerate it anywhere and diff a stale copy.

Nothing here reads the wall clock: unlike gen_tree.py (which stamps the newest
`researchedAt`), the plan table has no per-row timestamp to derive one from, and a
wall-clock `generated` field would make the CI diff check below fail every day even when
plans.py has not changed — the exact bug this docstring exists to warn the next editor
away from.

Usage: gen_plans.py [--out src/data/plans.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]                 # site/
REPO = HERE.parent
sys.path.insert(0, str(REPO / "api"))

from explorer_api import plans as P  # noqa: E402


def _jsonable(value: object) -> object:
    """`Decimal` is the only quota/price type `json.dumps` cannot handle
    natively; everything else (int, bool, str, None) already round-trips."""
    return str(value) if isinstance(value, Decimal) else value


def build() -> dict:
    return {
        "features": list(P.QUOTA_FEATURES),
        "plans": [
            {
                "id": plan.id,
                "name": plan.name,
                "price_usd": _jsonable(plan.price_usd),
                "included_credit_usd": _jsonable(plan.included_credit_usd),
                "quotas": {k: _jsonable(v) for k, v in plan.quotas.items()},
            }
            for plan in P.PLANS.values()
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=HERE / "src" / "data" / "plans.json")
    args = ap.parse_args()
    data = build()
    args.out.write_text(json.dumps(data, indent=2) + "\n")
    print(f"wrote {args.out} ({len(data['plans'])} plans)")


if __name__ == "__main__":
    main()
