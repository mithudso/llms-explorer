# Hermes setup optimization

Version: 1.0.2
Delta: fresh ordinary-prompt model/tool checks pass after persistent guidance; test-loaded models safely unloaded and resource headroom restored.
Status: both installations operational under scoped acceptance; repository merge awaits the separate Cloudflare credential fix.

The user requested applying the Hermes depth research to the Mac and the RTX 5080 Linux installation, selecting memory/context services and verifying the result. This work uses the accepted research without reopening its paid claim gates. It preserves existing sessions, provider data, native runtime ownership and the indexing/Ollama pause.

## Selected memory and context stack

| Need | Selected mechanism | Reason |
| --- | --- | --- |
| Essential personal preferences and environment hints | Hermes native curated memory | Small, bounded snapshots; no second service or embedding request. |
| Conversation recovery | Native session history and session search | Preserves the source transcript behind compaction summaries. |
| Shared project decisions and task state | Stele MCP | Existing authenticated service on both machines; explicit project selection. |
| Existing local source and memory-central context | Global AI Hub MCP, three read-only tools | Keyword lookup, concept lookup and pack reading; no inference/indexing tools exposed. |
| Current upstream library documentation | Context7 MCP, two read-only tools | Version-aware retrieval; its actual anonymous handshake and library resolution pass. |
| Context management | Built-in compressor, lean tail | Supported recovery path without adding a second context-engine implementation and 15 extra tools. |

The choice fits this installed environment. It is not a benchmark showing one provider universally outperforms every alternative. RetainDB is selected on the Linux host but unavailable without its required credential. The Mac's pending source-update completion restored the OpenViking plugin; its availability flag does not prove ingestion/retrieval quality. Existing OpenViking and RetainDB data stay intact. External automatic providers are disabled in the proposed stack so they do not silently ingest transcripts or depend on the paused local pipeline.

Hermes allows one external memory provider alongside native memory. Its native snapshots remain frozen within a session. Validate new settings in a fresh session rather than rewriting a running conversation's cached prompt. [Hermes memory providers](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers), [persistent memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory)

## Bounded tool disclosure

The intended MCP allowlists contain seven Stele tools, three local Hub tools and two Context7 tools. Resource and prompt wrappers are disabled. Lazy connection and stdio recycling avoid keeping unused local servers resident. Tool Search uses a 1,200-token listing cap, three default hits and eight maximum hits per query; full schemas remain retrievable on demand. This bounds catalog overhead without claiming a measured end-to-end speedup. [MCP configuration](https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference), [Tool Search](https://hermes-agent.nousresearch.com/docs/user-guide/features/tool-search), [Context7](https://github.com/upstash/context7)

## Runtime findings and limits

Both published Hermes launchers are installed and functional. The Mac source is on clean main at fa59cb998af6; the Linux source is clean and detached at bf0203a794a07aac3ff764972ab9087baa4e4f4e. Hermes PM owns the interpreter and dependency generations. A Mac status invocation completed its pre-existing interrupted source update; this rebuilt the desktop package, resolved managed dependencies and restored the moved OpenViking plugin.

Configured model URLs point to currently inactive ports, but source inspection shows that the real CLI re-resolves native managed endpoints before use. The seed URL alone is not a reproduced Hermes failure. The remote managed router is healthy with its model unloaded. Its launch context is 65,536 tokens, while the model advertises 262,144 natively. Leave the explicit context override unset and use runtime-derived capacity. Keep the current models, sampling, placement and KV settings while establishing a real behavioral baseline. [Context management](https://hermes-agent.nousresearch.com/docs/developer-guide/context-compression-and-caching)

The existing desktop SSH master expired normally. Direct IPv4 SSH fails, while the host's mDNS IPv6 route succeeds using the already trusted host key. The alias repair retains that host-key identity. It does not accept a new key or weaken verification.

## Acceptance contract

Configuration installation, transport discovery and model behavior are separate gates:

1. Preserve preimages and fresh hashes; assert only intended settings changed.
2. Verify the actual Hermes MCP loader, filtered catalog and read calls on both machines.
3. Exercise native memory writes in isolated test profiles, then read the fact in a fresh process. Preserve ordinary user memories.
4. Discover the installed operations skill and its references through the real skill interface.
5. Run the configured native model with bounded turns and genuine tool execution. Inspect completion, actual tool result, route, context, token usage and latency.
6. Preserve rollback receipts and record explicit gaps. A greeting or successful configuration parse is insufficient.

The private continuation, configuration preimages and detailed diagnostics live at `/Users/mitch/.global-ai-hub/research/hermes-setup-optimization-2026-10-27/`. Published summaries must contain no tokens, raw secret-bearing process arguments or provider credentials.

## Observed memory and context results

| Check | Mac | RTX 5080 |
| --- | --- | --- |
| Connected selected MCP servers | 3/3 | 3/3 |
| Actual registered MCP tool allowlist | 12, exact match | 12, exact match |
| Shared Stele record fetched through Hermes dispatch | Pass | Pass |
| Hub keyword source retrieval | Pass | Pass |
| Context7 library resolution and documentation | Pass | Pass |
| Deferred MCP tools / visible bridge schemas | 12 / 3 | 12 / 3 |
| Observed catalog listing length | 1,197 characters | 1,050 characters |
| Operations skill and three supporting file identities | Pass | Pass |
| Native memory/user writes recovered by a fresh process | Pass | Pass |
| Frozen in-process memory snapshot retained | Pass | Pass |
| Closed fixture transcript recovered with session search | Pass | Pass |

Persistence checks use the real memory store/tool/session-search functions in isolated temporary homes. They do not claim that a model independently chose to save a memory. The fixtures were removed after verification. The operations skill loads 3,966 characters, with a 51-character description; its large research reference stays on demand.

The first acceptance attempt caught two configuration defects before model tests: utility flags belonged under each server's `tools` mapping, and the Mac Hub executable needed its existing Hub-owned interpreter. Both were repaired with fresh hash guards. Initial observations and immutable receipts remain private. The final v3 receipt SHA256 is `c5f5bded0b3438b5de14dfe120ae1201a864caa2e9ddd75c25b84014b168382f`.

The native model harness also exposed a CLI inconsistency: both installed routes advertised `--run-budget` in help but rejected it in gateway-backed execution. Those attempts exited before inference. The corrected harness uses an outer timeout; no global agent budget was changed.

## Initial model behavior and follow-up

The first full configured model run completed on both hosts. Each produced a fresh checksum through actual terminal execution and fetched the expected shared Stele record through Tool Search. The Mac took 43.343 seconds and the Linux host 197.459 seconds. These use different models and cache states, so they do not establish a comparative speed ranking.

The initial Linux run failed its read-only instruction: after the headless policy blocked an inline Python command, the model created a 112-byte helper in its test directory, executed it and removed it. The functional result was correct, but the instruction failure remains part of the result. A separate stricter prompt-control test passed in 74.589 seconds using only read operations, with no file writes or denied commands.

A small persistent task-boundary block is now appended to each profile's operating guidance. It prohibits file creation/editing/deletion during read-only tasks, including temporary helpers, and says to use a permitted read-only equivalent or report a blocked command. All original persona bytes and approval settings are preserved. Fresh ordinary-prompt runs pass with this persistent change: 24.212 seconds on the Mac and 139.907 seconds remotely, with exact checksum/title results and no model-directed file writes. The remote model used the existing read-only hash utility after its inline command was denied. The original failure remains recorded; passing retests do not establish universal instruction adherence.

The Mac's loaded model had roughly 26 GiB resident memory, low free-memory samples and rising swap counters during concurrent host activity. These observations do not attribute all swap activity to Hermes. No supported setting caps the initial native window while retaining automatic managed growth; generated presets and model metadata were left intact.

After final tests, fresh checks found four idle slots, no processing/deferred requests and empty active-session registries on each host. The official per-model unload operation released only the task-loaded models. Both routers and their owners remain alive and healthy; normal on-demand loading remains configured. The Mac free-memory sample rose from 11% to 61%, and remote GPU allocation fell from 14,715 MiB to 603 MiB. No unrelated model, Ollama service or retained GPU owner was stopped.

## Use and rollback

Start a fresh Hermes chat to pick up the new frozen operating guidance and tool catalog. Existing conversations were preserved. Native models load on demand; they were unloaded after verification to leave both hosts with usable headroom.

For connection checks on the Mac:

```sh
/Users/mitch/.local/bin/hermes memory status
/Users/mitch/.local/bin/hermes mcp list
/Users/mitch/.local/bin/hermes mcp test stele
/Users/mitch/.local/bin/hermes mcp test global_ai_hub
/Users/mitch/.local/bin/hermes mcp test context7
```

For the Linux host:

```sh
ssh 5080 /home/mitch/.local/bin/hermes memory status
ssh 5080 /home/mitch/.local/bin/hermes mcp list
ssh 5080 /home/mitch/.local/bin/hermes mcp test stele
ssh 5080 /home/mitch/.local/bin/hermes mcp test global_ai_hub
ssh 5080 /home/mitch/.local/bin/hermes mcp test context7
```

Expected: built-in memory enabled, external automatic provider unset, three configured MCP servers and successful connection tests. The connection test lists the server's native catalog; the separately verified runtime allowlist contains only 12 tools. Do not confuse these counts.

Exact preimages are retained privately under `/Users/mitch/.global-ai-hub/research/hermes-setup-optimization-2026-10-27/config-change/20261027T165555.772628Z/`. Before rollback, compare current file hashes with the final receipts. Restore only matching task-owned files; reconcile later user edits instead of overwriting them. Do not reset source checkouts or copy live databases. The installed skill has an identical repository copy in this report's `skill/` directory.

Unverified: existing desktop/gateway conversations were not reset, long idle-recycle timers were not soak-tested, semantic retrieval quality was not benchmarked, and no exhaustive model or UI qualification is claimed. The known CLI budget-option mismatch remains documented. No runtime context/quantization/placement tuning was made without comparative evidence.

## Research delivery dependency

The accepted 226-claim research and prior projection tests remain unchanged. GitHub Actions on PR 242 pass. The separate Cloudflare Pages build log confirms rejected private-library credentials. Refreshing its encrypted token and obtaining a green preview are required before merge:

https://github.com/mithudso/llms-explorer/pull/242
