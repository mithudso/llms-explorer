---
title: "Voice & Real-Time Agent Design (2024–2026)"
description: "> Scope note: This report covers the application / design layer of voice agents — architecture choices, real-time APIs, turn-taking, latency engineering, orchestration frameworks, components, UX, and"
---

# Voice & Real-Time Agent Design (2024–2026): Research Report

*Generated: 2026-05-31 | Sources: 32 | Overall confidence: High (with Low-confidence pockets noted inline)*

> Scope note: This report covers the **application / design layer** of voice agents — architecture choices, real-time APIs, turn-taking, latency engineering, orchestration frameworks, components, UX, and evaluation. Model-internal speech architecture (Whisper encoders, the Thinker–Talker decomposition, audio tokenization) is deliberately out of scope and is covered by the existing `multimodal-llm-architecture` reference. Cross-reference that reference for "how the model produces audio"; this report is "how you build and operate a voice product around such models."

---

## Overview

A voice agent is a real-time conversational system that listens, reasons, and speaks back inside a turn-taking loop tight enough to feel human. The dominant 2024–2026 design tension is **cascaded** pipelines (STT → LLM → TTS as discrete, swappable stages) versus **speech-native / speech-to-speech (S2S)** models (one model that ingests and emits audio directly, e.g., OpenAI's `gpt-realtime` and Google's Gemini Live API). Cascaded wins on control, debuggability, compliance, and provider choice; S2S wins on latency and emotional prosody but is hard to audit and gate ([Coval](https://www.coval.ai/blog/speech-to-speech-vs-cascaded-voice-ai-which-architecture-should-you-deploy), [Speko](https://speko.ai/blog/s2s-vs-cascaded), [Hamming](https://hamming.ai/blog/are-speech-to-speech-models-ready-to-replace-cascade-models)).

As of mid-2026, **most production voice agents still use cascaded architectures**, with S2S adoption projected below 15% in H1 2026 and rising to roughly 25–30% by end of H2 2026 as evaluation tooling and compliance frameworks mature ([Coval](https://www.coval.ai/blog/speech-to-speech-vs-cascaded-voice-ai-which-architecture-should-you-deploy)). The engineering north star is a **voice-to-voice latency budget under 800 ms**, and the field has converged on streaming everything, semantic turn detection, and first-class barge-in as the table-stakes pattern ([Hamming](https://hamming.ai/resources/voice-ai-latency-whats-fast-whats-slow-how-to-fix-it), [Smallest.ai](https://smallest.ai/blog/designing-voice-assistants-stt-llm-tts-tools-and-latency-budget)).

---

## Core Concepts

### 1. Architecture: Cascaded vs. Speech-Native (S2S)

**Cascaded** = an orchestration layer coordinating specialized services: VAD → streaming STT → LLM → streaming TTS ([Softcery](https://softcery.com/lab/ai-voice-agents-real-time-vs-turn-based-tts-stt-architecture)). **S2S** = a single model that "processes the entire exchange in a single latent space with no intermediate representations" ([Speko](https://speko.ai/blog/s2s-vs-cascaded)).

Trade-off summary (confidence: **High** — multiple independent sources agree):

| Dimension | Cascaded | Speech-to-Speech |
|---|---|---|
| Voice-to-voice latency | ~800 ms–2 s (compounding) | 200–300 ms; ~85% reduction vs. non-streaming cascade ([Coval](https://www.coval.ai/blog/speech-to-speech-vs-cascaded-voice-ai-which-architecture-should-you-deploy)) |
| Control / business-logic injection | Strong — text intermediary for filters, audit trails, fallbacks | Weak — "model generates audio directly" before any compliance check ([Coval](https://www.coval.ai/blog/speech-to-speech-vs-cascaded-voice-ai-which-architecture-should-you-deploy)) |
| Debuggability | Isolate failures per stage (STT vs. LLM vs. TTS) | Opaque — "you can't easily determine why" output is poor ([Coval](https://www.coval.ai/blog/speech-to-speech-vs-cascaded-voice-ai-which-architecture-should-you-deploy)) |
| Provider flexibility | 5+ STT, 7+ TTS, dozens of LLMs ([Speko](https://speko.ai/blog/s2s-vs-cascaded)) | Effectively OpenAI + Google only |
| Emotional prosody | Lost at text boundary | Preserved (no speech→text→speech round-trip) ([Coval](https://www.coval.ai/blog/speech-to-speech-vs-cascaded-voice-ai-which-architecture-should-you-deploy)) |
| Reasoning / complex tool-calling | Stronger (text for function calls) | Lags; "complex tool-calling workflows need text" ([Coval](https://www.coval.ai/blog/speech-to-speech-vs-cascaded-voice-ai-which-architecture-should-you-deploy)) |
| Cost | Predictable ~$0.0095–$0.17/min ([Speko](https://speko.ai/blog/s2s-vs-cascaded)) | Wide spread $0.00165–$0.30/min |

**When to use which:** S2S for premium/empathetic experiences (mental-health, coaching, luxury, multilingual); cascaded for high-volume tier-1 support, regulated industries, and complex tool-driven workflows ([Coval](https://www.coval.ai/blog/speech-to-speech-vs-cascaded-voice-ai-which-architecture-should-you-deploy)). A **streaming cascade** (Deepgram + GPT-4o-mini + Cartesia) can already hit sub-1-second latency, narrowing S2S's main advantage ([Speko](https://speko.ai/blog/s2s-vs-cascaded)).

### 2. Real-Time APIs

**OpenAI Realtime API** graduated to GA in 2025 with the `gpt-realtime` S2S model (GA snapshot `gpt-realtime-2025-08-28`, 32,768-token context, 4,096 max output) ([OpenAI Realtime blog](https://developers.openai.com/blog/realtime-api), [OpenAI docs](https://developers.openai.com/api/docs/guides/realtime)). Key design facts:

- **Transport:** WebRTC is recommended for *client* media (browser/mobile) for "more consistent performance"; WebSockets for *server* media pipelines (phone calls, broadcast ingest) ([OpenAI docs](https://platform.openai.com/docs/guides/realtime-webrtc), [webrtcHacks](https://webrtchacks.com/how-openai-does-webrtc-in-the-new-gpt-realtime/)). WebRTC sessions use the new `https://api.openai.com/v1/realtime/calls` endpoint.
- **Auth:** Ephemeral client secrets via `POST /v1/realtime/client_secrets` keep permanent keys off the client; the GA interface drops the `OpenAI-Beta: realtime=v1` header ([OpenAI Realtime blog](https://developers.openai.com/blog/realtime-api)).
- **Sessions:** Configured via `session.update` (instructions, turn-detection mode, truncation) ([OpenAI Realtime blog](https://developers.openai.com/blog/realtime-api)).
- **Tool use / function calling:** Keep tools and business logic **server-side** via a **sideband control channel** — two connections to one session (one client, one server); the server monitors, updates instructions, and answers tool calls. GA adds **asynchronous function calling** with automatic placeholder responses ("I'm still waiting on that") to suppress hallucination during pending calls ([OpenAI Realtime blog](https://developers.openai.com/blog/realtime-api), [OpenAI server-controls docs](https://platform.openai.com/docs/guides/realtime-server-controls)).

**Gemini Live API** (GA on Vertex AI) is built on **Gemini 2.5 Flash Native Audio** — raw audio through a single low-latency model, with 30 HD voices in 24 languages, emotion-aware responses, live speech-to-speech translation, and tool use (function calling + Google Search) ([Google Cloud blog](https://cloud.google.com/blog/topics/developers-practitioners/how-to-use-gemini-live-api-native-audio-in-vertex-ai), [Gemini Live API docs](https://ai.google.dev/gemini-api/docs/live-api/capabilities), [blog.google](https://blog.google/products/gemini/gemini-audio-model-updates/)). It is multimodal — agents can converse about live visual streams (charts, video) alongside spoken input ([Google Cloud blog](https://cloud.google.com/blog/topics/developers-practitioners/how-to-use-gemini-live-api-native-audio-in-vertex-ai)).

### 3. Turn Detection, Endpointing, and Barge-In

The hardest UX problem in voice agents is knowing **when the user is done speaking** and **letting them interrupt**. Three layers, increasing in sophistication ([LiveKit](https://livekit.com/blog/turn-detection-voice-agents-vad-endpointing-model-based-detection), [LiveKit docs](https://docs.livekit.io/agents/logic/turns/)):

- **VAD (server VAD):** Classifies each audio frame as speech/non-speech in real time (Silero VAD is the widely-used reference model). Cheap but dumb — it only sees energy, not meaning ([LiveKit](https://livekit.com/blog/turn-detection-voice-agents-vad-endpointing-model-based-detection)).
- **Endpointing:** Uses a silence-timeout on top of VAD to declare end-of-turn. The core latency trap: "A silence timeout set to 800 ms adds nearly a full second to every single response before the pipeline even starts" ([LiveKit](https://livekit.com/blog/turn-detection-voice-agents-vad-endpointing-model-based-detection)).
- **Semantic / model-based turn detection:** Reads the partial transcript and infers whether sentence structure is complete. "Can trigger before trailing silence occurs, which is the main latency advantage," letting silence thresholds drop to **200–300 ms** without raising false interruptions ([LiveKit](https://livekit.com/blog/turn-detection-voice-agents-vad-endpointing-model-based-detection), [appinventiv](https://appinventiv.com/blog/why-ai-voice-agents-fail/)). OpenAI exposes both **Server VAD** and **Semantic VAD** modes ([OpenAI VAD docs](https://developers.openai.com/api/docs/guides/realtime-vad)); Azure offers a noise-resilient **Semantic VAD** ([Microsoft](https://techcommunity.microsoft.com/blog/healthcareandlifesciencesblog/configuring-noise-detection-and-barge%E2%80%91in-with-azure-voice-live-api/4506916)).

Two persistent VAD-only failure modes: **false positives** (pauses/hesitations read as turn ends) and **delayed responses** (strict silence thresholds stall replies after the user is semantically done) ([LiveKit](https://livekit.com/blog/turn-detection-voice-agents-vad-endpointing-model-based-detection), [SkyScribe](https://www.sky-scribe.com/en/blog/ai-voice-recognition-barge-in-turn-taking-and-vad)).

**Model-integrated turn detection** is the 2026 frontier: **Deepgram Flux** is a "conversational speech recognition" model with first-of-its-kind model-integrated end-of-turn detection, detecting end-of-turns in **~260 ms** (median <300 ms, p95 ~1.5 s) at Nova-3 accuracy — collapsing ASR + VAD + endpointing into one model ([Deepgram Flux intro](https://deepgram.com/learn/introducing-flux-conversational-speech-recognition), [Deepgram Flux docs](https://developers.deepgram.com/docs/flux/quickstart)).

**Barge-in (interruption):** Keep the turn-detection layer active even while the agent is speaking; on detected user speech, **cancel the current TTS stream and hand control back to STT immediately**. Echo cancellation runs client-side; **push-to-talk** is the fallback for devices lacking echo cancellation ([LiveKit](https://livekit.com/blog/turn-detection-voice-agents-vad-endpointing-model-based-detection), [futureagi](https://futureagi.com/blog/voice-ai-barge-in-turn-taking-2026/)). **Backchanneling** ("mm-hm", "yeah") is the subtle case: pure VAD misreads backchannels as either silence or a full barge-in, so the 2026 stack moves to **dedicated turn-taking models that classify backchannel vs. barge-in as a learned signal** ([appinventiv](https://appinventiv.com/blog/why-ai-voice-agents-fail/), [DEV/Mishra](https://dev.to/deepak_mishra_35863517037/the-art-of-interruption-vad-strategies-for-fluid-ai-conversations-15bh)).

### 4. Latency Engineering

Target: **under 800 ms end-to-end** for production voice agents ([Hamming](https://hamming.ai/resources/voice-ai-latency-whats-fast-whats-slow-how-to-fix-it), [Ultravox](https://www.ultravox.ai/voice-ai/understanding-latency-in-voice-ai-systems)). Component latencies are **cumulative and sequential** — a naïve "each stage waits for the previous" pipeline easily exceeds 2–3 s ([Smallest.ai](https://smallest.ai/blog/designing-voice-assistants-stt-llm-tts-tools-and-latency-budget)). Representative budget (confidence: **High** — consistent across Hamming, Smallest.ai, Twilio):

| Component | Typical | Optimized | Example budget (Smallest.ai) |
|---|---|---|---|
| VAD / turn detection | 200–800 ms | 200–400 ms | 50 ms (capture) |
| STT | 200–400 ms | 100–200 ms | 150 ms |
| **LLM TTFT** | **300–1000 ms** | **200–400 ms** | **400 ms** |
| TTS first chunk | 150–500 ms | 100–250 ms | 150 ms |
| Network | 100–300 ms | 50–150 ms | 50 ms |
| **Total** | 1000–3200 ms | 670–1450 ms | **~800 ms** |

Sources: [Hamming](https://hamming.ai/resources/voice-ai-latency-whats-fast-whats-slow-how-to-fix-it), [Smallest.ai](https://smallest.ai/blog/designing-voice-assistants-stt-llm-tts-tools-and-latency-budget).

**Where it accrues:** LLM inference is the dominant cost — Hamming attributes ~70% of total latency to it, "making model selection critical" ([Hamming](https://hamming.ai/resources/voice-ai-latency-whats-fast-whats-slow-how-to-fix-it)). For voice, **TTFT matters more than total generation time**, because TTS can begin streaming as soon as the first sentence is complete ([Smallest.ai](https://smallest.ai/blog/designing-voice-assistants-stt-llm-tts-tools-and-latency-budget), [Cresta](https://cresta.com/blog/engineering-for-real-time-voice-agent-latency)).

**Mitigations:** streaming STT (save 100–200 ms), streaming TTS (save 200–400 ms on TTFB), fast LLMs (GPT-4o-mini ~400 ms TTFT, Claude 3.5 Haiku ~360 ms), semantic endpointing (save 200–400 ms), and geographic colocation (US-coast-to-coast +60–80 ms, US–Europe +80–150 ms, US–Asia +150–250 ms) ([Hamming](https://hamming.ai/resources/voice-ai-latency-whats-fast-whats-slow-how-to-fix-it), [relinns](https://relinns.com/blogs/tips-to-improve-voice-agent-latency)).

### 5. Components: Streaming ASR/STT and TTS

**STT (May 2026 landscape):** **Deepgram** leads on voice-agent latency and end-of-speech detection (Nova-3 hosted WER ~5.26% on its own real-world test set); **Nova-3 + Flux** is positioned as the May-2026 voice-agent default. **ElevenLabs Scribe v2 Realtime** leads multilingual real-time; **AssemblyAI** leads transcript intelligence; **Whisper** covers 57+ languages but is beaten by Scribe v2 on its 30 ([futureagi STT](https://futureagi.com/blog/speech-to-text-apis-in-2026-benchmarks-pricing-developer-s-decision-guide/), [Softcery STT/TTS](https://softcery.com/lab/how-to-choose-stt-tts-for-ai-voice-agents-in-2025-a-comprehensive-guide), [AssemblyAI](https://www.assemblyai.com/blog/best-api-models-for-real-time-speech-recognition-and-transcription)).

**TTS time-to-first-audio (TTFA) benchmark, May 2026** (confidence: **Medium** — single benchmark source, vendor-published): Gradium TTS 155 ms P50 (2 ms IQR); Cartesia Sonic-3 188 ms P50 but 100 ms IQR (50× wider); ElevenLabs Turbo v2.5 264 ms P50 (28 ms IQR), Flash v2.5 288 ms; Deepgram Aura-2 313 ms ([Gradium benchmark](https://gradium.ai/content/tts-latency-benchmark-2026)). Positioning consensus: **ElevenLabs = voice realism / cloning benchmark; Cartesia = streaming-latency benchmark** ([futureagi TTS](https://futureagi.com/blog/elevenlabs-vs-cartesia-tts-2026/), [Cartesia](https://www.cartesia.ai/vs/elevenlabs-vs-deepgram), [Cekura TTS](https://www.cekura.ai/blogs/best-tts-for-ai-voice-agents)).

### 6. Voice UX / Design

Voice UI's defining constraint: **nothing is visible and the spoken sentence is gone the moment it lands**, so error recovery is a *primary discipline*, not an edge case ([InfoWorld](https://www.infoworld.com/article/4153289/building-enterprise-voice-ai-agents-a-ux-approach.html), [fuselabcreative](https://fuselabcreative.com/voice-user-interface-design-guide-2026/)). Key patterns:

- **Confidence-tiered confirmation:** High confidence → act + implicit confirmation ("I've sent the invoice to your inbox"); medium confidence → clarify ("I found 3 contacts named John — which one?"); low confidence → graceful fallback ([InfoWorld](https://www.infoworld.com/article/4153289/building-enterprise-voice-ai-agents-a-ux-approach.html)). Implicit confirmation beats explicit yes/no questions in enterprise flows.
- **Error recovery as trust:** users forgive the first error; doubt by the second; "doesn't work" by the third — so agents must state when confused and offer concrete next steps, not cryptic failures ([InfoWorld](https://www.infoworld.com/article/4153289/building-enterprise-voice-ai-agents-a-ux-approach.html), [Clearly Design](https://clearly.design/articles/ai-design-4-designing-for-ai-failures)).
- **Consent before consequential action:** the foundational moment before an agent takes a significant action ([Smashing](https://www.smashingmagazine.com/2026/02/designing-agentic-ai-practical-ux-patterns/)).

### 7. Evaluation

A **4-layer voice-agent quality framework**: (1) Infrastructure — audio quality, latency, ASR/TTS perf; (2) Execution — intent classification, response accuracy, tool-calling logic; (3) User-behavior — interruption handling, conversation flow, sentiment; (4) Business-outcome — containment rate, first-call resolution (FCR), escalation ([dev.to/Paul](https://dev.to/kuldeep_paul/how-to-evaluate-voice-ai-agents-a-practical-end-to-end-framework-for-quality-reliability-and-k44), [Cekura metrics](https://www.cekura.ai/blogs/voice-ai-evaluation-metrics), [Hamming metrics](https://hamming.ai/resources/voice-agent-evaluation-metrics-guide)).

Headline metrics and targets: **WER** = (S+D+I)/total words, target <5% for enterprise — but WER "ignores interaction dynamics" (barge-in, endpointing, turn-taking) and underestimates real-world UX under noise/accents/far-field ([dev.to/Paul](https://dev.to/kuldeep_paul/how-to-evaluate-voice-ai-agents-a-practical-end-to-end-framework-for-quality-reliability-and-k44)). **Interruption handling**: agent should stop within **200 ms** of user speech and acknowledge/address the interruption **>90%** of the time ([dev.to/Paul](https://dev.to/kuldeep_paul/how-to-evaluate-voice-ai-agents-a-practical-end-to-end-framework-for-quality-reliability-and-k44)). **MOS** (naturalness) ~4.5/5 for near-human; **Task Success Rate / FCR** target ~85%+ ([dev.to/Paul](https://dev.to/kuldeep_paul/how-to-evaluate-voice-ai-agents-a-practical-end-to-end-framework-for-quality-reliability-and-k44), [Hamming testing](https://hamming.ai/resources/voice-agent-testing-guide), [Braintrust](https://www.braintrust.dev/articles/how-to-evaluate-voice-agents)). Testing tooling (Hamming, Coval, Cekura, Braintrust) emphasizes **simulated callers / regression / load testing** before live traffic, and **per-component instrumentation** tagged by `call_id`/`turn_id` ([Hamming testing](https://hamming.ai/resources/voice-agent-testing-guide), [Softcery QA](https://softcery.com/lab/ai-voice-agents-quality-assurance-metrics-testing-tools)).

---

## Tools / Frameworks

**Orchestration frameworks (open source):**
- **Pipecat** — Python, pipeline/frame model stringing VAD → STT → LLM → TTS; "most elegant" for 1:1 voice assistants; transport-agnostic (WebSocket, WebRTC via Daily, Twilio media streams) but you assemble production deployment yourself ([f22labs](https://www.f22labs.com/blogs/difference-between-livekit-vs-pipecat-voice-ai-platforms/), [Cekura framework](https://www.cekura.ai/blogs/pipecat-vs-livekit-the-real-difference), [AssemblyAI frameworks](https://www.assemblyai.com/blog/vapi-vs-pipecat-vs-livekit)).
- **LiveKit Agents** — WebRTC-first; ships production transport (rooms, participant mgmt, track routing, egress/ingress, recording, SFU) in Go/Python/Node; best for multi-participant and latency-sensitive deployments that also need SIP ([Mansoori](https://www.mansooritechnologies.com/blog/livekit-vs-pipecat-voice-ai-orchestration), [LiveKit GitHub](https://github.com/livekit/agents), [WebRTC.ventures](https://webrtc.ventures/2026/03/choosing-a-voice-ai-agent-production-framework/)).
- **TEN** — third open-source contender alongside LiveKit/Pipecat ([Medium/Garcia](https://medium.com/@ggarciabernardo/realtime-ai-agents-frameworks-bb466ccb2a09)).

**Managed platforms (build-faster, telephony-included):**
- **Vapi** — middleware/BYO-everything (your LLM, TTS, STT, telephony Twilio/Vonage/Telnyx); ~500–800 ms latency; weaker native telephony (no warm transfer / branded calls / native SIP) and gated compliance ([Retell vs Vapi](https://www.retellai.com/comparisons/retell-vs-vapi), [SuperDupr](https://superdupr.com/blog/vapi-vs-bland-vs-retell)).
- **Retell AI** — managed, voice-quality + sub-500 ms latency leader; ships warm transfer, branded calls, native SIP trunking, KB retrieval, HIPAA/SOC2/GDPR on every plan ([Retell vs Vapi](https://www.retellai.com/comparisons/retell-vs-vapi), [ainora](https://ainora.lt/blog/retell-ai-vs-bland-ai-vs-vapi-comparison-2026)).
- **Bland AI** — API-first, high-volume outbound; ~600–900 ms latency, all-inclusive pricing, strong data governance ([SuperDupr](https://superdupr.com/blog/vapi-vs-bland-vs-retell), [ainora](https://ainora.lt/blog/retell-ai-vs-bland-ai-vs-vapi-comparison-2026)).

**Telephony integration:** PSTN reaches a WebRTC room via **SIP trunking** — buy a number (Twilio/Vonage/Telnyx), point its Voice URL at the framework's SIP URI. LiveKit telephony supports DTMF, call transfers, secure trunking, HD voice, region pinning, noise cancellation, plus connectors that bridge Twilio/WhatsApp without manual SIP config ([LiveKit telephony docs](https://docs.livekit.io/telephony/), [LiveKit agents-integration](https://docs.livekit.io/telephony/agents-integration/)).

---

## Practical Patterns

1. **Stream every stage; never block.** Begin TTS on the first complete sentence of the LLM stream; begin LLM on the first finalized STT segment. Naïve sequential pipelines hit 2–3 s ([Smallest.ai](https://smallest.ai/blog/designing-voice-assistants-stt-llm-tts-tools-and-latency-budget), [Hamming](https://hamming.ai/resources/voice-ai-latency-whats-fast-whats-slow-how-to-fix-it)).
2. **Optimize for LLM TTFT, not total tokens.** It's ~70% of the budget; pick a fast tier model and keep the prompt small ([Hamming](https://hamming.ai/resources/voice-ai-latency-whats-fast-whats-slow-how-to-fix-it)).
3. **Use semantic (or model-integrated) turn detection** to push silence thresholds to 200–300 ms without false cut-offs; Deepgram Flux folds end-of-turn into ASR (~260 ms) ([LiveKit](https://livekit.com/blog/turn-detection-voice-agents-vad-endpointing-model-based-detection), [Deepgram Flux](https://deepgram.com/learn/introducing-flux-conversational-speech-recognition)).
4. **Make barge-in first-class.** Keep turn detection live during playback; cancel TTS within 200 ms; distinguish backchannel from interruption with a turn-taking model ([LiveKit](https://livekit.com/blog/turn-detection-voice-agents-vad-endpointing-model-based-detection), [appinventiv](https://appinventiv.com/blog/why-ai-voice-agents-fail/)).
5. **Keep tools/business logic server-side** via a sideband channel (OpenAI Realtime) so secrets and policy never touch the client ([OpenAI Realtime blog](https://developers.openai.com/blog/realtime-api)).
6. **Match transport to context:** WebRTC for browser/mobile clients; WebSocket for server-side / telephony media ([OpenAI docs](https://platform.openai.com/docs/guides/realtime-webrtc)).
7. **Tier confirmations by confidence** and treat error recovery as a primary design surface ([InfoWorld](https://www.infoworld.com/article/4153289/building-enterprise-voice-ai-agents-a-ux-approach.html)).
8. **Instrument per component** (`call_id`/`turn_id`), watch p95 tail latency, and gate releases with simulated-caller regression tests ([Hamming testing](https://hamming.ai/resources/voice-agent-testing-guide), [appinventiv](https://appinventiv.com/blog/why-ai-voice-agents-fail/)).
9. **Default cascaded for regulated/tool-heavy; reserve S2S for empathy-first** experiences, or use a hybrid (S2S for conversation, cascade for compliance-gated branches) ([Coval](https://www.coval.ai/blog/speech-to-speech-vs-cascaded-voice-ai-which-architecture-should-you-deploy)).

---

## Anti-Patterns

- **Blocking pipeline** — waiting for the full LLM response, then starting TTS, then playing audio; adds hundreds of ms per turn for no reason ([appinventiv](https://appinventiv.com/blog/why-ai-voice-agents-fail/)).
- **Over-long silence timeout** — an 800 ms endpoint timeout adds ~1 s to *every* turn ([LiveKit](https://livekit.com/blog/turn-detection-voice-agents-vad-endpointing-model-based-detection)).
- **Endpointing that holds too long** — semantic detection waiting past the fallback silence timeout shows up as a discrete tail-latency jump, not a gradual rise ([appinventiv](https://appinventiv.com/blog/why-ai-voice-agents-fail/)).
- **No / poor barge-in** — speaking over the user or ignoring interruptions; treating backchannels as full barge-ins ([futureagi](https://futureagi.com/blog/voice-ai-barge-in-turn-taking-2026/), [appinventiv](https://appinventiv.com/blog/why-ai-voice-agents-fail/)).
- **Retry cascades without hard timeouts** — a 30 s API outlier strands the caller even if it averages away in dashboards ([appinventiv](https://appinventiv.com/blog/why-ai-voice-agents-fail/)).
- **Weak multi-turn context** — failing to resolve "cancel that one" three turns deep; demos pass, production fails ([appinventiv](https://appinventiv.com/blog/why-ai-voice-agents-fail/)).
- **Deploying S2S into regulated flows** — no text intermediary means non-compliant audio can reach the customer before any filter ([Coval](https://www.coval.ai/blog/speech-to-speech-vs-cascaded-voice-ai-which-architecture-should-you-deploy)).
- **WER-only evaluation** — ignores barge-in, endpointing, turn-taking, and real-world noise/accents ([dev.to/Paul](https://dev.to/kuldeep_paul/how-to-evaluate-voice-ai-agents-a-practical-end-to-end-framework-for-quality-reliability-and-k44)).

---

## Suggested Sub-Concepts (future child concepts)

1. **Cascaded vs. speech-native architecture selection** (incl. hybrid/gated designs)
2. **Real-time voice APIs** — OpenAI Realtime (`gpt-realtime`) & Gemini Live API: transport, sessions, sideband tools
3. **Turn detection & barge-in** — VAD, endpointing, semantic/model-integrated detection (Flux), backchannel classification, push-to-talk
4. **Voice latency budgeting & optimization** — the <800 ms budget, TTFT dominance, streaming, colocation
5. **Voice component selection** — streaming STT/TTS landscape and benchmarks (Deepgram/AssemblyAI/Whisper; ElevenLabs/Cartesia/Gradium/Deepgram)
6. **Voice orchestration frameworks & telephony** — LiveKit Agents, Pipecat, TEN; SIP/Twilio/PSTN bridging
7. **Managed voice-agent platforms** — Vapi vs. Retell vs. Bland (build-vs-buy, compliance, telephony)
8. **Voice UX design** — confidence-tiered confirmation, error recovery, consent, persona, multilingual, accessibility
9. **Voice-agent evaluation** — 4-layer framework, WER limits, interruption accuracy, MOS, TSR/FCR, simulated-caller testing

---

## Knowledge Gaps & Low-Confidence Areas

- **TTS latency benchmark numbers (Section 5)** rely on a single vendor-published benchmark ([Gradium](https://gradium.ai/content/tts-latency-benchmark-2026)) — directional, not independently verified. **Confidence: Medium-Low.**
- **S2S adoption-percentage projections** (<15% H1 2026 → 25–30% H2 2026) come from one analyst source ([Coval](https://www.coval.ai/blog/speech-to-speech-vs-cascaded-voice-ai-which-architecture-should-you-deploy)) — **Low confidence**; treat as a forecast, not a measured figure.
- **Vendor latency claims** (Retell sub-500 ms, Bland 600–900 ms) are largely from competitor-comparison pages (often Retell's own) — directionally consistent but commercially motivated. **Confidence: Medium.**
- **Exact OpenAI/Gemini interruption-handling internals** (how barge-in is implemented inside the GA models) are not publicly detailed and shade into model-internal territory owned by `multimodal-llm-architecture`.
- **Cost figures** vary widely by configuration and date; treat all $/min numbers as order-of-magnitude.

---

## Sources

1. [Coval — Speech-to-Speech vs Cascaded: Which Architecture Should You Deploy?](https://www.coval.ai/blog/speech-to-speech-vs-cascaded-voice-ai-which-architecture-should-you-deploy)
2. [Speko — Speech-to-Speech vs Cascaded Pipelines](https://speko.ai/blog/s2s-vs-cascaded)
3. [Hamming AI — Are Speech-to-Speech Models Ready to Replace Cascade Models?](https://hamming.ai/blog/are-speech-to-speech-models-ready-to-replace-cascade-models)
4. [Softcery — Real-Time (S2S) vs Turn-Based (Cascading STT/TTS) Architecture](https://softcery.com/lab/ai-voice-agents-real-time-vs-turn-based-tts-stt-architecture)
5. [Krzysztof Sopyla — Speech-to-Speech Models in 2026: Three Architectural Bets](https://ai.ksopyla.com/posts/voice-to-voice-models-2026-review/)
6. [OpenAI — Developer notes on the Realtime API](https://developers.openai.com/blog/realtime-api)
7. [OpenAI — Realtime and audio guide](https://developers.openai.com/api/docs/guides/realtime)
8. [OpenAI — Realtime API with WebRTC](https://platform.openai.com/docs/guides/realtime-webrtc)
9. [OpenAI — Realtime API with WebSocket](https://platform.openai.com/docs/guides/realtime-websocket)
10. [OpenAI — Webhooks and server-side controls](https://platform.openai.com/docs/guides/realtime-server-controls)
11. [OpenAI — Voice activity detection (VAD)](https://developers.openai.com/api/docs/guides/realtime-vad)
12. [webrtcHacks — How OpenAI does WebRTC in the new gpt-realtime](https://webrtchacks.com/how-openai-does-webrtc-in-the-new-gpt-realtime/)
13. [Google Cloud — How to use Gemini Live API Native Audio in Vertex AI](https://cloud.google.com/blog/topics/developers-practitioners/how-to-use-gemini-live-api-native-audio-in-vertex-ai)
14. [Google AI — Live API capabilities guide](https://ai.google.dev/gemini-api/docs/live-api/capabilities)
15. [blog.google — Gemini 2.5 Native Audio upgrade](https://blog.google/products/gemini/gemini-audio-model-updates/)
16. [LiveKit — Turn Detection for Voice Agents: VAD, Endpointing, Model-Based Detection](https://livekit.com/blog/turn-detection-voice-agents-vad-endpointing-model-based-detection)
17. [LiveKit — Turns overview (docs)](https://docs.livekit.io/agents/logic/turns/)
18. [Microsoft — Configuring Noise Detection and Barge-In with Azure Voice Live API](https://techcommunity.microsoft.com/blog/healthcareandlifesciencesblog/configuring-noise-detection-and-barge%E2%80%91in-with-azure-voice-live-api/4506916)
19. [SkyScribe — AI Voice Recognition: Barge-In, Turn-Taking, and VAD](https://www.sky-scribe.com/en/blog/ai-voice-recognition-barge-in-turn-taking-and-vad)
20. [futureagi — Voice AI Barge-In and Turn-Taking: A 2026 Implementation Guide](https://futureagi.com/blog/voice-ai-barge-in-turn-taking-2026/)
21. [Deepgram — Introducing Flux: Conversational Speech Recognition](https://deepgram.com/learn/introducing-flux-conversational-speech-recognition)
22. [Deepgram — Getting Started with Flux (docs)](https://developers.deepgram.com/docs/flux/quickstart)
23. [Hamming AI — Voice AI Latency: What's Fast, What's Slow, and How to Fix It](https://hamming.ai/resources/voice-ai-latency-whats-fast-whats-slow-how-to-fix-it)
24. [Smallest.ai — Designing Voice Assistants: STT, LLM, TTS, Tools, and Latency Budget](https://smallest.ai/blog/designing-voice-assistants-stt-llm-tts-tools-and-latency-budget)
25. [Twilio — Core Latency in AI Voice Agents](https://www.twilio.com/en-us/blog/developers/best-practices/guide-core-latency-ai-voice-agents)
26. [Cresta — Engineering for Real-Time Voice Agent Latency](https://cresta.com/blog/engineering-for-real-time-voice-agent-latency)
27. [futureagi — Best Speech-to-Text APIs in 2026](https://futureagi.com/blog/speech-to-text-apis-in-2026-benchmarks-pricing-developer-s-decision-guide/)
28. [Gradium — TTS Latency Benchmark 2026 (TTFA)](https://gradium.ai/content/tts-latency-benchmark-2026)
29. [futureagi — ElevenLabs vs Cartesia: 2026 Streaming TTS Comparison](https://futureagi.com/blog/elevenlabs-vs-cartesia-tts-2026/)
30. [Softcery — How to Choose STT and TTS for Voice Agents](https://softcery.com/lab/how-to-choose-stt-tts-for-ai-voice-agents-in-2025-a-comprehensive-guide)
31. [f22labs — LiveKit vs Pipecat Voice AI Platforms](https://www.f22labs.com/blogs/difference-between-livekit-vs-pipecat-voice-ai-platforms/)
32. [WebRTC.ventures — Choosing a Voice AI Agent Production Framework](https://webrtc.ventures/2026/03/choosing-a-voice-ai-agent-production-framework/)
33. [LiveKit — Telephony introduction (docs)](https://docs.livekit.io/telephony/)
34. [Retell AI — Vapi vs Retell comparison](https://www.retellai.com/comparisons/retell-vs-vapi)
35. [ainora — Retell AI vs Bland AI vs Vapi (2026)](https://ainora.lt/blog/retell-ai-vs-bland-ai-vs-vapi-comparison-2026)
36. [SuperDupr — Vapi vs Bland vs Retell (2026)](https://superdupr.com/blog/vapi-vs-bland-vs-retell)
37. [InfoWorld — Building enterprise voice AI agents: A UX approach](https://www.infoworld.com/article/4153289/building-enterprise-voice-ai-agents-a-ux-approach.html)
38. [Clearly Design — Designing for AI Failures: Error States and Recovery](https://clearly.design/articles/ai-design-4-designing-for-ai-failures)
39. [Smashing Magazine — Designing for Agentic AI: Practical UX Patterns](https://www.smashingmagazine.com/2026/02/designing-agentic-ai-practical-ux-patterns/)
40. [fuselabcreative — Voice UI Design Guide 2026](https://fuselabcreative.com/voice-user-interface-design-guide-2026/)
41. [dev.to/Kuldeep Paul — How to Evaluate Voice AI Agents: End-to-End Framework](https://dev.to/kuldeep_paul/how-to-evaluate-voice-ai-agents-a-practical-end-to-end-framework-for-quality-reliability-and-k44)
42. [Cekura — A Developer's Guide to Voice AI Evaluation Metrics (2026)](https://www.cekura.ai/blogs/voice-ai-evaluation-metrics)
43. [Hamming AI — Voice Agent Evaluation Metrics Guide](https://hamming.ai/resources/voice-agent-evaluation-metrics-guide)
44. [Hamming AI — Voice Agent Testing Guide](https://hamming.ai/resources/voice-agent-testing-guide)
45. [Braintrust — How to evaluate voice agents](https://www.braintrust.dev/articles/how-to-evaluate-voice-agents)
46. [appinventiv — AI Voice Agent Challenges: 8 Failures & How to Fix Them](https://appinventiv.com/blog/why-ai-voice-agents-fail/)
47. [relinns — 7 Ways to Improve Your AI Voice Agent Latency](https://relinns.com/blogs/tips-to-improve-voice-agent-latency)
48. [Ultravox — Understanding Latency in Voice AI Systems](https://www.ultravox.ai/voice-ai/understanding-latency-in-voice-ai-systems)
49. [LiveKit — agents (GitHub)](https://github.com/livekit/agents)
50. [Cekura — Pipecat vs. LiveKit: The Real Difference](https://www.cekura.ai/blogs/pipecat-vs-livekit-the-real-difference)

---

## Methodology

Ran 10 web searches and 4 full-page deep-reads (3 fetch timeouts were retried sequentially and succeeded) across the web using the built-in WebSearch/WebFetch fallback (firecrawl/exa MCPs were not configured in this environment; per skill guidance, source-count target was raised ~50% to compensate). Sub-questions investigated: (1) cascaded vs S2S architecture, (2) OpenAI Realtime + Gemini Live APIs, (3) turn detection / VAD / barge-in, (4) latency budgeting, (5) STT/TTS components, (6) orchestration frameworks + telephony, (7) managed platforms, (8) voice UX, (9) evaluation, (10) anti-patterns. Each sub-question is backed by 3+ independent sources except the TTS latency benchmark (single source, flagged Medium-Low) and S2S adoption forecast (single source, flagged Low). Injection guard honored — all fetched content treated as data; no adversarial redirect content encountered.
