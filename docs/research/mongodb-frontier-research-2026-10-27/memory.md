# MongoDB research continuation

Version: 1.4.0
Delta: 1.3.0 to 1.4.0; independent launch verification, continuing task, and publication blocker.
Status: expansion verified; research running; preview credential repair required before merge.

## Completed

- Added 21 pending topics across 13 existing parents in both trees. Stored 26 CVS rows, including five covered skips. No researched nodes were created.
- Independent planning audit passed 68 reads and 235 exact spans. Native preservation checks passed for node metadata, queue prefixes, and 254 historical files. Scratch idempotence changed zero bytes.
- Passed 23 runner/checkpoint tests, two llmsx frontier tests, 56 hub tree tests, 25 site generator tests, and 23 built tree page tests: 129 total. The site build and publication policy passed. Initial checks exposed missing declared dependencies and an absent site/dist; isolated dependency setup and the build resolved them. Validation retains those attempts.
- Created a native plan with all 54 eligible topics in 29 cohorts. Launched controller PID 25579 at 2026-10-27T16:59:20Z, using four Sol/medium workers. The first cohort is ranked-40fb1cf4. Independent verification observed actual source activity and substantive cached bodies, with no premature promotion.

## Current ownership and paths

TASK-944 tracks expansion/initiation. Inventory TASK-945 and expansion TASK-946 are complete. Delivery TASK-947 remains active. TASK-950 owns the continuing full queue. KNOW-948 preserves the independent local-plan boundary.

Publication checkout: /Users/mitch/dev/worktrees/llms-explorer-mongodb-research-20261027, branch research/mongodb-frontier-20261027.
Active runtime checkout: /Users/mitch/dev/worktrees/llms-explorer-mongodb-queue-20261027, branch research/mongodb-queue-live-20261027. Keep it while the runner is active.
Plan: /Users/mitch/.global-ai-hub/research/.ranked/mongodb-local-20261027/plan.json
Launch receipt: /Users/mitch/.global-ai-hub/research/.ranked/mongodb-local-20261027/launch.json
Live continuation: /Users/mitch/.global-ai-hub/research/.ranked/mongodb-local-20261027/memory.md
Private discovery and guarded receipts: /Users/mitch/.global-ai-hub/research/.frontier/mongodb-20261027/

## Preserved boundaries

The completed October 24 local plan and unavailable October 22 remote plan retain their identities. Remote overlap is unknown. Preserve all old reservations, unrelated dirty work, other worktrees, and the divergent original /Users/mitch/dev/llms-explorer main. Embeddings, indexing services, and Ollama remain paused. Source-library reuse and native keyword publication follow the research contract.

The batch marker reserves exactly 54 topic names. The native DR holder additionally displays the existing parent, MongoDB Security Architecture. Its combined display therefore contains 55 labels; actual assignments remain 54. A started runner does not make the queue complete. Bound gates and both-tree/pack/site persistence are still required for each result. Substantive dissent stays withheld while independent cohorts continue.

## Read or resume

```sh
/Users/mitch/dev/worktrees/llms-explorer-mongodb-queue-20261027/llmsx/.venv/bin/python /Users/mitch/dev/worktrees/llms-explorer-mongodb-queue-20261027/scripts/codex_ranked_research.py status --repo /Users/mitch/dev/worktrees/llms-explorer-mongodb-queue-20261027 --hub /Users/mitch/.global-ai-hub --plan /Users/mitch/.global-ai-hub/research/.ranked/mongodb-local-20261027/plan.json
```

If no runner remains alive, use the same command with `run` instead of `status` and append `--continue-on-review`. Native .runner.lock rejects duplicate owners. Never rebuild the saved plan or repeat completed discovery. Inspect existing dissent before retrying unchanged claims.

## Remaining delivery

PR 243 is committed, pushed, and deliberately kept as a draft. Cloudflare preview fails in hub/bootstrap.sh cloning the private ollama-client repository: `remote: Invalid username or token. Password authentication is not supported for Git operations.` The existing Preview LIBS_READ_TOKEN needs user replacement. Do not reuse a broad GitHub OAuth token or bypass failing CI. The signed-in Chrome Beta tab is already on the preview settings.

https://github.com/mithudso/llms-explorer/pull/243
https://dash.cloudflare.com/b41ba4dc457dce7653c93af955ecc462/pages/view/llms-explorer/settings/preview

After the user refreshes the secret, retry only this preview deployment, wait for every check to pass, mark PR 243 ready, and squash-merge it. Remove only the clean publication worktree and its merged branch. Preserve the active runtime worktree and ongoing results. Resume publication of those results through a separate review branch once their gates pass.

Root and the earlier writer lost Stele transport. A fresh graph writer is reconciling TASK-950 links and the fact-level novelty lesson. The same Cloudflare credential failure already exists as KNOW-938 from PR 242. Do not duplicate it.
