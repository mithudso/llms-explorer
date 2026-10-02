# Article Index

Extracted from: *Agentic Skill Optimization - Mitch Hudson.md*

This folder contains 27 individual markdown files, organized by the original structure. Draft 28 (the raw Slack notes dump) was removed on 2026-10-02 and is not published. See "Publication status" below for where each draft went.

## Part A: Start Here — Orientation & Live Demos

1. **Orientation — Worked Examples: The Tooling Explains Itself** — Self-explaining examples of the tooling in action
2. **Report Generation from Context — A Quick Demo** — Quick demo of generating structured reports
3. **The Deep Document Optimizer — A Live Run** — Full end-to-end session of the document optimizer

## Part B: Project Briefings — What Each System Is

4. **Customer Dashboard — Project Briefing** — Chrome extension + backend aggregator
5. **MDB Context Hub — Project Briefing** — MCP skill-sharing server
6. **TSE Strategy Backtest Scoreboard — Project Briefing** — Case diagnosis strategy evaluator
7. **MDB Case Assistant — Project Pitch** — Case-triage Chrome extension
8. **StickySites — Project Briefing** — Standalone briefing project

## Part C: Applied Case Studies & Results

9. **Case Study — Gamifying Incident-Response Training** — [redacted] rate-limiting fire drill training game
10. **Case Study — Keeping a Customer's Feature-Request Tracking in Sync** — Agent-driven state sync
11. **Comparing Output Quality Across Claude Model Tiers and Effort Levels** — Controlled benchmark
12. **Comparative Review — Case-Resolution Diagnosis Strategies** — Blind multi-strategy comparison
13. **Producing a Customer Context File — Glean vs. the mdb-tam Corpus** — Head-to-head comparison
14. **Customer Context Files — Turning Scattered Account Data into Proactive Engagement** — TAM tooling ecosystem
15. **From Discovery to the Board** — Initial discovery through board-level readout

## Part D: Technical Deep Dives

16. **Reducing LLM Cost and Latency Without Losing Context** — Token savings architecture
17. **Implementing a Native macOS Meeting-Intelligence System** — System audio + on-device speech
18. **State That Survives the Session** — Durable state across sessions
19. **Markdown as the LLM Output Gateway** — Tokens → AST → render pipeline
20. **Legible by Construction — Automated Docs, Indexes, Logging** — Systems that stay legible
21. **Automated Auditing and Security-First Software Design** — Security from the start
22. **Building Codebases for Machine Collaborators** — Structuring for AI navigation

## Part E: The Skill System — Architecture & Method

23. **Compounding Expertise — An Iterative Skill-Optimization Pipeline** — Multi-stage optimization
24. **Skill Catalog — Domain Authority and Optimization Machinery** — Skills for case resolution
25. **The Hub-and-Spoke Skill Methodology** — Taming skill sprawl
26. **Semantic Skill Discovery and the Optimizer Family** — Hub finding and skill matching
27. **A Closed-Loop System for Autonomous Skill-Knowledge Acquisition** — Self-expanding expertise

---

## File Statistics

- **Total files**: 27 markdown documents
- **Total content**: ~5,800 lines
- **Format**: Markdown with full formatting preserved
- **Each file**: Independently readable article

## How to Use

- Each file is a complete, standalone article
- Numbering preserves the original recommended reading order
- Related articles can be cross-referenced using the file numbers
- All markdown formatting, links, and code blocks are preserved

---

## Publication status

The site copy is canonical once a draft is scheduled or published; these drafts are the pre-edit originals. Scheduled posts were redacted (no customer names) and run through `/ddo` on 2026-10-02. `.github/workflows/publish-scheduled.yml` moves each scheduled post to `site/src/content/blog/<slug>.md` on its `date`.

| Draft | Status | Site file |
|---|---|---|
| 01 | published | `site/src/content/blog/orientation-worked-examples-the-tooling-explains-itself.md` |
| 02 | scheduled 2026-10-30 | `site/scheduled-posts/report-generation-from-context.md` |
| 03 | scheduled 2026-10-04 | `site/scheduled-posts/the-deep-document-optimizer-a-live-run.md` |
| 04 | scheduled 2026-10-06 | `site/scheduled-posts/customer-dashboard-project-briefing.md` |
| 05 | scheduled 2026-10-08 | `site/scheduled-posts/mdb-context-hub-project-briefing.md` |
| 06 | scheduled 2026-10-10 | `site/scheduled-posts/case-diagnosis-backtest-scoreboard-project-briefing.md` |
| 07 | published | `site/src/content/blog/mdb-case-assistant-project-pitch.md` |
| 08 | published | `site/src/content/blog/stickysites-project-briefing.md` |
| 09 | scheduled 2026-10-12 | `site/scheduled-posts/case-study-gamifying-incident-response-training.md` |
| 10 | scheduled 2026-10-14 | `site/scheduled-posts/case-study-keeping-feature-request-tracking-in-sync.md` |
| 11 | published | `site/src/content/blog/comparing-output-quality-across-claude-model-tiers-and-effort-levels.md` |
| 12 | scheduled 2026-10-16 | `site/scheduled-posts/comparative-review-case-resolution-diagnosis-strategies.md` |
| 13 | scheduled 2026-10-18 | `site/scheduled-posts/producing-a-customer-context-file-glean-vs-the-mdb-tam-corpus.md` |
| 14 | scheduled 2026-10-20 | `site/scheduled-posts/customer-context-files-turning-scattered-account-data-into-proactive-engagement.md` |
| 15 | scheduled 2026-10-22 | `site/scheduled-posts/from-discovery-to-the-board.md` |
| 16 | published | `site/src/content/blog/reducing-llm-cost-and-latency-without-losing-context.md` |
| 17 | published | `site/src/content/blog/implementing-a-native-macos-meeting-intelligence-system.md` |
| 18 | published | `site/src/content/blog/state-that-survives-the-session.md` |
| 19 | published | `site/src/content/blog/markdown-as-the-llm-output-gateway.md` |
| 20 | published | `site/src/content/blog/legible-by-construction-automated-docs-indexes-logging-and-test-centric-design.md` |
| 21 | published | `site/src/content/blog/automated-auditing-and-security-first-software-design.md` |
| 22 | published | `site/src/content/blog/building-codebases-for-machine-collaborators.md` |
| 23 | scheduled 2026-10-24 | `site/scheduled-posts/compounding-expertise-an-iterative-skill-optimization-pipeline.md` |
| 24 | scheduled 2026-10-26 | `site/scheduled-posts/skill-catalog-domain-authority-and-optimization-machinery-for-case-resolution.md` |
| 25 | scheduled 2026-10-28 | `site/scheduled-posts/the-hub-and-spoke-skill-methodology.md` |
| 26 | published | `site/src/content/blog/semantic-skill-discovery-and-the-optimizer-family.md` |
| 27 | published | `site/src/content/blog/a-closed-loop-system-for-autonomous-skill-knowledge-acquisition.md` |
| 28 | removed 2026-10-02 | raw Slack notes; never published |

---

*Generated: 2026-08-31*
