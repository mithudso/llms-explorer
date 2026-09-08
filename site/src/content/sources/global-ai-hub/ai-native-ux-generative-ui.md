---
title: "AI-Native UX & Generative UI Design for LLM Applications"
description: "AI-native UX is consolidating into a recognizable pattern language. Three findings dominate. First, streaming is the foundational UX primitive: users perceive streaming interfaces as ~40% faster than"
---

# AI-Native UX & Generative UI Design for LLM Applications: Research Report
*Generated: 2026-05-31 | Sources: 24 | Confidence: High (with two Medium/contested areas noted)*

## Executive Summary

AI-native UX is consolidating into a recognizable pattern language. Three findings dominate. First, **streaming is the foundational UX primitive**: users perceive streaming interfaces as ~40% faster than buffered responses even at identical total latency, making **time-to-first-token (TTFT)** the key design metric, not total completion time ([Redis](https://redis.io/blog/streaming-llm-responses/), [TheFrontKit](https://thefrontkit.com/blogs/what-is-streaming-ui-in-ai-applications)). Second, **Generative UI** — LLMs emitting renderable components rather than only text — has standardized around tool-call-driven rendering. The **Vercel AI SDK** is the reference implementation, but its **RSC path (`streamUI`/`createStreamableUI`) is officially paused**; the recommended production approach is now the client-side **`useChat`** hook reading typed message `parts`, with **`streamObject`/`useObject`** for structured-output-to-component ([ai-sdk.dev](https://ai-sdk.dev/docs/ai-sdk-ui/generative-user-interfaces), [Vercel](https://vercel.com/docs/ai-sdk)). Third, the **trust/calibration layer is contested**: NN/g warns that chain-of-thought "show your work" displays and citations can *inflate* unjustified trust because reasoning traces are often post-hoc rationalizations and users rarely click citations yet feel more confident seeing them ([NN/g](https://www.nngroup.com/articles/explainable-ai/)).

Four authoritative design frameworks now govern this space: **Microsoft's 18 Guidelines for Human-AI Interaction** (the most cited, 4-phase rubric), **Google's People + AI Guidebook** (6 chapters + patterns), **Apple's Generative AI HIG** (transparency-first), and the community **Shape of AI** pattern library (6 categories, ~60 named patterns). They converge on: disclose AI use, set capability expectations, support efficient correction/dismissal, fail gracefully, and give granular feedback + global controls.

---

## 1. Streaming UX

**Why it matters.** TTFT is "one of the most visible metrics for production LLM apps because it directly shapes perceived responsiveness" ([Redis TTFT](https://redis.io/blog/ttft-meaning/)). Thresholds: under 0.5s feels instant, 0.5–1s responsive, and above 1.5–2s feels sluggish unless the UI explains what is happening ([Redis](https://redis.io/blog/streaming-llm-responses/)). Streaming TTFT is typically 200–500ms vs 5–30s for buffered ([TheFrontKit](https://thefrontkit.com/blogs/what-is-streaming-ui-in-ai-applications)). **Perceived speed gain: ~40%** at identical total time ([Redis](https://redis.io/blog/streaming-llm-responses/)). *Confidence: High.*

**The hard part is rendering, not receiving** ([TheFrontKit](https://thefrontkit.com/blogs/what-is-streaming-ui-in-ai-applications)). Transport is usually **Server-Sent Events (SSE)** over a persistent HTTP connection (`data: {"choices":[{"delta":{"content":"..."}}]}`); WebSockets are the bidirectional alternative.

**Named rendering techniques** ([TheFrontKit](https://thefrontkit.com/blogs/what-is-streaming-ui-in-ai-applications)):
- **Markdown buffering / "only render complete structures"** — defer rendering of unclosed bold/italic markers, code fences, incomplete table rows, partial list items, to avoid formatting flicker as ambiguous characters arrive.
- **Code-highlight strategies** — (a) defer syntax highlighting until block completion, (b) progressive highlighting with 200–300ms debounce, (c) language detection from the opening fence.
- **Layout-thrash prevention** — set min-heights on response containers; use CSS that grows vertically without sibling reflow; scroll the response area independently from page content.
- **Smooth streaming** — batch/animate token reveal rather than rendering each raw chunk, to avoid jitter (the perceived-TTFT lever product teams control independently of infra TTFT, per [Redis](https://redis.io/blog/streaming-llm-responses/)).

**Stop / regenerate / progressive disclosure.** Streaming enables **progressive disclosure** — users read early tokens while later ones arrive. A **Stop button** must be visible during streaming and must preserve partial output; **Retry/Regenerate** and **Copy** appear post-completion; a **rendered/raw toggle** lets users inspect source ([TheFrontKit](https://thefrontkit.com/blogs/what-is-streaming-ui-in-ai-applications)). Early interruption also cuts token cost.

**Accessibility (streaming-specific).** Use `aria-live="polite"` + `aria-atomic="false"` so screen readers announce new content without re-reading; `aria-busy="true"` during the stream; batch announcements every 2–3s, not per-token; never steal input focus while streaming ([TheFrontKit](https://thefrontkit.com/blogs/what-is-streaming-ui-in-ai-applications)). *Confidence: High.*

---

## 2. Generative UI

**Definition (Vercel):** "the process of allowing a large language model (LLM) to go beyond text and 'generate UI'" ([ai-sdk.dev](https://ai-sdk.dev/docs/ai-sdk-ui/generative-user-interfaces)).

**The tool-call-driven pattern (current recommended path).** Architecture: client sends prompt + conversation history + available tools via `useChat` → model decides whether to call a tool → tool results stream back and map to React components ([ai-sdk.dev](https://ai-sdk.dev/docs/ai-sdk-ui/generative-user-interfaces)).
- **Tool definition** (`ai/tools.ts`, `createTool()`): a `description`, a Zod **`inputSchema`**, and an **`execute`** function returning structured data shaped like the component props.
- **API route**: `streamText()` with the tools, returning `toUIMessageStreamResponse()`.
- **Typed message `parts`**: each message carries a `parts` array. Text parts `{ type:'text', text }`; tool parts `{ type:'tool-{toolName}', state, input/output }`. Tool-part **states**: `input-available` (loading), `output-available` (success, has data), `output-error`.
- **Client rendering**: switch on `part.type` and `part.state`; spread `part.output` into the component (`<Weather {...part.output} />`).

**RSC path is paused.** `streamUI` / `createStreamableUI` (AI SDK RSC) streams React Server Components directly from the server, but **"Development of AI SDK RSC is currently paused"** and Vercel recommends **AI SDK UI for production** ([ai-sdk.dev streamUI](https://ai-sdk.dev/docs/reference/ai-sdk-rsc/stream-ui), [GitHub discussion #2162](https://github.com/vercel/ai/discussions/2162)). Decision rule from the maintainers: RSC/Server Actions → `streamUI`; client-side hooks → `streamText` + `useChat` or `streamObject` + `useObject` ([#2162](https://github.com/vercel/ai/discussions/2162)). *Confidence: High.*

**Structured-output-to-component.** `streamObject` (core) constrains output to a **Zod/Valibot/JSON schema** and streams **partial objects** as fragments arrive; the client **`useObject`** (still `experimental_useObject`) progressively builds the object so the UI can render incrementally — recommended for large response structures ([ai-sdk.dev structured data](https://ai-sdk.dev/docs/ai-sdk-core/generating-structured-data), [AI Hero](https://www.aihero.dev/structured-outputs-with-vercel-ai-sdk), [DevActivity](https://devactivity.com/posts/development-integrations/boosting-ai-app-performance-streaming-structured-content-with-vercel-ai-sdk/)).

**`useChat` API surface** ([ai-sdk.dev useChat](https://ai-sdk.dev/docs/reference/ai-sdk-ui/use-chat)): returns `messages` (`UIMessage[]`), `status` (`'submitted'|'streaming'|'ready'|'error'`), `error`, `sendMessage`, `regenerate` (resend last user message, optional `messageId`), `stop` (aborts the transport stream), `clearError`, `resumeStream`, `addToolOutput`, `setMessages`. The status enum is the canonical state machine for skeleton/typing/stop affordances.

**Generative-UI runtimes beyond Vercel.** **Thesys C1** is an OpenAI-compatible API middleware that returns a **structured UI spec** (forms, tables, charts, layouts) instead of text, rendered by the **C1 React SDK**; supports tool calls, state, actions, multi-step flows, and bring-your-own components/design system ([Thesys](https://www.thesys.dev/), [DEV](https://dev.to/anmolbaranwal/thesys-react-sdk-turn-llm-responses-into-real-time-user-interfaces-30d5)). Thesys also publishes **OpenUI** as "the open standard for generative UI" ([GitHub](https://github.com/thesysdev/openui)). Vendor-reported productivity claims (80% less frontend code, 10x faster) are **marketing, not independently verified** — *Confidence: Low* on those figures, High on the architecture.

---

## 3. Latency Masking & Perceived Performance

- **TTFT is a design variable**, shapeable independently of infra latency via streaming and animation ([Redis](https://redis.io/blog/streaming-llm-responses/)). *High.*
- **Skeleton screens / placeholders / shimmer** during the 200ms–several-seconds gap before first token — "if nothing visible happens during this time, users think the submit failed" ([TheFrontKit](https://thefrontkit.com/blogs/what-is-streaming-ui-in-ai-applications)). *High.*
- **Thinking/typing indicators** and "We're experiencing high demand, your request is queued" messaging buy patience: "Transparency beats silence — users are forgiving when they understand what's happening" ([OrangeLoops](https://orangeloops.com/2025/07/9-ux-patterns-to-build-trustworthy-ai-assistants/)). *High.*
- **Optimistic UI** — render the user's submitted turn immediately and an assistant placeholder before the stream begins. *Medium (widely practiced; less formally sourced here).*
- **Progressive disclosure** as latency mask — see §1. *High.*

---

## 4. Trust & Calibration UI (most contested area)

**Goal:** "calibrating users' trust is crucial for establishing appropriate reliance" — neither over- nor under-trust ([NN/g research agenda](https://www.nngroup.com/articles/genai-ux-research-agenda/)).

**Citations / source attribution.** Best practices ([NN/g explainable AI](https://www.nngroup.com/articles/explainable-ai/)): make citations visually prominent and **separate** from the response; place sources **adjacent to the specific claim**; use meaningful labels (publication/article titles) not generic ones; link to the relevant **section**; set the expectation upfront that sources may be inaccurate or fabricated. **Perplexity** is the exemplar — inline numbered citations next to referenced text, retrieve-then-synthesize, with measurably lower reference-hallucination than ChatGPT ([ZipTie](https://ziptie.dev/blog/how-perplexity-ai-answers-work/), [SearchEngineLand](https://searchengineland.com/how-different-ai-engines-generate-and-cite-answers-463234)). **Contrarian finding:** "people rarely click citation links, yet they still develop false confidence from seeing citations present" ([NN/g](https://www.nngroup.com/articles/explainable-ai/)). *Confidence: High on the practices; the trust effect is Medium/contested.*

**"Show your work" / reasoning traces.** This is where guidance **diverges**. The Shape of AI documents **Stream of Thought** ("reveal AI's reasoning, tool use, and decisions") as a Governor pattern, and ChatGPT-5 Thinking ships a step-by-step walkthrough ([Shape of AI](https://www.shapeof.ai/), [SearchEngineLand](https://searchengineland.com/how-different-ai-engines-generate-and-cite-answers-463234)). But **NN/g recommends avoiding step-by-step reasoning displays "for now"** because they are "rationalizations generated after the fact, rather than faithful representations" and risk promoting trust in flawed tools ([NN/g](https://www.nngroup.com/articles/explainable-ai/)). **Report both:** collapsible reasoning aids steerability/debugging but should not be presented as ground-truth explanation. *Confidence: Low (genuine disagreement between sources).*

**Confidence display & uncertainty.** Google PAIR's Explainability + Trust chapter recommends **partial explanations, progressive disclosure, and model-confidence displays** ([PAIR feedback](https://pair.withgoogle.com/chapter/feedback-controls/), [Buildo](https://www.buildo.com/blog-posts/what-we-learned-from-googles-people-ai-guidebook)). "Good AI UX doesn't pretend to be certain — it exposes confidence levels, pauses, narrows scope, and backs off when conditions degrade" ([UX Bulletin](https://www.ux-bulletin.com/ux-for-degradation-graceful-failure-design/)). **Confidence cascades** (from voice assistants): high confidence → act + confirm; medium → request clarification; low → explicit uncertainty ([OrangeLoops](https://orangeloops.com/2025/07/9-ux-patterns-to-build-trustworthy-ai-assistants/)). *Medium — numeric confidence percentages are debated; behavioral confidence cues are better supported.*

**Anthropomorphization / disclaimers** ([NN/g](https://www.nngroup.com/articles/explainable-ai/)): eliminate first-person phrasing that implies human thinking; avoid names/personalities/backstories that inflate perceived capability; put **specific, actionable disclaimers** ("Double-check AI outputs") near the input, not buried in footers; avoid vague "AI-generated, for reference only." *High.*

---

## 5. Refusal / Error / Fallback UX

**Error taxonomy (Google PAIR Errors + Graceful Failure)** ([PAIR errors](https://pair.withgoogle.com/chapter/errors-failing/)):
- **System limitations** — can't give a right/any answer (missing data, insufficient precision).
- **Context errors** — system "working as intended" but the user perceives an error because it broke their mental model or rested on poor assumptions.
- **User-perceived vs. invisible** — context errors/failstates are visible; "happy accidents" and background errors are not.
- Error **sources**: prediction/training-data errors, input errors, relevance errors (low confidence, bad timing), system-hierarchy errors (multi-system conflicts).

**Communication principle:** "**Be human, not machine** … Address mistakes with humanity and humility"; make failure "**safe, boring, and a natural part of the product**" ([PAIR errors](https://pair.withgoogle.com/chapter/errors-failing/)).

**Graceful-degradation patterns** ([aiuxdesign.guide](https://www.aiuxdesign.guide/patterns/error-recovery), [UX Bulletin](https://www.ux-bulletin.com/ux-for-degradation-graceful-failure-design/)): degradation answers three user questions — *what still works? what doesn't? what next?* Offer **2–3 recovery options** (retry / wait-in-queue / offline-basic mode); let users **revert an AI decision**; route to **human assistance or manual paths** when the AI can't solve it.

**"I don't know" done well:** "Graceful failure doesn't just say 'I don't know' — it suggests next steps, like ChatGPT prompting users to rephrase" ([OrangeLoops](https://orangeloops.com/2025/07/9-ux-patterns-to-build-trustworthy-ai-assistants/)). **Guardrail-block messaging** should acknowledge the limit, explain, and offer an alternative rather than a cryptic refusal ([Clearly Design](https://clearly.design/articles/ai-design-4-designing-for-ai-failures)). Maps to **HAX G9/G10** (efficient correction; scope when in doubt). *Confidence: High.*

---

## 6. Human-AI Handoff & Steering

**Prompt-input design — NN/g "4 main uses of prompt controls"** ([NN/g prompt controls](https://www.nngroup.com/articles/prompt-controls-genai/)):
1. **Increase feature discoverability** — show upload icons etc. instead of forcing users to ask ("can you upload files?").
2. **Educate & inspire** — conversation starters, prompt libraries ("Inspiration Center"); ~19–30% of users are unfamiliar with GenAI capabilities.
3. **Set constraints** — scope/output controls up front (Perplexity **Focus**: Reddit/YouTube/academic; chart-type pickers).
4. **Facilitate follow-ups** — since **77% of conversations have >1 exchange**, offer edit/regenerate/copy and quick modifiers (Gemini "Shorter," "More casual").

**Input best practices** ([NN/g](https://www.nngroup.com/articles/prompt-controls-genai/)): standard icons **with labels/tooltips** (novel icons confuse); clearly named features (avoid vague brand labels like "Think Carefully"); group controls by purpose (proximity); don't override standard gestures.

**Suggestions / follow-ups** ([NN/g prompt suggestions](https://www.nngroup.com/articles/prompt-suggestions/)): system-generated hints (questions, phrases, keywords) showcase capability and reduce effort; **follow-up questions** shown below an answer drive engagement and continuation; proactively ask framing questions instead of launching a generic response (**mixed-initiative**).

**Feedback affordances** ([NN/g](https://www.nngroup.com/articles/prompt-controls-genai/), [Shape of AI](https://www.shapeof.ai/)): standard, universally-understood icons — **favorite, thumbs-up, thumbs-down, copy, share** — at the bottom of each reply; **edit-in-place** of generated artifacts (diagrams, text); **Regenerate** to explore alternatives; **Variations** to compare versions side-by-side. Google PAIR's **Feedback + Control** chapter adds three rules: align feedback with model improvement (implicit vs explicit), communicate value + time-to-impact, and balance control/automation with easy opt-out ([PAIR](https://pair.withgoogle.com/chapter/feedback-controls/), [Buildo](https://www.buildo.com/blog-posts/what-we-learned-from-googles-people-ai-guidebook)). *Confidence: High.*

---

## 7. Conversational & Agent UX Patterns + Design-System Heuristics

### Microsoft — 18 Guidelines for Human-AI Interaction (2019 CHI paper, the canonical rubric; validated with 49 practitioners against 20 products) ([Microsoft Research](https://www.microsoft.com/en-us/research/blog/guidelines-for-human-ai-interaction-design/), [HAX Toolkit](https://www.microsoft.com/en-us/haxtoolkit/ai-guidelines/))

**Initially:** G1 Make clear what the system can do · G2 Make clear how well it can do it.
**During interaction:** G3 Time services based on context · G4 Show contextually relevant information · G5 Match relevant social norms · G6 Mitigate social biases.
**When wrong:** G7 Support efficient invocation · G8 Support efficient dismissal · G9 Support efficient correction · G10 Scope services when in doubt · G11 Make clear why the system did what it did.
**Over time:** G12 Remember recent interactions · G13 Learn from user behavior · G14 Update and adapt cautiously · G15 Encourage granular feedback · G16 Convey the consequences of user actions · G17 Provide global controls · G18 Notify users about changes.

The toolkit also ships **HAX Design Patterns**, a searchable **Design Library** with implementation examples, and a **Workbook** for prioritization ([HAX Toolkit](https://www.microsoft.com/en-us/haxtoolkit/ai-guidelines/)). *Confidence: High.*

### Google — People + AI Guidebook (PAIR) ([PAIR](https://pair.withgoogle.com/), [Buildo](https://www.buildo.com/blog-posts/what-we-learned-from-googles-people-ai-guidebook))
Six chapters: **User Needs + Defining Success · Data Collection + Evaluation · Mental Models · Explainability + Trust · Feedback + Control · Errors + Graceful Failure**, plus a pattern set with sensitizing examples (patterns *and* anti-patterns). *High.*

### Apple — Generative AI HIG ([Apple HIG](https://developer.apple.com/design/human-interface-guidelines/generative-ai))
Transparency-first: "**Communicate where your app uses AI**" to set expectations and let people knowingly opt in; responsibly/transparently incorporate generation; manage expectations and maintain user control; built-in safety guardrails on model input/output. Granular Apple error/feedback specifics were **not extractable** (JS-rendered page) — see Knowledge Gaps. *Medium (page-render gap).*

### Shape of AI — community pattern library (curator Emily Campbell) ([Shape of AI](https://www.shapeof.ai/))
Six categories with ~60 named patterns:
- **Wayfinders** (start the first prompt): Gallery, Follow Up, Initial CTA, Nudges, Prompt Details, Randomize, Suggestions, Templates.
- **Inputs / Prompt Actions**: Auto-fill, Chained Action, Describe, Expand, Inline Action, Inpainting, Madlibs, Open Input, **Regenerate**, Restructure, Restyle, Summary, Synthesis, Transform.
- **Tuners** (refine via context/params): Attachments, Connectors, Filters, Model Management, Modes, Parameters, Preset Styles, Prompt Enhancer, Saved Styles, Voice and Tone.
- **Governors** (human-in-the-loop oversight): **Action Plan** (show intended steps before execution), Branches, **Citations**, Controls (pause mid-stream), Cost Estimates, Draft Mode, Memory, References, Sample Response, Shared Vision, **Stream of Thought**, Variations, **Verification** (confirm before proceeding).
- **Trust Builders**: Caveat, Consent, Data Ownership, **Disclosure** (mark AI content), **Footprints** (trace steps prompt→result), Incognito Mode, Watermark.
- **Identifiers**: Avatar, Color, Iconography, Name, Personality.
*Confidence: High (primary source).*

**Agent UX specifics.** Showing the agent's plan and tool use maps to Shape of AI **Action Plan**, **Stream of Thought**, **Footprints**, and **Verification**, and to HAX **G11** (why it did what it did) — surface intended steps before execution, reveal tool calls, and gate consequential actions behind confirmation ([Shape of AI](https://www.shapeof.ai/), [Microsoft Research](https://www.microsoft.com/en-us/research/blog/guidelines-for-human-ai-interaction-design/)). *High.*

---

## Key Takeaways

1. **Optimize TTFT, not total latency.** Stream by default; mask the pre-first-token gap with skeletons; animate token reveal (smooth streaming). Perceived speed ≈ +40%.
2. **Generative UI = tool-calls → typed `parts` → components.** Use Vercel AI SDK `useChat` + `streamText`/tools (client-side) — **not** the paused RSC `streamUI`. Use `streamObject`/`useObject` + a Zod schema for structured-output-to-component. Thesys C1/OpenUI is the schema-driven runtime alternative.
3. **Calibrate trust deliberately and skeptically.** Inline, claim-adjacent citations (Perplexity-style) with honest disclaimers near the input; treat reasoning-trace displays as steering aids, not faithful explanations (NN/g caution); prefer behavioral confidence cues (confidence cascades) over raw percentages.
4. **Engineer failure.** Classify errors (PAIR: system / context / invisible); "be human, not machine"; offer 2–3 recovery paths + revert + human handoff; never a cryptic refusal.
5. **Make steering cheap.** Prompt controls for discoverability/education/scoping/follow-ups; standard feedback icons (thumbs/copy/edit/regenerate); mixed-initiative framing questions.
6. **Anchor to the four frameworks.** Microsoft 18 Guidelines (rubric), Google PAIR (process + patterns), Apple HIG (transparency), Shape of AI (concrete pattern vocabulary).

## Knowledge Gaps

- **Apple Generative AI HIG granular detail** — the official page is JS-rendered and did not return full text via WebFetch after 2 attempts; only high-level transparency/expectations guidance was confirmed via secondary sources. The error-handling, feedback, and over-reliance specifics should be read directly at developer.apple.com.
- **Numeric confidence display** — whether to show explicit confidence percentages is contested; behavioral cues (cascades, hedging language) are better supported than numeric scores. *Low/Medium.*
- **Reasoning-trace display** — direct disagreement: Shape of AI / shipping products embrace "Stream of Thought"; NN/g advises against presenting it as explanation. *Low.*
- **Thesys C1 productivity claims** (80% less frontend code, 10x faster) — vendor marketing, not independently verified.
- **Full HAX Design Patterns catalog** — confirmed to exist as a searchable library but individual patterns were not enumerated here (out of scope for this pass).

## Sources
1. [Vercel AI SDK — Generative UI](https://ai-sdk.dev/docs/ai-sdk-ui/generative-user-interfaces) — tool-call→parts pattern; RSC paused.
2. [Vercel AI SDK — useChat reference](https://ai-sdk.dev/docs/reference/ai-sdk-ui/use-chat) — messages/status/stop/regenerate API.
3. [Vercel AI SDK — streamUI (RSC)](https://ai-sdk.dev/docs/reference/ai-sdk-rsc/stream-ui) — RSC streaming, paused.
4. [Vercel AI SDK — Generating Structured Data](https://ai-sdk.dev/docs/ai-sdk-core/generating-structured-data) — generateObject/streamObject + Zod.
5. [vercel/ai Discussion #2162](https://github.com/vercel/ai/discussions/2162) — streamUI vs streamObject/streamText decision rule.
6. [Vercel — AI SDK docs](https://vercel.com/docs/ai-sdk) — three-layer (Core/UI/RSC) architecture.
7. [AI Hero — Structured Outputs with Vercel AI SDK](https://www.aihero.dev/structured-outputs-with-vercel-ai-sdk) — useObject/streamObject usage.
8. [DevActivity — Streaming structured content](https://devactivity.com/posts/development-integrations/boosting-ai-app-performance-streaming-structured-content-with-vercel-ai-sdk/) — progressive object rendering.
9. [Redis — Streaming LLM responses](https://redis.io/blog/streaming-llm-responses/) — perceived +40%, TTFT thresholds.
10. [Redis — TTFT meaning](https://redis.io/blog/ttft-meaning/) — TTFT definition/metric.
11. [TheFrontKit — Streaming UI in AI apps](https://thefrontkit.com/blogs/what-is-streaming-ui-in-ai-applications) — SSE, markdown buffering, layout thrash, stop, a11y.
12. [NN/g — Explainable AI in Chat Interfaces](https://www.nngroup.com/articles/explainable-ai/) — citations, anti-reasoning-trace, disclaimers, anthropomorphization.
13. [NN/g — Prompt Controls in GenAI](https://www.nngroup.com/articles/prompt-controls-genai/) — 4 main uses + input best practices.
14. [NN/g — Prompt Suggestions](https://www.nngroup.com/articles/prompt-suggestions/) — suggestions and follow-ups.
15. [NN/g — Research Agenda for GenAI in UX](https://www.nngroup.com/articles/genai-ux-research-agenda/) — trust calibration framing.
16. [Microsoft Research — Guidelines for Human-AI Interaction](https://www.microsoft.com/en-us/research/blog/guidelines-for-human-ai-interaction-design/) — all 18 guidelines, 4 phases.
17. [Microsoft HAX Toolkit — AI Guidelines](https://www.microsoft.com/en-us/haxtoolkit/ai-guidelines/) — toolkit components (Patterns/Library/Workbook).
18. [Google PAIR Guidebook](https://pair.withgoogle.com/) — 6 chapters + patterns.
19. [Google PAIR — Feedback + Control](https://pair.withgoogle.com/chapter/feedback-controls/) — feedback rules, confidence display.
20. [Google PAIR — Errors + Graceful Failure](https://pair.withgoogle.com/chapter/errors-failing/) — error taxonomy, "be human not machine."
21. [Apple HIG — Generative AI](https://developer.apple.com/design/human-interface-guidelines/generative-ai) — transparency, expectations, control.
22. [Shape of AI](https://www.shapeof.ai/) — 6-category, ~60-pattern AI UX library.
23. [Thesys C1 + OpenUI](https://www.thesys.dev/) / [DEV writeup](https://dev.to/anmolbaranwal/thesys-react-sdk-turn-llm-responses-into-real-time-user-interfaces-30d5) — schema-driven generative-UI runtime.
24. [OrangeLoops — 9 UX patterns for trustworthy AI](https://orangeloops.com/2025/07/9-ux-patterns-to-build-trustworthy-ai-assistants/) / [ZipTie — How Perplexity cites](https://ziptie.dev/blog/how-perplexity-ai-answers-work/) — trust/confidence/citation patterns.

## Methodology
Ran 11 web searches + 8 deep page-fetches (built-in WebSearch/WebFetch fallback; firecrawl/exa not configured, so source targets were raised ~50%). Analyzed 24 sources across 7 sub-questions: streaming UX, generative UI, latency masking, trust/calibration, refusal/error UX, human-AI steering, and design-system heuristics. Prioritized primary/authoritative sources (Vercel AI SDK docs, NN/g, Microsoft HAX/Research, Google PAIR, Apple HIG, Shape of AI). Injection guard honored — no fetched page content was treated as instructions; no adversarial redirection encountered.
