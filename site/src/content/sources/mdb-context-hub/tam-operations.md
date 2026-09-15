---
title: "Semantic Monitoring, Reporting & Customer Dashboards for TAM (value-chain synthesis)"
description: "Hub for the MongoDB Technical Account Manager's operational toolkit — producing account deliverables, scoring customer health, running case and incident operations, automating reports, and integrating"
---

# TAM Operations

Hub for the **MongoDB Technical Account Manager's operational toolkit** — producing account deliverables, scoring customer health, running case and incident operations, automating reports, and integrating the Customer Dashboard's support data. Each former standalone skill is an on-demand reference under this hub's `references/`.

Boundary: this hub owns the **TAM operator's own work** — deliverables, health, case/incident process, reporting, and the support-API integration. When the question is about MongoDB/Atlas *technical* depth, the *prose craft* of a deliverable, or *MCP tooling* mechanics, defer to the sibling hubs.

## Sub-skill routing table (14 references)

| Sub-topic | When to load | Reference file |
| --- | --- | --- |
| `tam-expertise` | TAM deliverables, health/churn/NRR, success frameworks, 30-60-90 onboarding, escalation/stakeholder dynamics | `references/tam-expertise.md` |
| `tam-reference` | MongoDB Premium Services TAM operating reference — roles, S1–S4 SLAs, JIMP, lifecycle, Straight-to-8, Monday | `references/tam-reference.md` |
| `tam-account-reports` | Generate a named-account doc from live MCP data — account review, support plan, JIMP, weekly update, case analysis | `references/tam-account-reports.md` |
| `account-health-scorer` | Health-scoring algorithms — weighted composites, signals, grading, time-series trending, anomaly detection | `references/account-health-scorer.md` |
| `account-artifacts-collector` | Parallel data collection across MCP + local sources, persisting typed JSON artifacts for reports | `references/account-artifacts-collector.md` |
| `operator-report-generator` | Operator report engines — shift handoff (SBAR), meeting prep, freshness scoring, BLUF, template rendering | `references/operator-report-generator.md` |
| `customer-file-consolidator` | Collect/dedupe/consolidate a customer's local files into a unified TAM briefing, ingest to corpus | `references/customer-file-consolidator.md` |
| `case-tracker` | Build/extend the active case tracker — TS Tools API, case schema, severity model, LLM summarization, diagnostics | `references/case-tracker.md` |
| `case-timeline-visualization` | Vanilla-JS temporal/event-sequence visualization — DOM/SVG/Canvas, zoom/scroll, accessibility | `references/case-timeline-visualization.md` |
| `incident-response` | Incident lifecycle — SEV classification, IC/roles, postmortems, SLO/SLI + error budgets, on-call, MTTD/MTTR | `references/incident-response/SKILL.md` |
| `autoremediation` | Self-healing — retry/circuit-breaker, recovery, graceful degradation, canary rollback, AI repair loops | `references/autoremediation.md` |
| `firedrill-integration-tester` | Firedrill/game-day validation — scenarios, safety/abort, scoring, agent orchestration via firedrill tools | `references/firedrill-integration-tester/SKILL.md` |

## Related standalone skills (value-chain neighbors)

Top-level skills (not folded references) this hub hands off to:

- **Proving customer value / outcomes** — time-to-value, mutual success plans, value scorecards, outcome-vs-activity metrics, the CS-platform landscape (Gainsight/ChurnZero/Totango-Catalyst/Vitally/Planhat) → `value-realization-outcome-cs` (defer health-score *algorithm* to `references/account-health-scorer.md`, QBR/EBR *structure* to `references/tam-expertise.md`).
