---
title: "Survey Question Writing"
description: "A survey question is a measurement instrument. Bad wording does not just irritate respondents — it injects measurement error that downstream statistics cannot fix."
---

# Survey Question Writing

## Overview

A survey question is a measurement instrument. Bad wording does not just irritate respondents — it injects measurement error that downstream statistics cannot fix.

Default mental model: every question is a hypothesis about what the respondent will read. If two thoughtful readers could parse the stem differently, the question is broken.

## Core Concepts

### 1. Question-stem hygiene (Dillman)

Stems must be **direct, concrete, mutually exclusive, and answerable in one read**:
- **One concept per question** — no "and/or" coordination across distinct constructs.
- **Common vocabulary** — no jargon.
- **Concrete time window** — "in the last 30 days" not "recently".
- **Specified reference** — "your most recent purchase" not "purchases".
- **Symmetric framing** — avoid "do you agree that X is good" (loaded).

### 2. Likert scales: 5-point vs 7-point

| Decision | Use 5-point | Use 7-point |
|---|---|---|
| Mobile / short pulse | Yes | Avoid |
| Need granularity (academic, MTMM) | No | Yes |
| Comparing to existing 5-pt benchmarks | Yes | No |

**Default: 5-point** for operational customer/employee surveys. **7-point** when you need discrimination for regression/factor analysis.

### 3. Balanced anchors and label coverage

A balanced scale has the same number of positive and negative points around a neutral midpoint, with **labels on every point**.

- Good: Strongly disagree / Disagree / Neither / Agree / Strongly agree
- Bad: Hate it / Dislike / Neutral / Like / Love (asymmetric intensity)

### 4. NPS, CSAT, and CES — pick one per question

| Metric | Question wording | Scale | Use when |
|---|---|---|---|
| **NPS** (Reichheld 2003) | "How likely is it that you would recommend [company/product] to a friend or colleague?" | 0–10 | Loyalty, top-line growth proxy |
| **CSAT** | "How satisfied were you with [specific experience]?" | 1–5 or 1–7 | Post-interaction satisfaction |
| **CES** | "[Company] made it easy to handle my issue." | 1–7 | Service/support friction |

**Do not modify the NPS stem** if you want to compare to industry benchmarks. NPS scoring: 0–6 = Detractors, 7–8 = Passives, 9–10 = Promoters.

### 5. The agree-disagree anti-pattern (Saris & Gallhofer 2014)

"Do you agree or disagree that [statement]?" invites acquiescence bias (respondents lean toward "agree").

- Anti-pattern: "Do you agree that the website is easy to use?" (5-pt agree/disagree)
- Better: "How easy or difficult is the website to use?" (Very difficult ... Very easy)

Item-specific scales reduce systematic error and increase reliability.

### 6. Double-barreled and leading questions

**Double-barreled** = one question, two concepts. Split it.

- Bad: "How satisfied are you with the price and quality of the product?"
- Fix: Two questions, one for price, one for quality.

**Leading** = stem prejudges the answer.

- Bad: "How helpful was our amazing support team?"
- Fix: "How would you rate the support you received?" (Very poor ... Very good)

### 7. "Don't Know" vs "Neutral" vs forced-choice

- **Neutral midpoint** = respondent has an opinion but it is centered.
- **"Don't Know" / "Not applicable"** = respondent lacks the information. Place it **visually offset from the scale** (Dillman) so satisficers don't select it by default.
- **Forced-choice** = use only when you genuinely need a side.

### 8. Ordering effects

- **Question order**: early questions can prime later ones. Put sensitive/demographic questions last. Put the headline metric (NPS/CSAT) before drill-downs.
- **Response option order**: randomize unordered option lists across respondents. Never randomize a Likert.
- **Matrix straight-lining**: long batteries of similar Likert items invite straight-lining.

### 9. Open- vs closed-ended

- **Closed-ended** = the default for quantitative analysis, benchmarking, large samples.
- **Open-ended** = use sparingly (1–2 per survey). Place after the closed question that primed the topic.

### 10. Mobile constraints

- Stem ≤ 20 words; aim for ≤ 12.
- Scale ≤ 7 points (5 preferred).
- Avoid grids/matrices on mobile — collapse to single-question-per-screen.
- Total survey ≤ 5 minutes for transactional touchpoints.

## Templates

### NPS (canonical, do not modify the stem)

> How likely is it that you would recommend [Company/Product] to a friend or colleague?
> 0 (Not at all likely) — 10 (Extremely likely)

### Generic attribute rating (item-specific, preferred over agree-disagree)

> How would you rate the [speed / clarity / accuracy] of the response you received?
> Very poor — Poor — Fair — Good — Excellent

### Rewrite examples

| Original (broken) | Rewrite | Why |
|---|---|---|
| "Do you agree that our new pricing is fair and competitive?" | "How would you rate our pricing?" (Very unfair ... Very fair) | Agree-disagree + double-barreled |
| "How helpful was our amazing support team?" | "How would you rate the support you received?" | Leading adjective |
| "Recently, how often have you used the dashboard?" | "In the last 30 days, how many times did you open the dashboard?" | Vague time + vague frequency |

## Anti-Patterns

- **Agree-disagree everything.** Causes acquiescence bias.
- **Double-barreled stems.**
- **Loaded adjectives** in stems.
- **Endpoint-only labels on 7-pt scales.**
- **Random Likert order.** Never randomize ordered response options.
- **Modifying the NPS stem.** Breaks benchmark comparability.
- **Stacking NPS + CSAT + CES + 10 drill-downs.** Pick a primary metric per touchpoint.

## References

1. Dillman, D. A. *Internet, Phone, Mail, and Mixed-Mode Surveys: The Tailored Design Method* (4th ed.). Wiley.
2. Saris, W. E., & Gallhofer, I. N. *Design, Evaluation, and Analysis of Questionnaires for Survey Research* (2nd ed.). Wiley.
3. Reichheld, F. F. "The One Number You Need to Grow." *Harvard Business Review*, 2003.
4. Pew Research Center. "Writing Survey Questions." https://www.pewresearch.org/writing-survey-questions/
