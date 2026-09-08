---
title: "AI-Native UX and Generative UI Design"
description: "The frontend, UI, and UX hub for designing and building user interfaces. This"
---

# Frontend & UI/UX Expert

The frontend, UI, and UX hub for designing and building user interfaces. This
skill covers the full surface of frontend work: visual and interaction design
(layouts, design systems, tokens, color, typography), markup and styling
(HTML semantics, CSS layout), platform targets (responsive web and native
mobile/iOS), implementation review of framework-free UIs, and
accessibility/UX evaluation against the published standards.

Use it when the task is about designing or implementing a user interface rather
than the underlying language mechanics, generic software patterns, or
Chrome-extension-specific UI surfaces. For a single deep sub-area, match the
routing table below and read the corresponding reference file before answering.

## How to use this skill

This skill consolidates 9 frontend sub-skills as on-demand reference files.
Match the task to the routing table below and **Read the listed
`references/…md` file before answering deep questions** — the table alone is not
enough for depth. For exact syntax, property, and platform-API details, defer to
the official sources (HTML Living Standard, MDN, W3C WCAG 2.2, WAI-ARIA APG,
Apple Human Interface Guidelines) as the source of truth.

## Sub-skill routing table

This hub absorbs 9 former standalone skills as on-demand reference files. When a
task matches a row, **Read the listed `references/` file** before answering — do
not rely on this table alone for depth.

| Sub-topic | When to load | Reference file |
| --- | --- | --- |
| `accessibility-ux-reviewer` | Accessibility and UX review against WCAG 2.2, the WAI-ARIA Authoring Practices Guide, and MDN | `references/accessibility-ux-reviewer.md` |
| `ai-native-ux-generative-ui` | **AI-native UX & generative UI** — the interface/interaction layer of LLM apps: streaming UX (TTFT, markdown buffering, smooth streaming, a11y), generative UI (Vercel AI SDK `useChat`/`streamObject` typed parts, the paused RSC path, Thesys C1/OpenUI), latency masking, trust/calibration UI (claim-adjacent citations, confidence cascades, the reasoning-trace caveat), refusal/error UX (PAIR taxonomy), human-AI steering & feedback, and the four governing frameworks (Microsoft HAX 18 Guidelines, Google PAIR, Apple Generative AI HIG, Shape of AI). Backend/model/agent layers → `ai-agent-engineering`; generic visual design → web-design / `ui-ux-pro-max`; the trust psychology → `applied-psychology`. | `references/ai-native-ux-generative-ui.md` |
| `frontend-design` | Production-grade frontend engineering: design systems and tokens, component architecture | `references/frontend-design.md` |
| `frontend-design-ui-ux-expert` | DEPRECATED — use `frontend-design` instead; this content was merged into the enriched frontend-design reference | `references/frontend-design-ui-ux-expert.md` |
| `html-css` | HTML (Living Standard) and CSS expert reference for markup structure, semantics, layout, and styling | `references/html-css.md` |
| `mobile-ios-design` | iOS Human Interface Guidelines and SwiftUI patterns for building native iOS and iPadOS apps | `references/mobile-ios-design.md` |
| `ui-ux-pro-max` | UI/UX design intelligence for web and mobile: 50+ styles, 161 color palettes, 57 font pairings | `references/ui-ux-pro-max.md` |
| `visual-design-principles-and-critique` | **Visual-design critique RUBRIC** — when the task is to *evaluate/critique* a graphic/brand asset or UI screen (not produce one). Named **visual-design** principles (visual hierarchy, gestalt grouping, C.R.A.P., balance, emphasis/focal point, white space, scale & proportion/modular scale, unity/variety/rhythm, Z/F/Gutenberg scanning patterns) each as **Detect a violation → Rate severity (Nielsen 0–4) → Fix**. For *producing* a design → web-design / `ui-ux-pro-max`; **Nielsen's 10 usability heuristics + Laws of UX** as the lens → `usability-heuristics-laws-of-ux`; accessibility-only → accessibility-ux-reviewer; prompting a VLM to critique a screenshot → `ai-mcp-sdk-prompting`. | `references/visual-design-principles-and-critique.md` |
| `micro-typography-craft` | **Editorial micro-typography & type-craft defect catalog** (the typography-pass depth layer for the visual-design-critique family) — the nameable, screenshot-detectable type-craft problems a critique should catch, each as **DETECT (on-screen tell) → RATE (Blocker→Nit) → FIX (+ CSS/InDesign control)**: widows/orphans/runts & stranded subheads; ragged-edge (rag) quality, rivers, bad line breaks; kerning/tracking/letter-spacing ("keming", all-caps tracking, display kerning); leading/line-height, vertical rhythm & baseline-grid alignment; measure (CPL ~45–75); hyphenation & justification (H&J) & justified-text gaps; hanging punctuation & optical margin alignment, optical vs metric kerning, optical sizing (opsz); correct glyphs (curly vs straight quotes, en/em dashes, real vs faux small caps, old-style/lining/tabular figures, ligatures, true vs faux bold/italic, ×/…/primes, proper fractions); and "type crimes" (stretched/condensed faux styles, ransom-note font mixing, centered body, underline-for-emphasis, all-caps passages). The high-level typographic-scale/measure/line-height rubric → `visual-design-principles-and-critique` (P2); how to *run* a crit → `visual-design-critique-methodology`; WCAG contrast/numeric a11y → `computational-aesthetics-ui-metrics`; choosing fonts/styles for a NEW design → `ui-ux-pro-max` / web-design. | `references/micro-typography-craft.md` |
| `visual-design-critique-methodology` | **Design-critique METHODOLOGY** (companion to the rubric above) — *how to run and give* a design critique: structured formats (I-Like-I-Wish-What-If, Describe/Interpret/Evaluate, Rose/Bud/Thorn, design studio/charrette), Connor & Irizarry *Discussing Design*, critique-vs-feedback-vs-review, observation-before-judgment, actionable-non-prescriptive feedback, severity & design QA / spec-parity, running a crit (objectives up front, sync vs async, closing the loop), and crit anti-patterns (compliment sandwich, HiPPO, bikeshedding, design-by-committee, vague praise). The principles themselves → `visual-design-principles-and-critique`; heuristic eval / Laws of UX → `usability-heuristics-laws-of-ux`. | `references/visual-design-critique-methodology.md` |
| `emotional-design-and-visual-trust` | **Affective / emotional-resonance & visual-trust critique axis** — when the task is to judge whether a design *feels right, trustworthy, and on-tone* at first glance (the subjective-emotional complement to the principles/heuristics references). Norman's **visceral/behavioral/reflective** levels applied to evaluating an asset; the **first-impression** aesthetic judgment + **halo effect** + aesthetic→perceived-trust pathway (Lindgaard, Reinecke); **Stanford/Fogg web credibility** (the 10 guidelines, "design look = the most-mentioned credibility factor", prominence-interpretation, surface credibility, trust signals that build vs erode); **brand personality** from type/color/imagery/shape (Aaker's five dimensions, warmth×competence) and the **emotional-tone audit**; and the **critique pass** (5-second / squint first-glance tests, an affective audit, severity rating reframed for trust defects, a fix vocabulary, composition with other lenses, anti-patterns). The **aesthetic-usability effect** itself → `usability-heuristics-laws-of-ux`; visual-composition principles → `visual-design-principles-and-critique`; how to *run* a crit → `visual-design-critique-methodology`; objective metrics → `computational-aesthetics-ui-metrics`; WCAG → accessibility-ux-reviewer; general trust/emotion psychology (Mayer ABI, emotion regulation) → `applied-psychology`. | `references/emotional-design-and-visual-trust.md` |
| `usability-heuristics-laws-of-ux` | **Usability heuristic evaluation + Laws of UX as a critique instrument** — Nielsen's 10 usability heuristics (each with detection signals and fixes), the heuristic-evaluation method (evaluator process, the verbatim 0–4 severity scale, 3–5 evaluators + the 1−(1−λ)^n discovery formula, aggregation/prioritization, heuristic evaluation vs usability testing), and the Laws of UX (Yablonski/lawsofux.com — Hick, Fitts, Jakob, Miller, Tesler, Postel, Doherty, Aesthetic-Usability, Von Restorff, Serial Position, Peak-End, Zeigarnik, + the Gestalt grouping laws) with each law's concrete UI implication. Load for a detection→severity→fix critique pass. General UX guidance → ui-ux-pro-max; WCAG → accessibility-ux-reviewer. | `references/usability-heuristics-laws-of-ux.md` |
| `deceptive-design-and-dark-patterns` | **Design-ETHICS critique axis** — the *is-this-honest?* lens (complement to the *is-this-good?* critique references). When the task is to audit/critique a UI, mockup, flow, or spec for **deceptive, manipulative, or coercive patterns** and their 2024-26 **legal exposure**: the named taxonomies (Brignull/deceptive.design 16 types; Gray et al. — nagging, obstruction, sneaking, interface interference, forced action; Mathur et al. — urgency, scarcity, social proof, misdirection, sneaking, obstruction, forced action; the 6 "dark" attributes); the high-risk flows (sign-up, consent/cookie banners, subscription & cancellation, checkout, defaults); and the regulatory layer (EU DSA Art. 25 + EDPB, GDPR consent & CNIL cookie rules, FTC "Bringing Dark Patterns to Light" + Negative Option/click-to-cancel, CCPA/CPRA + state clauses) — each as **DETECT (UI tell) → RATE (harm + compliance risk) → FIX (honest pattern)**. The honest twin (persuasion + heuristics/Laws of UX) → `usability-heuristics-laws-of-ux`; the trust consequence → `emotional-design-and-visual-trust`; WCAG → accessibility-ux-reviewer; persuasion/nudge *psychology* → `applied-psychology`; drafting honest copy → `content-and-marketing-writing`. | `references/deceptive-design-and-dark-patterns.md` |
| `computational-aesthetics-ui-metrics` | **OBJECTIVE / quantitative scoring layer** (the measurement complement to the three *subjective* critique references above) — machine-computable metrics that feed, but never replace, a human/LLM critique. Image-statistic aesthetic metrics (Hasler-Süsstrunk colourfulness, colour harmony, visual complexity, Rosenholtz feature-congestion / edge-density clutter, symmetry), the **Aalto Interface Metrics (AIM)** toolkit + the computational-aesthetics-of-UI research line (Reinecke, Miniukovich & De Angeli, Ngo), layout / grid / white-space metrics, **visual saliency / attention prediction** (Itti-Koch, the AUC/NSS/CC/SIM metric zoo, UMSI & UEyes, predictive-attention tools), and **automated accessibility checkers as objective signals** (axe-core, Lighthouse a11y score, programmatic WCAG contrast-ratio, target-size 2.5.8, APCA). Carries the load-bearing caveat: these correlate only weakly-to-moderately with human aesthetic judgment (~48–49% web / ~32% mobile variance explained) — flag candidates and quantify deltas, never rank or auto-score. Subjective principles/rubric → `visual-design-principles-and-critique`; WCAG compliance *review* → accessibility-ux-reviewer; prompting a VLM to critique a screenshot → `ai-mcp-sdk-prompting`. | `references/computational-aesthetics-ui-metrics.md` |
| `vanilla-js-ui-reviewer` | Practical review reference for large plain-JavaScript UIs that manage DOM, events, focus, state, and accessibility without a framework | `references/vanilla-js-ui-reviewer.md` |
| `web-design` | Senior web graphic designer for interfaces, layouts, and visual systems | `references/web-design.md` |
| `react-nextjs` | React 19 and Next.js 15+ expert reference. | `references/react-nextjs.md` |

## Cross-hub boundaries

This hub owns frontend design, UI/UX, and interface implementation. Hand off
when the task falls into a sibling hub:

- **Chrome-extension-specific UI** — content scripts, shadow DOM injected into
  host pages, extension popup/options surfaces, MV3 UI plumbing →
  `chrome-extension-expert`.
- **JavaScript / TypeScript language specifics** — syntax, language APIs, type
  systems, runtime semantics → `programming-languages`.
- **Language-agnostic software design patterns and architecture** — generic
  design patterns, separation of concerns, structural patterns →
  `software-engineering-patterns`.

Some topics legitimately touch two hubs (e.g., a vanilla-JS UI review brushes
against JS language mechanics, and an extension popup is still HTML/CSS). Lead
with the hub that matches the user's intent — interface design and
implementation intent stays here; language-mechanics or extension-runtime intent
hands off.

Note: a separate plugin skill `frontend-design:frontend-design` also exists.
This hub absorbs the top-level `frontend-design` skill (now
`references/frontend-design.md`), not the plugin — invoke the plugin skill
directly if that is what you need.

<!-- cross-hub-map -->
## Cross-hub map — where every frontend topic lives

This family is split across these hubs. If a task's deep material is **not** in this hub's Sub-skill
routing table, it is a reference file under a sibling hub below — **activate that hub or `Read` its
`references/<name>.md` directly**. Every former standalone skill in this family is now a reference under one
of these hubs (nothing was deleted).

| Hub | Owns | Example reference files |
| --- | --- | --- |
| `frontend-ui` | Frontend & UI/UX (design, HTML/CSS, web/mobile, accessibility reviews) | `references/accessibility-ux-reviewer.md`, `references/frontend-design.md`, `references/frontend-design-ui-ux-expert.md`, `references/html-css.md`, … |
