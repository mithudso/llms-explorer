# skill-optimizer changelog

Moved out of `SKILL.md` frontmatter per this skill's own Pass J.1 rule ("no changelog or other non-executing bulk in frontmatter") — the frontmatter is always-loaded on every invocation, and history has no bearing on how the skill runs on a typical one. Newest first.

- "2026-09-14 sko v2.18.0->v2.18.1 — manual review (own quality bar was self-violated: Pass J.1 demands 'no changelog or other non-executing bulk in frontmatter', but frontmatter carried a 5-entry, 602-char changelog array). Extracted the changelog to this file, replaced it in frontmatter with a `changelog_ref` pointer. Mirrored to the `~/.global-ai-hub/skills/skill-optimizer/` twin per Step 1.5's shadowing rule (kept byte-identical to canonical, verified via diff). Not run through the full 15-pass convergence loop — a manual patch, not a certified pass; no hub/registry rebuild attempted (this was a direct file fix, not a `/sko` invocation)"
- "2026-09-09 sko v2.16.1->v2.17.0 — registry backend replaced (tam_* / mdb-context-hub -> global-ai-hub semantic_ops.router); 6 operator-requested fixes applied"
- "2026-08-21 sko v2.16.0->v2.16.1 — Pass H 10/10 pos, 0/10 neg (predicted); 5 Medium fixed"
- "2026-08-21 sko v2.15.1->v2.16.0 — semantic-index step + streaming-checkpoint pointer; 2 Medium fixed"
- "2026-07-20 sko v2.14.0->v2.15.0 — sync mechanics extracted to references/sync-protocol.md; Pass H shadow-by-move fix; 9 Medium fixed"
- "2026-07-20 sko v2.13.0->v2.14.0 — cite-then-restate contradiction fixed; phantom step refs disambiguated; 8 Medium fixed"
