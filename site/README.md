# LLMS-Explorer site

The Astro site for `docs/site/00-platform-design.md` step 1: the reference
tables, the essays, the worked examples and the launch posts, every page with a
`.md` twin, and the site's own `llms.txt` family generated from those twins.
Hosted on Cloudflare Pages.

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

## Tools (`site/tools/`)

All run as `hub/.venv/bin/python site/tools/<tool>.py` from the repo root and
are pure functions of their inputs — nothing under `dist/` or the generated
content is hand-edited.

| Tool | Reads | Writes | When |
|---|---|---|---|
| `gen_reference.py` | the `/ldo` rubric in `skills/llms-deep-optimizer/` | `src/content/reference/*.md` (attribute + pass tables, spoke copies) | by hand, when the rubric changes; output is committed |
| `gen_figures.py` | `outputs/exports/*.llms/manifest.json`, lint JSON | `src/data/figures.json` (the numbers the blog cites) | by hand, after a snapshot refresh; output is committed |
| `twins.py` | `src/content/**/*.md`, `dist/` | `dist/**/*.md` twins + `dist/_headers` | `postbuild` |
| `build_llms.py` | the twins in `dist/`, `llms.overrides.json` | `dist/llms.txt`, `llms-full.txt`, `llms-small.txt`, `llms-facts.txt`, `llms-vocabulary.txt`, `manifest.json`; refreshes `_headers` | `postbuild` |

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
| Environment variable | `SITE_URL` = the production URL (default in `astro.config.mjs`: `https://llms-explorer.pages.dev`) |
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
4. `llms_lint.py check` over all five llms files with `--json` — **exit 1 on
   any High finding** fails the run
5. `--check-links` on `main` only (needs the network and the deployed site):
   advisory on a push, because Pages is still deploying that same commit;
   blocking on the daily `schedule` run and on `workflow_dispatch`
6. `site/dist` uploaded as the `site-dist` artifact

Snapshot promotion (master §8): the daily refresh pushes `HEAD:snapshot`; the
`promote` job (`needs: build`, snapshot only, `success()`) fast-forwards `main`
with `git push origin HEAD:main` — no `--force`, so a diverged `main` fails
loudly instead of being overwritten. Pages deploys `main`. Configure
`PROMOTE_TOKEN` (above) if the promoted commit should re-run this workflow for
the link check.
