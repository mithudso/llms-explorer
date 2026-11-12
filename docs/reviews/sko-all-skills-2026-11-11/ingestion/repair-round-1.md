# Ingestion bounded repair

Repaired all seven corroborated blind findings and the additional distribution-path issue. Fresh independent recheck is pending; the original blind report is unchanged.

| Finding | Level | Repair and evidence |
|---|---|---|
| BI-ING-001 | Medium | Parsed YAML identifiers and aliases remain whole; folding occurs only between complete tokens. test_routing_surface.py: 15 passing checks; the saved preimage produced 13 failures. |
| BI-ING-002 | Medium | Customer selfcheck accepts the required family sitemap and the single-file shape; it applies the corresponding file requirements and byte caps. test_selfcheck.py: 5 pass, including family+sitemap, single without siblings, missing sitemap and JSON credential counterexamples; preimage 4 failed/1 passed. |
| BI-ING-003 | High | Directory/glob expansion checks resolved containment before reads, deduplicates resolved identities and records rejected/duplicate/missing/unreadable inputs. Two directory/glob outside-symlink fixtures and the real-file alias fixture pass; before repair all three failed. |
| BI-ING-004 | Medium | The compiler budgets the fully rendered small digest, preserves complete source units and every facet, and raises before replacement if the selected minimum cannot fit. Three budget/rollback cases pass; a short-final-row case also prevents rejecting a complete facet whose omission notice costs more. All inputs are synthetic/private. |
| BI-ING-005 | Medium | The normalizer emits a body-free, root-qualified source_statuses ledger with empty, duplicate-of, unsupported, unreadable, outside-root and hidden dispositions. Two per-input/serialized-inventory ledger regressions pass; both failed on the saved preimage. |
| BI-ING-006 | Medium | Worked topical facts place the URL immediately after the em dash; no literal source: token remains in either example. Both extracted worked rows pass bundled P7 source grammar; the original recipe caused a High finding. |
| BI-ING-007 | Medium | The reference and main procedure distinguish valid headingless bare URLs from present broken fragments; only the latter count against the R3 threshold. The bundled checker accepts /fixture/plain.md with no heading and rejects its invented #top fragment. This helper already passed before the prose repair; the contradictory baseline quote is preserved in the original blind report. |
| INTEGRATION-PATH-001 | Medium | Tests resolve an explicit LLMS_EXPLORER_REPO or discover repository markers, and missing required helpers fail instead of skipping. Both source and legacy distribution layouts run from isolated staged copies with zero skips. The same preimage layout checks failed because five interop tests silently skipped. |

61 offline tests passed with zero skips. Both source and legacy distribution paths were exercised through temporary copies. Existing private-compile suppression and default/public completion-hook dispatch tests still pass; no live publication ran.

Ruff F401/F821, YAML/JSON/corpus bindings, Python syntax and scoped diff checks pass. Trigger verdicts remain predictions. Full before/after hashes and individual executed test results are in `repair-round-1.json`; preimages and raw failure output stay private.

No staging, commit, global sync, index rebuild, service start or external-source workflow occurred.
