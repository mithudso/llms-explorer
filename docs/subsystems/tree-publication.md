---
title: API tree publication
type: subsystem
created: 2026-11-11
updated: 2026-11-11
sources:
  - code: api/explorer_api/tree_publication.py
  - code: api/explorer_api/moderation.py
  - code: api/explorer_api/trees.py
  - code: api/explorer_api/routes/proposals.py
verified_at: c458299c
---

# API tree publication

The public tree file stays canonical. `trees.py` reads one byte snapshot for a
fork and its SHA. `moderation.py` parses and hashes the same snapshot before
applying a proposal. API writes serialize JSON in the hub's format without
calling the hub's website-refresh hook.

`tree_publication.py` coordinates cooperating API writers with a stable
`.tree.json.lock` advisory lock. Synchronous writers refuse a busy lock instead
of blocking the API event loop. Async decision writers can wait cancellably.

A decision writes an owner-private `.tree.json.publication.json` journal before
replacing the tree. The journal binds the proposal ID and before/after bytes
and hashes. The caller owns the SQL transaction; its outer commit or rollback
finalizes the journal and releases the lock. Nested SAVEPOINT completion does
not finalize the outer publication.

Callers that accept a proposal must use the coordinated commit path:

```python
proposal = await moderation.decide(session, moderator, proposal_id, accept=True)
await moderation.commit_decision(session)
```

After an interrupted or ambiguous commit, the next decision acquires the lock
and reads the proposal's durable status through a fresh database session. It
keeps or restores the bound bytes only when the file still matches the recorded
before/after state. Unknown decisions, invalid journals and unrelated file edits
fail closed for explicit recovery. Preserve the journal while investigating;
do not delete it to force a retry.

This is recoverable coordination between PostgreSQL and a file. Public readers
may briefly see staged bytes before commit. External writers that do not use
this lock remain outside its concurrency guarantee. Tests use temporary files
and isolated PostgreSQL, including separate-process recovery and contention.
