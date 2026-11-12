# Step 6.7: location sync

Discover the target skill's installed copies and hash their contents. Treat the explicitly selected source as canonical only after checking repository instructions and the user's intent. Report divergent, newer, vendored, remote, and plugin-managed copies. Do not overwrite them automatically.

Respect git worktree ownership and preserve other work. Before any authorized synchronization, save a recoverable preimage, check for concurrent writers and symlink loops, and verify the destination after writing. Never push or merge another repository without authorization. In read-only mode, inspect and report only. If a required copy cannot be synchronized, report SYNC-PARTIAL.

## Git clone destinations

A git clone is a repository destination. Do not copy a source file into it and
call that delivered. Inspect its branch, worktree ownership, remote and dirty or
divergent state first. Preserve active work and concurrent writers.

When delivery to that repository is authorized, use its commit, push, PR, required
checks and merge workflow. Verify the final content on the remote default branch.
Then fetch and fast-forward only a clean compatible clone; never reset, stash
another writer's work, force-push or rewrite its default branch. A dirty,
divergent, independently owned or inaccessible clone stays unchanged and appears
as blocked or report-only in the location table. Record the exact blocker and
recoverable branch/PR when delivery cannot finish. Authorization for this source
repository does not authorize publishing a different repository.

Example: a clean clone on its default branch and strictly behind the verified
remote may run `git fetch origin` followed by `git merge --ff-only origin/main`
when `main` is its actual default branch. A clone with local commits or edits
remains preserved while delivery proceeds in an isolated owned worktree.
