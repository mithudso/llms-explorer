# Standards and evidence

## Contents

- Source map
- Numeric checks
- Evidence limits

## Source map

These are references for choosing and applying methods, not a claim that every
method is a formal standard. The catalogue adapts general inspection techniques
into operational passes. Its coverage is broad and extensible, not exhaustive.

| ID | Authority and use |
| --- | --- |
| WCAG | W3C WCAG 2.2 and WAI Understanding documents: applicable accessibility criteria and exceptions |
| HEURISTICS | Nielsen Norman Group: ten usability heuristics; expert inspection does not replace user testing |
| METHODS | Nielsen Norman Group: choosing research methods by behavior/attitudes, qualitative/quantitative evidence and context of use |
| FRONTEND | Existing frontend-ui expertise: visual principles, typography, critique methodology, accessibility, trust and AI interaction. These inspection rubrics require product context; they are not universal numeric standards. |

W3C normative WCAG 2.2:
https://www.w3.org/TR/WCAG22/

W3C implementation guidance:
https://www.w3.org/WAI/WCAG22/quickref/

Text contrast, SC 1.4.3 (Level AA):
https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html

Target size, SC 2.5.8 (Level AA):
https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html

Nielsen heuristics:
https://www.nngroup.com/articles/ten-usability-heuristics/

Research-method selection:
https://www.nngroup.com/articles/which-ux-research-methods/

Read the matching `frontend-ui/references/` source if installed: visual-design-
principles-and-critique, micro-typography-craft, accessibility-ux-reviewer,
usability-heuristics-laws-of-ux, emotional-design-and-visual-trust,
deceptive-design-and-dark-patterns, or ai-native-ux-generative-ui. These optional
expertise sources add depth; the catalogue remains usable without them. Missing
mandatory target evidence still blocks the affected selected pass.

## Numeric checks

Source passages checked on 2026-11-08 using retrieved W3C and NN/G text. Cached
fetch timestamps varied from 2026-11-07 to 2026-11-09 UTC. The quickref query
returned no readable answer; numeric text came from the two Understanding pages.
For other criteria, read the linked normative criterion before judging a failure.

- SC 1.4.3 requires at least 4.5:1 for ordinary text and 3:1 for large text.
  Large means at least 18pt regular or 14pt bold; use computed size and weight,
  not a visual guess. Check incidental/inactive, decorative and logotype
  exceptions. Ordinary branded text is not exempt. Do not round a failing ratio
  up to the threshold. Use actual composited colors; antialiased screenshot pixels
  are not reliable substitutes for computed text colors.
- SC 2.5.8 requires a target at least 24 by 24 CSS pixels OR a valid exception.
  Exceptions include spacing (the specified 24px-diameter circle test), equivalent
  control, inline text, unmodified user-agent control, and essential presentation.
  Do not mistake the 44 by 44 enhanced criterion for the AA minimum. A generous
  touch target may be good usability advice without being an AA failure.
- For non-text contrast, use SC 1.4.11, its required information scope and exceptions.
  For reflow, text spacing, focus, authentication, dragging, status messages and
  timing, fetch the exact criterion rather than infer compliance from a screenshot.
- Platform guidelines and product requirements can exceed these minima. Record
  which rule is normative, which is a platform expectation and which is a heuristic.

## Evidence limits

A clean automated accessibility scan does not prove WCAG conformance. A fast lab
trace does not prove field performance. Readability, symmetry, colorfulness and
visual complexity scores can corroborate findings; they do not establish usability.
An expert scan is not eye tracking, a simulated persona is not a participant, and
a screenshot is not a keyboard, screen-reader or workflow test. Do not invent
conversion lifts, task times, heatmaps, satisfaction scores or research samples.

Only run user research, collect telemetry or expose real users to experiments when
authorized. Analyze existing authorized evidence otherwise. Keep participant
identifiers private and explain sample and selection limitations. Treat an
unvalidated design hypothesis as a hypothesis, not a proven Medium+ defect.
