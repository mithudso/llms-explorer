<!-- llms-explorer concept facts · https://llms-explorer.com/tree/appintentstesting-harness-for-siri-schemas-and-entity-integrations/ · pack 2026-10-23 · ~1860 tokens -->

# AppIntentsTesting harness for Siri schemas and entity integrations

> Source-anchored research for AppIntentsTesting harness for Siri schemas and entity integrations. Run status: COMPLETED.

Parent: [App Schemas integration for Siri AI](https://llms-explorer.com/tree/app-schemas-integration-for-siri-ai/) · 6 facets · 21 facts · page: https://llms-explorer.com/tree/appintentstesting-harness-for-siri-schemas-and-entity-integrations/

## Structure and components

- Keep ordinary unit tests for application business rules, and use AppIntentsTesting for discovery, parameter resolution, result transfer and system integration. Neither a direct perform() test nor a harness-only suite covers every layer. (high confidence) — [source](https://developer.apple.com/videos/play/wwdc2026/295/)

## How it works

- AppIntentsTesting runs against a live app from a separate UI Testing process. IntentDefinitions uses the app bundle identifier and registered type names; tests need no app-module import. (high confidence) — [source](https://developer.apple.com/documentation/appintentstesting.md)
- makeReference(identifier:) constructs entity references for intent parameters. Stable identifiers matter because saved automations may resolve them in later sessions. (high confidence) — [source](https://developer.apple.com/documentation/appintentstesting/testing-your-app-intents-code.md)

## How-to and procedures

- Use an XCUITest/UI Testing bundle and the same code-signing development team as the app. The runner and application execute in separate processes; ordinary intent tests need no UI navigation automation. (high confidence) — [source](https://developer.apple.com/videos/play/wwdc2026/295/)
- To test Spotlight indexing, establish that a uniquely named fixture is absent, create it through an intent, then use spotlightQuery to assert the indexed entity exists with expected properties. A record visible inside the app does not establish that indexing occurred. (high confidence) — [source](https://developer.apple.com/videos/play/wwdc2026/295/)
- Create IntentDefinitions(bundleIdentifier:), then look up registered definitions by string name through collections such as intents and entities. Renames, parameter spellings and enum raw values require explicit maintenance because the test does not import the app types or receive their parameter-name completion. (high confidence) — [source](https://developer.apple.com/videos/play/wwdc2026/295/)
- To test onscreen context, navigate to a known entity and retrieve viewAnnotations() from its entity definition. Assert annotation count and entity identity/properties; use XCUITest to confirm the expected screen when necessary. This checks the context supplied to Siri. (high confidence) — [source](https://developer.apple.com/videos/play/wwdc2026/295/)

## Problems, failure modes and limitations

- flutter_intents issue #57 records a request for an AppIntentsTesting example scaffold and closure through PR #67 on June 9, 2026; this is adoption evidence, not a reported runtime failure. (low confidence) — [source](https://github.com/touyou/flutter_intents/issues/57)

## Comparisons and alternatives

- WWDC26 demonstrates an annotation failure caused by passing a calendar identifier instead of the displayed event identifier; correcting EntityIdentifier fixes the harness assertion. (low confidence) — [source](https://developer.apple.com/videos/play/wwdc2026/295/)
- AppIntentsTesting exercises registered intents, entities, enums and queries out of process through App Intents infrastructure. The test target uses type-erased definitions instead of linking against application types. This validates the system-facing boundary beyond directly calling perform(). (high confidence) — [source](https://developer.apple.com/documentation/appintentstesting/testing-your-app-intents-code.md)
- The official guide demonstrates exporting an entity with exported(as:) and reimporting with resolved(from:), then asserting a preserved property. This tests the serialization round trip rather than merely constructing a local entity. (low confidence) — [source](https://developer.apple.com/documentation/appintentstesting/testing-your-app-intents-code.md)

## Facts and statements

- Build an intent with makeIntent(...), execute it with try await run(), and assert returned properties through result.value and dynamic member lookup. Primitive values and enum raw strings are converted by the framework. (high confidence) — [source](https://developer.apple.com/videos/play/wwdc2026/295/)
- WWDC26 demonstrates enum raw-string parameters and string-to-entity resolution through EntityStringQuery; the latter selects the first matching entity. (low confidence) — [source](https://developer.apple.com/videos/play/wwdc2026/295/)
- Test entity string matching, identifier lookup and suggested entities separately. Seed known records, query the entity definition and assert result count and properties; successful business logic alone does not establish correct entity resolution. (high confidence) — [source](https://developer.apple.com/videos/play/wwdc2026/295/)
- An entity returned by a query or intent can be passed directly into another intent. Test a create/update or find/create/add chain to verify entity references and result values survive the same cross-intent boundary used by composed Shortcuts. (high confidence) — [source](https://developer.apple.com/documentation/appintentstesting/testing-your-app-intents-code.md)
- Make test-only intents reset or seed app data and navigate to required screens. Set isDiscoverable to false and compile them inside #if DEBUG: nondiscovery hides them from user-facing surfaces, while conditional compilation excludes them from release builds. (high confidence) — [source](https://developer.apple.com/documentation/appintentstesting/testing-your-app-intents-code.md)
- After navigating to a known screen, viewAnnotations() returns system-visible entity annotations. Assert their count and entity identity; the API also exposes selection state. (high confidence) — [source](https://developer.apple.com/documentation/appintentstesting/testing-your-app-intents-code.md)
- Passing harness tests does not establish that Siri understands a particular utterance. Apple recommends progressing from AppIntentsTesting to Shortcuts configuration, Spotlight discoverability and finally live Siri tests covering natural language, entity resolution, onscreen context and cross-app workflows. (high confidence) — [source](https://developer.apple.com/videos/play/wwdc2026/240/)
- App Schemas describe the actions and entities Siri understands. A passing custom App Intent test alone does not establish schema adoption or the complete Siri experience. (high confidence) — [source](https://developer.apple.com/videos/play/wwdc2026/240/)
- Apple framework availability metadata lists the 27.0 generation for iOS, iPadOS, macOS, Mac Catalyst, tvOS, visionOS and watchOS. This is an API availability declaration, not evidence that every Siri feature or test environment is generally released. (low confidence) (verified as of 2026-09-10) — [source](https://developer.apple.com/documentation/appintentstesting.md)
- ViewAnnotation exposes both entity and isSelected. A test can verify selection state as well as the annotated entity properties. (high confidence) — [source](https://developer.apple.com/documentation/appintentstesting/testing-your-app-intents-code.md)
