---
title: "Resume and CV Writing"
description: "A resume is read in 10-15 seconds on the first pass. It is parsed by an ATS (applicant tracking system) before any human sees it. It must survive the parse, then earn the human read, then earn the int"
---

# Resume and CV Writing

## Overview

A resume is read in 10-15 seconds on the first pass. It is parsed by an ATS (applicant tracking system) before any human sees it. It must survive the parse, then earn the human read, then earn the interview.

## Core Concepts

### 1. The X-Y-Z achievement formula (Laszlo Bock / Google)

> **Accomplished [X] as measured by [Y] by doing [Z].**

- **X** — the achievement or outcome (not the task).
- **Y** — the measurement: percentage, dollar amount, users, time saved, headcount, latency.
- **Z** — the approach, method, or tools that produced it.

Weak: "Responsible for sales." Better: "Increased sales 25%." X-Y-Z: "Increased Q1 regional sales 25% ($1.2M ARR) by launching a partner-channel program across three Midwest accounts."

### 2. Quantification discipline

Every bullet should contain a number unless physically impossible. Acceptable units: %, $, headcount, users, time saved, cycle-time reduction, NPS / CSAT delta, p95 latency.

### 3. ATS parse-friendly formatting

Failure modes:
- **Two-column layouts and tables** scramble field order.
- **Custom or decorative headings** ("My Journey," "What I Bring") confuse the parser.
- **Text boxes, graphics, embedded images** are often dropped entirely.
- **Non-standard fonts** can render as glyph junk.
- **PDF vs DOCX** — both work if text-selectable. Image-only PDFs fail the parse.

### 4. Role tailoring

For each target role: (a) reorder bullets so the top 3 in each job align with the target JD's stated priorities, (b) swap in keywords from the JD into the skills section, (c) rewrite the summary in the language the JD uses.

### 5. The skills section debate

Keep a skills section but limit it to: (a) hard tools and technologies, (b) certifications, (c) languages. Do not list soft skills ("communication," "leadership") — they are not parseable signals.

### 6. LinkedIn vs resume tone

The resume is third-person implicit and clipped ("Led a 5-engineer team that shipped..."). LinkedIn is first-person and conversational ("I lead a team that builds...").

### 7. Academic CV vs industry resume

**CV** (curriculum vitae): used for postdocs, faculty, some government-lab and research-institute roles. Several pages. Comprehensive: publications, presentations, grants, teaching, service.

**Resume**: industry standard. One page (early career) to two pages (senior, ≥10 years). Brief, achievement-focused.

**Going from academia to industry:** do not submit your CV. Translate to a 2-page resume.

### 8. Employment gap explanation

- **Caregiving / family leave** — name it in one line on the resume.
- **Education / certification** — list as its own entry: "Independent study in [topic], earned [credential]."
- **Health, personal, undisclosed** — a single line ("Career break, 2024-2025") is acceptable.

Tone cue: matter-of-fact framing reads as normal; apologetic framing reads as a red flag.

### 9. Senior-IC vs management-track resumes

A senior IC's resume emphasizes technical depth, architectural decisions, cross-team influence without authority.

A manager's resume emphasizes team outcomes, headcount grown, attrition controlled, hiring loops run.

**Same person applying to both tracks needs two resumes.**

## X-Y-Z bullet examples

- **Engineering:** Reduced p95 API latency from 850ms to 180ms by introducing a Redis read-through cache and refactoring the N+1 query pattern.
- **Sales:** Grew enterprise pipeline 3x ($4.2M to $12.6M) in 12 months by repositioning the discovery motion.
- **PM:** Shipped a self-serve onboarding flow that lifted activation from 32% to 51% by sequencing three A/B-tested copy and UI changes.

## Anti-Patterns

1. **Responsibility bullets instead of achievement bullets.** "Responsible for managing the customer-success team."
2. **Two-column "designer-y" templates.** Beautiful in Figma, mangled by the ATS.
3. **Soft skills as standalone skills entries.** "Strong communicator, team player."
4. **The 30-page CV submitted for an industry role.**
5. **Identical resume for every application.**
6. **Apologetic gap framing.** "I was unfortunately out of work due to..."
7. **Mixing IC and manager track signals.**

## Resume header template

```
[Full Name]
[City, State] | [phone] | [email] | [linkedin URL] | [portfolio/GitHub URL]
```

## References

- [The XYZ Method Resume — Teal](https://www.tealhq.com/post/xyz-resume)
- [Anatomy of an ATS-Friendly Resume Format (2026) — Jobscan](https://www.jobscan.co/blog/20-ats-friendly-resume-templates/)
- [Harvard FAS Mignone Center for Career Success — Resume vs CV](https://careerservices.fas.harvard.edu/blog/2023/08/28/the-resume-vs-curriculum-vitae-cv/)
