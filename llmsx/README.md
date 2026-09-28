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

## `llmsx explorer` — the concept-tree workbench

```bash
pip install 'llmsx[tui]'
llmsx explorer                 # inside an llms-explorer checkout, or clones one to ~/.llmsx/llms-explorer
llmsx explorer --repo ~/src/llms-explorer --no-sync
```

One screen: a collapsible outline of `concept-tree/tree.json` on the left (roots,
children indented, frontier concepts dimmed, `●` on nodes with a pack, `[needs-review]`
badges), and on the right a tabbed Markdown view of the selected concept — *Overview*
(summary, parent, children, skill, marks, your local notes), *Facts* (the pack's facets,
each fact with its source link), *Skill* (SKILL.md), one tab per reference file, and one
tab per llms-family file (`llms.txt`, `llms-full.txt`, `llms-small.txt`, `llms-facts.txt`,
`llms-vocabulary.txt`) when `~/.global-ai-hub/llms-concepts/<slug>.llms/` exists (or
`$LLMSX_CONCEPTS_PATH`). Selecting a node never opens another screen. Everything
rendered is treated as untrusted display text.

| key | does | writes |
|---|---|---|
| `/` `↑↓` `→ ←` | filter (names and aliases); move; expand / collapse in place | — |
| `m` / `f` / `x` | mark needs-review / mark further-research (picks a mode, adds a queue row) / clear | `concept-tree/marks.json`, `concept-tree/RESEARCH_QUEUE.md` |
| `E` | edit the node's summary, aliases, or add a child (a new frontier point) | `concept-tree/tree.json` (other keys untouched) |
| `e` | open the current tab's file in `$EDITOR` | that file |
| `n` | notes for this concept — local only, never committed | `$LLMSX_HOME/notes/<slug>.md` |
| `b` / `B` | toggle the current file into the bundle / export the bundle | `$LLMSX_HOME/bundles/<name>/bundle.md` + `bundle.json` |
| `R` | research this concept: one `claude -p` job (`dr`, `family`, `deep`, `crawl`, `full`) or `queue` only | tree (validated after; snapshot restored on failure) |
| `s` / `c` | `git pull --ff-only` / commit the three allow-listed files and push | the repo |
| `,` | settings: `repo_url`, `push_url`, GitHub token, and *Windows…* to show or hide each pane and tab | `$LLMSX_HOME/config.json` (0600) |
| `t` / `l` | tags for the concept / link it to another concept (clickable in the overview) | `marks.json` tags / `relatedConcepts` in `tree.json` |
| `T` | cycle the outline filter: all · frontier · researched · tagged | — |
| `N` / `M` | new local root / move the concept under another node or a local root | `$LLMSX_HOME/local-tree.json` — never committed |
| `L` | Library: the site's directory of scored llms-full files, blog posts, skills, and your imports, each with a preview; `b` bundles the row's file | — |
| `G` | the access ledger report (`llms_ledger.py report`), by file, kind, project or surface | — |
| `S` | run any skill with `claude -p`: /dr, rabbithole, concept-family-explorer, full-suite, /lca, crawl-to-llms-txt (URL or folder), crawl-repo-to-llms, notes-to-llms-txt (a folder of notes → llms family), memory-to-llms-txt, and every deep optimizer (/ldo, /cdo, /pdo, design, SQL, strategy, skill, /ddo) | whatever the skill writes; the tree is validated after |
| `I` | import an llms file from a local path or an https URL, organised by host or folder | `$LLMSX_HOME/imports/` |
| `W` / `J` | braindump (ctrl+s saves verbatim, ctrl+p parses with the braindump skill) / journal (dated entries; ctrl+p turns the folder into an llms family) | `$LLMSX_HOME/braindumps/`, `$LLMSX_HOME/journal/` |
| `F` / `Q` | flashcards (Leitner boxes) / a multiple-choice quiz over the selected branch | `$LLMSX_HOME/flashcards.json` |
| `X` | export this concept, the whole branch, the current file, or the bundle as markdown | `$LLMSX_HOME/exports/` |
| `[` / `]` | previous / next detail tab; `→` on a leaf and `←` at a root move focus between panes | — |

`E` opens the node's editable fields (summary, aliases, children, linked concepts, tags) in
`$EDITOR` when one is set — vim takes the terminal, save and quit applies, an emptied file
cancels — and falls back to the in-app form otherwise.

`$LLMSX_HOME` defaults to `~/.llmsx`. A bundle is the list of reference, skill, pack and
llms files you want to hand an agent: `bundle.json` is `[{"path", "kind", "concept",
"what", "how", "description"}]` with absolute paths; `bundle.md` is the same list as
bullets an agent can `cat` in order (copied to the clipboard when `pbcopy`/`xclip` exists).

**Token handling.** The token is read from `$LLMSX_GITHUB_TOKEN`, else from the config
file. It reaches git only through a throwaway `GIT_ASKPASS` helper for the one push or
`ls-remote` — never a URL, `.git/config`, argv, or any committed file — and each installed
copy uses its own user's token; the tool ships with none. A commit stages only
`tree.json`, `marks.json` and `RESEARCH_QUEUE.md`, never forces, never rewrites history.
Without the `claude` CLI, `R` offers only `queue`.
