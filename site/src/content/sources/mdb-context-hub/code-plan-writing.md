---
title: "Code Plan Writing"
description: "Translating a specification, requirement, or feature request into a structured sequence of implementable tasks."
---

# Code Plan Writing

Translating a specification, requirement, or feature request into a structured sequence of implementable tasks.

**Break-even point:** any change touching 4+ files, any refactor with a coherent end state.

## Output Format

Every plan document must contain these sections in order:

1. **Header** — Feature name, one-sentence goal, architecture summary, tech stack
2. **File Map** — Table: Action (Create/Modify/Delete) | File path | Responsibility
3. **Tasks** — Numbered blocks with checkbox steps, exact code, commands, and expected outputs
4. **Validation** — Per-task done criteria + overall acceptance criteria
5. **Not In Scope** — Explicit list of excluded work

**Delivery:** Save to `docs/plans/YYYY-MM-DD-&lt;feature-slug&gt;.md` unless the user specifies otherwise.

## Plan Document Formats

### Implementation Plan (for execution)
```markdown
# [Feature] Implementation Plan

## File Map
| Action | File | Responsibility |
|--------|------|---------------|

## Task 1: [Component Name]
- [ ] Write failing test
- [ ] Run test, confirm failure
- [ ] Implement minimal code
- [ ] Run test, confirm pass
- [ ] Commit
```

### ExecPlan (for AI agents)
Self-contained documents for autonomous multi-hour execution. Required sections: Purpose, Progress (timestamped checkboxes), Surprises & Discoveries, Decision Log, Context & Orientation, Concrete Steps (exact commands + expected outputs), Validation & Acceptance, Idempotence & Recovery.

## Key anti-patterns

- **Planning Without a Spec** — Plan solves the wrong problem
- **Placeholder Steps** — Defers decisions to the implementer
- **Monolith Tasks** — Tasks touching 10+ files are decomposition failures
- **Plan-Then-Forget** — Plan becomes fiction when reality diverges
