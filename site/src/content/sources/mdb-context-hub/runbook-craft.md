---
title: "Runbook Craft"
description: "A runbook is not a piece of documentation. It is a procedural script someone must execute correctly while tired, under pressure, with paging alerts firing in the background. Every step must be unambig"
---

# Runbook Craft

## Overview

A runbook is not a piece of documentation. It is a procedural script someone must execute correctly while tired, under pressure, with paging alerts firing in the background. Every step must be unambiguous to a person who did not write it and may never have run it before.

## Core Concepts

### 1. The "fresh machine" test

A runbook is only correct if a person who has never run it before, on a freshly provisioned environment, with no tribal context, can complete it successfully.

Schedule a quarterly drill where someone who did not author the runbook runs it end-to-end on a sandbox or staging clone. Every pause is a defect in the runbook, not in the runner.

### 2. Atomic, numbered steps with a verb-first imperative

Each step performs exactly one action that produces exactly one verifiable result. The verb comes first.

Bad: "Now we need to make sure that the broker is running and you may also want to check the lag, and if the lag is high then restart things."

Good:
1. Run `kafka-broker-api status --broker mdb-prod-1`. Expected output: `STATUS: HEALTHY`.
2. Run `kafka-consumer-groups --describe --group mdb-tam-consumer`. Record the `LAG` column.
3. If `LAG > 50000`, go to step 7 (broker restart). Otherwise continue to step 4.

### 3. "You are here" markers and progress anchoring

- **Section banners** at the top of each major phase: `=== PHASE 2 of 5: failover the primary ===`.
- **State-check steps** at the boundary of each phase.
- **Numbered top-level steps that never restart**: use 1-25 across the whole runbook.

### 4. Prerequisites block at the top, before step 1

A complete prerequisites block contains:
- **Access**: which SSO group, which IAM role, which secrets vault entry.
- **Tools and versions**: `mongosh >= 2.0`, `aws-cli >= 2.13`, `jq`.
- **Inputs**: cluster ID, account ID, ticket number.
- **Approvals**: who must sign off in writing before step 1.
- **Communication**: which Slack channel to post in.

### 5. Rollback as a first-class section, defined before the change

A rollback section answers four questions:
1. **What signals trigger a rollback?** Quantitative thresholds. ("Error rate > 2% sustained for 5 minutes." Not "if things look bad.")
2. **What is the rollback command?** Exact, copy-pasteable.
3. **What is the rollback verification?**
4. **What is the data-loss / state-loss implication?**

### 6. Decision points with measurable thresholds

Bad: "If memory looks high, restart the service."
Good: "If `mem_used_pct > 85` for 3 consecutive samples, restart the service (step 12)."

### 7. Post-condition checks at the end of each phase

A post-condition check has three parts:
- **The command to run** (or signal to observe).
- **The expected result** (exact string, numeric range).
- **What to do if the result does not match** (rollback, escalate, retry).

### 8. Ownership, review cadence, and metadata

Every runbook needs:
- **Owner** (a team, not a person).
- **Last reviewed** (date + name).
- **Next review due** (a real calendar date).
- **Linked alert / page / dashboard**.
- **Estimated duration**.
- **Risk level** (read-only / mutates non-prod / mutates prod / irreversible).

### 9. Plain copy-pasteable commands, no placeholders in prose

- **Code-fenced blocks** for every command, with no surrounding prose inside the block.
- **A "set variables" step at the top** that declares all substitutions once using environment variables.

### 10. Common anti-patterns

- **The narrative blob**: paragraphs where steps should be.
- **Hardcoded secrets** in code blocks.
- **"You should know" gaps**: the runbook assumes the runner has the same context as the author.
- **Ambiguous phrasing**: "investigate the issue", "check the dashboard."
- **Outdated commands.**
- **No rollback.**

## Full runbook skeleton

```markdown
# Runbook: <one-line title that matches the alert name>

| Owner team | mdb-tam-platform |
| Last reviewed | 2026-05-15 by @mitch.hudson |
| Next review due | 2026-08-15 |
| Linked alert | `PD: tam-helper-relay-down` |
| Estimated duration | 15–25 min |
| Risk level | Mutates prod state — rollback available |

## Prerequisites
- Access: `tam-prod-readwrite` SSO group, VPN connected.
- Tools: `kubectl >= 1.28`, `mongosh >= 2.0`, `jq`.

## Variables (set once)
```bash
export CLUSTER_ID=<from alert>
```

## Phase 1 — Triage (steps 1–4)
## Phase 2 — Mitigate (steps 5–12)
## Phase 3 — Verify (steps 13–18)

## Rollback procedures
## Post-incident
## Known gotchas
```

## Decision Heuristics

- **When to split a runbook**: more than 3 levels of branching, more than ~40 atomic steps, or two different audiences.
- **When to automate vs. document**: a runbook executed > 1x/month and fully deterministic is automation-eligible.
- **When to mark a step "stop and escalate"**: any condition the runbook author did not anticipate, any post-condition mismatch.
- **When to retire a runbook**: the underlying alert hasn't fired in 12 months and the system has changed.

## References

- [Google SRE Workbook — On-Call](https://sre.google/workbook/on-call/)
- [PagerDuty Runbook Automation](https://www.pagerduty.com/platform/automation/runbook/)
- [Nobl9 — Runbook Example: A Best Practices Guide](https://www.nobl9.com/it-incident-management/runbook-example)
- [Rootly — Incident Response Runbooks](https://rootly.com/incident-response/runbooks)
