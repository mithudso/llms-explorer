---
name: deep-optimizer
description: >-
  Route mixed-artifact optimization work to the matching deep-optimizer family member, or plan a resumable folder/session sweep. TRIGGER: "which optimizer fits these files", "run deep optimizer", "sweep this folder", "optimize everything changed this session". Covers code, prose, prompts, skills, agents, evals, SQL, MongoDB MQL, UI, graphics, llms files and trading strategies. SKIP: a single known artifact uses its specialist: code-deep-optimizer; writing-expert (references/document-critique.md); prompt-deep-optimizer; skill-optimizer; agent-deep-optimizer; deep-eval-optimizer; deep-query-optimizer; deep-mongodb-mql-query-optimizer; ui-deep-optimizer; design-deep-optimizer; llms-deep-optimizer; deep-strategy-optimizer. Whole-tree skill taxonomy uses skill-tree-architect.
origin: local
model: claude-opus-5-5
effort: high
version: "1.5.0"
updated: "2026-11-11"
category: meta
whenToUse:
  - "Which optimizer should review these mixed files?"
  - "Sweep this folder with the matching optimizers"
  - "Optimize all files changed in this session"
related_skills:
  - code-deep-optimizer
  - skill-optimizer
  - agent-deep-optimizer
  - deep-eval-optimizer
  - ui-deep-optimizer
metadata:
  changelog_ref: references/CHANGELOG.md
---

> **Output rules:** Skip preamble and recaps. When delivering fixes, output diffs/edits directly. Required structured outputs (convergence tables, findings tables) are not preamble; keep them.

# deep-optimizer — convergence-loop optimizer family ROUTER

The optimizer family uses domain-specific multi-pass audits, verifies changes, and loops to a supported exit.

**Check the write mode.** Most members can fix editable targets in place. `prompt-deep-optimizer` reports the rewrite and writes the target only under its opt-in `--write` flag — a production prompt is usually a string embedded in source, so an unrequested write lands in the middle of a code file. Check the Writes column before assuming a run changed anything on disk.

| Sub-hub | Domain | Alias | Writes | Key gates |
|---|---|---|---|---|
| `code-deep-optimizer` | Source files & repos (any language/framework) | `/cdo` | in place | build/lint/tests verify gate; 18 passes |
| `document-critique` | Prose documents (specs, RFCs, runbooks, KBs) | `/ddo` | in place | passes 0–14; blind re-audit; human-voice pass |
| `prompt-deep-optimizer` | Production prompts shipped in code | `/pdo` | **report only; `--write` opt-in** | 16 passes; injection guard; algorithm pick; `pdo_tools.py selfcheck` executed gate; evidence grading (EXECUTED/ISOLATED/SIMULATED) |
| `skill-optimizer` | `SKILL.md` files | `/sko` | in place | 16 passes A–P; Pass H trigger eval; hub sync |
| `agent-deep-optimizer` | Claude Code subagent definitions (`~/.claude/agents/*.md`, `.claude/agents/`, plugin agents read-only) | `/ado` | in place | 16 passes A–P; `ado_tools.py schema` deterministic gate; 10+10 delegation eval; optional `claude -p --agent` load check; registry `agent:<name>` verify |
| `deep-eval-optimizer` | Skill evaluation suites | `/deo` | in place | 12-pass evaluation audit and optional measured execution |
| `deep-query-optimizer` | SQL queries (Postgres/MySQL/SQLite/SQL Server) | `/dqo` | in place | EXPLAIN/EXPLAIN ANALYZE verify; index DDL |
| `design-deep-optimizer` | Graphic/brand & UI/UX screens | `/deso` | in place | 11-pass critique; WCAG verify; code-backed fixes |
| `ui-deep-optimizer` | Existing interface visual design, workflows and interaction | `/ui-deep-optimizer` | editable targets; report-only otherwise | 70 methods; immediate Medium+ repairs per pass; fresh rendering and complete no-edit sweep |
| `deep-strategy-optimizer` | Trading strategies, indicators, their cards & backtests | `/dso` | in place | 273 passes, one per evaluation method, in 9 families; strategy/indicator applicability filter; project test + figure-verification gate; opt-in held-out promotion |
| `llms-deep-optimizer` | `llms.txt` / `llms-full.txt` / `llms-facts.txt` / family indexes; topical llms files from fact pools | `/ldo` | in place | 16 passes P0–P15; `llms_lint.py` deterministic gate; FTS5 keyword + vector + agent-usability probes |

## Routing

Identify the artifact type and route:

- **Code (`.js`, `.ts`, `.py`, `.go`, `.rs`, `.java`, any source file or repo)** → `code-deep-optimizer`
- **Prose document (spec, RFC, README, runbook, KB article, weekly update)** → writing-expert (references/document-critique.md)
- **Production prompt (system prompt, agent instruction block, tool template in codebase)** → `prompt-deep-optimizer`
- **Skill file (`SKILL.md`, Claude Code skill)** → `skill-optimizer`
- **Subagent definition (`~/.claude/agents/<name>.md`, `.claude/agents/<name>.md`, an `--agents` JSON entry; "my agent never gets picked", "least-privilege tools for this agent")** → `agent-deep-optimizer`. The body is a system prompt, but the artifact is the whole file (frontmatter grant, precedence, routing, final-report contract); `prompt-deep-optimizer` gets only a bounded sub-dispatch over the body.
- **Skill evaluation suite** → `deep-eval-optimizer`
- **SQL query** → `deep-query-optimizer`
- **llms file (`llms.txt`, `llms-full.txt`, `llms-small.txt`, `llms-facts.txt`, a `<stem>.llms/` export dir, a family index) or "build an llms file for <topic>"** → `llms-deep-optimizer`. Route here for links/descriptions/facts/serving of the file itself; a `SKILL.md` about a site still goes to `skill-optimizer`. *Building* a concept pack (everything about X across docsets) is `llms-concept-abstractor` (`/lca`), which hands the result here with `--ldo`.
- **MongoDB MQL / aggregation pipeline** → `deep-mongodb-mql-query-optimizer`
- **Existing UI/UX interface, workflow, screen, or HTML/CSS** → `ui-deep-optimizer`. Graphic/brand assets and asset-only visual critiques → `design-deep-optimizer`.
- **Trading strategy, indicator or scorecard, strategy card, or the backtest/research that measured it** → deep-strategy-optimizer. Route here for "is this number real" or "is this signal real" (lookahead, cost path, overfitting, evidence floor, hit rate vs base rate); route to `code-deep-optimizer` for the same file's code health. Educational market questions go to `trading-and-investing`, not here.

## Sweep mode: `--sweep <folder|session>`

For "run X on every file in this folder" and "run the optimizers on everything created this
session". The router enumerates, routes each file to its member, and keeps a resumable ledger;
the members still own their own loops. Engine: `scripts/sweep.py` (stdlib; `--help` for usage).

1. **Plan.** Resolve the sweep helper from the selected optimizer directory. Use `python3 "<optimizer-dir>/scripts/sweep.py" plan --folder <DIR>`, or the same absolute helper with `plan --session` while working inside the target repo (targets are its dirty tree plus branch commits, or `--since "6 hours ago"` / `--base REF`). The `sweep.py` shorthand below always means that absolute bundled helper, not a script in the target repository.
   It writes `<DIR>/.sweep/ledger.json` (session: `<git root>/.sweep/session.json`), one row per
   file with `member`, `alias`, `status`. Show the per-member counts, then proceed. Unroutable files
   (binaries, data) become `skipped` rows with a reason. `--map .ext=member` overrides a route. Ambiguous JSON is not inferred as MQL: use `--map .json=deep-mongodb-mql-query-optimizer` for a deliberately selected pipeline set; the alias is `/dmqo`. Changing the explicit route invalidates an old skipped/completed route, preserving prior failure details.
2. **Dispatch.** Loop: `sweep.py next --n 4` claims up to 4 pending rows (the cap counts rows already
   in flight). Dispatch one subagent per claimed row invoking that row's `alias` on that one file,
   all claimed rows in a single parallel batch; no nested dispatch. Rows for `/cdo` are batched
   into one `--scope=<paths>` call per repo so cdo's own `.cdo/ledger.json` applies.
3. **Record.** `sweep.py done <path> --status done|failed --findings N --note "<Status>"` after each
   subagent returns. A failed row is reported and retained with its note across reset/replan. Requeue it only with the explicit `sweep.py retry <path>` action; its failure history remains attached.
4. **Resume.** After an interruption run `sweep.py reset` (running -> pending), then `plan` again:
   it keeps completed/skipped rows only when file SHA and route are unchanged, and requeues edited non-failed rows. Failed rows remain failed even after content or route edits; the explicit `retry` action applies the planned change and preserves the failure history. `sweep.py status`
   lists what is still open.
5. **Report** the final `status` counts and each member's own Status line. Do not start convergence
   loops beyond what each member runs on its own row, and do not widen the sweep past the plan.

Routing in the plan: `SKILL.md` -> `/sko`; `agents/*.md` -> `/ado`; `*.sql` -> `/dqo`; `llms*.txt`
or `*.llms/` -> `/ldo`; `prompts/` or `*.prompt*` -> `/pdo`; `strategy_cards/*.md` -> `/dso`;
`evals/evals.json` -> `/deo`; images -> `/deso`; `.html`, `.css` -> `/ui-deep-optimizer`; source code -> `/cdo`; other
prose (`.md`, `.txt`, `.rst`, `.docx`, `.pdf`) -> `/ddo`.

## Cross-hub map

| Hub | Owns |
|---|---|
| `deep-optimizer` | This router — all optimizer siblings |
| `mongodb-expert` | `deep-mongodb-mql-query-optimizer` (MQL/aggregation optimizer) |
| `software-engineering-patterns` | `/code-review` (one-shot diff review, not a convergence loop) |
| `skill-tree-architect` | Whole-tree taxonomy rebalance (not a per-artifact optimizer) |
| `agent-asset-parity-auditor` (agent) | Roster-wide missing / ignored / stale-copy agent audit (not a per-artifact optimizer) |
