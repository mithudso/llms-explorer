# MongoDB frontier batch pilot

Version: 1.0.0  
Verified as of: 2026-10-01  
Delta: First actual shared-source retrieval and synthesis test.

## Result

The bounded pilot succeeded at batch retrieval, shared synthesis and source-support verification. Four unresearched children of **Archive Rules** now have research packets: **Archive Data Expiration Rule**, **Archive Schedule Window**, **Online Archive Terraform Resource**, and **Index Sufficiency Warning**. They reference five shared parent claims and add three claims each. The second independent model pass supported all 17 revised claims and found no inheritance issues.

This is a research-method pilot, not a completed standard `/dr` or an installed skill. All evidence comes from one MongoDB authoring origin, including its Terraform provider documentation. It does not meet the standard `/dr` requirement for three independent origins. No Atlas resources were changed, no concept-tree nodes were finalized, and indexing/Ollama remain paused.

## Measured usage

| Stage | Input tokens including cache writes/reads | Output tokens | Reported model cost |
|---|---:|---:|---:|
| Shared synthesis | 58,584 | 7,885 | $0.311149 |
| Initial verification | 45,003 | 6,911 | $0.244444 |
| Revised verification | 56,340 | 4,785 | $0.268532 |
| Total | 159,927 | 19,581 | $0.824125 |

The CLI's `sonnet` alias resolved to `claude-sonnet-5-5`. Costs above are the CLI's reported list-price accounting, not an invoice. Output totals include thinking tokens where reported. The synthesis made one model call and no model-side web requests. Two separate verification calls account for the repair cost.

The research retrieval was one real `POST /v2/batch/scrape` job, not six unrelated scrape calls. Job `01a0f913-9790-7171-b4be-02b399da812d` completed all six URLs in **23.22 seconds**, consumed **six credits**, and returned no URL errors or robots blocks. The request used Markdown, `onlyMainContent: true`, `maxAge: 0`, and `maxConcurrency: 3`. All six retained bodies were nonempty HTTP 200 responses and have SHA-256 hashes in the source inventory.

Verification separately fetched five pages directly over HTTP. MongoDB's `.md` representation omitted the standard page's Custom Criteria tab even though the rendered page included it. A second Firecrawl batch refreshed the rendered standard page and Terraform Registry page: job `01a0f919-0fae-73fd-b13f-46cae858a0a6`, two URLs, two credits. **Total Firecrawl consumption was eight credits.** Full source bodies, API receipts, original model outputs and assembled inputs are retained privately; the public files contain synthesized claims and sanitized measurements.

## Sharing benefit: calculated, not a live A/B comparison

The six research bodies contained **121,870 Unicode characters**. A replay of each child's own final claim dependencies would deliver **16 page bodies totaling 381,562 characters** to separate concept researchers. The shared batch delivered six bodies once, a **68.06% reduction in source payload characters** and a **62.5% reduction in logical page deliveries** against that calculated baseline.

Including all inherited parent dependencies raises the calculated baseline to 22 deliveries and 461,113 characters, a 73.57% source-payload reduction. The conservative child-only calculation is the headline result. The dependency matrix and formula are in the metrics artifact:

`payload reduction = 1 - unique batch source characters / replayed per-concept source characters`

These figures exclude system prompts, generated foundation text, thinking/output tokens, verification, refetches and repair calls. No independent-agent control run was executed. Consequently, **this test does not establish measured end-to-end token, cost or latency savings**. The measured model totals above include the extra review that a headline payload estimate would hide. Firecrawl batching coordinates retrieval; deduplication and shared-context synthesis remove repeated evidence ingestion. Individual scraping with an effective shared cache could obtain the same deduplication benefit.

## What the research found

| Concept | Added evidence and boundaries |
|---|---|
| Archive Data Expiration Rule | Keep cluster-side selection age separate from deletion of already archived data. UI docs give 7–9125 days; provider docs give 7–9215. The live enforced limit is unresolved. Archive deletion and collection deletion have different storage consequences. |
| Archive Schedule Window | UI windows have a two-hour minimum and running jobs may overrun them. Some monthly dates skip months. Equal start/end values in the provider example do not establish valid window semantics. |
| Online Archive Terraform Resource | Provider docs describe criteria, collection types, immutable fields, pause/resume, synchronization and timeout behavior. `master` and Registry `latest` URLs are unpinned; an examples tag does not identify their current provider release. |
| Index Sufficiency Warning | The vendor describes a first-run scanned/returned threshold of 10. The check stops after sufficient indexes are detected and does not warn about a later index drop. Standard and time series index guidance retain separate scopes. |

Claims cite source IDs linked to full URLs in the source inventory. They distinguish vendor statements from inferred operational consequences and preserve unresolved questions. They establish documentation support, not tested Atlas/API/provider behavior.

## Verification findings

The initial verifier returned inconsistent labels: several `NOT_IN_SOURCE` reasons or notes said the claim was supported. That result was rejected as a reliable gate. It also exposed a parent claim that generalized UI edits to API/CLI, uncertainty about unpinned provider versions, and a dynamic-tab retrieval gap. The orchestrator revised eight claim texts, narrowed provider scopes, repaired citations, and supplied fresh rendered content to a second verifier. The second pass returned 17 `SUPPORTED` rows with consistent reasons and no inheritance issues. Two final citation-list repairs added the UI page to the provider/UI comparisons; the text already checked by the verifier did not change.

The replay bundle retains both original and corrected packets, both gates and all usage records. This is one same-model independent-context review, not cross-model agreement or empirical validation. A matching vendor page can still repeat a vendor error. Numeric API enforcement, timezone behavior and Terraform replacement behavior remain open questions.

## Recommendation

Proceed with **shared source retrieval plus explicit parent claim references and scoped child deltas** for narrow cohorts like this. Keep claims tied to original evidence, retrieval date, collection type, interface and provider version. Re-verify an inherited fact when its scope changes. Do not count vendor mirrors as independent corroboration, and ensure a verifier's labels agree with its reasons. Preserve complete rendered tabs where Markdown exports omit content.

Before changing production skill behavior, run a matched control using the same source set, claims budget, model and verification policy. That control should measure full input/output/cache tokens and cost for one shared packet versus four isolated researchers. The remaining independent-origin and operational questions belong to further research; they do not block completion of this bounded pilot.

## Artifacts and replay

Public artifacts alongside this report: structured results, source inventory, final verifier output, metrics, executed prompt briefs and continuation memory. The private replay bundle is `/Users/mitch/.global-ai-hub/research-tests/mongodb-batch-pilot-2026-10-01/replay-bundle.zip`. It contains retained source bodies, receipts, raw model outputs, full prompts and the test harness. It contains no credentials. Extract it into a new directory for inspection; read saved outputs before rerunning anything. Running the harness again incurs model or scrape usage. Do not resubmit a successful batch simply to retrieve its saved results.

Source grouping plan: `/Users/mitch/dev/llms-explorer/docs/research/frontier-batches-2026-10-01/README.md`, cohort D04. The selected names were confirmed as frontier children without existing nodes in the source checkout's `/Users/mitch/dev/llms-explorer/concept-tree/tree.json`; no matching prior run appeared in the research index. This pilot selected four concepts, not the entire MongoDB frontier.
