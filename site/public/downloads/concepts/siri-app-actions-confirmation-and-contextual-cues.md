<!-- llms-explorer concept facts · https://llms-explorer.com/tree/siri-app-actions-confirmation-and-contextual-cues/ · pack 2026-10-23 · ~1648 tokens -->

# Siri app actions confirmation and contextual cues

> Source-anchored research for Siri app actions confirmation and contextual cues. Run status: COMPLETED.

5 facets · 13 facts · page: https://llms-explorer.com/tree/siri-app-actions-confirmation-and-contextual-cues/

## Definitions

- Device authentication is a separate execution control from confirmation: an App Intent can require the device to be unlocked, schemas carry default authentication policies based on sensitivity and data, and developers may override a schema policy only to make it stricter. (high confidence) (verified as of 2026-10-23) — [source](https://developer.apple.com/documentation/appintents/appintent)

## How it works

- On September 20, 2026, 9to5Mac reported user complaints that Siri AI required an iPhone to be unlocked for many requests, including simple send-message requests, even when the allow-Siri-when-locked setting was enabled. The report characterizes this as beta access or reliability behavior; it does not establish that the unlock prompt is an action confirmation or that Siri failed to resolve the user's intent. (low confidence) (verified as of 2026-09-20) — [source](https://9to5mac.com/2026/09/20/five-ways-that-the-new-siri-ai-is-frustrating-iphone-and-apple-watch-users/)

## Problems, failure modes and limitations

- An app can explicitly request confirmation before performing an App Intent, including with requestConfirmation() and conditional confirmation APIs. Apple also says Apple Intelligence or Siri may request confirmation for destructive or sensitive entity updates; this app-defined prompt is distinct from system-managed risk confirmation. (high confidence) — [source](https://developer.apple.com/documentation/appintents/appintent)
- At WWDC26, Apple described Siri and App Intents confirmations as contextual and risk-based: the system evaluates an intent's schema side-effect metadata together with dynamic system state before execution, and actions with higher risk are more likely to prompt. If the person declines, the intent does not run. Apple's OwnershipProvidingEntity documentation separately says the system may request confirmation for destructive or sensitive actions and can include ownership context when an entity is shared or public. (high confidence) (verified as of 2026-10-23) — [source](https://developer.apple.com/videos/play/wwdc2026/347/)
- Context annotations improve reference resolution but do not guarantee that Siri identifies the intended entity: Apple says Siri may ask for clarification or act on another item if it cannot understand the visible entities quickly enough. Lightweight display-representation queries can help Siri resolve them faster. (medium confidence) — [source](https://developer.apple.com/videos/play/wwdc2026/343/)
- In an October 9, 2026 hands-on review using Siri AI on an iPhone 18 Pro with iOS 27, Nielsen Norman Group observed a drafted message with confirmation before sending. Its comparison also found old Siri selected the wrong contact and literal message content; the reviewer said the confirmation lets a user catch that type of resolution error. This is one reviewer's test, not evidence that every message action always prompts. (low confidence) (verified as of 2026-10-09) — [source](https://www.nngroup.com/articles/ai-assistant-context/)

## Comparisons and alternatives

- Two Siri AI beta reports show context-to-action gaps rather than a guaranteed path from suggestion to completion: Tom’s Guide reported that an onscreen Messages reminder suggestion still required manual entry of details, while 9to5Mac reported lookup failures and unclear errors for some app data and commands. These are dated beta observations, not universal behavior. (medium confidence) (verified as of 2026-09-20) — [source](https://www.tomsguide.com/phones/iphones/i-spent-a-week-with-siri-ai-here-are-my-honest-pros-and-cons)

## Facts and statements

- The App Intents parameter-resolution step occurs before perform(): the system may infer @Parameter values from the current conversation or ask the person to provide them. Apple documents side-effect confirmation as a separate gate after intent selection and before execution, so resolving an action or value is distinct from authorizing its effects. (high confidence) — [source](https://developer.apple.com/documentation/appintents/appintent)
- OwnershipProvidingEntity supplies sharing and ownership context for an entity. Apple says Siri may skip confirmation for private entities by default and uses current ownership state to decide whether to confirm shared or public content; the protocol is documented for Apple OS 27 releases as of 2026-10-23. (high confidence) (verified as of 2026-10-23) — [source](https://developer.apple.com/documentation/appintents/ownershipprovidingentity)
- On-screen context is provided through structured app entities attached to the views that display them, using APIs such as appEntityIdentifier, NSUserActivity, and view annotations. These cues can let Siri resolve references such as “the third one”; they add app data and location context beyond text visible in pixels. (high confidence) — [source](https://developer.apple.com/documentation/appintents/providing-contextual-cues-to-apple-intelligence-and-siri)
- Apps can shape spoken and visual results with IntentDialog, entity DisplayRepresentation, and static or interactive snippets. Apple’s snippets documentation warns that Siri AI might not display IntentDialog or ShowsSnippetView for an App Intent, so a custom result view is not guaranteed in every Siri AI interaction. (high confidence) (verified as of 2026-10-23) — [source](https://developer.apple.com/videos/play/wwdc2026/343/)
- An app can add its own confirmation gate with AppIntent.requestConfirmation(). Apple's interactive-snippet guidance shows the intent pausing for the person to review or change ticket details; if they cancel, the intent stops before the follow-on action runs. (high confidence) — [source](https://developer.apple.com/documentation/appintents/appintent.md)
- Apple says an app's onscreen data remains private to that app unless the developer supplies context. Developers can attach matching app entities to views, allowing Siri to ground references such as 'the third one' in structured content; Apple warns not to associate unrelated entities with a view. This app-supplied context is distinct from model inference over an unannotated screen. (high confidence) — [source](https://developer.apple.com/documentation/appintents/providing-contextual-cues-to-apple-intelligence-and-siri.md)
