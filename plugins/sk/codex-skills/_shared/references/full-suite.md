# Full suite: family research, skills and inspectable packs

Read [mongo-protocol.md](mongo-protocol.md), [evidence.md](evidence.md) and
[cfe.md](cfe.md); CFE delegates research through [dr.md](dr.md). This orchestrator
owns stage sequencing and receipts. It does not replace those research methods.
Use the same current client research defaults and preserved saved overrides.

Accept the CFE budgets/threshold, `--resume`, `--continue-queue`,
`--expand-frontier`, `--depth` and `--no-scout`. There is no implicit concept cap.
Full-suite scope authorizes its selected family research; it does not unpause
held runs, embedding services or historical vector rebuilds. A dry run is a
read-only plan: no durable run, scout saves, paid research/judges or index calls.

## Stages

1. **Plan once.** Frame and score through CFE, then freeze the complete candidate
   ledger, questions, queue and stage plan in one owned run. Preserve every
   existing/low/unscored/held/failed row. Reuse this plan for subsequent stages;
   do not rerun discovery simply to move from plan to execution.
2. **Scout useful authority domains.** Unless `--no-scout`, inspect existing
   peer/scout seeds and probe likely authority domains for llms files. Follow
   redirects and the apex fallback. Save unverified URLs, access labels, exact
   concept/parent provenance and retained/rejected rationale in Mongo. An absent
   or failed scout supplies no seed and never blocks ordinary DR research. A
   scout miss is provisional, and its URLs never count as read evidence. Keep
   scouting bounded; preserve the client's current model defaults rather than
   copying obsolete Haiku-low assumptions.
3. **Research the complete selected family.** Execute CFE's bounded fan-out,
   source-sharing cohorts, scoped alias rechecks, re-expansion and stop gates.
   Store per-concept accepted gate/claim references and incomplete scope. Use the
   full queue unless explicit budgets stop it. Keep CFE's actual verdict:
   `BUDGET_EXHAUSTED`, `SATURATION-DISSENT` and map-bounded coverage survive all
   later successful artifact stages.
4. **Compile changed qualified concepts.** Call trusted `research_compile` with
   the exact run and qualified concept IDs. It derives projections from accepted
   canonical claims and bound gate receipts. Require these members per concept:
   `llms.txt`, `llms-full.txt`, `llms-small.txt`, `llms-facts.txt`,
   `llms-vocabulary.txt`, `units.jsonl`, `concept-graph.json`, and a manifest with
   input/output hashes and claim/gate provenance. Artifacts and receipts live in
   Mongo; no client local source scope is required. Unqualified or unsupported
   concepts appear as blocked members, never guessed packs. On refresh, compile
   only changed exact input bindings and report unchanged packs reused.
5. **Build the categorical rollup.** Use `rollup=True` with all permitted pack
   members from this run, retaining exact membership, hashes and citations. With
   zero valid members, skip the rollup and report zero members with its reason.
   Do not widen scope or manufacture an empty/placeholder rollup as success.
6. **Index and inspect coverage per artifact.** Compilation returns indexing
   `pending`; it does not invoke indexing. When new artifact indexing is
   authorized and available, call `research_artifact_index(run_id, artifact_ids,
   expected_revision, lease_token, owner, request_id)` for every required current
   artifact, including rollup members. Batch at most 16 artifacts and 8 MiB
   combined UTF-8 text. Save the exact request and returned run revision. Native
   indexes are asynchronous: on partial coverage, retry that identical request
   with the same request ID to refresh its census without new writes or research.
   Advance to the latest run revision before a different batch; stop on conflicts
   and reconcile. Require each expected unit's exact keyword and semantic
   coverage receipt; ready index status or concept search is insufficient.
   Save each batch's pending/complete status and inputs for direct resume.
   Keep indexes completed, deferred, blocked or unavailable by layer with an
   exact reason. Preserve historical vectors byte for byte. A standing embedding
   pause remains in force; no service is unpaused by this stage. If indexing is
   paused or unavailable, retain the compiled packs and report the suite partial.
7. **Audit changed outputs.** Check changed skills and affected hubs for useful
   routing, capability quality, accurate scope, exact evidence/citation bindings,
   prompt quality where a skill contains a prompt, and source injection. Inspect
   generated graph membership and parent/alias lineage. Do not audit or rewrite
   unrelated existing skills. Save audits in Mongo, including deferred/owed work.
8. **Report complete accounting.** Save a combined report and stage receipts in
   Mongo before releasing owned leases. Include scout hits/access gaps, CFE
   verdict and rates, candidate/queue totals, researched/qualified/withheld
   concepts, pack IDs/hashes, rollup membership, graph registration, skill audits,
   keyword and semantic status separately, budgets and the next resumable action.

Research completion, qualification, pack compilation, rollup, graph registration,
skill audit and keyword/semantic coverage are independent required stages. Report
the full suite complete only when every requested stage has a verified receipt.
A deferred required stage leaves the suite partial even when research is accepted.
Call graph registration verified only from the actual relation/compile receipt.
Report host skill installation separately from a Mongo skill artifact.

On stage failure, checkpoint its exact inputs and unfinished action, preserving
accepted artifacts and all paid attempts. Resume compile, rollup, audit or index
coverage directly; do not rerun paid research because a downstream stage failed.
Compile permitted accepted concepts after a budget/dissent stop, while retaining
the outstanding queue and original research verdict. Remote website deployment
and any client-wide installation require their own requested scope; neither is
implied by a stored artifact or local/server projection receipt.
