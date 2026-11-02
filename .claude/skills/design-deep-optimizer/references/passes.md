# Pass Checklists — DETECT → RATE → FIX

The per-pass working checklists for the 11-pass critique, and the spoke each pass draws on.
Read this before the first run of a session; the SKILL.md gives the dispatch order and bundle
structure, this file gives the contents of each pass.

**Every finding carries:** severity · lens (pass + spoke) · region (Set-of-Mark coordinate or
CSS selector) · concrete fix. A finding without a locatable region or a concrete fix is
recorded **Low**.

**Every pass emits a row**, including `N/A` — a heuristics or WCAG pass over a static brand
asset still reports, so the scorecard shows coverage rather than silence.

---

## Severity scale

Used identically by every pass. Rate on user impact, not on how much the defect annoys you.

| Severity | Meaning | Examples |
| --- | --- | --- |
| **Blocker** | Unusable, inaccessible, or actively misleading for some users | Text below WCAG AA on a primary action; a control not reachable by keyboard; the primary CTA is invisible |
| **High** | Materially damages comprehension, trust, or task completion | No clear focal point; hierarchy inverted so the secondary action dominates; brand palette contradicted on a key surface |
| **Medium** | Noticeably degrades quality; a competent reviewer would flag it | Inconsistent spacing scale; weak type hierarchy; muddled grouping; poor rag |
| **Low** | Real but minor; polish | A widow; slight optical misalignment; one off-scale radius |
| **Nit** | Preference, defensible either way | A hue choice within an acceptable palette |

**Medium is the apply threshold** in EDITABLE mode. Do not inflate Low findings to Medium to
justify a change, and do not deflate a Blocker because the fix is inconvenient.

---

## Bundle A — Composition & visual
*Spoke: `visual-design-principles-and-critique`*

### P0 — Intent & context

Establishes what "good" means for this artifact. Every later pass rates against P0's answer, so
a wrong P0 makes every downstream severity wrong.

**DETECT**
- What is this artifact? (landing page, app screen, logo, poster, email, component)
- Who is the audience, and in what context and device do they meet it?
- What is the single job it must do? What action should follow?
- What brand, design system, or spec constrains it?
- What is explicitly out of scope?

**RATE** — P0 does not emit severities. It emits a stated context block.

**FIX** — If `--context` was supplied, use it verbatim. Otherwise infer and **state the
assumption in the report**, because a reader who disagrees with the assumption can then discount
the findings that depend on it. Never silently assume a purpose.

### P1 — Visual hierarchy & composition

**DETECT**
- **Focal point** — squint or blur the image. What survives? Is it what P0 said matters?
- **Scanning path** — does the layout support a Z, F, or Gutenberg path, or fight it?
- **Gestalt grouping** — proximity, similarity, closure, continuity, common region. Are related
  things visually related, and unrelated things separated?
- **C.R.A.P.** — Contrast, Repetition, Alignment, Proximity. Each is a separate check.
- **Balance** — symmetric, asymmetric, or accidentally lopsided?
- **Scale** — does size encode importance consistently?
- **White space** — is it doing work, or is it leftover? Is density uniform where it should vary?

**RATE**
- No discernible focal point, or focal point on the wrong element → **High**
- Grouping that implies a wrong relationship → **High**
- Misalignment breaking an established grid → **Medium**
- Uneven spacing rhythm → **Medium**
- Slight optical centering issues → **Low**

**FIX** — Name the element and the change: "increase the CTA to 1.5× surrounding type and move it
above the fold-line at y≈420" beats "improve hierarchy." Every fix must be executable by someone
who did not run the pass.

### P2 — Typography & legibility

Two layers: macro type system, then micro type craft.

**DETECT — macro**
- Type hierarchy: are levels distinguishable, and is the number of levels justified?
- Pairing: do the families work together, and is the count disciplined (usually ≤ 2–3)?
- Measure: roughly 45–75 characters per line for body text; flag long or short outliers.
- Vertical rhythm: consistent leading and spacing scale.

**DETECT — micro.** Load `frontend-ui/references/micro-typography-craft.md` — it carries the full
DETECT→RATE→FIX catalog. Check for:
- Widows, orphans, runts
- Rag quality, rivers, bad line breaks
- Kerning and tracking defects ("keming")
- Baseline-grid alignment
- H&J and justified-text gaps
- Hanging punctuation
- **Glyph crimes** — straight vs curly quotes, hyphen/en/em dash misuse, faux small caps,
  old-style vs tabular figures in the wrong context
- **Type crimes** — faux bold, faux italic, artificially condensed or stretched faces,
  ransom-note family mixing

**RATE**
- Body text too small or too tight to read comfortably → **High**
- Hierarchy levels indistinguishable → **High**
- Faux bold/italic, artificial condensing → **Medium** (a real weight exists; use it)
- Measure well outside 45–75ch on long-form body → **Medium**
- Widows, minor rag → **Low**
- Straight quotes in display type → **Low**, or **Medium** on brand-critical surfaces

**FIX** — Give the value, not the direction: "set body to 16px/1.5, max-width 65ch", not "improve
readability."

### P3 — Colour & contrast

**DETECT**
- Harmony and palette discipline: how many hues, and is each earning its place?
- Semantic consistency: does one colour mean one thing throughout (danger, success, interactive)?
- **Contrast math** — compute it, do not eyeball it. WCAG 2.2: 4.5:1 for normal body text,
  3:1 for large text (≥ 24px, or ≥ 19px bold), 3:1 for meaningful non-text and UI component
  boundaries. Delegate the math to `frontend-ui/references/accessibility-ux-reviewer.md`.
- Colour as sole information carrier (fails for colour-blind users).
- Behaviour in dark mode, if applicable.

**RATE**
- Body text below 4.5:1 → **Blocker**
- Interactive element or its focus indicator below 3:1 → **Blocker**
- Colour as the only signal for state → **High**
- Semantic inconsistency (the same hue means two things) → **Medium**
- Palette sprawl → **Medium**

**FIX** — Supply the replacement value and its measured ratio: "`#767676` on `#FFFFFF` = 4.54:1,
replacing `#999999` at 2.85:1."

---

## Bundle B — Interaction & accessibility

Mostly `N/A` for static brand assets. Emit the `N/A` row; do not silently skip.

### P4 — Usability heuristics & Laws of UX
*Spoke: `usability-heuristics-laws-of-ux`*

**DETECT — Nielsen's 10**, each as its own check:
1. Visibility of system status
2. Match between system and the real world
3. User control and freedom (undo, exit)
4. Consistency and standards
5. Error prevention
6. Recognition rather than recall
7. Flexibility and efficiency of use
8. Aesthetic and minimalist design
9. Help users recognize, diagnose, recover from errors
10. Help and documentation

**DETECT — Laws of UX**
- **Hick's Law** — too many simultaneous choices?
- **Fitts's Law** — are frequent or important targets big enough and close enough?
- **Jakob's Law** — does it violate a strong convention without a reason?
- **Miller's Law** — unchunked lists beyond working-memory capacity?
- **Doherty Threshold** — is feedback under ~400 ms, or at least acknowledged?
- **Peak-End Rule** — how do the most intense moment and the ending feel?

**RATE** — Use Nielsen's 0–4 severity, then map: 4 → Blocker, 3 → High, 2 → Medium, 1 → Low,
0 → Nit.

**FIX** — Name the heuristic violated and the specific remedy.

### P5 — Accessibility (WCAG 2.2)
*Spoke: `frontend-ui/references/accessibility-ux-reviewer.md`*

**DETECT**
- Contrast (see P3 — report once, cross-reference)
- **Target size** — WCAG 2.2 SC 2.5.8 requires 24×24 CSS px minimum, with defined exceptions
- Focus order, and a visible focus indicator meeting SC 2.4.11
- Keyboard reachability of everything interactive; no keyboard traps
- Alt text presence and quality; decorative images correctly null-alt
- Semantic structure: real headings in order, landmarks, labelled form controls
- Motion: is there a `prefers-reduced-motion` path?
- Text resize and reflow to 320px without loss of content or function

**RATE**
- Any keyboard trap, or an interactive control unreachable by keyboard → **Blocker**
- Missing or invisible focus indicator → **Blocker**
- Missing form label → **Blocker**
- Target below 24×24 with no exception → **High**
- Heading levels skipped → **Medium**
- Alt text present but unhelpful → **Medium**

**FIX** — Cite the specific success criterion number. It converts an opinion into a requirement.

---

## Bundle C — Affect & objective signal

### P6 — Affective / first-impression / trust
*Spoke: `misc-catch-all/references/emotional-design-and-visual-trust.md`*

**DETECT**
- **First impression (sub-second).** What does it feel like before it is read? Name three
  adjectives. Do they match P0's intended tone?
- **Norman's three levels** — visceral (immediate look), behavioural (use), reflective (what
  using it says about the user).
- **Trust signals** — polish, consistency, and the absence of the specific cues that read as
  untrustworthy: mismatched styling, stock-photo generic, dense unexplained forms, aggressive
  urgency, dark-pattern shapes.
- **Brand personality** — does the artifact's character match the brand's claimed character?

**RATE**
- Reads as untrustworthy or deceptive on a transactional surface → **High**
- Tone contradicts the stated brand → **High**
- Generic and undifferentiated where distinctiveness was the goal → **Medium**

**FIX** — Ground in a visual cause. "The 4px radius and slab face read institutional against the
stated 'friendly' tone; use the 12px radius and the rounded face already in the system" beats
"feels cold."

### P7 — Objective metrics
*Spoke: `computational-aesthetics-ui-metrics`*

**DETECT** — Compute, do not estimate:
- Visual complexity (edge density, element count)
- Colourfulness
- Balance and symmetry scores
- White-space ratio
- Contrast ratios (shared with P3)
- **axe** automated accessibility scan (code or URL inputs only)

**RATE** — On its own, a metric is **never** the sole basis for a finding above Low. Published
computational-aesthetics measures explain only roughly half the variance in human aesthetic
judgment, so a metric **corroborates** a subjective finding and raises confidence; it does not
manufacture one. An axe violation is the exception: it is a direct standards failure and rates
on its own.

**FIX** — Report the number, the direction, and the corroborated pass: "white-space ratio 0.11
vs 0.30–0.45 typical for this layout class; corroborates the P1 density finding."

---

## Bundle D — Brand & guard

### P8 — Brand / design-system / spec parity

**DETECT**
- Colours, type, spacing, radii, shadows, iconography against the stated brand or token set
- Component usage against the design system: is this a system component, a legitimate variant,
  or an ad-hoc reinvention?
- Against a supplied spec: every stated requirement present and correct?
- Logo usage: clear space, minimum size, approved lockup, no distortion or recolouring

**RATE**
- Logo misuse (stretched, recoloured, below minimum size) → **High**
- Off-token colour or type on a primary surface → **High**
- Ad-hoc component where a system component exists → **Medium**
- Off-scale spacing value → **Medium**
- Minor radius or shadow drift → **Low**

**FIX** — Name the token: "use `color.brand.primary` (`#1B4D3E`), not `#1C4E3F`."

### P9 — Adversarial / hallucination guard
*Spoke: `vision-model-design-critique`*

**The reliability backbone.** Vision models locate confidently and wrongly; this pass is what
separates a finding from a plausible sentence.

**DETECT**
- Re-run the visual passes (**P1, P6, P8**) in a fresh context, 2–3 times.
- For each finding from those passes, check: does it reappear? Can the element be re-located at
  the same region on every run?

**RATE — the keep/drop rule**
- Corroborated across runs **and** re-locatable → keep at its assigned severity
- Corroborated but the region drifts → keep, downgrade one level, mark `low-confidence (region)`
- Not reproduced on re-run → **drop**. Do not report it.
- References an element that cannot be re-located at all → **drop**. This is the hallucination
  case; a fix instruction pointing at a nonexistent element is worse than no finding.

**FIX** — P9 produces no fixes. It filters. Record how many findings were dropped, so the report
shows the filter ran and had an effect.

---

## P10 — Synthesis

**DETECT**
- Deduplicate across passes — the same defect legitimately surfaces in P1, P3, and P7.
- Where duplicates disagree on severity, **keep the highest**, and record which passes agreed
  (multi-pass agreement is a confidence signal worth showing).
- Group by region so a fixer works one area at a time rather than jumping around.
- Rank by severity, then by blast radius within severity.

**The "what's working" section is required.** Per `visual-design-critique-methodology`, a
critique that lists only faults is a worse critique: it gives no signal about what to preserve,
and a fixer who does not know what is load-bearing will break it while fixing something else.
Name at least two things that work and why.

**Output shape**

```
| # | Severity | Pass(es) | Region | Finding | Fix |
```

Then: what's working · dropped-by-P9 count · per-pass coverage scorecard (including `N/A` rows).

---

## Pass-to-spoke map

| Pass | Spoke |
| --- | --- |
| P0, P1 | `visual-design-principles-and-critique` |
| P2 | `visual-design-principles-and-critique` + `frontend-ui/references/micro-typography-craft.md` |
| P3 | `visual-design-principles-and-critique` + `frontend-ui/references/accessibility-ux-reviewer.md` |
| P4 | `usability-heuristics-laws-of-ux` |
| P5 | `frontend-ui/references/accessibility-ux-reviewer.md` |
| P6 | `misc-catch-all/references/emotional-design-and-visual-trust.md` |
| P7 | `computational-aesthetics-ui-metrics` |
| P8 | the supplied brand, design system, or spec |
| P9 | `vision-model-design-critique` |
| P10 | `visual-design-critique-methodology` |
