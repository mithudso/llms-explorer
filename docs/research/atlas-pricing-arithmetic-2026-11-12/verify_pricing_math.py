"""Firsthand conditional arithmetic only; no Atlas or invoice measurement."""

import json
from decimal import Decimal, localcontext
from fractions import Fraction


def require(condition, label):
    if not condition:
        raise RuntimeError(label)


def ratio(numerator, denominator):
    d = Decimal(numerator) / Decimal(denominator)
    f = Fraction(numerator) / Fraction(denominator)
    require(
        d == Decimal(f.numerator) / Decimal(f.denominator),
        "independent Fraction replay",
    )
    return format(d, "f")


def main():
    with localcontext() as context:
        context.prec = 40
        hourly = Decimal("0.08") * Decimal(730)
        require(hourly == Decimal("58.40"), "illustrative hourly multiplication")
        require(
            Fraction("0.08") * Fraction(730) == Fraction("58.40"),
            "hourly Fraction replay",
        )
        shared = Decimal(57)
        cap = Decimal(30)
        threshold = next(n for n in range(1, 10) if cap * n > shared)
        require(
            threshold == 2 and cap < shared < 2 * cap,
            "integer fleet threshold under stated assumptions",
        )
        component_sum = Decimal(700) + Decimal(1000)
        require(component_sum == Decimal(1700), "reported component addition")
        result = {
            "schema": "conditional-pricing-arithmetic/v1",
            "kind": "firsthand synthetic calculation; not vendor benchmark or measured spend",
            "decimal_precision": context.prec,
            "independent_fraction_replay": "passed",
            "independent_origin_credit": 0,
            "actual_invoice_or_TCO_measurement": False,
            "assumptions": {
                "periods_and_charge_scope": "Amounts are comparable only if their periods, currency, geography, applicable terms and included charge components match.",
                "fleet": "Each Flex cluster charge component is assumed at a 30 currency-unit cap; one shared cluster is assumed to cost 57 for the same period and charge scope; aggregate workload must fit. Other service charges are excluded.",
                "headline": "56.94 and 0.08 are stated inputs. 730 hours is an explicit illustration; the calculation does not establish the vendor headline's period or configuration.",
                "case_study": "3000 is an illustrative baseline for a post reporting over 3000. 160 is its reported replacement server amount. Availability, staffing, taxes, backup and service scopes differ or remain unspecified.",
            },
            "values": {
                "headline_to_flex_cap_ratio": ratio("56.94", "30"),
                "assumed57_to_flex_cap_ratio": ratio("57", "30"),
                "minimum_integer_fleet_at_cap_for_possible_saving": threshold,
                "one_flex_at_cap": "30",
                "two_flex_at_cap": "60",
                "illustrative_730h_at_008": format(hourly, "f"),
                "difference_from_5694": format(hourly - Decimal("56.94"), "f"),
                "reported3000_to160_cash_change_percent": ratio("284000", "3000"),
                "reported700_plus1000": format(component_sum, "f"),
                "component_share_using3000_baseline_percent": ratio("170000", "3000"),
            },
            "bounds": {
                "two_clusters_not_sufficient_for_savings": "The integer threshold is necessary only under the stated cap/model; two low-use clusters can cost less than the assumed shared cluster.",
                "over 3000_baseline": "With replacement amount 160 fixed, a baseline strictly above 3000 makes its arithmetic cash reduction exceed 94.6666 percent. A component amount 1700 divided by a total strictly above 3000 is below 56.6666 percent.",
                "no_generalization": "These calculations do not establish actual savings, TCO, equivalent resilience, current prices, contract terms or product fitness.",
            },
        }
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
