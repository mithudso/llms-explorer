#!/usr/bin/env bash
# Sync the installable skill copies under skills/ from the canonical hub.
#
# The copies in skills/ are what `npx skills add mithudso/llms-explorer`
# installs and what the site renders as each skill page's prompt; the
# canonical sources live in the hub (~/.claude/skills, itself a mirror of
# ~/.global-ai-hub/skills). Run this after optimizing a skill in the hub so
# the published copies don't drift.
#
# Usage: scripts/sync-skills.sh [--check]
#   --check  report drift, exit 1 if any file differs; write nothing
#
# Env: SKILLS_HUB overrides the hub path (default ~/.claude/skills).
set -euo pipefail
cd "$(dirname "$0")/.."

HUB="${SKILLS_HUB:-$HOME/.claude/skills}"
CHECK=0
if [ "${1:-}" = "--check" ]; then CHECK=1; fi
[ -d "$HUB" ] || { echo "hub not found: $HUB" >&2; exit 2; }

drift=0
for dir in skills/*/; do
  name="$(basename "$dir")"
  src="$HUB/$name"
  # dr is a wrapped command, not a hub skill dir — skip it (hand-maintained).
  [ "$name" = "dr" ] && continue
  if [ ! -f "$src/SKILL.md" ]; then
    echo "SKIP $name — no hub source at $src" >&2
    continue
  fi
  # SKILL.md itself
  if [ "$CHECK" = 1 ]; then
    if ! cmp -s "$src/SKILL.md" "$dir/SKILL.md"; then
      echo "DRIFT $name/SKILL.md"; drift=1
    fi
  else
    cp "$src/SKILL.md" "$dir/SKILL.md"
  fi
  # companion dirs we ship (hub-only extras like evals/ are not synced)
  for sub in references scripts; do
    s="$src/$sub/"; d="$dir$sub/"
    [ -d "$s" ] || continue
    if [ "$CHECK" = 1 ]; then
      if ! diff -rq -x '__pycache__' -x '.DS_Store' "$s" "$d" >/dev/null 2>&1; then
        echo "DRIFT $name/$sub"; drift=1
      fi
    else
      mkdir -p "$d"
      rsync -a --delete --exclude '__pycache__' --exclude '.DS_Store' "$s" "$d"
    fi
  done
done

if [ "$CHECK" = 1 ]; then
  [ "$drift" = 0 ] && echo "in sync"
  exit "$drift"
fi
# guard: never ship a machine-specific absolute path (the literal
# "/Users/<username>" doc example in skill prose is fine; a real one is not)
if grep -rln "/Users/mitch" skills/ 2>/dev/null; then
  echo "WARNING: absolute /Users/ paths found in skills/ (listed above)" >&2
  exit 3
fi
echo "synced"
