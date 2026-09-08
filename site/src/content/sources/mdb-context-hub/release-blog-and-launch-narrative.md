---
title: "Release Blog and Launch Narrative"
description: "A launch is a one-shot narrative event — distinct from a landing page (steady-state conversion), an exec memo (internal alignment), or a changelog (continuous release log)."
---

# Release Blog and Launch Narrative

## Overview

A launch is a one-shot narrative event — distinct from a landing page (steady-state conversion), an exec memo (internal alignment), or a changelog (continuous release log).

## 1. Four launch archetypes

| Archetype | Narrative arc | Risk |
|---|---|---|
| **Category-defining** | "The old game is over. A new game is starting." | Overclaim; chasm failure |
| **GA / tier launch** | "We've been quietly proving this works. Now you can rely on it." | Audience asks "wasn't this already out?" |
| **Feature drop** | "You already use [product]. Here is the thing you've been asking for." | Lost in the noise |
| **Relaunch** | "We shipped this. You may have missed it. Here is why it matters now." | Embarrassment |

**Heuristic:** If you can't name the archetype in 10 seconds, the launch isn't ready.

## 2. The launch-post arc

### Beat 1 — Name the shift (the "why now")

Open with a one-paragraph claim about a shift in the world. **Never open with the product.** Andy Raskin's whole thesis: "the old game is over; a new game is starting."

| Strong | Weak |
|---|---|
| "Two years ago, paying online meant integrating with a bank. Today, it means writing seven lines of code." | "We're excited to announce a new feature." |

### Beat 2 — Stakes (the cost of the old game)

What does the reader lose by staying with the old way? Quantify if possible.

### Beat 3 — The reveal

Now — and only now — name the product and the one-line description. Apple's pattern: "Today, Apple introduced [X], a [category] that [primary benefit]."

### Beat 4 — Proof

Customer logos, quotes, measurable outcomes, demo link. One outside voice is worth ten internal claims.

### Beat 5 — Call to action and honesty

1. **Clear CTA** — one primary CTA, one secondary at most.
2. **What's not in v1** — the honest-disclosure section.

## 3. The "why now" paragraph

A working "why now" paragraph:
1. **Names a shift** that has already occurred.
2. **Establishes the cost** of operating as if the shift hadn't happened.
3. **Creates urgency** that is "you're already behind if you ignore this."

**Template:**
> Until recently, [old default] was the only way to [task]. But [shift A] and [shift B] have changed what's possible. Teams that adapt are [outcome]. Teams that don't are [cost]. Today we're announcing [product] to help you [verb] in this new world.

**Anti-pattern:** "AI is everywhere." This is a backdrop, not a why-now. It has no specific shift, no cost, no urgency.

## 4. The cross-channel launch ladder

```text
T-2 weeks   Analyst & press briefing (embargoed)
T-3 days    Pre-launch teaser; waitlist priority email
T=0         Blog post (canonical); Press release; Release notes published
T+0:05      Founder/CEO tweet thread; Company X/LinkedIn post
T+1 hour    Customer email blast; In-product announcement
T+1 day     Community post (Hacker News, Reddit, Discord) ← founder shows up
T+2 to +7d  Partner co-marketing; long-form deep-dive blog
```

**Sequencing rules:**
1. **The blog post is the canonical source.** Every other piece links to it.
2. **Analyst and press briefings are under embargo.**
3. **Release notes accompany the announcement.** When the blog post says "today we're launching X," the docs and the changelog must already reflect X.

## 5. The "what's not in v1" honesty section

**Template:**
> v1 deliberately ships without [X], [Y], and [Z]. We chose this scope to get [primary benefit] in your hands sooner. [X] is on the roadmap for [quarter]. If [X] or [Y] is a hard requirement for you today, [alternative path].

**What this section does:** Lets engineers in evaluation mode answer "can I use this yet?" without booking a call. Pre-empts the inevitable Hacker News commenter who finds the missing feature.

## 8. Anti-patterns

- **The "we're excited to announce" opener.** Cut. Open with the shift.
- **The "this changes everything" overclaim.**
- **The "product-first" structure.** Specs, then features, then maybe a sentence about who cares.
- **The hidden "what's not in v1."**
- **The "AI/cloud/edge is everywhere" why-now.**
- **The post that doesn't match the docs.**
- **The four-CTA ending.** If you list four CTAs the reader picks zero.

## 9. Success criteria for a launch

Define before launch day. Sample tiers:
- Unique pageviews on the blog post in week 1
- Tier-1 press hits
- Hacker News front page
- Signups attributable to launch
- New-product activation rate in week 1, week 4

## Launch blog post skeleton

```markdown
# [Product name]: [one-line description that names the new game]

By [Human Author], [Title] · [DATE]

[BEAT 1 — Why now.] Until recently, [old default]. But [shift]. [Cost of old default.]

[BEAT 2 — Stakes.]

[BEAT 3 — Reveal.] Today, we're launching [Product], a [category] that [primary benefit].

## [Capability 1, framed as outcome]
## [Capability 2, framed as outcome]
## [Capability 3, framed as outcome]

## How customers are using it
> "[Specific, quantified quote.]"
> — [Name, Title, Company]

## Get started

[Primary CTA]
[Secondary CTA, optional]

## What's not in v1
[Honest paragraph about scope cuts.]
```

## References

- Andy Raskin, "The Greatest Sales Deck I've Ever Seen" (Medium / Mission.org, 2016)
- Apple Newsroom (apple.com/newsroom)
- Linear changelog (linear.app/changelog)
- Stripe Blog launches (stripe.com/blog)
- Lenny Rachitsky, lennysnewsletter.com
