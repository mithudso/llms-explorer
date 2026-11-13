# Mounted-home agent configuration sync prompt

- Version: 1.1.0
- Delta: 1.0.0 to 1.1.0; record interrupted copying and authentication-blocked continuation.
- Updated: 2026-11-13
- Status: INCOMPLETE_AUTH_BLOCKED
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

Translate local home paths for each destination. The mount location is an access
path, while the mounted machine uses `/Users/mitch` when it executes commands.
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

Synchronization is incomplete. The SMB mount disconnected twice. A saved Finder
reconnect worked temporarily, then the mount disappeared again. A direct
`mount_smbfs -N` attempt returned 77 with an authentication failure. The SSH
fallback returned 255 because host-key verification was unavailable. Connection
URLs, host values, and credentials remain private.

The Finder authentication request is pending; no user reply is recorded at this
checkpoint. No structured configuration merges have been applied. Resume only
after verifying the intended filesystem is mounted at `/Volumes/mitch` and its
device identity matches the target. A directory at that path alone is not proof
of a mounted filesystem. Inspect private receipts and reread current file state
before retrying interrupted operations.
