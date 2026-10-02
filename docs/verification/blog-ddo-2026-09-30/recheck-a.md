# Group A final independent re-audit — 2026-09-30

Bounded approval for four audited posts; Medium dissent A-R1 for vocabulary.md at the recorded hash.

This reviewer produced Group B repairs but did not author or review the Group A edits. Earlier Group A reports, findings and edit rationale were withheld. Same-model separate-author review, not a cross-model certification.

Reviewed every final post body and its frontmatter, examples, tables, headings and reference context through the selected critique, technical, evidence, terminology, security/injection and voice lenses. Earlier Group A reports, scripts and diffs were not read. Article operations were not executed. Approval is bounded by the source limits below; it is not a runtime acceptance result.

| Post | Reviewed SHA-256 | Result | Medium+ findings |
|---|---|---|---|
| rtx-5080-egpu-apple-silicon-m5-thunderbolt-5.md | `d884549f9d421e04cf0f0fa3b1fdd684b9dd438ad9326f056e48e1352160abc6` | approved | 0 |
| mdb-case-assistant-project-pitch.md | `31e78fb2443e5dea17360b53ec0339f3396545d0c1404bc60daa7c460b50faec` | approved | 0 |
| vocabulary.md | `69ea7b45dad985e9ea48453a80a81e0e3058afc2f4a79c11f35f0e40a21aefb1` | dissent | 1 |
| six-months-of-hand-made-llms.md | `8aabc6ac6db1575f0b8ed39dbb597d1e7f359e9123aba5bb4beb9a232e98c98b` | approved | 0 |
| semantic-indexing.md | `c0c9327f360b5c6ecb6320ba81613eddbcd0edf970400f1fa250b8d14c09d9bc` | approved | 0 |

## Corroborated dissent

### A-R1 — Medium: vocabulary example interpretation contradicts the retained output

Span: `site/src/content/blog/vocabulary.md:113-116`.

> Either line tells an agent that "small" in a query is this file and that "full" is the neighbour it is contrasted with;

The explanatory paragraph attributes a small/full contrast to both examples. The target grammar at line 102 explicitly names llms-full.txt, but the retained generated output at line 110 names /_llms/, x-markdown-tokens, llms.txt and x-max-tokens under not:. It contains no full or llms-full.txt neighbor. This is contradicted by the displayed source itself, independent of the missing original generation artifact.

The reader is told that the demonstrated generated line supplies a key distinction it does not contain. That overstates the current output and obscures the gap between the proposed target grammar and the retained model output.

Primary evidence: the post at lines 102 and 110; `hub/scripts/docset_refine/vocabulary.py:468-505` renders the stored contrast field and does not supply an unrecorded full-file neighbor.

Smallest supported correction:

> The target example contrasts small with full. The retained generated example names other neighbors and does not supply that distinction; its model-written definition still needs review.

Preserve both quoted examples and the existing qualification that the original generation artifact is unavailable. The finding is unresolved in the recorded hash. The reviewer did not edit the post.

## Checks and source limits

### rtx-5080-egpu-apple-silicon-m5-thunderbolt-5.md

Bounded approval.

Primary checks:

- Checked macOS TinyGPU prerequisites and compute setup against the project documentation. Source: https://docs.tinygrad.org/tinygpu/.
- Checked the distinction between native macOS eGPU graphics support and the described TinyGPU compute path. Source: https://support.apple.com/en-us/102363.
- Checked the dated M5 Pro/Max and Thunderbolt 5 platform context. Source: https://www.apple.com/newsroom/2026/03/apple-introduces-macbook-pro-with-all-new-m5-pro-and-m5-max/.
- The upstream default rope_theta=500000 supports the article warning about its recorded 10000 fallback; the proposed metadata-preserving lookup is consistent with that warning. Source: https://github.com/meta-llama/llama3/blob/main/llama/model.py.
- Read the downloadable setup, wrapper, proxy and patch as source, including the dated source-inspection caveats, context limit, environment handling, patch applicability and prepared-environment assumptions. Source: site/public/downloads/egpu/rtx5080_egpu_harness.py, site/public/downloads/egpu/ollama-egpu, site/public/downloads/egpu/ollama-egpu-proxy.py, site/public/downloads/egpu/tinygpu-blackwell-gsp.patch.
- Read only the GGUF header/metadata with an independent binary reader: qwen2 architecture, 40 blocks, embedding length 5120, 40 attention heads and 40 KV heads. Conditional FP16 KV arithmetic gives 819200 bytes/token and 3.125 GiB at 4096 tokens, matching the article table. No model was loaded. Source: /Users/mitch/.ollama/models/blobs/sha256-de0334402b975e19dd48eb43a13f7534772fb5b4a054447f8f6a861b87ec5799.
- Checked client/provider documentation for the configuration examples and the stated chat-completions versus Responses compatibility boundary. Source: https://aider.chat/docs/llms/ollama.html, https://developers.openai.com/codex/config-advanced.

Source limits:

- Raw panic traces, the reported registry observations, zero-offload behavior, benchmark timing and contention observations were not independently reproduced. The article states its evidence limits; these remain historical, qualified observations.
- The named GGUF file metadata and file size were inspected; its full approximately 8 GB digest and actual runtime allocation were not verified. The KV estimate is conditional on the stated FP16 layout.
- No fresh-machine installation, hot-unplug test, GSP causality experiment, model inference or end-to-end agent tool-cycle acceptance was performed. Reading the download sources does not establish those outcomes.
- Concurrent source changes cannot retroactively extend the article dated inspection scope. The review does not convert its qualified proxy or configuration examples into a universal compatibility guarantee.

### mdb-case-assistant-project-pitch.md

Bounded approval.

Primary checks:

- Checked the extension permission/CSP boundaries and the distinction between manual-mode gating and proof that a human initiated each call. The prose preserves that distinction. Source: /Users/mitch/dev/mdb-case-assistant/manifest.json, /Users/mitch/dev/mdb-case-assistant/src/background/backend-gate.js.
- Checked the local Slack-draft design and operator-triggered workflow against source. Source: /Users/mitch/dev/mdb-case-assistant/src/background/s1-swarm-dispatcher.js.
- Counted 42 static server.registerTool registrations, supporting the MCP tool-count claim. Source: /Users/mitch/dev/mdb-case-assistant/mcp-server/src/index.ts.
- Checked stdio MCP transport, the local authenticated HTTP relay and localhost development boundary. The prose distinguishes this relay from a hosted backend. Source: /Users/mitch/dev/mdb-case-assistant/mcp-server/src/relay-client.ts, /Users/mitch/dev/mdb-case-assistant/scripts/dev-relay-state.mjs.

Source limits:

- The pitch is explicitly dated to version 1.0.178. Current source inspection supports contracts but does not independently establish every feature or the 61-operation inventory in that historical release.
- No case data was fetched or written, no extension or relay was run, and no firedrill or adversarial security exercise was performed.
- The business benefit is a project rationale rather than a independently measured speedup. Source-level JSON/output contracts reduce a class of risk without proving every workflow safe.

### vocabulary.md

Dissent: A-R1 above.

Primary checks:

- Checked field-level LLM grounding/filtering and the limitations of token-overlap heuristics; the article correctly qualifies grounding as distinct from truth. Source: hub/scripts/docset_refine/vocabulary.py:380-428.
- Checked rendering, source/definition requirements, LLM origin/grounding markers and add-only alias registration. The source corroborates A-R1. Source: hub/scripts/docset_refine/vocabulary.py:468-533.
- Checked vocabulary grammar/linter references, including the P7 anchor expectation. Source: hub/scripts/llms_lint.py.
- Compared the proposed target line and retained generated line directly. The shared small/full claim is internally contradicted. Source: site/src/content/blog/vocabulary.md:102,110,113-116.

Source limits:

- The original generation artifact for the retained vocabulary output was not available; the post explicitly states this. The quotation remains a qualified historical record.
- No model generation, alias registration, tree mutation or retrieval evaluation was performed. Proposed sense IDs, relation fields, homonym navigation and consumer adoption remain design intent rather than demonstrated shipped behavior.
- A token-overlap score does not establish semantic correctness; the review checks the article qualification and source mechanics, not the factual adequacy of every generated term.

### six-months-of-hand-made-llms.md

Bounded approval.

Primary checks:

- Checked the recorded 11/20 to 14/20 result, 354 additional LLM units, raw/clean byte and page/code counts, and 11611 deterministic plus 354 generated units against the dated local record. Source: hub/docs/specs/2026-08-30-docset-golden-baseline.md.
- Read the author fetch record to check the cited specification and publisher observations as historical observations. Source: research/dr-llms/00-my-fetches.md.
- Checked the study author sample scope and fetch-traffic observations. The post keeps requests separate from proof of downstream use. Source: https://ahrefs.com/blog/llmstxt-study/.
- Checked the author HTTP Archive analysis and the 5.07% scoped adoption figure. Source: https://caseyrb.com/blog/state-of-llms-txt-adoption/.
- Checked Google guidance about additional AI files and the referenced llms.txt specification context. Source: https://developers.google.com/search/docs/appearance/ai-features, https://llmstxt.org/.

Source limits:

- The complete catalog, download volume, corpus page counts, delimited-document count and final failure inventory were not regenerated or downloaded during this review. The article frames them as its dated author record.
- The saved golden evaluation is evidence of the recorded run, not a new independent experiment. No extraction, synthesis or inference was run.
- The cited traffic/adoption studies have their stated sample and time limits; fetch evidence does not establish model consumption or general adoption across all sites.

### semantic-indexing.md

Bounded approval.

Primary checks:

- Recomputed results from the saved 11-question dataset without issuing queries: keyword/vector top results agree twice; the hybrid winner is neither leg first result twice; first vector timing is 124.62 ms and later timings have median approximately 15.42 ms. These support the dated demo statements. Source: site/src/data/demo.json.
- Checked semantic/default and facts/raw layer selection, model matching, first-use keyword-index handling and RRF rank summation with k=60 against the implementation. Source: hub/mcp-server/hub_mcp_server.py:316-367, site/tools/gen_demo.py.
- Checked FTS5 BM25 keyword ranking/default OR semantics and cosine scoring in the SQLite vector-store path. Source: hub/scripts/docset_indexer.py:279-291,345-367.
- Checked unicode61 tokenization/case folding and BM25 behavior against SQLite documentation. Source: https://www.sqlite.org/fts5.html.

Source limits:

- The saved demo is one recorded laptop run; no inference, indexing, query execution or benchmark rerun was performed.
- The timing data does not establish the cause of the first-query overhead or general latency on other hardware. The post retains that uncertainty.
- Rank agreement and RRF examples describe this dataset; there was no new human relevance labeling or broad retrieval-quality evaluation.

## Completion boundary

Root owns the minimal vocabulary correction, any post-change verification, repository validation and final completion reporting. This report preserves the reviewed pre-correction vocabulary hash and does not claim per-post CLEAN convergence.

Only `recheck-a.md` and `recheck-a.json` were written for this task. No target edits, article commands, inference, indexing, installation, service changes, build, tests, staging or commits were performed.
