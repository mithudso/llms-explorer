# Multi-domain research canary

One live-assisted trial per domain and configuration. These small samples do not establish a model ranking. Model and effort vary together; this compares configurations.
Primary text is frozen and hashed for scoring. Live search leads are counted separately.
Quality requires full entailment, an atomic unique statement and an exact quote in the supplied packet. A rejected claim is not automatically false.
Astra/high supplies blind judgments; exact quotes and statement bindings are checked deterministically.
Reference facts await human review. Costs remain unknown; tokens are measured. Raw evidence/logs stay private.

| Domain | Model / effort | Concepts raw / grounded | Facts raw / supported unique | Quality | Depth / 3 | Mechanisms | Contradictions | Seconds |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| authentication | gpt-6-luna / max | 3 / 3 | 10 / 9 | 90.0% | 2.11 | 0 | 0 | 124.25 |
| authentication | gpt-6.1-sol / medium | 6 / 4 | 10 / 10 | 100.0% | 2.2 | 0 | 0 | 65.8 |
| http | gpt-6-luna / max | 5 / 3 | 8 / 6 | 75.0% | 2 | 3 | 0 | 101.9 |
| http | gpt-6.1-sol / medium | 8 / 7 | 26 / 26 | 100.0% | 2.12 | 2 | 0 | 95.95 |
| storage | gpt-6-luna / max | 4 / 2 | 9 / 2 | 22.2% | 2 | 0 | 0 | 194.49 |
| storage | gpt-6.1-sol / medium | 7 / 7 | 23 / 20 | 87.0% | 2.25 | 8 | 2 | 85.14 |
