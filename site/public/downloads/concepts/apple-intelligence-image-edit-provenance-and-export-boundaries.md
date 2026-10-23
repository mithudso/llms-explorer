<!-- llms-explorer concept facts · https://llms-explorer.com/tree/apple-intelligence-image-edit-provenance-and-export-boundaries/ · pack 2026-10-23 · ~1197 tokens -->

# Apple Intelligence image edit provenance and export boundaries

> Source-anchored research for Apple Intelligence image edit provenance and export boundaries. Run status: COMPLETED.

Parent: [Intelligent Photos editing and memory workflows](https://llms-explorer.com/tree/intelligent-photos-editing-and-memory-workflows/) · 4 facets · 10 facts · page: https://llms-explorer.com/tree/apple-intelligence-image-edit-provenance-and-export-boundaries/

## How it works

- Apple's WWDC26 camera/photo engineers state that AI edits such as Clean Up and Spatial Reframe update IPTC metadata in the file alongside EXIF, and that Photos Info displays which edit was used. This is a metadata disclosure mechanism; the answer does not establish a signed C2PA edit history. (low confidence) (verified as of 2026-06-12) — [source](https://developer.apple.com/videos/play/wwdc2026/8018/)
- Google's current SynthID page offers a public Detector portal for supported images, video and audio, and separately describes checking Google AI media through Gemini, Search and Chrome. Because the same page lists Apple as coming soon, access to a detector is not evidence of validated Apple export detection. (low confidence) (verified as of 2026-10-23) — [source](https://deepmind.google/models/synthid/)

## Problems, failure modes and limitations

- The 2025 forensic author changed both Credit and Digital Source Type and observed the Clean Up/AI label disappear when the edited file was opened in Photos. Consequently, absence of that metadata-driven label alone cannot authenticate an image as unedited. (low confidence) — [source](https://www.malwr4n6.com/post/apple-intelligence-photo-forensics)

## Comparisons and alternatives

- Postcue reports that the Clean Up label survives iMessage and AirDrop but disappears through some third-party apps. Its page labels the behavior reported rather than vendor-confirmed and supplies no current iOS 27 destination-by-destination test matrix, so this is a lead for validation rather than a universal export rule. (low confidence) (verified as of 2026-10-23) — [source](https://postcue.ai/tools/apple-photos-clean-up)

## Facts and statements

- Apple's September 14, 2026 announcement describes SynthID support for Apple Intelligence image generation and editing as upcoming. Its footnote says a software update later in 2026 will cover most edited images depending on the edits applied. Google’s current SynthID page also lists Apple as coming soon. These sources do not establish universal or already-shipped Apple watermarking. (high confidence) (verified as of 2026-09-14) — [source](https://www.apple.com/newsroom/2026/09/siri-ai-a-profoundly-more-capable-and-personal-assistant-is-here/)
- SynthID embeds an imperceptible signal in image content, whereas IPTC/EXIF labels are file metadata. Google designs the signal to tolerate operations including cropping, filtering and lossy compression. That design statement is not an Apple-specific guarantee that every export or share preserves detection. (medium confidence) — [source](https://deepmind.google/models/synthid/)
- In a forensic experiment updated March 18, 2025, malwr4n6 found Clean Up output with Credit set to Apple Photos Clean Up and Digital Source Type set to compositeWithTrainedAlgorithmicMedia. IPTC defines that source-type category for generative edits such as inpainting or outpainting; it does not mean the entire image was generated from scratch. (medium confidence) — [source](https://www.malwr4n6.com/post/apple-intelligence-photo-forensics)
- The same 2025 forensic experiment observed that Clean Up output lost camera make/model and location metadata. This is an observation from the author's exported sample, not a demonstrated privacy or export rule for every iOS 27 workflow. (low confidence) — [source](https://www.malwr4n6.com/post/apple-intelligence-photo-forensics)
- Photos retains a route back to the original: Apple's iOS 27 guide provides Revert to Original after saving, and Amateur Photographer's September 30, 2026 hands-on review describes the AI editing tools as non-destructive. This in-library recovery does not demonstrate that a shared rendered image includes the original or a reversible edit history. (high confidence) (verified as of 2026-09-30) — [source](https://support.apple.com/en-au/guide/iphone/iph2413db0ab/27/ios/27)
- The iOS 27 Image Playground guide describes automatically saved gallery versions, continued editing from an earlier version, and share/copy controls. It makes no promise in those instructions that recipient files include the gallery's version history or that all provenance markers survive sharing. (low confidence) (verified as of 2026-10-22) — [source](https://support.apple.com/en-lamr/guide/iphone/iph0063238b5/27/ios/27)
