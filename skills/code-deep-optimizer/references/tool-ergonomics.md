# Pass M5 — tool ergonomics (conditional) — code-deep-optimizer

> Reference for `code-deep-optimizer`. M5 is **conditional**: it runs only when the target ships a
> runnable entrypoint (CLI, script, TUI launcher, server). Otherwise record `N/A (library only)`.
> It is reported in the receipt but is outside the fixed 18-pass count.

A tool the owner has to debug before using it is unfinished. Findings come from observed failures:
`error: externally-managed-environment` (PEP 668), `ModuleNotFoundError: chromadb`, an Ollama
`Model 'mxbai-embed-large' missing` 404, and repeated requests for "a single command" with usage
text.

## Checks (each Medium unless noted)

| # | Check | Fails when |
|---|---|---|
| E1 | **One command** | Starting the tool needs more than one documented command, or several scripts must run in order. Fix: one entrypoint (console script, `./tool`, or `python -m pkg`). |
| E2 | **Sane defaults** | A common run needs flags. Fix: no-argument invocation does the most likely useful thing (or prints usage); recursive/resume/incremental are the default, opt-outs are flags. |
| E3 | **Usage on bad input** | An unknown subcommand or missing argument gives a traceback or silence. Fix: argparse/click usage, exit code 2, a one-line example. (High if it exits 0.) |
| E4 | **Own environment** | The README says `pip install ...` globally, or the tool imports a third-party package with no venv story. Fix: self-created `.venv` (uv when present, else `venv`) and re-exec; never global pip into a PEP 668 Python. |
| E5 | **Preflight** | A required program, Python module, local service or model is assumed present. Fix: check up front and print the exact missing item with the exact fix command, exit 3; no traceback. |
| E6 | **Discoverable** | `--help` is missing, wrong, or lacks an example; the README quick start does not match the real command. |

## Fix recipe

Copy `scripts/tool_bootstrap.py` next to the tool (stdlib only). Call `ensure_venv()` first, then
`preflight(...)` with the tool's real prerequisites. Add the usage text and the no-argument
default in the tool's own argument parser. Add one test per check that failed (E3: bad argument
exits 2 with usage; E5: missing prerequisite exits 3 and names the fix).

`TOOL_NO_VENV=1` skips the venv step for CI and containers. The bootstrap never touches system
site-packages.

## Limits

Report-only for E1 when the fix would reshape the repo's public interface; the behavior-drift guard
still applies. Preflight must not start services, pull models, or install anything: it only reports.
