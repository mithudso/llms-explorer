---
title: "Visual Writing"
description: "Reference for the words that ship with images, charts, and infographics: alt text, captions, chart titles, axis labels, and annotations. The image is half the message. This skill is the other half."
---

# Visual Writing

Reference for the words that ship with images, charts, and infographics: alt text, captions, chart titles, axis labels, and annotations. The image is half the message. This skill is the other half.

## The one rule: visual writing makes images legible without the image

Every other rule in this skill follows from one premise: a reader who cannot see the image must still receive the load-bearing information. That reader may be a blind user with a screen reader, a sighted user on a slow network, a sighted user skimming for the chart's takeaway, or a search engine indexing the page.

- **The alt text serves the screen reader.**
- **The caption serves the skimmer.**
- **The chart title serves the takeaway.**
- **The annotation serves the trend.**

They are four jobs, not one.

## Core concept 1 — The alt-text triple

Alt text answers three questions:
1. **What's there?** — concrete, observable content
2. **Why is it there?** — the function the image serves in the page
3. **What does it show?** — the specific information a sighted reader gets

## Core concept 2 — The W3C alt-decision-tree categories

| Image type | Alt text strategy | Example |
|------------|-------------------|---------|
| **Decorative** | Empty alt (`alt=""`) | A flourish, a hero-section gradient |
| **Informational** | Describe the information | "Bar chart: 2024 revenue rose 18% over 2023" |
| **Functional** | Describe the function, not the icon | `alt="Search"` for the magnifying-glass icon |
| **Image of text** | Repeat the text verbatim | A logotype reading "Acme Corp" → `alt="Acme Corp"` |
| **Complex** | Short alt + long description nearby | `alt="Cluster topology diagram (long description below)"` |

## Core concept 3 — Caption vs alt text vs long description

- **Alt text** is for users who cannot see the image. It lives in `alt=""`. Typically 5 to 15 words.
- **Caption** is visible to everyone. It lives in `<figcaption>`. Adds context, attribution.
- **Long description** is a structured prose alternative for complex images.

**Anti-pattern: duplication.** If `alt="Sales rose 18% in Q4"` and the caption reads the same, the screen-reader user hears it twice.

## Core concept 4 — Tufte's principles

1. **Above all else, show the data.** Title and labels exist to disclose the data.
2. **Maximize the data-ink ratio.** Erase ink that doesn't carry data.
3. **Erase redundant data-ink.** A bar chart with a legend, title, axis labels, and a redundant data table embeds the same fact four times.
4. **Reject chartjunk.** Heavy gridlines, moiré fills, 3-D effects, drop shadows.
5. **Use sparklines for in-line trend.** Caption a sparkline like a word — usually with just the latest value.

## Core concept 5 — The Knaflic "action title" rule

The chart title states the takeaway. The axis labels confirm it.

**Generic title (descriptive only):**
> Quarterly Revenue, 2023–2024

**Action title (takeaway-bearing):**
> Q4 2024 revenue exceeded plan by 18% — the strongest quarter on record

**Rule of thumb: no chart without a takeaway.** If you cannot state in one sentence what the chart is for, either find the takeaway or delete the chart.

## Core concept 6 — Axis labels

1. **Label the units.** "Revenue (USD millions)" not "Revenue."
2. **Date axes get human dates.** "Jan 2024" — not raw timestamps, not "Q1".
3. **Avoid axis label rotation.** If labels overflow horizontally, the chart probably has too many categories.

## Core concept 7 — Annotations

An annotation is a written assertion attached to a specific data point. Use annotations for:
- The single highest or lowest point ("**peak: 8,420 — Aug 14**")
- A regime change ("← deploy of v2.3")
- An anomaly ("backfill artifact; ignore")

**Annotations are journalism inside a chart.** Empty annotations ("note this") are wasted ink.

## Core concept 8 — Accessible data-viz captioning

The "describe the trend, then the value" pattern:

> Sales increased steadily from January to July, then declined through December. The peak was 8,420 units in July. The lowest month was December at 3,100 units.

**Anti-pattern: read every value.**
> January was 4,200, February was 4,800, March was 5,100...

If every value matters, provide a `<table>` and skip the chart alt-text recital.

## Templates

### Alt-text formula for charts

```text
[Chart type]: [trend / takeaway]. [Key value]. [Anomaly or outlier].

Examples:
"Line chart: API latency rose steadily from May to August, peaking at 480 ms
on Aug 14, then dropped back to 140 ms after the Aug 22 deploy."

"Bar chart: Q4 2024 revenue exceeded plan by 18% — the strongest quarter on record."
```

### Chart takeaway title — before / after

| Generic descriptive | Action title |
|---|---|
| "Quarterly Revenue" | "Q4 2024 was the strongest quarter on record" |
| "Customer Churn by Month" | "Churn doubled in March after the price change" |
| "API Latency, P95" | "Latency stabilized after the Aug 22 deploy" |

## Anti-patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| `alt="image"` or `alt="picture of X"` | Adds no information | Describe what's shown |
| Alt text identical to the visible caption | Screen reader hears it twice | `alt=""` and `aria-labelledby` the caption |
| Reading every chart value in alt text | Long, useless | Trend + key value + outlier |
| Descriptive chart titles only ("Quarterly Revenue") | Reader has to extract the meaning | Action title with takeaway |
| Chartjunk: 3-D bars, drop shadows | Hides data | Strip to data-ink |

## References

- W3C WAI: [Images Tutorial](https://www.w3.org/WAI/tutorials/images/) and [Alt Decision Tree](https://www.w3.org/WAI/tutorials/images/decision-tree/)
- Edward Tufte, *The Visual Display of Quantitative Information* (2nd ed., 2001)
- Cole Nussbaumer Knaflic, *Storytelling with Data* (2015)
- UK GDS: [Text descriptions for data visualisations](https://accessibility.blog.gov.uk/2023/04/13/text-descriptions-for-data-visualisations/)
- WCAG 2.1, Success Criterion 1.1.1 (Non-text Content)
