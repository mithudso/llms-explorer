# Proposed device recovery and central hydration contract

**PROPOSED v1.0.0, 2026-11-13; unimplemented/unvalidated.** All behavior is proposed, not a native guarantee. One elected collector owns upstream discovery/subscriptions/reads; materializers/distributors consume durable work. Devices use this service only. Qualify physical shards, concerns, ordering/fencing; no exactly-once claim.

## 1. Feed identity and API

Authenticated scope is `(tenant,org,cohort,partition,fieldPolicy,grantVersion)`. Reauthorize reads, buffered sends and ACKs. Grant changes reset sessions/cursors; dispatched bytes cannot be recalled. Signed cursors bind protocol/key version, principal/device, scope/partition, grantVersion, sequence/expiry; they grant no access.

Journal: immutable `{entryId,seq,effectId?,caseId,contentVersion?,disposition,payloadRef}`. IDs survive retries. Projection/effect/journal sequence commit together. `head` (high-water) is highest contiguous committed sequence, never an allocator counter; `floor` is oldest resumable position. Decimal-string sequences are partition-local, not ReplayId arithmetic/global order. Scans disclose no forbidden payload.

JSON endpoints use `/v1/feeds/{partition}` with authenticated session/cursor headers. Proposed configurable limits: 100 entries/256KiB per page, 1MiB unacked/device, 30-second heartbeat/head check; not provider limits or measured SLOs.

| Operation | Required request → successful response |
| --- | --- |
| `POST /sessions` | `{deviceId,grantVersion,afterCursor?,stateLost}` → `{sessionId,sessionGeneration,grantVersion,head,floor,readCursor,limits}`. New/missing state requires snapshot. |
| `GET /entries` | Session, afterCursor, bounded limit → `{pageId,fromExclusive,scannedThrough,entries,throughCursor,head,more}`. Read `(after,capturedHead]`; cursor covers scannedThrough only. |
| `POST /acks` | `{sessionId,sessionGeneration,pageId,throughCursor}` → `{durableAckCursor}` after durable commit. Reject unissued/beyond-scan ACK; duplicate/lower ACK is idempotent. |
| `POST /snapshots` | Current session → 202 building or `{snapshotId,boundary,nextPageToken,expiresAt}`; `GET /snapshots/{id}/pages` returns immutable items, nextPageToken and final completionToken. |
| `POST /snapshot-acks` | `{snapshotId,completionToken}` after local commit → durableAckCursor at boundary; record reset/history-loss disposition. |

Example: after 41, scan through 47 returns visible 43/46 and cursor 47. Persist entries/barrier before ACK 47. Page 48–52 arriving first leaves a hole: replay it before ACK 52. Validate issued ranges/current session generation, not signature alone.

Client MUST atomically persist IDs/state/contiguous cursor before ACK. Store monotonic ACK per device/scope/grant/partition. New sessions inherit that ACK under a new generation; reject old-session ACKs. Resume from the lower valid local cursor/server ACK. New ACK must cover `(server ACK,through]` by issued contiguous ranges; holes cannot advance it. Crashes repeat IDs idempotently. Lost local state requires snapshot. Receipt never means read/rearm/upstream progress.

## 2. Attach, resume and snapshot reset

`GET /wakeups` emits `{kind:"wake",partition,observedHead}`/heartbeats. Each distributor arms wakeups, captures H, rereads its devices' journals from durable ACK through H, then rechecks head before waiting. Repeat on reconnect/wake/periodic check, catching attach races even if hints vanish/duplicate/reorder. Change streams are not durable inter-process broadcast; head checks never query Salesforce.

Return 410 `SNAPSHOT_REQUIRED` for expired/below-floor cursor or invalid reset generation; never jump to head. Grant mismatch requires reauthorization. Record historyLost when old delivery cannot be established.

Snapshot MUST freeze authorized state at B and retain journal >B before pages. Without a qualified consistent/versioned view return 503 `SNAPSHOT_UNQUALIFIED`. Lease expiry/exhaustion aborts/restarts. Concurrent commits stay journaled; live buffer is optional. After final page atomically replace local state/persist B, snapshot-ACK, reread >B; never skip a snapshot/attach race.

Snapshots silently restore state, never create effects. Replay retains effect IDs and frozen disposition; muted history cannot become paging. Current-state repair cannot reconstruct purged/unobserved transitions.

Bound/fairly schedule device/tenant work. Pause at unacked limit; timeout closes `SLOW_CONSUMER`, resuming from ACK. Never drop/ACK buffers. Pressure returns 429/retryAfterMs; dormant retention expires/resets.

## 3. Central baseline and incremental coverage

Collector adapter alone schedules Salesforce I/O. Sync state: `{runId,authorityEpoch,queryContractHash,window,continuation,acceptedPage,coveredThrough,deletionCoverage,status}`. Accept only current-authority/expected-version results; reject stale overwrites even when old-owner reads finish.

Fully paginate; persist results/obligations before continuation. Failures keep boundaries; bounded retries cost budget. Qualified getUpdated uses latestDateCovered, not requested end; track deletions separately. Expired cursors restart overlapping deduplicated windows. Complete coverage needs all pages/deletes; intake differs from processed/repair progress.

Salesforce baseline is not atomic by assumption: retain work after an intake boundary; merge by qualified ordering/CAS and reconcile changes/deletes. Unknown order/pre-state requires quarantine/silent repair, not invented transitions. Hydration cannot rewrite episode evidence/history. Repair every gap ID; overflow/expiry needs entity/deletion reconciliation. Refresh time-only/unsupported values centrally.

## 4. Coalescing and authorized content cache

`POST /v1/case-content`: `{caseIds,fieldContract,minContentVersions?,maxSourceAgeSeconds}`, maximum 50 IDs proposed. Per-item `{caseId,state,contentVersion,sourceVersion?,lastVerifiedAt,completeFields,stale,payload?}`; state `ready|pending|incomplete|tombstone`. Ready requires fields/minVersion/age bounds; otherwise incomplete/pending. Pending returns 202/job/retry; denial exposes no content. ETags bind scope/grant/fields/version; 304 never renews age. Devices never query Salesforce.

Coalesce baseline/gap/device IDs in bounded tenant queues. Single-flight `(tenant,org,caseId,fieldContractHash)`; authorize each recipient; stronger unmet field/version demands schedule follow-up. Proposed defaults: flush 100ms/50 IDs, 2 in-flight batches/tenant, 1000 eligible IDs; also obey qualified adapter count/byte limits, not assumed Salesforce limits.

Cache scope/fields/contentVersion. Proposed TTL 60s, hard age 300s narrowed by caller maxSourceAge; age is last verification, not absence of unseen changes. Invalidation increments dirtyGeneration/coalesces refresh; clear only if captured generation/version still matches, else retry. Hits never renew age. Label stale; beyond bound return 202/503 `FRESHNESS_UNMET`.

Qualified deletes write versioned tombstones/invalidate content; old hydration cannot resurrect them. Permission/ambiguous not-found is not deletion. Missing fields stay incomplete and enqueue authorized repair; absent placeholders cannot erase known values. Unknown ordering stays unqualified.

## 5. Budget, errors and unexecuted traces

Budget central pages/retries under existing reserves. At capacity reject new device jobs; retain accepted obligations/backpressure intake. Intake needs durable acceptance; processed progress cannot pass repair. Fairly prioritize qualification/deletes over optional details. Wider intervals expose degraded freshness/coverage; no retention extension. Metrics: queue/cache age, depth/hits, incomplete/tombstones, head–ACK lag; no bodies.

Errors `{code,retryable,requestId,retryAfterMs?}`: 400 malformed/tampered, 401 auth, 403 scope/grant, 409 ACK/version, 410 reset, 429 admission, 503 unavailable/unqualified. Never advance progress on failure. Breaking wire/identity/ACK changes require v2; additive v1 fields remain compatible. Announce retirement/migration windows.

All traces below are **unexecuted acceptance requirements**:

| Given → fault/action | Required observation |
| --- | --- |
| after 41 → commit 42 races attach; wake lost | Journal reread/check returns 42; no device upstream read. |
| Apply 43 → crash before ACK | Same IDs; no duplicate local effect; persist before contiguous ACK. |
| Page 52 before 47 | Hole retained; ACK 52 rejected until earlier range is durably covered. |
| Below-floor cursor → snapshot B; commit B+1 during pages | Silent consistent state plus retained catch-up; expired hold resets. |
| Grant revoked with buffered work | Subsequent send/read/ACK denied; no old-grant confidential payload. |
| Many requests/ID → invalidation during fetch | One flight; stale generation cannot clear dirty; bounded follow-up. |
| Delete → old hydration | Tombstone wins; no resurrection/invented episode. |
| Page failure / missing required field | Coverage stays behind; incomplete repair visible; retries budgeted. |

Q2 inputs: exact Case qualifier/severity fields/types/values, enabled entities/field access, cohorts/grants and qualified ordering/topology/fencing/budget/retention. Q10 uses these traces plus [acceptance matrix][matrix]: measure source→journal→device timing, severity upgrades, replay/duplicates and lost visibility. No org/parser/device/shard/fencing test ran.

## Evidence boundaries

Source facts: [distribution], [hydration], [authorization]. This adds no certified facts; preserve frozen [rule/episode policy][policy].

[distribution]: https://raw.githubusercontent.com/mithudso/llms-explorer/main/outputs/llms-concepts/salesforce-single-subscriber-durable-mongodb-alert-distribution.llms/llms-facts.txt
[hydration]: https://raw.githubusercontent.com/mithudso/llms-explorer/main/outputs/llms-concepts/salesforce-case-baseline-hydration-and-reconciliation.llms/llms-facts.txt
[authorization]: https://raw.githubusercontent.com/mithudso/llms-explorer/main/outputs/llms-concepts/shared-case-alert-authorization-and-sensitive-data-minimization.llms/llms-facts.txt
[policy]: https://raw.githubusercontent.com/mithudso/llms-explorer/main/docs/research/salesforce-pubsub-full-suite-2026-11-12/application-policy-contract.md
[matrix]: https://raw.githubusercontent.com/mithudso/llms-explorer/main/docs/research/salesforce-pubsub-full-suite-2026-11-12/architecture-assessment.md#acceptance-and-failure-matrix
