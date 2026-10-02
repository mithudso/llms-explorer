# Native MLX greedy block verifier

Version: 0.1.0. Delta: initial token-level backend, pinned canonical manifest, independent session caches and rollback checkpoints.

This sidecar loads the existing `llmsx-research-gemma31-mlx` Ollama manifest and exposes a genuine causal block forward. It imports Ollama `v0.35.0`, whose module origin is commit `cc4069396f3ad2c370c53eed2e4a42ac13adab84`. It reads the existing per-tensor NVFP4 safetensors blobs. It does not rewrite models, change the saved LLMSX provider, or contact an Ollama completion endpoint.

The installed Ollama app reports the same revision with `vcs.modified=true`. The sidecar uses the published source, so its output and numerical behavior must be qualified separately against the installed runtime. Loading the same weights is not proof of token parity.

## Build and preflight

Prerequisites: Go 1.26 or newer, CGO, an Apple Silicon Mac, Xcode/clang and a compatible Ollama app with native MLX libraries. The inspected host has Go 1.27.1 and bundled `mlx_metal_v4`. An existing compatible library avoids compiling MLX with CMake. Ollama's loader discovers libraries relative to the sidecar executable; `DYLD_LIBRARY_PATH` alone does not supply its discovery root.

From this directory:

```sh
go test ./...
go vet ./...
mkdir -p /tmp/llmsx-speculative-native/lib
# Create this link only if it does not already exist.
ln -s /Applications/Ollama.app/Contents/Resources /tmp/llmsx-speculative-native/lib/ollama
go build -o /tmp/llmsx-speculative-native/speculative-mlx .
/tmp/llmsx-speculative-native/speculative-mlx --probe
```

`--probe` checks the canonical manifest, tokenizer metadata and native Metal runtime without loading model weights. Omitting `--model` on an ordinary launch exits without loading weights. The default required manifest SHA256 is `559e7d6999dbf031c7f842e84257eea6d43a8adcb6ff90a727baa05d4a5e6b0d`. A changed manifest fails before loading.

Start only after checking unified-memory headroom and confirming another copy of the target is not resident:

```sh
/tmp/llmsx-speculative-native/speculative-mlx \
  --model llmsx-research-gemma31-mlx \
  --listen 127.0.0.1:11551 \
  --max-context 4096
```

Only loopback addresses are accepted. The service defaults to one active cache session, a 16-token maximum proposal block and 512-token prefill chunks. `--max-context` caps this experiment without changing the model's saved 65,536-token research setting. Request an increased cap explicitly for the later long-context gate. Stop this user-owned process with SIGINT or SIGTERM to free its sessions and model arrays.

## Protocol

`GET /health`, `GET /describe` and `POST /rpc` with `{"op":"describe"}` report the loaded model, artifact/source identity, MLX library and runtime version, vocabulary, full canonical tokenizer fingerprint, special token IDs, EOS IDs and capabilities. `mlx_c_source_revision` identifies the imported module's declared MLX-C dependency; it does not prove the bundled library was built from that source. This backend supports greedy block verification and rollback. It does not implement stochastic speculation or RTX drafting.

All operations use `POST /rpc` with JSON. The response is one JSON document. Failures return an HTTP error and `{"error":"..."}`. Requests are limited to 4 MiB.

| Operation | Request fields after `op` | Main result |
|---|---|---|
| `tokenize` | `text`, optional `add_bos` | `token_ids` |
| `decode` | `token_ids` | `text`, `valid_utf8` |
| `open` | `prefix_ids`, `session_id` | `state`, `prefill_ms` |
| `verify` | `state`, `token_ids` proposals, optional `inspect_ids` | `state`, `target_ids`, `verify_ms`, `target_forward_count`, optional selected logits |
| `commit` | `state`, `token_ids` committed output | next `state`, `done`, `cache_offsets` |
| `rollback` | `state` | unchanged committed `state`, restored offsets |
| `state` | `session_id` or `state` | prefix, pending status and offsets |
| `close` | `session_id` | `closed` |

The complete state is `{session_id, round_id, prefix_digest, position}`. Prefix digest hashes `b"llmsx-token-prefix-v1\0"` followed by each token encoded as a big-endian unsigned 32-bit integer. Verification and commit require the exact current state. A stale round, incorrect digest or conflicting session ID returns HTTP 409/400 before a target forward.

For proposals `[d0, ..., d(k-1)]`, `verify` returns `k+1` argmax IDs. Row `i` predicts the next token at the committed prefix plus proposals `[:i]`; the last row is the bonus prediction. The coordinator accepts the matching prefix and uses the target prediction at the first mismatch. `commit` accepts only an exact prefix of this target-certified run. It supports truncation at the output budget and EOS, and rejects output after EOS. A second verification requires commit or rollback of the first.

For diagnostics, `inspect_ids` selects at most eight valid vocabulary IDs. The verifier gathers those columns from the same `Unembed` output that produces its argmax; it performs no second target forward. The response adds `inspect_ids`, `inspect_shape: [k+1, N]` and a flat row-major `inspect_logits` array in the requested ID order. Scores convert to float32 after the model's existing unembedding, softcap and suppression. Nonfinite cells are JSON `null`; `inspect_nonfinite` maps their flat indices to `-inf`, `+inf` or `nan`. Inspection adds work to the lazy graph, so compare inspected and ordinary predictions before treating the diagnostics as evidence about an unchanged execution path.

Example request sequence:

```json
{"op":"open","session_id":"experiment-1","prefix_ids":[2,105,111]}
{"op":"verify","state":{"session_id":"experiment-1","round_id":0,"prefix_digest":"<returned digest>","position":3},"token_ids":[123,456]}
```

Use the state returned by `open` and the actual verified output IDs for `commit`; the IDs above illustrate the schema and are not a benchmark prompt.

## Cache convention and transaction behavior

Logical `position` counts every committed token. The native cache holds all committed tokens except the last token, which remains pending. A verifier forwards `[pending_token] + proposals` in one causal block. It snapshots each possible rollback boundary, including the pre-write boundary for an explicit abort. `commit` retains only the predecessor states of the final emitted token and makes that token pending. No extra full target forward is required to incorporate the correction or bonus.

Each session uses `Model.NewCaches()` and shares only read-only model weights. Native snapshots restore rotating windows when a live rewind cannot reach the requested offset. Every commit checks that all cache offsets match the required pending-token position. A failed native operation invalidates the affected session. Cancellation cannot preempt an already dispatched Metal graph; after it completes, the service discards the disconnected request's session. The coordinator must close its draft session as well.

The bundled Gemma assistant loads with the canonical manifest but this sidecar's verifier does not call it. Measure the installed Ollama assistant baseline independently; do not label these greedy results as assistant-enabled.

## Prompt and compatibility discipline

The sidecar accepts already rendered token prefixes. It does not choose a chat template or execute tools. Use exactly the same prefix IDs for target-only and speculative trials. For an installed-Ollama comparison, send the same rendered prompt through `/api/generate` with `raw=true` and neutral greedy sampling settings.

The canonical alias container uses renderer `gemma4`. The pinned renderer resolver chooses the large template only when a model name contains `12b`, `26b` or `31b`, or its model-type field identifies at least 12 billion parameters. The alias contains `gemma31` without the trailing `b` and its container model-type field is empty. The pinned source therefore chooses the small no-thinking template for this alias. The installed dirty build may differ; verify its actual rendering before a chat-endpoint parity claim.

The small text-only no-thinking prefix is:

```text
<bos><|turn>user
USER_PROMPT<turn|>
<|turn>model
```

The displayed format includes the logical BOS token. If the literal `<bos>` string is already present, call `tokenize` with `add_bos=false`, or use the verified actual default. The canonical tokenizer reports `tokenizer_add_bos=false`. Keep the literal BOS in both native and raw Ollama fixtures; omitting it produced repeated separators in the initial controls. The sidecar reports the actual policy in metadata.

An optional first system turn precedes the user turn. The large no-thinking template adds `<|channel>thought\n<channel|>` after the model cue. Switching from the alias to the official base may therefore change prompt formatting. The decoder returns `valid_utf8` before JSON serialization can replace partial UTF-8 byte sequences. The Python facade must treat false as an alignment fallback, rather than accept the repaired text. Full tokenizer fingerprint equality checks token semantics; it does not establish chat-template equivalence.

## Validation scope

The unit suite checks independently computed prefix hashes, Unicode tokenizer canonicalization, complete state rejection, exact context capacity, first/partial/full acceptance, correction, output truncation, EOS and snapshot fallback. The pure cache double verifies restoration ordering and cleanup, but does not prove real Metal rotating-cache correctness.

The required hardware gate compares token-by-token greedy output with block verification, forces rejection before and after the 1,024-token window, checks abort/retry, and compares actual cache offsets and completed token streams. Later gates cover the intended research context, structured output and tool syntax before throughput claims. No cross-device speedup follows from a passing build or preflight.

The [same-prefix diagnostic](../../docs/research/speculative-decoding-block-parity-2026-09-30.md) observes score and greedy-selection differences across verification shapes and cache construction histories. Shape-dependent MLX arithmetic is a hypothesis for the observed 64-token block-versus-single-token parity failure. The imported `mlxrunner/nn/linear.go` passes the full query shape to `mlx.QuantizedMatmul`; `mlxrunner/nn/sdpa.go` also treats single-query and causal-block attention differently. Local MLX 0.32.1 kernel headers show different floating-point reduction orders in single-vector, small-batch vector and tiled NVFP4 projections, plus different attention arithmetic. The actual bundled library reports `0.32.2-65-g59d600b`, and includes these kernel families. Available kernels do not establish which one ran. The exact dispatch and cause of the divergence remain unproven. Trace them before proposing a fix or claiming exact parity.
