# Proposed Case-alert application contract

**PROPOSED v1, 2026-11-12; unimplemented and unvalidated.** All requirements describe proposed behavior. See the [assessment](architecture-assessment.md) for source citations/recovery limits. This worker MUST NOT inherit native Salesforce Flow interview, scheduled-path or Case escalation-rule lifecycles.

## Central source, freshness and budget

Use one elected central intake and authenticated fanout. Choose **event-first hybrid** with qualified event access, field coverage and allocation headroom: subscriptions plus central reconciliation. Otherwise choose **central incremental polling**, including deletions, durable successful-window checkpoints and overlap dedupe. Existing sync feeds need equivalent qualification. Devices MUST NOT add upstream discovery polling.

Default intake MUST include all relevant Case transitions, including qualification exits and deletes. Do not apply qualifier-only or severity-only upstream filters. Filter optimization requires independently qualified exit/reentry, replay and configuration-change coverage; otherwise disable it/use the unfiltered source. This is a proposed application constraint. Reconciliation can repair current state but cannot reconstruct an unseen false→true episode.

Planning defaults, not guarantees:

| Variable | Meaning and proposed default |
| --- | --- |
| `F` | Event change-to-device-receipt target: 60 seconds. |
| `P` | Poll interval: 300 seconds; freshness target `P + L`. |
| `R` | Reconciliation interval: 900 seconds; repair target `R + L`. |
| `S` | Timer interval: 30 seconds; lateness target `S + L`. |
| `L` | Measured source/query, processing and fanout delay. |
| `Bc`, `Be`, `r` | Daily call/delivery headroom after other integrations; reserve `r = 0.20`. Entitlements remain inputs. |

With `D = 86400` seconds/day, pages/poll `qP`, pages/reconciliation `qR`, daily hydration/repair/retry calls `H/A/J`, messages/subscriber `V`, replay messages/subscriber `W`, subscribed clients `M`:

```text
C_est = ceil(D/P)*qP + ceil(D/R)*qR + H + A + J
E_est = (V + W)*M
C_est <= (1-r)*Bc; E_est <= (1-r)*Be
```

Omit polling in event mode. Include deletion pages; budget baseline separately. Normally `M = 1`; include failover overlap. Validate `L`/budgets against measurements/allocation counters before rollout. Subscription demand is not scheduled Case queries; these estimates do not define provider metering.

At reserve exhaustion, defer optional hydration, then widen reconciliation within target. If targets/budgets fail, publish `DEGRADED`, last coverage time and missed target. Bound retries/backpressure; retain unfinished work. Polling fallback needs a budget check/source boundary. Never advance coverage past failure or label current-state repair complete historical recovery.

Clock-only predicates require durable timers: stable `timerId`, `dueAt`, Case/rule identity, expected state version and immutable creation-time `ruleBinding`. Creation is first durable acceptance; retries reuse identity/binding. Recheck when due. Stale/canceled replay is a recorded no-op; rescheduling gets a new identity. Retry to a durable decision. Timer firing MUST NOT advance the Salesforce feed checkpoint. Stale/unsupported values need budgeted central refresh.

## Immutable rule binding and activation

Logical records; all identities include authorized tenant/org scope:

| Record | Required logical fields |
| --- | --- |
| `rule_revision` | Stable `ruleId`, immutable revision/hash, validation receipt. |
| `policy_authority` | Partition, active revision, activation epoch, touch, `lastAcceptanceSequence`, fence, send enabled/generation. |
| `source_inbox` | Validated `sourceKey`, provenance, `acceptanceSequence`, immutable `ruleBindings`, acceptance send enabled/generation. |
| `activation_ledger` | Identity, previous/new revisions, boundary, actor, migration receipt. |
| `episode_state` | Case/rule/cohort, `stateVersion`, last source version, qualifier/rank, episode/ordinal, rule generation, suppression. |
| `alert_effect` | Unique identity, revision, source/episode/transition, notify disposition, append-only journal link. |

Bind work **at first durable acceptance**, irrespective of event time. Duplicates/replay MUST reuse that binding. Retain bindings/identity lookup through the recovery window; outside it, quarantine or explicitly classify a baseline/new run. Never silently rebind.

Acceptance/activation MUST serialize through a **WRITE to the same authority record**; a snapshot read alone is insufficient:

```text
accept transaction:
  a = read policy_authority
  guarded WRITE/touch a WHERE activationEpoch, touch, collectorFence match
  require exactly one match; otherwise abort and retry the whole transaction
  duplicate: reuse stored sequence, bindings and disposition
  new work: increment a.lastAcceptanceSequence in that guarded WRITE
    insert work with this acceptanceSequence, revision and send enabled/generation
  advance only the contiguous durably accepted source checkpoint
commit together

activate transaction:
  guarded WRITE same authority; increment activationEpoch; choose new revision
  record cutoff = lastAcceptanceSequence and activation-ledger entry
commit together
```

`acceptanceSequence` increases for new work, including timers, in the authority-write transaction. It is partition-local. Validate one logical authority plus shard keys/indexes, transaction routing/concerns, fencing and failover before rollout. No global ordering or exactly-once delivery is claimed. Failed guards produce no acceptance/progress.

Accepted work keeps its revision through queues/retries/replay. Rollback is a new activation of retained content, preserving intervening decisions/effects. Retain referenced revisions.

A qualifier/mapping change requires migration: drain old work to cutoff; queue newer work; evaluate cutoff projections **silently**. Both qualify: preserve episode. Only new qualifies: silent baseline episode. Only old qualifies: configuration closure. Seed new rank. Emit no alert/source transition or silent old-episode rearm. Resume after migration receipt; genuine later exits/reentries follow normal transitions.

At the cutoff, freeze old timer readiness: ready/inflight old work drains with its binding; durably cancel not-yet-due old timers and record cancellations. Create new revision-bound timer identities from the silent cutoff baseline. Never rebind an old timer; canceled/stale replays remain no-ops.

Historical reevaluation requires `reevaluationRunId`, revision, input boundary and publication authorization. Default: review-only. Publication appends corrections/supersessions linked to old effects; never rewrite history/live state. Run/item retries reuse identity.

## Shared episodes, suppression and delivery

Episode scope is `(tenantId, orgId, caseId, ruleId, recipientCohort)`, independent of users/devices/revisions. Missing pre-state/ordering requires quarantine/repair or labeled baseline. Source dedupe must preserve distinct changes; no ReplayId arithmetic, payload hash or lifetime Case-only key substitutes for business identity.

Proposed defaults:

| Input/state | Required episode/effect result |
| --- | --- |
| Initial query, reconciliation discovery or undelete | Silent baseline, with silent active episode if qualifying. |
| Trusted qualifying CREATE after baseline boundary | New episode and entry effect. |
| Qualifying → qualifying, same/lower rank | Same episode, no notification; unrelated updates do not repeat entry. |
| Qualifying → qualifying, higher rank | Same episode, new escalation effect, including within-bucket increases. |
| Qualifying → nonqualifying or closed | End/rearm; no alert. Closure overrides severity. |
| Later reentry, or qualifying reopen | New episode/entry. Within-bucket downgrade/re-upgrade instead creates a new escalation in the same episode. |
| Steady qualification | No reminder; default cooldown zero and no time-only rearm. Timer predicates can cause genuine transitions. |

Atomically compare/update `episode_state.stateVersion`, record processed work, insert effect/journal entry and advance materializer progress. Unique effect: `(authorityPartition, caseId, ruleId, cohort, episodeId, transitionOrdinal, effectKind, reevaluationRunId-or-live)`; validate against physical shard keys. Suppressed transitions retain ordinal/disposition. Retries reuse effects; conflicts retry committed state. Revision changes cannot duplicate a transition.

Shared sending defaults **disabled until cohort approval**. Retain/evaluate muted work; record suppression. Authority serializes disable/enable; enable advances `sendGeneration`. Unmute allows future accepted transitions only; catch-up needs a new reevaluation run. Dispatch authorization MUST linearize with a guarded authority WRITE: sending enabled, acceptance generation unchanged. Commit attempt authorization before dispatch. Disable blocks later authorizations; already-authorized in-flight sends may arrive afterward. Socket delivery/revocation is not atomic with this transaction.

Device ACK is contiguous receipt; per-user read/dismissal is user interaction. Neither changes shared episode/rearming or another user. Delivery failures retry the same identity. History/catch-up may display suppressed decisions, never turn them into new paging notifications.

## Proposed acceptance traces

These are design expectations, not executed test results. `Q` means qualifying; ranks increase with urgency.

| Given → when | Required observable result |
| --- | --- |
| Gap → reconciliation discovers Q | Silent repair; historical uncertainty retained. |
| Poll page fails | Coverage stays behind; overlap retry; degraded freshness. |
| Timer due after Case closes | Durable no-op; no device source query. |
| Acceptance races activation | Authority write selects one binding, never mixed. |
| r1 accepted → r2 active → replay | Old binding/effect r1; new work r2. |
| New qualifier makes existing Case Q | Silent migration; no configuration alert. |
| Baseline Q → edit → rank up/down/up | Silent baseline/edit; two escalations, one episode. |
| CREATE Q → duplicate → exit/reentry → close/reopen Q | Initial entry once; new episodes on reentry/reopen. |
| Concurrent same-transition workers | One committed state advance/effect. |
| Muted Q entry → unmute → steady Q → rank increase | Suppressed history; no unmute page; later increase eligible. |
| Device ACK/user read → transport retry | Same identity; no shared rearm/other-user read. |
| Timer r1 not yet due → r2 migration → old timer replay | Durable cancellation; new r2 timer identity; old replay no-op; no feed-checkpoint advance. |
| Proposed filter hides Q exit/reentry | Reject optimization/use unfiltered source; reconciliation cannot certify the unseen episode. |

Deployment requires topology and end-to-end validation. This proposal authorizes no runtime/source change.
