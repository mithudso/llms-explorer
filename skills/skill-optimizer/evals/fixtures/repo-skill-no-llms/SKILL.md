---
name: sko-eval-repo-skill-no-llms
description: "Review a git repository's module layout and list dead code. TRIGGER: find dead code in this repo. SKIP: write new features -> code-deep-optimizer."
version: 1.0.0
category: custom
---
# Repo dead-code reviewer

Walk the repository tree, read each source file, and list functions that nothing calls. Report path:line for each.
