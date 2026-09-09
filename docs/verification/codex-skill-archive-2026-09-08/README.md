# Codex skill archive — 2026-09-08

Version: 1. Active skill delta: 730 → 666 (−64).

Archived 52 duplicate or superseded entries, 10 thin Claude command aliases, and 2 authoring examples. Exact duplicates were compared after removing frontmatter and generated resource-location metadata. Five near-duplicates were reviewed for plugin fixes: a11y-debugging, caveman-compress, cloudflare-one, stripe-apps, web-perf. Same-named skills with substantive differences remain. Specialized subject matter and references to Claude alone were not exclusion criteria. This is discovery curation, not certification that every remaining workflow or external service runs.

Claude sources and supporting resources remain intact. Archived entry files live outside discovery roots. Path-specific disabled settings in ~/.codex/config.toml prevent migrated copies from becoming active again. No plugins or MCP servers were disabled.

Fresh skills/list with forceReload in ~, llms-explorer, and codex-local-ai-setup reports 666 active skills and zero errors each. All 62 replacement paths remain active. All 64 archive hashes and persistent disabled selectors passed verification.

## Restore

Local archive: `~/.codex/skill-archive/20260908T111122Z`.

From this repository, run the preflight; add --apply to restore:

```sh
python3 scripts/restore_archived_codex_skills.py ~/.codex/skill-archive/20260908T111122Z/manifest.json
```

Restore preserves the archive and refuses to overwrite changed files. It requires the existing codex_rpc.py helper in codex-local-ai-setup (override with --rpc-dir). Restore individual enablement settings; do not replace the whole Codex config with its snapshot, which could discard later changes. Existing agent sessions need a restart to refresh cached skill catalogs.

## Archived entries

- **a11y-debugging**: Superseded by reviewed plugin version. Retained: `~/.codex/plugins/cache/claude-plugins-official/chrome-devtools-mcp/1.8.0/skills/a11y-debugging/SKILL.md`.
- **agent-development**: Duplicate body. Retained: `~/.codex/plugins/cache/claude-plugins-official/plugin-dev/local/skills/agent-development/SKILL.md`.
- **behavior-change-psychology**: Duplicate body. Retained: `~/.agents/skills/applied-psychology/references/behavior-change-psychology/SKILL.md`.
- **behavioral-decision-making**: Duplicate body. Retained: `~/.agents/skills/applied-psychology/references/behavioral-decision-making/SKILL.md`.
- **bf-triage**: Duplicate body. Retained: `~/.codex/plugins/cache/mongodb-internal/bf-triage/local/skills/bf-triage/SKILL.md`.
- **brainstorming**: Duplicate body. Retained: `~/.codex/plugins/cache/mongodb-internal/before-you-code/1.0.0/brainstorming/skills/brainstorming/SKILL.md`.
- **cavecrew**: Duplicate body. Retained: `~/.codex/plugins/cache/caveman/caveman/local/skills/cavecrew/SKILL.md`.
- **caveman-commit**: Duplicate body. Retained: `~/.codex/plugins/cache/caveman/caveman/local/skills/caveman-commit/SKILL.md`.
- **caveman-compress**: Superseded by reviewed plugin version. Retained: `~/.codex/plugins/cache/caveman/caveman/local/skills/caveman-compress/SKILL.md`.
- **caveman-help**: Duplicate body. Retained: `~/.codex/plugins/cache/caveman/caveman/local/skills/caveman-help/SKILL.md`.
- **caveman-review**: Duplicate body. Retained: `~/.codex/plugins/cache/caveman/caveman/local/skills/caveman-review/SKILL.md`.
- **claude-md-improver**: Duplicate body. Retained: `~/.codex/plugins/cache/claude-plugins-official/claude-md-management/1.0.0/skills/claude-md-improver/SKILL.md`.
- **cloudflare-one**: Superseded by reviewed plugin version. Retained: `~/.codex/plugins/cache/cloudflare/cloudflare/1.0.0/skills/cloudflare-one/SKILL.md`.
- **cloudflare-one-migrations**: Duplicate body. Retained: `~/.codex/plugins/cache/cloudflare/cloudflare/1.0.0/skills/cloudflare-one-migrations/SKILL.md`.
- **command-development**: Duplicate body. Retained: `~/.codex/plugins/cache/claude-plugins-official/plugin-dev/local/skills/command-development/SKILL.md`.
- **connect-recommend**: Duplicate body. Retained: `~/.codex/plugins/cache/claude-plugins-official/stripe/0.6.4/skills/connect-recommend/SKILL.md`.
- **connect-required-verification-information**: Duplicate body. Retained: `~/.codex/plugins/cache/claude-plugins-official/stripe/0.6.4/skills/connect-required-verification-information/SKILL.md`.
- **copilot-adversarial-review**: Duplicate body. Retained: `~/.codex/plugins/cache/mongodb-internal/copilot-adversarial-review/local/skills/copilot-adversarial-review/SKILL.md`.
- **cost-reducer**: Duplicate body. Retained: `~/.codex/plugins/cache/mongodb-internal/cost-reducer/local/skills/cost-reducer/SKILL.md`.
- **customer-satisfaction-loyalty-science**: Duplicate body. Retained: `~/.agents/skills/applied-psychology/references/customer-satisfaction-loyalty-science/SKILL.md`.
- **dispatching-parallel-agents**: Duplicate body. Retained: `~/.codex/plugins/cache/mongodb-internal/before-you-code/1.0.0/dispatching-parallel-agents/skills/dispatching-parallel-agents/SKILL.md`.
- **emotion-and-affect-psychology**: Duplicate body. Retained: `~/.agents/skills/applied-psychology/references/emotion-and-affect-psychology/SKILL.md`.
- **enterprise-b2b-buyer-psychology**: Duplicate body. Retained: `~/.agents/skills/applied-psychology/references/enterprise-b2b-buyer-psychology/SKILL.md`.
- **enterprise-poc-technical-validation**: Duplicate body. Retained: `~/.agents/skills/tam-operations/references/enterprise-poc-technical-validation/SKILL.md`.
- **firedrill-integration-tester**: Duplicate body. Retained: `~/.agents/skills/tam-operations/references/firedrill-integration-tester/SKILL.md`.
- **git-workflows**: Duplicate body. Retained: `~/.codex/plugins/cache/mongodb-internal/git-workflows/local/skills/git-workflows/SKILL.md`.
- **hook-development**: Duplicate body. Retained: `~/.codex/plugins/cache/claude-plugins-official/plugin-dev/local/skills/hook-development/SKILL.md`.
- **human-ai-interaction-psychology**: Duplicate body. Retained: `~/.agents/skills/applied-psychology/references/human-ai-interaction-psychology/SKILL.md`.
- **incident-response**: Duplicate body. Retained: `~/.agents/skills/tam-operations/references/incident-response/SKILL.md`.
- **learning-and-expertise-psychology**: Duplicate body. Retained: `~/.agents/skills/applied-psychology/references/learning-and-expertise-psychology/SKILL.md`.
- **live-hub-toolkit**: Duplicate body. Retained: `~/.agents/skills/chrome-extension-expert/references/live-hub-toolkit/SKILL.md`.
- **llm-quantization-strategies**: Duplicate body. Retained: `~/.agents/skills/misc-catch-all/references/llm-quantization-strategies/SKILL.md`.
- **mongodb-connection**: Duplicate body. Retained: `~/.codex/plugins/cache/claude-plugins-official/mongodb/1.2.1/skills/mongodb-connection/SKILL.md`.
- **moral-psychology**: Duplicate body. Retained: `~/.agents/skills/applied-psychology/references/moral-psychology/SKILL.md`.
- **okta-incident-response**: Duplicate body. Retained: `~/.agents/skills/misc-catch-all/references/okta-incident-response/SKILL.md`.
- **performance-and-resilience-psychology**: Duplicate body. Retained: `~/.agents/skills/applied-psychology/references/performance-and-resilience-psychology/SKILL.md`.
- **personality-and-individual-differences**: Duplicate body. Retained: `~/.agents/skills/applied-psychology/references/personality-and-individual-differences/SKILL.md`.
- **persuasion-and-influence-psychology**: Duplicate body. Retained: `~/.agents/skills/applied-psychology/references/persuasion-and-influence-psychology/SKILL.md`.
- **plugin-settings**: Duplicate body. Retained: `~/.codex/plugins/cache/claude-plugins-official/plugin-dev/local/skills/plugin-settings/SKILL.md`.
- **pr-review-loop**: Duplicate body. Retained: `~/.codex/plugins/cache/mongodb-internal/pr-review-loop/local/skills/pr-review-loop/SKILL.md`.
- **receiving-code-review**: Duplicate body. Retained: `~/.codex/plugins/cache/mongodb-internal/before-you-merge/1.0.0/receiving-code-review/skills/receiving-code-review/SKILL.md`.
- **resolve-pr-comments**: Duplicate body. Retained: `~/.codex/plugins/cache/mongodb-internal/before-you-merge/1.0.0/resolve-pr-comments/skills/resolve-pr-comments/SKILL.md`.
- **screenwriting-craft**: Duplicate body. Retained: `~/.agents/skills/misc-catch-all/references/screenwriting-craft/SKILL.md`.
- **session-report**: Duplicate body. Retained: `~/.codex/plugins/cache/claude-plugins-official/session-report/local/skills/session-report/SKILL.md`.
- **skill-creator**: Duplicate body. Retained: `~/.codex/plugins/cache/claude-plugins-official/skill-creator/local/skills/skill-creator/SKILL.md`.
- **stripe-apps**: Superseded by reviewed plugin version. Retained: `~/.codex/plugins/cache/claude-plugins-official/stripe/0.6.4/skills/stripe-apps/SKILL.md`.
- **stripe-docs**: Duplicate body. Retained: `~/.codex/plugins/cache/claude-plugins-official/stripe/0.6.4/skills/stripe-docs/SKILL.md`.
- **stripe-projects**: Duplicate body. Retained: `~/.codex/plugins/cache/claude-plugins-official/stripe/0.6.4/skills/stripe-projects/SKILL.md`.
- **trust-and-psychological-safety**: Duplicate body. Retained: `~/.agents/skills/applied-psychology/references/trust-and-psychological-safety/SKILL.md`.
- **verification-before-completion**: Duplicate body. Retained: `~/.codex/plugins/cache/mongodb-internal/before-you-merge/1.0.0/verification-before-completion/skills/verification-before-completion/SKILL.md`.
- **web-perf**: Superseded by reviewed plugin version. Retained: `~/.codex/plugins/cache/cloudflare/cloudflare/1.0.0/skills/web-perf/SKILL.md`.
- **writing-plans**: Duplicate body. Retained: `~/.codex/plugins/cache/mongodb-internal/before-you-code/1.0.0/writing-plans/skills/writing-plans/SKILL.md`.
- **claude-command-cdo**: Thin Claude command alias; canonical workflow remains available. Retained: `~/.agents/skills/code-deep-optimizer/SKILL.md`.
- **claude-command-cfe**: Thin Claude command alias; canonical workflow remains available. Retained: `~/.agents/skills/concept-family-explorer/SKILL.md`.
- **claude-command-ddo**: Thin Claude command alias; canonical workflow remains available. Retained: `~/.agents/skills/ddo/SKILL.md`.
- **claude-command-deso**: Thin Claude command alias; canonical workflow remains available. Retained: `~/.agents/skills/design-deep-optimizer/SKILL.md`.
- **claude-command-dmqo**: Thin Claude command alias; canonical workflow remains available. Retained: `~/.agents/skills/deep-mongodb-mql-query-optimizer/SKILL.md`.
- **claude-command-dqo**: Thin Claude command alias; canonical workflow remains available. Retained: `~/.agents/skills/deep-query-optimizer/SKILL.md`.
- **claude-command-lca**: Thin Claude command alias; canonical workflow remains available. Retained: `~/.agents/skills/llms-concept-abstractor/SKILL.md`.
- **claude-command-ldo**: Thin Claude command alias; canonical workflow remains available. Retained: `~/.agents/skills/llms-deep-optimizer/SKILL.md`.
- **claude-command-pdo**: Thin Claude command alias; canonical workflow remains available. Retained: `~/.agents/skills/prompt-deep-optimizer/SKILL.md`.
- **claude-command-sko**: Thin Claude command alias; canonical workflow remains available. Retained: `~/.agents/skills/skill-optimizer/SKILL.md`.
- **example-command**: Generic plugin authoring demonstration; no operational workflow. Retained: `not applicable (example)`.
- **example-skill**: Generic plugin authoring demonstration; no operational workflow. Retained: `not applicable (example)`.
