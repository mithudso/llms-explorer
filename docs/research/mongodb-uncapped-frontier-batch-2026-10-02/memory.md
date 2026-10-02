# Continuation memory

Version: 1.0.0  
Delta: Recorded the completed uncapped evidence pass and the qualification work still required.

## Completed

- Removed the default eight-concept cap in `concept-family-explorer` while retaining an optional explicit cap, bounded rounds/concurrency, per-concept evidence checks, and source-coherent synthesis groups.
- Processed the 25 viable concepts from queue SHA-256 `b41aa90fe8352b1131e1ad748e306b13ea30ba0ef79d3310a00bcc175ce009bd`, using a 703-node source-tree snapshot (SHA-256 `3fc510aeb562e43636aa81454e7693ee73dfe4ebddb67c75d43d5d646a81f922`). The current MongoDB family count was 120. Raw frontier was 686 exact / 685 case-fold-unique labels; these were not all scored gaps.
- Evidence outcomes: 20 supported, five partial, zero skipped/blocked. Cohorts: identity/federation/policy (12); search/vector/BM25/fusion (5); platform/core (8).
- Retrieval logged 67 URL request events, 65 successes, two moved/404 responses. Search used two `/v2/batch/scrape` jobs for 11 pages/credits; identity and platform used multi-URL CLI invocations. Overall credits, model tokens, and token savings were not measured.
- Corrected the installed Atlas IAM reference for current Organization Owner → Project Owner inheritance and separate database credentials.
- Merged skill change in skills PR 54 and prior family expansion in llms-explorer PR 136. The current artifact in this directory records this subsequent batch separately.

## Remaining

- Treat this as an evidence-only research pass. The 25 deltas have not all met the standard `/dr` three-independent-origin requirement, and no blind semantic gate or live Atlas test was run.
- Resolve the five partial topics: Entra group overage behavior in Atlas; full Atlas Search vs Vector Search boundaries; score-fusion missing-input/normalization details; optimal/empirical per-query weights; and Spark/Databricks deployment guidance.
- Run independent-origin research and claim verification for each concept before installation. Then persist only qualified child concepts to the canonical tree and complete the consolidated optimization pass.
- Keep indexing, embedding/registry rebuilds, semantic routing, and Ollama paused unless the user explicitly resumes them.

## Evidence bundle

Detailed source receipts and cached page text remain in the private research area; do not copy raw scraped passages into this public repository. The versioned report contains source URLs, summarized claims, retrieval counts, limitations, and continuation requirements.
