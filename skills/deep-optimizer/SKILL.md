---
name: deep-optimizer
description: >-
  Convergence-loop optimizer family ROUTER. Multi-pass audit-and-fix loops for code, prose, prompts, skills, SQL queries, UI/UX designs, and trading strategies — each loops to zero Medium+ findings with build/verify gates. Routes to: code-deep-optimizer (source files & repos, 16-pass audit, CDO alias /cdo); document-critique (prose docs, passes 0–14, DDO alias /ddo); prompt-deep-optimizer (production prompts in code, PDO alias /pdo); skill-optimizer (SKILL.md files, 15 passes, SKO alias /sko); deep-query-optimizer (SQL queries, EXPLAIN-verified, DQO alias /dqo); design-deep-optimizer (graphic/UI/UX screens, 11-pass critique, DDeSO alias /deso); deep-strategy-optimizer (trading strategies, cards & backtests, 19 passes, DSO alias /dso); llms-deep-optimizer (llms.txt / llms-full / llms-facts / family indexes and topical llms files, 16 passes, LDO alias /ldo). Route to the matching sub-hub. SKIP: MongoDB MQL/aggregation → mongodb-expert (references/deep-mongodb-mql-query-optimizer.md).
origin: local
model: claude-opus-5
effort: high
version: "1.1.0"
updated: "2026-08-04"
---

> **Output rules:** Skip preamble and recaps. When delivering fixes, output diffs/edits directly. Required structured outputs (convergence tables, findings tables) are not preamble; keep them.

# deep-optimizer — convergence-loop optimizer family ROUTER

Eight siblings. Each runs a domain-specific multi-pass audit, applies every Medium+ fix in place, verifies the result, and loops to convergence.

| Sub-hub | Domain | Alias | Key gates |
|---|---|---|---|
| `code-deep-optimizer` | Source files & repos (any language/framework) | `/cdo` | build/lint/tests verify gate; 16 passes |
| `document-critique` | Prose documents (specs, RFCs, runbooks, KBs) | `/ddo` | passes 0–14; blind re-audit; human-voice pass |
| `prompt-deep-optimizer` | Production prompts shipped in code | `/pdo` | 16 passes; injection guard; algorithm pick |
| `skill-optimizer` | `SKILL.md` files | `/sko` | 15 passes A–O; Pass H trigger eval; hub sync |
| `deep-query-optimizer` | SQL queries (Postgres/MySQL/SQLite/SQL Server) | `/dqo` | EXPLAIN/EXPLAIN ANALYZE verify; index DDL |
| `design-deep-optimizer` | Graphic/brand & UI/UX screens | `/deso` | 11-pass critique; WCAG verify; code-backed fixes |
| `deep-strategy-optimizer` | Trading strategies, their cards & backtests | `/dso` | 19 passes; project test + figure-verification gate; opt-in held-out promotion |
| `llms-deep-optimizer` | `llms.txt` / `llms-full.txt` / `llms-facts.txt` / family indexes; topical llms files from fact pools | `/ldo` | 16 passes P0–P15; `llms_lint.py` deterministic gate; FTS5 keyword + vector + agent-usability probes |

## Routing

Identify the artifact type and route:

- **Code (`.js`, `.ts`, `.py`, `.go`, `.rs`, `.java`, any source file or repo)** → `code-deep-optimizer`
- **Prose document (spec, RFC, README, runbook, KB article, weekly update)** → writing-expert (references/document-critique.md)
- **Production prompt (system prompt, agent instruction block, tool template in codebase)** → `prompt-deep-optimizer`
- **Skill file (`SKILL.md`, Claude Code skill)** → `skill-optimizer`
- **SQL query** → `deep-query-optimizer`
- **llms file (`llms.txt`, `llms-full.txt`, `llms-small.txt`, `llms-facts.txt`, a `<stem>.llms/` export dir, a family index) or "build an llms file for <topic>"** → `llms-deep-optimizer`. Route here for links/descriptions/facts/serving of the file itself; a `SKILL.md` about a site still goes to `skill-optimizer`.
- **MongoDB MQL / aggregation pipeline** → mongodb-expert (references/deep-mongodb-mql-query-optimizer.md) (mongodb family)
- **UI/UX screen, mockup, design asset, or HTML/CSS** → `design-deep-optimizer`
- **Trading strategy, strategy card, or the backtest/research that measured it** → `deep-strategy-optimizer`. Route here for "is this number real" (lookahead, cost path, overfitting, evidence floor); route to `code-deep-optimizer` for the same file's code health. Educational market questions go to `trading-and-investing`, not here.

## Cross-hub map

| Hub | Owns |
|---|---|
| `deep-optimizer` | This router — all optimizer siblings |
| `mongodb-expert` | `deep-mongodb-mql-query-optimizer` (MQL/aggregation optimizer) |
| `software-engineering-patterns` | `/code-review` (one-shot diff review, not a convergence loop) |
| `skill-tree-architect` | Whole-tree taxonomy rebalance (not a per-artifact optimizer) |
