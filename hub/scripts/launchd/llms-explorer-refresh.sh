#!/bin/sh
# Daily snapshot refresh of ~/dev/llms-explorer (com.llms-explorer.snapshot-refresh).
# The refresh script itself lives in that repo; this wrapper only finds it.
set -u
REPO="${LLMS_EXPLORER_DIR:-$HOME/dev/llms-explorer}"
[ -x "$REPO/scripts/refresh_snapshot.sh" ] || { echo "no refresh script at $REPO"; exit 1; }
exec /bin/sh "$REPO/scripts/refresh_snapshot.sh"
