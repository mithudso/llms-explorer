# AdSense value research for LLMS-Explorer

Version: 1.0.1
Date: 2026-09-30
Delta: new dossier; 34 source-backed atomic claims; baseline plus six deepening passes; follow-up raw-log and ownership-method verification.
Owner task: TASK-43, website refocus on COMP-1.

## Decision supported by the evidence

Refocus the site on helping people build useful AI workflows and reusable context. Lead with a concrete task, a worked result, and the next step. Keep the research library and tools as supporting resources. Google's own AdSense UX guidance recommends choosing one or two core strengths and prioritizing a clear next action. [User goals][S13], [Next action][S14].

The rejection does not identify a particular offending URL or prove that the site's whole corpus lacks value. The explicit policies concern valuable publisher content and added value on the screens that carry ads. A curated library can contribute value; a collection of copied material without useful curation cannot. [Low-value screens][S3], [Replicated content][S4].

These changes can address visible quality weaknesses. They cannot guarantee approval, and the code cannot manufacture sustained reader interest.

## Scope and research method

The single concept is **AdSense low value content eligibility for a tools-and-curated-knowledge site**. In scope: published AdSense eligibility, content/UX guidance, inventory-value boundaries, automation/curation exceptions, relevant Search spam guidance, and implications for this site. Out of scope: ad revenue forecasting, general SEO growth, legal rights analysis, or Google's undisclosed review classifier.

Applied the repository's `rabbithole` skill. Pass 0 established eight atomic claims. Each later pass checked the accumulated claims for mechanisms, limits, exceptions, primary wording, history, and contradictory interpretations. Only distinct facts count as new; restatements do not.

| Pass | Deepening question and evidence examined | New claims | Total | New-information rate |
| --- | --- | ---: | ---: | ---: |
| 0 | Baseline: program policies, readiness, low-value screens, replicated content, review procedure | 8 | 8 | Baseline |
| 1 | What added value changes eligibility? Manual curation, slight rewrites, rights, prominence, misleading downloads, audience requirement | 6 | 14 | 42.9% |
| 2 | What counts as publisher content? Multimedia, excluded chrome/links, ad balance, ongoing updates, similar-page consolidation, identifiable subject | 6 | 20 | 30.0% |
| 3 | Where does Search guidance stop applying? AI production method, ranking intent, purpose, authorship, disclosures, word-count myth | 6 | 26 | 23.1% |
| 4 | What changed or fails at review? Public crawler access, 2017 contextual-text rationale, truthful freshness | 3 | 29 | 10.3% |
| 5 | What does genuine interest mean? Invalid click/impression rules; searched for official numeric content/audience thresholds | 1 | 30 | 3.3% |
| 6 | Recheck exceptions and UX depth: primary AdSense guidance on core strengths, next actions, new and related work | 4 | 34 | 11.8% |

**Actual verdict: BUDGET_EXHAUSTED.** The default six-deepening-pass cap was reached. Two consecutive passes below 5% were not achieved. One or two further passes over remaining UX recommendations may add useful detail. The explicit content/value boundaries are sufficiently understood to guide implementation; this result does not claim exhaustive knowledge of Google's internal approval criteria.

No numeric minimum for posts, article length, traffic, or a mandatory waiting period emerged from the inspected official eligibility/content sources. Treat third-party recipes and Google-hosted community answers as opinion, not policy. Google's no-preferred-word-count statement belongs to Search guidance; it is not an AdSense exemption. [Eligibility][S6], [Content and UX][S8], [People-first guidance][S11].

## Countable claim ledger

“Requirement” means an explicit AdSense/Publisher rule. “Guidance” means a recommendation, not a standalone approval guarantee. Search rows concern Search and are not interchangeable with AdSense approval criteria.

| Claim | First pass | Atomic fact | Status | Source |
| --- | ---: | --- | --- | --- |
| C01 | 0 | AdSense publishers must comply with Google Publisher Policies. | requirement | [AdSense Program policies][S1] |
| C02 | 0 | AdSense readiness guidance asks for unique relevant content and a good user experience. | guidance | [AdSense readiness][S2] |
| C03 | 0 | AdSense readiness guidance asks for clear usable navigation. | guidance | [AdSense readiness][S2] |
| C04 | 0 | Google-served ads are prohibited on screens without publisher content or with low-value content. | requirement | [Low-value screens][S3] |
| C05 | 0 | Google-served ads are prohibited on screens still under construction. | requirement | [Low-value screens][S3] |
| C06 | 0 | Google-served ads are prohibited on screens primarily used for alerts, navigation, or behavioral purposes. | requirement | [Low-value screens][S3] |
| C07 | 0 | Embedded or copied material needs additional commentary, curation, or other added value to carry Google-served ads. | requirement | [Replicated content][S4] |
| C08 | 0 | Publishers can request another site review after addressing readiness problems. | procedure | [Site review][S5] |
| C09 | 1 | Google publisher examples forbid automated content without manual review or curation. | requirement | [Replicated content][S4] |
| C10 | 1 | Slightly rewriting or synonymizing copied material does not supply the required added value. | requirement | [Replicated content][S4] |
| C11 | 1 | Added curation does not waive intellectual property compliance. | requirement | [Replicated content][S4] |
| C12 | 1 | Publisher content should be the focal point of the user's screen. | guidance | [Low-value screens][S3] |
| C13 | 1 | AdSense prohibits ads mistaken for navigation or download links. | requirement | [AdSense Program policies][S1] |
| C14 | 1 | AdSense eligibility says original high-quality content must attract an audience. | requirement | [Eligibility][S6] |
| C15 | 2 | Publisher content can include images, videos, games, text, and managed user content. | definition | [Ads and publisher content][S7] |
| C16 | 2 | Whitespace, headers, footers, and links to other site content do not count as publisher content under the ads-to-content policy. | definition | [Ads and publisher content][S7] |
| C17 | 2 | Google-served ads cannot appear on screens with more ads or paid promotion than publisher content. | requirement | [Ads and publisher content][S7] |
| C18 | 2 | AdSense content guidance recommends regular updates that add unique content and give users reasons to return. | guidance | [Content and UX][S8] |
| C19 | 2 | AdSense content guidance recommends expanding or consolidating very similar pages. | guidance | [Content and UX][S8] |
| C20 | 2 | AdSense content guidance says unique page content must make the site's subject identifiable. | guidance | [Content and UX][S8] |
| C21 | 3 | Search scaled-content abuse targets mass content made primarily to manipulate rankings rather than help users, regardless of production method. | search-policy | [Search spam policies][S9] |
| C22 | 3 | Google Search does not treat all AI or automated content as spam. | search-guidance | [Search and AI][S10] |
| C23 | 3 | Search people-first self-assessment asks whether a site has a primary purpose and helps its intended audience achieve a goal. | search-guidance | [People-first guidance][S11] |
| C24 | 3 | Google Search explicitly says it has no preferred word count. | search-guidance | [People-first guidance][S11] |
| C25 | 3 | Search people-first guidance encourages accurate authorship and evidence of experience. | search-guidance | [People-first guidance][S11] |
| C26 | 3 | Search guidance recommends explaining substantial automation when readers would reasonably expect to know how content was created. | search-guidance | [People-first guidance][S11] |
| C27 | 4 | AdSense's readiness checks require a live site accessible without a password and without blocking its crawler. | procedure | [Site review][S5] |
| C28 | 4 | The 2017 AdSense insufficient-content article says text helps reviewers and contextual ad crawlers determine a page's topic. | historical-guidance | [2017 insufficient content][S12] |
| C29 | 4 | Search guidance warns against changing dates to imply freshness when content has not materially changed. | search-guidance | [People-first guidance][S11] |
| C30 | 5 | AdSense requires genuine interest in ad clicks and prohibits artificially inflating clicks or impressions. | requirement | [AdSense Program policies][S1] |
| C31 | 6 | AdSense UX guidance recommends focusing the site's core offering on one or two strengths. | guidance | [User goals][S13] |
| C32 | 6 | AdSense UX guidance recommends a clear next action and warns against cluttering a page with too many actions. | guidance | [Next action][S14] |
| C33 | 6 | AdSense audience guidance recommends showcasing new high-quality content on top landing pages. | guidance | [Returning users][S15] |
| C34 | 6 | AdSense audience guidance recommends linking related content on the same subject to encourage engagement. | guidance | [Returning users][S15] |

## Mechanism, history, and limits

AdSense content guidance asks for enough original page content to understand the site and give readers a reason to return. Its readiness checks also require public crawler access. Added curation must produce a useful result for readers rather than merely alter copied wording. [Content and UX][S8], [Site review][S5], [Replicated content][S4].

The 2017 insufficient-content article explains why readable text helps contextual review. Current Publisher policies also recognize multimedia and games as content. These sources do not support a universal “tools sites are forbidden” rule. A tool's working interface, explanation, sample result, limitations, and substantive page content still need assessment. [2017 insufficient content][S12], [Ads and publisher content][S7].

There is no contradiction between Search accepting useful AI-assisted content and Publisher policy rejecting unreviewed automatically generated material. The programs state different rules. Search focuses on ranking-manipulation intent; Publisher inventory policy explicitly mentions manual review or curation. A successful Search ranking would not itself establish AdSense eligibility. [Search and AI][S10], [Search spam policies][S9], [Replicated content][S4].

The inspected official sources do not disclose a page-specific explanation for this rejection, a numeric “unique value” score, or an approval formula. Do not translate linter grades, fact counts, traffic aspirations, or a redesigned homepage into an approval promise.

## Live observations and implications

Both [llmsx.org](https://llmsx.org/) and [llms-explorer.com](https://llms-explorer.com/) returned the same homepage text in this audit. It begins with an agent-oriented promise and corpus counts, then mixes tools, memory claims, indexes, a directory, a rubric, recipes, and a blog. **Inference:** a new reader must understand the system's internal categories before choosing a useful action. This is a usability finding, not proof of Google's reason for rejection.

The [directory](https://llmsx.org/directory/) and its [Plain entry](https://llmsx.org/directory/plain.com__docs/) explain the scoring scope, exclusions, findings, and source links. They explicitly say the mirrored text is not republished. Preserve this original analysis. A grammar grade describes the disclosed rubric; it does not establish factual correctness or AdSense readiness.

The [retrieval decision table](https://llmsx.org/examples/decision-table/) provides specific question-to-method choices and distinguishes measured from estimated costs. It is a useful candidate for a guided reader journey after checking its runnable examples and current commands.

The featured [local model performance post](https://llmsx.org/blog/local-model-performance-evaluation-mlx-egpu/) labels several throughput ranges empirical. Its shown harness output measures `Qwen2-beta-14B-Chat`, while highlighted ranges concern different models/hardware. The visible page does not establish that the displayed run supports those ranges. This is an evidence gap; this audit has not proven the figures false. Require matching logs, models, hardware, methodology, and reproducible results before featuring it as firsthand benchmarking.

Repository spot check before this refocus: `site/src/layouts/Base.astro` loaded the AdSense script independently of its `noindex` prop. `site/tools/build_sitemap.py` excludes noindex and canonical aliases. **Inference:** search exclusion alone does not control which screens inherit monetization. Define explicit page-level ad eligibility and assess those pages against inventory rules. Do not assume a noindex page is automatically safe for ads.

### Follow-up verification outside the counted depth passes

A narrow repository search for the exact throughput ranges and model labels found no matching raw runs for the featured blog's 15.5–17.2, 42–45, or 85–92 tokens/sec claims. The relevant JSON artifact, `docs/verification/local-ollama-dr-2026-09-30/tool-benchmark-official.json`, instead records `qwen3.6:35b-mlx` at 74.66 decode tokens/sec in an Atlas evidence tool test. `mlx-manifests.json` records model artifact sizes and digests. Neither establishes the blog's advertised cross-platform runs. This is a bounded evidence search, not proof that no historical run exists elsewhere.

Google's connection instructions explicitly offer a meta-tag verification method for publishers who do not want the AdSense code snippet on their homepage. Put `<meta name="google-adsense-account" content="ca-pub-1706083044457708">` in the head, using the site's existing publisher ID. This supports preserving ownership identification while defaulting ad loading off until pages are assessed. The publisher must confirm the chosen method and verification status in AdSense when requesting review. [Connect your site to AdSense](https://support.google.com/adsense/answer/7584263?hl=en).

## Recommended implementation and remaining work

1. **State one reader promise.** Organize the homepage around a small number of outcomes: learn a practical workflow, apply a skill or tool, and find supporting research. Keep advanced indexes reachable through the library and footer. Feature a completed example before corpus-size statistics.
2. **Show the work.** On featured guides show the actual input, result, method, sources, limitations, author/editor, and changes that matter. Report measurements only when the underlying run exists. Show AI assistance accurately where a reader would reasonably expect a creation-method explanation. [People-first guidance][S11].
3. **Turn the library into useful choices.** Curate entry points with “use this when,” useful comparisons, and links to the original source. Consolidate similar landing pages when they answer the same question. Keep raw files available for agents; explain their provenance and limits.
4. **Make tools understandable before installation.** Give each download a task, screenshot or sample result, supported platform, tested installation path, documentation, source, and limitations. Preserve the already verified GitHub Explorer and Skills Explorer distributions.
5. **Keep monetization scoped.** Do not run Google ads on blank, under-construction, error, pure navigation, or uncurated replicated screens. Start with a conservative set of original editorial pages that have been individually reviewed. Ownership verification and ad-serving configuration require separate checks. [Low-value screens][S3], [Replicated content][S4].
6. **Record real maintenance and interest.** Keep correction channels visible. Feature genuine new work and relevant next articles. Inspect actual analytics for completed reader actions and returning readers; do not invent testimonials, audience numbers, review dates, or targets presented as Google's thresholds. [Returning users][S15].
7. **Review the deployed site before resubmission.** Verify both domain behavior, canonicals, public access, accurate links, mobile use, and the pages proposed for ads. Request review in AdSense only after the changes and content assessment are live. [Site review][S5].

The visual/navigation refocus can ship now. The corpus still needs a page-by-page originality, evidence, curation, and publication-readiness pass. Verify the featured benchmark's raw evidence before promoting it. Genuine audience interest requires observed reader behavior over time; this session has no analytics evidence establishing it.

## Project continuity

Direct Stele reads found:

- [KNOW-31, verified GitHub Explorer release links](https://app.stele-ai.dev/p/llms-explorer-9d1wd/nodes/KNOW-31): preserve working tap, release and npm distributions plus the concurrent Skills Explorer section.
- [KNOW-44, truthful website refocus](https://app.stele-ai.dev/p/llms-explorer-9d1wd/nodes/KNOW-44): organize around reader tasks and avoid invented approval/evidence claims.
- [TASK-43, current website refocus](https://app.stele-ai.dev/p/llms-explorer-9d1wd/nodes/TASK-43): lifecycle owner for this dossier and implementation.
- [TASK-35, local model research qualification](https://app.stele-ai.dev/p/llms-explorer-9d1wd/nodes/TASK-35) and [TASK-15, plugin evaluation/Zotero](https://app.stele-ai.dev/p/llms-explorer-9d1wd/nodes/TASK-15): unrelated work remains in progress.

Historical Codex memory pointed to the sitemap and canonical workflow. The repository spot check above verified the relevant current behavior; the older deployment counts were not reused as current facts.

Adjacent topics surfaced but not researched here: consent/ad implementation, analytics task instrumentation, evidence validation for the benchmark corpus, and longer-term audience development.

[S1]: https://support.google.com/adsense/answer/48182?hl=en "AdSense Program policies"
[S2]: https://support.google.com/adsense/answer/7299563?hl=en "AdSense readiness"
[S3]: https://support.google.com/publisherpolicies/answer/11112688?hl=en "Low-value screens"
[S4]: https://support.google.com/publisherpolicies/answer/11190248?hl=en "Replicated content"
[S5]: https://support.google.com/adsense/answer/12176698?hl=en "Site review"
[S6]: https://support.google.com/adsense/answer/9724?hl=en "Eligibility"
[S7]: https://support.google.com/publisherpolicies/answer/11169917?hl=en "Ads and publisher content"
[S8]: https://support.google.com/adsense/answer/10015918?hl=en "Content and UX"
[S9]: https://developers.google.com/search/docs/essentials/spam-policies "Search spam policies"
[S10]: https://developers.google.com/search/blog/2023/02/google-search-and-ai-content "Search and AI"
[S11]: https://developers.google.com/search/docs/fundamentals/creating-helpful-content "People-first guidance"
[S12]: https://blog.google/products/adsense/how-to-address-insufficient-content/ "2017 insufficient content"
[S13]: https://support.google.com/adsense/answer/2892971?hl=en "User goals"
[S14]: https://support.google.com/adsense/answer/2893021?hl=en "Next action"
[S15]: https://support.google.com/adsense/answer/2893023?hl=en "Returning users"
