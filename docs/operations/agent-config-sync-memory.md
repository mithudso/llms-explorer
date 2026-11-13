# Mounted-home agent configuration sync memory

- Version: 1.2.0
- Delta: 1.1.0 to 1.2.0; record authenticated recovery, guarded round-three progress, and the current fixture checkpoint.
- Updated: 2026-11-13
- Status: IN_PROGRESS
- Repository record: `/Users/mitch.hudson/dev/llms-explorer/docs/operations/agent-config-sync-memory.md`.

## Assignment

The user requested a two-way sync of skills, rules, hooks, plugins, and MCP
servers between `/Users/mitch.hudson` and `/Volumes/mitch`. The mounted machine
uses `/Users/mitch` as its native runtime home. Files present on only one side
must survive. Modification date selects the winner for conflicting definitions.
The exact commissioned text is in the [prompt record](../../prompts/agent-config-sync.md).

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

The earlier inventory and topology checkpoint had these parent-reported counts:

| Measure | Earlier checkpoint result |
| --- | ---: |
| Primary inventory nodes | 86,344 |
| Mounted inventory nodes | 203,124 |
| Directory topology checks completed | 33,769 |
| Link topology checks completed | 1,914 |
| File comparisons in the planned pass | 189,363 |
| Fixture checks passing at the earlier checkpoint | 66 |

The interrupted round-two receipt has these results:

| Measure | Round-two receipt |
| --- | ---: |
| Verified writes | 80 |
| Verified bytes | 36,446,330 |
| TimeoutError outcomes | 184,271 |

Round two did not complete successfully. The 80 verified writes are the writes
recorded in that receipt, not an exact total for the overall sync. Earlier copy
attempts were not fully journaled and may have applied additional writes. The guarded pass after authenticated remounting is active; its final
comparison is still required to establish the actual state.
The directory/link counts describe completed topology checks, not exact counts
of created directories or links. Topology counts and fixture results do not
establish synchronized file content.

No structured configuration merges have been applied. Final residual-copy,
protected-state, and native-discovery verification remain outstanding.

## Authenticated recovery and active round three

The user confirmed Finder authentication. The parent agent verified the SMB
mount, successful read probe, native home, and distinct device identity. The
previous authentication blocker is resolved at this checkpoint. Mount identity
must continue to be checked before target writes; the existence of the path
`/Volumes/mitch` alone is insufficient.

The guarded round-three copy pass is active with a complete per-outcome journal.
The parent-reported progress snapshot was:

| Measure | Active snapshot; not a final receipt |
| --- | --- |
| Checks observed | Approximately 20,500 of 189,363 planned |
| Verified writes observed | 2,374 at the reported snapshot |
| Errors observed | None at the reported snapshot |

These progress observations are approximate. They do not establish final write
counts, total copied bytes, complete parity, or a successful full sync. The
private journal and final verification receipts must establish those outcomes.
Earlier unjournaled attempts still prevent an exact historical overall-write
claim.

The private implementation now uses file-descriptor-anchored directory creation,
temporary-file creation, replacement, and temporary-file cleanup. Parent
traversal avoids following symlinks and checks device/inode identity. Topology
execution journals every outcome and stops scheduling after `MountUnavailable`.
All submitted batch results are drained. Configuration processing retains a
sticky abort, outcome journal, and nonzero failure exits.

The parent agent confirmed that the completed 92-case fixture suite passes with
exit code 0, including 12 finalized inventory tests. Verifier work remains
active, so this is the current passing checkpoint rather than a final test
claim. No structured configuration merges have been applied. Private helper
source code remains outside Git.

## Earlier connection failures

Before authenticated recovery, the SMB filesystem disconnected twice. A saved
Finder reconnect succeeded temporarily, then the mount disappeared. The direct
`mount_smbfs -N` attempt returned 77 for authentication failure. An SSH fallback
returned 255 because host-key verification was unavailable. These are historical
connection outcomes; they no longer describe the current authentication state.
The public record excludes server values, the saved URL, and authentication
material. Authentication and SSH host-key checks were not bypassed.

## Tracking state

| Task | Responsibility | Checkpoint state |
| --- | --- | --- |
| `TASK-1465` | Complete mounted-home agent configuration sync | Open; parent is not claimed |
| `TASK-1467` | Inventory and sync planning | Done |
| `TASK-1468` | Definition asset copy | Claimed; guarded round-three copy pass active |
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

1. Finish the guarded round-three copy pass and inspect its complete outcome
   journal. Reverify the intended filesystem and device at `/Volumes/mitch`
   before further target writes.
2. Finish the active verifier work and independent review. If they produce
   changes, rerun the relevant current suite and record the actual result.
3. Complete the post-remount inventory comparison. Recheck source/destination
   metadata and content against the private receipts; an earlier planned
   operation is not proof of a completed copy.
4. Reconcile recoverable residual differences with original-byte backups,
   timestamp precedence, mount guards, and concurrent-edit checks. Retain honest
   accounting for the earlier unjournaled attempts.
5. Apply and verify the structured configuration merges with each destination's
   native paths and host-specific state intact.
6. Verify referenced assets, protected-state preservation, final inventory
   accounting, and fresh native discovery where the runtime is available.
7. Update both versioned records with the final evidence, incrementing their
   versions and Delta fields. Keep the result incomplete until the required
   synchronization and verification finish.
8. Update the draft PR with the final scope and evidence, wait for final checks,
   merge, verify the remote default branch content, and clean only the
   task-owned merged worktree and branch. The parent agent owns delivery and
   tracker completion.

## Delivery state

The recoverable checkpoint is on `codex/agent-config-sync-1465` in draft
[PR #363](https://github.com/mithudso/llms-explorer/pull/363). Authentication has
recovered and guarded copying is in progress. Synchronization and configuration
application are not complete. No merge or tracker completion is claimed. Keep
the PR draft until the remaining synchronization, validation, and delivery
requirements are satisfied.
