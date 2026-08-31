#!/bin/sh
# Refresh the llms-explorer snapshot from the live hub and push it.
#
# The hub (~/.global-ai-hub) is the runtime and the source of truth; this
# repo is the self-contained, publishable copy: skill, hub code + tests,
# MCP wiring, design docs, every docset export, the llms-full mirror,
# topical outputs, research notes, eval banks, logs. Each subtree is
# rsync'd with --delete so removals propagate; files over GitHub's 100 MB
# limit are skipped (listed in outputs/llms-full/SKIPPED.txt).
#
#   scripts/refresh_snapshot.sh            # copy, commit if changed, push
#   scripts/refresh_snapshot.sh --no-push  # copy + commit only
#
# Env: HUB_DIR (default ~/.global-ai-hub), CLAUDE_DIR (default ~/.claude),
#      MIRROR_DIR (default $CLAUDE_DIR/skills/web-text-mirror/text-mirror).
set -u
HUB="${HUB_DIR:-$HOME/.global-ai-hub}"
CL="${CLAUDE_DIR:-$HOME/.claude}"
MIR="${MIRROR_DIR:-$CL/skills/web-text-mirror/text-mirror}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PUSH=1; [ "${1:-}" = "--no-push" ] && PUSH=0
cd "$REPO" || exit 1
echo "== llms-explorer refresh $(date -u +%Y-%m-%dT%H:%M:%SZ) from $HUB"
X='--exclude __pycache__ --exclude *.pyc --exclude .DS_Store --exclude ._*'
sync() { # sync SRC DST (dirs end with /)
  mkdir -p "$2"; rsync -a --delete $X "$1" "$2"
}
one() { mkdir -p "$(dirname "$2")"; cp "$1" "$2"; }

# skill, research spokes, router, alias
sync "$CL/skills/llms-deep-optimizer/"            skills/llms-deep-optimizer/
mkdir -p skills/document-formats/references
cp "$CL"/skills/document-formats/references/llms-txt*.md skills/document-formats/references/
one "$CL/skills/document-formats/SKILL.md"        skills/document-formats/SKILL.md
one "$CL/skills/deep-optimizer/SKILL.md"          skills/deep-optimizer-router-SKILL.md
one "$CL/commands/ldo.md"                         commands/ldo.md

# hub code — same layout as the hub so `cd hub && pytest tests` works
mkdir -p hub/scripts hub/tests hub/docs hub/libraries/mcp-library
for f in llms_lint.py llms_serve.py llms_acquire.py llms_full_catalog.py docset_indexer.py \
         docset_rollout.py pipeline_manager.py embed_core.py concept_tree.py replicate_docsets.py \
         hub_lib.py hub_sqlite.py box_schedule.py quiet_hours_enforce.py ask; do
  [ -f "$HUB/scripts/$f" ] && one "$HUB/scripts/$f" "hub/scripts/$f"
done
sync "$HUB/scripts/docset_refine/"  hub/scripts/docset_refine/
sync "$HUB/scripts/hub_manager/"    hub/scripts/hub_manager/
sync "$HUB/scripts/semantic_ops/"   hub/scripts/semantic_ops/
sync "$HUB/scripts/launchd/"        hub/scripts/launchd/
sync "$HUB/mcp-server/"             hub/mcp-server/
one "$HUB/.mcp.json"                hub/.mcp.json
one "$HUB/libraries/mcp-library/registry.json" hub/libraries/mcp-library/registry.json
for f in MCP.md HUB-MANAGER.md ARCHITECTURE.md; do [ -f "$HUB/docs/$f" ] && one "$HUB/docs/$f" "hub/docs/$f"; done
for f in CLAUDE.md pyproject.toml requirements-dev.txt watch_dirs.txt; do [ -f "$HUB/$f" ] && one "$HUB/$f" "hub/$f"; done
for f in conftest.py test_docset_keyword.py test_docset_refine.py test_docset_rollout.py \
         test_docset_search.py test_ldo_followups.py test_llms_acquire.py test_llms_full_catalog.py \
         test_llms_full_mcp.py test_llms_full_tab.py test_llms_lint.py test_llms_serve.py \
         test_topical.py test_vocabulary.py test_replicate_docsets.py test_script_help.py \
         test_app_smoke.py test_queue_model.py test_box_pool.py; do
  [ -f "$HUB/tests/$f" ] && one "$HUB/tests/$f" "hub/tests/$f"
done
mkdir -p hub/docs/specs hub/docs/plans
cp "$HUB"/docs/superpowers/specs/*llms*.md "$HUB"/docs/superpowers/specs/*docset*.md "$HUB"/docs/superpowers/specs/*concept*.md hub/docs/specs/ 2>/dev/null
cp "$HUB"/docs/superpowers/plans/*docset*.md "$HUB"/docs/superpowers/plans/*llms*.md hub/docs/plans/ 2>/dev/null

# outputs
mkdir -p outputs/exports
for d in "$MIR"/*.llms; do [ -d "$d" ] && sync "$d/" "outputs/exports/$(basename "$d")/"; done
for d in outputs/exports/*/; do [ -d "$MIR/$(basename "$d")" ] || rm -rf "$d"; done
mkdir -p outputs/llms-full/files
cp "$HUB/llms-full/catalog.json" "$HUB/llms-full/manifest.json" outputs/llms-full/
rsync -a --delete --max-size=99m $X "$HUB/llms-full/files/" outputs/llms-full/files/
find "$HUB/llms-full/files" -type f -size +99M -exec basename {} \; | sort > outputs/llms-full/SKIPPED.txt
[ -d "$HUB/llms-topical" ] && sync "$HUB/llms-topical/" outputs/llms-topical/
[ -d "$HUB/llms-vocabulary" ] && sync "$HUB/llms-vocabulary/" outputs/llms-vocabulary/
one "$HUB/concept-tree/tree.json" concept-tree/tree.json
[ -f "$HUB/research/medusajs-docs-llms-full.txt" ] && one "$HUB/research/medusajs-docs-llms-full.txt" outputs/medusajs-docs-llms-full.txt

# research, evals, logs
mkdir -p research/pipeline evals logs
cp "$HUB"/research/research-*.md "$HUB"/research/RESEARCH-DELIVERABLES-INDEX.txt research/pipeline/ 2>/dev/null
[ -d "$CL/skill-consolidation/evals/llms" ] && sync "$CL/skill-consolidation/evals/llms/" evals/
cp "$HUB/prompts-hub.md" "$HUB/memory-hub.md" logs/
git add -A
if git diff --cached --quiet; then echo "no changes"; exit 0; fi
date -u +%Y-%m-%dT%H:%M:%SZ > SNAPSHOT.txt   # stamped only when something real changed
git add SNAPSHOT.txt
git -c user.name="${GIT_AUTHOR_NAME:-llms-explorer refresh}" -c user.email="${GIT_AUTHOR_EMAIL:-refresh@llms-explorer.local}" \
  commit -q -m "snapshot: $(date -u +%Y-%m-%d) refresh from the hub" || exit 1
git log --oneline -1
[ "$PUSH" = 1 ] && exec git push -q origin HEAD:main
exit 0
