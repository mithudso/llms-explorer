---
title: "design-deep-optimizer"
description: "Critique-and-fix optimizer for graphic, brand, and UI/UX work: an 11-pass critique (hierarchy, gestalt, typography, color, usability heuristics, WCAG, trust) with code-backed fixes verified by re-render and contrast checks."
order: 14
tags: [design, ui-ux, accessibility, optimization]
aliasCommand: "/deso"
---

The design member of the family. Ingests a screenshot, URL, HTML/CSS, or spec and runs
an 11-pass critique: visual hierarchy, gestalt, typography, color, usability
heuristics and Laws of UX, WCAG accessibility, affective/trust signals, metrics,
brand parity, and a hallucination guard that keeps findings anchored to what is
actually in the image.

Findings are severity-rated Blocker→Nit. When the design is **code-backed**, Medium+
fixes are applied to the source and verified — re-render, contrast measurement, axe —
to convergence. Image, URL, and spec inputs get critique-only findings.

**Use it for:** "critique this screen", "optimize this landing page", "why does this
UI feel untrustworthy", pre-ship design QA on HTML/CSS you can edit.

**Not for:** the code's logic ([code-deep-optimizer](/skills/code-deep-optimizer/)) ·
copywriting (writing skills) · building a design system from scratch.
