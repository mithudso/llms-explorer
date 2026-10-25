# Local MongoDB round continuation

Version: 1.2.0
Delta: 1.1.0 to 1.2.0; independent verifier confirmed actual source activity; draft PR opened.
Task: TASK-904; selection TASK-906, launch TASK-907, verification TASK-908.

## Scope and evidence

User explicitly authorized a new local research round because the source machine is unavailable. The native planner scanned the local October 20 queue and excluded coverage and reservations. Selected names have no matches in the hub tree, current origin/main repository tree, aliases or local research manifests. This is local evidence; remote completion is unknown.

- Hashed vs ranged shard key query trade-offs
- Multikey index coverage and multiKeyPaths
- Find projection vs $project aggregation coverage
- Collation-based case-insensitive equality

## Runtime

Repository: /Users/mitch/dev/worktrees/llms-explorer-mongodb-local-20261024
Base revision: a97cd05f
Private plan: /Users/mitch/.global-ai-hub/research/.ranked/mongodb-local-20261024/plan.json
Private source selection: /Users/mitch/.global-ai-hub/research/.ranked/mongodb-local-20261024/round-source.md
Launcher log: /Users/mitch/.global-ai-hub/research/.ranked/mongodb-local-20261024/runner.log

KNOW-881 supersedes the old Luna/max default for new runs. Use gpt-6.1-sol at medium effort, four workers, the shared private source library and a bound Sol/medium gate. Native finish must export both trees, packs and generated website content. Keep embeddings paused. No legacy reservation or canonical October 22 plan was modified.

## Live startup

Native runner PID 64620 owns the private plan. Adapter PID 65033 runs research for ranked-17bfb8f4. Four child Codex workers (65040, 65065, 65244, 65506) use gpt-6.1-sol at medium effort. Independent live verification confirmed ranked runner and adapter bytes match revision a97cd05fed3e60ba033846346af9319f5d5a9188. The manifest uses research-gate/v2. At the startup checkpoint all four concepts remained pending. At 2026-10-25T03:43:14Z the independent verifier observed 13 source records, up from zero. Collation worker child processes executed native source-put calls for official MongoDB and Spring documentation and issue evidence. The projection worker also recorded a covered-query source. All four workers remained active. These are research-progress observations; no claims or gates were complete.

Run directory: /Users/mitch/.global-ai-hub/research/ranked-17bfb8f4/
Launch receipt: /Users/mitch/.global-ai-hub/research/.ranked/mongodb-local-20261024/launch.json
Phase events: /Users/mitch/.global-ai-hub/research/.ranked/mongodb-local-20261024/ranked-17bfb8f4.events.jsonl

## Remaining steps

Startup verification passed. Monitor research, optional follow-up, gate, export and local publication. Inspect dissent before publishing. Preserve this active research worktree. Reconcile the unavailable run before combining results.

Inspect status:

```sh
python3 /Users/mitch/dev/worktrees/llms-explorer-mongodb-local-20261024/scripts/codex_ranked_research.py status --plan /Users/mitch/.global-ai-hub/research/.ranked/mongodb-local-20261024/plan.json
```

Resume only after confirming the saved runner PID and lock have no live owner:

```sh
python3 /Users/mitch/dev/worktrees/llms-explorer-mongodb-local-20261024/scripts/codex_ranked_research.py run --repo /Users/mitch/dev/worktrees/llms-explorer-mongodb-local-20261024 --hub /Users/mitch/.global-ai-hub --plan /Users/mitch/.global-ai-hub/research/.ranked/mongodb-local-20261024/plan.json
```

Stele transport closed during the selection-completion and launch-claim calls. Selection TASK-906 was claimed, but its completion and TASK-907 claim require reconciliation when transport recovers.

## Delivery and tracking

Documentation privacy and diff checks passed. Initial tracking commit: 72c9e553. Draft PR: https://github.com/mithudso/llms-explorer/pull/231
Keep the PR draft while research is active. Commit only reviewed authored outputs after successful claim gates and native completion. Never stage private source bodies or raw logs.

Disk task state: selection complete, launch complete, startup verification complete; research TASK-904 remains in progress. Stele TASK-906 completion, TASK-907 claim/completion and TASK-908 claim/completion remain to reconcile after its closed transport recovers. Do not treat graph bookkeeping as a research blocker.
