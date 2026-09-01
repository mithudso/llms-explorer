# Implementing a Native macOS Meeting-Intelligence System

A native macOS pipeline that captures meeting audio, transcribes it on-device, feeds transcripts into a customer context file, and uses that context to track sentiment and surface customer initiatives that were never explicitly named.

Two design choices shape the whole build:

- Apple's modern transcription stack (`SpeechAnalyzer`/`SpeechTranscriber`, macOS 26\) is now better than bolting in Whisper.  
- On macOS 14.4+, a **Core Audio process tap** is the correct way to capture the meeting's far-end audio, not ScreenCaptureKit.

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

**One gate before any of it — consent.** Recording customers carries jurisdictional legal requirements. Federal US and roughly 38 states allow one-party consent, but California, Florida, Washington, Illinois, and others require all-party consent. Meeting-notes tools (Granola, Gong, Otter) handle this by announcing themselves or requiring a setting. Practical rule: build a spoken or visible "this call is being recorded for notes" step into the workflow, store an explicit consent flag per meeting, and keep audio and transcripts inside a controlled corpus rather than a third-party cloud. This is not legal advice; it is the same posture the commercial tools adopt. Treat consent as a required field in the data model, not an afterthought.

---

## 1\. Audio capture — and why it is two streams

A meeting has two audio sources that live in different places on macOS:

| Source | What it is | API |
| :---- | :---- | :---- |
| You | your microphone | `AVAudioEngine` input node tap |
| Them | the far-end audio coming out of Zoom/Meet/Teams \= system output | Core Audio process tap (macOS 14.4+) |

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

Since macOS 14.4, a public Core Audio API can tap a process's (or the whole system's) output. The flow: describe a tap, create it, wrap it in an aggregate device, then pull buffers from that device.

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

- **Why a tap and not ScreenCaptureKit:** ScreenCaptureKit can deliver audio, but it starts the screen-capture machinery (and a screen-recording TCC prompt) for audio a Core Audio tap delivers directly. Apple's guidance: if you are not capturing the screen, use a Core Audio tap. Lower overhead, less alarming permission prompt.  
- **The aggregate-device step:** a raw process tap is not an input device you can read from. Wrapping it in an aggregate device makes system output look like a normal capture device to the IO proc.  
- **Reference implementation:** `insidegui/AudioCap` is the canonical worked example of this sequence, including the TCC permission check for audio capture.

### 1c. Mixing

You now have two ring buffers at possibly different formats. Two strategies:

- **Mix to one stream** (`AVAudioMixerNode` or sum the PCM) — simplest, but loses who-said-what.  
- **Keep them separate and transcribe each independently** — tag every utterance `speaker: "rep"` vs `speaker: "customer"` from the channel it came from. This is the recommended approach: it is the cheapest reliable speaker attribution available (see section 2d on why native diarization will not cover this).

---

## 2\. Transcription with SpeechAnalyzer

`SpeechAnalyzer` is the macOS 26 coordinator; modules attach to it. `SpeechTranscriber` does speech-to-text; `SpeechDetector` flags voice activity. It runs fully on-device, so audio never leaves the machine.

### 2a. Confirm the model assets exist

On-device, but the language model packs may need downloading. Gate on availability and locale, then install:

```
import Speech

let locale = Locale(identifier: "en-US")
let transcriber = SpeechTranscriber(locale: locale)   // minimal instance for the asset check; see 2b for full pipeline config

guard await SpeechTranscriber.supportedLocales.contains(
        where: { $0.identifier(.bcp47) == "en-US" }) else { /* unsupported */ return }

let installed = await SpeechTranscriber.installedLocales
if !installed.contains(where: { $0.identifier(.bcp47) == "en-US" }) {
    if let req = try await AssetInventory.assetInstallationRequest(
                       supporting: [transcriber]) {
        try await req.downloadAndInstall()     // one-time, ~GB-scale
    }
}
try await AssetInventory.reserve(locale: locale)   // keep assets from being reaped
```

`SpeechTranscriber.isAvailable` plus locale support is the real feature gate — "macOS 26" alone is not enough, because the model for a given language may not be installed.

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
        let span = result.text.runs.first?.audioTimeRange   // CMTimeRange (illustrative attribute access)
        store(utterance: text, at: span, speaker: .rep, final: true)
    } else {
        updateLiveCaption(text)                  // volatile / will be revised
    }
}
```

Notes:

- **Volatile vs. final drives the UX:** volatile results stream fast and get retracted or rewritten as more audio arrives (good for a live caption); only `isFinal` results are stable enough to persist. Write final results to disk; render volatile results to the screen.  
- **Format negotiation is mandatory:** feeding the wrong PCM format silently produces garbage. Always ask for `bestAvailableAudioFormat` and run an `AVAudioConverter`. This is the most common "it transcribes nothing" bug.  
- **`.audioTimeRange` is what makes the transcript useful later:** without per-segment timestamps you cannot align the two channels, jump back to the audio, or build a timeline. Enable it from the start.

### 2c. Post-hoc / file mode

For a saved recording (or to re-process), skip the live stream:

```
let file = try AVAudioFile(forReading: url)
let analyzer = SpeechAnalyzer(modules: [transcriber])
if let last = try await analyzer.analyzeSequence(from: file) {
    try await analyzer.finalizeAndFinish(through: last)
}
```

Independent benchmarks of a SpeechAnalyzer-based command-line tool report roughly 2.2x faster-than-realtime transcription on Apple Silicon versus comparable tools, with no noticeable quality loss, so batch re-processing a backlog of meetings is inexpensive.

### 2d. The honest gap: diarization

`SpeechAnalyzer` does not provide speaker diarization ("Speaker 1 / Speaker 2"). This is the biggest limitation for meeting use. Three options, in order of effort:

1. **Channel-based attribution (recommended):** the section 1c approach, transcribing mic and far-end separately. This yields rep-vs-customer attribution for free, which covers most of what a TAM needs.  
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
  "speaker": "customer",            // from the channel, section 1c
  "text": "we're still nervous about the failover story for the EU cluster",
  "final": true }
```

Then a per-account rollup in Markdown with front-matter — the context file a human or model reads:

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

- **Append raw, derive summaries.** Keep the immutable utterance log as source of truth; regenerate the rollup. If a model summarizes incorrectly, re-derive — the ground truth is never lost.  
- **`account_id` resolution is a real subproblem.** Map calendar invite to attendee domains to account. Wrong attribution silently corrupts the wrong customer's file, so make it explicit and reviewable rather than implicit.

### 3b. Wire into the existing corpus

The `mdb_tam_account_context` corpus already exists, with `corpus_search`/`corpus_query`/`corpus_get` and `report_run`. The native app's job ends at producing a clean utterance record; ingestion pushes into that corpus as a new collection (for example `meeting_transcripts`) keyed by account. Existing `tam-weekly-update-builder` and `account-data-collector` agents then consume meeting transcripts as another evidence source alongside cases and Slack.

This is the difference between a standalone gadget and something that compounds with the existing stack. The Granola path in `references/granola-transcription.md` is the existing template for this corpus-wiring (polling sync, dedup, 401/403/429 handling) — review it before designing the ingestion, since the same problem shape is already solved there.

---

## 4\. Sentiment and surfacing latent projects

Two analytical jobs. Both can run on-device with the macOS 26 Foundation Models framework — keeping customer data local — or route to the existing LLM stack.

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

Guided generation (`@Generable`/`@Guide`) forces typed output, avoiding JSON-parsing failures. Track `sentiment` over time to build the `sentiment_trend` and a churn-risk signal that feeds the health-scoring in the `tam-operations` flows.

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

- **This is a recommendation system, not a fact extractor — keep the two separate.** Sentiment and action items are grounded in what was said; latent projects are speculation. Mixing them lets a hallucinated "project" get logged as if the customer requested it. Always attach the evidence quote and a confidence score, and route low-confidence items to a human review queue rather than straight to the monday board.  
- **The `harsh-reviewer` and `tam-doc-validator` agents are the natural guardrail** — fact-check the generated analysis against the corpus before anything customer-facing or board-bound is created.

### 4c. Closing the loop into action

The analysis becomes TAM motion: create monday items for latent opportunities (gated, human-approved), attach risks to the account's health score, drop action items into the task MCP, and let `tam-weekly-update-builder` fold the sentiment trend into the next update — already fact-checked and in a human voice.

---

## 5\. How the pieces run

- **A menubar Swift app** owns capture and transcription. It must be native for the audio APIs and to keep audio on-device, and it writes utterance JSONL to a watched directory. Plan the distribution model early: Core Audio process taps and system-audio capture do not work under App Store sandboxing, so ship this app directly with a Developer ID signature rather than through the Mac App Store.  
- **A small local ingestion daemon** (Node or Python) watches that directory, resolves the account, and pushes records into the `mdb_tam_account_context` corpus, reusing the Granola ingestion pattern.  
- **Analysis** runs either in-app (Foundation Models) or in the daemon against the LLM stack, writing the rollup and structured analysis back to the corpus.  
- **The existing agents and MCPs** consume the corpus. You do not build the TAM brain — you feed the one already in place.

---

## 6\. Build order

1. **Spike the Core Audio tap** against `insidegui/AudioCap` to prove far-end audio capture works. This is the riskiest piece; if it does not work, nothing downstream matters.  
2. **Wire `SpeechAnalyzer`** on a saved WAV (file mode, section 2c) before going live — easier to debug.  
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