# prompt-deep-optimizer — archived changelog

Entries older than `SKILL.md`'s frontmatter `metadata.changelog` 5-entry window (Pass J, skill-optimizer audit 2026-08-21). `SKILL.md` keeps the 5 most recent entries; this file holds everything before that. Newest archived entry first.

2026-06-11 v2.3.0 — 2026-06-11 family-audit implementation: worked examples extracted to references/worked-examples.md; blind re-audit gate (6a0) on CLEAN exits; 5-field intent checklist with finding-justified deltas (6a, Step 4, glossary); behavioral smoke test (6a2) + fourth success criterion; cross-model gate stub (6a.5, default OFF); small-artifact profile (<~600 tokens, 3 merged groups, cap 3); Step 5 exit condition 7 (--budget-minutes / BUDGET_EXHAUSTED) + best-of-pool delivery on non-clean exits; convergence_check.py cited for edit distance (fabricated percentages removed); subagent timeout language fixed to error/empty-result; Pass O skip-row Medium conditioned on absent self-check; GEPA row corrected (Agrawal et al. 2025, arXiv:2507.19457) + canonical KB pointer; variant registration (6b item 9) + telemetry citing line; composed-artifact scoping in Step 1; ~600-token /ph tiebreaker + /pdo command shim + --max-iter outer-loop support; duplicate metadata.version field removed (top-level version is the single source of truth)

2026-05-31 v2.2.1 — patch release; changelog entry reconstructed 2026-06-11 (the original v2.2.1 line was missing — see audit rec progressive-disclosure-split)

2026-05-29 v2.2 — applied pdo self-audit iter 1: PII/secret redaction, injection-targeting-auditor gate, content-cycle detection, self-check concrete list, clarifying-question default, subagent timeout, citation task-gate, thinking-budget model list, engine-agnostic conditionals, fallback-chain pattern, Pass P pipeline-cache scoping

2026-05-29 v2.1 — applied skill-optimizer findings: fragment+jailbreak gates, terminology definitions, model-conditional Pass K, BLOCKED status column, Step 6 reordering, sibling-skill handoff
