# Outsourced scouting and seeding: Antigravity fan-out

`scripts/agy_fanout.py` hands the web legwork of scouting and first seeding to headless, read-only
Antigravity (`agy`) agents and merges what they find into an ordinary scout bundle (schema 1.0.0). The
orchestrating model spends its tokens on reading sources and building claims, not on search. Every
lead is an **unverified candidate**: the agents' queries and access labels earn no evidence credit,
satisfy no discovery or negation floor, and never replace the consumer's own source reading.

Used by `/dr`, `concept-family-explorer`, `rabbithole` and `full-suite`. Their dispatch step is
default-on when `doctor` passes, opt-out with `--no-agy-scout` (`--no-agy` for full-suite), and always
falls back to the previous behavior. A failed, refused, slow or absent scout never blocks research.

## Commands

```bash
S=~/.claude/skills/research-scout/scripts/agy_fanout.py   # repository copy: .claude/skills/research-scout/scripts/
python3 $S doctor [--live]                    # agy on PATH, headless flags present; --live adds one small ping
python3 $S plan --preset dr --concept "<exact concept>" --parent "<exact parent>"    # dry run: tasks, argv, reuse, refusals
python3 $S run  --preset dr --concept "<c>" --parent "<p>" [--concept ... --parent ...] [--background]
python3 $S status <run-dir> [--wait SECONDS]  # exit 2 while running, 0 when finished
python3 $S run --resume <run-dir>             # re-run only failed or missing agents
python3 $S merge <run-dir>                    # rebuild the bundle from agents/*.json
python3 $S probe-llms --host <host>[,<host>] [--from-run <run-dir>] [--mirror]
```

`run` prints JSON. Foreground: the run summary (`run_dir`, `scout_json`, `bundle_status`, task counts,
per-concept status, token usage, `reused`). `--background`: `{"run_dir", "pid", "state": "running"}`
at once; join with `status --wait`. If every concept already has a scouted bundle newer than
`--reuse-days` (default 14, exact name and parent), no run is created and the JSON says
`"state": "fresh"` with `"run_dir": null`; `--reuse-days 0` or `--focus` always scouts.

Exit codes: 0 ok (at least one agent merged, or everything reused), 1 usage or IO error, 2 still
running (`status`), 3 privacy gate refused (nothing sent), 4 every agent failed, 5 `agy` missing,
unauthenticated, out of quota or given an unknown model.

## Presets and angles

One headless `agy -p` per (concept cluster x angle), at most `--max-parallel` (default 4, hard cap 8) at once.

| Preset | Angles (one agent each) | Default cluster | Caller |
| --- | --- | --- | --- |
| `dr` | primary, limits, evidence | 1 | `/dr` Phase 0, per concept |
| `cfe-seeds` | primary, limits | 2 sibling concepts per agent | concept-family-explorer before Step 6 |
| `cfe-frontier` | parent, siblings, children, adjacent, frontier | 1 (the subject) | concept-family-explorer before Step 1 |
| `full-suite` | domains, primary | 3 | full-suite Step 0 |
| `rabbithole` | mechanism, parts, limits, primary, disagreement | 1 | rabbithole Pass 0 |

`--angles a,b` narrows or reorders any preset; `neighbors` (candidates for sibling, child, adjacent or
frontier concepts) is available everywhere. `--cluster N` (1 to 3) groups concepts that share a parent.
`--focus "<gap>"` narrows every angle to one named gap inside the concept (a later rabbithole pass).
`--budget-minutes N` stops starting agents after N minutes; `--timeout` (default 8m) bounds each agent.

| Angle | Brief |
| --- | --- |
| primary | Official docs, specifications and standards, original papers, registry or regulator entries, source repositories. |
| limits | Limits, failure modes, risks, counter-evidence, retractions, postmortems, issue threads. At least one `negation` query. |
| evidence | Independent empirical sources: studies, reviews, benchmarks, trials, datasets, audits. |
| neighbors | Sibling, child, adjacent or emerging concepts the sources expose, each with an opened lead. |
| domains | Authority hostnames (official site, docs host, standards body, regulator, registry, publisher, repository). |
| mechanism, parts, disagreement | How it works; components and sub-types; where experts or documents conflict. |
| parent, siblings, children, adjacent, frontier | The five CFE neighborhoods; each fills `candidates` with the matching relationship. |

## Agent contract

Each agent runs `agy -p <prompt> --output-format json --json-schema <schema> --print-timeout <t> --model <m>
--settings <read-only> --disable-slash-commands` in its own empty scratch directory inside the run
directory. Model: `gemini-3.8-flash-medium`, or `AGY_SCOUT_MODEL`, or `--model`; `--effort` passes through.

- **Permissions** (per session, never saved): allow `read_url(*)`; deny `command(*)`, `write_file(*)`,
  `unsandboxed(*)`, `mcp(*)`; `allowNonWorkspaceAccess` false. `--dangerously-skip-permissions` is never used.
  Tools that need approval are soft-denied in headless mode, so a refused tool shows on stderr, not as a hang.
- **Prompt**: untrusted-content guard, the angle brief, the concept names, parents and aliases, a budget of
  3 to 5 searches and 3 to 6 pages per concept, a required negation query, honest `access` labels
  (`readable` only for a page opened and read), a locator per lead, no invented URLs, no claims or verdicts.
  Read the exact text with `plan --show-prompts` or in the run's `prompts.md`.
- **Schema**: `queries[]`, `leads[]`, `candidates[]`, `domains[]`, `gaps[]`; arrays an angle does not need come back empty.

## Output handling

Agent output is untrusted data. The merge keeps only http(s) URLs with a public host, no credentials and at
most 2048 characters; strips control characters; bounds every string; keeps at most 8 leads, 20 queries,
12 candidates and 12 domains per agent; dedupes URLs across agents into one source with several concept ids;
and keeps the strongest access label. A `readable` claim without a locator is downgraded to `unopened`.
Every source's `limitations` ends with "observed by Antigravity agent, unverified by orchestrator", and
`origin_group` stays null for the consumer to resolve. Candidates need at least one valid lead and carry
`coverage_check.status` `not-checked`: CFE repeats inventory, aliases, placement and CVS. Nothing returned is executed or followed.

Bundle mapping: concepts get selection kind `frontier` (`family-anchor` for `cfe-frontier`) with the absolute
path of the run's `tasks.json`; status is `scouted` (has leads), `no-leads` (agents ran, found none),
`blocked` (every agent for it failed) or `pending`; run status is `ready` only when every agent merged and every
concept has a negation query, else `partial` (`in_progress` while agents run). Files in the run directory
(directory 0700, files 0600): `scout.json`, `handoff.md`, `prompts.md`, `memory.md`, `tasks.json`, `schema.json`,
`status.json`, `domains.json`, and `agents/<task>.json` plus `.stderr` per agent. One writer per run (`run.lock`).

## Privacy gate

Prompts contain public concept names and generic instructions only. Before anything is sent, every concept
(name, parent, aliases) and the focus text are screened. A concept is refused if it contains an email address,
a home-directory path, a key- or token-like string, an internal hostname or private address, a customer name or
repository denylist term (`publish_scrub` when the checkout is reachable), a term from `AGY_SCOUT_DENY`
(comma-separated) or `~/.claude/skill-consolidation/agy-denylist.txt`, or the local account or host name as a whole word.
Default: any refusal exits 3 and sends nothing. `--skip-refused` drops the refused concepts and runs the rest.
A refusal is recorded as a concept index, a digest and category names only, never the text, and the refused
concept is absent from `tasks.json` and the bundle. Remove or rename it, or research it without Antigravity.

## Failure modes

| Condition | Result |
| --- | --- |
| `agy` missing or lacks the headless flags | `doctor` and `run` exit 5; use the caller's previous scouting path |
| Not signed in, quota or rate limit, unknown model | the first such agent stops the run (`fatal`), remaining agents are skipped, exit 5 |
| One agent times out, errors or returns malformed JSON | retried once (`--retries`), then recorded as a gap; the others still merge, status `partial` |
| Every agent fails | exit 4, concepts `blocked` |
| Run interrupted or the process dies | `status` reports `failed`; `run --resume <run-dir>` re-runs only missing or failed agents |

Cost note: measured on a public topic (`dr` preset, angles primary and limits, run in parallel), the two agents took
108 s and 173 s and used 62K and 84K Gemini tokens (146K total, 173 s wall clock), about 25 s of each being CLI cold
start. Tokens bill to the Antigravity quota, not to the orchestrating session. Total agents = clusters x angles; bound
it with `--angles`, `--cluster`, `--max-parallel` and `--budget-minutes`. `plan` shows the count before any spend, and
`doctor --live` costs one small ping (about 25 s).

## `probe-llms`

A deterministic HTTP check, not an agent. For each host it tries `/llms.txt` and `/llms-full.txt` on the host,
its `www` or bare twin and the registrable apex, follows redirects, and rejects HTML pages, soft 404s and any body
whose first line is not a markdown heading. Output per host: found, final URL, bytes, `shape`
(`spec-conformant`, `api-first`, `non-conformant-prose`) and cues (H1, blockquote, `##` sections, link lines,
Optional section, mentions of `llms-full.txt` and `llms-sitemap.txt`, version marker). `--mirror` writes a found
`llms.txt` to `~/.claude/skill-consolidation/mirrors/<host>.md` under the header
`<!-- mirrored <date> from <url> by agy_fanout probe-llms -->`. `--from-run <run-dir>` probes the hosts the
`domains` angle found. It replaces model-based llms.txt checks, whose literal-path misses produced false negatives.

## Reading the results

Unchanged consumer paths: `scout.py seeds --concept ... --parent ...` (at most six candidate URLs with bundle
provenance), `scout.py find --parent ...` (frontier candidates), `with_scout.py` for Claude `/dr` research, and the
repository Codex adapter. Record the run id, revision and source ids of every lead you keep or reject.
