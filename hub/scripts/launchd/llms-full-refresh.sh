#!/bin/sh
# Weekly llms-full.txt catalog + mirror refresh (com.global-ai-hub.llms-full-refresh).
#
# Re-compiles llms-full/catalog.json from the public directories, then
# downloads every entry not yet in the manifest and retries the failed ones
# (a site that 404'd last week may have shipped its file since). Already-ok
# files are NOT re-fetched; pass --refresh by hand for a full re-pull.
#
# Runs on the hub venv, unlike docset-replicate.sh: this job only talks to
# the public internet, so macOS Local Network privacy (the reason that
# script needs /usr/bin/python3) does not apply — and /usr/bin/python3 is
# 3.9, too old for this module.
set -u
HUB="${HUB_DIR:-$HOME/.global-ai-hub}"
PY="$HUB/.venv/bin/python"
cd "$HUB" || exit 1
echo "== llms-full refresh $(date -u +%Y-%m-%dT%H:%M:%SZ)"
"$PY" "$HUB/scripts/llms_full_catalog.py" compile || exit 1
exec "$PY" "$HUB/scripts/llms_full_catalog.py" download --jobs 12 --retry-failed
