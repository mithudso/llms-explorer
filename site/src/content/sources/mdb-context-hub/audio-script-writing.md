---
title: "Audio Script Writing"
description: "Reference for writing that will be heard, not read. The eye can re-scan a sentence; the ear gets one pass."
---

# Audio Script Writing

Reference for writing that will be heard, not read. The eye can re-scan a sentence; the ear gets one pass.

## The one rule: writing for the ear is single-pass

Listeners process roughly **150–160 words per minute** for narration, **130–145 wpm** for voice-UI prompts, and **110–125 wpm** for IVR. They lose comprehension on:

1. Subordinate clauses stacked more than one deep
2. Parentheticals (the ear has no parens)
3. Lists longer than three items without explicit numbering
4. Numbers and proper nouns delivered without a beat of silence after

## Core concept 1 — The one-idea-per-sentence rule

**Eye version (fine on the page):**
> The migration, which we'd been planning since February, finally launched on Tuesday after a final round of testing that revealed two minor bugs we patched overnight.

**Ear version:**
> We'd been planning the migration since February. It finally launched on Tuesday. The last round of testing turned up two small bugs. We patched them overnight.

## Core concept 2 — Signposting

**Signpost vocabulary:**
- **First / second / third / finally** — explicit numbering
- **Here's the thing** — flag a key insight
- **Two reasons** — set up a numbered list
- **Coming up** — preview before an ad break
- **Back to the story** — return marker after a digression

## Core concept 3 — No parentheticals, no em-dashed asides

- Before: "The team (which had only formed in January) shipped on time."
- After: "The team shipped on time. They'd only formed in January."

## Core concept 4 — Pacing markers as breath beats

| Mark | Pause length | Function |
|------|--------------|----------|
| Comma | ~100 ms | mid-sentence beat |
| Period | ~250 ms | sentence boundary |
| Em-dash or ellipsis | ~350–500 ms | dramatic pause |
| Paragraph break | ~750 ms–1.5 s | scene change |
| `[pause]` stage direction | author-specified | deliberate silence |

## Core concept 5 — The cold open

Three patterns that work:

**Pattern A — Drop into a scene:**
> It's 2 a.m. The paging system goes off. Marcus rolls over, reads the alert, and the alert is wrong.

**Pattern B — A question with stakes:**
> What would you do if your entire backup tier disappeared in the middle of a restore?

**Pattern C — A single startling fact:**
> Last year, 47% of incident retrospectives never produced a single action item.

**Anti-pattern — The throat-clear:**
> Hi everyone, welcome to the podcast. Today we're going to be talking about...

## Core concept 7 — Voice-UI prompts (Alexa, Google Assistant, Siri)

Three constraints beyond "writing for the ear":
1. **The prompt must end with an explicit prompt-for-input.**
2. **Confirm without echoing.** "Adding milk to your list" is good; "I heard you say milk; I will now add milk to your list" is voice-UI throat-clearing.
3. **Three-option ceiling.** Lists of more than three options exceed working memory.

## Core concept 8 — IVR scripts

1. **Most-likely path first.** Order by call-volume share, not alphabetical.
2. **Always offer a human escape.** "Press 0 at any time to reach an agent."
3. **Confirm critical inputs.** Read back at the cadence a person can write down.
4. **Re-prompt twice, then escalate.** Caller silence twice in a row = route to agent.

## Core concept 10 — Podcast show notes craft

**Required sections:**
1. Episode title — keep under 60 characters; concrete, specific
2. One-paragraph summary — 50–80 words; uses the episode keyword once
3. Chapter timestamps — 4–8 chapters; `[12:15] How to find your first sponsor`
4. Guest bio — 1 paragraph, links to guest sites
5. Mentioned resources — every link spoken aloud
6. Transcript — full or summary
7. Call to action

## Anti-patterns

| Anti-pattern | Why it fails | Fix |
|--------------|--------------|-----|
| Long sentences with nested clauses | Ear loses the through-line | One idea per sentence |
| Em-dashes and parens in spoken prose | No audio equivalent | Hard sentence break |
| Throat-clear intros | Loses 20–30% in 60s | Cold open first |
| Voice-UI prompt without input request | Caller doesn't know it's their turn | End with explicit prompt |
| IVR with no zero-out | Caller rage | Always offer human escape |
| Generic show-note chapter labels | No SEO, no scannability | Concrete labels with keywords |

## References

- NPR Training: "How to write a mean script"
- Google: Conversation Design
- Amazon: Alexa Design Guide
- Buzzsprout: "How to Write Podcast Show Notes"
