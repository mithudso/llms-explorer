# Mounted-home agent configuration sync memory

- Version: 1.5.0
- Delta: 1.4.0 to 1.5.0; record accepted final content/configuration/native gates, corrected accounting, metadata limits, and PR delivery tracking.
- Updated: 2026-11-13
- Status: VERIFICATION_COMPLETE
- Repository record: `/Users/mitch.hudson/dev/llms-explorer/docs/operations/agent-config-sync-memory.md`.

## Assignment

The user requested a two-way sync of skills, rules, hooks, plugins, and MCP
servers between `/Users/mitch.hudson` and the system originally accessed through
`/Volumes/mitch`. Transport now uses trusted SSH. The canonical Unix account and
native home were verified through the non-root SSH session, rather than inferred
from the SMB display name or mount label. Files present on only one side must
survive. Modification date selects the winner for conflicting definitions.
The exact commissioned text is in
`/Users/mitch.hudson/dev/llms-explorer/prompts/agent-config-sync.md`.

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

Asset application, structured configuration merges, final native proof
classification, and full-suite verification are complete. Repository delivery
is tracked separately through PR 363 and the private delivery receipt.

## Trusted SSH recovery

The user confirmed Finder authentication, and the parent agent verified the SMB
mount, read probe, native home, and distinct device identity. Transport later
moved to trusted SSH. Strict verification matched the pinned host key exactly
to known-host evidence. The canonical native home and non-root SSH session were
verified. The SMB display name is separate from the canonical Unix account.
No authentication input request remains pending at this checkpoint.

## Completed primary phase 100

The full primary host-local staged merge completed with exit code 0:

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

## Remote snapshot and completed asset rounds

The verified SSH snapshot contains 185,279 files, approximately 3.5 GB. The
initial comparison identified 4,084 files missing remotely. It also observed
640 initially inventoried cache paths absent on both sides during active
external plugin-updater activity. Those superseded-cache observations are not
deletions or restorations performed by this sync.

The outgoing delta contains 3,671 files, approximately 54 MB. Remote staging was
verified as 3,672 entries including metadata. This staging result does not prove
that all entries have been applied to the remote live paths.

Attempt 101 timed out while connecting and did not execute an apply. The initial
remote application is no longer running. Later completed receipts report:

| Phase | Completed result |
| --- | --- |
| Remote 103 | Exit 0; 3,671 actual remote writes; 54,022,536 bytes; zero errors; zero backflow |
| Residual client 110 | Exit 2; 506 verified writes: 378 actual primary assets plus 128 outgoing-stage writes; one disappearing-parent error |
| Single-file retry 113 | Exit 0; one actual primary write; 15,752 bytes |
| Remote residual 112 | Exit 0; 128 actual remote writes; 9,138,813 bytes; zero errors |

These are phase-local counts. Staging writes are separate from live asset writes.
Do not add completed, interrupted, and earlier unjournaled attempts into an
asserted overall historical total.

Native directory creation checked 106 primary paths and created one new
component. It checked 376 remote paths and created 15 new components. These
creation counts are distinct from earlier directory/link topology-check counts.
A fresh remote native census completed with 234,068 nodes, 188,754 file hashes,
and zero errors.

For historical accounting, guarded round three exited 3 with 6,358 verified
writes, 105,785,818 bytes, 128 mount failures, and one `NotADirectoryError`.
Interrupted round four exited 130 with 66,180 drained outcomes, 39,225 verified
writes, 429,878,519 bytes, zero journal errors, and 144 submitted paths whose
interrupted outcome remained uncertain. Round two was unsuccessful despite a
former exit-code bug returning zero. Later guards corrected failure exits.

## Guard and test checkpoint

The private implementation uses directory file descriptors for directory and
temporary-file creation, replacement, and temporary-file cleanup. Parent
traversal avoids following symlinks and checks device/inode identity. Topology
execution journals every outcome and stops scheduling after `MountUnavailable`.
All submitted batch results are drained. Configuration processing retains a
sticky abort, outcome journal, and nonzero failure exits.

The final private fixture suite completed with 250 passing checks and exit code
zero. Earlier checkpoint counts of 169 and 241 are superseded by that completed
run. A focused 29-case comparator run also passed. Fixture results and native
proofs have distinct roles; neither substitutes for the other.

The file engine uses guarded pre-write checks, snapshots/backups, and
replacement. These checks are not an atomic conditional compare-and-swap.
Separate marketplace-writer conflict handling must not be attributed to the
general file engine. Private helper source remains outside Git.

## Applied configuration and generated-path accounting

There are 53 verified structured-configuration writes: 47 in the initial round
and six in the follow-up round. Actual destination counts are 29 primary and
24 remote. The final normalized comparison covers 36 files with zero pending
differences and zero issues. Account/runtime policies and host-specific trust
remain preserved.

The final comparison explicitly classifies 39 configuration-delegated paths,
20 native-catalog generated paths, 24 owned scratch paths, and 220 plugin-orphan
garbage-collection markers preserved as host runtime state. The earlier four
logical marker paths were a preliminary plan count, not the final classification
count. These classifications are not additional writes or an additive inventory
total. Do not overwrite runtime state merely to force parity.

## Native discovery and authenticated metadata acceptance

Both hosts list the same 50 MCP names and 205 native Codex plugin entries.

Claude registries contain identical sets of 91 portable keys. Native listings
show 92 user-scope records plus one project-scope record on both hosts. The
primary also discovers 16 synced-scope records. All 16 corresponding directories
and manifests exist remotely. HOME and repository working-directory probes do
not change these counts. Their optional remote activation requires the native
claude.ai login. File sync preserved account separation and copied the files;
it did not migrate authentication or establish managed-plugin activation.

Authenticated core metadata acceptance passed on both hosts:

| Service | Tools listed | Negotiated protocol |
| --- | ---: | --- |
| Skills distribution | 5 | 2025-11-25 |
| Research library | 40 | 2025-11-25 |

The primary used its installed MCP Python SDK. The remote used bounded HTTP
metadata requests after the known local SDK runtimes were unavailable. Each
service accepted initialize, the initialized notification, and tools/list.
Neither remote service assigned a session ID. No tools/call, corpus queries,
models, or embeddings ran.

An initial temporary-probe request received Cloudflare error 1010 because its
default library User-Agent was rejected. Giving that probe a descriptive
application User-Agent completed acceptance. Native endpoint definitions and
effective auth matched across hosts. No credentials, account state, TLS checks,
native configuration, or edge policies changed. Raw diagnostics and private
endpoint/authentication values remain outside Git.

## Final asset and protected-state verification

Primary native probe 2 passed 9,305 paths and 15,828 proofs. Remote serial probe 3
initially reported four directory-change errors. The guard was corrected to
check ancestor identity by inode, device, and mode while retaining strict full
leaf/link checks. An independent reviewer approved that change. Remote probe 4
then passed 2,504 paths and 2,479 proofs with zero errors.

Comparisons 3 and 4 found four actual body differences in secondary agent aliases.
Client round 120 made four staging writes and zero live writes. Server round 121
rejected the wrong residual allowlist before writes. Server round 122 used the
original pinned allowlist and passed: four actual remote updates, 87,299 bytes,
zero errors. Fresh remote probe 6 passed four logical paths and four proofs.
Primary probe 3 passed four paths and eight proofs.

Final comparison 5 and its export exited zero:

| Measure | Final result |
| --- | ---: |
| Paths examined | 235,742 |
| Canonical file matches | 190,245 |
| Directories | 41,831 |
| Portable directory links | 1,449 |
| Compatible alias candidates | 1,952 |
| Preserved pre-existing link exceptions | 265 |
| Canonical body mismatches | 0 |
| One-sided entries | 0 |
| Unresolved entries | 0 |
| Proof errors | 0 |
| Input errors | 0 |
| Remaining required probes | 0 |

The final evidence combines native baseline inventories with fresh logical
overlays and targeted native probes. The comparator reports
`live_filesystem_revalidated=false`. Do not describe this as a simultaneous
fresh all-file validation of both live filesystems.

The report contains 62,818 metadata-difference rows, including expected native
home byte-size differences, modification times, and modes. A read-only review
examined 405 mode differences on identical content. Existing native permissions
were retained rather than normalized when canonical bodies already matched.
The verified claim is canonical content, configuration, and actual native
discovery/protocol acceptance, not identical raw byte sizes, modes, or times.

All six native authentication files had available baselines and remained
unchanged. Protected-state verification exited zero. Task-owned runtime cleanup
confirmed the bounded remote wake process and task SSH control socket were
already absent. No unrelated process was signaled. Sources and backups remained
unchanged.

## Storage recovery

The parent reports approximately 1.4 GB of external free-space recovery. After
a failed compression attempt, a 135,126,354-byte receipt was restored from a
verified remote archive. Its expected SHA-256 was:

```text
6fc3a85925f3ccb2caa31c9866d991bf391cef6a2e5b0c09a8fea2651e4453b7
```

Sources and backups were untouched. Detailed storage and restoration receipts
remain private.

## Earlier connection failures

Before authenticated recovery, the SMB filesystem disconnected twice. A saved
Finder reconnect succeeded temporarily, then the mount disappeared. The direct
`mount_smbfs -N` attempt returned 77 for authentication failure. An SSH fallback
returned 255 because host-key verification was unavailable. These are historical
connection outcomes; they no longer describe the current authentication state.
The public record excludes server values, the saved URL, and authentication
material. Authentication and SSH host-key checks were not bypassed.

## Tracking state

| Task | Responsibility | State as of this commit |
| --- | --- | --- |
| `TASK-1465` | Complete mounted-home agent configuration sync | Verification accepted; parent owns delivery and closure |
| `TASK-1467` | Inventory and sync planning | Done |
| `TASK-1468` | Definition asset copy | Complete |
| `TASK-1469` | Structured configuration merge | Applied and normalized comparison passed |
| `TASK-1470` | Installed parity verification and record delivery | Claimed; verification complete and delivery pending |

## Private continuation material

Detailed inventories, copy plans, backups, helper code, configuration snapshots,
and verification receipts remain in the operator-only run directory:

```text
/Users/mitch.hudson/.local/share/agent-config-sync/20261113-1520/
/Users/mitch/.local/share/agent-config-sync/20261113-1520/
```

Inspect that run's current receipts before resuming. Recheck current source and
destination metadata; a saved copy plan does not authorize overwriting a later
concurrent edit. Keep raw configuration values, tokens, account identifiers,
private artifact bodies, and helper execution logs out of Git and PR messages.

The full safe comparison copy is
`/Users/mitch.hudson/.local/share/agent-config-sync/20261113-1520/final-comparison.json`.
Its SHA-256 is:

```text
812db814b7228a3b5b85c3a32651974b4ad2a21a5d81c98ed694b74644640f9d
```

## Delivery and recovery

All synchronization verification gates recorded here passed. As of this commit,
the remaining work is repository delivery: the parent watches final required
checks, reviews and merges the final PR tip, verifies the default-branch content,
cleans only this task's merged worktree/branch, and completes tracking.

Actual check conclusions, merge identity, and task closure are recorded in
GitHub and the private delivery receipt. This verification record does not
self-certify a later merge and does not need a narrative-only follow-up commit
to repeat that receipt. If later filesystem changes require another sync, start
from current native metadata and preserve the historical accounting limits.

## Delivery state

These verified records are prepared on `codex/agent-config-sync-1465` in
`/Users/mitch.hudson/dev/.worktrees/agent-config-sync-1465`. Draft PR:

https://github.com/mithudso/llms-explorer/pull/363

As of this commit, verification is complete and PR delivery is pending. The
actual final check and merge state belongs to GitHub and the private delivery
receipt. No merge or tracker completion is claimed by this record.
