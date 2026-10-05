# Hub corpus review continuation

Version: 1.0.3
Delta: Finish corpus review; preserve applicability findings, corrected assumptions and publication state.

TASK-561 reviews /Users/mitch/.global-ai-hub/llms-concepts/ for parent TASK-482. The inventory has 4114 real-directory files, 661 fact dossiers, 339 name/title candidates and 293 content hits. The external document-extraction alias is excluded. Counts do not establish an atomic snapshot or validated findings. All screens used local files without embeddings. The original .llms suffix caused an overbroad title screen; version 1.0.1 removed it. Version 1.0.3 clarifies traversal/alias scope rather than claiming the corpus expanded.

The review preserves the original numerical failure and frozen F32 receiver. No model requests, probes, GPU initialization/reset, runtime changes or new model downloads occurred in this review. Read the findings before later coding/DR sessions. The pinned template uses preserve_thinking; generic preserve_reasoning is a different upstream key. Later sessions need raw tool/result/SSE, reasoning replay, context limit, cached/uncached tokens, checkpoint and real workspace-verifier observations. Keep full tools/skills. Claude 2.1.286 is newer than the documented 2.1.181 stable attribution-header boundary; capture behavior before applying the old workaround. Keep f16 KV, all reserves and original 0.05 gate.

Local source inventory and screen:
/Users/mitch/.cache/claude-egpu/experiments/hub-local-llm-corpus-review-v100/SOURCE-INVENTORY.json
/Users/mitch/.cache/claude-egpu/experiments/hub-local-llm-corpus-review-v100/SOURCE-SCREEN.json
/Users/mitch/.cache/claude-egpu/experiments/hub-local-llm-corpus-review-v100/RESULT.json

Public review and exact request:
/Users/mitch/dev/llms-explorer/docs/research/hub-local-llm-corpus-review-2026-10-05/README.md
/Users/mitch/dev/llms-explorer/docs/research/hub-local-llm-corpus-review-2026-10-05/prompts.md

Static F32 review is passed and sealed; physical receiver remains unconsumed. The next root operation must use external static SHA 2d6111ec6ca005c98f6815c4f6c31cc7a320da6fed3e5a5c99c1d579f1d462b0 after a separately confirmed fresh cold recovery. Actual numerics/peak/coding/standard DR remain pending. No elapsed-time promises.

Publication uses the isolated codex/qwen36-cold-evidence-20261005 branch. Preserve unrelated staged changes and divergent history in /Users/mitch/dev/llms-explorer. Focused tests and privacy check passed; commit/PR/CI/merge results will be recorded at shipment. The broader runtime goal remains unfinished even when this review task closes.

## Close reconciliation

KNOW-157, KNOW-382, KNOW-404 and KNOW-139 remain true as scoped decisions. No runtime or model-cleanup re-verification is claimed. KNOW-124 was updated because its old owner and no-download restrictions were stale after the October 5 candidate trial. The update preserves historical coding/research results and adds the current numerical gap. TASK-554 completed static preparation only; TASK-482 and TASK-129 remain unfinished.

## Publication handle

The review/evidence PR is:
https://github.com/mithudso/llms-explorer/pull/145

The authoritative local publication receipt records CI, merge and local materialization status after shipment:
/Users/mitch/.cache/claude-egpu/experiments/hub-local-llm-corpus-review-v100/PUBLICATION.json

Do not infer physical acceptance from a merged documentation PR. The primary checkout remains protected from branch synchronization because it has unrelated staged changes and divergent history. Any local copies of new merged documentation must preserve that index and history.
