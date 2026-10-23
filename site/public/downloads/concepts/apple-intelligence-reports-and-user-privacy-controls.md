<!-- llms-explorer concept facts · https://llms-explorer.com/tree/apple-intelligence-reports-and-user-privacy-controls/ · pack 2026-10-23 · ~1275 tokens -->

# Apple Intelligence Reports and user privacy controls

> Source-anchored research for Apple Intelligence Reports and user privacy controls. Run status: COMPLETED.

Parent: [Private Cloud Compute trust architecture and verification](https://llms-explorer.com/tree/private-cloud-compute-trust-architecture-and-verification/) · 5 facets · 9 facts · page: https://llms-explorer.com/tree/apple-intelligence-reports-and-user-privacy-controls/

## Structure and components

- Apple Intelligence Report modelRequests entries can expose timestamps and request identifiers, prompt and response text, model and modelVersion, clientIdentifier, and executionEnvironment; observed schemas may also include useCase. Prompt and response fields can contain personal content, so handle the exported JSON as sensitive. (high confidence) (verified as of 2026-09-22) — [source](https://eclecticlight.co/2026/09/22/read-an-apple-intelligence-report/)
- Some privateCloudComputeRequests content consists of encoded attestation bundles. Independent analysis describes those blocks as difficult to interpret in an ordinary text or JSON reader, so the export is not a plain-language explanation of every processing detail. (high confidence) (verified as of 2026-09-22) — [source](https://eclecticlight.co/2026/09/22/read-an-apple-intelligence-report/)

## How it works

- Apple describes the report as a record of requests sent to Private Cloud Compute and warns that it can be empty when no PCC requests occurred since the duration changed. 9to5Mac reported empty seven-day exports in its 2025 checks, while Daring Fireball found that Writing Tools Proofread produced no entry but Summarize produced a PCC entry. An empty export therefore does not prove that Apple Intelligence was unused; it can reflect the chosen capture window and which tasks reached PCC. (medium confidence) (verified as of 2026-10-23) — [source](https://support.apple.com/en-us/guide/iphone/iphe3f499e0e/ios)
- Apple Support says the report covers PCC requests and may be empty when no PCC request occurred since the duration changed. A separate schema analysis says modelRequests can include both OnDevice and PrivateCloudCompute entries, while a macOS analysis reports that on-device interactions appear in the unified log. Given this scope conflict, an empty export is evidence only about entries in the selected report window; it does not establish that no Apple Intelligence activity occurred outside that window or that no on-device processing occurred. (medium confidence) (verified as of 2026-10-22) — [source](https://support.apple.com/guide/iphone/apple-intelligence-and-privacy-iphe3f499e0e/ios)

## Problems, failure modes and limitations

- A July 2026 parser feasibility study says the exported JSON itself is unsigned and cannot prove that the device recorded activity completely or truthfully. It says some included PCC evidence can be checked against transparency records, but that does not establish that the device omitted no activity. (low confidence) (verified as of 2026-07-05) — [source](https://github.com/NagaYu/pcc-verify/blob/main/docs/FEASIBILITY.md)

## Comparisons and alternatives

- Published report samples indicate that the exported JSON can expose sensitive request content. AppleInsider's iOS 18.1 inspection described timestamps, request identifiers, optional task text, and software-component details; a July 2026 parser study lists prompt and response fields in modelRequests, and a September 2026 guide also describes those fields. Treat the export as potentially sensitive, and treat its exact fields as version-specific rather than a stable public schema. (medium confidence) (verified as of 2026-09-24) — [source](https://appleinsider.com/inside/ios-18/tips/how-to-read-the-apple-intelligence-report-in-ios-181/amp/)
- The Off choice disables the report setting, not Apple Intelligence itself: Apple's guides label it as turning off the report, and a September 2026 field guide says requests may still go to PCC when features need it. Users should read Off as stopping report capture rather than stopping Apple Intelligence processing. (medium confidence) (verified as of 2026-10-23) — [source](https://support.apple.com/en-us/guide/iphone/iphe3f499e0e/ios)

## Facts and statements

- Apple's current iOS 27 and macOS 27 user guides direct users to Privacy & Security > Apple Intelligence Report, allow a last-15-minutes window (the default), a last-7-days window, or Off, and say Export Activity saves Apple_Intelligence_Report.json to a location the user chooses. (high confidence) (verified as of 2026-10-23) — [source](https://support.apple.com/en-us/guide/iphone/iphe3f499e0e/ios)
- In a 2025-03-17 report about iOS 18.1 and macOS 15.1 beta, 9to5Mac said its staff found empty seven-day reports and offered low feature use or on-device handling as explanations; that sample was historical and does not establish behavior for current OS releases. (low confidence) (verified as of 2025-03-17) — [source](https://9to5mac.com/2025/03/17/our-apple-intelligence-privacy-reports-are-empty-how-about-yours-poll/)
