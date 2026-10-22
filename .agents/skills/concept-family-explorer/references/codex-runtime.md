# Codex research runtime

These are repository skills under `.agents/skills`. The sync does not install
anything in `~/.codex`. Run `python3 scripts/sync_codex_research_skills.py --check`
to detect source drift; omit `--check` to sync with an automatic backup.

## Models and effort

| Claude role | Codex role |
| --- | --- |
| Sonnet | `gpt-6.1-sol` |
| Opus / Fable | `gpt-6-astra` |
| Haiku | `gpt-6-luna` |

This maps workflow tiers, not equivalent model capability or price. Claude study
results in inherited changelogs describe Claude runs only. Codex comparisons live
in the repository research benchmark report. Supported reasoning efforts on this
installation are `low`, `medium`, `high`, `xhigh`, and `max`; retain the requested
effort. The skill's `model` and `effort` frontmatter document defaults. They do not
switch the active Codex session. Headless invocations enforce them with `--model`
and `-c 'model_reasoning_effort="max"'` (or the requested effort).

Codex `/dr` defaults to `gpt-6-luna` at `max` effort. Standard research runs one
Luna/max research pass with deliberate scouting for deeper sources. When the scout
finds unread deeper evidence with a stated information gap, the
adapter runs one additional Luna/max pass seeded with those discoveries and merges
both results. Domain-specific primary-source and independent-origin requirements, missing
source/unique-claim floors or an incomplete scout report also trigger
that follow-up. Already-read non-doc sources alone do not trigger repetition. A complete result
meeting the domain requirements stops after the first pass. Each run records
normalized unique facts, novel mechanisms and origin proxies. Gate-confirmed
novel facts are a lower bound; unaudited facts are never labeled supported. The merge
and scope check remain `gpt-6.1-sol` at `medium`. Explicit model/effort overrides
apply to both standard research passes. Quick keeps one low-effort pass; saturate
keeps two independent max-effort passes. `--passes` counts additional passes in
the adaptive lane, so its standard default is 1 (two research passes in total).

## Research and shared resources

New runs use research-gate/v2. Gate input predetermines all version/default,
numeric, API, security and volatile claims plus a deterministic ordinary sample
(standard: ten, quick: zero, saturate: all). Quick still checks risky claims.
Each verdict must preserve the exact full claim, ID and hash, and bind exact
Unicode evidence spans to pinned source snapshot hashes. Missing, duplicate,
altered or stale judgments fail. Non-supported verdicts stop promotion. Finish
rechecks the canonical inputs and evidence; legacy receipts are not v2 evidence.
Private gate attempts and raw source bodies stay outside public outputs.

From the repository root, use
`python3 .agents/skills/dr/scripts/codex_dr_run.py <subcommand> ...` for every
`dr_run.py` operation below. From another working directory, use this helper's
absolute path and absolute render output paths. It loads
`~/.global-ai-hub/scripts/dr_run.py` (override with
`DR_SHARED_RUN`) and applies Codex defaults, transport, and completion hooks in memory.
It preserves adaptive scouting, escalation, source seeding, scope filtering,
merging, claim gates, schema validation, resume, locking, and shared state.
The Codex `finish` command compiles the recorded claims to llms concept packs
and merges both `~/.global-ai-hub/concept-tree/tree.json` and
`<repo>/concept-tree/tree.json`, including standalone and orchestrated runs.
It writes `llms.txt`, `llms-full.txt`, `llms-small.txt`, `llms-facts.txt`, and
`llms-vocabulary.txt`, plus units, graph and manifest, under both
`~/.global-ai-hub/llms-concepts/<slug>.llms/` and
`<repo>/outputs/llms-concepts/<slug>.llms/`. Authored statements retain their full
text, caveats, confidence labels and verification dates. Hub packs retain original
source URLs. Repository copies scrub private identifiers and withheld references.
Denylisted topics and descendants retain hub packs;
repository packs and website data exclude them. Existing repository copies are
backed up before removal. Each tree is merged independently, with backups and
publishable nodes preserved. The run records `artifacts/receipt.json` and `codex_artifacts` in its
manifest. Completion also regenerates website reader JSON, tree JSON, context
JSON and downloadable facts. Read `references/research-library.md`: /dr, CFE and
rabbithole share source snapshots and extracts, and research briefs receive
bounded local-library seed sources before external discovery.
Export or website-refresh failures stop finalization and can be retried. Completed
concepts in budget-exhausted runs receive partial packs; runs with no recorded
claims or failed verification do not promote research. Local tree updates do
not commit, push, or publish. `LLMS_EXPLORER_REPO` selects the repository when
the adapter is installed elsewhere.
It never invokes Claude. `research --dry-run` generates Codex briefs without
calling a model. Research workers validate with `claims-check`; the parent
research command alone records `concept-done` after merging.

Each worker uses `codex exec --ignore-user-config --ephemeral --json`, the
workspace-write sandbox, an enforced wall-clock timeout, live web search for
research/gates, disabled hooks/plugins/apps/host skill discovery, explicit
`skills.config` disablement of every discovered skill folder (including symlink
targets), and no MCP
servers. A merge call disables shell and web tools. Codex does not expose
Claude's `--max-turns`; the adapter records that requested hint as unenforced.
Token usage is measured from JSON events. Cost is unknown unless Codex reports
it; do not interpret a shared runtime's aggregate zero as a free run.

Paths under `~/.claude/skill-consolidation` and canonical peer skills are real
shared resources. Do not rename them to nonexistent Codex directories. Existing
hub manifests, router, and tree helper use that shared catalogue. A new Codex
skill may instead be rendered to `<repo>/.agents/skills/<slug>/SKILL.md` (or
`~/.codex/skills/<slug>/SKILL.md` only when user-level installation is requested).
Use an existing Codex hub only when it exists. Verify filesystem installation;
the shared semantic router may not index a Codex-only destination, so report
registry verification as unavailable rather than claiming it passed. Never
create a second catalogue or silently edit a canonical peer to satisfy a route.
