---
title: "uv — The Unified Python Toolchain"
description: "uv is an extremely fast Python package and project manager written in Rust by"
---

# uv — The Unified Python Toolchain

`uv` is an extremely fast Python package and project manager written in Rust by
Astral (the Ruff team). It is a single static binary that consolidates the jobs
previously spread across `pip`, `pip-tools`, `virtualenv`/`venv`, `pyenv`,
`pipx`, `poetry`, `twine`, and `build` — typically **10-100x faster** than the
`pip`/`pip-tools` baseline. This reference covers the five pillars named in the
brief: **project/workspace management**, the **universal lockfile**,
**Python-version install/pinning**, the **tool/pipx replacement**, and the
**pip-compatible interface** — plus the build backend, PEP 723 scripts, and
configuration/caching.

> For everyday Python idioms, async, typing, and a uv quick-start cheat sheet,
> see `references/python-patterns.md`. For static type checkers (mypy/Pyright/
> ty/Pyrefly) see `references/python-static-type-checking.md`; for pytest/
> Hypothesis see `references/python-testing.md`. This file is the deep,
> tool-specific reference for uv itself. Defer to the official docs
> (https://docs.astral.sh/uv/) as the source of truth for exact flags/versions.

## Command surface at a glance

`uv <command>` top-level commands (uv 0.11.x):

| Group | Commands |
| --- | --- |
| **Project** | `init`, `add`, `remove`, `sync`, `lock`, `run`, `tree`, `export`, `version`, `build`, `publish` |
| **Python mgmt** | `python install`/`pin`/`list`/`find`/`uninstall`/`dir` |
| **Tools (pipx)** | `tool install`/`run` (alias `uvx`)/`upgrade`/`list`/`uninstall`/`dir`/`update-shell` |
| **pip interface** | `pip install`/`compile`/`sync`/`freeze`/`list`/`show`/`tree`/`uninstall`/`check` |
| **Env / misc** | `venv`, `cache` (`clean`/`prune`/`dir`), `self update`, `auth`, `format`, `audit` |

Two front-doors that confuse newcomers: the **project interface** (`uv add`,
`uv sync`, `uv run` — operates on `pyproject.toml` + `uv.lock`, the recommended
path) and the **pip interface** (`uv pip ...` — a drop-in low-level imperative
layer with no lockfile). Don't mix them on the same environment expecting
managed state; the project interface owns `uv.lock`, the pip interface does not.

---

## 1. Project & workspace management

### Single project

```bash
uv init myproject          # app layout: pyproject.toml, main.py, .python-version, .gitignore
uv init --lib mylib        # library layout: src/mylib/__init__.py + [build-system]
uv init --package myapp    # packaged app (installable, has [build-system])
uv add requests 'httpx>=0.27'
uv add --dev pytest ruff   # dev dependency group (PEP 735 [dependency-groups])
uv add --group docs mkdocs # named dependency group
uv remove requests
uv run pytest              # run a command inside the project env (auto-syncs first)
uv run python script.py
uv tree                    # show the resolved dependency tree
uv version --bump minor    # read/update [project].version
```

`uv run` and `uv sync` **auto-create** the `.venv`, **auto-install** the pinned
Python if missing, **auto-lock**, and **auto-sync** before running — so the venv
is an implementation detail you rarely activate manually. Key files:

- `pyproject.toml` — standard PEP 621 metadata + `[tool.uv]` config, `[dependency-groups]`, `[tool.uv.sources]`.
- `uv.lock` — the universal lockfile (commit to git; never hand-edit).
- `.python-version` — the pinned interpreter (written by `uv python pin`).
- `.venv/` — the project virtualenv (gitignored).

**Dependency groups** (PEP 735, the modern replacement for `[project.optional-dependencies]`
"extras" used as dev deps): `dev` is the implicit default group. Control install
scope on `sync`/`run`: `--group <g>`, `--only-group <g>`, `--no-dev`, `--no-default-groups`,
`--all-groups`. Extras (consumer-facing optional features) are separate:
`--extra <e>`, `--all-extras`.

**Dependency sources** — `[tool.uv.sources]` redirects a dependency away from PyPI:

```toml
[tool.uv.sources]
mylib       = { workspace = true }                        # local workspace member
httpx       = { git = "https://github.com/encode/httpx", tag = "0.27.0" }
foo         = { path = "../foo", editable = true }         # local editable path
bar         = { url = "https://example.com/bar-1.0-py3-none-any.whl" }
torch       = { index = "pytorch" }                        # pin to a named [[tool.uv.index]]
```

`[tool.uv.sources]` is **non-standard metadata** that uv strips when building a
distribution — it affects your dev resolution, not what downstream consumers get.

### Workspaces (monorepo)

A workspace is multiple packages in one repo sharing **one `uv.lock`** and one
`.venv`, each with its own `pyproject.toml`. Inspired by Cargo workspaces.

```toml
# root pyproject.toml
[project]
name = "albatross"
dependencies = ["bird-feeder", "tqdm>=4,<5"]

[tool.uv.workspace]
members = ["packages/*"]
exclude = ["packages/seeds"]

[tool.uv.sources]
bird-feeder = { workspace = true }   # resolve from the workspace, editable
```

- Members are addressed with `uv run --package <member>` / `uv add --package <member> <dep>`.
- `workspace = true` sources are treated as **editable** — cross-package edits are live.
- Root `[tool.uv.sources]` apply to all members unless a member overrides them.
- Use a workspace when packages are **co-released and tightly coupled**; use
  separate projects (path/git sources) when versions must diverge or a member
  needs a conflicting dependency (a single shared lock forbids conflicts).

---

## 2. The universal lockfile (`uv.lock`)

`uv.lock` is a **universal (cross-platform) resolution**: one lockfile valid for
every OS, architecture, and Python version inside the project's `requires-python`
range. A package can appear multiple times with different versions/URLs gated by
**environment markers** (`sys_platform`, `python_full_version`, etc.); the marker
chooses which entry installs on a given machine.

```bash
uv lock                 # create/update uv.lock
uv lock --check         # CI gate: fail if lockfile is stale (was --locked/--frozen era)
uv lock --upgrade       # re-resolve everything to newest allowed
uv lock --upgrade-package requests   # bump just one package
uv sync                 # install exactly what the lock says into .venv
uv sync --frozen        # install from lock without re-resolving (fail if missing/stale)
uv sync --locked        # assert lock is up-to-date, then install (CI)
uv sync --no-install-project   # deps only, skip the project itself (Docker layer caching)
```

**Resolution knobs** (also valid in the pip interface):

- `--resolution {highest|lowest|lowest-direct}` (env `UV_RESOLUTION`). `lowest`
  is for testing your declared lower bounds; `lowest-direct` lowers your direct
  deps but keeps transitive at highest.
- `--prerelease {disallow|allow|if-necessary|explicit|if-necessary-or-explicit}`.
- `--fork-strategy {requires-python|fewest}` — `requires-python` (default) picks
  the latest version compatible with each supported Python minor; `fewest`
  minimizes the number of distinct versions.
- `requires-python` semantics: uv considers **only lower bounds** of dependency
  `requires-python` and ignores upper bounds (`>=3.8,<4` is treated as `>=3.8`),
  because honoring upper bounds causes pathological backtracking. Your project's
  `requires-python` must be a **subset** of every dependency's range.

**Export / interop** — `uv.lock` is uv-native; export to standard formats for
other tooling:

```bash
uv export --format requirements.txt -o requirements.txt
uv export --format pylock.toml      -o pylock.toml      # PEP 751 standard lock
uv export --format cyclonedx1.5     -o sbom.json        # SBOM
```

uv **reads** `pylock.toml` (PEP 751) for install but keeps `uv.lock` as its
native format because PEP 751 doesn't yet capture everything uv needs (e.g. full
fork/marker model). Treat `uv.lock` as the source of truth and `pylock.toml`/
`requirements.txt` as generated artifacts.

`uv.lock` is **deterministic and committed**. The cross-platform guarantee is
the headline benefit over a platform-specific `pip-compile` `requirements.txt`.

---

## 3. Python version install & pinning

uv downloads and manages standalone CPython/PyPy builds (python-build-standalone)
— no `pyenv` needed, and no system Python required.

```bash
uv python install                # install the latest CPython
uv python install 3.12 3.13      # install several
uv python install pypy@3.10
uv python install --default      # also expose as `python`/`python3` on PATH (uv 0.8+)
uv python install --reinstall
uv python list                   # installed + downloadable
uv python list --only-installed
uv python pin 3.12               # write .python-version for this project
uv python pin --resolved 3.12.7  # pin an exact patch
uv python find 3.12              # print the path uv would use
uv python uninstall 3.11
uv python dir                    # where managed interpreters live
```

**Selection & preference:**

- Request syntax: `3.12`, `cpython@3.12`, `pypy@3.10`, `>=3.11,<3.13`, or a path.
- `.python-version` (project) / `.python-versions` pins the interpreter; `requires-python`
  in `pyproject.toml` bounds what is acceptable.
- `--python-preference {only-managed|managed|system|only-system}` (`[tool.uv]
  python-preference`) controls managed-vs-system priority. `managed` (default)
  prefers uv's downloads but will use a compatible system Python.
- `--no-python-downloads` (env `UV_PYTHON_DOWNLOADS=never`) forbids auto-download
  — useful in locked-down CI/containers.
- Automatic downloads: `uvx python@3.12 -c ...` or `uv venv` will fetch a missing
  interpreter on demand unless downloads are disabled.

---

## 4. Tool / pipx replacement (`uv tool`, `uvx`)

uv runs and installs CLI tools from Python packages in **isolated** environments,
replacing `pipx`.

```bash
uvx ruff check            # ephemeral: run ruff in a throwaway env (== uv tool run ruff)
uvx pycowsay 'hi'
uvx ruff@0.6.0 check      # pin the tool version
uvx --from httpie http    # package name != command name
uvx --with mkdocs-material mkdocs build   # add extra deps to the ephemeral env

uv tool install ruff      # persistent: install into ~/.local + symlink the executables onto PATH
uv tool install 'httpie>0.1.0'
uv tool install mkdocs --with mkdocs-material        # bundle plugins
uv tool install --with-executables-from ansible-core ansible
uv tool install git+https://github.com/httpie/cli   # from VCS
uv tool list
uv tool upgrade --all
uv tool uninstall ruff
uv tool update-shell      # add the tool bin dir to PATH in your shell rc
uv tool dir --bin         # where executables are linked (XDG-based)
```

- `uvx` = `uv tool run`: an **ephemeral** environment, ideal for one-off or
  CI invocations; it caches the env so repeat runs are fast.
- `uv tool install` is **persistent**: executables are symlinked (copied on
  Windows) into the tool bin dir. Only the package's own entry points are
  exposed — not its dependencies' executables.
- If the bin dir isn't on `PATH`, uv warns; run `uv tool update-shell`.

---

## 5. pip-compatible interface (`uv pip`)

A near-drop-in, much faster reimplementation of the pip / pip-tools workflow.
Operates **imperatively on an environment** with **no lockfile and no automatic
project management** — use it for legacy flows, scripts, containers, or when you
explicitly want pip semantics.

```bash
uv venv                              # create .venv (add --python 3.12 to choose)
uv pip install ruff 'httpx>=0.27'
uv pip install -r requirements.txt
uv pip install -e .                  # editable install of the current project
uv pip install --system ruff         # install into the active/system interpreter (Docker)
uv pip compile requirements.in -o requirements.txt   # pip-tools replacement
uv pip compile --universal requirements.in -o requirements.txt  # cross-platform, with markers
uv pip compile --generate-hashes requirements.in -o requirements.txt
uv pip sync requirements.txt         # make the env EXACTLY match the file (removes extras)
uv pip freeze / list / show / tree / check / uninstall
```

Deliberate differences from pip (uv is stricter / more correct by default):

- `uv pip install` does **not** mutate a global Python unless you pass `--system`
  or activate a venv; otherwise it targets `.venv`.
- `uv pip compile --universal` produces one marker-annotated `requirements.txt`
  valid across platforms — the pip-tools world's per-platform lock pain solved.
- `uv pip sync` is destructive-to-match (like `pip-sync`): it uninstalls anything
  not in the file. Use it for reproducible CI/containers.
- Resolution flags (`--resolution`, `--prerelease`, `--index`, `--index-strategy`)
  match the project interface.

---

## Build backend, publishing & PEP 723 scripts

**Build backend.** Since mid-2025 `uv init --package`/`--lib` default to uv's own
PEP 517 backend `uv_build` (package `uv-build`), zero-config for pure-Python
projects; Hatchling remains a fine alternative for projects needing plugins or
non-pure builds.

```toml
[build-system]
requires = ["uv_build>=0.10,<0.12"]
build-backend = "uv_build"
```

```bash
uv build              # produce sdist + wheel in dist/
uv publish            # upload to PyPI (replaces twine); use trusted publishing / token
```

**PEP 723 inline-script metadata** — single-file scripts declare their own deps
and Python, run in an isolated ephemeral env:

```python
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx", "rich>=13"]
# ///
import httpx
```

```bash
uv run script.py                 # uses the embedded /// script /// block
uv add --script script.py httpx  # edit the inline block programmatically
uv run --with rich --no-project example.py   # add deps ad hoc without a block
```

---

## Configuration & cache

- **Config files:** `[tool.uv]` in `pyproject.toml` (project), or a standalone
  `uv.toml` (project or `~/.config/uv/uv.toml` global). `uv.toml` wins over
  `[tool.uv]` when both exist.
- **Env vars:** almost every flag has one — `UV_RESOLUTION`, `UV_PRERELEASE`,
  `UV_PYTHON`, `UV_PYTHON_DOWNLOADS`, `UV_INDEX`/`UV_DEFAULT_INDEX`,
  `UV_CACHE_DIR`, `UV_NO_CACHE`, `UV_PROJECT_ENVIRONMENT`, `UV_SYSTEM_PYTHON`.
- **Indexes:** `[[tool.uv.index]]` (name + url, optional `default`/`explicit`),
  `--index`/`--default-index`, `--index-strategy {first-index|unsafe-first-match|unsafe-best-match}`.
- **Cache:** global content-addressed store with hardlinks into venvs (why uv is
  fast and disk-light). `uv cache dir` / `uv cache clean` / `uv cache prune`
  (`--ci` prunes safely for caching layers). `--no-cache` / `UV_NO_CACHE` for
  hermetic runs.

---

## Practical patterns

- **Adopt incrementally:** start with `uv pip install -r requirements.txt` /
  `uv venv` (drop-in), then migrate to `uv init` + `uv add` + `uv.lock` when ready.
- **Reproducible CI:** `uv sync --locked` (or `uv lock --check` as a gate) so a
  stale lockfile fails the build instead of silently re-resolving.
- **Docker:** copy `pyproject.toml` + `uv.lock` first, `uv sync --no-install-project
  --frozen` for a cacheable deps layer, then copy source and `uv sync --frozen`.
  Use the `ghcr.io/astral-sh/uv` image or `COPY --from=ghcr.io/astral-sh/uv /uv /uv`.
  Set `UV_COMPILE_BYTECODE=1`, `UV_LINK_MODE=copy` in containers.
- **GitHub Actions:** `astral-sh/setup-uv@v5` installs uv and caches automatically;
  combine with `uv python install`.
- **Monorepo:** one workspace + one `uv.lock`; per-service deploys via
  `uv sync --package <svc>` or `uv export --package <svc>`.
- **Pin Python per project:** `uv python pin 3.12` so contributors and CI agree.

## Anti-patterns

- **Mixing interfaces on one env** expecting managed state — `uv pip install`
  into a project `.venv` then `uv sync` will reconcile to the lock and remove
  your manual installs. Pick the project interface *or* the pip interface.
- **Hand-editing `uv.lock`** — it's generated; edit `pyproject.toml` and re-lock.
- **Committing `requirements.txt` as the source of truth** in a uv project — the
  lock is `uv.lock`; export `requirements.txt` as a derived artifact.
- **Putting dev tools in `[project.dependencies]`** — use `[dependency-groups]`
  (`uv add --dev`) so they don't ship to consumers.
- **A workspace with conflicting dependency versions across members** — a single
  shared lock can't satisfy a true conflict; split into separate projects with
  path/git sources instead.
- **`uv pip install` without `--system` inside a container** and then wondering
  why the system interpreter is empty — in containers you usually want `--system`
  or an explicitly created venv on PATH.
- **Forgetting `requires-python` is a subset constraint** — if your floor is
  `>=3.8` but a dependency dropped 3.8, universal resolution fails; raise your
  floor or constrain the dep.

## Troubleshooting

- **"No interpreter found for Python 3.x"** → `uv python install 3.x`, or you set
  `--no-python-downloads`/`UV_PYTHON_DOWNLOADS=never` in a locked env.
- **Lockfile out of date in CI** (`uv sync --locked` fails) → run `uv lock`
  locally and commit; something changed `pyproject.toml` without re-locking.
- **"Tool executable not on PATH"** after `uv tool install` → `uv tool update-shell`
  then restart the shell; verify with `uv tool dir --bin`.
- **Resolution is "too constrained"/conflict** → check overlapping `requires-python`,
  try `--resolution lowest-direct` to isolate, or `uv tree --invert <pkg>` to see
  who requires a pin.
- **Editable workspace dep not picking up changes** → confirm the member is in
  `[tool.uv.workspace] members` and referenced with `{ workspace = true }` in
  `[tool.uv.sources]`; re-run `uv sync`.
- **Private index auth** → `uv auth` or `UV_INDEX_<NAME>_USERNAME/PASSWORD`; set
  `--index-strategy` if a package exists on multiple indexes.

## References

- uv official docs — https://docs.astral.sh/uv/ (projects, workspaces, resolution, tools, python-versions, pip, build-backend, export, settings)
- uv resolution & universal lockfile — https://docs.astral.sh/uv/concepts/resolution/
- uv workspaces — https://docs.astral.sh/uv/concepts/projects/workspaces/
- uv tools (pipx replacement) — https://docs.astral.sh/uv/concepts/tools/ and /guides/tools/
- uv Python versions — https://docs.astral.sh/uv/concepts/python-versions/ and /guides/install-python/
- uv pip interface — https://docs.astral.sh/uv/pip/
- uv build backend (stable, default since 2025) — https://docs.astral.sh/uv/concepts/build-backend/
- PEP 751 pylock.toml — https://packaging.python.org/en/latest/specifications/pylock-toml/
- Real Python: Managing Python projects with uv — https://realpython.com/python-uv/
- pydevtools: uv complete guide / build-backend-now-stable / uv 0.8 PATH — https://pydevtools.com/handbook/explanation/uv-complete-guide/
- Verified locally against uv 0.11.16 (Homebrew, 2026-05) — command surface, `uv init` output, export formats, lock/sync flags
