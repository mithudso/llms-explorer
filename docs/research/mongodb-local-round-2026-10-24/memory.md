# Local MongoDB round continuation

Version: 1.4.0
Delta: 1.3.0 to 1.4.0; all 62 claims supported; native exports and local round completion succeeded.
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

## Verification repair

The initial runner stopped at 2026-10-25T03:52:18Z. All four concepts completed research (62 canonical claims, 91 source ledger records). The first gate selected 40 claims: 37 SUPPORTED and 3 UNVERIFIED. Native export and local publication had not run.

The user requested: Verify the 3 unverified. A read-only research-contract-auditor independently fetched all three missing cited pages. The Frogred8 article contains the two printed projection plans. The two Stack Overflow pages contain the historical elemMatch FETCH explanation and MongoDB 3.6.0 hint reproduction.

Recovered Frogred8 text through the web reader, because direct HTTP returned 403. Recovered both Stack Overflow questions and answers from the official Stack Exchange API, preserving the raw API responses privately. Stored each recovered body through the native source-put command. Canonical source URLs remain unchanged.

Changed two canonical multikey claims: attribute the array-versus-scalar explanation to the historical answer, and describe multiKeyPaths as an object containing an empty array for address.zipcode. Preserved both original claims documents under /Users/mitch/.global-ai-hub/research/ranked-17bfb8f4/repairs/three-unverified-20261025/. Did not edit prior gate receipts. The canonical helper accepted the corrected 19-claim multikey document.

A fresh native bound gate is running with --sample all, covering all 62 canonical claims. Inspect the new manifest gate receipt before native completion or publication.

Stele transport recovered. TASK-907 is complete and TASK-908 is claimed for this verification. TASK-906 status still needs reconciliation.

## Verified resolution

The fresh native gate completed at 2026-10-25T04:07:03Z: validated research-gate/v2, all 62 claims selected, all 62 SUPPORTED. Packet SHA-256: 038a7bf52a63aabede8a72bbbaa1ff3f0172f8e40e2e2e766004b1b1435d9d1a. The independent auditor reran the canonical validator (exit 0), checked inclusion of the three exact target statements, and matched all five target evidence spans and hashes.

The unchanged projection claim ID begins 77e00a8c. Corrected historical elemMatch claim ID begins 327dc898. Corrected historical non-multikey claim ID begins 18734439. The earlier failed attempt remains intact.

The first export attempt failed with ModuleNotFoundError: No module named 'llms_txt' under system Python. Reran the native ranked runner with uv run --directory llmsx, which installed the declared dependency into this worktree's environment. No implementation change or new research call was needed.

The plan and cohort now report complete; manifest reports finalized. Native receipt contains eight packs (four concepts in each target), all 64 pack members present, and both tree targets. Native completion also regenerated local website content and marked the four queue entries complete. Existing eligible hub research was refreshed through the standard shared completion hook. Embeddings remain paused.

Tracking reconciled: TASK-906 and TASK-907 are done. TASK-908 remains active until verification records are committed. TASK-904 remains active until delivery checks pass.

Remaining delivery: finish scoped generation/privacy checks, commit approved public artifacts and tracking records, push PR 231, wait for CI and merge. Keep private gate attempts, API bodies and source-library data outside Git.

Validation: 65 focused concept/tree/facts/privacy tests passed. Native research_site_sync --check passed with zero changed files.
