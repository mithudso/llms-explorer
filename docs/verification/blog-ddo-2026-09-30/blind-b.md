# Independent blind blog review B

Reviewed 2026-09-30. Eleven posts were read in full. The audit found one Major and eight Medium occurrences (eight unique findings; B07a/B07b share a root cause). No Blocking finding was corroborated.

Assignment list only; no baselines, sibling reports, prior findings, writer scripts or git diff were read. This is same-model fresh-context independence, not cross-model validation.

DDO, document-critique, kill-the-AI-ism, explanation-document and security references applied. Diagnostic lenses were evaluated in this reviewer context because all four available agent slots were occupied.

## site/src/content/blog/semantic-skill-discovery-and-the-optimizer-family.md

Audited SHA-256: `ecf7a8840c13c94d7414761c22c30d02ee5dd4b45987a4e009ede9e670bf71b4`.

### B01 — Medium

**Span:** §1 lines 42 and 68.

The prose and result-field table promise a one-line reason in tam_recommend_skills output, within an article whose grounding note says September implementation details were reviewed.

**Reader consequence:** A reader implementing result explanations against the inspected September tool will request a field that its output does not contain.

**Primary evidence:**

- [/Users/mitch/dev/mdb-context-hub/mcp-server/src/service.ts](/Users/mitch/dev/mdb-context-hub/mcp-server/src/service.ts:2576) (2576–2584): recommendSkills maps skillId, title, category, description, score, matchedKeywords and contextPath; it does not map reason.
- [/Users/mitch/dev/mdb-context-hub/mcp-server/src/server.ts](/Users/mitch/dev/mdb-context-hub/mcp-server/src/server.ts:704) (704–706): The handler returns recommendSkills output unchanged as text and structuredContent.

**Smallest correction:** Describe the September response using score, matchedKeywords and contextPath. If keeping the June reported reason fields, label them as June observations whose original response transcript is unavailable; do not present them as the verified September response contract.

### B02 — Medium

**Span:** §6.6 line 183.

The compression paragraph groups LLMLingua, LongLLMLingua and LLMLingua-2 together as perplexity-scored token pruning.

**Reader consequence:** The grouping gives developers the wrong scoring and model architecture for LLMLingua-2 when choosing or reproducing a compressor.

**Primary evidence:**

- [https://arxiv.org/abs/2403.12968v2](https://arxiv.org/abs/2403.12968v2): The LLMLingua-2 paper describes task-agnostic token classification with a distilled bidirectional Transformer encoder; it distinguishes this from the earlier perplexity-based approach.
- [https://github.com/microsoft/LLMLingua](https://github.com/microsoft/LLMLingua): The primary project documents LLMLingua-2 as a distinct compression approach.

**Smallest correction:** Separate the methods: LLMLingua/LongLLMLingua use perplexity or information-entropy scoring; LLMLingua-2 uses a distilled encoder for token classification. Preserve the named methods.

**Source limits:**

- June query transcripts, reported scores and role-hook receipts were not available for independent reconstruction. Their historical qualifications should remain.
- September local source can establish lexical candidate membership and optional semantic page reranking; it cannot establish past tool responses or measured retrieval benefit.
- Historical optimizer versions, pass catalogs, token reductions, Glean behavior and local truncation thresholds were not independently rerun.

## site/src/content/blog/state-that-survives-the-session.md

Audited SHA-256: `5305ed6f421ac0da9b42dba2b0640c9a407f45ce02c6a7712aa3d160ff4fae29`.

No Medium-or-higher finding was corroborated within the source limits below.

**Source limits:**

- The historical SessionStart recall count, saved-prompt receipt, rotation-job state and v1.0.569 status were not recreated.
- Current dual-write-corpus-store source supports local-first storage with an asynchronous, best-effort Atlas mirror and retry/dead-letter behavior; it does not prove the historical run's durability or memory benefit.
- The research citations were checked for the described memory and poisoning mechanisms. No controlled A/B evidence of benefit was available.

## site/src/content/blog/legible-by-construction-automated-docs-indexes-logging-and-test-centric-design.md

Audited SHA-256: `dd2334457b287de78604b67115ddecff9b13b22a66d04fdcd93da7550a117db4`.

### B03 — Medium

**Span:** §6 line 162; related diagram wording at line 175.

The article states that the CLI/API/app surfaces cannot drift because they share one implementation.

**Reader consequence:** Shared domain logic prevents duplicated business implementations, but adapter-specific parsing, authorization, serialization and errors still differ. The absolute promise weakens the later requirement for adapter contract tests.

**Primary evidence:**

- [/Users/mitch/dev/mdb-context-hub/mcp-server/src/http.ts](/Users/mitch/dev/mdb-context-hub/mcp-server/src/http.ts:13) (13, 119–143): The HTTP adapter adds a 32 MiB body limit, origin rejection, HTTP method checks and request/response handling.
- [/Users/mitch/dev/mdb-context-hub/mcp-server/src/index.ts](/Users/mitch/dev/mdb-context-hub/mcp-server/src/index.ts:1) (1–7): The stdio entry point connects its own transport directly; it does not exercise the HTTP adapter's behavior.

**Smallest correction:** Limit the guarantee to changes in the shared domain implementation. State that interface parity still requires adapter contract tests. Keep the figure, but clarify that its 'can't drift' shorthand refers to shared domain logic rather than every surface behavior.

**Source limits:**

- June inventory counts and domain counts, test totals and operational status are dated historical observations, not a new run.
- The inspected CI checks tool names/counts, not every prose claim or schema semantic. Branch-protection settings were not inspected.
- Telemetry key-pattern redaction and free-text limits were checked in source; no security scanner or CI job was executed.

## site/src/content/blog/automated-auditing-and-security-first-software-design.md

Audited SHA-256: `0ac4d2fbea37c0fd3809adfe1d32ee40842d2c60fd7140b77e8a201687ab4bd1`.

No Medium-or-higher finding was corroborated within the source limits below.

**Source limits:**

- The June advisory totals and severity distribution were not reproduced with a fresh dependency audit.
- The inspected CI marks the audit step continue-on-error; the article appropriately distinguishes advisory checks from enforceable merge gates. Actual branch-protection settings were not inspected.
- The review did not execute scanners, establish a legal conclusion or verify procurement outcomes.

## site/src/content/blog/implementing-a-native-macos-meeting-intelligence-system.md

Audited SHA-256: `d0a0c8fe592188afc09b3ae8bd894d646112c996c4e6a379d6584286eefb1ad2`.

### B04 — Major

**Span:** §4 locale preparation, lines 164–166.

The illustrative code returns when AssetInventory.reserve(locale:) returns false and comments that this means the reservation limit was reached.

**Reader consequence:** Apple returns false when the locale is already reserved. A normal later invocation can stop before transcription even though its required locale is available; actual reservation failures throw.

**Primary evidence:**

- [https://developer.apple.com/documentation/speech/assetinventory/reserve(locale:)](https://developer.apple.com/documentation/speech/assetinventory/reserve(locale:)): The return contract says false means the locale was already reserved. Unsupported assets or a reservation limit produce an error.
- [https://developer.apple.com/tutorials/data/documentation/speech/assetinventory/reserve(locale:).json](https://developer.apple.com/tutorials/data/documentation/speech/assetinventory/reserve(locale:).json): The official machine-readable documentation exposes the same return and error contract.

**Smallest correction:** Allow both true and false to continue. Keep the Boolean only if needed to track whether this invocation created the reservation. Handle thrown limit/unsupported-asset errors separately and describe reservation cleanup ownership.

### B05 — Medium

**Span:** §4 results loop, lines 198–199.

The code stores the entire final transcript with audioTimeRange from only its first attributed-string run.

**Reader consequence:** For a result containing multiple timed runs, the JSONL utterance covers only the first run's audio. Playback and two-channel alignment can therefore use the wrong end time.

**Primary evidence:**

- [https://developer.apple.com/documentation/speech/speechmoduleresult/range](https://developer.apple.com/documentation/speech/speechmoduleresult/range): SpeechModuleResult.range is the audio-input range to which the result applies.
- [https://developer.apple.com/videos/play/wwdc2025/277/](https://developer.apple.com/videos/play/wwdc2025/277/): The Apple session demonstrates audioTimeRange on individual attributed-string runs for word-level highlighting.

**Smallest correction:** Store result.range for the whole utterance. Use each run's audioTimeRange only for finer word/run timestamps.

**Source limits:**

- The post explicitly describes uncompiled sketches and omitted helpers, not a shipped meeting system. No recording, transcription or application build was performed.
- Native reservation, result-range, immediate-return analyzer-start and Core Audio tap permission contracts were checked against Apple's documentation.
- Distribution entitlements, runtime permissions, speaker identity, channel purity, retention policy and organization-specific recording approval remain implementation responsibilities. Private downstream corpus integrations were not exercised.

## site/src/content/blog/comparing-output-quality-across-claude-model-tiers-and-effort-levels.md

Audited SHA-256: `2407e3cb4c5460cf78fcbe89cad8efd8a050397322c833837d49a921424aead1`.

### B06 — Medium

**Span:** §4 item 3, line 124; contradicted by §3.1 lines 79–88.

The interpretation calls Haiku's two neutral-prompt losses cosmetic and says all variance lived in T1.

**Reader consequence:** The article's own table shows T3 and T4 score differences, and its rubric treats return-type and sentence-length compliance as correctness. The interpretation misreports the demonstrated limits of the benchmark.

**Primary evidence:**

- [site/src/content/blog/comparing-output-quality-across-claude-model-tiers-and-effort-levels.md](/Users/mitch/dev/llms-explorer/site/src/content/blog/comparing-output-quality-across-claude-model-tiers-and-effort-levels.md:79) (79–88, 92–101): Neutral T1 is 10 for all models; Haiku loses one point each on T3/T4. Experiment B's total differences are confined to T1. The text identifies T3/T4 requirements as correctness constraints.

**Smallest correction:** Say that all Experiment B score differences were on T1. Describe the neutral T3/T4 differences as the stated return-type and sentence-length requirements, preserving every reported score.

**Source limits:**

- Original outputs, request-routing receipts, token counts and independent grading records are unavailable. Reported historical model names are not verified provider identifiers.
- Each condition has one response and the article now acknowledges sampling, harness and internal-reasoning confounders. No causal effect or purchasing recommendation was independently established.
- This was an internal arithmetic/rubric consistency check, not a rerun of model inference.

## site/src/content/blog/egpu-fallen-off-the-bus.md

Audited SHA-256: `dae242cffab4122cccef5068862b45a8b8b1f94cb8787b5af7bced92ce3cb61a`.

No Medium-or-higher finding was corroborated within the source limits below.

**Source limits:**

- Original kernel traces, BAR/register captures and service/inference receipts were not available; the reported incident's causal chain and successful recovery were not independently recreated.
- Linux Thunderbolt authorization, PCI resource handling and pci=realloc=off semantics were checked against primary kernel documentation.
- The official NUC 15 Pro TPS and Razer power documentation support the stated tunnel and adapter distinctions; they do not independently prove this system's measured behavior. No privileged hardware command was executed.

## site/src/content/blog/local-model-performance-evaluation-mlx-egpu.md

Audited SHA-256: `ac304ff07f7c8a72804e3fd5c2986a6252487f7b32cdde41c6d973e5052657f7`.

No Medium-or-higher finding was corroborated within the source limits below.

**Source limits:**

- The noindex flag, unverified evidence note and withdrawn section 7 were read and preserved. Matching raw comparative benchmark artifacts are unavailable.
- The downloadable benchmark uses nonstreaming generation and does not measure TTFT/jitter; the memory profiler's fixed 4096 value does not establish process RSS or dGPU allocation. Existing qualifications accurately bound these limitations.
- Apple/NVIDIA specifications and MLX/Tinygrad runtime documentation support general hardware/runtime descriptions, not the historical model/hardware comparisons. No benchmark, inference or device operation was run.

## site/src/content/blog/customer-docs-to-llms-family.md

Audited SHA-256: `a5a42b97c82c556be3d7b3d1a9550f6c466f84591afb8d4a9db47791d4a9d7b8`.

### B07a — Medium

**Span:** Export bullet, lines 127–128.

The article applies spec-v2 most-specific-wins nesting to exported hub/spoke indexes without separating navigation from published URL coverage.

**Reader consequence:** These curated exports link upstream vendor pages from a different hierarchy and often a different origin. A consumer cannot infer native vendor-page scope from the export folders.

**Primary evidence:**

- [https://llmstxt.org/](https://llmstxt.org/): The current v2 specification defines more-specific index coverage by the published URL path under which an index lives.
- [outputs/exports/code.claude.com.llms/overview/part-1/llms.txt](/Users/mitch/dev/llms-explorer/outputs/exports/code.claude.com.llms/overview/part-1/llms.txt): The saved artificial Overview/Part 1 index links upstream code.claude.com/docs/en/*.md URLs.
- [hub/scripts/docset_refine/export_llms.py](/Users/mitch/dev/llms-explorer/hub/scripts/docset_refine/export_llms.py:191) (191–194, 268–327): Page lines preserve upstream URLs while split exports create navigation directories and synthetic part buckets.
- [hub/scripts/llms_serve.py](/Users/mitch/dev/llms-explorer/hub/scripts/llms_serve.py:354) (354–365): The local service publishes exports under /d/...; that hierarchy does not make it the origin serving the linked upstream vendor pages.

**Smallest correction:** Call the spokes curated navigation indexes. Explain that v2 most-specific URL coverage applies when indexes are published within the relevant page origin/path; exported folders alone do not establish that scope.

**Source limits:**

- The displayed corpus/unit/page counts match the figures snapshot. The reproduction note already distinguishes that snapshot from later manifest counts.
- Original August acquisition/lint receipts were not recreated; command flags and generator behavior were inspected without crawling or indexing.
- B07a and B07b are two article occurrences of the same coverage-scope defect.

## site/src/content/blog/hub-and-spoke-indexes.md

Audited SHA-256: `c387126a7bad6bc69f817ca0e9d094c1c968c1fb3bd9488ef1f08e79478ea3ce`.

### B07b — Medium

**Span:** Lines 24–28, 71–74, 97–99 and 114–115.

The discussion treats the exported section/part hierarchy as path-scoped most-specific-wins coverage and asserts that every page URL lives under its spoke's path.

**Reader consequence:** Synthetic Overview/Part directories are navigation buckets. Their upstream /docs/en/ URLs are not descendants of /overview/part-1/, and a locally hosted export is not authoritative over a vendor origin. The statement overstates what P10/path coverage proves.

**Primary evidence:**

- [https://llmstxt.org/](https://llmstxt.org/): The v2 scope rule follows the published URL origin/path; syntactic index validity and curated navigation do not confer arbitrary upstream path authority.
- [outputs/exports/code.claude.com.llms/overview/part-1/llms.txt](/Users/mitch/dev/llms-explorer/outputs/exports/code.claude.com.llms/overview/part-1/llms.txt): Its linked pages use upstream /docs/en/ paths, not /overview/part-1/.
- [outputs/exports/developers.cloudflare.com.llms/cache/how-to/llms.txt](/Users/mitch/dev/llms-explorer/outputs/exports/developers.cloudflare.com.llms/cache/how-to/llms.txt): The exported index retains upstream vendor URLs.
- [hub/scripts/docset_refine/export_llms.py](/Users/mitch/dev/llms-explorer/hub/scripts/docset_refine/export_llms.py:191) (191–194, 268–327): The generator preserves upstream page URLs and creates synthetic split directories.

**Smallest correction:** Describe the export as a complete reachable navigation tree of curated indexes. Reserve most-specific-wins and URL containment claims for indexes actually published under the corresponding origin/path. Scope the historical P10 claim to its retained gate receipt or qualify it if that receipt is unavailable; do not call synthetic part directories page URL scopes.

### B08 — Medium

**Span:** Reproduce, lines 128–130.

The reproduction note says the current generator numbers parts consecutively, in contrast to saved Part 1/61/121-style names.

**Reader consequence:** Readers expecting newly generated Part 2/3 paths will not reproduce those names: the inspected current generator still derives part numbers from the first page offset.

**Primary evidence:**

- [hub/scripts/docset_refine/export_llms.py](/Users/mitch/dev/llms-explorer/hub/scripts/docset_refine/export_llms.py:287) (287–289): The label is Part {i + 1} with i ranging from 0 to len(pages) in PART_PAGES steps. With PART_PAGES=60 this produces Part 1, Part 61, Part 121.

**Smallest correction:** Remove the unsupported claim that current numbering is consecutive, or state that the inspected generator names parts from their starting page offsets. Preserve the saved export filenames.

**Source limits:**

- The saved exports and current generator were inspected without regeneration. Counts are character-derived token estimates, as the article states.
- No historical gate receipt proving P10 path coverage was available. Native same-origin URL scope and curated index navigation must remain distinct.
- B07a and B07b are two article occurrences of the same coverage-scope defect.

## site/src/content/blog/topical-llms-from-a-fact-pool.md

Audited SHA-256: `af002b2d0de52c4c6bba390847ab56d048d3d39f797995a338f3f315ea363377`.

No Medium-or-higher finding was corroborated within the source limits below.

**Source limits:**

- The August 168/79 snapshot is documented in the repository memory log. Later manifest counts differ, and the article already labels the snapshot correctly.
- Source inspection confirms keyword scoring plus file-prior affinity and optional embedding fallback. No embedding model or indexing job was run.
- The superiority of file affinity is a historical observation without preserved labeled evaluation metrics; it should remain an observation rather than a quantified performance guarantee. Source hyperlinks establish provenance, not fact truth.

## Coverage and limits

Every frontmatter field and prose section, code block, table, figure reference, reproduction instruction, link and qualification was read. Eligible defects were tested against primary documentation or repository source. The review covered intent and thesis preservation; structure and synthesis; technical correctness and operational feasibility; risk and failure modes; completeness and role/workflow; audience and pedagogy/usability; evidence and source verification; terminology and hallucination/injection; meta cleanup and voice.

Read-only review. No article commands, recording, inference, indexing, installations, services or configuration changes were executed. Historical observations are not independently reproduced.

No blanket certification. Missing empirical receipts are source limits, not findings where the prose already qualifies them. Minor style preferences and unsupported suspicions are omitted. Hashes identify the exact bytes read before any corrective iteration; changed posts require targeted re-audit. Root owns corrections and site validation.
