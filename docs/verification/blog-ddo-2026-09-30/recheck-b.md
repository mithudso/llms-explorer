# Independent Group B recheck — 2026-09-30

Reviewed all prose in six final articles. Five are approved within the stated source limits. One has a corroborated Medium source-fidelity dissent. “Approved” means no eligible dissent was found; it does not certify the historical experiment records, production execution, or CLEAN.

The reviewer did not author the Group B repairs and did not read Group B reports, blind-b findings, earlier repair rationale, or git diff. This is same-model independence. No article commands, builds, tests, inference, indexing, installs, service/config changes, external messages, article edits, staging or commits were performed.

All selected read-only document-critique lenses were applied: intent contract and reader outcome, structure and information hierarchy, technical correctness, operational feasibility and reproducibility, risk and failure modes, completeness, roles and workflow, audience fit, pedagogy and usability, evidence and source verification, terminology and referents, hallucination and injection resistance, meta and scaffolding cleanup, human voice, synthesis and cross-section consistency.

This independent review does not reset optimization iteration caps or waive evidence gaps. Any subsequent root fix is limited to a changed-span/hash guard, not a second full review.

## semantic-skill-discovery-and-the-optimizer-family

- Result: **approved**
- Reviewed SHA-256: `c78fd5e52b8d1b6052fab61b744031edce7598e58d95a9a999c91f60f6a269d0`
- Coverage: Read all 336 lines. Checked lexical tokenization, stopwords, field weights, matchedKeywords scope, search pagination, optional semantic page reranking/fallback, and role/query merging against service.ts and semantic.ts. Checked the Agent Skills description limit and progressive disclosure against the specification. Reviewed all four optimizer workflows, peer pass bounds, historical score examples, thresholds, method catalog, and evidence qualifications.

No corroborated Medium-or-higher dissent found.

Primary sources:

- /Users/mitch/dev/mdb-context-hub/mcp-server/src/service.ts (scoreSkill, searchSkills, recommendSkills, resolveRoleSkills)
- /Users/mitch/dev/mdb-context-hub/mcp-server/src/semantic.ts
- https://agentskills.io/specification
- /Users/mitch/.agents/skills/skill-optimizer/SKILL.md
- /Users/mitch/.claude/skills/skill-optimizer/references/passes.md

Source limits:

- June recommendation/role transcripts, similarity score runs, harness truncation experiments, token-reduction receipts, and exact installed-skill survey were not independently recovered. The article explicitly bounds these as historical/local observations.
- September implementation inspection supports the specifically dated correction; it does not reconstruct June scoring or prove recommendation quality. Optimizer source inspection does not certify that every historical run followed the described workflow.

## legible-by-construction-automated-docs-indexes-logging-and-test-centric-design

- Result: **dissent**
- Reviewed SHA-256: `2a0728980e57f9fd14a4db09a0380cd128262e92ebfb6849ebce7ac5ae23546b`
- Coverage: Read all 212 lines. Checked the June CI inventory gate, exact gated names/counts versus ungated prose, generator output serialization, telemetry event fields and key-based redaction, service/adapter separation, operations audit and documented runner gaps. Reviewed the distinction between project instructions, detection, and mechanically enforced gates; tested explanatory consistency by source inspection. Checked Aider repomap and Anthropic context retrieval descriptions against their primary documentation.

**B-RECHECK-01 — Medium: banner scope exceeds dated generator behavior.**

Span: site/src/content/blog/legible-by-construction-automated-docs-indexes-logging-and-test-centric-design.md:44, “writes JSON registries and generated Markdown. Every generated output carries the literal banner:”

The example makes the banner a universal marker of the generated/manual boundary, but its JSON registries and YAML manifests have no such banner. A reader cannot apply the described boundary by looking for that marker in every generated artifact.

Primary evidence: `/Users/mitch/dev/mdb-context-hub`, revision `eb6ce292c81e58983ae85ac3c74cb658da0ef5e2`, `scripts/skill-pack-lib.mjs`:741–761. Context Markdown receives `GENERATED_WARNING` at 741; YAML serializes directly at 742; registries/audit serialize as bare JSON at 745, 754 and 761. This finding is corroborated in the June source, not inferred from a later redesign.

**Smallest supported correction:** Replace “Every generated output carries the literal banner:” with “Generated Markdown carries the literal banner:”. Keep the JSON registry mention and the exact banner unchanged.

Primary sources:

- /Users/mitch/dev/mdb-context-hub at eb6ce292c81e58983ae85ac3c74cb658da0ef5e2: .github/workflows/ci.yml; scripts/skill-pack-lib.mjs; mcp-server/src/telemetry.ts; mcp-server/src/service.ts; docs/tool-inventory.json; docs/external-calls.md
- https://aider.chat/docs/repomap.html
- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

Source limits:

- No server was started, tests executed, external call made through the application, or operations runner invoked. This is a source review, not a runtime coverage or redaction audit.
- The architectural principles and claimed productivity value are author judgments; repository source supports the named mechanisms, not general empirical superiority. The source documents contain known coverage gaps.

## implementing-a-native-macos-meeting-intelligence-system

- Result: **approved**
- Reviewed SHA-256: `3dd87fcbcf4ab631079781b43fd2b6ed116a99b934b504b1912eb9217d6e66cd`
- Coverage: Read all 371 lines. Checked Core Audio tap/aggregate-device lifecycle, global-versus-process capture scope, system audio permission and usage-description requirements, OS version bounds, microphone separation, real-time callback constraints, format conversion, clock/timestamp handling, SpeechAnalyzer asset reservations, optional formats, result ranges and finalization. Reviewed channel labels versus person identity, bounded utterance ingestion, account attribution, consent/retention controls, model availability, guided-generation limits, inference labels and human review. Treated the Swift blocks as the explicitly disclosed illustrative API shape.

No corroborated Medium-or-higher dissent found.

Primary sources:

- https://developer.apple.com/documentation/CoreAudio/capturing-system-audio-with-core-audio-taps
- https://developer.apple.com/videos/play/wwdc2025/277/
- https://developer.apple.com/documentation/speech/assetinventory/reserve(locale:)
- https://developer.apple.com/documentation/speech/speechanalyzer/bestavailableaudioformat(compatiblewith:)
- Apple public DocC JSON for those three symbol/sample pages
- /Users/mitch/.claude/skills/references/granola-transcription.md

Source limits:

- No Swift compilation, capture, transcription, asset download, corpus ingestion, model inference, sandbox validation or App Store review was performed. The article explicitly identifies omitted helpers and production error handling.
- Apple API documentation supports the API contracts, not the proposed system as an implemented product. The existing corpus deployment, historical meeting-account integration, third-party accuracy/performance comparisons, and long-transcript behavior were not independently reproduced.
- The local Granola reference supports the named polling/dedup/error-handling pattern. It does not establish that the proposed native ingestion has been built, or certify current vendor pricing/features.

## comparing-output-quality-across-claude-model-tiers-and-effort-levels

- Result: **approved**
- Reviewed SHA-256: `9f4656e45faba9409adebf96a5b2f234003aea4c6375e61cfb12df0022826e99`
- Coverage: Read all 187 lines. Reviewed model labels, task fixtures, deterministic rubric, answer arithmetic, score aggregation, word counts, mutable-input versus required behavior, effort/tier comparison, interaction interpretation and table-to-conclusion consistency. Checked current primary Claude model documentation as a temporal boundary. The article now distinguishes reported single samples from verified provider routing and avoids causal/population claims.

No corroborated Medium-or-higher dissent found.

Primary sources:

- https://platform.claude.com/docs/en/models/overview
- The article’s preserved tasks, answer samples and score tables (internal arithmetic consistency only)

Source limits:

- The raw experiment outputs, exact system prompt, provider request/response routing, effort mapping, latency/billing records, and repeated trials were not independently recovered. Reported model IDs and scores remain historical observations, not independently authenticated calls.
- Current vendor model documentation cannot prove the exact availability or routing at the dated experiment scope. Small numerical comparisons are valid for the reported table but do not establish statistical significance, causal effort effects, or a purchasing recommendation.

## customer-docs-to-llms-family

- Result: **approved**
- Reviewed SHA-256: `3417a59a54f1d96db9c8bb0f572e5fb453c9b4d4085db92f79876098fa2409d1`
- Coverage: Read all 147 lines. Reviewed acquisition fallback/probe validity, deterministic refine commands as data, page/unit/count relationships, full/small/facts artifact roles, whole-page character budget and approximate token estimates, typed/sourced fact claims, phase-specific lint history, index split behavior, key-material handling, exported versus origin-authoritative scope, and snapshot-date caveats. Checked exporter implementation and dated project receipts, without executing any recipe.

No corroborated Medium-or-higher dissent found.

Primary sources:

- /Users/mitch/dev/llms-explorer/hub/scripts/docset_refine/export_llms.py (build_small, build_split_index, _split)
- /Users/mitch/dev/llms-explorer/logs/memory-hub.md: v1.1.54 and v1.1.55 (2026-08-30), v1.1.56 (2026-08-31)
- /Users/mitch/dev/llms-explorer/outputs/exports/ (named manifest/artifact source scope)

Source limits:

- No crawl/refine/export/lint/index stage was run. Retained source code and dated receipts support the mechanism and described phase changes; they do not authenticate a single simultaneous run containing every current/generated figure count.
- All published counts and historical lint statuses retain their snapshot scope. Individual facts-to-mirror anchors, vendor PEM provenance and every leaf index were not exhaustively re-linted. Article notes distinguish later refreshes and preservation of the reported key-material warning.

## hub-and-spoke-indexes

- Result: **approved**
- Reviewed SHA-256: `dbdcc5c74d473de3825667ad7b9cfb90719ffbd7ce6ba47abd1a67a5c042a73c`
- Coverage: Read all 136 lines. Checked recursive path partitioning, 10,000-byte split threshold versus 100,000-byte High threshold, 60-page buckets, actual part-name offsets, root Optional handling, metadata/description links, no-page-drop intent, nested serving and relative-link scope, v2 origin/path authority qualifications, and generator parity workflow. Source inspection supports the algorithm; the explicit authority qualification prevents local export paths from claiming vendor-origin precedence.

No corroborated Medium-or-higher dissent found.

Primary sources:

- /Users/mitch/dev/llms-explorer/hub/scripts/docset_refine/export_llms.py: INDEX_SPLIT_BYTES, PART_PAGES, _split, build_split_index
- /Users/mitch/dev/llms-explorer/logs/memory-hub.md: v1.1.55 (2026-08-30)
- Retained origin/path authority explanation in the article

Source limits:

- Historical P10 agent-retrieval receipts and complete lint transcripts were not recovered; the article explicitly limits that evidence. No serving, lint, generation, retrieval or agent test was executed.
- Source inspection verifies partition/filename logic and scope qualifications, not live serving availability, downstream agent behavior, or that the generated snapshot is still identical after future refreshes.

## Receipt and disposition

Six original reviewed hashes remain recorded above and in the JSON. They were verified before the report writes and on readback. Root owns the single correction. Keep the original dissent receipt; attach any bounded follow-up span/hash result separately.
