#!/bin/sh
# Weekly topical-family refresh (com.global-ai-hub.topical-refresh).
#
# Rebuilds every llms-topical/<slug>.llms/ from its recorded pool, researches
# the vocabulary's undefined terms from the hub estate, registers grounded
# aliases, queues what is still undefined, and re-indexes both layers.
# Runs on the hub venv (embed_core + the local Ollama model); Sunday 04:00,
# after the llms-full mirror refresh at 03:00 so the mirror it reads is fresh.
set -u
HUB="${HUB_DIR:-$HOME/.global-ai-hub}"
cd "$HUB" || exit 1
export PYTHONPATH="$HUB/scripts"
exec "$HUB/.venv/bin/python" "$HUB/scripts/topical_refresh.py"
