"""The plan table of component 15 §5, as data.

Global constraint of the step-3 plan: *"Tier numbers live in component 15 §5 and
are loaded from `api/plans.py` as data — no tier threshold is written inline in
a route."* This module is that load. Every number below is transcribed from the
spoke's feature table, and `tests/test_plans.py` parses that table and fails the
build if the two ever disagree — so the document stays the authority even though
the code is what runs.

Three things live here and nowhere else:

* :data:`PLANS` — price, included credit and the quota dict per plan.
* :data:`FEATURE_KINDS` — what *kind* of limit each quota is, which is what
  :func:`explorer_api.ledger.check_quota` dispatches on. A quota with no kind is
  a hole in enforcement, so the test asserts the two sets are equal.
* :func:`upgrade_target` / :func:`upgrade_url` — the cheapest plan that actually
  lifts the limit the caller just hit, so a 402 can say what to buy rather than
  pointing at a price page and hoping.

``None`` in a quota means *no limit*; :data:`UNLIMITED` is its readable name.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

#: A quota of ``None`` is "no limit", exactly as the migration's seed writes it.
UNLIMITED: None = None

#: Where a refused request sends the user. Path only up to the plan: the site
#: owns the page, this module owns which plan to name.
BILLING_URL = "https://llms-explorer.com/billing"

#: 15 §5 column order — also cheapest-first, which is what makes
#: :func:`upgrade_target` "the *cheapest* plan that lifts the limit".
PLAN_ORDER: tuple[str, ...] = ("free", "starter", "pro")

#: The quota keys, in the order the spoke's rows introduce them.
QUOTA_FEATURES: tuple[str, ...] = (
    "lint_max_bytes",
    "lint_per_day",
    "lint_model_passes",
    "keyword_queries_per_day",
    "semantic_queries",
    "indexes",
    "index_max_units",
    "storage_gb",
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
    "lint_model_passes": "flag",
    "keyword_queries_per_day": "counter",
    "semantic_queries": "choice",
    "indexes": "counter",
    "index_max_units": "cap",
    "storage_gb": "counter",
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


#: 15 §5, transcribed. `tests/test_plans.py` re-parses the spoke and compares.
PLANS: Mapping[str, Plan] = {
    plan.id: plan
    for plan in (
        _plan(
            "free", "Free", price="0", credit="0",
            # "files ≤ 64 KB, 20/day" — binary KB, as the seeded quota reads.
            lint_max_bytes=65536,
            lint_per_day=20,
            lint_model_passes=False,
            keyword_queries_per_day=200,
            # D7: the 16-document demo, rate-limited and not billed.
            semantic_queries="demo-only",
            # "1 index ≤ 20k units, 200 MB"; storage is quoted decimally.
            indexes=1,
            index_max_units=20000,
            storage_gb=Decimal("0.2"),
            private_trees=1,
            publish=False,
            overage=False,
        ),
        _plan(
            "starter", "Starter", price="9", credit="10",
            lint_max_bytes=UNLIMITED,
            lint_per_day=UNLIMITED,
            lint_model_passes=True,
            keyword_queries_per_day=5000,
            semantic_queries="credits",
            indexes=5,
            index_max_units=UNLIMITED,
            storage_gb=Decimal("5"),
            private_trees=3,
            publish=True,
            overage="opt-in",
        ),
        _plan(
            "pro", "Pro", price="39", credit="50",
            lint_max_bytes=UNLIMITED,
            lint_per_day=UNLIMITED,
            lint_model_passes=True,
            keyword_queries_per_day=50000,
            semantic_queries="credits",
            indexes=50,
            index_max_units=UNLIMITED,
            storage_gb=Decimal("50"),
            private_trees=20,
            publish=True,
            overage="opt-in",
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


def _is_better(candidate: Any, current: Any, kind: str) -> bool:
    """Would ``candidate`` let through something ``current`` refuses?"""
    if kind == "flag":
        return bool(candidate) and not bool(current)
    if kind == "choice":
        return candidate in METERED_CHOICES and current not in METERED_CHOICES
    if candidate is UNLIMITED:
        return current is not UNLIMITED
    if current is UNLIMITED:
        return False
    return candidate > current


def upgrade_target(plan_id: str, feature: str) -> Plan | None:
    """The cheapest plan above ``plan_id`` whose ``feature`` limit is higher.

    ``None`` when there is nothing left to sell — which is the honest answer for
    a Pro user at a hard limit, and stops a 402 from advertising a plan that
    would not have helped.
    """
    current = quota(plan_id, feature)
    kind = get(plan_id).kind_of(feature)
    for candidate_id in PLAN_ORDER[PLAN_ORDER.index(plan_id) + 1:]:
        candidate = PLANS[candidate_id]
        if _is_better(candidate.quota(feature), current, kind):
            return candidate
    return None


def upgrade_url(plan_id: str, feature: str, *, base_url: str = BILLING_URL) -> str | None:
    """Where to send a caller this limit just refused, or ``None`` if nowhere."""
    target = upgrade_target(plan_id, feature)
    if target is None:
        return None
    return f"{base_url}?plan={target.id}&reason={feature}"


__all__ = [
    "BILLING_URL",
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
    "upgrade_target",
    "upgrade_url",
]
