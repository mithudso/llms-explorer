---
title: "Chatbot Conversation Writing"
description: "A chatbot is a conversation, not an interface. Every turn the bot takes should advance the user's goal or surface a clear next move. The work breaks into three layers:"
---

# Chatbot Conversation Writing

## Overview

A chatbot is a conversation, not an interface. Every turn the bot takes should advance the user's goal or surface a clear next move. The work breaks into three layers:

1. **Persona** — who the bot is, what it sounds like, what it refuses to do.
2. **Turn design** — the individual response, plus the choices it offers.
3. **Recovery design** — what happens when the bot doesn't understand, when the user is angry, or when the conversation has to leave the bot.

## Core Concepts

### 1. Cooper-Reeves conversational design

The four Gricean maxims:
- **Quantity** — say as much as is needed, not more
- **Quality** — only say true things
- **Relation** — stay on the user's topic
- **Manner** — be clear, brief, and orderly

### 2. Persona consistency

A minimum persona doc includes:
- **Name** (or explicit no-name policy)
- **Role** (what the bot is for — support? sales? in-product help?)
- **Voice traits** (3–5 adjectives — e.g., "warm, precise, never cute")
- **Refuses to do** (e.g., diagnose medical issues, take payment, promise pricing)
- **Vocabulary** (3–5 words it uses; 3–5 it doesn't)
- **Disclosure boilerplate** (the exact "I'm an AI assistant" line)
- **Escalation trigger phrases**

### 3. The "no, I'm not human" disclosure rule (2024–2026 norms)

As of 2026, plain-and-unambiguous AI disclosure is no longer optional:
- **California SB 243** (effective Jan 1, 2026) requires disclosure, plus reminders every three hours for minor users
- **EU AI Act** requires upfront disclosure for any AI system interacting with natural persons
- **FTC** treats undisclosed AI as potentially deceptive

Writing implications:
- **Disclose in the first turn**, not buried in a tooltip
- Use direct language: "I'm an AI assistant" — not "I'm an enhanced automation experience"
- **If asked "are you a human?"** answer plainly: "No, I'm an AI assistant."

### 4. Turn-taking conventions

A conversational turn has three jobs:
1. **Acknowledge** what the user just said
2. **Resolve** the user's intent
3. **Hand the turn back** with a clear next move

Length convention: **1–3 short sentences** per turn for support bots, **1–5 sentences** for in-product help.

### 5. The graceful-confusion pattern

When the bot doesn't understand, three things must happen:
1. **Admit it cleanly.** "I'm not sure what you mean by 'reset'."
2. **Offer a small, finite menu.** Two or three concrete interpretations.
3. **Provide a path out.** Always include "talk to a human" no later than the second failed understanding.

### 6. Fallback hierarchies

| Tier | Trigger | Response |
|---|---|---|
| **T1: Clarify** | Low-confidence intent match | "Did you mean X or Y?" |
| **T2: Reframe** | Two failed clarifications | "I can help with A, B, or C. Which is closest?" |
| **T3: Offer human** | Three failed turns, or angry-sentiment trigger | "Let me get a human on this." |
| **T4: Hard escalation** | Keywords: fraud, emergency, refund, account locked | Immediate handoff |

### 7. Brand-voice-in-bot transfer

Three transfer rules:
- **Drop the edge in failure modes.** Humor in a working flow is fine. Humor when the user is locked out is not.
- **Keep the rhythm, simplify the vocabulary.**
- **Reuse hero phrases sparingly.** One signature phrase per conversation.

### 8. Escalation-to-human prose

Three elements must be present:
1. **Confirm the handoff is happening.** "I'm connecting you to a person now."
2. **Preserve context.** "I'll share what we've discussed so you won't have to repeat yourself."
3. **Set the wait expectation.** "Average wait is about 4 minutes."

## Anti-Patterns

- **The "I'm an enhanced automation experience" dodge.** Coy disclosure reads as deceptive.
- **The infinite "I didn't understand, please rephrase" loop.** Two failures is the ceiling; escalate.
- **The hidden escalation path.** Surface the escalation in the conversation itself.
- **The promise-the-bot-can't-keep.** "I'll refund you" when refund authority is human-only.

## References

- Erika Hall, *Conversational Design* (A Book Apart, 2018).
- California SB 243 (Companion Chatbot Disclosure Act), effective Jan 1, 2026.
- EU AI Act Article 50 (transparency obligations for AI systems).
- Byron Reeves and Clifford Nass, *The Media Equation* (CSLI / Cambridge, 1996).
