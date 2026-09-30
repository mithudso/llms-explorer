# Independent Group C recheck

Reviewed 2026-09-30T17:36:07.258326+00:00. Separate author, first-time review of these three files, same model. No prior Group C report, finding, repair rationale, script or git diff was read. Targets remained unchanged.

One findings-only audit completed passes0–14,10.5,11.5, terminology, full prose voice, source/invariant and injection checks. Technical architecture/explanation contract applied; no invented measured results, customer quotes or sales approvals were required.

| Post | Reviewed SHA-256 | Result | Eligible Medium+ |
|---|---|---|---|
| reducing-llm-cost-and-latency-without-losing-context.md | `b2261c3b16a84f60e353efdbaa4cd6f6252816901f5389ff3b47359911ef7520` | dissent | 2 |
| stickysites-project-briefing.md | `fa10f9b1663f4effe5c747d17bd44c1b5609ed6e50b87d8abc4e43cc0be011c4` | approved | 0 |
| v2-vs-v1.md | `dc9d82db983c1af4e5c4123ae1a803a0f632e1fa1a45d82ef0c4b211e9e8cf67` | approved | 0 |

## Corroborated dissent

### RECHECK-C01 — Medium

Location: reducing paper lines 22, 69, 71, 125, 126, 170.

The age-horizon table drops older source data before it can enter a prompt, and the wording suggests retrieval bounds govern the entire assembled prompt.

- Primary: `/Users/mitch/dev/mdb-tam@e390fd30ccbad5aa8c974c702f9b3b7a32db9214:src/background/context-modules.js` (429-447). isDocumentWithinAge filters indexed documents. Missing/unparseable timestamps pass. searchFieldedIndex applies that filter before ranking.
- Primary: `/Users/mitch/dev/mdb-tam@e390fd30ccbad5aa8c974c702f9b3b7a32db9214:src/background/preprocessor.js` (2013-2058,2110-2197,2200-2248). buildPromptScopedContextObject keeps base segments including slack_digest. applyRetrievalSelectionToScopedContext returns unchanged for empty query or no matching documents, conditionally filters selected ID-backed arrays, and has no Slack-digest age filter. contextToCompactPromptContext serializes both the scoped context and selected retrieval evidence.

Minimal correction: Scope PROMPT_SCOPE_RESULT_LIMITS and PROMPT_SCOPE_MAX_AGE_DAYS to selected indexed modules/chunks. Say dated index candidates outside the per-source horizon are excluded; undated candidates pass. Say base context can retain older or unmatched material, including Slack digest data, and empty/no-match retrieval does not prune it. Remove the executive claim that all older data is dropped before any prompt is built; qualify the table and conclusion consistently. Retain all existing numeric limits, June date and unmeasured-result caveats.

Meaning change: Corrects a universal final-prompt exclusion guarantee into the actual conditional retrieval filter. Does not change constants or assert a measured cost/quality result.

Disposition: source unchanged; root owns the correction.

### RECHECK-C02 — Medium

Location: reducing paper lines 22, 79, 130, 170.

The background content optimizer strips source markers and removes orphan rules before corpus text can be retrieved.

- Primary: `/Users/mitch/dev/mdb-tam@e390fd30ccbad5aa8c974c702f9b3b7a32db9214:server/src/corpus-agents/content-optimizer.js` (20-47,75-122). source_markers and orphan_hr have no replacement field. analyzeTextQuality reports their matches. optimizeDocument applies only patterns whose replacement is defined, namely excessive newlines and trailing whitespace. optimizeDocument defaults to dryRun=true and only writes with dryRun=false.

Minimal correction: State that the analyzer flags source markers, orphan rules and high redundancy. The apply path collapses excessive newlines and strips trailing spaces; dryRun is the default. Remove the guarantee that every corpus document is cleaned before retrieval. Label the table as analysis available / transformations on explicit non-dry-run application, and align the summary/conclusion. Do not claim source-marker or orphan-rule removal by this module.

Meaning change: Separates detection from executed transformation and removes an unsupported mandatory pre-retrieval order. Retains the optimizer path and demonstrated newline/whitespace mechanisms.

Disposition: source unchanged; root owns the correction.

## reducing-llm-cost-and-latency-without-losing-context.md

Contract: Explain the June 2026 reduce-then-cache mechanisms and their limitations. Audience: Engineers and technical leads reviewing an LLM-backed TAM dashboard.

Verification:

- 12/4 to24/12 retrieval limits; age constants30/120/60/365; segment TTLs2–20min; line-case dedupe; scoped minified JSON. Constants and serializer confirmed; age/full-prompt scope contradicted as RECHECK-C01. Primary: mdb-tam@e390fd30ccbad5aa8c974c702f9b3b7a32db9214: src/background/preprocessor.js:282-299,628-688,2200-2248.
- Recent helper72h/40 default; feedback cases144h/40,Slack72h/160,meetings168h/12; meeting prep3200 and deep dive8192. Confirmed statically, not executed. Primary: mdb-tam@e390fd30ccbad5aa8c974c702f9b3b7a32db9214: src/background/llm.js:1554-1560,2946-2980,3319-3341,3918.
- System/preamble explicit cache breakpoints followed by uncached live snapshot; server1024 default; text escape and80/400 limits. Confirmed request construction and default. Primary: mdb-tam@e390fd30ccbad5aa8c974c702f9b3b7a32db9214: server/src/live/recommender.js:37-38,154-165,188-195,229-245.
- Extension prefix/suffix cache envelope,5m/1h normalization,on-by-default toggle and cache usage capture. Envelope/settings mapping confirmed.9 cited implementation files are byte-identical to June revision; current options file differs, so its historical facts are restricted to June source. Primary: mdb-tam@e390fd30ccbad5aa8c974c702f9b3b7a32db9214: src/background/llm.js:470-494,589-633; src/options/options.js at June revision.
- Anthropic prefix matching,write premium,5m refresh and1h cadence guidance. Confirmed vendor guidance; no workload savings inferred. Primary: https://platform.claude.com/docs/en/build-with-claude/prompt-caching.
- UTF-16 string caps256×1024/16000/32000; per-workflow output budgets; same-entity queue coalescing. Confirmed static length/slice, constants and entity-key filtering. Coalescing is not cross-source fact deduplication. Primary: mdb-tam@e390fd30ccbad5aa8c974c702f9b3b7a32db9214: server/src/lib/recommendation-store.js:34-46; src/background/monday.js:36-37; server/src/jobs/runner.js:83; src/background/corpus-store/dual-write-corpus-store.js:125-130.
- Noise removal flags/transformations. Partially confirmed; RECHECK-C02. Primary: mdb-tam@e390fd30ccbad5aa8c974c702f9b3b7a32db9214: server/src/corpus-agents/content-optimizer.js.

Source limits:

- Explicitly disclosed, retained: No controlled cost, latency, hit-rate or answer-quality comparison is published. Static request construction and named settings do not establish realized savings or complete live deployment acceptance.
- Partial telemetry confirmed: Extension callClaudeModel returns four cache/input/output usage fields. Server llm-trace/live-recommendations schemas retain input/output counts rather than separate cache counters. Per-path cost/payback needs additional telemetry.
- Scoped negative claim: Lossy runtime compression rejection is documented; no per-user budget/cost-adaptive model implementation was identified in the cited paths. This audit does not prove absence from every unpublished branch.

Coverage: all selected passes reviewed; no attempted prompt injection; complete original voice and terminology reviewed. Two Medium source-scope errors remain proposed.

## stickysites-project-briefing.md

Contract: Describe StickySites v1.10.0 features, local-only architecture and trust boundaries. Audience: Leadership, maintainers, reviewers and new extension users; per-section labels.

Verification:

- MV3; storage/activeTab/contextMenus; no host_permissions; broad all_urls content scripts; ES-module worker/classic ordered scripts; Alt+S. Confirmed supporting dated snapshot; Chrome restrictions separately verified. Primary: stickysites@427aa9adf54ac3d0ab52c0158e900b2346b8920d: manifest.json; src/background/service-worker.js.
- Six storage scopes; per-page origin+pathname; cached JWK until lock/disable; AES256GCM12-byteIV; PBKDF2SHA256600000iterations16-byte salt; six-key re-encryption. Confirmed code; no decryption/key theft/live security test. Primary: stickysites@427aa9adf54ac3d0ab52c0158e900b2346b8920d: src/content/note-types.js; src/content/crypto-content.js; src/shared/crypto.js; src/shared/notes-storage.js.
- 72 tests/three suites; Node>=22; dev-only canvas/Vitest; no runtime third-party imports/build. Static source confirmed; minor version ambiguity retained as limit. Primary: stickysites@427aa9adf54ac3d0ab52c0158e900b2346b8920d: package.json,.nvmrc,.github/workflows/test.yml,tests/*.js,manifest.json.
- 500ms save;rich text/search/popout/outline/mentions;SPA re-key;bare-key/modifier conflict;selection escaping. Static handlers and declared categories confirmed; no live UI acceptance claim. Primary: stickysites@427aa9adf54ac3d0ab52c0158e900b2346b8920d: src/content/panel.js;sticky-inject.js;mentions.js;outline.js;popup.js;popout.js.
- No external calls/identity/telemetry in described snapshot; shared DOM risks and execCommand deprecation. No network primitives found in inspected historical shipped sources; shared-DOM and deprecated API behavior confirmed by documentation. This is scoped static evidence, not a proof of all possible browser network activity. Primary: stickysites@427aa9adf54ac3d0ab52c0158e900b2346b8920d: manifest and shipped JS/HTML network-primitive scan; https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts; https://developer.mozilla.org/en-US/docs/Web/API/Document/execCommand.

Source limits:

- Historical snapshot limit: The described no-Drive/bare-key behavior is corroborated by v1.10.0 main snapshot 427aa9adf54ac3d0ab52c0158e900b2346b8920d. Version1.10.0 is not a unique immutable tag: earlier June4 code included Drive/identity and June17 afternoon merges removed bare shortcuts and changed Vitest. The article date has no review time; approval is bounded to its described historical snapshot, not every commit carrying the same version.
- Minor supporting measurement limit, below eligible floor: The approx other-content-scripts line total~1274 is not independently reproduced: summing the named src/content JavaScript paths except panel/outline gives1700 at the supporting snapshot. Principal individual component sizes(1848/800/363/86/71/869/41) and572 test lines match. This scope indicator does not change installation, permissions or security behavior and is not scored Medium.
- Static verification, not executed tests: 72 statically declared tests across crypto5/notes-storage46/outline-ops21 and CI npm ci/npm test verified in source; no test run or live UI receipt was produced.
- Unmeasured performance and planning: The2–4second low-end unlock range has no benchmark receipt in this review. Shadow DOM/spinner plans are dated statements, not confirmed present-day delivery.

Coverage: all selected passes reviewed; no attempted prompt injection; complete original voice and terminology reviewed. No corroborated Medium+ dissent. Approval is bounded to the recorded bytes and disclosed source limits.

## v2-vs-v1.md

Contract: Explain August2026 proposal changes alongside the independently named hub pipeline transition. Audience: Documentation publishers and hub maintainers who need to separate spec validity from pipeline migration.

Verification:

- v2 modifiedAugust10;H1-only required;BOM;subpaths/most-specific;twins and rel discovery;Optional convention;view/search/follow;well-known rejected. Confirmed primary proposal/changes. v1 validity is a format compatibility statement, not a universal answer-quality guarantee. Primary: https://llmstxt.org/ and https://llmstxt.org/changes.html.
- llms_acquire full→index;absolute links only;HTML rejected;no Accept negotiation/docs API/index recursion;Mintlify/YAML/Cloudflare parsing. Confirmed static implementation; proposed acquisition ladder distinguished. Primary: hub/scripts/llms_acquire.py: complete file, especially _fetch/probe/split_llms_full/parse_llms_index/acquire.
- summary.json cleanup guard;inside pages unlink only;._skip;lint after deletions;CLI dry-run;zeroHigh gate. Confirmed, including guard weakness and ordering accurately disclosed. Primary: hub/scripts/docset_rollout.py:141-198.
- 10KB split,100KBwrong-name andI2/N6/H3 lint;deterministic passes;BOMhygiene;directory traversal. Confirmed static checks/thresholds; no live links checked. Primary: hub/scripts/llms_lint.py:76-77,395,518-529,1353-1393,1457-1540,1624-1645; hub/scripts/docset_refine/export_llms.py:35-36.
- facts auto query layer;dimension mismatch error;FTS keyword layer;markdown serve endpoints/headers. Confirmed code; deployed store identity not enumerated. Primary: hub/scripts/docset_indexer.py:245,350-373,856-868,962-977; hub/scripts/llms_serve.py:300-312,365-396; hub/scripts/embed_core.py:54.
- V1 rationale andV2reference/extract/export shapes;reported metrics. Design/working-note attribution and current metrics confirmed; historical fact count separately limited. Primary: hub/docs/specs/2026-08-30-docset-reference-extraction-design.md; hub/docs/specs/2026-08-30-llms-txt-as-docset-schema-design.md; docs/site/components/11-v2-vs-v1.md; outputs/exports/code.claude.com.llms/manifest.json.

Source limits:

- Explicit historical metric limit: Current manifest confirms191pages,llms-full acquisition,root1136bytes/~280tokens,small199155manifest-size units/~49785estimated tokens andfull~2.1Mestimated tokens. It currently reports14386units/~873788fact tokens. Article explicitly labels14031/~845k as the reported August30 snapshot; that original receipt was not independently recovered in this review.
- Explicit consumer assessment limit: Claude Code/Cursor/generic MCP/Lighthouse compatibility cells are expectations conditional on fetch configuration; no consumer tests were run or receipts included. They are not approved as verified current product guarantees.
- Static procedure limit: Cleanup guard and ordering confirmed from code; dry-run/backup/usable-index precautions are appropriate. No cleanup or lint command was executed.
- Embedding scope: mxbai-embed-large is the docset code default and query honors the recorded docset model; environment/CLI overrides exist. This review did not query every deployed store or call an embedding model. Dimension-mismatch guard is confirmed.

Coverage: all selected passes reviewed; no attempted prompt injection; complete original voice and terminology reviewed. No corroborated Medium+ dissent. Approval is bounded to the recorded bytes and disclosed source limits.

No article procedure, test/build/install/service, inference/indexing/Ollama, stage/commit or telemetry action was run. Hash readback confirmed all three source files still match their reviewed hashes.
