# Research process comparison

Historical old-contract outputs and fresh updated-contract outputs use the original frozen SQLite evidence, three stages, three models, two efforts and two repetitions. Both arms receive fresh blind Astra/high judgments with identical full-statement binding and scoring. Models and efforts stay fixed within each pair.

This measures bounded research-stage synthesis. It does not execute live discovery, adaptive follow-ups, production gates, resume, source sharing or publication. The updated prompts include the mandatory current runtime and library companions. Their additional context is part of this process comparison.

| Model | Effort | Arm | n | Grounded concepts | Accepted claims | Quality | Coverage /24 | Depth /3 | Seconds | Output tokens |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gpt-6-luna | medium | old | 6 | 5.5 | 22.7 | 91.9% | 10.8 | 2.45 | 24.9 | 2873 |
| gpt-6-luna | medium | updated | 1 | 10.0 | 24.0 | 96.0% | 12.0 | 2.38 | 40.5 | 2780 |
| gpt-6-luna | max | old | 6 | 12.8 | 31.8 | 90.5% | 9.2 | 2.39 | 187.6 | 25547 |
| gpt-6-luna | max | updated | 5 | 13.0 | 30.2 | 92.6% | 8.4 | 2.39 | 181.0 | 23575 |
| gpt-6.1-sol | medium | old | 6 | 16.2 | 33.7 | 94.8% | 8.0 | 2.45 | 103.1 | 5278 |
| gpt-6.1-sol | max | old | 6 | 17.2 | 35.2 | 97.7% | 10.8 | 2.46 | 543.9 | 24931 |
| gpt-6.1-sol | max | updated | 3 | 15.3 | 33.7 | 93.5% | 9.0 | 2.40 | 583.8 | 21496 |
| gpt-6-astra | medium | old | 6 | 14.5 | 35.5 | 99.1% | 8.5 | 2.48 | 106.6 | 4431 |
| gpt-6-astra | max | old | 6 | 16.3 | 35.0 | 97.2% | 9.5 | 2.49 | 688.8 | 23885 |
| gpt-6-astra | max | updated | 3 | 15.0 | 35.7 | 99.1% | 7.7 | 2.36 | 623.0 | 20275 |

## Paired changes by research stage

| Stage | Pairs | Grounded concepts | Accepted claims | Quality points | Coverage /24 | Depth /3 | Seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| dr | 6 | -0.33 | +0.67 | +3.15 | -0.33 | +0.027 | -43.3 |
| concept-family-explorer | 2 | +4.00 | -5.00 | -1.15 | -1.00 | -0.130 | +15.8 |
| rabbithole | 4 | -1.25 | -1.00 | -2.75 | -0.75 | -0.050 | +34.9 |

48 of 72 arm-trials scored. Quality pools accepted unique atomic claims across raw claims. Other measures are per-trial means. Generation timing excludes judges and any failed attempts; all attempt records remain private. Historical timings reflect the earlier scheduling and service conditions. USD is unknown.

Two repetitions and one topic do not establish statistical superiority. The 24-concept/36-claim caps can hide breadth differences. One model judge supplies semantic assessments. Reference coverage is the original provisional 24-item rubric. Differences may reflect service drift and sampling as well as contract changes; these are historical controls, not simultaneous fresh old-process runs. No full-workflow speedup or accuracy claim follows from these trials.
