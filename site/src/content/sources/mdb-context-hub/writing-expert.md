---
title: "Writing and Documentation"
description: "Reference for technical, business, and report writing. Deep treatments of every craft concept live in references/advanced-craft.md and the per-topic files in the Sub-skill routing table below. Load th"
---

# Writing Expert

Reference for technical, business, and report writing. Deep treatments of every craft concept live in `references/advanced-craft.md` and the per-topic files in the Sub-skill routing table below. Load the matching reference when the user needs depth beyond the core rules in this skill.

**Output is correct when:** the delivered document (a) opens with the bottom line if BLUF applies, (b) contains zero Tier 1 terms, (c) matches the audience register in the Tone Calibration table, and (d) addresses the user's stated goal without adding unrequested content. Apply the Tier 1 ban list to your own prose as well as to the user's document.

## When to use this skill

Activate when the user:

- Asks to write, draft, or improve any prose document (report, summary, email, runbook, architecture doc, proposal, meeting minutes)
- Needs help with document structure, tone, or formatting
- Wants a status report, QBR, account review, executive summary, or post-mortem
- Asks about writing frameworks (BLUF, Pyramid Principle, SCQA, STAR, Minto)
- Wants to eliminate AI-sounding prose or improve human voice
- Needs to calibrate tone for different audiences (executive vs developer vs customer)
- Asks about data storytelling or dashboard-to-prose conversion
- Wants markdown formatting guidance (headings, tables, lists, code blocks)
- Has an ambiguous "make this better" request — triage by asking: audience, document type, and primary goal (clarity / tone / structure)

## When NOT to use this skill

Route to a sibling hub instead when the user needs:

- **Software / product / engineering docs** — API docs, runbooks, specs, PRDs, RFCs, design docs, commit messages, PR descriptions, changelogs, error messages, UI microcopy → `technical-writing-craft`
- **Executive / business / persuasion** — one-pagers, OKRs, pitch decks, proposals, speeches, public speaking, founder letters, whitepapers, case studies → `executive-comms`
- **Marketing / PR / external comms** — sales copy, press releases, crisis PR, newsletters, op-eds, launch narratives, audio scripts, NPS/support replies → `content-and-marketing-writing`
- **Career / academic / legal / formal** — resumes, cover letters, job descriptions, performance reviews, academic/citation writing, legal-adjacent prose, policy, surveys → `career-and-formal-writing`
- **AI-voice cleanup of an existing draft** → `kill-the-ai-ism`
- **Multi-pass structural/factual document critique** (review loop, fact-check, ship-readiness) → `writing-expert` (references/document-critique.md)

## Sub-skill routing table

This hub consolidates 18 prose-craft sub-skills plus a deep-craft reference as on-demand reference files. When a task matches a row, **Read the listed `references/<name>.md` before deep answers** — do not rely on this table alone for depth.

| Sub-topic | When to load | Reference file |
| --- | --- | --- |
| `advanced-craft` | Deep treatments of journalism structures (inverted pyramid, hourglass, bury-the-lede), achievement frameworks (STAR/SOAR/PAR/CAR), sentence devices (fragments, tricolon, title vs sentence case, Oxford comma), style sheets, show-don't-tell, Curse of Expertise, information scent, emphasis discipline, and front-matter craft (TL;DR, kicker, nutgraf, deck, tabular-vs-prose). | `references/advanced-craft.md` |
| `editing-and-revision` | Multi-pass editing and revision craft for tightening prose after drafting is complete. | `references/editing-and-revision.md` |
| `rhetorical-frameworks-deep` | Deep reference for rhetorical and argument frameworks — Aristotle (ethos/pathos/logos), Toulmin (claim/data/warrant), Pyramid. | `references/rhetorical-frameworks-deep.md` |
| `storytelling-and-narrative` | Narrative craft for business and technical writing — customer-facing prose, story arcs. | `references/storytelling-and-narrative.md` |
| `headline-craft` | Craft, critique, and rewrite headlines for articles, blogs, marketing pages, news, op-eds, social posts, and email subject lines. | `references/headline-craft.md` |
| `plain-language` | Plain-language craft for customer-facing, legal-adjacent, regulated, and accessibility-driven simplification (US Federal Plain Language guidelines). | `references/plain-language.md` |
| `inclusive-language` | Bias-free, inclusive language for technical writing, customer comms, internal docs, and code (APA 7th bias-free guidelines). | `references/inclusive-language.md` |
| `localization-friendly-writing` | Writing source-language text (typically English) that will translate cleanly. | `references/localization-friendly-writing.md` |
| `anti-jargon-translator` | Translates technical prose into plain language with a structured diff of what changed. | `references/anti-jargon-translator.md` |
| `brand-voice-guide-writing` | Authoring craft for the brand voice guide artifact — the document other writers follow. | `references/brand-voice-guide-writing.md` |
| `audience-modeler` | Infer and profile the audience for any document, then re-evaluate the draft against it. | `references/audience-modeler.md` |
| `visual-writing` | Writing the words that travel with images, charts, infographics, and video. | `references/visual-writing.md` |
| `accessibility-writing` | Accessibility writing — heading structure, descriptive link text, alt-text, screen-reader-friendly prose. | `references/accessibility-writing.md` |
| `ai-collaboration-writing` | How writers work with LLMs as collaborators — not replacements — and ship human-voiced prose. | `references/ai-collaboration-writing.md` |
| `realtime-writing-under-pressure` | Real-time, time-pressured channels — Slack updates, breaking-news comms, 60-second answers, live blogs, status-page posts. | `references/realtime-writing-under-pressure.md` |
| `interview-and-conversational` | Interview and conversational craft — question design, podcast/interview prep. | `references/interview-and-conversational.md` |
| `profile-writing` | Journalistic profile of a person — scene, anecdote, and reporting to reveal character and context. | `references/profile-writing.md` |
| `email-craft` | General-purpose professional email — subject-line discipline, BLUF openings, single-ask-per-email, reply-all etiquette. | `references/email-craft.md` |
| `ddo` | Document Deep Optimizer — runs a full multi-pass critique on any document, | `references/ddo/SKILL.md` |
| `document-critique` | Multipass document review agent that surfaces and fixes findings through 15 structured passes (intent, structure, technical correctness… | `references/document-critique.md` |
| `draft-review-revise-loop` | Meta-skill — explicit three-pass workflow for any prose document: draft → review against | `references/draft-review-revise-loop.md` |
| `kill-the-AI-ism` | Diagnostic skill for detecting and replacing generator artifacts ("AI-isms") in prose. | `references/kill-the-AI-ism.md` |

## Core Principles

1. **BLUF (Bottom Line Up Front)** — Lead with the conclusion. Put the most important information in the first sentence. Supporting details follow in decreasing importance.

2. **One idea per paragraph** — Each paragraph makes exactly one point. The first sentence states it; the rest support it.

3. **Active voice by default** — "The team deployed the fix" not "The fix was deployed by the team." Passive voice only when the actor is unknown or irrelevant.

4. **Concrete over abstract** — "Latency increased from 50ms to 340ms" not "Performance degraded significantly."

5. **No AI-isms** — Apply the full Tier 1 ban list below. Chatbot tics (`certainly`, `I hope this helps`, `Let's dive in`) are Tier 3 tells — delete on sight.

6. **Preserve facts** — Never substitute, paraphrase, or fabricate numbers, names, dates, or technical claims from the input. If a claim is unclear, flag it rather than rewrite it.

7. **Confirm before rewriting** — Before editing any document over 100 words, ask at most one compound question: "Who is the audience, what's the primary goal (clarity / tone / structure / AI-ism removal), and is there a length target?" — unless all three are already stated. For from-scratch requests (no existing document), ask: topic, audience, and desired length before drafting.

8. **Self-check before delivery** — Scan every output for Tier 1 terms and Tier 3 chatbot tics before responding. Remove any found. Confirm the document opens with the bottom line if BLUF applies. Re-read the output against the user's stated goal to confirm it answers what was asked, not a related-but-different question.

## Quick Framework Selection

| Situation | Framework | Structure |
|---|---|---|
| Status update / email | **BLUF** | Conclusion → context → details → action required → deadline |
| Executive presentation | **Minto Pyramid** | Answer → supporting arguments → data |
| Problem analysis | **SCQA** | Situation → Complication → Question → Answer |
| Case study / achievement | **STAR** | Situation → Task → Action → Result |
| News / announcement | **Inverted Pyramid** | Most important → supporting → background |
| Investigation / research | **5W1H** | Who, What, When, Where, Why, How |

## Document Type Templates

### Executive Summary
1. One-sentence bottom line
2. Key metrics (3–5 numbers that tell the story)
3. What changed since last report (delta-focused)
4. Risks / blockers (max 3)
5. Recommended actions with owners and dates

### Incident Post-Mortem
1. Summary (what happened, duration, impact — 2–3 sentences)
2. Timeline (bullet list with timestamps)
3. Root cause (specific, technical, no blame)
4. Contributing factors
5. Remediation actions (with owners, dates, status)
6. Lessons learned

### Technical Runbook
1. Purpose (one sentence: when to use this)
2. Prerequisites (tools, access, permissions)
3. Steps (numbered, imperative mood, one action per step)
4. Verification (how to confirm each step worked)
5. Rollback (how to undo if things go wrong)
6. Troubleshooting (common failure modes + fixes)

### Status Report
1. TL;DR (one sentence)
2. Completed this period (bullet list)
3. In progress (with % or ETA)
4. Blocked / at risk (with mitigation)
5. Next period plan
6. Metrics table

### Proposal / Business Case
1. Problem statement (quantified: cost, risk, or missed opportunity)
2. Proposed solution
3. Alternatives considered (with one-line rationale for rejecting each)
4. Cost and timeline
5. Risks and mitigations
6. Recommendation

### Meeting Minutes
Decisions made (numbered) → action items (owner + date) → open questions. Skip discussion recap — only decisions and actions matter.

### Unlisted Document Types
For types not above (RCA letters, press releases, cover letters, change announcements), apply the closest template and note the adaptation: "Using Incident Post-Mortem structure for RCA letter — sections 3–5 map directly."

## Tone Calibration

| Audience | Register | Detail level | Jargon | Example |
|---|---|---|---|---|
| C-suite / VP | Formal, concise | High-level only | Business terms, no tech | "Revenue impact: $2.3M ARR at risk" |
| Engineering manager | Semi-formal | Summary + key details | Technical OK | "The replica set election took 45s due to priority misconfiguration" |
| Developer / DBA | Direct, technical | Full detail | Expected | "Run rs.reconfig() with the updated priority values" |
| Customer (technical) | Professional, empathetic | Relevant detail | Their stack's terms | "We identified the root cause in the connection pooling layer" |
| Customer (executive) | Warm, professional | Impact-focused | Minimal | "Service was restored at 14:32 UTC with no data loss" |

## Anti-AI-ism Rules

### Tier 1 — Always replace

| AI-ism | Plain alternative |
|---|---|
| delve | examine, explore, look at |
| leverage | use |
| robust | strong, reliable |
| paradigm | model, approach |
| seamless | smooth, easy |
| utilize | use |
| commence | start, begin |
| facilitate | help, enable |
| furthermore | also, and |
| navigate (metaphorical) | handle, manage, deal with |
| landscape | field, space, area |
| cutting-edge | new, latest, advanced |
| holistic | complete, comprehensive, full |
| it's important to note | (delete — just state the point) |
| in today's rapidly evolving | (delete) |
| game-changer | (be specific about what changed) |

### Tier 2 — Flag in clusters (2+ in one section)
harness, foster, resonate, ecosystem, journey, empower, unlock, drive (metaphorical), transform, innovative, dynamic, significant

### Tier 3 — Structural tells
- Em dashes used as sentence separators in prose (target: ≤1 per 500 words for AI-ism detection; the craft rule for polished human prose is ≤1 per 100 words — see Em-dash discipline in the craft section; structural use in headings and table separators is exempt)
- Uniform paragraph/sentence lengths — vary between 1 and 5 sentences
- Formulaic openings ("In the world of...", "When it comes to...", "In an era of...")
- Hedge-stacking ("could potentially", "may eventually", "might arguably")
- Generic conclusions ("In conclusion, X remains a Y")
- Chatbot tics ("I hope this helps!", "Let me know if...", "Certainly!", "Let's dive in!")

### Context tolerance

Tier 1 replacements are mandatory in all contexts. Tier 2 and Tier 3 strictness varies:

| Content type | Tier 2 / Tier 3 strictness |
|---|---|
| Investor/executive email | Strictest — no promotional language |
| Customer-facing summary | Strict — empathy OK, no AI tells |
| Technical blog | Moderate — technical terms get passes |
| Internal docs/runbooks | Relaxed — clarity over style |
| Slack messages | Most relaxed — conversational is fine |

## Sentence and paragraph craft (Williams / Pinker reference)

### Given/New contract (Williams)
Every sentence's subject should carry old (given) information; its predicate should carry new information. Violations make text feel jumpy.
- Bad: "Many companies use containers. Containers are the unit that..."
- Good: "Many companies use containers. These containers package..."
- Apply when: text feels choppy or each sentence opens a new topic.

### Topic-sentence-first vs buried-lede paragraphs
A topic sentence at the start signals the point; a buried lede forces the reader to extract it. Default to topic-sentence-first for business and technical writing; buried-lede is acceptable in narrative writing for surprise.
- Bad: 5-sentence paragraph where the actual claim is sentence 5.
- Good: Sentence 1 makes the claim; sentences 2–5 support it.
- Apply when: paragraphs feel like they bury the point.

### Verb-first sentences (kill nominalization)
A nominalization turns a verb into a noun ("perform a calculation", "make a decision"). Replace with the verb form ("calculate", "decide").
- Bad: "We made the decision to perform an investigation."
- Good: "We decided to investigate."
- Apply when: scanning verbs and finding "perform", "conduct", "make", "do" + noun.

### So-what test
Every paragraph should answer "so what?" — explicitly or implicitly. Read each paragraph and ask "so what?"; if there's no answer, cut.
- Bad: "MongoDB uses a document model. Documents live in collections. Collections live in databases." (three facts, no point)
- Good: "MongoDB's document model stores related data together, eliminating the joins that slow relational queries."
- Apply when: a paragraph feels like throat-clearing or filler.

### Concession-counter-claim ("Yes, X. But Y.")
Acknowledge the opposing view before stating yours. Shows consideration and disarms pushback.
- Bad: "We should use X." (no acknowledgement of objections)
- Good: "Yes, Y has lower latency. But Y costs 3x more, and our SLO is met with X."
- Apply when: writing persuasive prose anticipating disagreement.

### Headlines vs subheads
A headline tells the reader the conclusion; a subhead tells them the topic. Use headlines in business writing (claim-first), subheads in reference docs (topic-first).
- Headline: "Renewal at risk: TechCorp's CSAT dropped 30 points in Q3"
- Subhead: "TechCorp renewal status"
- Apply when: writing scannable content.

### Front-matter conventions (TL;DR / abstract / exec summary)
For full exec-summary structure see `## Document Type Templates → Executive Summary` above.
- **TL;DR:** ~1 paragraph, top of long documents, the conclusion.
- **Abstract:** ~150–300 words, formal documents, summarizes methods and findings.
- **Executive summary:** ~1 page, business documents, the decision context + ask.
- Pick one; don't stack all three.

### Footnote / endnote / inline-citation styles
- **Inline (parenthetical):** "(Williams, 1990, p. 50)" — APA-style, common in academic writing.
- **Footnotes:** numbered superscripts at the bottom of each page — common in legal/journalism.
- **Endnotes:** numbered superscripts gathered at the end — common in books.
- **Markdown link references:** `[claim][1]` with `[1]: https://...` — common in technical writing.
- Pick one and hold it throughout the document.

### Em-dash / en-dash / hyphen discipline
- **Hyphen (-):** compound modifiers ("data-driven"), prefixes ("non-trivial").
- **En-dash (–):** ranges ("pages 5–10"), connections between equals ("New York–London flight").
- **Em-dash (—):** parenthetical asides — like this — or to set off a strong break.
- AI-written prose over-uses em-dashes. Target ≤1 per 100 words in human prose.

### List-of-three rhythm
Three items lands harder than two or four. "Veni, vidi, vici." For business writing: lists of 3 feel complete; lists of 2 feel incomplete; lists of 4+ feel like a dump.
- Apply when: choosing how many examples to include.

### Parallelism in bulleted lists
Every bullet should start the same way: all noun phrases, all verb phrases, or all complete sentences. Do not mix.
- Bad: "- Increased CSAT\n- Reduce churn risk\n- The team is happier"
- Good: "- Increased CSAT by 15 points\n- Reduced churn risk by 30%\n- Improved team morale (Q3 survey)"
- Apply when: writing any bulleted list.

### Curse of Knowledge (Pinker)
You can't unknow what you know. Once expert, you forget what's hard for non-experts. Test by reading aloud to someone outside your domain, or by writing as if to your 6-months-ago self.
- Apply when: writing for an audience less expert than you.

### Cohesion vs coherence (Williams)
- **Cohesion** = local sentence-to-sentence flow (does sentence 2 connect smoothly to sentence 1?).
- **Coherence** = global argument structure (does the whole doc build toward one conclusion?).
- Both matter; they're different problems. Cohesion is sentence-level; coherence is structural.
- Apply when: text reads OK sentence-by-sentence but feels aimless overall (low coherence), or the argument is sound but prose feels jumpy (low cohesion).

## Additional craft concepts (deep reference)

The deep treatments of journalism structures (inverted pyramid, hourglass, bury-the-lede),
achievement frameworks (STAR/SOAR/PAR/CAR), sentence-level devices (deliberate fragments,
tricolon/isocolon, title vs sentence case, Oxford comma), cross-document consistency (style
sheets and term banks), the show-don't-tell evidence rule, the Curse of Expertise,
information scent, emphasis discipline (bold/italic/underline), and front-matter craft
(TL;DR, kicker, nutgraf, deck, tabular-vs-prose) each carry a rule, a worked example, and
source citations. **Read `references/advanced-craft.md` before giving a depth answer on any of
these** — the core rules above cover the common case; that file covers the edge cases and the
why.

<!-- cross-hub-map -->
## Cross-hub map — where every writing topic lives

This family is split across these hubs. If a task's deep material is **not** in this hub's Sub-skill
routing table, it is a reference file under a sibling hub below — **activate that hub or `Read` its
`references/<name>.md` directly**. Every former standalone skill in this family is now a reference under one
of these hubs (nothing was deleted).

| Hub | Owns | Example reference files |
| --- | --- | --- |
| `writing-expert` | Writing Expert (prose craft, voice, style, editing) — hub | `references/editing-and-revision.md`, `references/rhetorical-frameworks-deep.md`, `references/storytelling-and-narrative.md`, `references/headline-craft.md`, … |
| `technical-writing-craft` | Technical & Product Writing (docs, specs, engineering comms) — hub | `references/api-docs-craft.md`, `references/howto-writing.md`, `references/tutorial-writing.md`, `references/knowledge-base-authoring.md`, … |
| `executive-comms` | Executive & Business Communication (leadership, persuasion, decks) — hub | `references/one-pager-writing.md`, `references/okr-writing.md`, `references/proposal-and-grant-writing.md`, `references/pitch-deck-writing.md`, … |
| `content-and-marketing-writing` | Content, Marketing & External Comms (PR, newsletters, launch, social) | `references/sales-and-marketing-copy.md`, `references/press-release-writing.md`, `references/crisis-pr-writing.md`, `references/newsletter-writing.md`, … |
| `career-and-formal-writing` | Career, Academic, Legal & Formal Writing | `references/resume-and-cv-writing.md`, `references/cover-letter-writing.md`, `references/job-description-writing.md`, `references/performance-review-writing.md`, … |
