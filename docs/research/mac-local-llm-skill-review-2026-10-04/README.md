# What the complete Mac local LLM skill changes for the RTX 5080 effort

Version: 1.1.0
Reviewed: 2026-10-04
Delta: review all files of version 1.5.0 after the source changed from eight monolithic files to 134 files in 21 topical packs during the review. Preserve the earlier version 1.4.0 inventory.

The research changes the next agent-performance investigation. It does not justify replacing the prepared CUDA candidate with an MLX model or declaring the RTX 5080 qualified. The strongest new lead is the size and stability of the actual agent input, rather than bare decode speed.

## Coverage and limits

I inventoried every file, including hidden metadata, under /Users/mitch/.claude/skills/running-llm-models-locally-on-mac-expert/. The reproducible screen reads all file bytes and parses the complete manifest, 436 dossier sections, 14,978 topic fact-layer rows, 141 top-level fact rows and 281 correction entries across the top-level and topical layers (including copies). I read applicable sections and inspected the material primary/local sources. This is not an independent fact check of every row. Many fact rows repeat dossier prose and are not independent findings.

The SQLite database was opened read-only, its quick_check returned ok, and all 14,978 indexed rows were screened. It is a derived index, not independent evidence. Every topical index, digest, correction layer and manifest was included. The inventory records every source file hash and all section ranges in /Users/mitch/dev/llms-explorer/docs/research/mac-local-llm-skill-review-2026-10-04/inventory.json. The manifest records nine rounds, 436 researched concepts and 38 unresearched candidates. Of the researched dossiers, 221 ended BUDGET_EXHAUSTED and 215 SATURATED-DEPTH. Those labels do not mean hardware acceptance. The two JSON metadata files still advertise skillVersion 1.0.0 while /Users/mitch/.claude/skills/running-llm-models-locally-on-mac-expert/SKILL.md advertises 1.5.0. The migrated /Users/mitch/.agents/skills/running-llm-models-locally-on-mac-expert/ directory was absent, so this review used the specified canonical source.

## Findings that change the effort

| Finding and evidence | Consequence |
|---|---|
| The local capture dossier records Claude Code 2.1.289 at about 14k proxy tokens with a clean profile and 66k–96k with the user's heavy profile. The captures returned HTTP 500 and used cl100k, not Qwen tokenization. Source: /Users/mitch/.claude/skills/running-llm-models-locally-on-mac-expert/llms/topics/agent-clients-context-and-compaction/llms-full.txt:245. | Before judging coding or research throughput, record the exact model-rendered input size and loaded tools for the actual qualification profile. A 66k payload cannot fit a 32k window. This is a lead about payload size, not a measured CUDA failure or speed. |
| The same dossier found no prompt reduction from CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT=1 on 2.1.289 with a custom base URL. It also found that moving dynamic prompt sections moved tokens rather than reducing their total. | Remove any assumed speed gain from those switches. A future controlled experiment must demonstrate a change in this exact client's request. Do not replace full-tools qualification with --bare, six tools, disabled skills, or a one-sentence system prompt. |
| Current Claude gateway documentation makes deferred MCP discovery conditional on forwarding tool_reference blocks. The local Anthropic converter handles text, thinking, images, tool_use and tool_result, but has no tool_reference handling. Source: /Users/mitch/dev/macuda/llama.cpp/tools/server/server-chat.cpp:396. | Do not simply enable tool search to shrink the large profile. First qualify a compatibility adapter that retains discovery, schemas, names, tool results and repeated-turn behavior. Keep all required coding and /dr capabilities available. Merely accepting a request is insufficient. |
| The generic preserve_reasoning flag is aliased to preserve_thinking in current llama.cpp. Sources: /Users/mitch/.claude/skills/running-llm-models-locally-on-mac-expert/llms/topics/chat-templates-reasoning-and-tool-calling/llms-full.txt:921 and /Users/mitch/dev/macuda/llama.cpp/common/jinja/caps.cpp:22. | Correct the earlier claim that these keys are unaliased. The inspected checkout already has the alias and default-on rule. Check the actual embedded template capability and repeated-turn rendered prefix; do not edit the immutable candidate template merely to add another flag. |
| Billing-header advice is version-dependent. Anthropic documents a conversation-stable block on custom base URLs from 2.1.181. The inspected local converter already normalizes cch. Source: /Users/mitch/dev/macuda/llama.cpp/tools/server/server-chat.cpp:312. | Do not assume every warm miss is a changing attribution header. Compare actual request prefixes and cache logs before choosing a fix. The normalizer operates on the Anthropic route and does not normalize the version/hash suffix. |
| The hybrid-checkpoint research separates valid exact-position recurrent state from unsafe rollback. PR 24797 was closed unmerged; PR 25592 remains open. Source: /Users/mitch/.claude/skills/running-llm-models-locally-on-mac-expert/llms/topics/llama-cpp-internals/llms-full.txt:967. | If real turns log forcing full prompt re-processing despite stable input, inspect checkpoint validity and use it as a focused follow-up experiment. Do not apply the rejected patch or silently add an open patch to the current pinned build. |
| Overflow handling depends on the actual error, slot context, usage counters and client recovery. A prompt-size error and a mid-generation KV-pool failure are different failures. Source: /Users/mitch/.claude/skills/running-llm-models-locally-on-mac-expert/llms/topics/agent-clients-context-and-compaction/llms-full.txt:1263. | Retain explicit 32768 context and measure actual compaction on the installed client. Preserve the original error body and usage. Do not label every memory error prompt-too-long or rely on an untested error-text rewrite. |
| The local Metal accounting dossier found that phys_footprint can remain small for resident file-backed no-copy buffers. It reports one anomalous GPU-written-buffer result and leaves the mechanism open. Source: /Users/mitch/.claude/skills/running-llm-models-locally-on-mac-expert/llms/topics/memory-and-wired-limits/llms-full.txt:1334. | Measure host pressure and residency separately from discrete VRAM allocations and peak. RSS/footprint alone cannot admit the RTX model. These Metal observations do not establish how the TinyGPU/CUDA route accounts for memory. |

Primary references verified during this review:

https://code.claude.com/docs/en/llm-gateway-protocol

https://raw.githubusercontent.com/ggml-org/llama.cpp/master/common/jinja/caps.cpp

https://github.com/ggml-org/llama.cpp/pull/24797

https://github.com/ggml-org/llama.cpp/pull/25592

The web renderer could not extract the requested environment-variable/model-window entries, and direct Markdown retrieval returned HTTP 403. Those entries remain dossier-derived here. The retained version 1.4.0 inventory is historical; its eight files were replaced during review and it is not the expected live snapshot. The source record distinguishes this failure from successful gateway/source inspection. The local request-size and Metal measurements are recorded research results; their raw captures were not independently replayed in this review.

## Useful facts that do not change the current hardware trial

- MLX, NAX, ANE, Metal wired limits, oMLX, MTPLX, SSD expert offload and JACCL/RDMA describe other execution paths. They cannot enlarge the physical RTX 5080's 16 GB VRAM. Their reported speeds do not prove performance on this rig.
- The MLX fp16 partial-attention overflow hypothesis is about a Metal kernel. It does not explain the old CUDA selected-token error by itself. Preserve the absolute 0.05 threshold, exact token/byte checks and matched cache/batch controls.
- Quant evaluation should include task success and tail errors. A low mean KLD or a dense-model label cannot qualify IQ2 coding or research. The corpus has no verified dense Qwen3.5-27B Unsloth KLD table, and Qwen3.6-27B per-quant quality is still an unresearched frontier item.
- MTP/drafting requires measured acceptance and end-to-end latency. Recurrent verification can require expensive restore/redecode and published reports include loops even with MTP alone. The first trial's --spec-type none remains appropriate.
- Ollama's current Qwen parser recovers a tool call emitted inside thinking. That corrects an old blanket parser claim but does not qualify our separate converter/parser or justify restarting paused Ollama.
- A Codex Responses endpoint that skips namespace tools can silently lose MCP functions. That is a separate client route; a Claude Messages success cannot be transferred to it.
- Metal panic, memory-pressure and cluster recovery recipes are not evidence that a Blackwell GSP fault can be safely reset on this rig. The existing physical recovery and single-owner constraints remain.

Additional primary references:

https://github.com/ggml-org/llama.cpp/pull/25819

https://raw.githubusercontent.com/ollama/ollama/main/model/parsers/qwen35.go

## Concrete next test sequence

1. Preserve the prepared Qwen3.6-27B IQ2 CUDA trial and original context, f16 KV, reserve and numerical limits. The prior failure was experimental_configuration_mismatch before weight load. A corrected native guard is prepared; its physical result remains unmeasured.
2. After actual startup and original first-inference/numerical/peak admission, capture the exact coding and /dr profile payloads, including full required tools and instructions. Count with the actual model tokenizer and template. Compare the result with the per-slot 32768 window and output reserve. Do not infer the profile's size from a clean or unrelated heavy profile.
3. In the already-required coding pair, retain prompt-evaluation, generation, cached-token and elapsed-time measurements separately. Save repeated-turn prefix/template evidence and cache/checkpoint log lines. No new generic dozen-test loop is needed to investigate this lead.
4. If input cannot fit, repair capability-preserving profile/discovery handling before a genuine standard /dr. If stable inputs still re-prefill, make a separately reviewed checkpoint experiment. Keep original first-trial receipts immutable.
5. Admit standard /dr only when coding/tool/stream/context behavior passes; then validate actual cited research and installed artifacts. A health response, capture server, source review or CPU test does not satisfy this goal.

This review changes the performance-diagnosis order and corrects stale advice. It starts no GPU/model service and leaves the full hardware qualification incomplete.

## Reproduce the corpus check safely

```sh
/opt/homebrew/bin/python3 -B /Users/mitch/dev/llms-explorer/docs/research/mac-local-llm-skill-review-2026-10-04/screen_corpus.py --verify-against /Users/mitch/dev/llms-explorer/docs/research/mac-local-llm-skill-review-2026-10-04/inventory.json
```

Expected: 134 files, skill version 1.5.0, 436 dossiers, 15,119 fact rows, 281 correction entries, zero model requests and zero hardware operations. A changed source hash fails the comparison so a future session reviews the delta rather than silently reusing this review.
