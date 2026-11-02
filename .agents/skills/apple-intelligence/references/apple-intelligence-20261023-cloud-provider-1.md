<!-- hub-reference-banner -->
> **Reference file — part of the `apple-intelligence` hub.** Created by `/dr` deep research 2026-10-23; research dir `~/.global-ai-hub/research/apple-intelligence-20261023-cloud-provider-1`.

---
name: apple-intelligence-20261023-cloud-provider-1
description: "Explain Private Cloud Compute expansion to Google Cloud and NVIDIA; Foundation Models PCC eligibility quotas and migration; Foundation Models provider interoperability and release status; Foundation Models adapter lifecycle across OS releases. TRIGGER: Apple Intelligence. SKIP: unrelated topics."
version: "1.0.0"
updated: "2026-10-23"
category: "research"
keywords: ["Apple Intelligence", "Foundation Models", "privacy", "availability", "developer integration", "research", "evidence", "limitations", "verification"]
tags: ["dr"]
provenance: "/dr · ~/.global-ai-hub/research/apple-intelligence-20261023-cloud-provider-1"
---

# Apple Intelligence — cloud-provider-1

## Overview

Apple’s 2026 expansion runs selected Apple Intelligence inference on Google Cloud, adding Intel TDX CPUs, NVIDIA Confidential Computing GPUs, and Google Titan to PCC’s trust chain. Apple says the five original privacy requirements remain and describes added safeguards across firmware, host and guest software, request parsing, worker lifetimes, key isolation, hardware inventory, and attestation roots. These are provider commitments. Apple’s existing PCC transparency docs describe a public release log, binary publications, and a Virtual Research Environment. Apple and Google also announced an open-source host stack, while Apple’s Google Cloud binaries, research tools, and live-node access were future commitments in June. As of 2026-10-23, Apple release notes call the deployment a beta preview and say pccvre cannot parse its attestations. Independent work reports risks in underlying TDX and GPU attestation designs but does not establish a compromise of Apple’s deployment.

Foundation Models can route app sessions to Apple’s PCC server model, but developer eligibility and end-user quotas are separate gates. Apple’s dedicated access page requires Small Business Program membership, a first-time-download threshold, and an assigned managed entitlement; it permits App Store release and TestFlight or ad hoc testing, with a six-month migration window after specified eligibility losses. The app-facing API is available on OS 27 platforms and depends on Apple Intelligence device and region support plus network access. Apple exposes per-person daily quota states, reset information, and an iCloud+ upgrade path, but no fixed request count. Earlier reports differ about iCloud+ quota boosts, and Apple’s download-count wording does not settle whether the threshold is per app or account-wide. Reports about the fm CLI are separate from native framework API eligibility.

Apple's Foundation Models exposes provider interoperability through a public Swift LanguageModel protocol. A provider declares capabilities and executor configuration; its executor translates Foundation Models transcripts and options into provider requests. Apple's current support page links Claude and Gemini, but their release paths and maturity differ: Anthropic has a dedicated Claude package with dated GitHub releases and a repository Beta label, while Google provides GeminiLanguageModel through Firebase AI Logic, which remains in public preview. Apple also ships an experimental Chat Completions utility, and independent packages expose OpenAI APIs. These findings establish protocol and wire-format compatibility, not an OpenAI-owned Foundation Models provider.

Apple's custom Foundation Models adapter path was tied to system-model versions: each adapter targeted one version, so supporting multiple versions required separate compatible artifacts and per-version evaluation. Apple's current toolkit matrix ends at version 26.0.0, lists it for the OS 26 family, and says it is incompatible with OS 27 and later. Apple staff also confirmed that custom adapters are unsupported as of OS 27. For OS 26 deployments, Apple says an Account Holder must request the adapter entitlement; local training and testing do not need it. One developer later reported that the request page said Apple was no longer accepting requests, but Apple's current training page does not state whether new requests are accepted. Public evidence also leaves open what happens when an app built against OS 26 runs on a device upgraded to OS 27, so that runtime behavior should not be assumed.

## Core Concepts

### Private Cloud Compute expansion to Google Cloud and NVIDIA

- Apple announced a Google Cloud expansion for selected high-demand Apple Intelligence workloads using Intel TDX CPUs, NVIDIA Confidential Computing GPUs, and Google’s Titan chip; Google identifies NVIDIA Blackwell GPUs in the Google Cloud platform, and NVIDIA independently confirms Blackwell Confidential Computing for PCC inference there. verified-as-of: 2026-06-11[^c1-2][^c1-3][^c1-4][^c1-1]
- Apple says the Google Cloud extension retains PCC’s five core requirements: stateless computation, enforceable guarantees, no privileged runtime access, non-targetability, and verifiable transparency. Apple also says the Google Cloud trusted computing base includes firmware, host and guest operating systems, and application code.[^c1-1][^c1-2][^c1-3]

### Foundation Models PCC eligibility quotas and migration

- As of 2026-10-09, Apple lists three PCC eligibility conditions: enrollment in the App Store Small Business Program, fewer than 2 million first-time App Store downloads from any of the developer's apps, and Apple's assignment of the Private Cloud Compute entitlement to the developer account. Eligible developers incur no PCC cloud API cost. verified-as-of: 2026-10-09[^c2-1][^c2-9][^c2-10][^c2-5]
- Apple allows eligible PCC apps to ship through the App Store where Apple Intelligence is available and to be tested through TestFlight or ad hoc distribution; installs through those test channels do not count as first-time App Store downloads. verified-as-of: 2026-10-09[^c2-1][^c2-10][^c2-5]
- Apple says it will notify a developer and require migration to an alternative solution within six months if any app later exceeds the 2 million first-time-download threshold or the developer leaves the App Store Small Business Program; first-time download information is available in App Store Connect Analytics. verified-as-of: 2026-10-09[^c2-1][^c2-10][^c2-5]
- The app-facing PCC model has a separate daily per-person request quota. Apple’s Foundation Models guide exposes below-limit, approaching-limit, and limit-reached states, a reset date when known, and a system UI suggestion to subscribe to iCloud+ for more access; the guide does not publish a numeric daily allowance. verified-as-of: 2026-08-06[^c2-2][^c2-8][^c2-7]
- PCC applies a daily request allowance per user, and Apple says an iCloud+ subscription can provide more access; this is a user quota, separate from the eligible developer's no-cloud-API-cost arrangement. verified-as-of: 2026-10-09[^c2-2][^c2-1][^c2-10]
- Apple's public developer material describes daily PCC limits but gives no fixed requests-per-user number; it says limits can vary by feature, request complexity, system demand, system policy, and other factors. Apple mentions future fee-based expanded access but publishes no price or timing, so developers should not plan around an assumed numeric quota or paid-access offer. (two sources) verified-as-of: 2026-10-09[^c2-1][^c2-2][^c2-10]
- Apple documents PrivateCloudComputeLanguageModel in Foundation Models for iOS, iPadOS, Mac Catalyst, macOS, visionOS, and watchOS 27 or later. The API reports unavailable states such as deviceNotEligible and systemNotReady; using PCC also requires a supported Apple Intelligence device and region and a network connection. verified-as-of: 2026-10-13[^c2-3][^c2-2][^c2-10]

### Foundation Models provider interoperability and release status

- Apple's public LanguageModel protocol describes model capabilities and executor configuration. A LanguageModelExecutor translates Foundation Models transcript entries and request options into provider-native requests, then streams results to LanguageModelSession. Apps add provider packages with Swift Package Manager and initialize the same LanguageModelSession(model:) API.[^c3-1][^c3-3][^c3-4]
- Apple's developer overview lists Claude and Gemini under supported third-party models and says any provider can publish a Swift package conforming to LanguageModel. This is the framework's stated provider surface, not a closed list of hard-coded endpoints. verified-as-of: 2026-10-05[^c3-4][^c3-2]
- Anthropic's ClaudeForFoundationModels package conforms Claude to Apple's LanguageModel protocol and uses LanguageModelSession; its README labels the package beta, while the repository's latest tagged release is v0.2.3 dated October 7, 2026. verified-as-of: 2026-10-23[^c3-6][^c3-7][^c3-1][^c3-8]
- The ClaudeForFoundationModels README labels the integration Beta and says it targets the OS 27 server-side language-model API introduced in OS betas, with APIs subject to change before general availability. (two sources) verified-as-of: 2026-10-23[^c3-6][^c3-7]
- Google's GeminiLanguageModel is distributed through Firebase AI Logic. Firebase release notes say Firebase 12.19.0 added it as a public preview on 2026-09-09; Firebase 13.0.0 notes direct use through ai.geminiLanguageModel(name:). The guide's 2026-10-20 revision still calls the integration Preview and lists iOS and macOS as the initial supported platforms. verified-as-of: 2026-10-20[^c3-9][^c3-10][^c3-11]
- Apple's Foundation Models Utilities package exposes ChatCompletionsLanguageModel for any server that implements the Chat Completions REST API. Hugging Face separately documents OpenAI Chat Completions and Responses support in AnyLanguageModel. This supports API-level compatibility, but it does not establish an OpenAI-owned LanguageModel provider; Apple's support overview names Claude and Gemini as its supported third-party models. This last distinction is an inference from the cited package descriptions and support list. (two sources) verified-as-of: 2026-10-23[^c3-5][^c3-13][^c3-4]
- Firebase announced its Gemini adapter as a preview on June 9, 2026. Its launch post instructed developers to use the Firebase Apple SDK branch wwdc26-preview during the preview. verified-as-of: 2026-06-09[^c3-11][^c3-10]
- Firebase's guide, last updated October 20, 2026, labels the integration Preview, says it has no SLA or deprecation policy and could change in backwards-incompatible ways, and lists iOS and macOS as the initial supported platforms. Its prerequisites require Xcode 27 from the Mac App Store and an Apple platform simulator or physical device running the corresponding OS version, for example iOS 27. verified-as-of: 2026-10-23[^c3-10][^c3-9]
- Firebase's October 7, 2026 SDK 13.0.0 release notes remove its interim GenerativeModelSession, SystemLanguageModel, and HybridModel bridge types and direct developers to use GeminiLanguageModel through Apple's native framework. verified-as-of: 2026-10-07[^c3-9][^c3-10]

### Foundation Models adapter lifecycle across OS releases

- Each custom adapter is compatible with one specific system-model version. Apple says developers supporting devices with different system-model versions need a different adapter for each version; the toolkit versions include the matching model assets. verified-as-of: 2026-10-05[^c4-1][^c4-3][^c4-5]
- Apple's adapter page lists beta toolkit versions 0.1.0 and 0.2.0 as removed, identifies 26.0.0 as the last release, lists OS 26 compatibility, and explicitly says the toolkit is incompatible with OS 27 and later. verified-as-of: 2026-10-05[^c4-1][^c4-5]
- Apple staff confirmed in June and July 2026 Developer Forums replies that custom adapters are no longer supported as of OS 27. A Frameworks Engineer pointed developers to the on-device base models or their own Core ML or Core AI models, and said Background Assets remains available for delivering custom models. verified-as-of: 2026-10-05[^c4-2][^c4-3][^c4-1]

## Tools & Frameworks

- Tentative: Google says Apple and Google engineered an open-source host stack to support PCC transparency. Google’s June 2026 post announces the stack but does not identify a repository or code artifact.[^c1-3] _(Private Cloud Compute expansion to Google Cloud and NVIDIA)_
- Hugging Face announced AnyLanguageModel 1.0 on October 20, 2026; the repository lists v1.1.0, released October 22, as latest on October 23. The package documents OpenAI Chat Completions and Responses APIs, Anthropic Messages, Gemini, and Open Responses-compatible endpoints as integrations in its own cross-provider implementation. verified-as-of: 2026-10-23[^c3-13][^c3-12] _(Foundation Models provider interoperability and release status)_
- Apple's current training page says the Apple Developer Program Account Holder must request the adapter entitlement to deploy adapters; the entitlement is not required for local training or testing, and toolkit downloads require program membership and acceptance of toolkit terms. A developer's 2026 post reports that the request page said Apple was no longer accepting requests, so the page does not establish whether requests are currently open. (two sources) verified-as-of: 2026-10-23[^c4-1][^c4-7] _(Foundation Models adapter lifecycle across OS releases)_

## Methodology

- Apple’s existing PCC transparency documentation describes a public append-only release log, binary publication, research tools, and a Virtual Research Environment. Apple’s June 2026 expansion post says Google Cloud binaries, public research tooling, and live-node access will be provided; it presents these as commitments. (two sources)[^c1-5][^c1-1][^c1-2] _(Private Cloud Compute expansion to Google Cloud and NVIDIA)_
- As of 2026-10-23, Apple’s release notes describe PCC on Google Cloud as a preview serving some requests from iOS and macOS 27 beta systems. The notes say pccvre does not yet parse Google Cloud attestations and that support will arrive with the public security research program. verified-as-of: 2026-10-23[^c1-6][^c1-2] _(Private Cloud Compute expansion to Google Cloud and NVIDIA)_
- TEE.fail researchers report extracting Intel TDX attestation keys with a physical DDR5 interposer and using extracted keys to compromise NVIDIA GPU Confidential Computing attestation in tested configurations. Apple says its Google Cloud PCC uses TDX and NVIDIA Confidential Computing, but the TEE.fail work does not evaluate PCC on Google Cloud; it is evidence of component-level risk, not a demonstrated PCC compromise. (two sources)[^c1-7][^c1-2][^c1-9] _(Private Cloud Compute expansion to Google Cloud and NVIDIA)_
- A May 22, 2026 independent study of the pre-expansion PCC reported that published binaries lacked reproducible builds and symbols. Because the study predates Apple’s June Google Cloud announcement, it does not establish whether the Google Cloud binaries have the same properties.[^c1-8][^c1-2] _(Private Cloud Compute expansion to Google Cloud and NVIDIA)_
- Apple’s general Release Transparency documentation describes client verification of attested software measurements against an append-only public log and publication of firmware and user-space binaries for inspection. Apple’s current release notes say pccvre does not yet parse Google Cloud attestations or transparency-log releases, with support planned for the public security research program. verified-as-of: 2026-10-23[^c1-5][^c1-6] _(Private Cloud Compute expansion to Google Cloud and NVIDIA)_
- Apple’s June announcement commits to publishing Google Cloud binaries, research tooling, and access to live PCC nodes in research mode. As of 2026-10-23, Apple’s release notes still describe the Google Cloud deployment as a preview serving some requests from beta operating systems and say the public security research program is forthcoming; these statements do not report a completed public end-to-end assessment. (two sources) verified-as-of: 2026-10-23[^c1-2][^c1-6] _(Private Cloud Compute expansion to Google Cloud and NVIDIA)_
- Apple documents PrivateCloudComputeLanguageModel for iOS and iPadOS 27, Mac Catalyst 27, macOS 27, visionOS 27, and watchOS 27 or later; the Foundation Models guide recommends availability checks and using an on-device model on earlier OS releases. verified-as-of: 2026-10-13[^c2-3][^c2-2][^c2-7] _(Foundation Models PCC eligibility quotas and migration)_
- Apple recommends evaluating adapters with a use-case-specific process for each model version, using quantitative and qualitative checks and evaluating safety. Its guide also says to host the roughly 160 MB adapter as a Background Assets download instead of bundling all version variants in the app. verified-as-of: 2026-10-05[^c4-1][^c4-5] _(Foundation Models adapter lifecycle across OS releases)_

## Practical Patterns

- Apple describes additional Google Cloud controls: a cryptographically verifiable append-only ledger of PCC fleet hardware; at least two independent vendor roots of trust for sensitive components; request parsing in a dedicated process and namespace; short-lived shared inference software; and attested keys in a separate confidential VM isolated from external inputs.[^c1-2][^c1-3] _(Private Cloud Compute expansion to Google Cloud and NVIDIA)_
- The Foundation Models API exposes PCC quota state through quotaUsage, including approaching and reached states, and a limitIncreaseSuggestion that can show Apple's system upgrade UI. Exhaustion raises quotaLimitReached; resetDate identifies the quota refresh when known, and Xcode schemes can simulate approaching or reached limits for testing. verified-as-of: 2026-08-06[^c2-2][^c2-3][^c2-10] _(Foundation Models PCC eligibility quotas and migration)_
- Protocol conformance alone does not establish feature parity. Apple exposes provider-declared capabilities, while Firebase's current integration guide lists supported Gemini models, says Gemini Live API is unsupported, and documents only iOS and macOS for this integration. verified-as-of: 2026-10-23[^c3-1][^c3-10] _(Foundation Models provider interoperability and release status)_
- Tentative: A third-party client issue opened in July 2026 treated .fmadapter files as version-locked and proposed a clear startup error if an OS update swaps the base model. The issue was a deferred and closed proposal, not an implementation test, so it records a developer's maintenance concern but does not verify runtime behavior. verified-as-of: 2026-10-23[^c4-6] _(Foundation Models adapter lifecycle across OS releases)_

## Anti-Patterns

_(none recorded)_

## Troubleshooting

- Runtime PCC availability depends on Apple Intelligence support for the device and region and on service readiness; Apple exposes deviceNotEligible and systemNotReady states, requires a network connection, and recommends an on-device fallback when PCC cannot serve a request. An iOS 27 app example implements availability and quota fallback. Although its prose also describes offline fallback, its shown response handler retries only quotaLimitReached and rethrows other errors. verified-as-of: 2026-10-23[^c2-3][^c2-2][^c2-7] _(Foundation Models PCC eligibility quotas and migration)_
- A Daring Fireball entry dated 2026-07-12 reports a third-party macOS wrapper that invokes the fm command-line tool to reach PCC without the app-facing entitlement and says it cannot run in sandboxed Mac App Store apps; this CLI report does not establish that native PrivateCloudComputeLanguageModel calls bypass Apple’s managed-entitlement requirement. (two sources) verified-as-of: 2026-07-12[^c2-6][^c2-1] _(Foundation Models PCC eligibility quotas and migration)_
- The cited public material does not establish whether an adapter call from an app built against OS 26 continues to work after a device upgrades to OS 27, throws, or degrades silently. An independent migration guide marks this legacy-binary runtime behavior untested; Apple's page states that the adapter training toolkit is incompatible with OS 27 and later. (two sources) verified-as-of: 2026-10-10[^c4-1][^c4-5] _(Foundation Models adapter lifecycle across OS releases)_
- Tentative: In a June 2026 asset-pack troubleshooting thread, an Apple Frameworks Engineer said an on-demand Background Asset must be made local with ensureLocalAvailability(of:requireLatestVersion:) before constructing SystemLanguageModel.Adapter(name:). The original poster later said the error persisted after following that advice, so the thread does not confirm a complete fix.[^c4-2] _(Foundation Models adapter lifecycle across OS releases)_
- Tentative: A 2025 forum report that initially described a toolkit v0.2.0 load failure as a base-model incompatibility was later resolved by an Apple Frameworks Engineer as an invalid adapter identifier: a hyphenated name failed validation, and changing it to an underscore worked. That report is not evidence that the OS had changed the adapter's base model.[^c4-4] _(Foundation Models adapter lifecycle across OS releases)_

## Disagreements & Open Questions

- Open (Private Cloud Compute expansion to Google Cloud and NVIDIA): Has Apple launched the public PCC-on-Google-Cloud research program and updated pccvre to parse Google Cloud attestations after the 2026-10-23 release notes?
- Open (Private Cloud Compute expansion to Google Cloud and NVIDIA): Where is the Apple-Google open-source host stack published, and which measured host components does it include?
- Open (Private Cloud Compute expansion to Google Cloud and NVIDIA): How does Apple map the two independent vendor roots of trust to specific Google Cloud components and bind GPU attestation to the CPU and VM attestation?
- Open (Private Cloud Compute expansion to Google Cloud and NVIDIA): Has an independent evaluator tested the combined Apple, Google, Intel, and NVIDIA attestation and transparency chain against physical-access and attestation-relay attacks?
- Open (Private Cloud Compute expansion to Google Cloud and NVIDIA): Has Apple published support for Google Cloud attestations in pccvre and opened the announced live-node research program since the October 23, 2026 release-notes snapshot?
- Open (Private Cloud Compute expansion to Google Cloud and NVIDIA): Has an independent evaluator tested whether PCC’s added host-stack controls, hardware ledger, and separate trust roots resist physical interposer and attestation-relay attacks in the actual Google Cloud deployment?
- Disagreement (Foundation Models PCC eligibility quotas and migration): WWDC26 session 241 summarizes no-cost developer access as available below the 2 million first-time-download threshold, while Apple’s dedicated PCC access page also requires App Store Small Business Program membership and an account-assigned managed entitlement. The dedicated access page is the explicit eligibility rule.[^c2-4][^c2-1]
- Disagreement (Foundation Models PCC eligibility quotas and migration): Daring Fireball’s 2026-06-13 article says iCloud+ subscribers did not receive extra PCC quota in third-party apps; Apple’s Foundation Models guide, last modified 2026-08-06, says a person can subscribe to iCloud+ for more access. The later official guide describes the current user-quota upgrade path.[^c2-5][^c2-2]
- Disagreement (Foundation Models PCC eligibility quotas and migration): Apple describes eligibility using first-time downloads from any of a developer's apps and says the migration trigger occurs if any app crosses the threshold. X2 Labs summarizes the threshold as downloads across all apps. Apple does not define the aggregation rule on its public page, so per-app versus account-wide counting remains unclear.[^c2-1][^c2-10]
- Open (Foundation Models PCC eligibility quotas and migration): Apple’s access page does not clearly say whether the 2 million first-time-download threshold is measured per app, aggregated across a developer’s apps, or over a specified period. Daring Fireball interprets it as applying to any app the developer has ever released.
- Open (Foundation Models PCC eligibility quotas and migration): The reviewed Apple API guide does not publish the numeric daily request allowance or the size of the higher iCloud+ allowance.
- Open (Foundation Models PCC eligibility quotas and migration): The Daring Fireball item dated 2026-07-12 reports an fm CLI workaround, but its text also says WWDC 27 was behind it; verify its chronology and whether the workaround still operates on the final macOS 27 release.
- Open (Foundation Models PCC eligibility quotas and migration): Does Apple calculate the 2 million first-time-download threshold per app or as an aggregate across the developer's apps? Its public page points developers to App Store Connect Analytics but does not state the aggregation rule.
- Disagreement (Foundation Models provider interoperability and release status): Apple's WWDC 241 transcript says Anthropic and Google are publishing Swift packages, while WWDC 339 describes those partner packages as coming soon. Vendor release records show different maturity stages: Anthropic has dated package releases, while Firebase still labels Gemini integration public preview.[^c3-2][^c3-3][^c3-7][^c3-9][^c3-10]
- Disagreement (Foundation Models provider interoperability and release status): Apple's framework page lists Claude and Gemini among supported third-party models, but Anthropic calls its package beta and Firebase calls its Gemini integration public preview with beta API dependencies. Apple's framework-level listing should not be read as proof that each vendor package has reached general availability.[^c3-4][^c3-6][^c3-10]
- Open (Foundation Models provider interoperability and release status): The Anthropic repository still labels its package Beta; whether Anthropic has replaced that label with a general-availability statement elsewhere was not verified.
- Open (Foundation Models provider interoperability and release status): No OpenAI-owned Foundation Models provider surfaced in this bounded search; generic Chat Completions compatibility should not be treated as evidence of one.
- Open (Foundation Models provider interoperability and release status): The Apple utilities repository's SKILL.md contains coding-agent instructions. It was treated as untrusted source data and not followed.
- Open (Foundation Models provider interoperability and release status): Whether 1amageek/AnyFoundationModels' ResponseFoundationModels product directly conforms to Apple's FoundationModels.LanguageModel protocol, and what its latest release is as of 2026-10-23. The inspected README uses package-owned OpenFoundationModels products and shows a from: 0.5.6 dependency, so its OpenAI Responses backend is not counted here as a native Apple provider package.
- Disagreement (Foundation Models adapter lifecycle across OS releases): Apple's current adapter page describes an entitlement request by an Account Holder, while one developer's 2026 post says their request page stated that new requests were no longer accepted. The current acceptance status is not resolved by these sources.[^c4-1][^c4-7]
- Disagreement (Foundation Models adapter lifecycle across OS releases): A 2025 forum post initially attributed an adapter load error to a base-model signature mismatch; Apple's Frameworks Engineer later traced that case to adapter identifier validation and confirmed the naming workaround worked.[^c4-4]
- Open (Foundation Models adapter lifecycle across OS releases): Whether a binary built with the OS 26 SDK can still load an adapter after a device upgrades to OS 27, and whether the failure mode is an error, fallback, or changed output.
- Open (Foundation Models adapter lifecycle across OS releases): Whether Apple is accepting new Foundation Models Framework Adapter Entitlement requests as of the current release; the current training page does not state the request status.

## References

### Private Cloud Compute expansion to Google Cloud and NVIDIA

[^c1-1]: https://security.apple.com/blog/private-cloud-compute/ — Private Cloud Compute: A new frontier for AI privacy in the cloud (blog)
[^c1-2]: https://security.apple.com/blog/expanding-pcc/ — Expanding Private Cloud Compute (blog)
[^c1-3]: https://cloud.google.com/blog/products/identity-security/powering-the-next-era-of-confidential-ai — Powering the next era of Confidential AI (blog)
[^c1-4]: https://blogs.nvidia.com/blog/nvidia-confidential-computing-apple-private-cloud-compute/ — NVIDIA Confidential Computing to Help Expand Apple’s Private Cloud Compute (blog)
[^c1-5]: https://security.apple.com/documentation/private-cloud-compute/releasetransparency — Release Transparency (docs)
[^c1-6]: https://security.apple.com/documentation/private-cloud-compute/releasenotes/ — Release Notes (docs)
[^c1-7]: https://tee.fail/ — TEE.fail: Breaking Trusted Execution Environments via DDR5 Memory Bus Interposition (paper)
[^c1-8]: https://arxiv.org/abs/2605.24239 — Unlocking Apple's Private Cloud Compute: An Analysis of Privacy-Preserving Artificial Intelligence (paper)
[^c1-9]: https://consortiumforverifiedcomputing.org/atlas/apple-private-cloud-compute — Apple Private Cloud Compute research atlas (blog)

### Foundation Models PCC eligibility quotas and migration

[^c2-1]: https://developer.apple.com/private-cloud-compute/ — Accessing Private Cloud Compute (docs)
[^c2-2]: https://developer.apple.com/tutorials/data/documentation/foundationmodels/adding-server-side-intelligence-with-private-cloud-compute.md — Adding server-side intelligence with Private Cloud Compute (docs)
[^c2-3]: https://developer.apple.com/tutorials/data/documentation/foundationmodels/privatecloudcomputelanguagemodel.md — PrivateCloudComputeLanguageModel (docs)
[^c2-4]: https://developer.apple.com/videos/play/wwdc2026/241/ — What’s new in the Foundation Models framework - WWDC26 (docs)
[^c2-5]: https://daringfireball.net/linked/2026/06/13/pcc-severely-limited-third-party-developers — Apple’s Private Cloud Compute Is Severely Limited for Third-Party Developers (blog)
[^c2-6]: https://daringfireball.net/linked/2026/07/12/ — Daring Fireball Linked List: July 12, 2026 (blog)
[^c2-7]: https://www.ioscoffeebreak.com/issue/issue78 — Sending Long Issues Through Private Cloud Compute (blog)
[^c2-8]: https://github.com/kylebegeman/swift-lm/blob/master/docs/02-foundation-models-reference.md — SwiftLM Foundation Models reference (repo)
[^c2-9]: https://techcrunch.com/2026/06/08/apple-bets-cheaper-ai-will-woo-small-developers/ — Apple bets cheaper AI will woo small developers (blog)
[^c2-10]: https://x2labs.ai/notes/ios-ai-without-a-backend — Add AI to your iOS app without running an AI backend (blog)

### Foundation Models provider interoperability and release status

[^c3-1]: https://developer.apple.com/tutorials/data/documentation/foundationmodels/languagemodel.md — LanguageModel — FoundationModels API reference (Markdown representation) (docs)
[^c3-2]: https://developer.apple.com/videos/play/wwdc2026/241/ — What's new in the Foundation Models framework — WWDC26 (docs)
[^c3-3]: https://developer.apple.com/videos/play/wwdc2026/339/ — Bring an LLM provider to the Foundation Models framework — WWDC26 (docs)
[^c3-4]: https://developer.apple.com/foundation-models-framework/ — Get started with the Foundation Models framework — Apple Developer (docs)
[^c3-5]: https://github.com/apple/foundation-models-utilities — Apple Foundation Models Utilities repository (repo)
[^c3-6]: https://github.com/anthropics/ClaudeForFoundationModels/blob/main/README.md — ClaudeForFoundationModels README (repo)
[^c3-7]: https://github.com/anthropics/ClaudeForFoundationModels/releases — ClaudeForFoundationModels GitHub releases (repo)
[^c3-8]: https://claude.com/resources/articles/claude-for-foundation-models — Claude Foundation Models integration announcement (blog)
[^c3-9]: https://firebase.google.com/support/release-notes/ios — Firebase Apple SDK Release Notes (docs)
[^c3-10]: https://firebase.google.com/docs/ai-logic/apple-foundation-models-framework/get-started — Gemini through Apple Foundation Models guide (docs)
[^c3-11]: https://firebase.blog/posts/2026/06/apple-foundation-models-gemini — Gemini in Foundation Models framework (blog)
[^c3-12]: https://github.com/huggingface/AnyLanguageModel/releases — AnyLanguageModel GitHub releases (repo)
[^c3-13]: https://huggingface.co/blog/anylanguagemodel-1-0 — AnyLanguageModel 1.0 release article (blog)

### Foundation Models adapter lifecycle across OS releases

[^c4-1]: https://developer.apple.com/apple-intelligence/foundation-models-adapter — Foundation Models adapter training (docs)
[^c4-2]: https://developer.apple.com/forums/thread/829108 — Adapter Problem - compatibleAdapterNotFound (forum)
[^c4-3]: https://developer.apple.com/forums/thread/831314 — Adapter Training Toolkit: updated version for OS 27? (forum)
[^c4-4]: https://developer.apple.com/forums/thread/794839 — Foundation Models Adapter Training Toolkit v0.2.0 adapter compatibility report (forum)
[^c4-5]: https://hbmartin.github.io/Foundation-Models-and-Core-AI-and-MLX-skills/part-17-migration-from-pre-ios-27/references/02-adapter-sunset/ — The adapter sunset: migrating off custom LoRA adapters (blog)
[^c4-6]: https://github.com/Arthur-Ficial/apfel/issues/362 — Apfel issue 362: custom adapter support (repo)
[^c4-7]: https://www.reddit.com/r/Applelntelligence/comments/1uexrec/i_finetuned_apples_ondevice_model_the_macos_26/ — I fine-tuned Apple's on-device model, then Apple closed the door (forum)
