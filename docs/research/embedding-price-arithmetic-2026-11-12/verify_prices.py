#!/usr/bin/env python3
"""Reproduce conditional embedding-price arithmetic without vendor/API claims."""

import argparse
import json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path


def nonnegative(value: str) -> Decimal:
    number = Decimal(value)
    if not number.is_finite() or number < 0:
        raise ValueError("inputs must be finite and nonnegative")
    return number


def standard_cost(volume: str, remaining_allowance: str, rate: str) -> Decimal:
    tokens = nonnegative(volume)
    allowance = nonnegative(remaining_allowance)
    price = nonnegative(rate)
    return max(Decimal(0), tokens - allowance) * price


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def calculate() -> dict:
    rate = nonnegative("0.06")
    discount = nonnegative("0.33")
    factor = Decimal(1) - discount
    amounts = {
        "standard_1B_fresh_200M": standard_cost("1000", "200", "0.06"),
        "standard_1B_exhausted": standard_cost("1000", "0", "0.06"),
        "standard_200M_fresh_200M": standard_cost("200", "200", "0.06"),
        "standard_100M_fresh_200M": standard_cost("100", "200", "0.06"),
        "batch_1B_no_free_credits": Decimal("1000") * rate * factor,
        "batch_200M_no_free_credits": Decimal("200") * rate * factor,
    }
    expected = {
        "standard_1B_fresh_200M": "48.00",
        "standard_1B_exhausted": "60.00",
        "standard_200M_fresh_200M": "0.00",
        "standard_100M_fresh_200M": "0.00",
        "batch_1B_no_free_credits": "40.20",
        "batch_200M_no_free_credits": "8.04",
    }
    for name, amount in amounts.items():
        check(amount == Decimal(expected[name]), f"wrong result: {name}")
    check(factor == Decimal("0.67"), "wrong discount multiplier")
    check(
        amounts["batch_200M_no_free_credits"] > amounts["standard_200M_fresh_200M"],
        "batch counterexample failed",
    )
    ratio = Fraction(Decimal("0.02")) / Fraction(rate)
    check(ratio == Fraction(1, 3), "wrong rate ratio")
    check(Decimal("0.02") == Decimal("0.02"), "equal rate check failed")
    rejected = ["-1", "NaN", "Infinity", "-Infinity"]
    for bad_value in rejected:
        for position in range(3):
            inputs = ["1000", "200", "0.06"]
            inputs[position] = bad_value
            try:
                standard_cost(*inputs)
            except ValueError:
                continue
            raise RuntimeError(f"accepted invalid input at position {position}")
    return {
        "schema": "conditional-embedding-price-arithmetic/v1",
        "scope": "synthetic arithmetic only; every price and allowance is assumed",
        "assumptions": {
            "volume_unit": "million billable tokens",
            "currency": "USD",
            "standard_rate_per_million": str(rate),
            "fresh_standard_allowance_millions": "200",
            "batch_discount_fraction": str(discount),
            "batch_multiplier": str(factor),
            "batch_free_credits": False,
            "inference_scope": "any-geography base rate; surcharges excluded",
            "same_token_count_across_providers": True,
        },
        "results_usd": {name: format(amount, ".2f") for name, amount in amounts.items()},
        "list_rate_comparison": {
            "assumed_rates_per_million": ["0.02", "0.02", "0.06"],
            "first_two_rates_equal": True,
            "first_to_third_ratio": str(ratio),
        },
        "invalid_inputs_rejected_at_each_argument": rejected,
        "network_requests": 0,
        "checks_passed": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(calculate(), indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
