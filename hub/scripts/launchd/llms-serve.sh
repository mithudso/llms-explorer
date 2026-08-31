#!/bin/sh
# Hub llms.txt HTTP server (com.global-ai-hub.llms-serve) — serves /llms.txt,
# /d/<stem>/… (docset_refine exports) and /m/<key>/… (llms_full_catalog mirror).
# Read-only; binds 127.0.0.1 unless HUB_LLMS_HOST says otherwise.
set -u
HUB="${HUB_DIR:-$HOME/.global-ai-hub}"
cd "$HUB" || exit 1
exec "$HUB/.venv/bin/python" "$HUB/scripts/llms_serve.py"
