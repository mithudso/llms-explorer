# llmsx

A dependency-free, read-only CLI and an optional Textual TUI over the
llms-explorer concept tree and llms-concept-abstractor concept packs.

```bash
llmsx tree show                     # indented tree, frontier marked ·
llmsx tree show "LLMs.txt" --depth 2
llmsx tree detail <slug>            # one node's fields
llmsx tree search caching           # concept + alias substring
llmsx tree frontier [slug]          # named but never researched
llmsx tui                           # the Textual tree browser (pip install 'llmsx[tui]')
```

Data comes from the site's generated `site/src/data/tree.json`
(`site/tools/gen_tree.py`). Override with `--data <path>` or `$LLMSX_TREE`.
Step 3 adds `--api <url>` serving the same shape.

## Concept packs (`llmsx concepts`)

A *different* data model from the tree above: a concept pack is a directory
`<slug>.llms/` built by the `llms-concept-abstractor` skill (`/lca`) or
`llms-deep-optimizer --family` (`/ldo`), each with its own `manifest.json`,
`concept-graph.json` and llms-family markdown files.

```bash
llmsx concepts list                 # catalog every pack — summary, useful_for, related terms
llmsx concepts list --query caching # substring filter over name/summary/related terms
llmsx concepts show <slug>          # one pack's summary, facets, related terms, files
llmsx concepts serve <slug>         # llms.txt to stdout — pipeable: > out.md
llmsx concepts serve <slug> --file llms-full.txt
llmsx concepts tui                  # the Textual concept-pack browser (pip install 'llmsx[tui]')
```

`<slug>` may be an exact slug or a case-insensitive substring of the slug or
concept name; an ambiguous substring lists its candidates instead of
guessing. `serve --file` accepts one of `llms.txt`, `llms-full.txt`,
`llms-small.txt`, `llms-facts.txt`, `llms-vocabulary.txt`,
`concept-graph.json`, `manifest.json`.

Data comes from `~/.global-ai-hub/llms-concepts` by default. Override with
`--data <path>` (under `concepts`) or `$LLMSX_CONCEPTS_PATH` — a *different*
env var from `$LLMSX_TREE` above, because it is a different data model.

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

`llmsx family <topic>` and `llmsx optimize <file-or-text>` are thin CLI
wrappers over `run_skill` for `concept-family-explorer` and
`llms-deep-optimizer` respectively (needs `pip install 'llmsx[skills]'`).
Both print a one-line disclaimer to stderr before the model's output: this is
one model turn against the skill's instructions, not its full multi-pass
loop.

## Parity with the hub-manager Concepts tab

Two different things share the name "Concepts" here, deliberately kept apart:

- `llmsx tui`'s `ConceptBrowser` walks the SEO research tree (`tree.json`,
  above) — a `Tree` widget, a filter `Input` widened to aliases, a detail
  `RichLog`, frontier concepts drawn dim italic with a `(frontier)` label.
  Its two write actions — queue a concept, launch research — are absent:
  they mutate the hub, which this read-only package cannot reach. They
  arrive in step 3, over the API.
- `llmsx concepts tui`'s `ConceptPackBrowser` is the actual port of
  `~/.global-ai-hub/scripts/hub_manager/app.py`'s `TabPane("Concepts"`: a
  `DataTable` listing concept packs, the same filter-by-slug/name/summary
  behaviour, a detail `RichLog` with summary/facets/related terms/files, and
  an "edit in `$EDITOR`" action. Indexing is not ported — it depends on
  `docset_indexer.py`, ChromaDB and an Ollama pool, hub-specific heavy
  dependencies this package does not carry; the Index button says so.
