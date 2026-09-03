# skill-tree-architect — changelog

Full version history. `SKILL.md` frontmatter `metadata.changelog` keeps only the most recent
entries (capped at 5 per the sko sync protocol); this file is the durable record.

- **2026-07-20 v1.3.0 → v1.4.0:** sko full-profile optimization run (four fix rounds, incl.
  blind-gate remediation: snapshot-not-git recovery claim corrected, crossroute invocation
  documented, referents --status added to the tool-failure rule).
  Routing surface: description tightened (876 → 855 chars, TRIGGER moved to char 250,
  terse/casual anchors added: "skill-tree health check", "skills folder is a mess"); "triggers"
  folded into the skill-optimizer SKIP edge; script SKIP targets rephrased as direct-run tools
  (detect-candidates.mjs, meta-validate.mjs); dangling `skill-hub-autodetect` reference dropped
  from whenNotToUse. Correctness: meta-validate hard-gate list corrected (only spoke-copy +
  dangling-row + frontmatter/naming/manifest errors gate; circular SKIP / description cap /
  tier-config are non-gating Medium); two-tier cap relabeled by severity+cause (>1000 = Medium
  Glean import cap, >1536 = High harness truncation), replacing the overloaded soft/hard labels;
  audit-placement single-cap semantics documented (run at 1000, derive >1536 from descLen) and
  `--desc-cap 1000 --json` pinned in baseline + Phase-4 recapture; PROBE-DISSENT re-attributed
  as this skill's analog of the contract's BLIND-AUDIT-DISSENT; probe seeding aligned to the
  5–10 CQ corpus shape. Coverage: standalone desc-cap sweep added (audit-placement caps hubs
  only); healthy-tree zero-item exit defined; Phase-1 tool-failure rule; Phase-3 explicit-go
  defined; Phase-3 mid-run failure rail; Phase-4 step 1 split into gates 1a–1d; "very high
  spoke count" made concrete (≥14, audit-placement `HIGH_SPOKES`). Structure: Phase-3 step
  detail extracted to `references/apply-procedure.md` (55.7% of body was dormant apply detail;
  now 44.1%); changelog history extracted to this file; em-dash density brought under 1/100
  words; `model`/`effort` frontmatter keys added (claude-opus-4-8 / xhigh).
- **2026-06-28 v1.2.0 → v1.3.0:** Phase 3 step 9 + Phase 4 step 1 gate: regenerate the
  consolidated SKILLS-INDEX (node gen-skills-index.mjs) after the tree mutates, then --check it
  in VERIFY, so the cross-family index never drifts after a rebalance.
- **2026-06-11 v1.1.0 → v1.2.0:** Phase 3 step 4 fold now names the deterministic command:
  tier.mjs --demote <spoke> --apply (targeted demote flag added to tiering/tier.mjs this pass;
  previously only idle/LRU triggers could demote).
- **2026-06-11 v1.0.0 → v1.1.0:** canonical-contract adoption: tiering-aware folds (tier.mjs
  demote, never raw rm), full crossroute re-file sequence, snapshot+rollback, tree-health
  telemetry, contract exit statuses, two-tier desc cap (sko Pass M); concept-tree crosswalk
  (adjudicate, targeted queries); CQ-corpus probe replay in Phase 4.
- **v1.0.0:** initial: whole-tree ANALYZE / PLAN / APPLY / VERIFY orchestrator over the
  skill-consolidation toolchain.
