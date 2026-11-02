# Frontier application lessons

Version: 1.0.0
Delta: initial concrete operational lessons.

The installed /Users/mitch/.global-ai-hub/scripts/concept_tree.py save_nodes() calls research_site_hook.refresh(). Calling the queue-only CFE sync while holding /Users/mitch/.global-ai-hub/research/.global.lock launched a refresh child that waited for the same lock. The guarded writer stopped only its own blocked child and restored all six exact file preimages. Use the supported process-scoped RESEARCH_SITE_SYNC_DISABLED=1 for this queue-only helper call, then run the narrow repository tree/context generators after releasing the lock. Do not change the global service configuration. The failed attempt and successful retry remain private.

Raw childConcepts links are required for the TUI outline and root website branches; queue-only rows cover only some frontier consumers. Use the existing edit_node(add_child=...) API and preserve every other node field. Do not upsert a new researched node for a planning candidate.

Combining llmsx, hub and site tests in one pytest process caused a conftest import collision around INJECTION. Run the standard package-specific checks in separate processes. All 37 narrow checks passed after separation, without changing test or implementation code.

The installed CLI can load a different data checkout from the publication worktree. Verify the actual selected data path; use the explicit canonical hub path when the original checkout retains older local commits.
