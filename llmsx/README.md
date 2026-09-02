# llmsx

A dependency-free, read-only CLI and an optional Textual TUI over the
llms-explorer concept tree.

```bash
llmsx tree show                     # indented tree, frontier marked ·
llmsx tree show "LLMs.txt" --depth 2
llmsx tree detail <slug>            # one node's fields
llmsx tree search caching           # concept + alias substring
llmsx tree frontier [slug]          # named but never researched
llmsx tui                           # the Textual browser (pip install 'llmsx[tui]')
```

Data comes from the site's generated `site/src/data/tree.json`
(`site/tools/gen_tree.py`). Override with `--data <path>` or `$LLMSX_TREE`.
Step 3 adds `--api <url>` serving the same shape.

Install for development:

```bash
cd llmsx && ../hub/.venv/bin/python -m pip install -e .
```

## Running it

Prefer the installed `llmsx` command. `python -m llmsx` also works, except from
the directory that *contains* this project folder (the repo root): there the
`llmsx/` directory itself shadows the installed package as a namespace package.
`llmsx …` and `pytest llmsx/tests` are unaffected.

## Running a skill (`llmsx.skills`)

`llmsx.skills` loads a `SKILL.md` — this repo's `skills/<name>/` or
`~/.claude/skills/<name>/` — and runs it against a model.

```python
from llmsx.skills import available_skills, load_skill, run_skill

available_skills()                       # every skill on the search path
skill = load_skill("notes-to-llms-txt")  # SkillNotFoundError lists the paths tried
skill.description, skill.model           # frontmatter; `model` is the skill's own default

run = run_skill(skill, "…my messy notes…")     # needs pip install 'llmsx[skills]'
run = run_skill(skill, "…", client=my_client)  # or inject any transport
print(run.text, run.model, run.usage)
```

Search order: `$LLMSX_SKILL_PATH` (os.pathsep-joined), then the nearest
`skills/` at or above the cwd, then `~/.claude/skills`. Pass
`include_references=True` to append the skill's `references/*.md` to the
system prompt.

`client` is anything with `.messages.create(**kwargs)` (the Anthropic SDK
shape) or a plain callable taking the same kwargs — the callable form is how
the tests run offline, and how a caller stubs, records or caches a call
without importing the SDK.

**What this is not.** A thin invocation layer: one model turn, carrying the
skill's instructions verbatim. The skills themselves describe multi-pass
loops, subagent fan-out, filesystem locks and concept-tree writes — behaviour
belonging to an agent harness with tools. `run_skill` drives none of it; a
caller who needs the loop drives it. The JS sibling (`../llmsx-js`) has the
same API and the same boundary.

## Parity with the hub-manager Concepts tab

`llmsx tui` mirrors `~/.global-ai-hub/scripts/hub_manager/app.py`'s Concepts
tab: the `Tree` widget, the filter `Input` that shows only matching branches
(here widened to aliases), the detail `RichLog`, and frontier concepts drawn
dim italic with a `(frontier)` label. Its two write actions — `n` queue a
concept, `R` launch research — are deliberately absent: they mutate the hub,
which this read-only package cannot reach. They arrive in step 3, over the API.
