#!/bin/sh
# Make this checkout runnable on its own: a venv with the hub's dependencies,
# then the test suite for the llms code. Run from anywhere:
#   sh hub/bootstrap.sh          # create .venv, install, run tests
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/python -m pip install -q --upgrade pip
.venv/bin/python -m pip install -q -r requirements-dev.txt
HUB_DOCSET_BACKEND=sqlite .venv/bin/python -m pytest tests/ -q
