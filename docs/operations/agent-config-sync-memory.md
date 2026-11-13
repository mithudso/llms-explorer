# Mounted-home agent configuration sync memory

- Version: 1.0.0
- Delta: Initial recoverable execution checkpoint.
- Updated: 2026-11-13
- Status: IN_PROGRESS
- Repository record: `/Users/mitch.hudson/dev/llms-explorer/docs/operations/agent-config-sync-memory.md`.

## Assignment

The user requested a two-way sync of skills, rules, hooks, plugins, and MCP
servers between `/Users/mitch.hudson` and `/Volumes/mitch`. The mounted machine
uses `/Users/mitch` as its native runtime home. Files present on only one side
must survive. Modification date selects the winner for conflicting definitions. The exact
commissioned text is in the [prompt record](../../prompts/agent-config-sync.md).

This record covers agent configuration and necessary supporting assets. It does
not authorize research execution, copying account/session databases, or forcing
active applications to reload.

## Scope and safeguards

The source inventory spans the discovered agent harnesses, their skill and
plugin packages, rules, hook definitions, MCP configuration, and referenced
portable backing assets. Symlink reads map the mounted system's native home
through its mount. Copied local command paths use each destination's native
home. SSH command arguments after the remote hostname retain their remote
meaning.

The executor preserves authentication, account, session, database, active-lock,
and runtime state. It keeps host-specific hook trust local. It backs up nodes
before overwriting them and checks for concurrent changes before writes. It
retains one-sided files and merges unique named configuration entries. A newer
MCP definition remains atomic. Target-aware hook identity prevents an older
command variant from becoming a second active definition of the same hook.

Generated crawler data and operational caches are excluded from the definition
sync. Skill instructions and functional supporting assets remain in scope.
Private configuration values and research bodies are not repository artifacts.

## Checkpoint evidence

The parent agent reported these aggregate counts for this checkpoint:

| Measure | Checkpoint result |
| --- | ---: |
| Primary inventory nodes | 86,344 |
| Mounted inventory nodes | 203,124 |
| Directory topology operations completed | 33,769 |
| Link topology operations completed | 1,914 |
| File comparisons in the active pass | 189,363 |
| Passing fixture checks | 66 |

Topology completion does not establish complete file synchronization. The file
comparison/copy pass is running. Configuration application, final residual-copy
verification, and native discovery checks remain outstanding. These numbers
must not be presented as a completed-sync receipt.

The fixture checks cover merge behavior, home-path mapping, SSH remote paths,
mtime precedence, original-byte backups, concurrent-write rejection, and
preservation of machine-local state. Final verification must use the actual
post-sync inventories and receipts.

## Tracking state

| Task | Responsibility | Checkpoint state |
| --- | --- | --- |
| `TASK-1465` | Complete mounted-home agent configuration sync | In progress |
| `TASK-1467` | Inventory and sync planning | Done |
| `TASK-1468` | Definition asset copy | Claimed; copy/comparison pass active |
| `TASK-1469` | Structured configuration merge | Pending |
| `TASK-1470` | Installed parity verification and record delivery | Pending; root will claim after copy and configuration stages |

## Private continuation material

Detailed inventories, copy plans, backups, helper code, configuration snapshots,
and verification receipts remain in the operator-only run directory:

```text
/Users/mitch.hudson/.local/share/agent-config-sync/20261113-1520/
```

Inspect that run's current receipts before resuming. Recheck current source and
destination metadata; a saved copy plan does not authorize overwriting a later
concurrent edit. Keep raw configuration values, tokens, account identifiers,
private artifact bodies, and helper execution logs out of Git and PR messages.

## Remaining work

1. Finish the active file comparison/copy pass and inspect its complete receipt.
2. Reconcile recoverable residual differences while preserving backups and
   concurrent edits.
3. Apply and verify the structured configuration merges with the destination's
   native paths and host-specific state intact.
4. Verify referenced assets, protected-state preservation, final inventory
   accounting, and fresh native discovery where the runtime is available.
5. Update this memory and the prompt record with the final outcome. Increment
   their versions and Delta fields when those outcomes are recorded.
6. Run the repository checks required for these records, publish the final PR
   scope and evidence, wait for final checks, merge, verify the remote default
   branch content, and clean only the task-owned merged worktree and branch.

## Delivery state

A recoverable checkpoint is being prepared on `codex/agent-config-sync-1465`.
Its PR must remain a draft while synchronization and verification are active.
The record will gain the actual PR URL, final merge identity, final aggregate
results, and any remaining limits after the parent agent provides them.
