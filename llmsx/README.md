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

## Parity with the hub-manager Concepts tab

`llmsx tui` mirrors `~/.global-ai-hub/scripts/hub_manager/app.py`'s Concepts
tab: the `Tree` widget, the filter `Input` that shows only matching branches
(here widened to aliases), the detail `RichLog`, and frontier concepts drawn
dim italic with a `(frontier)` label. Its two write actions — `n` queue a
concept, `R` launch research — are deliberately absent: they mutate the hub,
which this read-only package cannot reach. They arrive in step 3, over the API.
