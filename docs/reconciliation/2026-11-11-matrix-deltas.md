# Matrix and streaming retrieval reconciliation

Version: 1.0.1. Delta: detect hashes reused between queries; add library Usage
documentation, native source binding and regression coverage for TASK-1359.

The reviewed pending retrieval changes now use one shared float32 matrix per
database for MCP codebase search and `HubCorpus`. The matrix reads vectors in
batches, observes database/WAL changes, reloads replaced databases, retires deleted
hashes, filters incompatible dimensions and rejects malformed/nonfinite vectors.
On changed snapshots it fingerprints stored model/vector values, then decodes
only new or changed vectors. This also detects GC and re-add of the same hash
between queries, even when SQLite reuses the rowid and the model stays the same.
Equal scores retain descending path order, including ties at the top-k boundary.
NumPy is an explicit runtime dependency; the previously reviewed FastAPI floor
remains intact.

`VecStore.query` streams id/vector rows into a bounded heap and fetches complete
rows only for winners. Both reads use one SQLite snapshot. It preserves kind
filters, scalar cosine, output rounding and malformed-JSON errors. Nonfinite
scores use the legacy full-sort behavior instead of the heap. Nonpositive limits
return no results.

The codebase encoder, docset embedding contracts, revision-aware query cache,
lexical adapters, reranker, LAN configuration and shared lint shim remain intact.
The MCP registry now lists the existing keyword/facts tools, the hub tool count
is corrected, and the SSH example uses placeholders. Incomplete wiki rewrites,
private fleet configuration and unrelated runtime replacements were excluded.

Verification: 80 focused tests passed with MCP-first collection, including synthetic cosine parity,
boundary ties, malformed/nonfinite inputs, WAL refresh, missing vectors,
database replacement, actual writer/GC behavior, compaction, concurrent sharing,
streamed winner reads, concurrent deletion, contracts and lexical fusion. Added
regressions cover unobserved GC/re-add, unchanged-vector decode avoidance and
database replacement between signature inspection and the read snapshot. The
script documentation gate also passes with a library-only Usage example. An
in-memory MCP 2 client listed and called the actual search tool against a
temporary SQLite index. The fixture asserts the reviewed matrix, encoder,
SQLite and corpus module paths and the actual database/encoder used by dispatch.
Maintained-path Ruff, compileall and diff checks passed.
The MCP file has three unchanged pre-existing line-length diagnostics.

Limits: float32 arithmetic can reorder very close scores compared with Python
double arithmetic. Changed-database refreshes read vector text to verify its
fingerprint; this trades read I/O for correct invalidation without changing the
schema or writers. `refresh(force=True)` explicitly reloads even unchanged
values. No live
corpus, model, indexing service or performance benchmark was run. Endor package
risk evidence was unavailable; no package safety verdict is asserted. Combined
integration checks and delivery remain with the parent reconciliation task.
