# Research queue audit — 2026-10-29

Version: 1.0.1. Delta: clarify immutable evidence handling and transaction-check
scope after independent review. Observation window: 2026-10-29 15:29–15:38 UTC.

The queue needs reconciliation before another broad dispatch. The hub has **147
unique pending concepts**, of which **59 remain reserved by the paused suite**.
The October 27 MongoDB round has **15 local completions and 39 withheld concepts**.
No research, queue status, reservation, gate or service was changed by this audit.

## Scope and authority

The unchecked hub queue is the source for the ranked queue. The repository queue
also contains a much larger historical frontier inventory. These have different
coverage and cannot be synchronized by replacing either file wholesale. Queue
checkboxes, tree membership, cohort outcomes and publication each answer different
questions. A checked row alone is not evidence that every claim was verified.

The audit used the lossless parser in
`/Users/mitch/dev/worktrees/llms-explorer-queue-audit-20261029/scripts/mongodb_research_queue.py`,
the checkout scanner in
`/Users/mitch/dev/worktrees/llms-explorer-queue-audit-20261029/api/explorer_api/checkouts.py`,
saved plans, and an independent research-contract-auditor. The accompanying
`inventory.json` records exact source paths, SHA256 hashes, line numbers, duplicate
groups, status differences, omissions and cohort lists. Identity comparisons
collapse whitespace and case; they retain each authored name and source row.
Two occurrences of private operator-denylisted labels are redacted from the
public inventory. Source hashes and aggregate counts are unchanged.

The publication baseline is remote main `90cbb461`. Shared main `dbed74f0` is clean
but diverged by five local and twenty remote commits. It was preserved. The
retained MongoDB runtime is `d19fd59f`; its existing research edits were preserved.

## Inventory

| Source | Queue rows | Pending rows | Unique pending concepts | Done rows | Tree nodes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Hub | 303 | 148 | 147 | 155 | 2,166 |
| Remote main snapshot | 4,656 | 4,648 | 4,643 | 8 | 2,145 |
| Retained MongoDB runtime | 4,656 | 4,633 | 4,628 | 23 | 2,161 |
| Divergent shared main | 4,168 | 4,168 | 4,163 | 0 | 2,161 |

The paused `mongodb-2026-10-14` suite retains 694 unique reservations. Only 59
overlap the hub's pending concepts. The other **88 hub pending concepts are
unreserved**, which does not establish readiness: some already have nodes or
aliases, and 39 need correction of saved research. The scanner found no fresh DR
manifest or unfinished explorer batch holding additional work on this machine.
This does not establish whether a remote host has active work.

## Findings

### 1. High priority: 39 MongoDB concepts still require claim/evidence repair

`/Users/mitch/.global-ai-hub/research/.ranked/mongodb-local-20261027/plan.json`
contains 29 cohorts: ten complete, covering 15 concepts; nineteen `needs-review`,
covering 39 concepts; zero pending or running cohorts. Latest saved gates contain
29 `UNVERIFIED`, 18 `NOT-IN-SOURCE` and two `CONTRADICTED` judgments. These 49
judgments are the repair targets. Positive judgments in those cohorts do not
promote the cohorts. Both the hub and runtime correctly keep all 39 unchecked,
without result nodes.

All 54 plan row fields still say `pending`. Cohort checkpoints and bound
artifacts establish the actual outcomes. The existing MongoDB outcome task,
TASK-950, explicitly records this guard. Do not restart the finished controller
or rebuild discovery from those row fields. Correct each affected canonical
claim or source binding; retrieve a new immutable snapshot when needed. Preserve
existing pinned evidence and the failed packet, then request a fresh gate.

### 2. Medium: the ranked view no longer describes the current backlog

`/Users/mitch/.global-ai-hub/concept-tree/RESEARCH_QUEUE_RANKED.md:3` still describes
the October 20 snapshot: 195 rows, 194 normalized names, 137 above the score gate
and 58 below it. **86 ranked rows now refer to checked hub entries.** Conversely,
**39 current pending concepts are absent**, all scoring at least 3.2. They are
exactly the 39 withheld October 27 concepts; they are retained in their saved plan.

Current hub pending concepts comprise 90 at or above 3.2, 57 below it, and zero
unscored names. These counts use stored node/sidecar/inline scores; no scores were
recalculated. The runner has pending, reservation and coverage guards, so a stale
view does not by itself prove duplicate research was dispatched. It does give a
misleading priority overview. Regenerate a status-aware view while preserving
revisit intent, saved plan identities and held reservations. Show withheld work
as repair work instead of presenting it as fresh discovery.

### 3. Medium: 15 verified local results have not reached remote main

The hub and runtime have all 54 October 27 queue rows, with 15 checked and 39
unchecked. Remote main has all 54 unchecked and none of the 15 result nodes or
readers. The divergent shared main contains the 15 result nodes but none of the
54 exact queue labels. No single local checkout describes publication state.

The independent audit verified ten canonical artifacts; all ten export transaction
journals report complete. It found 30 pack directories across both roots, containing 240
members, plus 15 runtime readers, 15 Markdown downloads and 15 research-artifact
JSON files. Result publication remains a separate deliverable from the merged
frontier planning PR:
https://github.com/mithudso/llms-explorer/pull/243

The completed cohorts contain 230 claims: **213 supported sampled claims and 17
ordinary claims not sampled**. Do not describe all 230 as independently supported.
One public pack differs from its private peer because it redacts an issue
identifier/reference; that is expected privacy handling. Publish only the
qualified result projections through their own reviewed delivery scope.

### 4. Medium: duplicated and renamed labels obscure queue outcomes

The hub has eight duplicate groups. Seven concepts have both a checked and an
unchecked row: mtools Log Analysis Integration; FTDC Storage Overhead & Retention
Budgeting; SERVER JIRA Ticket Regression Mapping; PII Masking & Query Hash
Anonymization; Disk IOPS Burst Credit Depletion Playbook; Atlas CLI Failure
Scenarios; and Error Codes and Troubleshooting Benchmark Metrics. All seven are
also protected by the paused suite. For example, compare
`/Users/mitch/.global-ai-hub/concept-tree/RESEARCH_QUEUE.md:45` and
`/Users/mitch/.global-ai-hub/concept-tree/RESEARCH_QUEUE.md:119`.
Cross-Organization Billing appears twice pending, under different parents.
The repository queue has five other duplicate groups. These are recorded in the
inventory; multiple parents must survive any deduplication.

Of 148 pending hub rows, 59 match existing nodes and twelve match aliases. These
are coverage-review candidates, not automatic completions. Compare actual facts
and revisit scope before deciding whether more research is needed.

Five checked hub names have no exact node or alias. Similar successor names
exist for sleep/wake handling, Mach-O SDK stamps, sandbox report export, donation
links, and `natural hint and collection scans`. In the last case, the queue name
still begins with `$natural`. This is a name/alias continuity gap; it is not proof
that their research disappeared. Verify the mapping and retain historical names
as aliases when reconciling.

### 5. Medium: two queue consumers still skip valid embedded-backtick labels

The lossless inventory parser and API read all 4,656 repository rows. The older
hub parser and TUI parser read only **4,654**. They skip:

- ``Reading indexed `$or` plans with explain`` at
  `/Users/mitch/dev/worktrees/llms-explorer-queue-audit-20261029/concept-tree/RESEARCH_QUEUE.md:4227`.
- ``Same-field `$or` to `$in` rewrite`` at
  `/Users/mitch/dev/worktrees/llms-explorer-queue-audit-20261029/concept-tree/RESEARCH_QUEUE.md:4400`.

Both queue rows correctly use double-backtick Markdown delimiters. The API's
current parser preserves them. The older regex at
`/Users/mitch/dev/worktrees/llms-explorer-queue-audit-20261029/hub/scripts/concept_tree.py:79`
and the TUI regex at
`/Users/mitch/dev/worktrees/llms-explorer-queue-audit-20261029/llmsx/llmsx/explorer_store.py:96`
only accept single delimiters. Align the source consumers with the existing
lossless grammar and add a regression check covering embedded backticks. This
audit checks source behavior; it does not identify the installed TUI revision.

### 6. Medium: the older ranked plan needs outcome and evidence reconciliation

`/Users/mitch/.global-ai-hub/research/.ranked/codex-2026-10-20/plan.json` records 23
complete cohorts (82 concepts), one withheld cohort (four Apple concepts), and
seven pending cohorts (16 concepts). Four of those sixteen concepts subsequently
completed in the October 24 local plan. They are already checked in the hub.
The old plan retains its original pending cohorts and 86 stale row outcomes.
Resume must honor current coverage and the later completion receipts.

Seventeen of the 23 completed cohorts have neither an accessible recorded run
directory nor a corresponding run directory under this machine's current hub.
Their checked rows and tree nodes do not substitute for the missing local gate
packets. This is an evidence-access gap, not a finding that the historical
research was invalid. Locate the owning host/checkpoint before recertifying or
repairing these cohorts. The four withheld Apple concepts likewise cannot be
fully audited from an absent local run directory.

### 7. Low: six repository rows reference an unresolved parent

Six pending rows at
`/Users/mitch/dev/worktrees/llms-explorer-queue-audit-20261029/concept-tree/RESEARCH_QUEUE.md:728`
through line 733 name `Partition Fields`, which is neither a node nor an alias
in that tree. A related `Partition fields constraints for DATE rules` node exists,
but semantic similarity does not establish the intended parent. Select the
parent deliberately before placement. The current hub queue has no unresolved
pending parents.

### 8. Low: public continuation prose still reports the old running state

`/Users/mitch/dev/worktrees/llms-explorer-queue-audit-20261029/docs/research/mongodb-frontier-research-2026-10-27/README.md:5`
says the queue is running and preview credential repair remains pending. The
saved outcome and merged planning PR supersede both statements. Update this
historical report when reconciling the result publication, retaining the launch
snapshot as explicitly historical.

## Checks and limits

The independent audit passed canonical validation for all 29 current October 27
gate packets: 785 judgments and 1,314 exact evidence spans. Claim-local URLs,
source identities, snapshot hashes and character offsets match. All 29 current
claim-file hashes and manifest concept/depth bindings match. Canonical verification
passes all ten completed artifacts.

Across the whole October 27 round, the 815 canonical claims comprise 736
`SUPPORTED`, 29 `UNVERIFIED`, 18 `NOT-IN-SOURCE`, two `CONTRADICTED`, and 30 ordinary
`NOT-SAMPLED` claims. Mechanical validity does not resolve semantic dissent.

The audit did not rerun semantic judgments, retrieve new sources, reassess
organizational independence or negation searches, start workers, modify gates,
perform inference/indexing, or probe production deployment. It preserved the
content hashes of all eleven sampled queue/tree/plan source files. An independent
source-by-source recertification of the whole historical corpus is outside scope.

Stele task creation returned the monthly write-limit error, so no new graph task
or knowledge was created. The audit's continuation record is
`/Users/mitch/dev/worktrees/llms-explorer-queue-audit-20261029/memory.md`.

## Recommended order

1. Reconcile queue identity, duplicate status, parser grammar and the ranked view
   while preserving reservations and explicit revisits.
2. Publish the 15 locally qualified MongoDB projections with fresh publication
   checks. Keep raw private evidence private.
3. Repair the 49 dissenting judgments for the 39 withheld concepts, then obtain
   fresh gates. Continue from their existing claims and sources.
4. Locate historical run artifacts and reconcile the October 20 plan with later
   outcomes before resuming its remaining work. Leave the paused suite held.

The audit is complete. These remediation steps remain recommendations; the user
requested an audit, and no queue repair or research execution was performed.
