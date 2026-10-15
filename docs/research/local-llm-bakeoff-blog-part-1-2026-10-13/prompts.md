# Local LLM bake-off blog, part 1: prompt

Version: 1.0.0

Delta: Record the publication request.

## User prompt

```text
While waiting on all of that to finish, write up a blog post detailing everything you've worked on and discovered so far and add it to the ~/dev/llms-explorer blog list, there will be a 2nd part which includes the rest of what you work on including the winners and why. Then commit, push, and pr it.
```

## Execution scope

Write Part 1 only: setup, candidates, method, interim results and known harness faults. Do not name a winner. Part 2 carries the final model, server configuration, tuning, embedding and stability results. Publish from a separate worktree branch because the primary checkout holds unrelated untracked work. No model requests, indexing or service changes are part of this publication.
