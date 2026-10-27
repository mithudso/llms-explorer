<!-- hub-reference-banner -->
> **Reference file — part of the `apple-intelligence` hub.** Created by `/dr` deep research 2026-10-23; research dir `~/.global-ai-hub/research/apple-intelligence-20261023-round1-image-provenance`.

---
name: apple-intelligence-20261023-round1-image-provenance
description: "Explain Apple Intelligence image edit provenance and export boundaries. TRIGGER: Apple Intelligence. SKIP: unrelated topics."
version: "1.0.0"
updated: "2026-10-23"
category: "research"
keywords: ["Apple Intelligence", "Foundation Models", "privacy", "availability", "developer integration", "research", "evidence", "limitations", "verification"]
tags: ["dr"]
provenance: "/dr · ~/.global-ai-hub/research/apple-intelligence-20261023-round1-image-provenance"
---

# Apple Intelligence — round1-image-provenance

## Overview

Apple image provenance has separate layers: Photos Info labels, embedded IPTC/EXIF metadata, and announced SynthID signals in image content. Apple's September 2026 footnote limits SynthID to a later update and most edited images. An independent 2025 Clean Up experiment documents AI metadata, lost camera/location fields, and removable labels, but does not validate current iOS 27 exports. Photos retains originals and Image Playground retains gallery versions; neither establishes that a shared rendered file carries reversible history. Google's public detector provides a verification route for supported watermarks while still listing Apple as forthcoming. Current Apple-specific export tests remain a gap, so metadata visibility, watermark detection, and authenticity must be evaluated separately.

## Core Concepts

### Apple Intelligence image edit provenance and export boundaries

- Tentative: Apple's WWDC26 camera/photo engineers state that AI edits such as Clean Up and Spatial Reframe update IPTC metadata in the file alongside EXIF, and that Photos Info displays which edit was used. This is a metadata disclosure mechanism; the answer does not establish a signed C2PA edit history. verified-as-of: 2026-06-12[^c1-7]
- Apple's September 14, 2026 announcement describes SynthID support for Apple Intelligence image generation and editing as upcoming. Its footnote says a software update later in 2026 will cover most edited images depending on the edits applied. Google’s current SynthID page also lists Apple as coming soon. These sources do not establish universal or already-shipped Apple watermarking. verified-as-of: 2026-09-14[^c1-8][^c1-3]
- SynthID embeds an imperceptible signal in image content, whereas IPTC/EXIF labels are file metadata. Google designs the signal to tolerate operations including cropping, filtering and lossy compression. That design statement is not an Apple-specific guarantee that every export or share preserves detection. (two sources)[^c1-3][^c1-7]

## Tools & Frameworks

- In a forensic experiment updated March 18, 2025, malwr4n6 found Clean Up output with Credit set to Apple Photos Clean Up and Digital Source Type set to compositeWithTrainedAlgorithmicMedia. IPTC defines that source-type category for generative edits such as inpainting or outpainting; it does not mean the entire image was generated from scratch. (two sources)[^c1-5][^c1-4] _(Apple Intelligence image edit provenance and export boundaries)_
- Tentative: Google's current SynthID page offers a public Detector portal for supported images, video and audio, and separately describes checking Google AI media through Gemini, Search and Chrome. Because the same page lists Apple as coming soon, access to a detector is not evidence of validated Apple export detection. verified-as-of: 2026-10-23[^c1-3] _(Apple Intelligence image edit provenance and export boundaries)_

## Methodology

_(none recorded)_

## Practical Patterns

- Photos retains a route back to the original: Apple's iOS 27 guide provides Revert to Original after saving, and Amateur Photographer's September 30, 2026 hands-on review describes the AI editing tools as non-destructive. This in-library recovery does not demonstrate that a shared rendered image includes the original or a reversible edit history. verified-as-of: 2026-09-30[^c1-9][^c1-10] _(Apple Intelligence image edit provenance and export boundaries)_
- Tentative: The iOS 27 Image Playground guide describes automatically saved gallery versions, continued editing from an earlier version, and share/copy controls. It makes no promise in those instructions that recipient files include the gallery's version history or that all provenance markers survive sharing. verified-as-of: 2026-10-22[^c1-11] _(Apple Intelligence image edit provenance and export boundaries)_

## Anti-Patterns

- Tentative: The 2025 forensic author changed both Credit and Digital Source Type and observed the Clean Up/AI label disappear when the edited file was opened in Photos. Consequently, absence of that metadata-driven label alone cannot authenticate an image as unedited.[^c1-5] _(Apple Intelligence image edit provenance and export boundaries)_

## Troubleshooting

- Tentative: The same 2025 forensic experiment observed that Clean Up output lost camera make/model and location metadata. This is an observation from the author's exported sample, not a demonstrated privacy or export rule for every iOS 27 workflow.[^c1-5] _(Apple Intelligence image edit provenance and export boundaries)_
- Tentative: Postcue reports that the Clean Up label survives iMessage and AirDrop but disappears through some third-party apps. Its page labels the behavior reported rather than vendor-confirmed and supplies no current iOS 27 destination-by-destination test matrix, so this is a lead for validation rather than a universal export rule. verified-as-of: 2026-10-23[^c1-1] _(Apple Intelligence image edit provenance and export boundaries)_

## Disagreements & Open Questions

- Disagreement (Apple Intelligence image edit provenance and export boundaries): Broad descriptions of automatically watermarked Apple Intelligence output overstate the September Apple footnote: SynthID is forthcoming and covers most edits depending on the operation. The Mac Observer independently highlights this scope limitation, but its rollout facts derive from Apple rather than a separate product test.[^c1-8][^c1-6]
- Disagreement (Apple Intelligence image edit provenance and export boundaries): Postcue and BlankAI repeat the 2025 forensic analysis for exact Clean Up tags and camera/GPS removal. They are not additional independent experimental origins. The forensic article calls several fields EXIF broadly, while Apple's engineers explicitly distinguish IPTC metadata alongside EXIF.[^c1-1][^c1-2][^c1-5][^c1-7]
- Open (Apple Intelligence image edit provenance and export boundaries): Which released Apple OS build first enables SynthID, and which generation paths and edit types are included? Apple's dated September statement and Google's current page do not settle an exact build.
- Open (Apple Intelligence image edit provenance and export boundaries): Does SynthID remain detectable after each Apple-specific path: AirDrop, Messages, Files export, HEIC-to-JPEG conversion, screenshots, Shared Albums and social-platform recompression? No current independent Apple-specific matrix was verified.
- Open (Apple Intelligence image edit provenance and export boundaries): Which exact IPTC/XMP fields do Clean Up, Extend, Spatial Reframe and Image Playground write in released iOS 27? The 2025 sample cannot settle the current tag set.
- Open (Apple Intelligence image edit provenance and export boundaries): Does exported Image Playground content contain a signed C2PA manifest, a generator label, SynthID, or some combination for each provider path? Neither generic IPTC guidance nor the gallery-sharing guide proves that.
- Open (Apple Intelligence image edit provenance and export boundaries): The Google library fetch initially contained undecoded compressed bytes. Its snapshot was replaced through the native source snapshot helper with the Codex web-open representation before citation; no robustness measurements were inferred from it.

## References

### Apple Intelligence image edit provenance and export boundaries

[^c1-1]: https://postcue.ai/tools/apple-photos-clean-up — Does Apple Photos Clean Up add AI metadata to your photos? (blog)
[^c1-2]: https://blankai.app/remove-metadata-from-apple-image-playground-images — Remove Metadata from Apple Image Playground and Clean Up Photos (blog)
[^c1-3]: https://deepmind.google/models/synthid/ — Google SynthID (docs)
[^c1-4]: https://iptc.org/news/new-digital-source-type-term-added-to-support-inpainting-outpainting-in-generative-ai/ — New digital source type for inpainting and outpainting (docs)
[^c1-5]: https://www.malwr4n6.com/post/apple-intelligence-photo-forensics — Apple Intelligence Photo Forensics: Photo Cleanup (blog)
[^c1-6]: https://www.macobserver.com/news/iphone-18-pro-photos-ai-watermark-synthid-vs-reference-image/ — iPhone 18 Pro Photos and AI Watermarks: What Apple's SynthID Footnote Says (blog)
[^c1-7]: https://developer.apple.com/videos/play/wwdc2026/8018/ — Camera and Photo Technologies Group Lab — WWDC26 (docs)
[^c1-8]: https://www.apple.com/newsroom/2026/09/siri-ai-a-profoundly-more-capable-and-personal-assistant-is-here/ — Siri AI, a profoundly more capable and personal assistant, is here (docs)
[^c1-9]: https://support.apple.com/en-au/guide/iphone/iph2413db0ab/27/ios/27 — Undo and revert photo edits on iPhone (docs)
[^c1-10]: https://amateurphotographer.com/software/i-put-the-new-iphone-ai-photo-editing-tools-to-the-test-the-results-are-sometimes-downright-weird/ — I put the new iPhone AI photo editing tools to the test (blog)
[^c1-11]: https://support.apple.com/en-lamr/guide/iphone/iph0063238b5/27/ios/27 — Create original images with Image Playground on iPhone (docs)
