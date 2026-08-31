#!/bin/sh
# Quiet-hours boundary job. $1 is "quiet" (start of the owner's working day)
# or "resume" (end of it).
#
# Runs on /usr/bin/python3, not the venv, for the same reason the docset timer
# does: macOS grants Local Network access per binary, Apple's python3 has it
# and the homebrew python the venv is built on does not, so a launchd agent
# using the venv sees every LAN ssh fail with "No route to host".
set -u
HUB="${HUB_DIR:-$HOME/.global-ai-hub}"
export PYTHONPATH="$HUB/scripts"
cd "$HUB" || exit 1
exec /usr/bin/python3 "$HUB/scripts/quiet_hours_enforce.py" "$1"
