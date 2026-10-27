# MongoDB frontier expansion continuation

Version: 1.3.0
Delta: 1.2.0 to 1.3.0; all local validation passed and installed data-path limits recorded.
Task: TASK-918.
Status: both frontiers expanded and locally verified; commit/CI/merge next.

Scope: expand the research frontier with fresh source-backed candidates and checked CVS, preserving the existing exhaustive backlog and every older plan and reservation. New candidate labels remain unresearched. They reach the visible tree through parent-tagged queue rows; do not create researched nodes for planning candidates.

Repository: /Users/mitch/dev/worktrees/llms-explorer-mongodb-frontier-20261025
Private inventory and candidate evidence: /Users/mitch/.global-ai-hub/research/.frontier/mongodb-20261025/

Inventory checks both hub and repository trees, aliases, all child labels, both queues, local research manifests and reservations. The unavailable remote plan still cannot establish remote coverage. Model policy for any Codex discovery worker is Sol/medium. Source leads and CVS are planning evidence, not verified research findings. Indexing and Ollama remain paused.

Use the existing concept-family-explorer sync_trees.py queue-only spec (researched empty) to append selected gaps and scores under existing parents in both targets. Dry-run before apply. Keep raw source text and full private inventory outside Git. Preserve original tree and queue preimages.

Remaining: external-evidence discovery across MongoDB families; semantic deduplication; canonical CVS check; queue/tree merge; generated-tree and privacy validation; commit, push, CI and merge.

## Discovery and audit

42 proposals examined;34 genuinely new gaps scored;33 selected,8duplicate proposals rejected,1below threshold. Canonical CVS checker passed34rows with0arithmetic or decision failures. Score range3.40–4.65 for selected candidates, under17 existing parents. Independent source/novelty audit passed after clarifying DEK rewrapping scope. No label or research claim was promoted as completed.

Existing native edit_node(add_child=...) appends raw childConcepts, which is required for the TUI outline and root website branches. Queue-only rows alone would miss those surfaces. The guarded writer holds the shared hub lock, preserves per-target preimages and fresh hashes, uses this minimal edit API, then runs queue-only sync_trees with researched empty. It regenerates only gen_tree and gen_context; no broad pack refresh or hidden research dispatch.

Stele task920inventory completion and task921scoring claim updates encountered Transport closed. Disk state is authoritative for continuation until graph tracking reconnects. No model/runtime service was restarted to fix this.

## Guarded application

33 new child labels appended under17 existing parents in each raw tree. Node counts remain1915repository and1920hub. Every other node field remains equal to its preimage; both queue byte prefixes remain intact. All33 new queue rows are unchecked and match the checked scores. All139 protected plans, manifests, reservation inputs and ranked files are unchanged. Native helper idempotence on exact post-state copies changes0bytes.

The loaded MCP hub_concept_frontier API independently reports all33 labels with the expected17 parent associations and CVS/RESEARCH decisions. The guarded writer also checked source TUI build_outline and generated website nodes. Installed TUI tracing remains under independent verification.

A native installed hub helper unexpectedly calls research_site_hook.refresh from concept_tree.save_nodes inside the caller-held research/.global.lock. The first guarded attempt blocked on its own refresh child. Only that child was terminated; all six tree/queue/score files were rolled back to exact preimages. The successful retry used the supported per-command RESEARCH_SITE_SYNC_DISABLED=1, then the narrow gen_tree/gen_context commands after lock release. No persistent configuration setting or old receipt was changed. Site context is byte-identical.

Combined llmsx/hub/site pytest collection exposed a cross-package conftest import collision around INJECTION. Validation is split into the standard package-specific pytest processes; no implementation change is required.

Preflight, failed-attempt, rollback, successful apply and idempotence receipts remain under /Users/mitch/.global-ai-hub/research/.frontier/mongodb-20261025/guarded/. The current apply pointer is /Users/mitch/.global-ai-hub/research/.frontier/mongodb-20261025/guarded-apply.json.

## Completed local checks

Guarded writer completed37 tests in isolated package processes:2llmsx,10hub,25site. Deterministic generation and git diff checks passed. Context is byte-identical. The independent live verifier traced the actual installed CLI and exercised Explorer._load(auto_sync=False) against the hub and publication worktree:all33 selected entries are frontier and queued with correct parents and scores. Loaded hub API independently agrees.

The installed CLI imports its implementation from the original /Users/mitch/dev/llms-explorer checkout. Its default data path remains that older checkout and currently lacks the additions. Do not claim its default launch has updated data. The verified command for the updated hub is /Users/mitch/.local/pipx/venvs/pip/bin/llmsx explorer --repo /Users/mitch/.global-ai-hub --no-sync. No GUI or deployed website was exercised.

Only four native repository data files changed, plus this pass's documentation. No pack or skill refresh ran. The raw tree counts stayed1915repository and1920hub. The generated site's prior researched-date stamp intentionally remains unchanged.

Both root and guarded writer Stele reads report temporary backend unavailability. Disk task status:inventory and scoring complete;merge/delivery stage active. Pending graph reconciliation:verify TASK-920/TASK-921 actual statuses;complete inventory and scoring;claim/complete TASK-922 delivery;complete TASK-918 only after CI/merge. Record the installed save_nodes hook lesson once Stele reconnects.
