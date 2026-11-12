# Conditional search-cost arithmetic

Version: 1.0.0. Observed: 2026-11-12 UTC.

This is a reproducible arithmetic record. Every price, topology, capacity and
throughput input below is an explicit assumption. The calculations do not
attest current vendor prices, applicable contracts, availability, equal product
capability, actual spend, measured performance or total cost of ownership.
Primary sources must separately establish whether each input applies.

Run `python3 verify_tco_math.py`. It uses Decimal at precision 40 and separately
replays every numeric result with Fraction. The same command with `-O` must
produce identical results. Explicit checks remain enabled under `-O`.

## Cases and results

| Case | Assumed inputs | Arithmetic result |
| --- | --- | --- |
| Two-node illustrative period | 2 nodes, 730 hours, $0.11 or $0.12 per node-hour | $160.60 or $175.20; nearest dollars $161 and $175 |
| Conditional minimum comparison | The same comparison period and eligible scope, $160.60 versus an assumed $50 minimum | A numeric difference of $110.60; no capability or complete billing equivalence follows |
| Equal-RAM hourly ratio | $0.48 and $0.21 per hour | 2.285714…; approximately 2.3x |
| RAM-per-vCPU ratio | 16 GB / 8 vCPU and 16 GB / 2 vCPU | 2:1 and 8:1; not equal throughput |
| Hypothetical index excess | A 10 GB index and 3 GB available | 7 GB exceeds the assumed available capacity; no measured paging or latency follows |
| Throughput-heuristic multiplication | 2 nodes, 2 vCPU per node, an assumed 10 QPS per vCPU | 40 QPS as the arithmetic product only; not a benchmark or an achieved throughput guarantee |
| Alternative hourly amount | Baseline $0.48, alternative $0.25 | 47.916666…% less, rounded to 48%; CPU/storage differences remain separate |
| Shard node count | 2 nodes per shard, 3 shards | 6 nodes |
| Cluster plus search | Assumed $57 cluster charge covering the same region, contract and comparison period, plus the two-node 730-hour examples at $0.12 or $0.24 | $232.20 or $407.40, approximately $230 or $410 to the nearest ten; do not add the amounts if the scopes do not match |
| Raw vector bytes | 1536 dimensions, 4 bytes per float32, 1,000,000 vectors | 6144 bytes = 6.144 decimal KB = 6 KiB each; 6,144,000,000 bytes = 6.144 decimal GB total, approximately 6 GB. No index, allocator or metadata overhead is included |
| Classic OCU arithmetic | $0.24 per OCU-hour and 730 hours | 1 OCU gives $175.20, approximately $175; 2 OCUs give $350.40, approximately $350. This is not a statement about newer collection-generation minimums |

The equal-RAM low/high hourly pairs are `(0.11, 0.24)`, `(0.21, 0.48)`,
`(0.43, 0.99)`, `(0.89, 1.77)` and `(1.68, 3.26)`, at assumed 8, 16, 32, 64
and 128 GB respectively. Low divided by high gives 45.833333…%, 43.75%,
43.434343…%, 50.282485…% and 51.533742…%. Their outward whole-percent range
is 43–52%. Equal RAM does not mean equal CPU, storage or workload performance.

The historical hourly pairs are 0.12→0.12, 0.23→0.24, 0.48→0.48,
0.98→0.99, 3.22→3.26, 0.11→0.11, 0.21→0.21 and 5.79→5.87.
The largest increase is 4.347826…%, which rounds to about 4% to the nearest
whole percent. It is not a strict upper bound of 4%. Attribution, dates and
geography for any vendor-price comparison must be established separately.

For an author's assumed monthly infrastructure ranges, take arithmetic
midpoints only:

| Label | First range | Second range | Midpoints | Relative difference |
| --- | --- | --- | --- | --- |
| 100K | 150–250 | 20–40 | 200 and 30 | 85% |
| 5M | 1200–2000 | 300–1000 | 1600 and 650 | 59.375%, approximately 59% |
| 50M | 5000–8000 | 500–1000 | 6500 and 750 | 88.461538…%, approximately 88% |

These are arithmetic consequences of ranges, not validated invoices, measured
savings or a three-year TCO study. Labor, operations, service scope, geography,
availability, quality and contract terms are not supplied by these ranges.

## Conditional cancellation

Keep embedding, reranking and network-transfer components in each architecture's
absolute budget. Compare the component totals over a compatible billing period
and scope using explicit billable quantities, effective rates and applicable
terms. Do not assume that these totals match. A component cancels from the cost
difference when its comparable totals are established or explicitly assumed
equal; otherwise keep its cost difference.

Matching quantities, effective rates and terms is one sufficient basis for equal
totals. It is not mathematically necessary: 100 units at $0.02 and 200 units at
$0.01 both cost $2, so their cost difference is zero despite unequal inputs.
The executable's matched-input function uses a conservative comparison
precondition and rejects mismatched inputs. A separate equal-product
counterexample confirms that rejection by this function does not imply unequal
costs. This arithmetic does not attest real architectural spend or comparable
vendor terms. Model choices, remaining grants, request modes, inference
geography, transfer paths and contracts can require different inputs.

The existing conditional embedding-price proof is separate and unchanged. This
record supplies arithmetic evidence only and has zero independent-origin credit.

## Primary-input dependencies

- [MongoDB pricing](https://www.mongodb.com/pricing) and [Search Node billing](https://www.mongodb.com/docs/atlas/billing/search-node/) supply applicable rate and billing-unit premises.
- [MongoDB Search deployment options](https://www.mongodb.com/docs/atlas/atlas-search/about/deployment-options/) and [Vector Search deployment options](https://www.mongodb.com/docs/atlas/atlas-vector-search/deployment-options/) supply topology and resource guidance.
- [Search Node sizing](https://www.mongodb.com/company/blog/technical/the-art-and-science-of-sizing-search-nodes) supplies vendor sizing examples and heuristics; those remain guidance.
- [Pinecone pricing](https://www.pinecone.io/pricing/), [AWS OpenSearch pricing](https://aws.amazon.com/opensearch-service/pricing/) and the original attributed historical sources must be checked independently for any comparison.

The links identify dependencies; they do not certify that today's pages match
the assumed inputs above. Preserve historical source versions when discussing
historical rates.
