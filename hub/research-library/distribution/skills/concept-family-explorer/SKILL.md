---
name: concept-family-explorer
description: Explore a topic family through the shared MongoDB research library. Use
  for /cfe, concept-family-explorer, missing knowledge, scored and unscored frontier
  planning, and breadth across parents, siblings, children, adjacent domains, and
  emerging concepts.
metadata:
  version: 1.0.1
  delta: Keep commissioned prompts and continuation in MongoDB
---

# Concept family exploration through MongoDB

For authorized persisted research, save the commissioned prompt, scope, coverage ledger, and resumable continuation in MongoDB concept scope/metadata and queue continuation metadata through owned leases and current revisions. Merge existing metadata deliberately before replacement. Read-only requests do not create bookkeeping writes. Client prompt, memory, and research files are not prerequisites.

Read [the MongoDB library skill](../research-library-mongodb/SKILL.md) and its
[discovery and coverage contract](../research-library-mongodb/references/discovery.md).
Use the `research-library` MCP server for inventory, search, peer wording, sources,
leases, family edits, queue state, and versioned persistence. This route replaces
local-tree orchestration while preserving external research and coverage gates.

1. Define the subject, exclusions, competency questions, and user-supplied limits.
   Map five neighborhoods: parents/prerequisites, siblings, children/subconcepts,
   adjacent/crossover domains, and frontier/emerging ideas. Start with five to twelve
   candidate names per neighborhood when evidence supports them; retain unknowns
   and map limits. Record five to ten competency questions in MongoDB scope metadata.
2. Page the full active inventory once, plus relevant `research_related`,
   `research_frontier` scored/unscored/all, `research_incomplete`, queue, and leases.
   Continue until terminal pages. Alias-expand each candidate with two or three
   distinctive variants and all four broad/narrow semantic/keyword searches before
   labeling a gap. A strong existing match becomes HAVE or STALE. Unavailable search
   channels leave novelty provisional. Pending canonical family links remain labeled
   candidates; they do not authorize bypassing holds or editing internal flags.
3. Use independent external discovery to corroborate the map. Inspect primary
   documents, code, standards, research, issues, postmortems, and competing accounts.
   Harvest neighbors from readable evidence and findings from this run. Memory-only
   guesses or an empty top-k result cannot establish a completed discovery round.
4. Retain every candidate: HAVE, STALE, GAP, incomplete, unscored, low score, SKIP,
   held, failed, and ambiguous. Use relevance/usefulness/novelty/interest/viability
   axes, each zero to five. Save `cvs_axes` and rationale with a lease/CAS edit; the
   backend recomputes CVS with weights 0.25/0.25/0.20/0.15/0.15. Viability at most one
   or novelty zero hard-gates SKIP. Default threshold is 3.2. Scalar scores without
   axes remain REVIEW; null is unscored and zero is an actual score. Near ties favor
   viability, then relevance, then interest. Preserve a user-specified threshold in
   the scope ledger rather than rewriting the server default.
5. Group authorized above-threshold work by shared primary sources and dependency.
   Research the foundation first, then each child's distinct delta through
   [dr](../dr/SKILL.md). Reuse peer wording and relevant pinned sources without
   multiplying independent origins or inheriting claim qualification. Recheck live
   dedup and acquire leases immediately before dispatch. Queue writes do not dispatch
   research, and high CVS does not override STOP, pause, or another owner.
6. Persist every returning concept through the library tools. Family mutations use
   `research_relation_mutate` with all endpoint revisions and owned tokens, including
   the old parent for reparenting. Research may run independently, but reciprocal
   edits are one atomic operation. Read results and update the revision map.
7. Re-expand only newly discovered candidates after each productive batch. Keep an
   append-only competency and coverage ledger in MongoDB scope/metadata and queue
   continuation. Frontier saturation needs two consecutive evidence-grounded empty
   rounds, a productive prior round, adequate neighborhood coverage, and independent
   blind corroboration. Coverage saturation needs every enumerated node terminal
   and every competency question resolved. Report map-bounded results as map-bounded;
   the open world is not exhausted. Explicit pass/time/count caps yield
   BUDGET_EXHAUSTED; dissent or missing evidence remains visible.

Use [trusted completion](../research-library-mongodb/references/research-and-completion.md)
for each ready concept. Server publication may be unavailable while direct MongoDB
research and draft persistence remain usable. Report the family map, scored and
unscored frontier, held/skipped/failed rows, competency coverage, actual accepted
publication receipts, and the continuation. No local research files are required.
