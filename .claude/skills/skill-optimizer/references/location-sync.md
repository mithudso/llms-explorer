# Step 6.7: location sync

Discover the target skill's installed copies and hash their contents. Treat the explicitly selected source as canonical only after checking repository instructions and the user's intent. Report divergent, newer, vendored, remote, and plugin-managed copies. Do not overwrite them automatically.

Respect git worktree ownership and preserve other work. Before any authorized synchronization, save a recoverable preimage, check for concurrent writers and symlink loops, and verify the destination after writing. Never push or merge another repository without authorization. In read-only mode, inspect and report only. If a required copy cannot be synchronized, report SYNC-PARTIAL.
