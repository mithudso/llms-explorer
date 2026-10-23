# Research process comparison

Historical old-contract outputs and fresh updated-contract outputs use the original frozen SQLite evidence, three stages, three models, two efforts and two repetitions. Both arms receive fresh blind Astra/high judgments with identical full-statement binding and scoring. Models and efforts stay fixed within each pair.

This measures bounded research-stage synthesis. It does not execute live discovery, adaptive follow-ups, production gates, resume, source sharing or publication. The updated prompts include the mandatory current runtime and library companions. Their additional context is part of this process comparison.

The primary table uses only completed matched cells. Every old/new pair has the same skill, model, effort and repetition. Unmatched completed control scores remain in results.json and do not change the paired means.

Matched pairs: 35.

| Measure | Old | Updated |
|---|---:|---:|
| Accepted-claim quality (%) | 95.27 | 95.37 |
| Grounded concepts per trial | 13.66 | 13.66 |
| Accepted claims per trial | 32.20 | 32.37 |
| Reference coverage /24 | 9.40 | 9.03 |
| Claim depth /3 | 2.45 | 2.44 |
| Successful-generation seconds | 266.0 | 277.1 |

| Model | Effort | Arm | n | Grounded concepts | Accepted claims | Quality | Coverage /24 | Depth /3 | Seconds | Output tokens |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gpt-6-luna | medium | old | 6 | 5.5 | 22.7 | 91.9% | 10.8 | 2.45 | 24.9 | 2873 |
| gpt-6-luna | medium | updated | 6 | 7.8 | 26.3 | 93.5% | 11.0 | 2.48 | 31.7 | 3087 |
| gpt-6-luna | max | old | 6 | 12.8 | 31.8 | 90.5% | 9.2 | 2.39 | 187.6 | 25547 |
| gpt-6-luna | max | updated | 6 | 12.0 | 30.8 | 93.0% | 8.7 | 2.42 | 188.8 | 23612 |
| gpt-6.1-sol | medium | old | 6 | 16.2 | 33.7 | 94.8% | 8.0 | 2.45 | 103.1 | 5278 |
| gpt-6.1-sol | medium | updated | 6 | 16.0 | 33.3 | 93.9% | 9.2 | 2.44 | 117.1 | 5153 |
| gpt-6.1-sol | max | old | 6 | 17.2 | 35.2 | 97.7% | 10.8 | 2.46 | 543.9 | 24931 |
| gpt-6.1-sol | max | updated | 6 | 16.7 | 34.2 | 94.9% | 9.3 | 2.41 | 571.2 | 19115 |
| gpt-6-astra | medium | old | 6 | 14.5 | 35.5 | 99.1% | 8.5 | 2.48 | 106.6 | 4431 |
| gpt-6-astra | medium | updated | 6 | 13.7 | 34.3 | 97.6% | 7.5 | 2.43 | 129.8 | 4750 |
| gpt-6-astra | max | old | 5 | 16.2 | 34.8 | 96.7% | 9.0 | 2.47 | 702.5 | 23859 |
| gpt-6-astra | max | updated | 5 | 16.2 | 35.8 | 99.4% | 8.4 | 2.43 | 693.3 | 18066 |

## Paired changes by research stage

| Stage | Pairs | Grounded concepts | Accepted claims | Quality points | Coverage /24 | Depth /3 | Seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| dr | 12 | -0.50 | +0.08 | +1.81 | -0.92 | -0.021 | -9.2 |
| concept-family-explorer | 11 | +1.00 | -0.73 | +0.25 | -0.27 | -0.015 | +27.0 |
| rabbithole | 12 | -0.42 | +1.08 | -1.71 | +0.08 | -0.004 | +16.8 |

71 of 72 arm-trials scored. Quality pools accepted unique atomic claims across raw claims. Other measures are per-trial means. Generation timing excludes judges and any failed attempts; all attempt records remain private. Historical timings reflect the earlier scheduling and service conditions. USD is unknown.

failures.json lists currently unscored cells. attempt-failures.json retains failed attempts even after successful recovery. These failures receive no invented quality score. execution.json records measured retry usage and gaps in attempt telemetry.

Two repetitions and one topic do not establish statistical superiority. The 24-concept/36-claim caps can hide breadth differences. One model judge supplies semantic assessments. Reference coverage is the original provisional 24-item rubric. Differences may reflect service drift and sampling as well as contract changes; these are historical controls, not simultaneous fresh old-process runs. No full-workflow speedup or accuracy claim follows from these trials.
