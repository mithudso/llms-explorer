# llmsx

A CLI and an optional Textual TUI over the llms-explorer concept tree and
llms-concept-abstractor concept packs, plus a thin invocation layer over the
Claude skills SDK.

**Scope, precisely.** `llmsx tree …` and `llmsx concepts list/show/serve` are
read-only and install with zero third-party dependencies. `llmsx tui` and
`llmsx concepts tui` need the `tui` extra; the concept-pack TUI's "edit"
action opens `$EDITOR` on a pack file, which is a write. `llmsx family` and
`llmsx optimize` need the `skills` extra and make an outbound network call to
a model provider — see "Running a skill" below for exactly what that call
does and does not do.

## Install

```bash
pip install llmsx                 # tree + concepts list/show/serve only
pip install 'llmsx[tui]'          # + the Textual browsers
pip install 'llmsx[skills]'       # + `llmsx family` / `llmsx optimize`
```

## Browsing the concept tree (`llmsx tree`)

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
A future release may add `--api <url>` serving the same shape from a live
service instead of a checked-out file.

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
env var from `$LLMSX_TREE` above, because it is a different data model. Put
`--data` after `concepts` (or its subcommand); a top-level `--data` before
`concepts` binds to the tree's flag instead and `llmsx` refuses to run
rather than silently falling back to the default concept-packs directory.

## Development

Install for development from a checkout of this monorepo:

```bash
cd llmsx && ../hub/.venv/bin/python -m pip install -e '.[dev]'
```

Prefer the installed `llmsx` command. `python -m llmsx` also works, except from
the directory that *contains* this project folder (the repo root): there the
`llmsx/` directory itself shadows the installed package as a namespace package.
`llmsx …` and `pytest llmsx/tests` are unaffected — `llmsx/pyproject.toml`'s
`[tool.pytest.ini_options]` puts this package's own directory on `sys.path`
regardless of where `pytest` is invoked from.

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

Search order: `$LLMSX_SKILL_PATH` (`os.pathsep`-joined) first when set, then
*every* `skills/` directory at or above the current working directory —
nearest first, not just the nearest one — then `~/.claude/skills` last. That
matters: it means `llmsx family` / `llmsx optimize`, run from inside any
directory that happens to contain a `skills/<name>/SKILL.md`, will run
*that* file's instructions rather than a global copy. `_run_skill_cli`
prints the resolved `SKILL.md` path to stderr before every call for exactly
this reason — a `SKILL.md` is not automatically trusted input, and this is
the way to notice a shadowed or planted one before it runs. Pass
`include_references=True` to append the skill's `references/*.md` to the
system prompt (bounded — see `Skill.read_references`'s docstring).

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

## The two Textual browsers, and which hub screen each one is (or isn't)

Two different things share the name "Concepts" here, deliberately kept apart:

- `llmsx tui`'s `ConceptBrowser` walks the SEO research tree (`tree.json`,
  above) — a `Tree` widget, a filter `Input` widened to aliases, a detail
  `RichLog`, frontier concepts drawn dim italic with a `(frontier)` label.
  It has no hub counterpart to port: it is a from-scratch, read-only browser
  over data this package already owns, with no write path (there is nowhere
  for it to write to — see "Scope, precisely" above).
- `llmsx concepts tui`'s `ConceptPackBrowser` *is* the actual port of
  `~/.global-ai-hub/scripts/hub_manager/app.py`'s `TabPane("Concepts"`: a
  `DataTable` listing concept packs, the same filter-by-slug/name/summary
  behaviour, a detail `RichLog` with summary/facets/related terms/files, and
  an "edit in `$EDITOR`" action. Indexing is not ported — it depends on
  `docset_indexer.py`, ChromaDB and an Ollama pool, hub-specific heavy
  dependencies this package does not carry; the Index button says so.
