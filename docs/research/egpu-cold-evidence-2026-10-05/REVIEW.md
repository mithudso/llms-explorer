# Bounded supporting-code reviews

Version: 1.0.1
Delta: retain reviewed findings, fixes, counterexamples and independent audit scope separately from hardware qualification.

## Offline build and framing

| Round | Critical | High | Medium |
|---|---:|---:|---:|
|Initial supporting code|0|0|5|
|Reviewed v102 / final framing|0|0|0|
|Fresh-context blind audit|0|0|0|

The five findings were missing parser-hash regression coverage, incomplete declared build input binding, unverified archive replacement integrity, missing timeout/launch-error receipts, and incorrect FORCE_CUBLAS manifest metadata. A successor retains all failed historical outputs and corrects each finding. The v101 successor then refused a missing historical OpenSSL dependency before compilation; v102 explicitly reconciles four obsolete/drifted OpenSSL paths and pins actual version3 link operands. Every other historical input must still match.

Verification: eight builder regressions and eleven framing regressions pass. Independent review checked2,882 declared input pins, all760 compiler dependencies, exact archive member bytes/order/uniqueness, replacement bytes and one linked dispatcher. The fresh blind audit independently ran both regression suites and checked saved code/input hashes and dependency coverage. No review initialized a GPU or executed the diagnostic server.

## Future cold receiver

| Round | Critical | High | Medium |
|---|---:|---:|---:|
|Initial future receiver|0|0|2|
|Corrected renderer and19controls|0|0|0|
|First whole-chain blind audit|0|0|1|
|Runtime alias guard correction and21controls|0|0|0|
|Second fresh final audit|0|0|0|

The cold admission accepted numeric aliases such as `01791136050:203826` for an excluded boot. The first-trial mechanical owner boundary accepted an empty or malformed boot string before later validation. A shared canonical boot-ID validator now protects both boundaries. New regression counterexamples failed before the fix and pass afterward. This tightens admission and does not lower any memory, numerical, tools or research floor.

The three original per-file reviewers used the CDO file passes sequentially within independently delegated scopes. C1–C3, S1–S5, P1–P2, M1, M2, M4, T1 and T4 were recorded, with data/non-test/runtime-only cases marked N/A or partial. Repo M3, T2, T3 and cross-file duplication were assessed for these bounded helpers. No full repository optimizer or universal compiler-process closure was claimed. Existing historical optimizer dissents remain intact.

Original snapshots and consumed receipts remain under:

/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-f32-prefill-preparation-v100
/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-f32-prefill-preparation-v101
/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-renderer-preparation-v106/BACKUP-ITER1

Rollback means abandon the unconsumed future receiver and retain the current owner and all receipts. Do not overwrite sealed historical files or execute an old consumed receiver.

The first whole-chain blind audit independently verified all302pins and retained a Medium about runtime OpenSSL install-name aliases. The correction binds reviewed alias-to-canonical paths and hashes before launch and after readiness. The negative blind receipt remains unchanged.

The final separate-context audit verified all 302 current pins (10,822,817,889 bytes), nested 186/51/35 source maps, direct Mach-O load commands, and 21/21 hermetic cold controls. It approved static preparation for one future experimental cold trial only. The final static review is sealed; actual admission, ABI compatibility, peak, numerics, coding and standard DR remain unverified. All 40 focused builder/framing/cold controls passed again on the public source copies.
