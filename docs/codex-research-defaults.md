# Codex research defaults

The Codex versions of `/dr`, concept-family-explorer and `/rabbithole` default to
`gpt-6.1-sol` with `medium` reasoning effort. The skill generator preserves this
Codex policy when shared Claude sources change.

| Research depth | Default model and effort | Pass structure |
| --- | --- | --- |
| quick | Sol, medium | One research pass |
| standard | Sol, medium | One research/scout pass; one seeded follow-up when evidence gaps require it |
| saturate | Sol, medium | Two independent research passes, merged |

The merge, scope check and independent claim gate also use Sol/medium. Explicit
`--model` and `--effort` flags remain available. New ranked and MongoDB plans use
Sol/medium; resuming a saved plan retains its recorded settings.

Skill frontmatter documents the orchestrator default. It does not change the
model or effort of an already-running Codex session. The headless runtime applies
the research worker settings explicitly. Active workers retain their loaded code.

Check generated skills without calling a model:

```sh
python3 scripts/sync_codex_research_skills.py --check
python3 -m pytest tests/test_codex_research_skills.py tests/test_codex_ranked_research.py tests/test_mongodb_research_plan.py -q
```
