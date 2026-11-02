# Task completion requires delivery

The user gives standing authorization to commit, push, open or update pull
requests, and merge completed work in repositories they own. Perform these steps
without asking for another routine shipping confirmation.

A repository-changing task is complete only after its verified final changes
reach the remote default branch. Local edits, an unpushed commit, an open PR,
or queued auto-merge alone do not establish completion.

1. Review the task's diff and run the checks required for those changes. Fix
   failures before delivery. Check the current branch and worktree ownership.
2. Stage only task-owned files or hunks, then commit with a descriptive message.
   If the shared checkout contains other work, use an isolated worktree. Preserve
   active changes, private research bodies, transcripts, caches, and secrets.
3. Push the task branch. Open or update its PR with the final scope and validation.
4. Wait for the required checks on the final pushed commit. Fix failures and push
   again. Resolve routine merge conflicts without discarding either side's work.
5. Merge after the final push and passing checks. Confirm the PR is merged and
   the intended final changes are present on the remote default branch. A squash
   merge has a new commit identity; verify the merged PR and content, not ancestry
   of the original branch tip alone. Deliver later commits through a follow-up PR.
6. Fetch and synchronize the default branch where this preserves active work.
   Remove only this task's clean, merged worktree and branch. Report the PR URL,
   merge commit, and relevant checks. Complete the tracker after delivery.

Do not stop after implementation, tests, a local commit, push, or PR creation
when the remaining delivery steps are authorized and possible. Do not leave
finished work in a stash, local-only branch, draft PR, or temporary directory.

For a task that genuinely continues beyond the current turn, push a recoverable
checkpoint, keep its PR draft while work is active, and record its continuation
context. Ship a completed independent part through its own PR when useful.
Do not label an unfinished checkpoint as completed work. A later explicit user
request to pause or keep a change unmerged overrides automatic delivery.

If credentials, access, required checks, or branch protection prevent delivery,
record the exact blocker and the pushed branch or PR. Continue fixes that are
within scope. Do not claim a merge that has only been queued. Preserve safeguards:
do not force-push, rewrite the default branch, bypass required checks or secret
protection, or merge another active task's unfinished PR.

Apply this rule at task completion. It does not authorize blanket staging or
publishing other work through a session-start or every-edit hook. This policy
supersedes older instructions to skip PRs for personal repositories. Repositories
the user does not own retain their own contribution and permission policies.
