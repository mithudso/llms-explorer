---
title: "NPS Response Writing"
description: "This skill covers how to write replies to customer feedback collected at scale — NPS verbatim comments, CSAT free-text, post-support survey replies, and public app-store reviews."
---

# NPS Response Writing

## Overview

This skill covers how to write replies to customer feedback collected at scale — NPS verbatim comments, CSAT free-text, post-support survey replies, and public app-store reviews.

Three things make these responses different from support replies:
1. **The customer did not ask for help.** They volunteered feedback.
2. **The score is the spine.** Detractor (0–6), passive (7–8), and promoter (9–10) responses calibrate differently.
3. **Cadence is short.** Under 48 hours for detractors, under 72 hours for app-store replies.

## Core Concepts

### 1. The thank/acknowledge/route/commit template

1. **Thank** — one line, specific to the act of giving feedback, not the score.
2. **Acknowledge** — quote or paraphrase the specific point. Proves you read it.
3. **Route** — name what happens next internally. Be specific: "I'm sending this to our billing team's weekly review on Thursday" beats "I'll route this to the right team."
4. **Commit** — one concrete next step you (the responder) own, with a date or trigger.

### 2. Detractor vs passive vs promoter calibration

| Tier | Score | Customer state | Response goal | Length |
|------|-------|----------------|---------------|--------|
| Detractor | 0–6 | Frustrated, considering churn | Understand the specific failure; offer a save conversation | 4–8 sentences |
| Passive | 7–8 | Satisfied but unenthusiastic | Convert: ask one targeted question about what would have made it a 9 | 3–5 sentences |
| Promoter | 9–10 | Enthusiastic | Deepen the relationship; harvest specifics for marketing/CS | 2–4 sentences |

### 3. The "I'll route this to engineering" anti-pattern

"I'll pass this along to the team" signals that the responder has no agency. Replace with:
- A named destination: "I'll add this to our March platform-stability review."
- A named owner: "Our billing PM, Priya, will see this on Monday."
- An explicit decline: "I can't promise this gets prioritized — we're locked on Q2 commitments — but I've logged it under [theme]."

### 4. Closed-loop response cadence

- **Detractor first response:** within 24–48 hours.
- **Passive reply:** within 1 week.
- **Promoter reply:** within 2 weeks.
- **App-store reply:** within 72 hours.
- **Loop close-out** (confirming resolution back to the customer): within 30 days.

### 5. When an NPS verbatim becomes a save call

Escalate to a live conversation when any of these appear:
- Explicit churn language: "evaluating alternatives," "renewal is up"
- A specific named individual who is angry
- A claim of broken commitment ("you promised us X")
- Compounding issues ("this is the third time…")
- Legal/compliance language: "data breach," "GDPR," "lawsuit"

### 6. The honest-decline reply

1. Acknowledge the specific point.
2. State the trade-off plainly: "We deliberately chose X over Y because [reason]."
3. Offer the closest workaround you can.
4. Leave the door open: "If this stays a blocker for you, I want to know."

## Templates

### Detractor (NPS 3, verbatim: "Support takes forever and your billing portal is broken")

> Hi Sarah,
>
> Thanks for being direct in the survey — that's more useful to us than a polite 7.
>
> Two specific things you flagged: support response time, and the billing portal. On support: I pulled your last four tickets and the median first-response was 19 hours, which is outside our SLA for your plan. That's on us. On billing: the portal had a known issue with invoice downloads through last Tuesday; it's fixed now, but you would have hit it.
>
> I'm doing two things. First, I've flagged your account to our support lead, who will personally route your next three tickets. Second, I'd like 20 minutes with you this week to hear what "fast enough" looks like for your team.
>
> Tuesday or Thursday afternoon work?

### Passive (NPS 8, verbatim: "It's good, just nothing exciting")

> Hi Alex,
>
> Thanks for the note — "good but not exciting" is genuinely useful for us, more than a 10 with no comment would be.
>
> If you don't mind a quick question: what would have made it a 9 or 10 for you? One thing, off the top of your head, is enough.

### App-store 1-star reply (consumer iOS)

> Sorry the import flow blocked you on a 200MB file — that's a real bug, not the experience we want. We shipped a fix in v4.7.2 last week that raises the limit to 2GB and adds a progress indicator. If it's still failing for you, email support@[app].com.

## Anti-Patterns

- **The form-letter thank-you.** "Thank you for your valuable feedback." Reads as bot output.
- **The unprompted apology.** Saying "I'm sorry" to a passive (NPS 8) signals you read them as a detractor.
- **The route-to-the-void.** "I've passed this along to the team" with no named destination.
- **The re-survey ask before resolution.** Asking a detractor to re-rate before you have fixed anything.
- **The marketing voice.** "we're committed to delivering delight" to a frustrated customer.
- **The upsell smuggled into a promoter reply.**

## References

- [Introducing the Net Promoter System | Bain & Company](https://www.bain.com/insights/introducing-the-net-promoter-system-loyalty-insights/)
- [Net Promoter 3.0 | Bain & Company](https://www.bain.com/insights/net-promoter-3-0/)
- [How to respond to app store reviews | MobileAction](https://www.mobileaction.co/guide/how-to-respond-to-app-store-reviews/)
