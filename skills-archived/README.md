# Legacy skill archives

Version: 1.0.0
Delta: Record the four legacy root copies in the 20261108T231500Z snapshot.

The `20261108T231500Z` archive preserves 16 files from the root `skills/` tree byte for byte. Its manifest lists each former path, archived path and SHA-256 digest. These are historical copies; the archive is not a skill discovery root.

| Skill | Active canonical file |
| --- | --- |
| deep-strategy-optimizer | `.claude/skills/deep-strategy-optimizer/SKILL.md` |
| design-deep-optimizer | `.claude/skills/design-deep-optimizer/SKILL.md` |
| notes-to-llms-txt | `.claude/skills/notes-to-llms-txt/SKILL.md` |
| used-car-buying | `.claude/skills/used-car-buying/SKILL.md` |

The site prompt pages read `.claude/skills/<id>/SKILL.md`. LLMSX searches `.claude/skills/` by default. Both retain the active files above. Consumers that explicitly configured a former `skills/<id>` path must select the canonical directory. Repository-wide third-party discovery can include an archive when it searches every directory; use an explicit `.claude/skills/<id>` installation URL to choose the active version.

To restore a historical root copy, copy its directory from `20261108T231500Z/` back to `skills/`. Do not replace an active canonical skill with an archived copy.
