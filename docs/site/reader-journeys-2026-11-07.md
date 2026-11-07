# Reader journeys and useful-action measurement

Version: 1.0.0
Delta: implements the November6peer-review recommendations.
Task: TASK-1202. Date: 2026-11-07.

## What changed

LLMSX presents practical engineering for AI agents. Four primary destinations organize guides and experiments, skills, the research library and apps. Concept tree remains an explicit header link and homepage preview. The broad library, chronological article archive, original first workflow and existing installation anchors remain available.

Three worked workflows connect a concrete example to an article, a reference file, a skill and a relevant app. The skill-maintenance example includes an intentionally weak instruction, a revised instruction and a three-case evaluation rubric. It is a reproducible exercise, not a claim that this illustrative skill has been benchmarked. The article links retain the original experiment/backtest scopes.

Three app pages show the task, representative screenshot, environment, first useful result, recommended setup, verification command and limits. Detailed setup stays on the existing downloads page. HTML and Markdown twins share authored workflow/app JSON.

## Recommendation disposition

| Recommendation | Implementation |
|---|---|
| One audience and organizing promise | Homepage, shared title/brand/footer and repository README use the agent-engineering identity. |
| Four clear destinations with visible concept tree | Shared header, workflow index, library task/tree/context paths and apps chooser. |
| Three complete entry workflows | Session handoff, context selection, skill maintenance with source checks and reusable next steps. |
| Enduring guides alongside dated articles | Worked-workflow shelf leads the guides/experiments archive; chronological articles stay available. |
| Focused product pages | LLMSX Explorer, Skills Explorer and GitHub Explorer; source/release and existing setup links retained. |
| Skill discoverability | Full prompt opens on direct links; prompt/install copy controls and compatibility/dependency guidance; repository remains discoverable by the skills CLI. |
| GitHub identity | Description, homepage and six relevant topics updated and read back. |
| Baseline and useful actions | Private pre-change GA4 report captured; success/failure events and voluntary outcomes added. |
| Comprehension check | Acceptance checks ask whether a reader can identify audience, promise, offerings, first workflow and tree entry. This is an agent review, not a human usability study. |

## Measurement contract

Use the existing GA4 destination. Introduce no additional visitor identifier, storage, analytics provider or account requirement.

| Event | Meaning |
|---|---|
| resource_view | A workflow, skill or application page loaded. |
| workflow_open / workflow_evidence | A workflow or supporting article link was selected. |
| skill_prompt_link / skill_prompt_open | A prompt link was selected / the full prompt disclosure actually opened. |
| artifact_copy / artifact_copy_failed | Clipboard write resolved / failed in a reusable copy block. |
| research_copy_attempt / research_copy_install_attempt | A research reference/install copy was attempted. |
| research_reference_copy_success / research_install_copy_success | The corresponding clipboard write resolved. |
| reference_open / context_download / research_download | A reference or file link was selected, not proof that a file finished downloading. |
| app_setup_open / app_guide_open | A setup or guide link was selected, not a confirmed installation. |
| workflow_outcome | A visitor voluntarily reported completed or blocked; no text/files are submitted. |

Existing nav/card/CTA events remain available. Parameters contain bounded public identifiers only. Custom event URLs omit query strings and fragments. Browser Do Not Track, Global Privacy Control and the Google disable flag suppress the site's analytics loader and custom events. Strict account routes keep their existing third-party-script exclusion. Blocked analytics must not break reading, copying or navigation. The privacy page and its machine-readable twin describe these changes.

GA enhanced measurement and cookie behavior remain Google's separate service behavior; custom event payload guarantees do not claim a new server-side privacy boundary. No credentials or prompts belong in a page URL.

Counts by eventName and pagePath work with standard GA4 dimensions. Item/kind parameters are available in event payloads; custom-dimension registration is required before treating those fields as report dimensions. They are not automatically new report dimensions.

## Baseline and comparison

Captured the existing property's previous28complete days, 2026-10-10 through2026-11-06, before deploying this change. The property reports America/Los_Angeles. Raw event and page-path reports stay outside Git in the private implementation evidence directory. The page query was limited to100rows; its row_count was151. Do not sum the returned subset as whole-site views or sum users across rows.

Historical research_copy recorded clicks. It cannot be reinterpreted as clipboard success. New successful-copy and outcome events have no equivalent historical baseline; establish their first post-deploy window before assessing change.

For a later like-for-like28-day comparison:
1. Use standard pagePath plus eventName/eventCount for the relevant public pages.
2. Compare guide/skill/reference/app progression and newVsReturning at the property level.
3. Keep copied commands, selected downloads and reported outcomes distinct from confirmed use.
4. Exclude internal acceptance traffic where possible; this implementation's browser tests intercept Google's loader/network rather than submit synthetic conversions.
5. Report counts and uncertainty at this site's scale. No arbitrary percentage improvement or causal attribution is promised.

## Verification

Local checks cover route/evidence links, app previews and setup paths, one h1 per new page, exact workflow content in twins, bounded analytics payloads, all opt-outs and a throwing analytics handler. Browser checks exercise desktop/mobile navigation, prompt disclosures, copy success/failure and optional feedback. Existing account/CSP and library tests remain required. Final delivery records identify the reviewed revision and the actual deployed acceptance result.

Current documentation consulted:
https://docs.astro.build/en/guides/client-side-scripts/
https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema

Context7 tools were unavailable in this session. Official Astro documentation and the installed modern-web guidance supplied the implementation reference. Existing dependencies were reused for verification; no local model, embedding or indexing service was started.

