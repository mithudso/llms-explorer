<!-- hub-reference-banner -->
> **Reference file — part of the `apple-intelligence` hub.** Created by `/dr` deep research 2026-10-23; research dir `~/.global-ai-hub/research/apple-intelligence-20261023-round1-system-testing`.

---
name: apple-intelligence-20261023-round1-system-testing
description: "Explain AppIntentsTesting harness for Siri schemas and entity integrations. TRIGGER: Apple Intelligence. SKIP: unrelated topics."
version: "1.0.0"
updated: "2026-10-23"
category: "research"
keywords: ["Apple Intelligence", "Foundation Models", "privacy", "availability", "developer integration", "research", "evidence", "limitations", "verification"]
tags: ["dr"]
provenance: "/dr · ~/.global-ai-hub/research/apple-intelligence-20261023-round1-system-testing"
---

# Apple Intelligence — round1-system-testing

## Overview

AppIntentsTesting validates the system-facing App Intents contract through a live app process. Tests discover definitions by bundle identifier, construct intents dynamically, and inspect returned entities without importing app types. A useful suite covers parameter conversion, query fixtures, stable identifiers, chained intents, deterministic debug-only setup, Spotlight indexing, and visible entity annotations. These checks isolate integration defects before manual Shortcuts and Siri acceptance testing. They do not exercise Siri natural-language interpretation or prove that custom intents adopt supported App Schemas. Apple documentation supplies the API contract; independent developer examples supply additional implementation context. Release-status language in secondary material is inconsistent, so SDK availability and Siri rollout must remain separate questions.

## Core Concepts

### AppIntentsTesting harness for Siri schemas and entity integrations

- AppIntentsTesting runs against a live app from a separate UI Testing process. IntentDefinitions uses the app bundle identifier and registered type names; tests need no app-module import.[^c1-4][^c1-6]
- App Schemas describe the actions and entities Siri understands. A passing custom App Intent test alone does not establish schema adoption or the complete Siri experience.[^c1-2][^c1-5]
- AppIntentsTesting exercises registered intents, entities, enums and queries out of process through App Intents infrastructure. The test target uses type-erased definitions instead of linking against application types. This validates the system-facing boundary beyond directly calling perform().[^c1-3][^c1-4][^c1-6]

## Tools & Frameworks

- Use an XCUITest/UI Testing bundle and the same code-signing development team as the app. The runner and application execute in separate processes; ordinary intent tests need no UI navigation automation.[^c1-1][^c1-3] _(AppIntentsTesting harness for Siri schemas and entity integrations)_
- Tentative: Apple framework availability metadata lists the 27.0 generation for iOS, iPadOS, macOS, Mac Catalyst, tvOS, visionOS and watchOS. This is an API availability declaration, not evidence that every Siri feature or test environment is generally released. verified-as-of: 2026-09-10[^c1-4] _(AppIntentsTesting harness for Siri schemas and entity integrations)_
- Tentative: flutter_intents issue #57 records a request for an AppIntentsTesting example scaffold and closure through PR #67 on June 9, 2026; this is adoption evidence, not a reported runtime failure.[^c1-7] _(AppIntentsTesting harness for Siri schemas and entity integrations)_
- ViewAnnotation exposes both entity and isSelected. A test can verify selection state as well as the annotated entity properties.[^c1-3][^c1-4] _(AppIntentsTesting harness for Siri schemas and entity integrations)_

## Methodology

- Test entity string matching, identifier lookup and suggested entities separately. Seed known records, query the entity definition and assert result count and properties; successful business logic alone does not establish correct entity resolution.[^c1-1][^c1-5][^c1-6] _(AppIntentsTesting harness for Siri schemas and entity integrations)_
- To test Spotlight indexing, establish that a uniquely named fixture is absent, create it through an intent, then use spotlightQuery to assert the indexed entity exists with expected properties. A record visible inside the app does not establish that indexing occurred.[^c1-1][^c1-5] _(AppIntentsTesting harness for Siri schemas and entity integrations)_
- After navigating to a known screen, viewAnnotations() returns system-visible entity annotations. Assert their count and entity identity; the API also exposes selection state.[^c1-3][^c1-6] _(AppIntentsTesting harness for Siri schemas and entity integrations)_
- To test onscreen context, navigate to a known entity and retrieve viewAnnotations() from its entity definition. Assert annotation count and entity identity/properties; use XCUITest to confirm the expected screen when necessary. This checks the context supplied to Siri.[^c1-1][^c1-3] _(AppIntentsTesting harness for Siri schemas and entity integrations)_
- Tentative: The official guide demonstrates exporting an entity with exported(as:) and reimporting with resolved(from:), then asserting a preserved property. This tests the serialization round trip rather than merely constructing a local entity.[^c1-3] _(AppIntentsTesting harness for Siri schemas and entity integrations)_
- Keep ordinary unit tests for application business rules, and use AppIntentsTesting for discovery, parameter resolution, result transfer and system integration. Neither a direct perform() test nor a harness-only suite covers every layer.[^c1-1][^c1-6] _(AppIntentsTesting harness for Siri schemas and entity integrations)_

## Practical Patterns

- Build an intent with makeIntent(...), execute it with try await run(), and assert returned properties through result.value and dynamic member lookup. Primitive values and enum raw strings are converted by the framework.[^c1-1][^c1-3][^c1-6] _(AppIntentsTesting harness for Siri schemas and entity integrations)_
- Tentative: WWDC26 demonstrates enum raw-string parameters and string-to-entity resolution through EntityStringQuery; the latter selects the first matching entity.[^c1-1] _(AppIntentsTesting harness for Siri schemas and entity integrations)_
- makeReference(identifier:) constructs entity references for intent parameters. Stable identifiers matter because saved automations may resolve them in later sessions.[^c1-3][^c1-6] _(AppIntentsTesting harness for Siri schemas and entity integrations)_
- An entity returned by a query or intent can be passed directly into another intent. Test a create/update or find/create/add chain to verify entity references and result values survive the same cross-intent boundary used by composed Shortcuts.[^c1-3][^c1-6] _(AppIntentsTesting harness for Siri schemas and entity integrations)_
- Make test-only intents reset or seed app data and navigate to required screens. Set isDiscoverable to false and compile them inside #if DEBUG: nondiscovery hides them from user-facing surfaces, while conditional compilation excludes them from release builds.[^c1-3][^c1-5][^c1-1] _(AppIntentsTesting harness for Siri schemas and entity integrations)_
- Create IntentDefinitions(bundleIdentifier:), then look up registered definitions by string name through collections such as intents and entities. Renames, parameter spellings and enum raw values require explicit maintenance because the test does not import the app types or receive their parameter-name completion.[^c1-1][^c1-5] _(AppIntentsTesting harness for Siri schemas and entity integrations)_

## Anti-Patterns

- Passing harness tests does not establish that Siri understands a particular utterance. Apple recommends progressing from AppIntentsTesting to Shortcuts configuration, Spotlight discoverability and finally live Siri tests covering natural language, entity resolution, onscreen context and cross-app workflows.[^c1-2][^c1-5] _(AppIntentsTesting harness for Siri schemas and entity integrations)_

## Troubleshooting

- Tentative: WWDC26 demonstrates an annotation failure caused by passing a calendar identifier instead of the displayed event identifier; correcting EntityIdentifier fixes the harness assertion.[^c1-1] _(AppIntentsTesting harness for Siri schemas and entity integrations)_

## Disagreements & Open Questions

- Disagreement (AppIntentsTesting harness for Siri schemas and entity integrations): The October 12 walkthrough calls AppIntentsTesting out of beta/GM near its opening but still calls it beta in its limitations. Its release labels are internally inconsistent; the June walkthrough also describes early beta APIs. Neither establishes current Siri deployment status.[^c1-6][^c1-5][^c1-4]
- Disagreement (AppIntentsTesting harness for Siri schemas and entity integrations): Anton Gubarenko’s October 12 article describes the framework as out of beta/GM near the beginning but calls it beta in its Limitations section. The June Swift Dev post explicitly describes early beta-cycle snippets. These passages do not establish current release status.[^c1-6][^c1-5]
- Disagreement (AppIntentsTesting harness for Siri schemas and entity integrations): The official guide describes the intents collection but its first intent-test snippet uses definitions.intent in the singular. The WWDC example and both developer examples use definitions.intents. Treat the singular occurrence as a documentation inconsistency and verify snippets against the installed SDK.[^c1-3][^c1-1][^c1-5][^c1-6]
- Open (AppIntentsTesting harness for Siri schemas and entity integrations): Confirm installed Xcode/SDK signatures before using examples: the official article contains definitions.intent in one snippet while its prose and other examples use definitions.intents.
- Open (AppIntentsTesting harness for Siri schemas and entity integrations): The official Markdown documents are undated; 2026-10-23 records retrieval of their availability metadata, not a publication date.
- Open (AppIntentsTesting harness for Siri schemas and entity integrations): No relevant postmortem or controlled runtime failure investigation surfaced in the six external scout searches. The GitHub adoption issue does not establish tested CI success.
- Open (AppIntentsTesting harness for Siri schemas and entity integrations): The three author origins are Apple, Trevor Whittingham, and Anton Gubarenko. Their articles overlap with Apple material; derivative API explanations are not independent experimental confirmation.
- Open (AppIntentsTesting harness for Siri schemas and entity integrations): The scout found agent-skill and packaged-prompt repositories. Their assistant-directed instructions were treated as untrusted source content and were not followed; these candidates were not used as API authority.
- Open (AppIntentsTesting harness for Siri schemas and entity integrations): The web reader rejected official Markdown as unsupported content-type. Native source-library retrieval pinned and exposed the full official Markdown bodies; the corresponding HTML pages were JavaScript shells.
- Open (AppIntentsTesting harness for Siri schemas and entity integrations): No app or test suite was executed in this research. Apple demonstrations and developer sample code establish intended usage, not independently measured runtime reliability, timing or CI pass rates.
- Open (AppIntentsTesting harness for Siri schemas and entity integrations): Apple is one organizational origin across all official pages. Trevor’s TaskBox and Anton Gubarenko’s FocusTimer examples are separate authored engineering treatments, but repeated framework descriptions derive from Apple and are not additional independent confirmations of Apple’s implementation.
- Open (AppIntentsTesting harness for Siri schemas and entity integrations): Current GM/beta status and device-versus-simulator restrictions require explicit current SDK or release-note evidence. The collected framework metadata establishes minimum API versions only.
- Open (AppIntentsTesting harness for Siri schemas and entity integrations): The developer examples differ in how they pass identifiers to entities(identifiers:). Verify the exact overload and accepted types in the installed SDK before copying those snippets.
- Open (AppIntentsTesting harness for Siri schemas and entity integrations): Agent-skill repositories and derivative session summaries were discovery leads only. They were not used as empirical test evidence or counted as independent implementation origins.
- Open (AppIntentsTesting harness for Siri schemas and entity integrations): All six cited URLs have pinned body text in the private shared library, fetched October 23, 2026. Official Markdown twins carry documentation bodies rather than JavaScript shells. No new external page fetch was needed.

## References

### AppIntentsTesting harness for Siri schemas and entity integrations

[^c1-1]: https://developer.apple.com/videos/play/wwdc2026/295/ — Validate your App Intents adoption with AppIntentsTesting — WWDC26 (docs)
[^c1-2]: https://developer.apple.com/videos/play/wwdc2026/240/ — Build intelligent Siri experiences with App Schemas — WWDC26 (docs)
[^c1-3]: https://developer.apple.com/documentation/appintentstesting/testing-your-app-intents-code.md — Testing your App Intents code — official Markdown representation (docs)
[^c1-4]: https://developer.apple.com/documentation/appintentstesting.md — App Intents Testing — official Markdown framework catalog (docs)
[^c1-5]: https://theswift.dev/posts/test-siri-spotlight-shortcuts-appintentstesting/ — Test Siri, Spotlight, And Shortcuts Integrations With AppIntentsTesting — Trevor Whittingham (blog)
[^c1-6]: https://antongubarenko.substack.com/p/ios-27-app-intents-testing — iOS 27: App Intents Testing — Anton Gubarenko, October 12, 2026 (blog)
[^c1-7]: https://github.com/touyou/flutter_intents/issues/57 — flutter_intents #57 — Integration testing with AppIntentsTesting (forum)
