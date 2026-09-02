# Markdown as the LLM Output Gateway

### A Technical Review

*How a 2004 lightweight-markup language became the default machine-to-human interface layer for large language models — and where that role breaks down.*

**Version 1.0 — 2026-06-17**

---

## Abstract

Large language models emit text. Yet the text users actually see is rarely raw prose: it is headed, listed, tabulated, code-fenced, emphasized, and linked. The near-universal vehicle for that structure is **Markdown**. This review evaluates a specific thesis — that *Markdown functions as the interface layer ("gateway") through which an LLM transforms its machine-internal representations (a left-to-right token stream, serialized tool output, structured data) into semantically cogent, human-readable output.* The thesis holds, with qualifications. Markdown wins this role not because it is expressive but because it is **simultaneously legible as source and meaningful as structure**, cheap in tokens, ubiquitous in training data, and trivially streamable. It loses the role wherever structural fidelity matters more than human legibility, because Markdown is lossy by design. The review covers why models converged on Markdown, the CommonMark/GFM format substance, the parse-to-render pipeline and its real implementations, the rendering security surface, streaming behavior, the format's fidelity ceiling, a comparison against JSON/XML/HTML/plain text, the under-discussed reverse direction (Markdown as machine *input*), and the characteristic failure modes. Claims are tagged **\[ESTABLISHED\]**, **\[ANALYSIS\]**, or **\[CONTESTED\]** to keep evidence honest.

**A terminological note up front.** "LLM gateway" is an overloaded phrase. In infrastructure circles it denotes a *proxy control plane* between an application and model providers (LiteLLM, Portkey, OpenRouter — unified API, virtual keys, spend caps). **That is not the sense used here.** This review uses "gateway" in the *semiotic* sense: a translation membrane between machine representation and human cognition. The collision is worth naming because automated tooling routinely conflates the two — a fitting illustration of the disambiguation problem this very document is about.

---

## 1\. Framing the Thesis

An LLM's native output is a sequence of tokens sampled one at a time from a probability distribution. Nothing about that sequence is intrinsically "formatted." Formatting is a *convention the model learned to emit* and that downstream software learned to *interpret*. The thesis under review is that Markdown is the dominant such convention — the agreed contract at the boundary where machine output meets human reading.

Three properties make "gateway" the right metaphor rather than mere hyperbole:

1. **It is a boundary.** Markdown sits exactly at the machine/human interface — produced by a machine process, consumed by human eyes (usually after a render step).  
2. **It is a translation.** The same artifact carries one meaning to a parser (a structural contract) and another to a person (visual hierarchy and emphasis). Markdown is unusual in serving both at once.  
3. **It is a throughput-shaping chokepoint.** Like a network gateway, it imposes a protocol: what structure *can* pass (headings, lists, tables, code, emphasis, links) and what cannot (arbitrary layout, typed data, deep nesting) without an escape hatch.

The rest of this review tests each property and locates where the membrane is permeable, where it is lossy, and where it leaks (security).

---

## 2\. What "Machine → Human" Actually Means Here

The phrase "transforming machine language into human-readable output" needs unpacking, because three distinct machine-side inputs converge on the same Markdown gateway:

- **The token stream itself.** The model's own next-token output, shaped into Markdown syntax because the model was trained to produce it. Here the "machine language" is the raw generation and Markdown is the surface form it takes.  
- **Serialized / structured data.** Tool results, API responses, database rows, JSON blobs the model has in context and must *present*. The model transcodes structured data into Markdown tables, lists, and code blocks for human consumption.  
- **Code and logs.** Inherently machine-oriented text that needs to be shown verbatim but legibly — handled by fenced code blocks with language hints for highlighting.

In all three, Markdown is the *presentation transcoding target*. It is not where the model reasons; it is where the model's conclusions are dressed for a reader. **\[ANALYSIS\]** This distinction matters for §8: because Markdown is a presentation layer, its lossiness is acceptable — fidelity is bounded by what a human needs to see, not by what a machine needs to reconstruct.

---

## 3\. Why LLMs Converged on Markdown

Why this format and not HTML, JSON, reStructuredText, or plain prose? The reasons sort cleanly into what is well-established, what is plausible mechanism, and what is genuinely contested.

**\[ESTABLISHED\] Training-corpus ubiquity.** Markdown saturates the text LLMs train on: GitHub READMEs and issues, documentation sites, Reddit and Stack Overflow (both Markdown-based), forums, and chat logs. A model trained by next-token prediction over this corpus learns Markdown's regularities as a first-class dialect. The format is in the data, so it is in the model.

**\[ESTABLISHED\] Chat-UI rendering \+ preference reinforcement.** The dominant deployment surface — ChatGPT, Claude, Gemini chat interfaces — renders Markdown. Human-preference data (RLHF and its successors) rewards answers that *look* well-organized once rendered, which means rewards flow to Markdown-structured responses. Many systems also *instruct* Markdown output directly in the system prompt. This very harness states that assistant text "is displayed to the user as GitHub-flavored markdown in a terminal" — i.e., the gateway contract is declared explicitly, not merely hoped for, and was observed directly in this environment. **\[ESTABLISHED.\]**

**\[ANALYSIS\] Token economy.** Markdown's syntactic overhead is low relative to tag-based formats. `**bold**` is 8 characters / a few tokens; `<strong>bold</strong>` is 21 characters and more tokens; a styled HTML equivalent is worse. Across a long response, Markdown leaves more of the token budget for content. This is a plausible and arithmetically sound advantage, though it is rarely the *stated* design driver.

**\[ANALYSIS\] Graceful degradation / source legibility.** Markdown's founding design goal (Gruber & Swartz, 2004\) was that the *source* be publishable as-is — readable even unrendered. For an LLM gateway this is a structural gift: if rendering fails, is stripped, or happens in a plain-terminal context, the output is still legible. The format degrades gracefully to plain text, which no tag-based format does.

**\[CONTESTED\] Format affects model reasoning quality.** A separate, stronger claim sometimes appears: that prompting or responding *in Markdown* measurably improves the model's reasoning, not just its presentation. The evidence is mixed and model-dependent. Studies on prompt-format sensitivity show benchmark scores can shift non-trivially with formatting choices (Markdown vs. JSON vs. YAML vs. plain), but results do not converge on Markdown as universally superior, and effects are noisy across models and tasks. Treat "Markdown makes models think better" as unproven; "Markdown makes output more legible" as obvious. **\[CONTESTED.\]**

---

## 4\. The Format Substance: CommonMark, GFM, and Dialect Drift

"Markdown" is not one language; it is a family with a contested center. Reviewing the gateway requires knowing exactly what structure the contract guarantees.

- **Original Markdown (2004).** Gruber's reference implementation plus an informal description. Famously *under-specified*: edge cases (nested lists, emphasis boundaries, HTML blocks) behaved differently across implementations. As a machine contract, it was unreliable.  
- **CommonMark (2014–).** A rigorous, versioned specification with a reference test suite of several hundred cases, created precisely to make Markdown an unambiguous, interoperable contract. It standardizes block and inline parsing. **\[ESTABLISHED.\]** This is the substrate most serious tooling targets.  
- **GitHub Flavored Markdown (GFM).** A formal superset of CommonMark adding the features people actually expect: pipe **tables**, **task lists** (`- [ ]`), **strikethrough** (`~~`), literal-URL **autolinks**, and a *disallowed-raw-HTML* filter for safety. GFM is the de facto dialect of LLM output because it is what GitHub, and therefore much of the training corpus and many chat UIs, use. **\[ESTABLISHED.\]**  
- **The long tail.** Pandoc Markdown (footnotes, definition lists, math via `$...$`), MultiMarkdown, Markdown Extra, and MDX (JSX embedded in Markdown for React). These extend expressiveness at the cost of portability.

The design philosophy throughout is **lightweight markup**: a small, punctuation-based vocabulary that maps to a bounded set of structures. That smallness is the source of both Markdown's legibility (§3) and its fidelity ceiling (§8). The dialect spread is the source of a key failure mode (§11): the same source can render differently depending on which parser sits at the far side of the gateway.

---

## 5\. The Pipeline: Tokens → AST → Render

The gateway is not a single step; it is a small pipeline. Understanding it is necessary to reason about both streaming (§7) and security (§6).

```
 MACHINE SIDE                                                            HUMAN SIDE
 ┌──────────────┐   ┌───────────┐   ┌──────────────┐   ┌───────────┐   ┌────────────────┐
 │ model token  │──▶│ MD-shaped │──▶│  parser      │──▶│   AST     │──▶│  renderer +    │──▶ rendered
 │ stream /     │   │ text      │   │  (lexer:     │   │ (mdast /  │   │  sanitizer     │    output
 │ tool output /│   │ buffer    │   │  block then  │   │  token    │   │  (HTML / term /│    (human
 │ struct. data │   │           │   │  inline)     │   │  stream)  │   │   React)       │     eyes)
 └──────────────┘   └───────────┘   └──────────────┘   └───────────┘   └────────────────┘
   "machine            the gateway surface:               structural        presentation
    language"          plain text that is BOTH            contract           for a reader
                       legible source AND contract
```

**Parsing is two-phase**, a structure the CommonMark spec mandates. **\[ESTABLISHED.\]**

1. **Block parsing** identifies block-level structure: paragraphs, ATX/Setext headings, lists, blockquotes, fenced and indented code blocks, thematic breaks, HTML blocks. It establishes the document skeleton.  
2. **Inline parsing** then runs *within* blocks to resolve emphasis, code spans, links, images, and autolinks. Emphasis resolution in particular (the `*`/`_` delimiter-run algorithm) is the spec's most intricate corner.

The result is an **AST** (or an equivalent token stream). In the `unified`/`remark` ecosystem this tree is **mdast** (Markdown Abstract Syntax Tree); the low-level CommonMark-compliant tokenizer beneath remark is **micromark**. The AST is the pivot point: it can be transformed (e.g., remark → **rehype** to produce an HTML AST, **hast**) and emitted to many targets.

Real implementations a reviewer should know:

| Library | Ecosystem | Model | Notable trait |
| :---- | :---- | :---- | :---- |
| **marked.js** | browser/Node | lexer → tokens → renderer | Fast; deliberately *does not sanitize* (defers to DOMPurify) |
| **markdown-it** | browser/Node | pluggable token stream | CommonMark-compliant; HTML disabled by default (`html: false`) |
| **remark / unified** | Node/build | mdast \+ plugin transforms | Spec-grade via micromark; powers MDX, react-markdown's pipeline |
| **micromark** | low-level | streaming tokenizer | CommonMark/GFM reference-grade core |
| **react-markdown** | React | mdast → hast → React elements | Renders to a component tree, not an HTML string |

The renderer is polymorphic: the *same* AST becomes an HTML string, a tree of React elements, ANSI-styled **terminal** output (how a CLI harness shows GFM), or a PDF. This polymorphism is exactly what makes Markdown a *gateway* rather than a *format* — one machine-side artifact, many human-side surfaces.

---

## 6\. Rendering and the Safety Surface

The moment Markdown becomes HTML, it inherits HTML's attack surface — and LLM output is, by definition, untrusted-adjacent text that may be steered by upstream content (prompt injection, poisoned RAG context). The gateway is therefore also a **security boundary**, and treating it casually is the most common production mistake.

**The raw-HTML passthrough.** CommonMark permits embedded raw HTML; it passes through to the output. That means a model (or content the model is relaying) can emit `<img src=x onerror=alert(1)>`, `<script>`, or a `javascript:` URL inside a link. Rendered naively, these execute. **\[ESTABLISHED — this is a standard XSS class, not hypothetical.\]**

**Defenses, in layers:**

- **Sanitize after render.** The standard client-side pattern is render Markdown → HTML, then pass that HTML through **DOMPurify**, which strips dangerous tags/attributes/URLs. marked.js explicitly removed its own `sanitize` option and tells callers to use a dedicated sanitizer — render and sanitize are separate concerns. **\[ESTABLISHED.\]**  
- **Disable raw HTML at the parser.** markdown-it ships with `html: false`; GFM defines a *disallowed raw HTML* filter. If you never need embedded HTML, turning it off removes the surface entirely.  
- **Constrain URLs.** Allowlist schemes (`http`, `https`, `mailto`) and reject `javascript:`/`data:`; DOMPurify hooks can enforce HTTPS-only images to prevent tracking-pixel/SSRF-style leaks via `![](http://attacker/...)`.  
- **Content Security Policy.** In browser and especially Chrome MV3 extension contexts, a strict CSP (`script-src 'self'`) is a backstop so that even a sanitizer miss cannot execute inline script. Shadow-DOM isolation additionally prevents rendered Markdown's styles from bleeding into the host page.  
- **Syntax highlighting safely.** Fenced code blocks carry a language hint (```` ```python ````) consumed by highlight.js or Prism. Highlighters operate on escaped text, but misconfiguration that highlights *before* escaping reintroduces injection — order matters.

The reviewer's takeaway: **a Markdown gateway that renders to HTML without sanitization is an XSS vulnerability, full stop.** The "human-readable output" half of the thesis is only safe when the render step treats the model's text as untrusted.

---

## 7\. Streaming: Markdown's Structural Advantage and Its Failure Mode

LLMs generate left-to-right, and modern UIs stream tokens as they arrive. Markdown is unusually well-suited to this, and understanding why — and where it breaks — is core to the gateway's behavior.

**\[ANALYSIS\] Why Markdown streams well.** Markdown is largely **append-only and locally-scoped**. A paragraph, a list item, a sentence with emphasis — each becomes meaningful as soon as its few delimiter characters arrive. A UI can re-parse the growing buffer on each chunk and show incremental, mostly-correct output. There is no document-level envelope that must close before anything is valid (contrast JSON, §9).

**The partial-construct failure mode.** Streaming exposes a real weakness: **constructs that span a range render wrong until they close.**

- An opened fenced code block ```` ``` ```` with no closing fence yet makes *everything after it* render as code until the close arrives.  
- A half-emitted GFM table (header row present, delimiter row not yet) renders as plain pipe-laden text, then snaps into a table once the delimiter row lands.  
- An unbalanced `**` turns the remainder of the stream bold until the closing `**` appears.

Mitigations in practice **\[ANALYSIS, common engineering patterns\]**: incremental parsers that tolerate EOF gracefully (treat an unclosed fence as an open code block and render it as such); speculative closing of open constructs for display; or buffering a construct until it completes before committing it to the rendered view. The cost is a small rendering latency or transient flicker — a UX tax the gateway pays for being a streaming-friendly format.

---

## 8\. Semantic Fidelity: Markdown Is Lossy by Design

The single most important property for evaluating the thesis: **Markdown is a lossy, bounded representation.** It is not a general structured-data format and was never meant to be.

What Markdown represents natively: six heading levels, ordered/unordered (and, in GFM, task) lists, blockquotes, code (inline and fenced), emphasis/strong/strikethrough, links, images, thematic breaks, and — in GFM — simple pipe tables. That set covers the overwhelming majority of *human-facing prose structure*.

What it cannot represent natively: nested or cell-spanning tables (GFM tables have no `colspan`/`rowspan` and no nesting), arbitrary layout, typed/keyed data, document metadata, footnote/citation apparatus (outside extensions), or anything requiring precise geometry. The escape hatch is embedded raw HTML — which reintroduces the §6 security surface and breaks the legibility promise of §3.

**\[ANALYSIS\] The fidelity verdict:** Markdown is "good enough for \~90% of human-facing structure," and for the long tail you must either embed HTML or escalate to a different contract (JSON for data, HTML for layout, a structured-output API schema for machine round-trip). Crucially, because Markdown is a *presentation* layer (§2), this lossiness is usually acceptable: the reader does not need a machine-reconstructable structure, only a legible one. The thesis survives precisely because the gateway's job is human cognition, not data fidelity. Where a downstream *machine* must reconstruct exact structure, Markdown is the wrong gateway and the thesis does not apply.

---

## 9\. The Format Bake-Off

Set Markdown against the alternatives on the dimensions that matter for a machine→human contract. **\[ANALYSIS — qualitative synthesis.\]**

| Dimension | Markdown | JSON | XML | HTML | Plain text |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Human readability (unrendered) | **High** | Low (nested) | Low–med | Med (verbose) | **Highest** |
| Structural fidelity | Medium (lossy) | High (data) | **Very high** | High (+ layout) | None |
| Token overhead | **Low** | Medium | High | High | **Lowest** |
| Streaming / partial-parse | **Good (degrades)** | Poor (must be valid/complete) | Poor–med | Med (tolerant) | **Trivial** |
| Machine round-trip | Lossy | **Exact** | **Exact** | Near-exact | None |
| Native render target | via HTML | none | none | **direct** | none |

The pattern is clear and explains Markdown's dominance for *human-facing* output: it is the only row that is simultaneously **high-readability, low-overhead, and streaming-tolerant**. JSON and XML win machine round-trip and fidelity but are hostile to human reading and cannot be streamed incrementally (an incomplete JSON object is invalid, not partially-meaningful). HTML is Markdown's heavyweight cousin — higher fidelity and a direct render target, but verbose, token-expensive, and unreadable as source. Plain text wins readability and streaming but offers no structure at all.

Markdown is, in effect, **HTML's friendly front-end**: it compiles down to HTML for rendering while staying legible and cheap on the model side. That is the architectural reason it occupies the gateway position.

---

## 10\. The Reverse Channel: Markdown as Machine *Input*

A complete review must note that the gateway runs **both directions**, which is under-appreciated. Markdown is not only how models *talk to humans*; it is increasingly how humans (and pipelines) *talk to models*.

- **Document-to-Markdown ingestion.** RAG and context-assembly pipelines routinely convert PDF/HTML/DOCX sources into Markdown before feeding them to a model, because Markdown preserves heading/list/table structure at low token cost and is clean to chunk. Structure-aware chunking on Markdown headings is a standard retrieval pattern. **\[ESTABLISHED practice.\]**  
- **`llms.txt`.** A 2024 proposal (Jeremy Howard / Answer.AI) for a `/llms.txt` file at a site root — curated, Markdown-formatted links and content meant to be LLM-friendly, analogous to `robots.txt` but for model consumption. **\[ESTABLISHED as a proposal; CONTESTED in adoption — it is a community convention that major answer engines do not uniformly consume, and should not be presented as a standard the models actually read today.\]**  
- **Markdown as the agent context lingua franca.** Skill files, system prompts, tool descriptions, and agent memory are themselves overwhelmingly Markdown. The same legible-source/cheap-tokens properties that make Markdown a good *output* format make it a good *instruction* format.

So the membrane is bidirectional: machine→human (rendered output) and human/doc→machine (ingestible context). A format that serves both directions with the same syntax is a genuine lingua franca, which strengthens the "gateway" framing beyond the one-way output case.

---

## 11\. Failure Modes and Anti-Patterns

Naming the gateway's failure modes is part of operating it responsibly.

1. **Dialect drift.** The same source renders differently under CommonMark vs. GFM vs. a legacy parser (tables, task lists, autolinks, and raw-HTML handling are the usual divergence points). Mitigation: target CommonMark+GFM explicitly and pin the parser.  
2. **Inline-parse edge cases.** Intraword emphasis (`a_b_c`), tight-vs-loose lists, list-indentation ambiguity, and pipe-escaping in tables produce surprises. These are spec-defined but counterintuitive.  
3. **Injection via rendered constructs.** `[click](javascript:...)`, raw `<script>`/`<img onerror>`, and tracking/SSRF images via `![](http://...)`. (See §6 — this is the highest-severity failure.)  
4. **Streaming artifacts.** Unclosed fences, half-built tables, unbalanced emphasis mid-stream (§7).  
5. **Model-emitted malformed structure.** LLMs hallucinate structure: mismatched fence counts, broken table column alignment, headings that should be bold, nesting that does not close. The gateway faithfully renders the model's mistakes.  
6. **Over-formatting ("bullet-point soup").** The inverse problem — models over-applying headers, bold, and nested bullets until structure becomes noise rather than signal. This is a *style* failure of the gateway: structure is supposed to aid scanning, and excess structure defeats it. It is also a recognizable "AI tell" in prose, which is ironic for a format whose job is legibility.

---

## 12\. Evidence & Epistemics

To keep the review honest, the claims sort into three tiers:

- **\[ESTABLISHED\]** (verifiable from specs/implementations): the two-phase parse model; CommonMark's existence as a versioned spec with a test suite; GFM's superset features; the raw-HTML XSS class and DOMPurify/CSP as standard mitigations; marked-defers-sanitization and markdown-it-html-off defaults; Markdown's saturation of training corpora; chat UIs render Markdown; this harness declares GFM output.  
- **\[ANALYSIS\]** (sound reasoning, not a citation): token-economy and graceful-degradation as *reasons* for adoption; the streaming-fit argument and its mitigations; the lossiness verdict; the format bake-off ratings.  
- **\[CONTESTED\]** (genuinely open): that response/prompt format measurably changes model *reasoning* quality (mixed, model-dependent evidence); `llms.txt` real-world adoption by answer engines.

A version of this review with inline citations to the CommonMark spec, the GFM spec, the original Gruber documentation, DOMPurify's threat model, and the prompt-format-sensitivity literature can be produced with a `/dr` (deep-research) pass — see the closing offer.

---

## 13\. Verdict

**The thesis holds, bounded.** Markdown is the de facto gateway through which LLMs convert machine-side representations into human-readable output, and it earns that position for sound reasons: it is legible as source and meaningful as structure at the same time, cheap in tokens, ubiquitous in the training distribution, declared by the deployment surfaces, and uniquely tolerant of token-by-token streaming. No competing format occupies all of those properties at once.

**Where Markdown earns the "gateway" label:** human-facing assistant output, chat and terminal rendering, code presentation, light-to-medium structure (headings, lists, tables, emphasis), and — bidirectionally — as cheap, structured context fed back into models.

**Where Markdown is the wrong tool:** any contract that requires exact machine round-trip or high structural fidelity (use JSON or a structured-output schema), precise layout (HTML), or guaranteed-safe rendering without a sanitization step (none — always sanitize). And the gateway is *only* a safe boundary when the render side treats model text as untrusted.

Markdown's strength and its limit are the same fact: it is a *lightweight* markup language. Lightness buys legibility, cheapness, and streamability — the exact properties a machine→human gateway needs — at the cost of fidelity it was never trying to provide. For the job of making a model's output cogent to a person, that is the right trade. For the job of moving structured data between machines, it is not, and the thesis correctly does not claim it.

---

## Appendix A — Glossary

| Term | Definition |
| :---- | :---- |
| **Markdown** | A lightweight, punctuation-based markup language (Gruber & Swartz, 2004\) whose source is meant to be legible unrendered. |
| **CommonMark** | A strict, versioned, test-suite-backed Markdown specification created to remove ambiguity. |
| **GFM** | GitHub Flavored Markdown; a CommonMark superset adding tables, task lists, strikethrough, autolinks, and a raw-HTML filter. |
| **mdast / hast** | Markdown AST / HTML AST in the unified ecosystem. |
| **micromark** | Low-level CommonMark/GFM-compliant tokenizer underpinning remark. |
| **DOMPurify** | The standard client-side HTML sanitizer used to neutralize XSS in rendered Markdown. |
| **Gateway (this doc)** | A semantic translation membrane between machine representation and human cognition — *not* an AI-proxy control plane. |
| **llms.txt** | A 2024 proposed convention for an LLM-friendly Markdown file at a site root (limited adoption). |

## Appendix B — A Round-Trip Illustration

Machine-side input (a structured tool result the model holds in context):

```json
{"clusters":[{"name":"prod-east","tier":"M30","alerts":2},{"name":"prod-west","tier":"M40","alerts":0}]}
```

Gateway output the model emits (Markdown — legible as source, a contract to a parser):

```
| Cluster   | Tier | Open alerts |
|-----------|------|-------------|
| prod-east | M30  | 2           |
| prod-west | M40  | 0           |
```

Human-side render: a clean two-row table. The transcoding is **lossy** (the JSON's type information is gone; you cannot mechanically reconstruct the original object from the table without assumptions) and **legible** (a person reads it instantly). That trade — fidelity surrendered for cognition — is the gateway thesis in a single example.

---

## Provenance & Method

**How this review was produced.** Authored via the `prompt-helper-optimizer` skill in auto-execute (`/phe`) mode. During curation, six skills the optimizer/recommender surfaced on the substrings "llm"/"llms"/"gateway"/"data" were discarded as stopword or term-collision noise (`llms-for-trading-research`, `llm-routing-cascades`, `llm-integration-reviewer`, `llm-inference-serving`, `llm-ai-gateways`, `declarative-llm-frameworks`); the genuinely on-target `document-formats` (under-ranked at 0.016 by the recommender) was rescued; and the "gateway" sense was disambiguated from AI-proxy infrastructure.

**Skills that informed the content (and why).**

- `document-formats` — authority for Markdown/CommonMark/GFM authoring and processing (remark/unified, markdown-it, mdast) underpinning §4–§5, §8.  
- `markdown-rendering-browser` — the browser render-and-sanitize pipeline (marked.js, DOMPurify, highlight.js, CSP, shadow DOM) underpinning §5–§6.  
- `ai-mcp-sdk-prompting` — structured-output and context-engineering framing for §2, §3 (why models emit Markdown), §10.  
- `technical-writing-craft` / `writing-expert` — structure and prose discipline for the review form.  
- `kill-the-AI-ism` — kept the prose from the over-formatting failure mode it documents in §11 (judicious structure, prose for argument).  
- `document-critique` — self-review lens before delivery.

**Epistemic discipline.** Claims are tagged **\[ESTABLISHED\]** (verifiable from specs/implementations or observed in this environment), **\[ANALYSIS\]** (reasoning, not citation), or **\[CONTESTED\]** (open evidence). This document is knowledge-grounded, not a fresh web literature review: the two **\[CONTESTED\]** items — format-affects-reasoning and `llms.txt` adoption — and any reader who wants inline citations to the CommonMark/GFM specs and DOMPurify threat model would be best served by a follow-up `/dr` (deep-research) pass, which can produce a fully cited edition.