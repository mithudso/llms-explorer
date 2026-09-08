---
title: "Claude Code Skills"
description: "Reference for the Claude Code skills ecosystem — anatomy, authoring, discovery, distribution, management, composition, and optimization. Backed by references/claude-code-skills-context.md."
---

# Claude Code Skills Expert

Reference for the Claude Code skills ecosystem — anatomy, authoring, discovery, distribution, management, composition, and optimization. Backed by `references/claude-code-skills-context.md`.

## When NOT to use

- Plugin packaging, hook configuration, or agent definitions → use `claude-code-plugins`
- Searching the prompts.chat registry to find and install an existing skill → use `skill-lookup`
- Creating a brand-new skill interactively from a description → use `skill-creator`
- Optimizing trigger accuracy, fixing over-triggering, or improving prose quality of an existing skill → use `skill-optimizer`

## Quick reference

### SKILL.md structure

```
---
name: kebab-case-name
description: Verb-first, 1-3 sentences, include trigger phrases and exclusions
origin: local
---

# Skill Title

## When to use this skill
- Specific trigger conditions

## Instructions / Reference content
```

### Key frontmatter fields

| Field | Purpose |
|---|---|
| `name` | Max 64 chars, kebab-case (required) |
| `description` | Max 1,024 chars — the primary activation signal |
| `disable-model-invocation` | `true` to prevent auto-triggering from the description — skill only runs when the user explicitly types `/skill-name` |
| `user-invocable` | `false` to hide from slash menu |
| `allowed-tools` | Pre-approve tools for this skill's execution |
| `context` | `fork` for isolated subagent execution |
| `agent` | Target agent type (e.g., `Explore`) |
| `hooks` | Skill-scoped lifecycle hooks |
| `paths` | Glob patterns limiting activation to matching files |

### Skill precedence (highest to lowest)

1. Enterprise managed settings
2. Personal (`~/.claude/skills/`)
3. Project (`.claude/skills/`)
4. Plugin (`plugin-name:skill-name`)

### Marketplace comparison

| Marketplace | Size | Security | Best for |
|---|---|---|---|
| Anthropic Official | ~20 | Verified by Anthropic | Trust-first installs |
| Agensi | 200+ | 8-point security scan | Vetted + creator payments |
| ClaudeSkills.info | 658+ | Community-vetted | Free, quality community skills |
| Skills.sh | ~2,000 | No audit | CLI-first, npm-style workflow |
| SkillsMP | 800K+ | No audit | Discovery only — audit before use |

### Security checklist

- Run `uvx mcp-scan@latest --skills` before installing unknown skills
- 36.8% of scraped skills have security flaws (Snyk ToxicSkills, Feb 2026)
- 13.4% contain critical vulnerabilities; 76 confirmed malicious payloads found
- Prefer Anthropic Official or Agensi-vetted skills for production use

## Full reference

For complete coverage of all frontmatter fields, token budget management, skillOverrides, CI/CD integration, and skill composition patterns, read `references/claude-code-skills-context.md` in this directory.
