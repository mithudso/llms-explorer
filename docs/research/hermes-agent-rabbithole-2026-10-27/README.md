# Hermes Agent Rabbithole research

Version: 1.0.4
Delta: 1.0.3 to 1.0.4; complete six depth passes, bound claim verification and scoped publication repairs.
Date: 2026-10-27
Task: TASK-929
Depth verdict: BUDGET_EXHAUSTED

> Run the rabbithole skill on hermes agent

This run researches Nous Research Hermes Agent itself. It records 226 atomic factual claims, with 85 distinct claim-cited URLs and 111 retained bibliography records. The depth dossier, claim dossier, metrics and sibling handoff accompany this report. Two independent Sol/medium baseline workers produced 24 compound rows, normalized to 76 unique atoms. Splitting, rephrasing and citation repair earned zero novelty.

| Depth pass | New atoms | Retired interpretations | Total atoms | New-information rate |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 76 normalized | 0 | 76 | Baseline |
| 1 | 52 | 0 | 128 | 40.625% |
| 2 | 16 | 0 | 144 | 11.111% |
| 3 | 22 | 2 | 164 | 13.415% |
| 4 | 27 | 0 | 191 | 14.136% |
| 5 | 18 | 0 | 209 | 8.612% |
| 6 | 19 | 2 | 226 | 8.407% |

All six rates exceed five percent. The six-pass cap stopped discovery; depth saturation was not established. The author estimates that two to three further targeted source passes could pay off. Live adapter authorization, crash/concurrency behavior and benchmark reproduction require a separate executable study.

## Evidence and verification

Five verified source organizations contribute evidence. Nous documentation and its repository count as one owner. NVIDIA, VantaSoft and Neogen supply substantive primary material; the commercial operators' findings are attributed to their own deployments and version limits. Folkfox contributes a documentation audit. Paper author groups are tracked separately; arXiv is a host, and unresolved affiliations are not invented.

The first bound gate supported 223 claims and left three exact full revision identities UNVERIFIED. A guarded edit narrowed only those three prefixes to the abbreviated identity present in the cited snapshot. The second independent gate supported all 226 exact structured claims, with pinned source hashes and Unicode evidence spans. Counts and novelty did not change. Both attempts and the correction preimage remain private.

Frozen research-artifact/v1 SHA256: 12a1f33044dd010ab5d2d80a6d2686fa2bd5ff8b6c0a86cc09401a41ecde3bde

Canonical structured-claims SHA256: b861b7e5e0c6f308c428d94096e0723197ce1265fae871a0fa7a15c239f604cb

The gate validates structured factual claims. Private auxiliary revision annotations and open questions are unvalidated provenance. Current public prose narrows the remaining source-identity note, and public exporters omit auxiliary revision metadata. Raw source bodies, exact quotes, worker logs and rejected attempts remain private.

## Persistence and projection repairs

Both eight-member concept packs contain the same 226 supported units. Both source trees carry depthPass=rabbithole and depthVerdict=BUDGET_EXHAUSTED. The generated reader, canonical JSON and Markdown retain every approved primary and secondary citation. The existing website tree schema exposes artifact identity; depth metadata remains in the canonical source trees.

Final checks exposed two existing projection defects. Typed readers discarded secondary URLs, and the ordinary refresh scanned/replaced unrelated reader leaves even with --run. The repair preserves also[] citations through reader JSON and Markdown. An explicit --only-slug option refreshes existing selected packs while leaving all other reader bytes intact; default full-refresh behavior stays available. Use --no-merge-tree when both canonical trees already contain the requested placement. Regression tests cover a two-source claim end-to-end and byte-for-byte preservation of an unrelated reader.

The final scoped refresh preserves all 1,823 non-Hermes reader JSON files and the source trees' unrelated node data. Existing global tree warnings remain; they are not certified clean by this run. No embeddings or local inference services were resumed. Hermes itself was not installed or executed.

## Continuation and delivery

Private canonical run: /Users/mitch/.global-ai-hub/research/hermes-agent-rabbithole-2026-10-27

Stable rendered dossier: /Users/mitch/.global-ai-hub/research/hermes-agent-rabbithole-2026-10-27/dossier.md

Depth report and metrics: /Users/mitch/.global-ai-hub/research/hermes-agent-rabbithole-2026-10-27/depth/dossier.md and /Users/mitch/.global-ai-hub/research/hermes-agent-rabbithole-2026-10-27/depth/metrics.json

The original /Users/mitch/dev/llms-explorer checkout remains divergent and is preserved. Work uses /Users/mitch/dev/worktrees/llms-explorer-hermes-rabbithole-20261027. The failed device-login attempt did not invalidate the existing GitHub session; ordinary PR CI fetched private dependencies successfully, and no credential rotation was needed.

Git delivery and CI receipts:

https://github.com/mithudso/llms-explorer/pull/242

## Validation

API: 281 passed. Hub: 594 passed, one skipped. Focused projection regressions: 48 passed plus six subtests. Ruff passed. Final site/projection suite: 305 passed plus six subtests. The 2,282-page build and publication policy check passed; the site llms family retains eight pre-existing Medium findings and zero High findings. Final commit CI is available through the PR above.

Worker event logs disclose a catalog-isolation limitation despite slim dispatch flags. Baseline adapter usage and six custom depth-worker receipts are recorded separately; cached tokens are included and cost remains unknown. No context-isolation qualification or live Hermes deployment qualification is claimed.
