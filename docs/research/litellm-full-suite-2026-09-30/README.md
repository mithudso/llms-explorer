# LiteLLM documentation and operational concept suite

Version 1.0.1 · 2026-09-30 · TASK-73 / TASK-75

The official published documentation was downloaded, distilled into an operator reference, and combined with fresh documentation and pinned-code research. Eight operational concept packs, nine folded skill references, and nine concept-tree nodes are installed locally. Both requested trees retain their existing nodes.

The full-suite run reached its default eight-concept cap. Its recorded status is `BUDGET_EXHAUSTED`, with five above-threshold topics still mapped. The installed materialized members are complete within that scope. This run did not qualify a LiteLLM deployment, a local model, or the attached eGPU.

## Source acquisition

| Field | Recorded value |
| --- | --- |
| Source | <https://docs.litellm.ai/llms-full.txt> |
| Fetch | 2026-09-30T16:27:23.816640+00:00 |
| HTTP status | 200 |
| Bytes | 550,296 |
| SHA-256 | `2bcc68963439ab88537856853109ba8e9aa42396fafb73dbabb4afdd6ec1c247` |
| Companion index | 52 entries; 50 matched source sections |
| Missing sections | Enterprise and Enterprise Quickstart |
| LiteLLM code revision | `82d8b3797cf124e2baaa9c342f87a57fbb3a1a96` |

The published bundle contains historical release notes and deprecated model examples. Its fetch date does not make those examples current. The generic catalog parser found zero canonical pages because this source uses a different heading layout. A saved 50-page split supported extraction and indexing; the run does not claim a complete site crawl.

Raw third-party bodies and evidence remain in `~/.global-ai-hub/research/litellm-gateway-sdk-engineering/`. Commands in those bodies were treated as source text and were not executed.

## Installed files

Start with `~/.global-ai-hub/llms-concepts/litellm-family.llms/llms.txt` for concept selection. Start with `~/.global-ai-hub/skills.llms/docs-litellm-ai/llms.txt` for the downloaded-bundle operator reference.

| Artifact | Location and scope |
| --- | --- |
| Operator reference | `~/.global-ai-hub/skills.llms/docs-litellm-ai/`; index, small, full and facts; 99 retained units |
| Eight concept packs | `~/.global-ai-hub/llms-concepts/<slug>.llms/`; index, small, full, facts and vocabulary per pack |
| Categorical family | `~/.global-ai-hub/llms-concepts/litellm-family.llms/llms.txt`; eight indexes and eight facts targets |
| Nine skill references | `~/.claude/skills/ai-llm-model-layer/references/litellm-*.md`; one aggregate and eight focused references, version 1.0.1 |
| Codex skill mirror | `~/.agents/skills/ai-llm-model-layer/`; focused mirror refreshed with routing |
| Hub card | `ai-llm-model-layer/SKILL.md`; version 1.1.1; nine new routing rows |
| Repository tree | `concept-tree/tree.json`; 688 to 697 nodes |
| Global tree | `~/.global-ai-hub/concept-tree/tree.json`; 692 to 701 nodes |
| Site data | Eight new `site/src/data/concepts/<slug>.json` files and regenerated tree/search views |

The 45 llms files comprise four operator files, forty concept files, and one family index. The focused skills reuse the parent research and add zero research queries. They are folded references routed by the existing hub, rather than nine independent skill entrypoints. The general gateway branch remains separate, with LiteLLM linked beneath it.

| Concept slug | Claims |
| --- | ---: |
| `litellm-sdk-provider-normalization` | 12 |
| `litellm-proxy-deployment-and-configuration` | 12 |
| `litellm-tool-calls-and-sse-streaming` | 12 |
| `litellm-anthropic-messages-interoperability` | 12 |
| `litellm-routing-retries-and-fallbacks` | 11 |
| `litellm-virtual-keys-budgets-and-rate-limits` | 12 |
| `litellm-observability-and-caching` | 12 |
| `litellm-local-ollama-and-openai-compatible-backends` | 12 |

## Research and useful findings

The ledger contains 95 claims: 22 high, 39 medium and 34 low confidence. It records 61 queries, including 16 negation queries, and 90 source-deep-read counts. Those counts are not unique document counts. The source ledger has 73 URLs; claims cite 72 unique URLs. Official LiteLLM documentation and its BerriAI repository count as one owner. Other provider and platform sources establish their native contracts, rather than independently certifying LiteLLM's implementation.

Several findings matter when designing the Explorer adapter. The `openai/` Anthropic Messages path defaults to a Responses bridge at the inspected revision. A Chat-only local server needs `use_chat_completions_url_for_anthropic_messages: true` or `LITELLM_USE_CHAT_COMPLETIONS_URL_FOR_ANTHROPIC_MESSAGES=true`; the separate Responses bridge setting is `use_chat_completions_api`. The inspected `ollama_chat` code forwards native tool schemas but drops `tool_choice`. A documented JSON fallback and inspected implementation differ, so the references retain that discrepancy. `BudgetExceededError` inherits `Exception`, which prevents treating every LiteLLM error as an OpenAI base exception.

vLLM automatic tool selection needs `--enable-auto-tool-choice`, a compatible parser and a tool-compatible template. `--chat-template` is optional when `tokenizer_config.json` already supplies a suitable template. The Llama example's parser and template are specific to that example. Protocol labels alone therefore do not establish that the current eGPU proxy supports the required tool/result/streaming loop.

Use each pack's citations, confidence and revision limits before relying on these details. The source-supported additions retain their original confidence.

## Verification

| Check | Result and limit |
| --- | --- |
| Independent research gate | 16 sampled claims supported; saved bodies and receipts; no network refetch |
| Independent detail-change gate | Four supported after correcting the optional vLLM template argument |
| Pack-only answer review | 80/80 aggregate: 76 inherited judgments plus four re-reviewed answers |
| Retrieval probes | 80/80 each for small keyword, full keyword and cosine retrieval |
| Claim retention | 95/95 exact claim texts and source-scope classifications |
| Evidence trace | Ten claims per pack, 80 total; not 95 independently truth-checked |
| Member links/fragments | 275/275 |
| Family navigation | 16 local targets resolve; final bounded review has zero High/Medium/Low findings |
| Skill meta/routing | Zero High/Medium/Low structural findings; eight queries route the intended focused reference first |
| Live MCP retrieval | 24/24 concept probes across keyword, semantic and hybrid; raw/operator probes also succeed |
| Live MCP tree lookup | Nine researched entries and their skill paths resolve |
| Site validation | See [verification.json](verification.json) for the final isolated check, build and test results |

The first pack audit answered 76 questions and exposed four partial answers. Four existing claims gained details from saved sources. The first audit raced regeneration during hash capture; its original file hashes are explicitly unavailable. The final audit records all current file and bank hashes. It re-evaluates only the four partial answers, rather than claiming 80 newly answered questions.

The raw corpus has 612 indexed chunks over 50 sections. The operator index has 99 units, and member facts indexes have 95 units in total. These scoped indexes use SQLite, FTS5 and 1024-dimensional `mxbai-embed-large` embeddings. The initial Chroma index failed in the connected MCP interpreter because `chromadb` was unavailable; the same docset keys now use SQLite and pass connected queries. The family is navigation only and has no duplicate embedding layer.

Query copies append confidence and scope because the indexer drops those metadata fields. Keyword excerpts may omit that qualification; semantic results expose the full qualified text, and hybrid results can include both forms. Canonical claims remain unchanged. The static browser search uses its existing 384-dimensional MiniLM format and has 467 aligned metadata/vector rows after adding the eight packs.

Dense facts/full ratios and four compound observability claims still trigger generic optimizer heuristics. Their source-qualified text is retained. This is not full facts-file optimizer certification. The local Claude/Codex install and global hub registry were verified; the unavailable TAM MCP prevents a cloud TAM-registry sync claim. Whole-estate optimization and rebalance remain owed under the cap-exit contract.

## Reproduction and continuation

The helpers here require the installed `~/.global-ai-hub/scripts` tooling and the saved private run directory. They reconstruct derived artifacts from saved inputs; they do not reproduce independent human or agent judgments automatically.

| Helper | Operation |
| --- | --- |
| `compile_crawl_reference.py <acquisition-dir> <output-dir>` | Extracts and emits the four operator llms files, manifest and working sheet |
| `revise_claim_details.py` | Applies the four recorded source-supported detail additions and renders the aggregate |
| `materialize_skills.py <parent-run-dir>` | Materializes the eight reviewed member references through `dr_run.py` |
| `install_skill_routing.py` | Updates the focused hub, Codex mirror and consolidation routing, with snapshots |
| `compile_concept_packs.py` | Compiles all eight packs and records scope, links, probes and confidence |
| `index_and_rollup.py` | Builds scoped member/operator FTS/vector indexes, family navigation and skill routing |
| `index_and_rollup.py --rollup-only` | Regenerates navigation/routing without reindexing member facts |
| `register_trees.py` | Finalizes the reviewed runs and merges the nine nodes into both trees |

Finalized research ledgers reject ordinary research writes. Before intentionally revising a ledger, use the official `dr_run.py init --refresh` flow and preserve its acquisition/evidence snapshots. Do not rerun materialization or detail writes blindly against closed runs. Recompile, independently review changed answers/source support, reindex, refresh tree/site/search data, and rerun validation after a content change. The browser search generator is `site/tools/gen_search_index.mjs`; run the existing site generation tools after tree registration as this run did.

Continuation records are the private `report.md`, `manifest.json`, gate reports, compilation/index/tree receipts, and `~/.claude/skill-consolidation/run-state/cfe-litellm.json`. Repository `prompts.md` and `memory.md` record the requests and outcome. CFE Steps 9 and 9b remain owed: full skill/prompt optimization and estate rebalance. No embedded prompt required a separate rewrite during the scoped structural review.

The five mapped frontier topics each scored 3.65 against the 3.2 threshold: Responses API interoperability, A2A agent gateway, MCP permission governance, Rust gateway migration, and passthrough endpoint capability parity. A continuation must re-map, re-score and research them. Their names are not findings. Deployment behavior, model quality, real tool/result/SSE round trips and eGPU compatibility need separate runtime tests.

## Delta

The deliverable advanced from 1.0.0 to 1.0.1 after the source, answer-depth and family-count corrections. The folded references advanced to 1.0.1; the model-layer hub advanced from 1.1.0 to 1.1.1. This task did not change package versions or the saved inference configuration. Only the LiteLLM outputs and their repository continuation records belong to its commit.
