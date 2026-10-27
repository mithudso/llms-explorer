# Hermes Agent Rabbithole research

Version: 1.0.1
Delta: 1.0.0 to 1.0.1; preserve completed baseline and first two depth passes.
Date: 2026-10-27
Task: TASK-929
Status: IN-PROGRESS

## Request and scope

> Run the rabbithole skill on hermes agent

This run researches Nous Research Hermes Agent itself: its agent loop, procedural learning, persistent memory, context management, tools, gateways, execution boundaries, security, failure modes and historical evolution. Adjacent agent products are handoff items.

Two independent Sol/medium research workers establish pass 0. Up to six sequential depth passes test the accumulated atomic claims. Each pass records new claims divided by total claims after that pass. Two consecutive rates below five percent establish depth saturation. Hitting the pass cap is BUDGET_EXHAUSTED, even if the final dossier is persisted.

## Evidence and continuation

Seed export: /Users/mitch/dev/llms-explorer/outputs/exports/hermes-agent.nousresearch.com.llms/llms-full.txt

Canonical private run: /Users/mitch/.global-ai-hub/research/hermes-agent-rabbithole-2026-10-27

Authoritative continuation: that run's manifest.json, claims/hermes-agent.json, depth/metrics.json and report.md. Raw fetched source bodies, exact evidence spans, worker logs and gate attempts remain in the private run and shared source library. Public files contain authored synthesis and source citations.

The shared main checkout has diverged from origin/main. This work uses /Users/mitch/dev/worktrees/llms-explorer-hermes-rabbithole-20261027 on branch research/hermes-agent-rabbithole-20261027. Preserve the original checkout, paused embeddings and unrelated runs.

## Measured progress

| Pass | New atoms | Accumulated atoms | New-information rate |
| --- | ---: | ---: | ---: |
| Baseline | 76 normalized from 24 raw rows | 76 | Baseline |
| Depth 1 | 52 | 128 | 40.625% |
| Depth 2 | 16 | 144 | 11.111% |

Corrections, splitting and rephrasing do not earn novelty. The first two depth passes remain above the saturation threshold. Baseline and depth worker event logs disclose a skill-catalog isolation limitation; this run does not establish a clean context-isolation gate. Fetched source bodies alone do not establish a substantive research read. Claim-specific source passages, hashes and reviewer checks address evidence separately.

Local API tests pass 281 cases. Local hub tests pass 594 cases with one skip. Missing declared private libraries were loaded into an isolated verification target; shared virtual environments remain unchanged. The inspected GitHub Actions failures came from Dependabot PRs. GitHub withholds ordinary Actions secrets in that context, so these failures do not prove LIBS_READ_TOKEN is invalid. This branch’s own PR CI remains the delivery gate.

## Remaining work

- Finish measured depth passes and compile the dossier.
- Validate and record final structured claims, render and independently gate them.
- Finish both trees, both concept-pack roots and generated website content.
- Validate owned artifacts and commit/push the scoped delivery.
