"""Token estimation and the budget a free-tier request is measured against.

One estimator, declared once. The site's `tools/twins.py` publishes
``X-Markdown-Tokens`` as ``len(text) // 4``, the llms family's manifests count
the same way, and component 19's free cap is quoted in the same unit. Three
different estimators would mean the number on the pricing page, the number in
the header and the number the quota enforces were three different numbers, and
the first bug report would be about the gap between them.

:data:`CHARS_PER_TOKEN` is therefore deliberately dumb and deliberately shared.
It is an *estimate*: real BPE tokenisers land within roughly ±25 % of it on
English prose and further off on code and CJK. That is accurate enough for a
size ladder and a free-tier ceiling, and it costs no dependency, no model and no
network — which is what lets the same number be computed in the browser, in the
CLI with nothing installed, and in six client libraries.

Where a real count matters — billing an actual model call — the ledger records
the units the provider reported, not this estimate. Nothing in this module ever
prices anything.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

#: The estimator this whole estate declares. See the module docstring.
CHARS_PER_TOKEN = 4


def estimate(text: str) -> int:
    """Tokens in ``text``, by the declared estimator."""
    return len(text) // CHARS_PER_TOKEN


def estimate_all(texts: Iterable[str]) -> int:
    """Tokens across many strings.

    Sums per string rather than concatenating: the concatenation would round
    once instead of many times and read ~2 tokens per string higher, which turns
    into a free-tier ceiling that moves depending on how the caller chunked the
    upload.
    """
    return sum(estimate(t) for t in texts)


class BudgetExceeded(ValueError):
    """A request larger than the budget it was checked against.

    Carries the numbers so a 402 can state them: a refusal that says "too large"
    without saying how large, against what, is a refusal the caller cannot act
    on.
    """

    def __init__(self, used: int, limit: int, *, unit: str = "tokens") -> None:
        self.used = used
        self.limit = limit
        self.unit = unit
        super().__init__(f"{used} {unit} exceeds the {limit} {unit} budget")


@dataclass(frozen=True, slots=True)
class Budget:
    """A ceiling on one request's size, and the verdict of checking it.

    ``limit`` of ``None`` is *no ceiling*, matching `plans.UNLIMITED` — the same
    convention the plan table uses, so a paid plan's absent cap needs no special
    case at any call site.
    """

    limit: int | None

    @property
    def unlimited(self) -> bool:
        return self.limit is None

    def remaining(self, used: int) -> int | None:
        if self.limit is None:
            return None
        return max(self.limit - used, 0)

    def allows(self, used: int) -> bool:
        return self.limit is None or used <= self.limit

    def check(self, used: int) -> int:
        """``used``, or raise :class:`BudgetExceeded`."""
        if not self.allows(used):
            raise BudgetExceeded(used, self.limit or 0)
        return used


#: A budget that refuses nothing, for the paid path and for local CLI runs.
UNLIMITED = Budget(None)


def truncate_to(text: str, limit: int) -> str:
    """The longest prefix of ``text`` that fits ``limit`` tokens.

    Used for the size ladder (``llms-small.txt``), never for enforcement: a
    quota that silently truncated the input would bill for work on material the
    caller did not know had been dropped. Enforcement raises; rendering trims.
    """
    if limit <= 0:
        return ""
    return text[: limit * CHARS_PER_TOKEN]


__all__ = [
    "CHARS_PER_TOKEN",
    "UNLIMITED",
    "Budget",
    "BudgetExceeded",
    "estimate",
    "estimate_all",
    "truncate_to",
]
