---
title: "skill-tree-architect"
description: "Whole-tree architect for a skill library's hub-and-spoke taxonomy — audits description-cap headroom, hub balance, and cross-hub placement, then rebalances for a new family."
order: 4
tags: [taxonomy, skill-tree, rebalancing]
aliasCommand: "skill-tree-architect"
---

Every other skill on this page adds to a skill library one piece at a time —
[concept-family-explorer](/skills/concept-family-explorer/) and
[rabbithole](/skills/rabbithole/) fill in research, [full-suite](/skills/full-suite/)
compiles it into llms-family files. None of them look at the *shape* of the resulting tree.
`skill-tree-architect` does: it audits tree-wide description-cap headroom, hub balance, and
cross-hub placement, then drives the rebalancing toolchain to reshape the tree around a
newly-grown family.

It runs read-only analysis first — placement audit, candidate detection, structural lint —
and surfaces a ranked rebalance plan: which hubs are over their description cap, which
spokes are filed under the wrong hub, which standalone skills need a hub of their own.
Zero-risk, idempotent repairs get applied directly; folding, splitting, and registry sync get
surfaced for human review rather than applied silently.

**Use it for:** "rebalance the skill tree", "is my taxonomy optimal", "the skills folder is a
mess, reorganize it", "find misplaced spokes".

**Not for:** one skill's own content, triggers, or peer-seeds (that's a single-skill audit,
not a tree-shape problem) · deciding what to build next (concept-family-explorer) · a
one-off structural lint of a single file.
