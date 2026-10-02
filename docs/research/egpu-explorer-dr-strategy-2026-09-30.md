# Running Explorer research through the attached RTX 5080

Version: 1.0.0 · Inspected: 2026-09-30 · Status: proposed integration; no eGPU `/dr` qualification yet.

Keep `llmsx-research-gemma31-mlx` as the canonical Apple Silicon research model. First connect one research worker to the existing NVIDIA backend through a complete tool adapter. Keep the coordinator and blind gate on the qualified MLX model during this trial. Move the full workflow to the eGPU only after the worker and gate pass the same evidence checks.

The user referred to Gemini's comparative script without a new attachment or path. This strategy inspects the previously supplied `rtx5080_egpu_harness.py`, `ollama-egpu-proxy.py` and `benchmark_suite.py`. It does not claim to have identified a different Gemini entry point or reproduced its comparative results.

## What is present on this Mac

- Read-only IOKit checks found the RTX 5080 device ID and the TinyGPU registry entry.
- `GET http://127.0.0.1:8000/v1/models` returned HTTP 200 and `Qwen2-beta-14B-Chat`.
- `GET http://127.0.0.1:11440/api/version` returned HTTP 200 from the compatibility bridge. Its version string is synthetic, not proof of an Ollama engine behind it.
- An existing tinygrad log records that model with 8,179,322,304 model bytes, 14,167,290,880 parameters, a 4,096-token context and the NV device. The log does not measure current peak VRAM or establish research accuracy.
- The route is the same-Mac TinyGPU DriverKit/tinygrad NV path. It is not a Linux CUDA server. [NVIDIA specifies 16 GB GDDR7 for the RTX 5080](https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5080/).

These checks requested metadata only. No generation, service restart, driver installation, model download or indexing ran for this plan.

## What the scripts actually test

The eGPU harness starts `tinygrad.llm` with `DEV=NV` and a model artifact, then starts an Ollama-shaped HTTP bridge. Its `run_benchmark()` times a counting completion and computes `len(resp.split()) / elapsed`. That is a whitespace-word estimate per wall-clock second. It is not tokenizer-counted decode throughput or streamed time to first token.

The bridge's nonstream response sets `total_duration=1000000000` and `load_duration=10000000`. It also synthesizes model size, family and quantization fields in `/api/tags`, `/api/ps` and `/api/show`. Do not use those values as measurements or capability evidence.

The separate `benchmark_suite.py` sends `stream=false` and calls `load_duration + prompt_eval_duration` TTFT. Combined with this bridge, its inputs include invented durations and missing prompt/decode duration fields. Repairing the calculation alone cannot recover measurements the server never supplied.

For an MLX/eGPU comparison, retain the exact request, output-token IDs, model digest, template, requested context, sampling settings, runtime revision, warm/cold state and raw timing records. Timestamp the first generated event at the client. Report first visible text separately if reasoning or a tool call arrives first. Use actual tokenizer counts for generation rate. Measure load and prefill inside the backend with device synchronization where needed. Measure GPU allocations separately; an HTTP model listing is not a memory trace.

## The missing agent protocol

Explorer's `llmsx/llmsx/ollama_agent.py` runs Claude Code and points `ANTHROPIC_BASE_URL` at the chosen local host. Claude supplies the tool loop; the server supplies inference. It therefore needs the [Anthropic-compatible Messages protocol](https://docs.ollama.com/api/anthropic-compatibility), including tool use.

The current bridge accepts Ollama `/api/chat` and translates it to OpenAI `/v1/chat/completions`. `_handle_chat()` forwards only model, messages, stream and temperature. It drops tool declarations and request limits. `_forward_to_backend()` emits only text, dropping `tool_calls`, reasoning and finish reasons. `/v1/messages` falls through to a backend that does not implement it.

The inspected [tinygrad server](https://github.com/tinygrad/tinygrad/blob/5877c3806ab119e5cac88fed05ea935880a84b14/tinygrad/llm/serve.py) already accepts tool schemas in chat templates and parses generated `<tool_call>` regions. That is a useful starting point, but its presence does not qualify this particular model for reliable tools. The bridge must preserve those operations before Explorer can exercise them.

The proposed route is:

```text
Explorer /dr coordinator — qualified Gemma31 on MLX
  → dr_run.py research — one child at a time
    → Claude Code worker tool loop
      → Anthropic-to-OpenAI adapter on an isolated local port
        → existing tinygrad NV server
          → RTX 5080
    → local file/command tools and bounded Firecrawl relay
  → fresh Gemma31 blind gate and Explorer completion checks
```

The GPU performs inference. Claude still executes file and command tools on the Mac, and Firecrawl retrieves internet evidence. Routing a completion to a GPU does not move those tools or make research offline.

## Implementation sequence and file ownership

| Area | Proposed owner files | Required change |
| --- | --- | --- |
| Protocol adapter | New project-owned adapter module and tests under `llmsx/`; use the supplied proxy as a reference | Translate Anthropic messages, tools and results to the backend's OpenAI format; preserve responses and SSE events |
| Worker selection | `llmsx/llmsx/ollama_agent.py`, `explorer_store.py`, related runtime tests | Resolve independent worker host, model and context consistently before constructing the command and environment |
| Backend capability and limits | Adapter plus pinned `tinygrad/llm/serve.py` integration | Advertise verified capabilities; reject an unknown model, unsupported mode or oversized prompt; retain cancellation and output limits |
| Measurement harness | New focused benchmark script, separate from historical downloads | Timestamp streamed arrivals; retain tokenizer counts and trustworthy backend counters; identify missing measurements explicitly |
| Acceptance | Existing local-model probe and Explorer acceptance helpers, with explicit backend arguments | Add offline adapter contracts, then actual tool and research trials with saved artifacts |

A project-owned adapter keeps the external tinygrad checkout and the published historical benchmark scripts intact. Pin the inspected tinygrad revision and record its local patch diff before execution. If a backend change is needed, isolate it in its own patch rather than changing a shared running checkout without a record.

### 1. Preserve the complete request and response

Map system content, role messages, `tool_use` IDs, JSON arguments and `tool_result` IDs without losing their associations. Translate input schemas, tool choice, output limits, temperature and supported stop sequences. Preserve multiple tool calls and error results. Reject unsupported image, thinking or forced-tool behavior explicitly.

For streaming, emit the Anthropic message/content-block lifecycle, text deltas, tool JSON deltas, final usage, stop reason and completion event. The tinygrad parser can emit a completed tool-call object near the end of generation; do not fabricate incremental argument fragments. Handle errors after headers as stream errors, and make client disconnects cancel generation. Verify the exact Claude Code calls, including model discovery and count-tokens behavior, rather than assuming `/v1/messages` alone is enough.

Before any inference, test these mappings against a fixture backend: a two-tool round trip, two calls in one response, a tool error, malformed arguments, output-cap exhaustion, truncated SSE, an oversized request and cancellation. Require no silent fallback to a cloud endpoint.

### 2. Give the worker its own model and context

Current `command()` selects the saved Ollama provider model. `main()` repeats that selection for model environment variables. Only the worker host can differ, and a configured `ollama_worker_host` overrides `OLLAMA_HOST` for children. Exporting `OLLAMA_HOST=...:11440` alone would neither change the worker model nor guarantee worker routing.

Add a single backend-resolution function used by both command and environment construction. Proposed settings are `ollama_worker_host`, `ollama_worker_model` and `ollama_worker_context`, with documented per-job overrides. Keep them independent from the canonical coordinator model. Check the blind-gate marker explicitly so the initial gate stays on MLX. Record each phase's actual host/model/context in the manifest. If a worker fails, save a failed attempt; do not silently retry on MLX and call it an eGPU result.

The existing NVIDIA backend starts with 4K context, while the current helper's compaction default assumes 65,536 tokens. Configure worker limits and compaction for the backend's measured capacity. Test 8K, then 16K, only if memory and prompt tests pass. Use stored source bodies and narrow excerpts to keep retrieval outside the model context. Reject over-capacity input instead of truncating tool definitions or evidence.

### 3. Qualify a resident model

Use the existing Qwen2 model first to prove transport and tool round trips. Its older weights are not the proposed final research choice. A modern instruction model in roughly the 8–14B class is a candidate only after the installed tinygrad architecture loader, tokenizer, chat template and tool format pass. Record a concrete model tag and digest at that point.

Gemma12's reported 7.7 GB weight footprint makes it a sizing candidate, but its MLX container is not automatically loadable by the NVIDIA backend. Gemma support was not established for this tinygrad checkout. Its earlier fresh-research factual errors also remain a qualification concern. Gemma26/31's reported artifacts exceed 16 GB before full workspaces and cache; an alternative quantization or offload is a new candidate with new measurements.

Measure actual weight, cache and workspace allocations under the intended prompt and output length. Require headroom and no unexpected host swapping or per-token weight streaming. Memory capacity alone cannot choose a research model.

### 4. Advance through work-based acceptance

1. Run the native two-tool probe through the NVIDIA adapter. Require actual evidence reads and a saved verdict with correct full schema paths.
2. Run a fresh one-concept worker with the unchanged standard source/negation/schema contract. Review exact names, limits and source entailment. Include any correction time in the recorded attempt.
3. Keep the first blind gate on qualified Gemma31 MLX. Retain the fifteen-fetch hard cap, exact footnote-to-URL mapping, two samples per core concept and `UNVERIFIED` handling.
4. If the hybrid trial passes, run a fresh five-concept hybrid `/dr`, install its reference and execute canonical Explorer completion. Record research, correction, retrieval, gate and completion times separately.
5. Qualify an eGPU gate and coordinator independently before a full eGPU-only `/dr`. Compare accepted-work time, corrections, supported/uncertain counts and retrieval use alongside token speed.

Use an isolated research fixture and serial workers. Preserve the canonical model and the user's paused indexing. Reuse the already attached persistent daemon during execution; do not bootstrap drivers, reset the PCI bus or hot-unplug the device as part of a benchmark. The supplied harness documents concrete bus/power-management panic incidents.

## Decision and stop conditions

The first experiment should be a hybrid MLX coordinator/gate with an eGPU worker. It offers a bounded way to test the missing protocol without discarding a qualified baseline. This is separate from cross-device speculative decoding; no draft/target coordination is required to run independent research workers.

Stop qualification if tools disappear, the worker exceeds context or memory, evidence records fail, or factual review rejects claims. A faster completion does not override those failures. The next implementation deliverable is the adapter and backend-resolution tests, followed by the two-tool probe. This strategy does not claim that the attached RTX has already completed `/dr` or improved its elapsed time.
