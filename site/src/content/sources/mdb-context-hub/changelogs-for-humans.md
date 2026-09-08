---
title: "Changelogs for Humans"
description: "Reference for user-facing changelog craft: the public-product update feed read by end users, not the engineering changelog read by integrators."
---

# Changelogs for Humans

Reference for **user-facing changelog craft**: the public-product update feed read by end users, not the engineering changelog read by integrators.

## How to use this skill

1. **Confirm the audience is the end user, not the developer/integrator.**
2. **Identify the surface.** Public changelog feed / monthly digest email / in-product "What's New" panel?
3. **Group by user benefit, not by file tree.**
4. **Lead with the outcome, not the mechanism.**
5. **Decide on visual treatment.** Major UI changes get a screenshot or GIF.
6. **Decide on version-number visibility.**

## 1. The shape of a user-facing changelog

```text
[Date]
## [Headline framed as a user benefit, not a feature name]

[One- to three-paragraph narrative explaining what changed and what it means.]

[Optional screenshot, GIF, or short video — inline, large, high contrast.]

─── Smaller items below the fold ──────────────────────────

• Bug fix: [user-visible symptom, not stack trace]
• Improvement: [outcome verb]
```

## 2. Group by user benefit, not by file tree

| Engineering grouping (wrong here) | User-benefit grouping (right) |
|---|---|
| `auth-service`, `billing-api`, `webhook-worker` | "Faster sign-in," "Clearer billing," "Webhooks you can trust" |
| `feat:`, `fix:`, `chore:`, `refactor:` | "New," "Improved," "Fixed" |
| Version `1.42.0`, `1.42.1` | "May 14," "May 21" — dated, not versioned |

## 3. Benefit-led language

| Engineering wording | Benefit-led rewrite |
|---|---|
| "Migrated sync layer to WebSockets" | "Changes now appear instantly on every device" |
| "Improved performance" | "Dashboard loads in under one second on slow connections" |
| "Added pagination to API endpoint" | "Lists with more than 100 items now load without timing out" |
| "Upgraded to Postgres 16" | (Omit. Internal change, no user-visible effect.) |
| "Fixed bug in import handler" | "Fixed: CSV imports no longer drop the last row" |

**Rules:**
1. **Replace internal nouns with user verbs.**
2. **Quantify when honest.** "3x faster" is honest if measured.
3. **Cut entries with no user-visible effect.**
4. **Name the bug by the symptom, not the cause.**
5. **Keep one sentence per atom.**

## 4. Visuals — when, where, what

| Change type | Visual |
|---|---|
| New UI surface | Static screenshot, full-bleed |
| Interaction change | Short GIF, 4–8 seconds |
| Workflow change spanning multiple screens | Captioned screenshot pair, before/after |
| Performance improvement | Optional: chart or "before/after" timer |
| Bug fix | None |

**Image craft checklist:**
- Real product data wherever the user's eye lands.
- Dark mode if your product has dark mode.
- Crop tightly.
- Alt text describes the change, not the chrome.
- GIFs: under 5 MB, autoplay-on, loop.

## 5. Version numbers — hide, downplay, or omit

Linear, Vercel, GitHub, Notion: no version numbers in the user changelog. The date is the version.

## 6. Channels and distribution patterns

| Channel | Length | Visual | Cadence |
|---|---|---|---|
| **Public changelog page** | Long form per entry | Inline screenshot/GIF | Per-ship |
| **In-product "What's New" panel** | 1–2 sentences per item | Small thumbnail or icon | Weekly to monthly |
| **Monthly digest email** | "Top 5 of the month" | Hero image + per-section | Monthly, fixed date |

## 7. Monthly digest pattern (Mailchimp / Notion style)

```text
Subject: What's new in [Product] — [Month Year]

[Hero image]

[Month] in [Product]
[One opening paragraph — the editorial framing of the month.]

The big one
  [Flagship change, 2-3 sentences, screenshot or GIF, "Learn more" link]

Smaller wins
  • [Item, one line, link]
  
Coming soon [Optional]

Footer: link to full changelog, unsubscribe, RSS link
```

## Anti-Patterns

- **The version-number-only changelog.** "v1.42.0 — bug fixes and improvements." This is not a changelog.
- **The "we're excited to announce" opener.** Cut. Open with the change.
- **The commit-log dump.** Pasting `git log --oneline` into a webpage.
- **The "improved performance" non-entry.** Either quantify it or omit it.
- **The screenshot of nothing.** Always shoot with realistic data.
- **The "internal upgrade" entry.** "We upgraded our database to version 16." The user does not care.

## References

- Linear changelog — linear.app/changelog
- Vercel changelog — vercel.com/changelog
- Stripe Blog: Changelog — stripe.com/blog/changelog
- Mailchimp "What's New" — mailchimp.com/whats-new
