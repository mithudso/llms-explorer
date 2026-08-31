# LLMS-Explorer site

The Astro site for `docs/site/00-platform-design.md`. Step 1: the reference
tables, the essays, the worked examples and the launch posts, every page with a
`.md` twin, and the site's own `llms.txt` family generated from those twins.
Step 2 adds the concept-tree explorer (`/tree/`, a page per node, `/tree/3d/`),
the directory of known llms files with their conformance grades (`/directory/`,
a page per site) and the recorded retrieval demo (`/demo/`) — all served from
build-time JSON under `src/data/`, no backend. Hosted on Cloudflare Pages.

## Run it locally

```sh
sh hub/bootstrap.sh          # once: hub/.venv with the vendored hub's deps + the hub tests the site uses
cd site
npm install
npm run build                # astro build, then postbuild: tools/twins.py + tools/build_llms.py
npx astro preview            # http://localhost:4321
```

`bootstrap.sh` runs the hub tests the site depends on (`llms_lint`, the
`docset_refine` chain). `sh hub/bootstrap.sh --all-tests` runs the whole
vendored suite, `--no-tests` just builds the venv.

`npm run dev` serves the pages without twins or llms files — those exist only
after a build, under `dist/`.

Tests (pytest, run on the hub venv — `pyyaml` comes from `hub/requirements-dev.txt`):

```sh
cd site && ../hub/.venv/bin/python -m pytest tests -q
```

## The `llmsx` CLI (`llmsx/`, a sibling of `site/`)

`llmsx` is the read-only CLI and Textual TUI over the same generated
`site/src/data/tree.json` this site renders at `/tree/` — component 09's
terminal surface, shipped in step 2. It is a separate installable package, not
part of the Astro build; `site/tools/gen_tree.py` is the only thing they share.

```sh
PYTHONPATH=llmsx hub/.venv/bin/python -m pytest llmsx/tests -q   # from the repo root, no install
hub/.venv/bin/python -m pip install -e 'llmsx[tui]'              # or install it: `tui` extra = Textual
llmsx tree show                                                  # see llmsx/README.md for the rest
```

The CLI has no runtime dependencies, so `PYTHONPATH=llmsx` is enough to import
it; Textual — needed only by the TUI and its parity test — already comes from
`hub/requirements-dev.txt`. CI runs those tests on every push and PR
(`.github/workflows/site.yml`, step "llmsx tests") that way, so no ad-hoc
`pip install` enters the workflow.

## Tools (`site/tools/`)

All run as `hub/.venv/bin/python site/tools/<tool>.py` from the repo root and
are pure functions of their inputs — nothing under `dist/` or the generated
content is hand-edited.

| Tool | Reads | Writes | When |
|---|---|---|---|
| `gen_reference.py` | the `/ldo` rubric in `skills/llms-deep-optimizer/` | `src/content/reference/*.md` (attribute + pass tables, spoke copies) | by hand, when the rubric changes; output is committed |
| `gen_figures.py` | `outputs/exports/*.llms/manifest.json`, lint JSON | `src/data/figures.json` (the numbers the blog cites) | by hand, after a snapshot refresh; output is committed |
| `gen_tree.py` | `concept-tree/tree.json` (the repo's own copy, never `~/.global-ai-hub`) | `src/data/tree.json` (nodes, edges, derived frontier) | `npm run generate`; output is committed, and CI diffs it |
| `gen_directory.py` | `outputs/llms-full/` (catalog, manifest, mirrored files) scored through `hub/scripts/llms_lint.py` | `src/data/directory.json` (a graded entry per site) | `npm run generate`; needs the `outputs/` mirror (not in CI, minutes over ~145 sites) so by hand after a snapshot refresh; output is committed |
| `gen_demo.py` | the live hub's docset indexes (keyword + vector) | `src/data/demo.json` (the three retrieval legs per golden question) | **run by hand on the M5** — it needs the live hub, so it is never in `generate` or CI; output is committed and the page is labelled with its recording date |
| `twins.py` | `src/content/**/*.md`, `dist/` | `dist/**/*.md` twins + `dist/_headers` | `postbuild` |
| `build_llms.py` | the twins in `dist/`, `llms.overrides.json` | `dist/llms.txt`, `llms-full.txt`, `llms-small.txt`, `llms-facts.txt`, `llms-vocabulary.txt`, `manifest.json`; refreshes `_headers` | `postbuild` |

Refresh the committed data with one command (from `site/`):

```sh
npm run generate             # gen_reference.py, gen_tree.py, gen_directory.py
```

`gen_demo.py` is deliberately not in it: it queries the live hub's indexes, so
it is run by hand on the M5 and its `src/data/demo.json` committed. CI has
neither the live hub nor `outputs/`, so it can only re-run `gen_tree.py` — which
is why `tree.json` alone is diffed for staleness there.

`build_llms.py` writes a banner mirror of the twins into `.llms-work/` and runs
the vendored `docset_refine` chain over it (`clean → extract → render →
export`, plus the vocabulary pass) — no model tokens, so the family is
reproducible in CI.

## `llms.overrides.json`

The only hand input to the site's llms family (master principle 2: generated,
never hand-edited). Keys: `title`, `summary`, `section_order`. Everything else
— page descriptions, facts, vocabulary, token counts — comes from the built
pages. Edit this file, rebuild, and the family follows.

## Twins and headers

Every content page `/x/y/` has a twin at `/x/y.md`, served as
`text/markdown; charset=utf-8` with `X-Markdown-Tokens: <count>` and
`Link: </llms.txt>; rel="describedby"`. The rules live in `dist/_headers`,
written by `twins.py` and extended by `build_llms.py` for the `llms*.txt`
files. `public/_headers` is not used — the file is generated into `dist/`.

## Cloudflare Pages settings

| Setting | Value |
|---|---|
| Production branch | `main` |
| Root directory | `site` |
| Build command | `sh ../hub/bootstrap.sh --no-tests && npm run build` |
| Build output directory | `dist` |
| Environment variable | `SITE_URL` = the production URL — `https://llms-explorer.com` (the custom domain; `llms-explorer.pages.dev` stays as the project's built-in preview host). Also the default in `astro.config.mjs` and `tools/twins.py`. |
| Node version | 22 (`engines.node` in `package.json`) |

`npm run build` alone is not enough: `postbuild` runs the twin and llms tools
on `../hub/.venv`, which only exists after `hub/bootstrap.sh`. That is why the
build command bootstraps first (`--no-tests`: Pages builds the site, CI runs
the tests). The build image must have `python3`.

| GitHub secret | Why |
|---|---|
| `PROMOTE_TOKEN` | a bot PAT with `contents:write`, used by the `promote` job. With the default `GITHUB_TOKEN` the fast-forward to `main` still lands but does not re-trigger Actions, so the main-only link check never runs on a promoted commit. |

`outputs/` (the docset exports, the llms-full mirror, topical outputs — ~838
MB, with files over Pages' per-asset cap) is **read at build time and never
deployed** (master §8). `gen_figures.py` reads it to produce the committed
`src/data/figures.json`; nothing under `outputs/` is copied into `dist/`.

## CI (`.github/workflows/site.yml`)

On every push to `main` / `snapshot`, every pull request, the daily
`schedule` run and `workflow_dispatch`:

1. `sh hub/bootstrap.sh` — venv, deps, the hub tests the site depends on
2. `cd site && npm ci && npm run build` (with `SITE_URL`) — pages, twins, llms family
3. `pytest site/tests`
4. `gen_tree.py --out "$RUNNER_TEMP/tree.json"` + `diff` against
   `src/data/tree.json` — a stale committed copy fails the run, which is what
   keeps "generated, never hand-edited" true. `gen_directory.py` (needs the
   `outputs/llms-full` mirror) and `gen_demo.py` (needs the live hub) cannot run
   in CI and are refreshed by hand
5. `llms_lint.py check` over all five llms files with `--json` — **exit 1 on
   any High finding** fails the run
6. `--check-links` on `main` only (needs the network and the deployed site):
   advisory on a push, because Pages is still deploying that same commit;
   blocking on the daily `schedule` run and on `workflow_dispatch`
7. `site/dist` uploaded as the `site-dist` artifact

Snapshot promotion (master §8): the daily refresh pushes `HEAD:snapshot`; the
`promote` job (`needs: build`, snapshot only, `success()`) fast-forwards `main`
with `git push origin HEAD:main` — no `--force`, so a diverged `main` fails
loudly instead of being overwritten. Pages deploys `main`. Configure
`PROMOTE_TOKEN` (above) if the promoted commit should re-run this workflow for
the link check.
