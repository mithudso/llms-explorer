"""The append-only ledger, and the one place a quota is enforced.

Component 15 §3 is the contract: every metered component writes a row, and the
sum of the rows is what the user owes. Two decisions this module makes explicit,
because 15 §3 states the columns but not their arithmetic:

**1. A ledger row's money is the row's total, not a per-unit rate.**
``numeric(12,6)`` cannot hold a per-token rate — mxbai at $0.10/1M is
$0.0000001 per token, which rounds to zero at six places, and a ledger of zeroes
is worse than no ledger. So ``units`` is the count, and ``unit_cost_usd`` /
``price_usd`` are that count's marginal cost and price *in dollars*. The
per-unit rates live where 15 §7 puts them — the ``prices`` table — and
:class:`PriceQuote` carries them. This is what makes §9's bar
("sum(rows) = job cost") true by construction.

**2. Rates are quoted per :data:`QUOTE_UNITS` of their kind**, exactly as 15 §3's
price list writes them: tokens and embeddings per 1M, storage per MB·month.

The price list itself is data. :data:`DEFAULT_PRICES` is 15 §3's published table
and is the floor; a row in the ``prices`` table overrides it, so a margin change
is an insert rather than a deploy. A model with neither raises
:class:`UnknownPrice` — a job billed at a guess is worse than a job that fails.

:func:`check_quota` is the single place a limit is enforced (the plan says so).
It dispatches on :data:`explorer_api.plans.FEATURE_KINDS` and refuses to guess:
a counter whose usage lives outside Postgres — docsets are in the per-user store
(master §5) — raises :class:`UncountableFeature` rather than allowing everything.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sqlalchemy import Date, Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from . import models as m
from . import plans

UTC = dt.UTC

#: 15 §3, §8: "target price ≥ 3× marginal cost"; Claude is resold at "list × 3".
MARGIN_MULTIPLE = Decimal(3)

#: `numeric(12,6)`: a tenth of a micro-dollar, matching `models.Money`.
MONEY_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")

#: How many units a price is quoted for, per ledger `kind` (15 §3's price list:
#: "$0.50 / 1M" for tokens, "$0.02 / MB·month" for storage).
QUOTE_UNITS: Mapping[str, Decimal] = {
    "input": Decimal(1_000_000),
    "output": Decimal(1_000_000),
    "embedding": Decimal(1_000_000),
    "storage_mb_month": Decimal(1),
}

#: 15 §3's `reason` for a row raised by a query rather than a job. Counting
#: these is how the free tier's keyword-query allowance is enforced.
QUERY_REASON = "query"


class UnknownPrice(LookupError):
    """No price in force for this (model, kind), in Postgres or the defaults."""

    def __init__(self, model: str, kind: str) -> None:
        self.model, self.kind = model, kind
        super().__init__(
            f"no price in force for model {model!r}, kind {kind!r}. Insert a row in "
            "`prices` (15 §7 — the list is owner-tunable) before metering it; a "
            "spend is never recorded at a guessed rate."
        )


class UncountableFeature(RuntimeError):
    """A counted quota whose usage this module cannot read from Postgres.

    Raised rather than defaulted to zero: the caller that owns the store —
    the docset registry, the artifact tree — must pass ``used=``.
    """

    def __init__(self, feature: str) -> None:
        self.feature = feature
        super().__init__(
            f"quota {feature!r} is counted outside Postgres; pass used=<count> "
            "from the store that owns it (master §5, one writer per store)."
        )


def money(value: Decimal | int) -> Decimal:
    """Quantize to the ledger's six places. The only rounding in this module."""
    return Decimal(value).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


@dataclass(frozen=True, slots=True)
class PriceQuote:
    """A rate: ``price_usd`` per ``QUOTE_UNITS[kind]`` units of ``model``."""

    model: str
    kind: str
    unit_cost_usd: Decimal
    price_usd: Decimal
    note: str | None = None

    def extend(self, units: int) -> tuple[Decimal, Decimal]:
        """``units`` at this rate → ``(marginal cost, price)``, both in dollars."""
        per = QUOTE_UNITS[self.kind]
        return (money(Decimal(units) * self.unit_cost_usd / per),
                money(Decimal(units) * self.price_usd / per))


#: 15 §3's price list, for the rows it prices numerically. The two Claude rows
#: are "API list price" × 3 — a number this repo does not own — so they are
#: deliberately absent: metering Claude requires the owner to insert the list
#: price of the day into `prices`, and until then :class:`UnknownPrice` says so.
DEFAULT_PRICES: tuple[PriceQuote, ...] = (
    PriceQuote("qwen3.5:35b", "input", Decimal("0.10"), Decimal("0.50"),
               "Ollama bulk, in/out same (power + amortised GPU)"),
    PriceQuote("qwen3.5:35b", "output", Decimal("0.10"), Decimal("0.50"),
               "Ollama bulk, in/out same"),
    PriceQuote("mxbai-embed-large", "embedding", Decimal("0.02"), Decimal("0.10"),
               "indexing, semantic queries"),
    PriceQuote("storage", "storage_mb_month", Decimal("0.005"), Decimal("0.02"),
               "uploaded docsets + artifacts"),
)

_DEFAULTS_BY_KEY: Mapping[tuple[str, str], PriceQuote] = {
    (p.model, p.kind): p for p in DEFAULT_PRICES
}


# --- prices ------------------------------------------------------------------


async def resolve_price(
    session: AsyncSession, model: str, kind: str, *, on: dt.date | None = None
) -> PriceQuote:
    """The rate in force for ``(model, kind)``: Postgres first, defaults after.

    "In force" means the newest `prices` row whose ``effective_from`` is not in
    the future, so tomorrow's price can be staged today without changing today's
    bills.
    """
    on = on or dt.datetime.now(UTC).date()
    stmt = (
        select(m.Price)
        .where(m.Price.model == model, m.Price.kind == kind,
               m.Price.effective_from <= on)
        .order_by(m.Price.effective_from.desc(), m.Price.id.desc())
        .limit(1)
    )
    row = (await session.execute(stmt)).scalars().first()
    if row is not None:
        return PriceQuote(row.model, row.kind, row.unit_cost_usd, row.price_usd, row.note)
    quote = _DEFAULTS_BY_KEY.get((model, kind))
    if quote is None:
        raise UnknownPrice(model, kind)
    return quote


async def seed_prices(session: AsyncSession) -> int:
    """Write :data:`DEFAULT_PRICES` into ``prices`` if they are not there.

    Optional: :func:`resolve_price` already falls back to them. This exists so
    an operator can see and edit the list in the database (15 §3) rather than
    having to know it is compiled in.
    """
    written = 0
    for quote in DEFAULT_PRICES:
        exists = await session.execute(
            select(m.Price.id).where(m.Price.model == quote.model,
                                     m.Price.kind == quote.kind).limit(1)
        )
        if exists.first() is None:
            session.add(m.Price(model=quote.model, kind=quote.kind,
                                unit_cost_usd=quote.unit_cost_usd,
                                price_usd=quote.price_usd, note=quote.note))
            written += 1
    return written


# --- writing -----------------------------------------------------------------


async def record(
    session: AsyncSession,
    user: m.User,
    component: str,
    kind: str,
    model: str,
    units: int,
    *,
    job: m.Job | None = None,
    call_id: str | None = None,
    api_key_id: str | None = None,
    client_ip: str | None = None,
    billable: bool = True,
    reason: str | None = None,
    at: dt.datetime | None = None,
) -> m.LedgerEntry:
    """Append one row of 15 §3's contract. Never updates; a correction is a row.

    ``billable=False`` still records the cost — 15 §8's failed verify gate means
    the work was done and paid for by us, and only that the *user* is not
    charged. :func:`usage` reports both totals so the margin stays visible.

    The row is added to the session but not committed: the caller owns the
    transaction, so a spend and the work it paid for land together or not at all.
    """
    if kind not in QUOTE_UNITS:
        raise ValueError(f"unknown ledger kind {kind!r}; expected one of {sorted(QUOTE_UNITS)}")
    if units < 0:
        raise ValueError(f"units must not be negative (got {units})")
    quote = await resolve_price(session, model, kind,
                                on=(at or dt.datetime.now(UTC)).date())
    cost_usd, price_usd = quote.extend(units)
    row = m.LedgerEntry(
        user_id=user.id,
        job_id=job.id if job is not None else None,
        call_id=call_id,
        api_key_id=api_key_id,
        client_ip=client_ip,
        component=component,
        model=model,
        kind=kind,
        units=units,
        unit_cost_usd=cost_usd,
        price_usd=price_usd,
        billable=billable,
        reason=reason,
    )
    if at is not None:
        row.at = at
    session.add(row)
    if billable and price_usd > ZERO:
        # The balance is debited in the same transaction as the row, so
        # `sum(billable rows)` and `credits.balance_usd` can never disagree.
        # Before this the balance was written only by Stripe and read only by
        # the dashboard, so "hard stop at zero" (master §7) had nothing to stop
        # on: an account could spend without limit at a balance of −$500.
        await _debit_credit(session, user, price_usd)
    await session.flush()
    return row


async def _debit_credit(session: AsyncSession, user: m.User, amount: Decimal) -> None:
    """Take ``amount`` off the account's balance, creating the row at zero first."""
    credit = await session.get(m.Credit, user.id, with_for_update=True)
    if credit is None:
        credit = m.Credit(user_id=user.id, balance_usd=ZERO)
        session.add(credit)
        await session.flush()
    credit.balance_usd = money(Decimal(credit.balance_usd) - amount)


# --- quotas ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class QuotaVerdict:
    """The answer :func:`check_quota` gives, and everything a 402 needs to say."""

    allowed: bool
    feature: str
    tier: str
    limit: Any
    used: int | None = None
    remaining: int | None = None
    upgrade_url: str | None = None
    reason: str | None = None

    def as_error(self) -> dict[str, Any]:
        """15 §5's structured refusal: ``{code, tier, upgrade_url}``."""
        return {"code": "quota", "feature": self.feature, "tier": self.tier,
                "limit": self.limit, "remaining": self.remaining,
                "upgrade_url": self.upgrade_url, "reason": self.reason}


async def _count_trees(session: AsyncSession, user: m.User) -> int:
    return int((await session.execute(
        select(func.count()).select_from(m.Tree).where(m.Tree.user_id == user.id)
    )).scalar_one())


def _start_of_day(now: dt.datetime | None = None) -> dt.datetime:
    return (now or dt.datetime.now(UTC)).astimezone(UTC).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


async def _count_lints_today(session: AsyncSession, user: m.User) -> int:
    return int((await session.execute(
        select(func.count()).select_from(m.Job).where(
            m.Job.user_id == user.id, m.Job.kind == "lint",
            m.Job.created_at >= _start_of_day(),
        )
    )).scalar_one())


async def _count_queries_today(session: AsyncSession, user: m.User) -> int:
    return int((await session.execute(
        select(func.count()).select_from(m.LedgerEntry).where(
            m.LedgerEntry.user_id == user.id,
            m.LedgerEntry.reason == QUERY_REASON,
            m.LedgerEntry.at >= _start_of_day(),
        )
    )).scalar_one())


async def _count_corpus_runs_today(session: AsyncSession, user: m.User) -> int:
    """Corpus syntheses this user has run today (19 §8).

    Counted off `jobs`, like lints, rather than off the ledger: a corpus run on
    the free tier is deterministic and writes no ledger row, so a ledger-based
    counter would let the free tier run without limit — which is precisely the
    tier the limit exists for.
    """
    return int((await session.execute(
        select(func.count()).select_from(m.Job).where(
            m.Job.user_id == user.id, m.Job.kind == CORPUS_JOB_KIND,
            m.Job.created_at >= _start_of_day(),
        )
    )).scalar_one())


#: Counted quotas this module can answer from Postgres. Anything else is
#: :class:`UncountableFeature` until the caller supplies ``used=``.
USAGE_COUNTERS: Mapping[str, Callable[[AsyncSession, m.User], Awaitable[int]]] = {
    "private_trees": _count_trees,
    "lint_per_day": _count_lints_today,
    "keyword_queries_per_day": _count_queries_today,
    "corpus_per_day": _count_corpus_runs_today,
}


async def check_quota(
    session: AsyncSession,
    user: m.User,
    feature: str,
    amount: int = 1,
    *,
    used: int | None = None,
    upgrade_url: str | None = None,
) -> QuotaVerdict:
    """Would ``amount`` more of ``feature`` be within ``user``'s plan?

    The single place a tier limit is enforced. Every threshold comes from
    :data:`explorer_api.plans.PLANS`; none is written here.
    """
    plan = plans.get(user.plan_id)
    limit = plan.quota(feature)          # UnknownFeature if the name is wrong
    kind = plan.kind_of(feature)

    def verdict(allowed: bool, **rest: Any) -> QuotaVerdict:
        url = None
        if not allowed:
            url = upgrade_url or plans.upgrade_url(plan.id, feature)
        return QuotaVerdict(allowed=allowed, feature=feature, tier=plan.id,
                            limit=limit, upgrade_url=url, **rest)

    if kind == "flag":
        return verdict(bool(limit),
                       reason=None if limit else f"{feature} is not on the {plan.id} plan")

    if kind == "choice":
        allowed = limit in plans.METERED_CHOICES
        return verdict(allowed, reason=None if allowed else f"{feature} is {limit!r} here")

    if kind == "cap":
        if limit is plans.UNLIMITED:
            return verdict(True, used=amount)
        allowed = amount <= limit
        return verdict(allowed, used=amount,
                       reason=None if allowed else f"{amount} exceeds the {limit} cap")

    # counter — daily or cumulative; both are "how many, against a ceiling".
    if limit is plans.UNLIMITED:
        # Deliberately does not count: an unlimited plan must not pay for a scan.
        return verdict(True)
    if used is None:
        counter = USAGE_COUNTERS.get(feature)
        if counter is None:
            raise UncountableFeature(feature)
        used = await counter(session, user)
    remaining = max(limit - used, 0)
    allowed = used + amount <= limit
    return verdict(allowed, used=used, remaining=remaining,
                   reason=None if allowed else f"{used}/{limit} already used")


# --- reading -----------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class UsageRow:
    """One ``(day, component, model)`` bucket of 15 §5's `/api/usage`."""

    day: dt.date
    component: str
    model: str
    units: int
    cost_usd: Decimal
    price_usd: Decimal
    billable_usd: Decimal


@dataclass(frozen=True, slots=True)
class UsageSummary:
    rows: list[UsageRow] = field(default_factory=list)
    total_usd: Decimal = ZERO
    billable_usd: Decimal = ZERO
    cost_usd: Decimal = ZERO
    units: int = 0

    @property
    def margin_usd(self) -> Decimal:
        return money(self.billable_usd - self.cost_usd)


async def usage(
    session: AsyncSession,
    user: m.User,
    since: dt.date | None = None,
    until: dt.date | None = None,
) -> UsageSummary:
    """15 §5's `GET /api/usage`: ledger aggregates by component, model and day.

    ``since``/``until`` are inclusive calendar dates in UTC, which is the only
    day boundary the ledger has — a user's local midnight is not a billing
    concept here.
    """
    day = cast(func.timezone("UTC", m.LedgerEntry.at), Date).label("day")
    billable_price = func.sum(
        m.LedgerEntry.price_usd * cast(m.LedgerEntry.billable, Integer)
    )
    stmt = (
        select(
            day,
            m.LedgerEntry.component,
            m.LedgerEntry.model,
            func.sum(m.LedgerEntry.units),
            func.sum(m.LedgerEntry.unit_cost_usd),
            func.sum(m.LedgerEntry.price_usd),
            billable_price,
        )
        .where(m.LedgerEntry.user_id == user.id)
        .group_by(day, m.LedgerEntry.component, m.LedgerEntry.model)
        .order_by(day, m.LedgerEntry.component, m.LedgerEntry.model)
    )
    if since is not None:
        stmt = stmt.where(m.LedgerEntry.at >= dt.datetime.combine(since, dt.time.min, UTC))
    if until is not None:
        end = dt.datetime.combine(until + dt.timedelta(days=1), dt.time.min, UTC)
        stmt = stmt.where(m.LedgerEntry.at < end)

    rows = [
        UsageRow(day=r[0], component=r[1], model=r[2], units=int(r[3]),
                 cost_usd=money(r[4]), price_usd=money(r[5]),
                 billable_usd=money(r[6] or ZERO))
        for r in (await session.execute(stmt)).all()
    ]
    return UsageSummary(
        rows=rows,
        total_usd=money(sum((r.price_usd for r in rows), ZERO)),
        billable_usd=money(sum((r.billable_usd for r in rows), ZERO)),
        cost_usd=money(sum((r.cost_usd for r in rows), ZERO)),
        units=sum(r.units for r in rows),
    )


async def credit_balance(session: AsyncSession, user: m.User) -> Decimal:
    """15 §7 `credits.balance_usd`; zero until Stripe (Task 6) tops it up."""
    balance = (await session.execute(
        select(m.Credit.balance_usd).where(m.Credit.user_id == user.id)
    )).scalars().first()
    return money(balance if balance is not None else ZERO)


__all__ = [
    "DEFAULT_PRICES",
    "MARGIN_MULTIPLE",
    "MONEY_QUANTUM",
    "QUERY_REASON",
    "QUOTE_UNITS",
    "USAGE_COUNTERS",
    "PriceQuote",
    "QuotaVerdict",
    "UncountableFeature",
    "UnknownPrice",
    "UsageRow",
    "UsageSummary",
    "check_quota",
    "credit_balance",
    "money",
    "record",
    "resolve_price",
    "seed_prices",
    "usage",
]
