---
title: "Orientation — Worked Examples: The Tooling Explains Itself"
description: "Two worked chat transcripts show Claude explaining, on request, the six-member deep-optimizer family and how /dr and concept-family-explorer compose into a research pipeline."
date: "2026-09-02"
order: 1
---

Two exchanges that show the tooling explaining itself.

## Example 1 — Explaining the optimizer family

❯ Explain all of the optimization skills I've developed? Include the repo-kickstarter, deep document, skill, code, prompt, and image optimizers.

You've built a family of "deep optimizer" skills — six tools that share one architectural spine but point it at different artifacts. Let me explain the shared pattern first, since that's the real insight, then walk each one.

```
★ Insight ─────────────────────────────────────
- These aren't six unrelated tools — they're siblings of one meta-pattern:
  diagnose → severity-rate → fix in place → verify → loop until convergence.
  Learn the pattern once and all six become legible.
- The key design split across the family is critique-only vs. apply-and-verify.
  When the artifact is executable/checkable (code, prompts, code-backed designs),
  the skill applies fixes and verifies them. When it can't verify (a screenshot,
  a pure-prose claim), it stops at findings.
- The "convergence loop" is what makes them deep rather than one-shot: they
  re-diagnose after fixing and keep going until no Medium-or-higher findings
  remain (or a budget is hit) — preventing both premature shipping and infinite
  polishing.
─────────────────────────────────────────────────
```

**The shared anatomy.** Every optimizer runs the same skeleton:

1. **Ingest & detect** — figure out what the artifact is (language, domain, format).  
2. **Multi-pass audit** — run N specialized review passes, often in parallel bundles.  
3. **Severity-rate** — Blocker / High / Medium / Low / Nit.  
4. **Remediate** — apply every Medium+ fix (where verifiable).  
5. **Verify** — build/lint/test, re-render, contrast-check, back out regressions.  
6. **Loop to convergence** — re-diagnose; repeat until clean.

Now the six, grouped by what they target.

### 1. repo-bootstrapper — "repo-kickstarter"

**Target:** an entire repository's scaffolding and meta-docs (not its logic).

This is the odd one out — it's a standard-enforcer, not a critique-loop. It brings any repo up to your "mdb-tam standard": refreshes CLAUDE.md, AGENTS.md, README indices, .github/, .vscode/, .editorconfig, .gitignore, dependabot, CODEOWNERS, issue/PR templates, CI workflows, the docs/ suite, and operations infrastructure (operations-registry.js, tool-inventory.json, CI drift checks, external-call audits).

Use it for: initializing a new repo or auditing an existing one to convention. Not for: reviewing code logic (→ code-deep-optimizer) or pure security (→ security-reviewer).

### 2. ddo / document-critique — "deep document"

**Target:** prose documents — specs, RFCs, runbooks, KBs, READMEs, weekly updates, customer summaries.

Runs passes 0–14 plus sub-passes 10.5 and 11.5 — intent → structure → claims → authoritative verification → adversarial/hallucination guard → human-voice rephrasing. Two surfaces:

- document-critique = findings-only (the review engine).  
- /ddo = the same engine, but it applies every Medium+ fix in place and loops to convergence.

Notable passes: it fact-checks, strips generator scaffolding, and runs an anti-AI-ism rephrase so the output reads human. Skip when: drafting from scratch (→ writing-expert) or the target is code, not prose.

### 3. sko / skill-optimizer — "skill"

**Target:** a single Claude Code / TAM skill file.

Audits a skill to production quality: runs a convergence-loop quality gate, writes Medium+ fixes, seeds peer-deferral edges (the "→ use other-skill" routing in descriptions), verifies, and syncs to the mdb-context-hub.

Has a structural-only --meta mode that does the wiring without content passes: registry registration, placement/folder/manifest validation, naming fixes, peer-edge seeding. This is the skill that keeps your ~200-skill taxonomy's trigger accuracy and collision avoidance healthy.

### 4. cdo / code-deep-optimizer — "code"

**Target:** a source file or whole repo's logic.

Auto-detects languages/frameworks/domains, activates matching reviewer skills, runs a 16-pass audit plus an opt-in advisory track (features, architecture, migration), applies every Medium+ fix in place, then verifies via build/lint/tests — backing out any regression — and loops to convergence.

This is the most "agentic" of the family because it closes the loop against a real toolchain. Skip for: a one-shot diff review (→ /code-review) or pure formatting (→ the language's formatter).

### 5. pdo / prompt-deep-optimizer — "prompt"

**Target:** prompts that live in code and run repeatedly — system prompts, agent instruction blocks, tool-call templates.

Runs a 16-pass audit in 5 parallel bundles, applies every Medium+ fix, loops to convergence. Its distinctive output: besides the rewritten prompt, it recommends an optimization algorithm (APE / OPRO / MIPROv2 / GEPA / PromptBreeder / ProTeGi / TextGrad / EvoPrompt) if you have training data, or says "structural-only" if you don't.

There's a lighter sibling for one-off prompts: /ph (critique) and /phe (optimize-save-run). Rule of thumb: production prompt in a codebase → pdo; quick one-off under ~600 tokens → ph/phe.

### 6. deso / design-deep-optimizer — "image"

**Target:** graphic/brand assets and UI/UX screens.

Ingests a screenshot, URL, code (HTML/CSS), or spec and runs an 11-pass critique over the frontend-ui spokes: hierarchy, gestalt, typography, color, usability heuristics / Laws of UX, WCAG, affective/trust, metrics, brand-parity, and a hallucination guard.

Here the critique-only vs. apply split is sharpest:

- Code-backed designs (HTML/CSS) → it applies Medium+ fixes and verifies via re-render + contrast + axe checks.  
- Image / URL / spec inputs → critique-only findings (it can't edit a PNG).

Skip for: producing a new design (→ web-design / ui-ux-pro-max) or critiquing a photograph/AI-generated image.

**The through-line:** pick the optimizer by what kind of artifact you're holding (repo, prose, skill, code, prompt, design), and remember that the ones targeting checkable artifacts will actually apply and verify fixes, while the ones targeting un-checkable inputs stop at a severity-ranked findings list.

## Example 2 — /dr and the concept-family explorer

❯ Explain the /dr and concept family explorer skills and give a few examples of how it's been successfully used

These two skills form a two-tier knowledge-building pipeline: one maps what to learn, the other learns one thing and turns it into a permanent capability.

```
★ Insight ─────────────────────────────────────
- The key relationship is altitude: concept-family-explorer operates above /dr.
  The explorer decides which topics are worth building; /dr is the worker that
  actually builds one.
- /dr is distinct from plain deep-research: deep-research ends in a cited report,
  /dr ends in an installed, registered skill — research is the means, a permanent
  capability is the end.
- The explorer's superpower is fighting unknown unknowns — it surfaces concepts
  you didn't know you were missing, scores them, then fans /dr across all the
  viable gaps in parallel.
─────────────────────────────────────────────────
```

**/dr — research → skill, in one shot.** `/dr <topic>` is a pipeline command: it deep-researches a topic (via firecrawl/exa/web), synthesizes the findings into an expert skill, installs it at user level, and cross-pollinates — wiring the new skill's peer-deferral edges into related existing skills so the taxonomy stays coherent.

Think of it as the productized version of the old manual flow (research → write SKILL.md → optimize → register → sync to hub). It typically finishes with optimization passes so the skill lands at production quality, not draft quality.

Use it when: you've named a topic you want to own permanently. Skip it when: you just want a one-off cited answer (→ deep-research), or you don't yet know which topics to build (→ concept-family-explorer).

**concept-family-explorer (CFE) — the gap-discovery layer.** CFE sits one level up. Given a subject, it:

1. Maps the full conceptual family — parent domain, sibling concepts, sub-concepts, adjacent/crossover fields, and the research frontier.  
2. Surfaces what you're missing — the useful or novel concepts not yet covered by your skill library.  
3. Scores each gap — using the da-* (data-analysis) skills as a scoring rubric to rank viability.  
4. Loops /dr on every viable gap — often fanning out parallel research agents — until the concept tree saturates (no new worthwhile concepts emerge).  
5. Finishes with skill-optimizer + prompt-deep-optimizer to bring the new batch to standard.

So CFE is how a single seed topic becomes a whole hub-and-spoke skill family in one orchestrated run.

**Real runs from your history** — each shows the explorer-maps-then-/dr-builds rhythm:

- **Organ-donation nonprofit → applied-psychology family.** Ran CFE across the giving/psychology/nonprofit space, it scored 8 gaps, and launched 6 research agents that became applied-psychology spokes — psychology-of-charitable-giving, health-behavior-change, community-based social marketing, fundraising-psychology, effective-altruism, volunteer-motivation. A messy real-world goal ("help my sister's nonprofit") turned into a coherent, scored, evidence-based skill cluster.  
- **Visual-design family.** CFE mapped the visual-design concept space, scored and ranked 13 gap-concepts against the CVS rubric, identified 4 knowledge-skills worth building (design-critique, vision-model, usability-heuristics, computational-aesthetics), then fanned 4 parallel /dr agents to build them. This is the canonical CFE shape: map → score → rank → parallel-/dr.  
- **Consumer credit & finance.** The consumer-credit-and-debt hub came out as 22 skills (2 hubs + 20 spokes) built via CFE — credit-reports, charge-offs, debt-collectors, mortgages, bankruptcy, NC-law, and so on. A single domain seed saturated into a full hub-and-spoke tree.  
- **Copywriting family.** 5 copywriting skills built via CFE parallel research — conversion/voice-of-customer, GEO/AEO, offer-design, direct-response, AI-copywriting — several passing clean audits.  
- **Single-topic /dr runs.** When you already knew the target, you went straight to /dr — e.g. /dr human-performance-technology, which ran 3 optimization iterations, hit Pass H 10/10, and registered to the hub. That's /dr used standalone, without the explorer above it.

**When to reach for which:** reach for /dr when you can name the exact skill you want ("I need a Human Performance Technology skill"). Reach for concept-family-explorer when you have a domain and suspect you're missing pieces ("map everything around organ-donation nonprofits and build what I lack") — it'll find the gaps, rank them, and dispatch /dr across all of them so you get a complete family instead of one isolated skill.