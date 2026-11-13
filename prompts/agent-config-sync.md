# Mounted-home agent configuration sync prompt

- Version: 1.5.0
- Delta: 1.4.0 to 1.5.0; record accepted content/configuration/native verification, corrected accounting, metadata boundaries, and delivery through PR 363.
- Updated: 2026-11-13
- Status: VERIFICATION_COMPLETE
- Tracking: Configuration sync task `TASK-1465`; the parent owns lifecycle transitions and final delivery.
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

Use `/Users/mitch.hudson/dev/llms-explorer/docs/operations/agent-config-sync-memory.md`
for the current stage, aggregate evidence, remaining work, and delivery status.
The memory record is a checkpoint until final verification and delivery finish.
Private configuration contents, authentication values, raw artifacts, and helper
execution receipts remain outside this repository.

## Current execution state

Transport moved to trusted SSH. Strict host-key verification matched the pinned
key exactly to known-host evidence. The parent agent verified the canonical
native home and a non-root SSH session. The SMB display name is separate from
the canonical Unix account. No authentication input request is pending.

The initial remote apply is no longer running. Primary phase 100, remote phase
103, remote residual phase 112, and single-file retry 113 completed. Residual
phase 110 recorded one disappearing-parent failure before that retry succeeded.
Their phase-local counts are in the continuation record. Earlier unjournaled
attempts prevent an exact historical overall-write claim. Source backups remain
retained, and this sync has not deleted original user data.

Structured configuration merges have been applied. The final normalized
comparison covers 36 files with zero pending differences and zero issues. There
are 53 verified configuration writes: 47 in the initial round and six in the
follow-up round. Actual destination counts are 29 primary and 24 remote.

Native discovery verified the same 50 MCP names on both hosts. Authenticated
metadata acceptance passed on both hosts with protocol `2025-11-25`: five skills
tools and 40 research-library tools. No tools were called and no corpus queries,
models, or embeddings ran. A temporary-probe rejection was resolved by giving
that probe its descriptive application User-Agent. Native definitions, auth,
accounts, TLS validation, and edge policies were unchanged.

Both native Codex catalogs list 205 entries. Claude portable registries have
identical sets of 91 keys. All 16 additional primary managed synced-scope plugin
directories and manifests also exist remotely. Their optional remote activation
requires the native claude.ai login; account identity was not transferred.

Final comparison 5 and its export passed with 235,742 paths examined and zero
canonical body mismatches, one-sided entries, unresolved entries, proof errors,
input errors, or remaining required probes. The final fixture suite completed:
250 checks passed with exit code zero. All six native authentication files with
available baselines remained unchanged.

These proofs combine native baselines with fresh logical overlays and targeted
native probes. They do not assert simultaneous fresh reads of every live file.
Existing permissions were retained when canonical content already matched.
There are 62,818 metadata-difference rows, including 405 reviewed mode differences
on identical content. Do not claim raw byte-size, mode, or modification-time
identity across native homes.

Synchronization verification is complete. These records are prepared through
https://github.com/mithudso/llms-explorer/pull/363

As of this commit, repository delivery is pending. Actual final checks, merge,
and delivery receipts are recorded in GitHub and the private run directory;
they do not require a later narrative-only record commit. Private helper code,
configuration data, and raw diagnostics remain outside Git.
