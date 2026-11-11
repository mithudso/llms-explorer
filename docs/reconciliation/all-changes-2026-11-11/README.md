# All-change reconciliation

Version:1.1.0. Delta: complete semantic dispositions and verified public integration. Task:TASK-1359.

User request: Merge commit push all changes.

The coordinator integrates only reviewed public deltas onto current main. Old branches
contain intentionally purged history; never push or merge them raw. All pending tracked,
staged, untracked and absent paths are inventoried and privately recoverable. Private
source bodies and credentials stay outside this repository.

## Recovery

Sixteen original worktrees; seven dirty;1,966 expanded paths;1,914 extant files/symlinks.
All source/index/status readbacks were stable. Recovery manifestSHA256:
b48f13ac0f7d9c1718ddd9d71ff75c4f75616f9809e33db718ffb47b022c77da.
Private storage: /Users/mitch/.local/state/llms-explorer-all-changes-20261111/.

## Public integration

- Combine dependency PR intents 330, 331, 332 and 336 with refreshed MCP 2.3.0 locks and native protocol verification on SDK 2 and supported SDK 1 baselines.
- Keep HuggingFace Hub at resolved 1.33.0: FastEmbed still constrains the transitive range below 2. The widened direct bound does not establish support for Hub 2.
- Add the v3 sitemap companion and historical access migration while retaining current qualified facts, exporter family API and shared linter. The public site excludes local resource paths and commands.
- Port matrix retrieval and streamed VecStore scoring with current embedding contracts, lexical fusion and model/LAN policy retained. Same-hash GC and reinsertion must invalidate old vectors before the next query.
- Archive 16 duplicate legacy root skill files byte-for-byte. Active canonical skills remain discoverable.
- Preserve both continuation histories after workstation PR338 reached main.

## Complete dispositions

The sanitized category counts are in `dispositions.json`. The complete private manifest is
`/Users/mitch/.local/state/llms-explorer-all-changes-20261111/all-path-dispositions.json`.
It accounts for every one of the original 1,966 expanded pending paths, including already
delivered bytes, stale projections, retained current privacy/research policy, invalid generated
agent adapters, private backups/browser artifacts and incomplete fleet automation. None of
those private bodies are copied into Git. A later read-only byte audit found no original
source drift. The original active checkouts remain untouched.

The invalid generated frontier adapter contains nonexistent translated model/command names;
the canonical current agent remains authoritative. Old snapshot trees, private watch roots,
raw logs and incomplete automation do not establish publishable changes.

## Verification and delivery

Package, native protocol, full Hub, API, CLI, site build/type/test, privacy and projection
checks are recorded in the private check receipts. Independent review identified and closed
the cache invalidation defect. Full-suite fixtures bind reviewed checkout modules so a deployed
Hub import cannot silently substitute installed code. Final CI must pass on the exact pushed
tip before merge; remote content and deployed public sitemap are the final delivery gates.

A private recovery snapshot is preservation, not proof that every path is safe to publish.
