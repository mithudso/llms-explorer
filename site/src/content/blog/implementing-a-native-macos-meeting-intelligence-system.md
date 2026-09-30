---
title: "Implementing a Native macOS Meeting-Intelligence System"
description: "A proposed macOS meeting pipeline using Core Audio taps and on-device transcription, with capture permissions, lifecycle handling, and reviewed analysis."
date: "2026-09-07"
order: 17
---

A native macOS pipeline that captures meeting audio, transcribes it on-device, feeds transcripts into a customer context file, and uses that context to track sentiment and surface customer initiatives that were never explicitly named.

Two design choices shape the whole build:

- Apple's `SpeechAnalyzer`/`SpeechTranscriber` stack on macOS 26 is one on-device transcription option. Compare supported languages, accuracy, and latency against Whisper on the recordings you need to handle.
- A **Core Audio process tap** can capture far-end audio without capturing video. Apple's sample requires macOS 14.2 or later; ScreenCaptureKit is another system-audio capture path.

---

## 0\. The shape of the system

```
┌─ Capture (Swift, native) ──────────────┐
│  mic  ──AVAudioEngine tap──┐            │
│                            ├─► mixer ──► ring buffer (PCM)
│  far-end ──CoreAudio tap───┘            │
└──────────────────────────────┬─────────┘
                                ▼
┌─ Transcribe (SpeechAnalyzer) ───────────┐
│  AsyncStream<AnalyzerInput> ─► analyzer  │
│  ◄── results: AttributedString + time ── │
└──────────────────────────────┬──────────┘
                                ▼
┌─ Structure ─────────────────────────────┐
│  utterance records (ts, speaker?, text) │
│  + account resolution                    │
└──────────────────────────────┬──────────┘
                                ▼
┌─ Context file ───────────────────────────┐
│  ──►  mdb_tam_account_context corpus      │
└──────────────────────────────┬───────────┘
                                ▼
┌─ Analyze (FoundationModels / LLM stack) ┐
│  sentiment · risks · action items ·      │
│  mentioned vs. latent projects           │
└──────────────────────────────┬──────────┘
                                ▼
        monday board · case MCP · weekly-update builder
```

Four native layers (capture → transcribe → structure → analyze), then a hand-off into the existing TAM stack.

**One gate before capture: recording authorization.** Requirements depend on participant locations and the circumstances of the call. Have the organization approve the consent and notice workflow for its use case. Store the meeting's authorization record, stop capture if authorization is withdrawn, and define retention and access rules for audio and transcripts. A notice or a Boolean field alone does not establish legal compliance. The local transcription stage and later corpus or cloud-analysis stages have different data destinations.

---

## 1\. Audio capture — and why it is two streams

A meeting has two audio sources that live in different places on macOS:

| Source | What it is | API |
| :---- | :---- | :---- |
| You | your microphone | `AVAudioEngine` input node tap |
| Far end | output from the selected meeting process or processes | Core Audio process tap (Apple sample: macOS 14.2+) |

Recording only the mic captures half the conversation. The far end is system output audio, which `AVAudioEngine` cannot reach; that requires tapping the system audio graph.

### 1a. The microphone

```
import AVFoundation

let engine = AVAudioEngine()
let input = engine.inputNode
let format = input.outputFormat(forBus: 0)

input.installTap(onBus: 0, bufferSize: 4096, format: format) { buffer, time in
    micRingBuffer.write(buffer)   // hand to the mixer/transcriber
}
try engine.start()
```

TCC requirement: add `NSMicrophoneUsageDescription` to Info.plist. The user gets the mic prompt on first run.

### 1b. The far end — Core Audio process taps

Apple's Core Audio sample supports process taps on macOS 14.2 or later. Describe a tap, create it, include it in an aggregate device, and read buffers from that device. Add `NSAudioCaptureUsageDescription` to Info.plist; the first recording from a tap-containing aggregate device prompts for system-audio permission, separately from the microphone permission.

The snippets here illustrate API shape. They omit ring-buffer implementations, conversion helpers, error paths, and concurrency management and have not been compiled as an application.

```
import CoreAudio

// 1. Describe what to tap. Empty process list + global = "everything the system plays."
let tapDescription = CATapDescription(stereoGlobalTapButExcludeProcesses: [])
tapDescription.isPrivate = true          // don't show in other apps' device lists
tapDescription.muteBehavior = .unmuted   // you still want to hear the call

// 2. Create the tap.
var tapID = AudioObjectID(kAudioObjectUnknown)
AudioHardwareCreateProcessTap(tapDescription, &tapID)

// 3. Build an aggregate device that includes the tap in its tap list.
let aggDesc: [String: Any] = [
    kAudioAggregateDeviceNameKey: "MeetingCapture",
    kAudioAggregateDeviceUIDKey: UUID().uuidString,
    kAudioAggregateDeviceIsPrivateKey: true,
    kAudioAggregateDeviceTapAutoStartKey: true,
    kAudioAggregateDeviceTapListKey: [
        [ kAudioSubTapUIDKey: tapDescription.uuid.uuidString ]
    ]
]
var aggDeviceID = AudioObjectID(kAudioObjectUnknown)
AudioHardwareCreateAggregateDevice(aggDesc as CFDictionary, &aggDeviceID)

// 4. Install an IO proc and read PCM buffers out of it.
var procID: AudioDeviceIOProcID?
AudioDeviceCreateIOProcIDWithBlock(&procID, aggDeviceID, ioQueue) {
    _, inInputData, _, _, _ in
    farEndRingBuffer.write(inInputData)   // raw output audio of the call
}
AudioDeviceStart(aggDeviceID, procID)
```

Notes:

- **Capture choice:** this design uses a tap for audio-only capture. The cited Apple tap sample does not establish a universal preference over ScreenCaptureKit or a measured overhead advantage. Validate the permission and capture behavior of the path you choose on supported macOS versions.  
- **The aggregate-device step:** a raw process tap is not an input device you can read from. Wrapping it in an aggregate device makes system output look like a normal capture device to the IO proc.  
- **Lifecycle and errors:** check every `OSStatus` before using the returned object. On stop, stop the device, destroy the IO proc, destroy the aggregate device, and destroy the process tap. Release already-created objects if a later creation step fails. Handle permission denial, selected-process exit, output-device changes, and cancellation.
- **Capture scope:** the empty exclusion list in the sketch captures global output, including unrelated applications. Prefer selected meeting processes when feasible and show the user the recording scope. Keep real-time callbacks short and avoid blocking I/O or model work there.
- **Reference implementations:** Apple's sample and `insidegui/AudioCap` show this sequence; AudioCap's own sample target is macOS 14.4+.

### 1c. Mixing

You now have two ring buffers at possibly different formats. Two strategies:

- **Mix to one stream** (`AVAudioMixerNode` or sum the PCM). This loses the channel distinction; the mixed signal alone does not establish who spoke.  
- **Keep them separate and transcribe each independently.** Record `channel: "local"` versus `channel: "far_end"`. A channel identifies an audio source, not a person: the far end may contain multiple participants, and the local mic may capture other people or speaker bleed. Use `speaker` only when identity has been established separately. Align both streams to a shared meeting clock.

---

## 2\. Transcription with SpeechAnalyzer

`SpeechAnalyzer` is the macOS 26 coordinator; modules attach to it. `SpeechTranscriber` does speech-to-text; `SpeechDetector` flags voice activity. The SpeechTranscriber stage runs on-device. Corpus ingestion and the selected analysis backend determine whether transcripts later leave the machine.

### 2a. Confirm the model assets exist

On-device, but the language model packs may need downloading. Gate on availability and locale, then install:

```
import Speech

let locale = Locale(identifier: "en-US")
guard SpeechTranscriber.isAvailable else { /* unavailable device */ return }
let transcriber = SpeechTranscriber(locale: locale, preset: .offlineTranscription)

guard await SpeechTranscriber.supportedLocales.contains(
        where: { $0.identifier(.bcp47) == "en-US" }) else { /* unsupported */ return }

let installed = await SpeechTranscriber.installedLocales
if !installed.contains(where: { $0.identifier(.bcp47) == "en-US" }) {
    if let req = try await AssetInventory.assetInstallationRequest(
                       supporting: [transcriber]) {
        try await req.downloadAndInstall()     // one-time, ~GB-scale
    }
}
_ = try await AssetInventory.reserve(locale: locale)
// false means this locale was already reserved; either return value can continue.
// Reservation-limit or unsupported-asset failures throw.
// Release the reservation when the app no longer needs this locale.
```

`SpeechTranscriber.isAvailable` plus locale support is the feature gate; "macOS 26" alone is not enough, because the model for a given language may not be installed. Apple's [`reserve(locale:)` contract](https://developer.apple.com/documentation/speech/assetinventory/reserve(locale:)) returns `false` for an already-reserved locale; it does not mean the limit was reached. Handle thrown failures separately, and manage reservation release at the app level so one capture does not release a locale another still needs.

### 2b. The streaming pipeline (live meeting)

```
let transcriber = SpeechTranscriber(
    locale: locale,
    transcriptionOptions: [],
    reportingOptions: [.volatileResults],   // get partials as people speak
    attributeOptions: [.audioTimeRange]      // timestamps per segment
)
let analyzer = SpeechAnalyzer(modules: [transcriber])

// Feed audio. SpeechAnalyzer wants a specific PCM format:
let analyzerFormat = await SpeechAnalyzer.bestAvailableAudioFormat(
                           compatibleWith: [transcriber])
let converter = AVAudioConverter(from: micFormat, to: analyzerFormat)!

let (stream, continuation) = AsyncStream<AnalyzerInput>.makeStream()
try await analyzer.start(inputSequence: stream)

// from your ring-buffer callback:
let converted = convert(buffer, with: converter, to: analyzerFormat)
continuation.yield(AnalyzerInput(buffer: converted))

// consume results concurrently:
for try await result in transcriber.results {
    let text = String(result.text.characters)   // result.text is AttributedString
    if result.isFinal {
        let span = result.range                         // CMTimeRange for the complete result
        store(utterance: text, at: span, speaker: .rep, final: true)
    } else {
        updateLiveCaption(text)                  // volatile / will be revised
    }
}
```

Notes:

- **Volatile vs. final drives the UX:** volatile results stream fast and get retracted or rewritten as more audio arrives (good for a live caption); only `isFinal` results are stable enough to persist. Write final results to disk; render volatile results to the screen.  
- **Negotiate the format:** handle a missing `bestAvailableAudioFormat`, and create a converter only when input and analyzer formats differ. Check conversion errors and reuse converter state across buffers. The snippet force-unwraps for brevity; production code must handle failure.
- **Run feeding and result consumption concurrently:** start a result-consumer task while the analyzer receives audio. On stop, finish the input sequence and finalize through the last sample, or cancel; await cleanup and retain only final results. Bounded queues need an explicit overflow policy and dropped-buffer telemetry.  
- **Store the whole result's time range:** [`result.range`](https://developer.apple.com/documentation/speech/speechmoduleresult/range) covers the complete utterance. An attributed-string run's `.audioTimeRange` covers that run, so use those attributes for word-level alignment or highlighting rather than assigning the first run's range to the whole transcript.

### 2c. Post-hoc / file mode

For a saved recording (or to re-process), skip the live stream:

```
let file = try AVAudioFile(forReading: url)
let analyzer = SpeechAnalyzer(modules: [transcriber])
if let last = try await analyzer.analyzeSequence(from: file) {
    try await analyzer.finalizeAndFinish(through: last)
}
```

The cited third-party tool reports do not establish a speed or accuracy bound for this pipeline. Measure elapsed time relative to audio duration and transcription error on a representative, versioned recording set before sizing a batch backlog. No benchmark of this proposed application is reported here.

### 2d. The honest gap: diarization

`SpeechAnalyzer` does not provide speaker diarization ("Speaker 1 / Speaker 2"). This is the biggest limitation for meeting use. Three options, in order of effort:

1. **Channel-based attribution:** transcribe local and far-end channels separately as in §1c. This preserves source-channel evidence; it does not distinguish several remote speakers or prove their identities.  
2. **Per-participant audio:** if the meeting platform exposes per-speaker streams (some Zoom/Teams setups do), tap those.  
3. **A diarization model on top:** run `pyannote` or `sherpa-onnx` over the mixed audio to segment speakers, then align by timestamp. Heavier, with more failure modes; use only if you need multi-speaker resolution on the customer side.

---

## 3\. Transcript to the customer context file

This layer turns transcription into a TAM asset. Two decisions matter: the record schema and where it lives.

### 3a. Record schema

Store utterances, not a blob. JSONL appended per meeting:

```
{ "account_id": "acme-corp",
  "meeting_id": "2026-06-17T14:00-acme-qbr",
  "consent": { "obtained": true, "method": "verbal", "ts": "..." },
  "ts_start": 312.40, "ts_end": 318.10,
  "channel": "far_end",            // audio source, not speaker identity
  "speaker": null,                  // resolve separately when supported
  "text": "we're still nervous about the failover story for the EU cluster",
  "final": true }
```

Then a per-account rollup in Markdown with front-matter, the context file a human or model reads:

```
---
account: Acme Corp
last_meeting: 2026-06-17
sentiment_trend: [0.2, 0.1, -0.3]   # last 3 touchpoints
open_risks: ["EU failover confidence", "renewal Q3"]
---
## Rolling summary
...
## Per-meeting log
- 2026-06-17 QBR — sentiment -0.3, raised EU failover ...
```

Notes:

- **Append raw, derive summaries.** Keep the immutable utterance log as source of truth; regenerate the rollup. If a model summarizes incorrectly, regenerate from the retained log. The transcript itself can still contain recognition errors.  
- **`account_id` resolution is a real subproblem.** Map calendar invite to attendee domains to account. Wrong attribution silently corrupts the wrong customer's file, so make it explicit and reviewable rather than implicit.

### 3b. Wire into the existing corpus

The `mdb_tam_account_context` corpus already exists, with `corpus_search`/`corpus_query`/`corpus_get` and `report_run`. The native app's job ends at producing a clean utterance record; ingestion pushes into that corpus as a new collection (for example `meeting_transcripts`) keyed by account. Existing `tam-weekly-update-builder` and `account-data-collector` agents then consume meeting transcripts as another evidence source alongside cases and Slack.

This is the difference between a standalone gadget and something that compounds with the existing stack. The Granola path in `references/granola-transcription.md` is the existing template for this corpus-wiring (polling sync, dedup, 401/403/429 handling) — review it before designing the ingestion, since the same problem shape is already solved there.

---

## 4\. Sentiment and surfacing latent projects

Two analytical jobs. Both can use the macOS 26 Foundation Models framework when its model is available on the device, or route to the existing LLM stack. Check model availability, context limits, and the selected backend's data destination. Local analysis alone does not make a remotely stored corpus local.

### 4a. Structured extraction (sentiment, risks, action items)

```
import FoundationModels

@Generable struct MeetingAnalysis {
    @Guide(description: "overall customer sentiment, -1.0 to 1.0")
    var sentiment: Double
    @Guide(description: "explicit risks or concerns the customer raised")
    var risks: [String]
    @Guide(description: "commitments or follow-ups, with owner")
    var actionItems: [String]
    @Guide(description: "MongoDB/Atlas topics the customer mentioned")
    var topicsMentioned: [String]
}

let session = LanguageModelSession(instructions: """
    You analyze TAM customer-meeting transcripts. Be conservative;
    do not invent concerns the customer did not voice.
    """)
let result = try await session.respond(
    to: transcriptText, generating: MeetingAnalysis.self).content
```

Guided generation constrains output structure; it does not prove factual accuracy or enforce a numeric range expressed only in a description. Validate ranges, verify quoted evidence against utterance IDs, and test long-transcript chunking and failures. Treat sentiment as a model estimate; do not call it a calibrated churn-risk signal without outcome data.

### 4b. Surfacing projects that were not explicitly mentioned

This is inference, and it concentrates both the value and the risk. A customer says "the EU cluster failover makes us nervous." Nobody said "disaster recovery project" or "multi-region architecture review," but those are the latent initiatives implied. The mechanism:

1. **Entity-link** what was said against the account corpus (open cases, monday initiatives, prior meeting topics, the account's architecture).  
2. **Gap-detect:** find adjacent initiatives the conversation implies but no one named — a failover concern implies a DR/HA review; repeated latency complaints imply an index/schema engagement; "our team is growing" implies an enablement or MongoDB University path.  
3. **Rank by signal strength** and emit as suggestions with evidence quotes, never as asserted fact.

```
@Generable struct LatentOpportunity {
    @Guide(description: "an initiative implied but NOT explicitly named by the customer")
    var initiative: String
    @Guide(description: "the verbatim quote that implies it")
    var evidence: String
    @Guide(description: "confidence 0-1 that this is real, not inferred noise")
    var confidence: Double
}
```

Notes:

- **This is a recommendation system, not a fact extractor — keep the two separate.** Sentiment and action items are grounded in what was said; latent projects are speculation. Mixing them lets a hallucinated "project" get logged as if the customer requested it. Attach the exact quote and utterance ID, label the initiative as inferred, and route inferred opportunities to human review before board creation. A model-written confidence score is not calibrated probability; review thresholds require validation.  
- **The `harsh-reviewer` and `tam-doc-validator` agents are the natural guardrail**: fact-check the generated analysis against the corpus before anything customer-facing or board-bound is created.

### 4c. Closing the loop into action

The analysis becomes TAM motion: create monday items for latent opportunities (gated, human-approved), attach risks to the account's health score, drop action items into the task MCP, and let `tam-weekly-update-builder` fold the sentiment trend into the next update. Verify the generated claims before publishing it.

---

## 5\. How the pieces run

- **A menubar Swift app** owns capture and transcription. It can call the native audio APIs and write utterance JSONL to a controlled directory. Prototype the intended sandbox, entitlements, permissions, and signing configuration before choosing distribution. The cited sources do not establish a blanket Mac App Store prohibition for system-audio capture, and this design has not passed an App Store or sandbox validation.  
- **A small local ingestion daemon** (Node or Python) watches that directory, resolves the account, and pushes records into the `mdb_tam_account_context` corpus, reusing the Granola ingestion pattern.  
- **Analysis** runs either in-app (Foundation Models) or in the daemon against the LLM stack, writing the rollup and structured analysis back to the corpus.  
- **The existing agents and MCPs** consume the corpus. You do not build the TAM brain — you feed the one already in place.

---

## 6\. Build order

1. **Spike the Core Audio tap** against `insidegui/AudioCap` to prove far-end audio capture works. This is the riskiest piece; if it does not work, nothing downstream matters.  
2. **Wire `SpeechAnalyzer`** on a saved WAV (file mode, section 2c) before going live; file input is easier to debug.  
3. **Two-channel live capture** with channel-based speaker tags.  
4. **Utterance JSONL plus corpus ingestion** (clone the Granola pattern).  
5. **Structured analysis** (sentiment and risks first; latent-opportunity inference last, behind the human-review gate).

---

## Sources

- [Capturing system audio with Core Audio taps (Apple)](https://developer.apple.com/documentation/CoreAudio/capturing-system-audio-with-core-audio-taps)  
- [insidegui/AudioCap](https://github.com/insidegui/AudioCap)  
- [Bring advanced speech-to-text to your app with SpeechAnalyzer — WWDC25](https://developer.apple.com/videos/play/wwdc2025/277/)  
- [On-Device Speech Transcription with Apple SpeechAnalyzer (Callstack)](https://www.callstack.com/blog/on-device-speech-transcription-with-apple-speechanalyzer)  
- [How Apple's New Speech APIs Outpace Whisper (MacStories)](https://www.macstories.net/stories/hands-on-how-apples-new-speech-apis-outpace-whisper-for-lightning-fast-transcription/)  
- [FluidInference/swift-scribe](https://github.com/FluidInference/swift-scribe)
