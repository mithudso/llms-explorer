<!-- llms-explorer concept facts · https://llms-explorer.com/tree/genmoji-and-image-wand-integration/ · pack 2026-10-23 · ~1044 tokens -->

# Genmoji and Image Wand integration

> Source-anchored research for Genmoji and Image Wand integration. Run status: COMPLETED.

Parent: [Apple Intelligence](https://llms-explorer.com/tree/apple-intelligence/) · 3 facets · 9 facts · page: https://llms-explorer.com/tree/genmoji-and-image-wand-integration/

## How it works

- Apple's June 8, 2026 press release said that the next-generation features were available for developer testing and would reach users in fall; it also said Genmoji quality was improved and users could describe desired changes. Apple's current iOS 27 guide documents the creation and refinement flow after that announced rollout. The announcement establishes preview timing, not general availability on June 8. (high confidence) (verified as of 2026-10-23) — [source](https://www.apple.com/newsroom/2026/06/apple-intelligence-brings-powerful-ai-capabilities-into-everyday-experiences/)

## Comparisons and alternatives

- Apps that render inline Genmoji need adaptive image glyph support and must preserve glyph attributes and image data when editing or storing text; unsupported contexts should provide an image or content-description fallback instead of silently dropping the glyph. (high confidence) — [source](https://developer.apple.com/videos/play/wwdc2024/10220/)
- Genmoji are personalized raster images rather than Unicode characters. Apple's NSAdaptiveImageGlyph API lets rich-text hosts lay them out with text, and RTFD can preserve them with an attachment fallback in unsupported environments. MacRumors's iOS 18.2 guide reported that keyboard insertion and pasting depended on app support, so Genmoji should not be assumed to behave like plain-text emoji in every text field. (high confidence) (verified as of 2024-11-01) — [source](https://developer.apple.com/videos/play/wwdc2024/10220/)

## Facts and statements

- Apple's current iOS 27 guide documents Genmoji creation from a text description, an existing emoji or Genmoji, a person from Photos (up to three), or another photo. Users can refine a result by describing changes or adding emoji, move among versions, and save created Genmoji with stickers. (high confidence) (verified as of 2026-10-23) — [source](https://support.apple.com/de-de/guide/iphone/iph4e76f5667/27/ios/27)
- Apple documents Genmoji insertion in messages, sticker sharing, and Messages Tapback reactions; independent release testing also observed inline, sticker, and Tapback use in iMessage. (high confidence) (verified as of 2026-10-23) — [source](https://support.apple.com/en-euro/guide/iphone/iph4e76f5667/27/ios/27)
- Genmoji are rasterized personalized images, not Unicode characters; Apple represents them in attributed text with NSAdaptiveImageGlyph, which carries image data and metadata for accessibility and layout so the glyph can sit inline with text. (high confidence) — [source](https://developer.apple.com/videos/play/wwdc2024/10220/)
- Apple documents Image Wand as a Notes Markup workflow: users circle a sketch, image, text box, or area under typed text, add a description, review generated variants and styles, and insert the selected result. The support article lists iOS 18.2 and iPadOS 18.2 or later. (high confidence) (verified as of 2026-02-05) — [source](https://support.apple.com/en-gb/108919)
- Apple's current iPhone support guide documents Image Wand inside Notes: users can circle a rough sketch or a blank area below surrounding text and images to create an image. The guide says the sketches, descriptions, and surrounding content remain available for later edits, including adding or removing elements and changing style or background. (high confidence) (verified as of 2026-10-23) — [source](https://support.apple.com/en-euro/guide/iphone/iph7db25a67c/ios)
- Apple's October 22, 2026 feature matrix lists Genmoji for iPhone, iPad, Mac, and Apple Vision Pro, while it lists Image Wand for iPhone, iPad, and Apple Vision Pro. Apple's current Image Wand iPhone guide documents a Notes workflow; the platform matrix does not establish that every platform has the same creation surface. (high confidence) (verified as of 2026-10-22) — [source](https://support.apple.com/en-us/121115)
