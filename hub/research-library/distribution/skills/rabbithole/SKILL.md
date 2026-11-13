---
name: rabbithole
description: Deepen one concept through its mechanism, parts, limits, failure modes,
  history, primary wording, and expert disagreement. Use for /rabbithole, exhaustive
  depth, or repeated deepening passes; use concept-family-explorer for neighboring
  topics.
metadata:
  version: 1.0.1
  delta: Keep commissioned prompts and continuation in MongoDB
---

# Deepening one MongoDB concept

For authorized persisted research, save the commissioned prompt, scope, coverage ledger, and resumable continuation in MongoDB concept scope/metadata and queue continuation metadata through owned leases and current revisions. Merge existing metadata deliberately before replacement. Read-only requests do not create bookkeeping writes. Client prompt, memory, and research files are not prerequisites.

Read [the MongoDB library skill](../research-library-mongodb/SKILL.md),
[versioned evidence edits](../research-library-mongodb/references/versioned-edits.md),
and [research and completion](../research-library-mongodb/references/research-and-completion.md).
Use the `research-library` MCP server and discovered `research_*` tools directly
for existing knowledge, sources, leases, claim changes, scope, and continuation.

1. Bound one concept's mechanism, internals, variants, history, and exceptions.
   Keep siblings, parent domains, and neighboring fields outside this depth run.
   Resolve aliases and current coverage through all four broad/narrow
   semantic/keyword searches, then read current claims, pinned sources, gaps, queue,
   and holders. Use supplied seed material as evidence leads and store readable
   source snapshots through MCP. Local research scripts or run directories are
   not needed to start or continue.
2. Reuse an owned draft or create a genuinely distinct concept after deduplication.
   Acquire its lease, reread its revision, and preserve all accepted historical
   evidence. An ordinary [dr](../dr/SKILL.md) pass supplies the baseline atomic claim
   inventory. Store the scope, boundary, and baseline through the library tools.
3. For each deepening pass ask: why does each claim hold, what is the mechanism,
   where are its limits, what are the exceptions, who disagrees and why, what did
   the primary source actually say, and how did understanding change over time?
   Vary terminology and use independent external discovery, primary sources,
   disconfirming searches, and exact source-cache lookup/read before another fetch.
   Save only new, relevant atomic claims with immutable source pins and Unicode
   evidence spans. Rephrasing an existing claim counts as zero new information.
4. Record each pass's new atomic claims divided by total accumulated claims after
   that pass in MongoDB telemetry or scope metadata, with retained/rejected leads
   and source gaps. Renew the owned lease and use each returned revision for edits.
   Shared or inherited sources retain origin and qualification separately.
5. Default maxPasses is six unless the user supplies another bound. Two consecutive
   passes each below five percent new-information rate support SATURATED-DEPTH.
   A pass/time cap yields BUDGET_EXHAUSTED, not saturation. If new work repeatedly
   moves into neighboring concepts, stop the boundary breach and hand those leads
   to [concept-family-explorer](../concept-family-explorer/SKILL.md) instead.
6. Keep the complete accumulated definition, mechanism, history, failures,
   limitations, conflicts, and questions as evidence-bound MongoDB claims/prose.
   New depth-pass assertions require the same independent gate as the baseline.
   Request `research_finalize` only when commissioned scope and evidence are ready;
   follow `research_publication_status` and verify the resulting current proof.
   If publication is unavailable, keep the full draft and explicit continuation
   in MongoDB. No client-side file can substitute for accepted publication.

Report depth yield per pass, primary evidence, unresolved disputes and source gaps,
neighbor handoffs, research stop verdict, and the separate publication outcome.
Keep tokens and credentials private; peer support labels never qualify new claims.
