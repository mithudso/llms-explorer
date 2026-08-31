#!/bin/sh
# Make this checkout runnable on its own: a venv with the hub's dependencies,
# then the hub tests the site actually depends on (plan Task 8: bootstrap
# "creates hub/.venv, installs, runs the hub's test subset").
#
# The vendored tree carries the whole hub suite, most of which covers
# subsystems the site never loads — the MCP server, the box pool, the TUI, the
# replication push. Running all of it from the site's CI gate would fail the
# site's build for reasons that have nothing to do with the site, so the
# default here is the subset: the modules site/tools/build_llms.py imports
# (llms_lint, and docset_refine's clean / extract / render / export_llms /
# vocabulary). Everything else is one flag away.
#
#   sh hub/bootstrap.sh              # venv + deps + the site-relevant hub tests
#   sh hub/bootstrap.sh --all-tests  # venv + deps + the whole vendored suite
#   sh hub/bootstrap.sh --no-tests   # venv + deps only
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

MODE=subset
case "${1:-}" in
  "") ;;
  --all-tests) MODE=all ;;
  --no-tests) MODE=none ;;
  *) echo "usage: sh hub/bootstrap.sh [--all-tests|--no-tests]" >&2; exit 2 ;;
esac

[ -d .venv ] || python3 -m venv .venv
.venv/bin/python -m pip install -q --upgrade pip
# requirements-dev.txt carries the test toolchain plus mcp and pyyaml, so no
# caller needs an ad-hoc pip install to run the hub or the site tests.
.venv/bin/python -m pip install -q -r requirements-dev.txt

if [ "$MODE" = none ]; then
  exit 0
elif [ "$MODE" = all ]; then
  set -- tests/
else
  set -- tests/test_llms_lint.py tests/test_docset_refine.py tests/test_vocabulary.py
fi
export HUB_DOCSET_BACKEND=sqlite
exec .venv/bin/python -m pytest "$@" -q
