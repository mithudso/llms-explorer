# Repository checkpoint reconciliation

Reconcile checkpoint `09f1058e` in PR #234 with main at `89314a7c`.
The checkpoint contains work accumulated across several research sessions.
Main advanced by 49 commits while that checkout remained on its older base.

## Conflict decisions

- Keep main's research runtime, provenance fixes, compiler, tests, and existing
  verified packs. Their conflicting checkpoint copies predate fixes already
  delivered to main.
- Merge concept records by exact concept identity. Keep main's complete record
  when both sides changed it. Retain all 230 checkpoint-only records and all
  main records. Connect retained children to their selected parents.
- Keep main's 1,056 CVS score records and current research queue. Merge the
  checkpoint's additional skill summaries and append-only workflow notes.
- Regenerate the tree, context, keyword search, and facts downloads from the
  reconciled repository data. Use the repository publication scrub and preserve
  the richer committed reader when an older pack would reduce its coverage.
- Preserve the original checkpoint in Git history. Merge main through a normal
  merge commit and update the existing PR without rewriting its branch.

The merged tree has 2,145 concepts. The publication projection has 1,823 reader
packs with 94,593 facts. These are snapshot counts; they do not establish new
research coverage or saturation.

## Preservation and validation

All 318 public research artifacts match their compiled units and declared
projection hashes. Their canonical identities agree with the concept tree.
Semantic vectors remain frozen: the existing 1,018 rows retain keyword coverage,
and 805 additional packs remain explicitly deferred from semantic indexing.
This reconciliation generates no embeddings and starts no model research.

The artifact compilation regression test sets its repository explicitly. This
prevents a temporary path left by another test from selecting a missing site
generator when the research tests run together.

Scratch under `tmp/` and the three vendor mirrors previously rejected by secret
protection remain local. Ignore rules preserve those files without including
them in the completion commit. The reconciliation does not unblock the vendor
mirrors or publish their credential-shaped examples.

Validation covers the research and script tests, exact artifact and tree
identity checks, privacy checks with the operator denylist, Ruff, generated data
currency, the full site build and publication policy, site and CLI tests, and the
required pull request checks.
