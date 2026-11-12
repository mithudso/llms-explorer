# History-safe trigger projections

The bounded root recheck identified a Medium history-growth defect. Its report
is preserved unchanged. This focused follow-up does not add a SKO iteration or
claim independent convergence.

The shared helper now replays the latest record for each query and honors
retirement. It selects 10 positive and 10 negative queries. Within each class it
prefers the newest explicitly selected rows, then the newest unmarked rows;
explicit exclusions remain ineligible. It preserves all source history and emits
an explicit error if either class has fewer than 10 eligible queries.

All 39 source bundles carry the same portable helper and a documented recipe.
Seventeen post-review helpers were updated; 22 helpers were added where generation
was inline or absent. Existing functional-evaluation caveats remain intact.

Six regression methods and two subtests pass on disposable histories. The same
suite fails the saved representative old helper with three errors. This is one
shared algorithm suite, plus 39 separate bundle-path/parity checks. All 39 checks
pass. Every current source corpus and trigger projection remains byte-identical;
no projection regeneration was required. This does not measure skill activation,
workflow output or empirical promotion.

The JSON receipt binds the exact source files and before/after hashes. Preimages
and explicit new-file absence records remain in the private task state. No global
copy, mirror, provider, live store, service or index was changed by this follow-up.
