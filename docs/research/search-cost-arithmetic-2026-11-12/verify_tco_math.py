"""Conditional arithmetic only; the inputs are assumptions, not price attestations."""
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, getcontext
from fractions import Fraction
import json

getcontext().prec = 40


def calculate(number):
    n = number
    hourly_low = n("0.11")
    hourly_high = n("0.12")
    hours = n("730")
    node_count = n("2")
    floor_low = node_count * hourly_low * hours
    floor_high = node_count * hourly_high * hours
    family_pairs = [("8", ".11", ".24"), ("16", ".21", ".48"),
                    ("32", ".43", ".99"), ("64", ".89", "1.77"),
                    ("128", "1.68", "3.26")]
    relative = {ram: n(low) / n(high) * n("100") for ram, low, high in family_pairs}
    historical_pairs = {"high_s20": (".12", ".12"), "high_s30": (".23", ".24"),
                        "high_s40": (".48", ".48"), "high_s50": (".98", ".99"),
                        "high_s80": ("3.22", "3.26"), "low_s30": (".11", ".11"),
                        "low_s40": (".21", ".21"), "low_s110": ("5.79", "5.87")}
    movement = {key: (n(new) - n(old)) / n(old) * n("100")
                for key, (old, new) in historical_pairs.items()}
    ranges = {"100k": ("150", "250", "20", "40"),
              "5m": ("1200", "2000", "300", "1000"),
              "50m": ("5000", "8000", "500", "1000")}
    savings = {}
    for key, (alo, ahi, blo, bhi) in ranges.items():
        a = (n(alo) + n(ahi)) / n("2")
        b = (n(blo) + n(bhi)) / n("2")
        savings[key] = {"first_midpoint": a, "second_midpoint": b,
                        "relative_difference_percent": (a - b) / a * n("100")}
    return {
        "two_node_730h_floor": {"at_011_per_node_hour": floor_low,
                                "at_012_per_node_hour": floor_high},
        "equal_scope_floor_comparison": {"first_floor": floor_low,
                                         "second_assumed_minimum": n("50"),
                                         "arithmetic_difference": floor_low - n("50")},
        "equal_ram_hourly_ratio": {"048_divided_by_021": n(".48") / n(".21"),
                                   "high_ram_per_vcpu": n("16") / n("8"),
                                   "low_ram_per_vcpu": n("16") / n("2")},
        "hypothetical_index_excess": {"index_gb": n("10"), "available_gb": n("3"),
                                      "difference_gb": n("10") - n("3")},
        "heuristic_product_only": {"nodes": n("2"), "vcpu_per_node": n("2"),
                                   "assumed_qps_per_vcpu": n("10"),
                                   "product_qps": n("2") * n("2") * n("10")},
        "storage_family_hourly_difference": {"baseline": n(".48"), "alternative": n(".25"),
            "relative_difference_percent": (n(".48") - n(".25")) / n(".48") * n("100")},
        "per_shard_node_multiplication": {"nodes_per_shard": n("2"), "shards": n("3"),
                                           "total_nodes": n("2") * n("3")},
        "historical_list_movements_percent": movement,
        "matched_period_cluster_plus_search": {
            "assumed_matching_cluster_period_cost": n("57"),
            "at_two_012_nodes": n("57") + floor_high,
            "at_two_024_nodes": n("57") + node_count * n(".24") * hours},
        "raw_vector_bytes_only": {"dimensions": n("1536"), "bytes_per_float32": n("4"),
            "one_vector_bytes": n("1536") * n("4"),
            "one_vector_decimal_kb": n("1536") * n("4") / n("1000"),
            "one_vector_kib": n("1536") * n("4") / n("1024"),
            "million_vectors_bytes": n("1536") * n("4") * n("1000000"),
            "million_vectors_decimal_gb": n("1536") * n("4") * n("1000000") / n("1000000000")},
        "classic_ocu_730h_only": {"one_at_024": n(".24") * hours,
                                  "two_at_024": n("2") * n(".24") * hours},
        "low_cpu_percent_of_high_cpu_at_equal_ram": relative,
        "author_range_midpoint_arithmetic_only": savings,
        "unequal_inputs_equal_totals_counterexample": {
            "first_quantity": n("100"), "first_rate": n(".02"),
            "second_quantity": n("200"), "second_rate": n(".01"),
            "first_total": n("100") * n(".02"),
            "second_total": n("200") * n(".01"),
            "component_delta": n("100") * n(".02") - n("200") * n(".01")},
    }


def leaves(value, prefix=""):
    for key, item in value.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(item, dict):
            yield from leaves(item, path)
        else:
            yield path, item


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def matched_component_delta(quantities, rates, terms_match):
    """Conservative matched-input precondition; sufficient, not necessary, for equality."""
    require(terms_match is True, "Applicable terms must be explicitly matched")
    require(quantities[0] == quantities[1], "Billable quantities differ")
    require(rates[0] == rates[1], "Effective rates differ")
    return quantities[0] * rates[0] - quantities[1] * rates[1]


def main():
    decimal = calculate(Decimal)
    rational = calculate(Fraction)
    decimal_leaves = dict(leaves(decimal))
    rational_leaves = dict(leaves(rational))
    require(decimal_leaves.keys() == rational_leaves.keys(), "Case identities differ")
    for key, value in decimal_leaves.items():
        expected = rational_leaves[key]
        other = Decimal(expected.numerator) / Decimal(expected.denominator)
        require(abs(value - other) <= Decimal("1e-30"), f"Independent arithmetic differs: {key}")
    require(matched_component_delta((Decimal("100"), Decimal("100")),
            (Decimal(".06"), Decimal(".06")), True) == 0, "Matched cost did not cancel")
    for quantities, rates, terms in [((1, 2), (1, 1), True), ((1, 1), (1, 2), True),
                                      ((1, 1), (1, 1), False)]:
        try:
            matched_component_delta(quantities, rates, terms)
        except RuntimeError:
            continue
        raise RuntimeError("Mismatched inputs incorrectly passed the conservative precondition")
    counterexample = decimal["unequal_inputs_equal_totals_counterexample"]
    require(counterexample["first_total"] == counterexample["second_total"] == 2,
            "Unequal-input equal-product counterexample changed")
    require(counterexample["component_delta"] == 0,
            "Equal compatible totals must cancel even when quantities and rates differ")
    try:
        matched_component_delta((Decimal("100"), Decimal("200")),
                                (Decimal(".02"), Decimal(".01")), True)
    except RuntimeError:
        pass
    else:
        raise RuntimeError("Counterexample must fail the conservative matched-input precondition")
    rounded = {
        "floor_low_nearest_dollar": str(decimal["two_node_730h_floor"]["at_011_per_node_hour"].quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
        "floor_high_nearest_dollar": str(decimal["two_node_730h_floor"]["at_012_per_node_hour"].quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
        "hourly_ratio_one_decimal": str(decimal["equal_ram_hourly_ratio"]["048_divided_by_021"].quantize(Decimal(".1"), rounding=ROUND_HALF_UP)),
        "storage_difference_nearest_percent": str(decimal["storage_family_hourly_difference"]["relative_difference_percent"].quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
        "max_historical_movement_percent": str(max(decimal["historical_list_movements_percent"].values()).quantize(Decimal(".000001"))),
        "max_historical_movement_nearest_percent": str(max(decimal["historical_list_movements_percent"].values()).quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
        "cluster_plus_search_at_012_nearest_ten": str(decimal["matched_period_cluster_plus_search"]["at_two_012_nodes"].quantize(Decimal("1E1"), rounding=ROUND_HALF_UP)),
        "cluster_plus_search_at_024_nearest_ten": str(decimal["matched_period_cluster_plus_search"]["at_two_024_nodes"].quantize(Decimal("1E1"), rounding=ROUND_HALF_UP)),
        "low_high_ratio_percent_floor": str(min(decimal["low_cpu_percent_of_high_cpu_at_equal_ram"].values()).quantize(Decimal("1"), rounding=ROUND_FLOOR)),
        "low_high_ratio_percent_ceil": str(max(decimal["low_cpu_percent_of_high_cpu_at_equal_ram"].values()).quantize(Decimal("1"), rounding=ROUND_CEILING)),
    }
    expected = {"floor_low_nearest_dollar": "161", "floor_high_nearest_dollar": "175",
        "hourly_ratio_one_decimal": "2.3", "storage_difference_nearest_percent": "48",
        "max_historical_movement_percent": "4.347826", "max_historical_movement_nearest_percent": "4",
        "cluster_plus_search_at_012_nearest_ten": "2.3E+2", "cluster_plus_search_at_024_nearest_ten": "4.1E+2",
        "low_high_ratio_percent_floor": "43", "low_high_ratio_percent_ceil": "52"}
    require(rounded == expected, "Display rounding changed")
    print(json.dumps({"schema": "conditional-tco-arithmetic/v1", "independent_origin_credit": 0,
        "decimal_precision": 40, "independent_fraction_replay": "passed",
        "matching_scope_required": True, "measured_spend_or_performance": False,
        "values": decimal, "display_rounding": rounded,
        "matched_component_delta": "0", "mismatched_input_precondition_cases_rejected": 3,
        "unequal_inputs_equal_totals_counterexample": "passed",
        "matching_inputs_sufficient_not_necessary": True},
        indent=2, default=str, sort_keys=True))


if __name__ == "__main__":
    main()
