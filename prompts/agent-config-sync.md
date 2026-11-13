# Mounted-home agent configuration sync prompt

- Version: 1.3.0
- Delta: 1.2.0 to 1.3.0; record verified SSH transport, completed primary staged merge, and active remote application.
- Updated: 2026-11-13
- Status: IN_PROGRESS
- Tracking: Configuration sync task `TASK-1465`; active copy stage `TASK-1468`.
- Repository record: `/Users/mitch.hudson/dev/llms-explorer/prompts/agent-config-sync.md`.

## Original user prompt

```text
Perform a two way sync with the system mounted on /Volumes/mitch/  and sync all of the skills, rules, hooks, plugins, mcp servers, don't delete anything, just whichever has latest change date wins.
```

## Execution scope

Synchronize agent definitions and their necessary supporting assets between the
primary home `/Users/mitch.hudson` and the mounted home `/Volumes/mitch`.
Preserve files found on only one side. Select the newer definition by
modification date when the same item differs. Record an explicit deterministic
tie decision and preserve both original versions when
there is no newer timestamp.

Merge named configuration entries so each system retains its unique skills,
rules, hooks, plugins, and MCP servers. Keep a conflicting MCP server definition
whole; mixing an older command with newer arguments or environment values can
produce an invalid server. Identify hooks by their target and binding so a newer
command replaces an older definition of that hook.

Translate local home paths for each destination. The mount location and SMB
display name are not Unix account identity. Use the canonical native home
verified through the trusted, non-root SSH session for remote commands.
Keep SSH remote command paths unchanged. Preserve each system's authentication,
account, session, database, lock, and runtime state. Preserve host-specific hook
trust and existing source files. Back up every overwritten node privately.

Keep generated crawler data, operational logs, and unrelated research bodies
outside this configuration sync. Copy the relevant skill instructions and
supporting code. Do not execute copied hooks or force active applications to
reload as part of synchronization.

## Continuation record

Use the [versioned sync memory](../docs/operations/agent-config-sync-memory.md)
for the current stage, aggregate evidence, remaining work, and delivery status.
The memory record is a checkpoint until final verification and delivery finish.
Private configuration contents, authentication values, raw artifacts, and helper
execution receipts remain outside this repository.

## Current execution state

Transport moved to trusted SSH. Strict host-key verification matched the pinned
key exactly to known-host evidence. The parent agent verified the canonical
native home and a non-root SSH session. The SMB display name is separate from
the canonical Unix account. No authentication input request is pending.

Primary host-local staged CAS merge phase 100 completed with exit code 0:
189,363 operations, 78,976 verified writes, zero errors, and 1,531,663,977 logical
bytes. Those writes comprise 75,305 actual primary asset writes and 3,671 writes
to the staging outgoing delta. These are phase-local results, not final global
sync totals. A fresh primary census completed with 226,667 nodes and 182,389 file
hashes, with zero errors.

The SSH snapshot verified 185,279 files, approximately 3.5 GB. It initially
identified 4,084 files missing remotely and observed 640 initially cached paths
absent on both sides during external plugin-updater activity. This sync does
not claim to have deleted or restored those superseded cache paths. The outgoing
3,671-file delta, approximately 54 MB, was staged remotely and verified as 3,672
entries including metadata.

Remote apply phase 102 is running at this checkpoint. Attempt 101 timed out
while connecting and did not run the apply. A bounded one-hour sleep assertion
was started. Source backups remain retained, and no original user data was
deleted by this sync. APFS copy-on-write staging has ten fixture checks for
independent content, source ctime preservation, and safe fallback on low disk.

The current private suite has 169 passing checks with exit code 0. No structured
configuration merges have been applied. Fresh cross-host digest comparison,
new cache-path reconciliation, residual sync, configuration merges, native CLI
verification, and final repository delivery remain outstanding. The helper
implementation and detailed configuration data remain outside Git.
