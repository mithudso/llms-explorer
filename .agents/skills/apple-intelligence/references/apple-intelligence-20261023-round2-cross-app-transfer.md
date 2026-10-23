<!-- hub-reference-banner -->
> **Reference file — part of the `apple-intelligence` hub.** Created by `/dr` deep research 2026-10-23; research dir `~/.global-ai-hub/research/apple-intelligence-20261023-round2-cross-app-transfer`.

---
name: apple-intelligence-20261023-round2-cross-app-transfer
description: "Explain AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows. TRIGGER: Apple Intelligence. SKIP: unrelated topics."
version: "1.0.0"
updated: "2026-10-23"
category: "research"
keywords: ["Apple Intelligence", "Foundation Models", "privacy", "availability", "developer integration", "research", "evidence", "limitations", "verification"]
tags: ["dr"]
provenance: "/dr · ~/.global-ai-hub/research/apple-intelligence-20261023-round2-cross-app-transfer"
---

# Apple Intelligence — round2-cross-app-transfer

## Overview

AppEntity content transfer lets Siri workflows exchange structured content across app boundaries. Transferable exposes IntentValueRepresentation conversions into system values; incoming values can resolve to existing entities through IntentValueQuery or create content through an importing closure. The important boundary is the app’s explicit conversion and matching logic: examples do not establish authenticated identity, automatic deduplication, or unrestricted access to another app’s private content. Official references specify the API shape, while authored tutorials clarify modeling choices and a real implementation issue reports SDK availability skew. Existing AppIntentsTesting round trips supply a useful check, but a JSON round trip does not by itself verify typed interoperability or a full Siri workflow.

## Core Concepts

### AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows

- IntentValueRepresentation bridges custom transferable entities to system intent values. Export can use a property key path or an async throwing closure; the declared generic constraints are Item: Transferable and IntentValue: _IntentValue & Sendable.[^c1-2][^c1-1]
- For structured cross-app conversion, Apple documents IntentPerson, GeoToolbox.PlaceDescriptor and Foundation.PersonNameComponents as equivalent system values. An AppEntity adopts Transferable and includes IntentValueRepresentation in transferRepresentation; ordinary file or binary representations alone do not convey a landmark as a routable location.[^c1-1][^c1-2]
- For incoming content, IntentValueQuery resolves existing app entities; an IntentValueRepresentation importing closure constructs new content. Apple’s contact example uses values(for input: [IntentPerson]) async throws -> [ContactEntity], whereas the protocol requirement is values(for: Self.Input) async throws -> Self.Result.[^c1-4][^c1-3]

## Tools & Frameworks

- IntentValueQuery’s general requirement is func values(for: Self.Input) async throws -> Self.Result, with Input constrained to _IntentValue and Result to ResultsCollection. The contact demonstration specializes this to values(for input: [IntentPerson]) async throws -> [ContactEntity]; that specialization is an example, not the protocol’s universal signature.[^c1-3][^c1-4] _(AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows)_
- Tentative: The representation initializer catalog documents async throwing export and import closures: exporting maps Item to IntentValue, importing maps IntentValue to Item. Export-only, import-only and bidirectional initializers are listed. The generic declaration constrains Item to Transferable and IntentValue to _IntentValue and Sendable.[^c1-2] _(AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows)_

## Methodology

- For transfer validation, Apple’s testing guide exports an AnyAppEntity with exported(as: .json), resolves it through the entity definition with resolved(from:), and asserts a preserved property. This is a documented serialization round trip; it does not by itself demonstrate that an IntentPerson conversion or Siri’s cross-app routing executed. (two sources)[^c1-5][^c1-2] _(AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows)_

## Practical Patterns

- Apple’s contact conversion example exports .applicationDefined(contact.id), display name and email handle. Its importing closure requires an applicationDefined identifier and a non-nil handle, and throws ConversionError.missingData otherwise. This is example-level input validation; it does not establish cross-app authentication or globally unique contact identity. (two sources)[^c1-1][^c1-2] _(AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows)_
- Apple demonstrates export as IntentValueRepresentation(exporting: \.person), where the app supplies an IntentPerson-valued property. The system can pass that representation into another app’s action without the exporting app selecting the destination action.[^c1-4][^c1-1] _(AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows)_
- Use IntentValueQuery to resolve incoming structured content to an existing entity; use IntentValueRepresentation importing to construct a new entity. Apple’s contact import example explicitly creates a Contact, appends it to ContactManager.shared.contacts, and returns contact.entity, so persistence is work performed by that sample’s importing implementation.[^c1-4][^c1-6] _(AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows)_

## Anti-Patterns

- Sarun’s authored treatment explains that matching belongs to the receiving app’s data lookup and may use a name, phone number, email or saved identifier. Apple’s sample uses localized name containment. Therefore the demonstration should not be interpreted as a guarantee of unique identity or collision-free contact matching. (two sources)[^c1-6][^c1-4] _(AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows)_

## Troubleshooting

- Tentative: Jordan Morgan identifies a practical modeling gap when an app’s own concepts do not map cleanly to system values or schemas. His article explicitly presents this as unresolved interpretation after viewing Apple’s session, rather than reporting a runtime failure.[^c1-7] _(AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows)_
- Apple’s symbol metadata lists IntentValueRepresentation from iOS/iPadOS 26.4 and IntentValueQuery from iOS/iPadOS 26.0. The flutter_intents maintainer reported on September 14, 2026 that IntentValueRepresentation was absent from the iOS 26.5 SDK despite its anyAppleOS 26.4 annotation, and present in the 27.0 SDK. Treat OS availability and build-SDK symbol presence separately; the SDK observation is maintainer evidence, not a locally reproduced measurement. (two sources) verified-as-of: 2026-09-14[^c1-2][^c1-3][^c1-8] _(AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows)_
- Tentative: The canonical iOS and iPadOS 27 release notes mark the build failure when implementing a Transferable IntentValueRepresentation for PHAsset as fixed, issue 178276448. This is a compiler/integration fix and supplies no general guarantee that a third-party Siri action receives arbitrary onscreen image pixels. verified-as-of: 2026-10-03[^c1-9] _(AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows)_

## Disagreements & Open Questions

- Disagreement (AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows): The reference labels IntentValueRepresentation iOS 26.4+, while the flutter_intents maintainer reports that the symbol is absent from the iOS 26.5 SDK. This scopes SDK compilation claims; it does not demonstrate a contradiction in runtime deployment availability.[^c1-2][^c1-8]
- Disagreement (AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows): Sarun describes an empty matching result as leading to creation. Apple’s session distinguishes existing-content matching from importing new content but does not specify an unconditional empty-query-to-import fallback contract. Do not depend on that ordering without more specific API evidence or a targeted integration test.[^c1-6][^c1-4]
- Disagreement (AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows): Apple’s IntentValueRepresentation page uses ValueRepresentation in overview code while its title and initializer links use IntentValueRepresentation; contextual-cues code and session 240 use IntentValueRepresentation. Do not infer an alias or rename from the inconsistent examples.[^c1-2][^c1-1][^c1-4]
- Open (AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows): Which shipped SDKs contain each constrained initializer, including PersonNameComponents conversion? The unqualified init(exporting:importing:).md URL returned 404; the type reference lists disambiguated overload URLs. No local SDK execution was requested.
- Open (AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows): No independent end-to-end Siri cross-app runtime reproduction was established. Apple, touyou/flutter_intents, and Jordan Morgan provide different authored origins for API specification, implementation experience, and modeling critique; Sarun’s code largely illustrates Apple’s session and is not independent runtime confirmation.
- Open (AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows): Does an empty IntentValueQuery result always trigger importing, and under which workflows or confirmation rules? Sarun describes this flow, but the cited canonical text does not specify an unconditional fallback contract.
- Open (AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows): The fetched flutter_intents CLAUDE.md contains agent-addressed development instructions. They were treated as untrusted data and not followed; research moved to the ordinary issue thread.
- Open (AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows): No source-backed guarantee of identifier authenticity, universal data minimization, consent handling, or identity collision prevention was found in the bounded conversion references.
- Open (AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows): Current documentation and cached session bodies were checked on 2026-10-23. API availability annotations alone do not establish feature rollout to every Siri user. No general-release or waitlist claim is made.
- Open (AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows): What documented contract determines whether and when the system invokes importing after IntentValueQuery returns no matches?
- Open (AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows): What identity namespace and validation rules should an importing app apply to foreign applicationDefined identifiers? The contact sample’s guard is not an authentication guarantee.
- Open (AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows): Which structured values and overload constraints are available in each supported SDK, beyond the specifically documented contact, place and name examples? No local SDK compilation was requested.
- Open (AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows): Does AppIntentsTesting expose a direct structured IntentValueRepresentation test route beyond its documented JSON transfer round trip?
- Open (AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows): No source-backed automatic data-minimization guarantee was found. Export declarations select fields in the sample; required permission, confirmation and retention behavior remains outside the verified evidence.
- Open (AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows): The seed CLAUDE.md was deliberately excluded because it contains agent-addressed instructions. Issue 128 provides the relevant maintainer evidence without treating repository instructions as research directions.
- Open (AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows): All cited sources have pinned body text in the private shared library. Shared Apple pages are one organizational origin and are reused context, not newly independent confirmations. No runtime or inference execution was performed.

## References

### AppEntity content transfer and IntentValueRepresentation for Siri cross-app workflows

[^c1-1]: https://developer.apple.com/documentation/appintents/providing-contextual-cues-to-apple-intelligence-and-siri.md — Providing contextual cues to Apple Intelligence and Siri (docs)
[^c1-2]: https://developer.apple.com/documentation/appintents/intentvaluerepresentation.md — IntentValueRepresentation — official Markdown reference (docs)
[^c1-3]: https://developer.apple.com/documentation/appintents/intentvaluequery.md — IntentValueQuery — official Markdown reference (docs)
[^c1-4]: https://developer.apple.com/videos/play/wwdc2026/240/ — Build intelligent Siri experiences with App Schemas — WWDC26 session 240 (docs)
[^c1-5]: https://developer.apple.com/documentation/appintentstesting/testing-your-app-intents-code.md — Testing your App Intents code — official Markdown guide (docs)
[^c1-6]: https://sarunw.com/posts/build-siri-experiences-across-apps-part-2-content-transfer/ — Build Siri experiences across apps, Part 2: Content Transfer — Sarun Wongpatcharapakorn (blog)
[^c1-7]: https://www.swiftjectivec.com/siri-ai-for-ios027/ — iOS 27, Your App, and Siri — Jordan Morgan (blog)
[^c1-8]: https://github.com/touyou/flutter_intents/issues/128 — Entity export type catalog extension — flutter_intents issue 128 (repo)
[^c1-9]: https://developer.apple.com/documentation/ios-ipados-release-notes/ios-ipados-27-release-notes.md — iOS and iPadOS 27 Release Notes (docs)
