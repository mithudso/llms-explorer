"""The plan table of component 15 §5, as data.

One plan (`free`) now, applied to every account — the site is free, supported
by donations (`explorer_api.billing`), not a paid tier ladder. Every number
below is transcribed from the spoke's feature table (`docs/site/components/
15-accounts-and-billing.md` §5); `tests/test_plans.py` asserts them directly
rather than parsing that table, since one plan's numbers are small enough to
compare by hand.

Two things live here and nowhere else:

* :data:`PLANS` — price, included credit and the quota dict for the plan.
* :data:`FEATURE_KINDS` — what *kind* of limit each quota is, which is what
  :func:`explorer_api.ledger.check_quota` dispatches on. A quota with no kind is
  a hole in enforcement, so the test asserts the two sets are equal.

``None`` in a quota means *no limit*; :data:`UNLIMITED` is its readable name.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

#: A quota of ``None`` is "no limit", exactly as the migration's seed writes it.
UNLIMITED: None = None

#: One plan. The comment on `PLAN_ORDER` used to explain why order mattered
#: (cheapest-first, for `upgrade_target`); with one plan there is no order to
#: keep, and no upgrade target to find — the site is free, supported by
#: donations (`explorer_api.billing`), not a paid tier ladder.
PLAN_ORDER: tuple[str, ...] = ("free",)

#: The quota keys, in the order the spoke's rows introduce them.
QUOTA_FEATURES: tuple[str, ...] = (
    "lint_max_bytes",
    "lint_per_day",
    "keyword_queries_per_day",
    "semantic_queries",
    "indexes",
    "index_max_units",
    "storage_gb",
    "corpus_max_tokens",
    "corpus_per_day",
    "private_trees",
    "publish",
    "overage",
)

#: How each quota is enforced. The four kinds are all `check_quota` knows:
#:
#: ``flag``    — the feature is on the plan or it is not (`True`/`False`).
#: ``choice``  — a named allowance; only :data:`METERED_CHOICES` are billable.
#: ``cap``     — a ceiling on *one* request's size, not on how many.
#: ``counter`` — how many in a window (daily) or in total (cumulative).
FEATURE_KINDS: Mapping[str, str] = {
    "lint_max_bytes": "cap",
    "lint_per_day": "counter",
    "keyword_queries_per_day": "counter",
    "semantic_queries": "choice",
    "indexes": "counter",
    "index_max_units": "cap",
    "storage_gb": "counter",
    # 19 §8: one is the size of a single request, the other is how many a day.
    # Different kinds on purpose — a cap refuses the request that is too big, a
    # counter refuses the sixth request of a day that were each fine.
    "corpus_max_tokens": "cap",
    "corpus_per_day": "counter",
    "private_trees": "counter",
    "publish": "flag",
    "overage": "choice",
}

#: The ``choice`` values that mean "yes, and it is metered". Anything else —
#: ``False``, ``"demo-only"`` — is a refusal. D7: the free tier's semantic
#: search is the 16-document demo, rate-limited and *not* billed, so it is not
#: an allowance a metered call may draw on.
METERED_CHOICES: frozenset[str] = frozenset({"credits", "opt-in"})


class UnknownPlan(KeyError):
    """A plan id that is not one of :data:`PLAN_ORDER`."""


class UnknownFeature(KeyError):
    """A quota key that is not in :data:`QUOTA_FEATURES`.

    Deliberately an error rather than ``None``: ``None`` reads as *unlimited*
    everywhere else in this module, so a typo'd feature name would silently
    hand out the farm.
    """


@dataclass(frozen=True, slots=True)
class Plan:
    """One row of 15 §5."""

    id: str
    name: str
    price_usd: Decimal
    included_credit_usd: Decimal
    quotas: Mapping[str, Any]

    @property
    def is_paid(self) -> bool:
        return self.price_usd > 0

    def quota(self, feature: str) -> Any:
        try:
            return self.quotas[feature]
        except KeyError:
            raise UnknownFeature(feature) from None

    def kind_of(self, feature: str) -> str:
        try:
            return FEATURE_KINDS[feature]
        except KeyError:
            raise UnknownFeature(feature) from None


def _plan(plan_id: str, name: str, price: str, credit: str, **quotas: Any) -> Plan:
    missing = set(QUOTA_FEATURES) - set(quotas)
    if missing:  # pragma: no cover - a construction error, caught at import
        raise AssertionError(f"plan {plan_id!r} is missing quotas: {sorted(missing)}")
    return Plan(
        id=plan_id,
        name=name,
        price_usd=Decimal(price),
        included_credit_usd=Decimal(credit),
        quotas=dict(quotas),
    )


#: 15 §5, transcribed. `tests/test_plans.py` asserts these values directly.
PLANS: Mapping[str, Plan] = {
    plan.id: plan
    for plan in (
        _plan(
            "free", "Free", price="0", credit="0",
            # "files ≤ 64 KB, 20/day" — binary KB, as the seeded quota reads.
            lint_max_bytes=65536,
            lint_per_day=20,
            keyword_queries_per_day=200,
            # D7: the 16-document demo, rate-limited and not billed.
            semantic_queries="demo-only",
            # "1 index ≤ 20k units, 200 MB"; storage is quoted decimally.
            indexes=1,
            index_max_units=20000,
            storage_gb=Decimal("0.2"),
            # 19 §8: "25k tokens/run, 5/day".
            corpus_max_tokens=25000,
            corpus_per_day=5,
            private_trees=1,
            publish=False,
            overage=False,
        ),
    )
}

assert list(PLANS) == list(PLAN_ORDER), "PLANS must stay in cheapest-first order"


def get(plan_id: str) -> Plan:
    """The plan, or :class:`UnknownPlan` — never a silent fallback to free."""
    try:
        return PLANS[plan_id]
    except KeyError:
        raise UnknownPlan(plan_id) from None


def quota(plan_id: str, feature: str) -> Any:
    """The limit ``plan_id`` has for ``feature``; ``None`` means unlimited."""
    return get(plan_id).quota(feature)


__all__ = [
    "FEATURE_KINDS",
    "METERED_CHOICES",
    "PLANS",
    "PLAN_ORDER",
    "QUOTA_FEATURES",
    "UNLIMITED",
    "Plan",
    "UnknownFeature",
    "UnknownPlan",
    "get",
    "quota",
]
