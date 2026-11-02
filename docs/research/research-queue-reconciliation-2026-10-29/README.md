# Research queue reconciliation — 2026-10-29

Version: 1.0.0

Delta: resolve the queue audit, repair withheld research, and publish the qualified results.

The queue parser now preserves concept names that contain backticks and reads metadata independently of tag order. Duplicate identities retain their original records and all parent contexts. Existing tree membership alone cannot complete research. Held work and coverage reviews remain explicit pending states.

The ranked runner now requires a current independently supported gate before `--retry-reviewed` can retry a review checkpoint. It saves row outcomes atomically from cohort results. The reconciliation helper updates saved outcomes and historical evidence access without rerunning research.

The repaired October 27 MongoDB plan has 29 complete cohorts covering 54 concepts. Nineteen cohorts needed claim or evidence corrections; ten previously accepted cohorts remain unchanged. Four Apple concepts also received corrected evidence and a new all-claim gate. Together the 58 concepts retain 855 canonical claims: 825 selected claims are supported, and 30 ordinary claims remain explicitly not sampled. These counts do not imply that every claim was independently sampled. An independent semantic review caught and closed an additional Apple callback delivery error after a native gate had accepted it.

Seventeen historical completed cohort directories were recovered with file hashes checked before and after restoration. Their legacy gates retain their original qualification. Existing historical pack projections were restored to missing hub paths without regrading their evidence. Failed and superseded gate attempts remain preserved privately.

The hub queue now has 299 unique entries, including 108 pending entries. The repository queue retains its separate broader frontier: 4,651 entries, including 4,588 pending entries. All 694 reservations in the paused suite remain unchanged. Six historical aliases preserve stable slugs and repair the six unresolved parent links. Queue identity mapping does not recertify additional policy assertions.

The synchronized public tree contains 2,203 nodes. The site has 1,881 concept readers and 95,448 facts. Reader JSON, tree/context data, keyword search, downloads and public canonical projections were generated together. Five private nodes remain excluded, and the unfinished Hermes Agent publication remains deferred to its existing draft.

`scripts/reconcile_research_queue.py` reports changes by default. Apply requires a backup directory. It checks fresh input hashes, takes runner/global locks, and journals all writes for rollback. The final repeat run proposed zero changes.

Delta is disabled in saved Claude user configuration. Existing Claude Code sessions need `/reload-plugins --force` to unload the module already in memory. No other plugin was disabled.

Validation includes the complete vendored hub and CLI suites, research script regressions, the full site build and publication policy, an independent claim/pack/publication audit, and the publication privacy scan with the operator's local denylist. Delivery receipts remain in the private continuation record.
