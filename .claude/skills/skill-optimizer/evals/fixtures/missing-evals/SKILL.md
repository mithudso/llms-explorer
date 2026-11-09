---
name: sko-eval-missing-evals
description: "Summarize supplied meeting notes into decisions and actions. TRIGGER: summarize these meeting notes. SKIP: write fiction -> writing-expert."
version: 1.0.0
category: custom
updated: "2026-10-05"
---
# Meeting notes summary fixture

## Process

1. Read the supplied notes. If no notes were supplied, ask once for them.
2. List decisions and actions separately. Preserve any stated owner and due date.
3. Mark absent owners or due dates as unspecified.
4. Return only those two lists. Example: Decision: adopt LF line endings. Action: Lee updates the formatter by Friday.
