"""`GET /api/usage` — the ledger, aggregated (component 15 §5).

15 §9's bar is that "dashboard numbers equal `/api/usage` aggregates", so this
route does no arithmetic of its own: it hands the window to
:func:`explorer_api.ledger.usage` and serialises what comes back.

Money crosses the wire as a **string** at six decimal places. JSON numbers are
IEEE doubles, and a dashboard that renders `0.1` for a row the ledger stores as
`0.100000` is the float bug the whole module set exists to avoid.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_serializer
from sqlalchemy.ext.asyncio import AsyncSession

from .. import ledger, models as m, plans
from ..db import get_session
# The single session dependency, imported directly. What this replaces was a
# `try: from ..auth import get_current_user` that named a function
# `explorer_api/auth.py` does not define, so the `except ImportError` stub —
# which 401s unconditionally — is what actually ran.
from .auth import current_user as get_current_user


router = APIRouter(prefix="/api", tags=["usage"])

#: The signed-in account, and one session per request. Annotated aliases
#: rather than defaults, so no callable is evaluated at import time.
CurrentUser = Annotated[m.User, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_session)]
FromDate = Annotated[dt.date | None, Query(alias="from",
                                           description="inclusive UTC start date")]
ToDate = Annotated[dt.date | None, Query(description="inclusive UTC end date")]


class MoneyModel(BaseModel):
    """Base for responses carrying money: every `Decimal` leaves as a string."""

    @field_serializer("*", when_used="json", check_fields=False)
    def _money_as_string(self, value: object) -> object:
        return str(ledger.money(value)) if isinstance(value, Decimal) else value


class UsageRowOut(MoneyModel):
    day: dt.date
    component: str
    model: str
    units: int
    cost_usd: Decimal
    price_usd: Decimal
    billable_usd: Decimal


class UsageOut(MoneyModel):
    from_: dt.date | None = Field(default=None, alias="from")
    to: dt.date | None = None
    tier: str
    units: int
    total_usd: Decimal
    billable_usd: Decimal
    credit_balance_usd: Decimal
    included_credit_usd: Decimal
    rows: list[UsageRowOut]

    model_config = {"populate_by_name": True}


@router.get("/usage", response_model=UsageOut, response_model_by_alias=True)
async def read_usage(
    user: CurrentUser,
    session: DbSession,
    from_: FromDate = None,
    to: ToDate = None,
) -> UsageOut:
    """Spend by day, component and model for the signed-in user only."""
    if from_ and to and from_ > to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"`from` ({from_}) is after `to` ({to})",
        )
    summary = await ledger.usage(session, user, since=from_, until=to)
    plan = plans.get(user.plan_id)
    return UsageOut(
        from_=from_,
        to=to,
        tier=plan.id,
        units=summary.units,
        total_usd=summary.total_usd,
        billable_usd=summary.billable_usd,
        credit_balance_usd=await ledger.credit_balance(session, user),
        included_credit_usd=plan.included_credit_usd,
        rows=[UsageRowOut(**asdict(row)) for row in summary.rows],
    )


__all__ = ["get_current_user", "router"]
