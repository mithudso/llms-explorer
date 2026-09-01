# Appendix — Original Slack Dump (Raw Notes)

JPMC Context file: [https://docs.google.com/document/d/132U5y-lnRwe6f7sjFpTq-jQcQdO60g26yo2viPT5YDM/edit?usp=sharing](https://docs.google.com/document/d/132U5y-lnRwe6f7sjFpTq-jQcQdO60g26yo2viPT5YDM/edit?usp=sharing) Can you doublecheck it's accurate?

\[11:26 AM\]

Do you know why this report only shows 1 AHA for JPMC? [https://mongodb.aha.io/shared/be1122ecbbcd994f115708a651f12189](https://mongodb.aha.io/shared/be1122ecbbcd994f115708a651f12189)

Mitch Hudson  \[11:33 AM\]

My MCP skill sharing server with concept tree  and semantic skill matching: [https://github.com/10gen/mdb-context-hub](https://github.com/10gen/mdb-context-hub)

\[11:34 AM\]

My backtesting scoreboard page for support cases using MDB extertise files: [https://github.com/10gen/tse-strategy-backtest-scoreboard](https://github.com/10gen/tse-strategy-backtest-scoreboard)

\[11:36 AM\]

I ported the claude-code skills over to glean and made an umbrella referenced mdb expert skill set with a skill aggregator so if you install this skill into glean you can say "solve this case \#\#\#\#\#" and it'll do that. One thing that I found to be super helpful and actually raised my solved rate was integrating some applied psychology and writing skills on top of the technical domains.

Zip  
[glean\_mongodb\_case\_optimization\_research\_platform\_integration\_umbrella\_skill.zip](https://files.slack.com/files-pri/T01C4Q4H3CL-F0BC3JPKHL0/download/glean_mongodb_case_optimization_research_platform_integration_umbrella_skill.zip?origin_team=E01C4Q4H3CL)  
[Zip](https://files.slack.com/files-pri/T01C4Q4H3CL-F0BC3JPKHL0/download/glean_mongodb_case_optimization_research_platform_integration_umbrella_skill.zip?origin_team=E01C4Q4H3CL)  
\[11:38 AM\]

I'm kindof most proud of a meta-research skill that saturates a conceptual family branch and creates applicable skills from them automatically. So like yesterday my sister in law wanted help with some visual design stuff, I have no experrience with that at all, so I set my workers to task and in a few hours had professional grade critiques, editing, image curation, and market typing with specific verified industry facts.

\[11:39 AM\]

One of the big issues is having too MANY skills that eat up your context, so I folded the skills into a hub and spoke architecture that all cross-reference each other with specific "when to use" and "when not to use" sections so they automatically route queries to the right skills without yet another agent or skill overheard.

\[11:44 AM\]

This all basically started with a probably neurotic fixation with skill creation and optimization. Integrating workflows and agents on top of that hasn't actually been as useful in my opinion as optimizing the skills themselves so they independently call relevant skills and functions versus and agent which is essentially just a skill in a crontab.

\[11:45 AM\]

Sorry I haven't actually had the chance to talk about all this with anyone, so I apologize if I'm infodumping.

Mitch Hudson  \[11:51 AM\]

Oh, right the semantic skill matching proof of concept using mdb vector search. Which would honestly really need voyageai auto-embedding to make it work. Frankly I am pushing the limits of what my context window can hold, and thank god MDB is paying for the tokens because.... ooof.... I'm just waiting for when someone taps me on the shoulder and tells me to cool it.

But when you have a skill matching skill it only uses keyword searching unless you specifically do semantic match analysis. Which for most use cases is fine if you just do keyword matching, but when you start looking for "build me a customer dashboard"   and it matches "customer" with  "customer transactions" skill or whatever, you get skill mismatch, which is exactly what semantic/vector search is meant to solve.

\[11:52 AM\]

Now in order for it to be feasible we'd have to be talking about thousands of skills shared across teams that are not frequently updated, otherwise the overhead of re-vectorizing each skill would be untenable.

\[11:52 AM\]

Ok I'm done now.

\[11:53 AM\]

Right now I wanted a proof of concept about the semantic skill matching so I'm not using mdb vector search yet, but honestly I could probably implement that in a day or two.

\[11:57 AM\]

OK one more. As a side bar I wanted to test the feasibility of my setup, so I told it to become an expert in everything credit and personal finance, and it helped me resolve some lingering credit issues on my credit report in such a way that I went from "I can't look at this" to "I literally just put the resolution paperwork in the mail  an hour ago" in less than 12 hours.

Mitch Hudson  \[12:05 PM\]

Ok one one more. I told it to become an expert in technical training methodology and psychology, and use that to create and implement a end to end training program for the incident responders program for Okta (enhanced support program they're paying us a boat load of money to have 15 min resolution time for S1 cases) and I did it, it's great. But one of the emergent findings was it (very correctly) questioned whether triaining is the right solution, or if better tooling would be a better choice. [https://mongodb.enterprise.slack.com/files/U086BHR9VU1/F0BBVCNP5U0/screen\_recording\_2026-06-16\_at\_20.58.26.mov](https://mongodb.enterprise.slack.com/files/U086BHR9VU1/F0BBVCNP5U0/screen_recording_2026-06-16_at_20.58.26.mov?origin_team=E01C4Q4H3CL&origin_channel=D0BAKU8RKHV)

| Screen Recording 2026-06-16 at 20.58.26.mov  
1x  
Mitch Hudson  \[12:19 PM\]

Ok... please tell me to stop at some point. But I started this whole thing with building a [https://github.com/10gen/mdb-tam/](https://github.com/10gen/mdb-tam/) which is effectively a customer context aggregator with built in mcp server functionality, but when Glean started allowing skills I effectively moved almost all the funcationality to Glean which has a lot less overhead.

I also experimented with a case triage chrome extension with mcp server, which complements the case triage stuff ts-tools is working on pretty well, but I got a call from security saying I was hitting the backend too often and to cool it, which it still has a lot of uses, it's just slower, and I haven't figured out who to talk to about implementing case webhook subscriptions. instead of polling the server. WHIch btw it turns out that authentication hijacking is easier than I thought it would be. [https://github.com/10gen/mdb-case-assistant/](https://github.com/10gen/mdb-case-assistant/)

Also another cool optimization skill I built out was a repo-kickstarter which....  hold on this may be easier:

\[12:21 PM\]

❯ Explain all of the optimization skills I've developed? Include the repo-kickstarter, deep document, skill, code, prompt, and image optimizers.

You've built a family of "deep optimizer" skills — six tools that share one architectural spine but point it at different artifacts. Let me explain the shared pattern first, since that's the real insight, then walk each one.

★ Insight ─────────────────────────────────────

- These aren't six unrelated tools — they're siblings of one meta-pattern: diagnose → severity-rate → fix in place → verify → loop until convergence. Learn the pattern once and all six become legible.

- The key design split across the family is critique-only vs. apply-and-verify. When the artifact is executable/checkable (code, prompts, code-backed designs), the skill applies fixes and verifies them. When it can't verify (a screenshot, a pure-prose claim), it stops at findings.

- The "convergence loop" is what makes them deep rather than one-shot: they re-diagnose after fixing and keep going until no Medium-or-higher findings remain (or a budget is hit) — preventing both premature shipping and infinite polishing.

─────────────────────────────────────────────────

The shared anatomy

Every optimizer runs the same skeleton:

1\. Ingest & detect — figure out what the artifact is (language, domain, format).

2\. Multi-pass audit — run N specialized review passes, often in parallel bundles.

3\. Severity-rate — Blocker / High / Medium / Low / Nit.

4\. Remediate — apply every Medium+ fix (where verifiable).

5\. Verify — build/lint/test, re-render, contrast-check, back out regressions.

6\. Loop to convergence — re-diagnose; repeat until clean.

Now the six, grouped by what they target.

---

1\. repo-bootstrapper — "repo-kickstarter"

Target: an entire repository's scaffolding and meta-docs (not its logic).

This is the odd one out — it's a standard-enforcer, not a critique-loop. It brings any repo up to your "mdb-tam standard": refreshes CLAUDE.md, AGENTS.md, README indices, .github/, .vscode/, .editorconfig, .gitignore, dependabot, CODEOWNERS, issue/PR templates, CI workflows, the docs/ suite, and operations infrastructure (operations-registry.js, tool-inventory.json, CI drift checks, external-call audits).

Use it for: initializing a new repo or auditing an existing one to convention. Not for: reviewing code logic (→ code-deep-optimizer) or pure security (→ security-reviewer).

---

2\. ddo / document-critique — "deep document"

Target: prose documents — specs, RFCs, runbooks, KBs, READMEs, weekly updates, customer summaries.

Runs passes 0–14 plus sub-passes 10.5 and 11.5 — intent → structure → claims → authoritative verification → adversarial/hallucination guard → human-voice rephrasing. Two surfaces:

- document-critique \= findings-only (the review engine).

- /ddo \= the same engine but applies every Medium+ fix in place and loops to convergence.

Notable passes: it fact-checks, strips generator scaffolding, and runs an anti-AI-ism rephrase so the output reads human. Skip when: drafting from scratch (→ writing-expert) or the target is code, not prose.

---

3\. sko / skill-optimizer — "skill"

Target: a single Claude Code / TAM skill file.

Audits a skill to production quality: runs a convergence-loop quality gate, writes Medium+ fixes, seeds peer-deferral edges (the → use other-skill routing in descriptions), verifies, and syncs to the mdb-context-hub.

Has a structural-only \--meta mode that does the wiring without content passes: registry registration, placement/folder/manifest validation, naming fixes, peer-edge seeding. This is the skill that keeps your \~200-skill taxonomy's trigger accuracy and collision avoidance healthy.

---

4\. cdo / code-deep-optimizer — "code"

Target: a source file or whole repo's logic.

Auto-detects languages/frameworks/domains, activates matching reviewer skills, runs a 16-pass audit plus an opt-in advisory track (features, architecture, migration), applies every Medium+ fix in place, then verifies via build/lint/tests — backing out any regression — and loops to convergence.

This is the most "agentic" of the family because it closes the loop against a real toolchain. Skip for: a one-shot diff review (→ /code-review) or pure formatting (→ the language's formatter).

---

5\. pdo / prompt-deep-optimizer — "prompt"

Target: prompts that live in code and run repeatedly — system prompts, agent instruction blocks, tool-call templates.

Runs a 16-pass audit in 5 parallel bundles, applies every Medium+ fix, loops to convergence. Its distinctive output: besides the rewritten prompt, it recommends an optimization algorithm (APE / OPRO / MIPROv2 / GEPA / PromptBreeder / ProTeGi / TextGrad / EvoPrompt) if you have training data, or says "structural-only" if you don't.

There's a lighter sibling for one-off prompts: /ph (critique) and /phe (optimize-save-run). Rule of thumb: production prompt in a codebase → pdo; quick one-off under \~600 tokens → ph/phe.

---

6\. deso / design-deep-optimizer — "image"

Target: graphic/brand assets and UI/UX screens.

Ingests a screenshot, URL, code (HTML/CSS), or spec and runs an 11-pass critique over the frontend-ui spokes: hierarchy, gestalt, typography, color, usability heuristics / Laws of UX, WCAG, affective/trust, metrics, brand-parity, and a hallucination guard.

Here the critique-only vs. apply split is sharpest:

- Code-backed designs (HTML/CSS) → it applies Medium+ fixes and verifies via re-render \+ contrast \+ axe checks.

- Image / URL / spec inputs → critique-only findings (it can't edit a PNG).

Skip for: producing a new design (→ web-design / ui-ux-pro-max) or critiquing a photograph/AI-generated image.

---

The six optimizers differ mainly along three axes — what they target, how many passes they run, and whether they actually apply and verify fixes or stop at findings.

repo-bootstrapper targets a repo's scaffolding and meta-docs. Rather than a fixed pass count it runs a checklist, it does write files directly, and it verifies its work through a CI drift check.

document-critique / ddo targets prose. It runs passes 0–14 plus sub-passes 10.5 and 11.5; the /ddo surface applies the fixes (plain document-critique is findings-only), and it verifies by fact-checking and re-diagnosing on each loop.

skill-optimizer / sko targets a single skill file. It runs a convergence-loop quality gate rather than a numbered pass list, applies fixes, and verifies through meta-validation plus a sync to the context hub.

code-deep-optimizer / cdo targets code. It runs a 16-pass audit, applies every Medium+ fix, and verifies the hardest way of the family — by running build, lint, and tests and backing out any regression.

prompt-deep-optimizer / pdo targets production prompts. It runs 16 passes organized into 5 parallel bundles, applies fixes, verifies by re-diagnosing, and additionally outputs an optimization-algorithm recommendation.

design-deep-optimizer / deso targets designs and UI. It runs an 11-pass critique and is the one with a conditional behavior: it applies fixes only when the design is code-backed (HTML/CSS), verifying via re-render, contrast, and axe checks — for screenshots, URLs, or specs it stays critique-only.

The through-line: pick by artifact type, and remember the checkable artifacts (repo, code, prompts, code-backed designs) get applied-and-verified fixes, while un-checkable inputs (raw prose claims, image/URL/spec designs) get a severity-ranked findings list.

One mental model ties them together: pick the optimizer by what kind of artifact you're holding (repo, prose, skill, code, prompt, design), and remember that the ones targeting checkable artifacts will actually apply and verify fixes, while the ones targeting un-checkable inputs stop at a severity-ranked findings list.

\[12:25 PM\]

❯ Explain the /dr and concept family explorer skills and give a few examples of how it's been successfully used

These two skills form a two-tier knowledge-building pipeline: one maps what to learn, the other learns one thing and turns it into a permanent capability. Let me explain each, how they nest, then show real runs from your own history.

★ Insight ─────────────────────────────────────

- The key relationship is altitude: concept-family-explorer operates above /dr. The explorer decides which topics are worth building; /dr is the worker that actually builds one.

- /dr is distinct from plain deep-research: deep-research ends in a cited report, /dr ends in an installed, registered skill — research is the means, a permanent capability is the end.

- The explorer's superpower is fighting unknown unknowns — it surfaces concepts you didn't know you were missing, scores them, then fans /dr across all the viable gaps in parallel.

─────────────────────────────────────────────────

/dr — research → skill, in one shot

/dr \<topic\> is a pipeline command: it deep-researches a topic (via firecrawl/exa/web), synthesizes the findings into an expert skill, installs it at user level, and cross-pollinates — wiring the new skill's peer-deferral edges into related existing skills so the taxonomy stays coherent.

Think of it as the productized version of the old manual flow (research → write SKILL.md → optimize → register → sync to hub). It typically finishes with optimization passes so the skill lands at production quality, not draft quality.

Use it when: you've named a topic you want to own permanently. Skip it when: you just want a one-off cited answer (→ deep-research), or you don't yet know which topics to build (→ concept-family-explorer).

concept-family-explorer (CFE) — the gap-discovery layer

CFE sits one level up. Given a subject, it:

1\. Maps the full conceptual family — parent domain, sibling concepts, sub-concepts, adjacent/crossover fields, and the research frontier.

2\. Surfaces what you're missing — the useful or novel concepts not yet covered by your skill library.

3\. Scores each gap — using the da-\* (data-analysis) skills as a scoring rubric to rank viability.

4\. Loops /dr on every viable gap — often fanning out parallel research agents — until the concept tree saturates (no new worthwhile concepts emerge).

5\. Finishes with skill-optimizer \+ prompt-deep-optimizer to bring the new batch to standard.

So CFE is how a single seed topic becomes a whole hub-and-spoke skill family in one orchestrated run.

---

Real runs from your history

Here's how these have actually played out in your sessions — each shows the explorer-maps-then-/dr-builds rhythm.

Organ-donation nonprofit → applied-psychology family. You ran CFE across the giving/psychology/nonprofit space, it scored 8 gaps, and launched 6 research agents that became applied-psychology spokes — psychology-of-charitable-giving, health-behavior-change, community-based social marketing, fundraising-psychology, effective-altruism, volunteer-motivation. A messy real-world goal ("help my sister's nonprofit") turned into a coherent, scored, evidence-based skill cluster.

Visual-design family. CFE mapped the visual-design concept space, scored and ranked 13 gap-concepts against the CVS rubric, identified 4 knowledge-skills worth building (design-critique, vision-model, usability-heuristics, computational-aesthetics), then fanned 4 parallel /dr agents to build them. This is the canonical CFE shape: map → score → rank → parallel-/dr.

Consumer credit & finance. The consumer-credit-and-debt hub came out as 22 skills (2 hubs \+ 20 spokes) built via CFE — credit-reports, charge-offs, debt-collectors, mortgages, bankruptcy, NC-law, and so on. A single domain seed saturated into a full hub-and-spoke tree.

Copywriting family. 5 copywriting skills built via CFE parallel research — conversion/voice-of-customer, GEO/AEO, offer-design, direct-response, AI-copywriting — several passing clean audits.

Single-topic /dr runs. When you already knew the target, you went straight to /dr — e.g. /dr human-performance-technology, which ran 3 optimization iterations, hit Pass H 10/10, and registered to the hub. That's /dr used standalone, without the explorer above it.

---

When to reach for which

Reach for /dr when you can name the exact skill you want ("I need a Human Performance Technology skill"). Reach for concept-family-explorer when you have a domain and suspect you're missing pieces ("map everything around organ-donation nonprofits and build what I lack") — it'll find the gaps, rank them, and dispatch /dr across all of them so you get a complete family instead of one isolated skill.