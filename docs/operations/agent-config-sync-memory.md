# Mounted-home agent configuration sync memory

- Version: 1.1.0
- Delta: 1.0.0 to 1.1.0; record interrupted copy evidence, mount authentication failures, and guarded continuation.
- Updated: 2026-11-13
- Status: INCOMPLETE_AUTH_BLOCKED
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
attempts were not fully journaled and may have applied additional writes. A
fresh comparison after remounting is required to establish the actual state.
The directory/link counts describe completed topology checks, not exact counts
of created directories or links. Topology counts and fixture results do not
establish synchronized file content.

No structured configuration merges have been applied. Final residual-copy,
protected-state, and native-discovery verification remain outstanding.

New mount/device identity guards and nonzero failure exits were implemented in
the private driver. Topology execution now journals every outcome and stops
scheduling after `MountUnavailable`. The parent agent fixed receipt-directory
handling and confirmed that the current 73-case suite passes with exit code 0.
An independent guard review is still active; findings may require additional
checks. This passing fixture result does not establish a successfully mounted
target or completed synchronization.

## Authentication blocker

The SMB filesystem disconnected twice. A saved Finder reconnect succeeded
temporarily, then the mount disappeared again. The direct `mount_smbfs -N`
attempt returned 77 for authentication failure. An SSH fallback returned 255
because host-key verification was unavailable. The public record retains only
these outcomes, not the server values, saved URL, or authentication material.

An asynchronous request for Finder authentication is pending. No user reply is
recorded at this checkpoint. A directory named `/Volumes/mitch` is not sufficient
proof of the intended mount. Verify the mounted filesystem and device identity
before any further target writes. Do not work around authentication or SSH
host-key checks.

## Tracking state

| Task | Responsibility | Checkpoint state |
| --- | --- | --- |
| `TASK-1465` | Complete mounted-home agent configuration sync | Open; parent is not claimed |
| `TASK-1467` | Inventory and sync planning | Done |
| `TASK-1468` | Definition asset copy | Claimed; incomplete and waiting for authenticated remount |
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

1. Complete Finder authentication, then verify that the intended filesystem and
   expected device are mounted at `/Volumes/mitch`.
2. Finish the independent mount-guard review. If it produces changes, rerun the
   complete current suite and record the actual result.
3. Re-inventory both sides after remounting. Compare current source/destination
   metadata and content against the private receipts. Do not infer copy success
   from earlier planned operations or reuse an unchecked stale plan.
4. Finish recoverable residual copying with original-byte backups, timestamp
   precedence, mount guards, and concurrent-edit checks. Establish complete
   accounting that includes the unjournaled earlier attempts.
5. Apply and verify the structured configuration merges with each destination's
   native paths and host-specific state intact.
6. Verify referenced assets, protected-state preservation, final inventory
   accounting, and fresh native discovery where the runtime is available.
7. Update both versioned records with the final evidence, incrementing their
   versions and Delta fields. Keep them truthfully incomplete until the required
   work is verified.
8. Update the draft PR with the final scope and evidence, wait for final checks,
   merge, verify the remote default branch content, and clean only the
   task-owned merged worktree and branch. The parent agent owns delivery and
   tracker completion.

## Delivery state

The recoverable checkpoint is on `codex/agent-config-sync-1465` in draft
[PR #363](https://github.com/mithudso/llms-explorer/pull/363). Synchronization is
incomplete and authentication-blocked. No merge or tracker completion is
claimed. Keep the PR draft until the remaining synchronization, validation,
and delivery requirements are satisfied.
