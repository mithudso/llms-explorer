# Mounted-home agent configuration sync memory

- Version: 1.3.0
- Delta: 1.2.0 to 1.3.0; record strict SSH verification, completed primary staged merge and census, and active remote application.
- Updated: 2026-11-13
- Status: IN_PROGRESS
- Repository record: `/Users/mitch.hudson/dev/llms-explorer/docs/operations/agent-config-sync-memory.md`.

## Assignment

The user requested a two-way sync of skills, rules, hooks, plugins, and MCP
servers between `/Users/mitch.hudson` and the system originally accessed through
`/Volumes/mitch`. Transport now uses trusted SSH. The canonical Unix account and
native home were verified through the non-root SSH session, rather than inferred
from the SMB display name or mount label. Files present on only one side must
survive. Modification date selects the winner for conflicting definitions.
The exact commissioned text is in the [prompt record](../../prompts/agent-config-sync.md).

This record covers agent configuration and necessary supporting assets. It does
not authorize research execution, copying account/session databases, or forcing
active applications to reload.

## Scope and safeguards

The source inventory spans the discovered agent harnesses, their skill and
plugin packages, rules, hook definitions, MCP configuration, and referenced
portable backing assets. Copied local command paths use each destination's
verified native home. The original mount path and SMB display name do not select
a Unix account. SSH command arguments after the remote hostname retain their
remote meaning.

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
attempts were not fully journaled and may have applied additional writes. Later
guarded passes and the final cross-host comparison are required to establish
the actual state.
The directory/link counts describe completed topology checks, not exact counts
of created directories or links. Topology counts and fixture results do not
establish synchronized file content.

No structured configuration merges have been applied. Final residual-copy,
protected-state, and native-discovery verification remain outstanding.

## Trusted SSH recovery

The user confirmed Finder authentication, and the parent agent verified the SMB
mount, read probe, native home, and distinct device identity. Transport later
moved to trusted SSH. Strict verification matched the pinned host key exactly
to known-host evidence. The canonical native home and non-root SSH session were
verified. The SMB display name is separate from the canonical Unix account.
No authentication input request remains pending at this checkpoint.

## Completed primary phase 100

The full primary host-local staged CAS merge completed with exit code 0:

| Measure | Phase-100 result |
| --- | ---: |
| Operations | 189,363 |
| Verified writes | 78,976 |
| Actual primary asset writes within that count | 75,305 |
| Outgoing staging-delta writes within that count | 3,671 |
| Errors | 0 |
| Logical bytes | 1,531,663,977 |

These are bounded phase-local results. They are not final global two-way totals,
and staging writes are not remote installation writes. Earlier unjournaled
attempts still prevent an exact historical overall-write claim.

APFS copy-on-write staging is covered by ten fixture checks proving content
independence, preservation of source ctime, and safe fallback when low disk
prevents cloning. Logical bytes do not assert equal physical disk allocation.
Source backups remain retained. This sync has not deleted original user data.

A fresh complete primary census reported 226,667 nodes and 182,389 file hashes,
with zero errors. It establishes that primary snapshot's accounting; it does
not establish cross-host parity or native-client activation.

## Remote snapshot and active phase 102

The verified SSH snapshot contains 185,279 files, approximately 3.5 GB. The
initial comparison identified 4,084 files missing remotely. It also observed
640 initially inventoried cache paths absent on both sides during active
external plugin-updater activity. Those superseded-cache observations are not
deletions or restorations performed by this sync.

The outgoing delta contains 3,671 files, approximately 54 MB. Remote staging was
verified as 3,672 entries including metadata. This staging result does not prove
that all entries have been applied to the remote live paths.

Remote apply phase 102 is running at this checkpoint. Attempt 101 timed out
while connecting and did not execute an apply. A bounded one-hour sleep
assertion was started to support the operation. Final remote apply, digest
comparison, residual reconciliation, and configuration application are not yet
reported complete.

## Guard and test checkpoint

The private implementation uses directory file descriptors for directory and
temporary-file creation, replacement, and temporary-file cleanup. Parent
traversal avoids following symlinks and checks device/inode identity. Topology
execution journals every outcome and stops scheduling after `MountUnavailable`.
All submitted batch results are drained. Configuration processing retains a
sticky abort, outcome journal, and nonzero failure exits.

The parent agent confirmed that the current private 169-case fixture suite
passes with exit code 0. The ten copy-on-write checks are part of the validation
scope. Passing fixtures do not replace fresh cross-host digest comparison or
native runtime verification. No structured configuration merges have been
applied. Private helper source code remains outside Git.

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
| `TASK-1468` | Definition asset copy | Claimed; primary phase complete, remote phase 102 active |
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

1. Finish remote apply phase 102 and inspect its complete outcome journal.
   Preserve the verified SSH identity and retained source backups.
2. Run a fresh cross-host digest comparison. Reconcile new cache paths and other
   recoverable residual differences against current source/destination state.
   Preserve honest accounting for external updater activity and the earlier
   unjournaled attempts.
3. Apply and verify the structured configuration merges with each destination's
   verified native home, whole MCP definitions, target-aware hook identities,
   and host-specific account/runtime state intact.
4. Complete protected-state, referenced-asset, final inventory, and native CLI
   verification. Rerun affected checks when fixes or new failures justify it.
5. Update both versioned records with the final evidence, incrementing their
   versions and Delta fields. Keep the result incomplete until the required
   synchronization and verification finish.
6. Update the draft PR with the final scope and evidence, wait for final checks,
   merge, verify the remote default branch content, and clean only the
   task-owned merged worktree and branch. The parent agent owns delivery and
   tracker completion.

## Delivery state

The recoverable checkpoint is on `codex/agent-config-sync-1465` in draft
[PR #363](https://github.com/mithudso/llms-explorer/pull/363). Strict SSH
verification and the primary staged merge are complete; remote apply is active.
The task is not done. Configuration merges and final cross-host/native checks
remain outstanding. No merge or tracker completion is claimed. Keep the PR
draft until the remaining synchronization, validation, and delivery requirements
are satisfied.
