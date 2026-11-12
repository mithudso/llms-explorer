# Arithmetic on attributed vector-index disk sizes

Version: 1.0.0. Observed: 2026-11-12 UTC.

This firsthand calculation uses two disk sizes reported by [MongoDB's quantization experiment](https://www.mongodb.com/company/blog/technical/scaling-vector-search-mongodb-atlas-quantization-voyage-ai-embeddings): 394.73 MB for float32 ANN and 407.66 MB for binary quantization. MongoDB describes approximately 300,000 Wikipedia fragments with 1024-dimensional voyage-3-large embeddings. These are vendor measurements; the operator did not reproduce the benchmark.

The reported inputs imply `(407.66 - 394.73) / 394.73 = 1293/39473`, or approximately **3.28 percent** more disk. MongoDB's [deployment guidance](https://www.mongodb.com/docs/vector-search/deployment/deployment-options/) separately estimates a binary index with rescoring at the original index size times `25/24`. That ratio implies `25/24 - 1 = 1/24`, approximately **4.17 percent**. Those ratios are not identical. `33/32 - 1 = 1/32` gives **3.125 percent**, which is a different ratio again. This calculation does not replace or derive the vendor's index-overhead model.

Run the standard-library script from this directory:

```sh
python3 verify_ratios.py
```

The output must match `results.json`. `Fraction` preserves the decimal inputs as exact rationals; `Decimal` supplies explicitly rounded display percentages. Runtime checks also run under Python optimization.

This is arithmetic on attributed inputs. It runs no database, index, model or cloud workload, and supplies no independent storage benchmark. The percentages inherit the precision and units of the reported inputs. They establish no universal index-size ratio or RAM, latency or billing result.
