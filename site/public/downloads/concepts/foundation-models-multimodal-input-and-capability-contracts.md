<!-- llms-explorer concept facts · https://llms-explorer.com/tree/foundation-models-multimodal-input-and-capability-contracts/ · pack 2026-10-23 · ~1386 tokens -->

# Foundation Models multimodal input and capability contracts

> Source-anchored research for Foundation Models multimodal input and capability contracts. Run status: COMPLETED.

Parent: [Apple Foundation Models framework](https://llms-explorer.com/tree/apple-foundation-models-framework/) · 5 facets · 10 facts · page: https://llms-explorer.com/tree/foundation-models-multimodal-input-and-capability-contracts/

## Structure and components

- Apple dates the iOS 27 and iPadOS 27 releases to 2026-09-14, while the current Attachment and LanguageModelCapabilities.Capability.vision symbols list 27.0 platform availability. Image prompting is therefore part of released OS 27 APIs as of 2026-10-23; API availability alone does not guarantee that the on-device model is ready or eligible on a particular device. (medium confidence) (verified as of 2026-10-23) — [source](https://support.apple.com/en-us/100100)

## How-to and procedures

- Check the selected model’s capabilities before sending an image: Apple defines LanguageModelCapabilities.Capability.vision as accepting image inputs in prompts and documents general capability inspection with capabilities.contains(.guidedGeneration). Applying that pattern to capabilities.contains(.vision) before dispatch is our recommendation. Check SystemLanguageModel.availability separately because it reports runtime states such as deviceNotEligible and modelNotReady. (high confidence) (verified as of 2026-10-23) — [source](https://developer.apple.com/documentation/foundationmodels/languagemodelcapabilities.md)

## Problems, failure modes and limitations

- Image support is advertised through `LanguageModelCapabilities.Capability.vision`; callers can inspect the selected model’s `capabilities` before sending an image. Apple says a request for an undeclared capability can fail with `LanguageModelError.unsupportedCapability`, and an independent Swift wrapper forwards image attachments only when the resolved model reports vision support. (high confidence) (verified as of 2026-10-23) — [source](https://developer.apple.com/documentation/foundationmodels/languagemodelcapabilities.md)
- Apple’s `LanguageModelError` assigns separate typed cases to `.unsupportedCapability` (the model lacks a requested feature) and `.unsupportedTranscriptContent` (the prompt contains content the model cannot process), distinguishing capability mismatch from unsupported prompt content. (high confidence) (verified as of 2026-10-23) — [source](https://developer.apple.com/documentation/foundationmodels/languagemodelerror.md)

## Comparisons and alternatives

- Apple’s WWDC26 Group Lab said Foundation Models had no built-in video input at that time. Apple’s image guide says apps capturing images or processing video streams should use `CVPixelBuffer`; represent and process frames in the app rather than pass raw video as an image attachment. (high confidence) (verified as of 2026-06-09) — [source](https://developer.apple.com/videos/play/wwdc2026/8011/)
- In its June 2026 Group Lab, Apple said image support did not change the on-device 4,096-token budget and estimated roughly 200 tokens per image. Treat that as approximate, dated guidance rather than a fixed cross-model image cost: a separate developer article says larger images consume more tokens and latency, and Apple recommends measuring actual requests with Instruments. (medium confidence) (verified as of 2026-06-09) — [source](https://developer.apple.com/videos/play/wwdc2026/8011/)

## Facts and statements

- Apple’s current guide lists CGImage, CIImage, CVPixelBuffer, and image file URLs as supported image prompt inputs. It says the framework infers whether a URL is an image from its UTType, performs needed scaling and color conversion, and can apply an explicit orientation transform. (high confidence) (verified as of 2026-10-23) — [source](https://developer.apple.com/documentation/foundationmodels/analyzing-images-with-multimodal-prompting.md)
- As of 2026-10-23, Apple’s symbol metadata lists `Attachment`, `LanguageModelCapabilities`, and `.vision` with availability from iOS, iPadOS, macOS, Mac Catalyst, visionOS, and watchOS 27.0. `SystemLanguageModel` availability separately depends on device, region, and model readiness. Apple’s iOS 27 overview still points developers to beta downloads, so the reviewed pages establish a 27.0 API floor but do not establish a general-release promise for every target. (medium confidence) (verified as of 2026-10-23) — [source](https://developer.apple.com/documentation/foundationmodels/attachment.md)
- Apple’s context guide states that the on-device model has a 4,096-token session context and that prompts, instructions, tool definitions and results, generated schemas, and responses all consume it. `SystemLanguageModel.contextSize` exposes the selected system model’s maximum, `tokenCount(for:)` helps estimate prompt/instruction/tool usage, and Instruments reports request input and output counts. (high confidence) (verified as of 2026-10-23) — [source](https://developer.apple.com/documentation/foundationmodels/managing-the-context-window.md)
- LanguageModelError is nonexhaustive and has distinct unsupportedCapability, unsupportedTranscriptContent, and contextSizeExceeded cases. Apple defines contextSizeExceeded as the session transcript exceeding the model’s context size and recommends trimming history or starting a fresh session. (high confidence) (verified as of 2026-10-23) — [source](https://developer.apple.com/documentation/foundationmodels/languagemodelerror.md)
