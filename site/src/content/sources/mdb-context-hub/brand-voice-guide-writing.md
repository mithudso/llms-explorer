---
title: "Brand Voice Guide Writing"
description: "Authoring craft for the brand voice guide as an artifact. The output is a document other writers will open, reference, and apply."
---

# Brand Voice Guide Writing

Authoring craft for the brand voice guide *as an artifact*. The output is a document other writers will open, reference, and apply.

## Overview

A brand voice guide answers four questions for every writer who opens it:

1. **Who do we sound like?** (Voice — the constant.)
2. **How do we shift in different situations?** (Tone — the variable.)
3. **Which words do we use, and which do we never use?** (Vocabulary.)
4. **What does this look like in practice?** (Examples — usually do/don't pairs.)

If a guide doesn't make these four questions answerable in under 10 minutes of reading, it will be ignored.

## Core Concepts

### 1. The four-section skeleton

1. **Voice** — three to five attributes that describe the constant personality. State each as "We are X. We are not Y." (Bloomstein's BrandSort framing: include the *not*.)
2. **Tone** — a matrix showing how voice flexes by situation.
3. **Vocabulary** — preferred words, banned words, and grammar/style decisions specific to the brand.
4. **Examples** — at least 5 do/don't pairs spanning the highest-traffic surfaces.

### 2. Voice attributes — the "we are X, we are not Y" pattern

The canonical format:

> **Confident, not arrogant.** We make declarative claims when we know we're right. We don't oversell, hedge with weasel words, or talk down to readers who know less than us.
>
> **Warm, not saccharine.** We sound like a competent colleague who likes their job. We don't use exclamation marks to perform enthusiasm or call readers "friend."

Three to five attributes is the sweet spot.

### 3. The brand-voice spectrum chart (typically 3 axes)

The Nielsen Norman Group axes: formal↔casual, serious↔funny, respectful↔irreverent, enthusiastic↔matter-of-fact.

```text
Formal        |---------------●---|        Casual
Serious       |---●---------------|        Playful
Matter-of-fact|---------●---------|        Enthusiastic
```

**Anti-pattern:** Putting all markers in the middle. "Moderately formal, moderately serious, moderately enthusiastic" is no voice.

### 4. The tone-shifts matrix

| Situation | Tone shift | Example |
|---|---|---|
| User succeeded (deploy passed) | Brief, warm, low-key | "Deployed in 47s. You're live." |
| User failed (deploy errored) | Direct, calm, no blame | "Deploy failed at build step. Logs below." |
| Onboarding (first-run) | Patient, encouraging, no jargon | "First time? We'll walk you through it." |
| Marketing (new feature) | Confident, specific, no hype | "Indexes now rebuild without a write pause." |
| Legal / policy update | Plain, precise, no marketing | "We updated our privacy policy on May 1." |

### 5. Do/don't pairs (the "this but not that" convention)

> **Do:** "We paused your build. Resume it when ready."
> **Don't:** "Oops! Looks like your build got paused. No worries — just click Resume whenever you'd like to keep going! 🚀"

The don't side teaches more than the do side. Pick don'ts from real drafts your team has actually shipped.

### 6. Vocabulary section: preferred, banned, and decisions

- **Preferred** — words that carry the voice. ("ship" not "release"; "you" not "the user".)
- **Banned** — words that break the voice. ("leverage", "synergy", "seamless", "robust", "delightful", "passionate".)
- **Decisions** — product-name capitalization, oxford comma, contractions allowed, em dash vs en dash.

### 7. Dating and versioning discipline

Every voice guide should display:
- **Version** (semver or date)
- **Last reviewed** date
- **Owner** (a person, not a team)
- **Next review** date (no more than 12 months out)

## Anti-Patterns

1. **No "we are not."** Lists three positive attributes with no opposites.
2. **Spectrum markers all centered.** "Moderately formal" is no guidance.
3. **Don't-side strawmen.** Don't pairs that are obviously bad teach nothing.
4. **No date, no owner.** Writers won't trust an undated guide.
5. **30+ page voice guide.** Anything past 10 pages won't be read.
6. **Banning words without preferring others.** "Don't say leverage" without "say use" leaves writers stuck.
7. **No tone matrix.** Writers can match personality but not situation.

## References

- [Mailchimp Content Style Guide — Voice and Tone](https://styleguide.mailchimp.com/voice-and-tone/)
- [Atlassian Design — Voice and Tone](https://atlassian.design/content/voice-and-tone/)
- Bloomstein, M. *Content Strategy at Work*. Morgan Kaufmann, 2012.
- Fenton, N. and Kiefer Lee, K. *Nicely Said*. New Riders, 2014.
- [Nielsen Norman Group — The Four Dimensions of Tone of Voice](https://www.nngroup.com/articles/tone-of-voice-dimensions/)
