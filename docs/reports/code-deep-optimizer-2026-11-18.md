# Code deep optimizer audit, 18 November 2026

The audit started from the deployed UI repair. The optimizer enumerated 931
eligible source files. Fifty received a static syntax and lint screen. Five
received a detailed per-file diagnosis. Fifty-nine initial entries matched
previously reviewed file hashes. The default file cap deferred 822 sources.
The final tracked ledger covers 62 current source hashes, with 869 remaining.
The detailed site-sync review retains an unresolved observability pass and
does not advance that file's ledger hash.

**Status:** partial review coverage. No repository-wide clean verdict.

| Surface | Findings repaired | Verification |
| --- | --- | --- |
| Research evidence and history | Preserve exact CRLF and bare-CR source bytes and Unicode offsets. Skip malformed cached attempt envelopes and continue to older exact reviews. | Research gate suite and independent archived-source and history checks. |
| Site research refresh | Hash the bytes parsed from each tree, resolve scoped aliases to their canonical reader, reject malformed pack slugs, index slug ownership and document the lock prerequisite. | Isolated concurrent-change, alias, and slug regressions. A separate tree writer that changes data after the final guard remains outside the repaired parse/hash race. |
| Research artifacts | Parse UTF-8 JSONL by physical lines and escape the three Unicode separator characters in newly written DR JSONL for existing readers. Declare UTF-8 on compiled pack and privacy-list I/O. | Exact claims and citations survive compilation, revalidation, public projection, site reads and reimport, including under an ASCII locale. |
| Skill registry | Serialize refresh discovery and reconciliation, retain valid aliases on partial reads, share one Codex settings read per lookup, flush cycle receipts and keep completed ingestion accounting when cache refresh fails. | Isolated SQLite and CLI failure regressions. One-shot watch errors exit with status 2. |

The final code passed 1,067 research, script and site tests plus 15 subtests,
and 69 focused skill registry tests. Maintained Ruff checks and all 57 Codex
adapter comparisons passed. The local full Hub test attempt lacked dependencies
in its initial environment. Full package CI is a separate gate. Repository-wide
dependency risk and test parallelization reviews remain open. No model-backed
or embedding evaluation belongs to these code contracts.

The previous [code audit](code-deep-optimizer-2026-11-11-followup.md) records
older API residuals outside this per-file cohort. Continue from the current
[tracked ledger](../../.cdo/ledger.json) and check file hashes before reusing
any prior verdict.
