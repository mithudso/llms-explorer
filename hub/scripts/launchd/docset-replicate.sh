#!/bin/sh
# Hourly docset replication (com.global-ai-hub.docset-replicate).
#
# Runs on /usr/bin/python3, NOT the venv, on purpose.
#
# macOS gates LAN access behind Local Network privacy (TCC), granted per
# binary. Apple's /usr/bin/python3 is pre-approved; the homebrew python the
# venv is built on is not, and has no way to be prompted from a launchd agent.
# The failure is silent and misleading — every ssh to a 192.168.x.x host dies
# with "No route to host" while the identical command works from a terminal,
# which inherits the terminal app's grant. Verified under launchd:
#
#   sh -> ssh                  : works
#   venv python -> ssh         : "No route to host"
#   /usr/bin/python3 -> ssh    : works
#
# replicate_docsets.py is stdlib-only for exactly this reason;
# tests/test_replicate_docsets.py asserts that, so adding a third-party import
# fails a test instead of silently breaking this timer.
#
# The alternative fix is granting Local Network permission to the venv python
# in System Settings > Privacy & Security > Local Network, which cannot be
# done from the command line.
set -u
HUB="${HUB_DIR:-$HOME/.global-ai-hub}"
export PYTHONPATH="$HUB/scripts"
cd "$HUB" || exit 1
exec /usr/bin/python3 "$HUB/scripts/replicate_docsets.py" push
