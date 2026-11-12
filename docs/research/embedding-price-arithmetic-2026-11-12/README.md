# Conditional embedding-price arithmetic

Version: 1.0.0. Observed: 2026-11-12 UTC.

This firsthand calculation verifies illustrative arithmetic. Each input below is
an assumption. The calculation establishes no current vendor price, entitlement,
invoice, contract, workload measurement or retrieval-quality result. Provider
documentation must establish the applicable inputs separately.

Assume a standard rate of $0.06 per million billable tokens and an applicable
fresh standard allowance of 200 million tokens (200M). One billion tokens (1B)
is 1,000 million tokens. Standard-request cost in this example is
`max(0, volume - remaining applicable allowance) × rate`.

| Assumed request volume and allowance | Exact calculation | Illustrative USD |
| --- | --- | ---: |
| 1B standard tokens; fresh 200M allowance | (1,000 − 200) × $0.06 | $48.00 |
| 1B standard tokens; exhausted allowance | 1,000 × $0.06 | $60.00 |
| 200M standard tokens; fresh 200M allowance | max(0, 200 − 200) × $0.06 | $0.00 |
| 100M standard tokens; fresh 200M allowance | max(0, 100 − 200) × $0.06 | $0.00 |
| 1B batch tokens; assumed 33% discount; no free credits | 1,000 × $0.06 × 0.67 | $40.20 |
| 200M batch tokens; assumed 33% discount; no free credits | 200 × $0.06 × 0.67 | $8.04 |

The last two rows use a discounted multiplier of `1 − 0.33 = 0.67`. Under
these assumptions, batch can cost more than standard requests covered by an
applicable allowance. A service completion window is a separate term. The
calculation does not assume that an allowance resets each month; a later estimate
must supply the remaining applicable balance.

For list-rate arithmetic only, $0.02 per million equals $0.02 per million, and
$0.02 is one third (1/3) of $0.06. Equal token counts across providers are an
assumption. The ratio establishes neither identical tokenization nor equal
retrieval quality or total cost.

The example assumes any-geography inference at the stated base rate. It excludes
scoped-inference surcharges, Files storage, database cluster resources, vector
and search index resources, Lucene storage, data transfer, engineering and
operations, taxes, private discounts and additional queries beyond the stated
token volume. No actual spend or engineering saving was measured.

Run the standard-library-only proof from this directory:

```sh
python3 verify_prices.py --output results.json
```

The program uses exact decimal arithmetic for every dollar result and exact
rational arithmetic for the one-third comparison. It checks the zero-cost clamp
and the batch counterexample, and rejects a negative or non-finite input. It
makes no network request. [results.json](results.json) records the successful
execution, including all assumptions.
