#!/usr/bin/env python3
"""Reproduce arithmetic on attributed vendor disk-size inputs; no benchmark."""
from decimal import Decimal, localcontext, ROUND_HALF_UP
from fractions import Fraction
import json

SOURCE_URL = 'https://www.mongodb.com/company/blog/technical/scaling-vector-search-mongodb-atlas-quantization-voyage-ai-embeddings'
RULE_SOURCE_URL = 'https://www.mongodb.com/docs/vector-search/deployment/deployment-options/'

def percent(value: Fraction, places: str = '0.01') -> str:
    with localcontext() as context:
        context.prec = 40
        result = Decimal(value.numerator) * 100 / Decimal(value.denominator)
        return format(result.quantize(Decimal(places), rounding=ROUND_HALF_UP), 'f')

def calculate() -> dict:
    # The vendor reports these decimal MB values for its own experiment.
    baseline = Fraction(39473, 100)
    binary = Fraction(40766, 100)
    increase = (binary - baseline) / baseline
    rule_increase = Fraction(25, 24) - 1
    other_increase = Fraction(33, 32) - 1
    if increase != Fraction(1293, 39473):
        raise RuntimeError('reported-input ratio identity failed')
    if rule_increase != Fraction(1, 24) or other_increase != Fraction(1, 32):
        raise RuntimeError('fraction subtraction identity failed')
    if percent(increase) != '3.28' or percent(rule_increase) != '4.17':
        raise RuntimeError('two-place percentage rounding failed')
    if percent(other_increase, '0.001') != '3.125':
        raise RuntimeError('three-place percentage rounding failed')
    if increase == rule_increase or rule_increase == other_increase:
        raise RuntimeError('distinct ratios were incorrectly equated')
    return {
        'schema': 'attributed-disk-ratio-arithmetic/v1',
        'evidence_kind': 'firsthand reproducible arithmetic on attributed vendor inputs',
        'source_url': SOURCE_URL,
        'rule_source_url': RULE_SOURCE_URL,
        'vendor_experiment_scope': 'approximately 300000 Wikipedia fragments; 1024-dimensional voyage-3-large; vendor-reported index disk sizes',
        'vendor_reported_inputs_mb': {'float32_ann': '394.73', 'binary_quantized': '407.66'},
        'derived_results': {
            'binary_over_float32_ratio': str(binary / baseline),
            'reported_input_increase_fraction': str(increase),
            'reported_input_increase_percent_two_places': percent(increase),
            '25_over_24_increase_fraction': str(rule_increase),
            '25_over_24_increase_percent_two_places': percent(rule_increase),
            '33_over_32_increase_fraction': str(other_increase),
            '33_over_32_increase_percent_three_places': percent(other_increase, '0.001'),
        },
        'limits': [
            'No database, index, model or cloud workload was executed.',
            'The operator did not independently reproduce the vendor disk-size measurements.',
            'The derived percentages inherit the precision and units of the vendor inputs.',
            'The calculation establishes neither a universal index-size ratio nor RAM, latency or billing savings.',
        ],
    }

if __name__ == '__main__':
    print(json.dumps(calculate(), indent=2, sort_keys=True))
