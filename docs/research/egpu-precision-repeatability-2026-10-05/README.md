# Repeated precision measurements on the retained RTX candidate

Version: 1.4.0
Date: 2026-10-05

Oct6 correction: this report retains the historical v110 source audit and commands. The actual consuming validator later refused its own system-owned and symlinked source closure before any GPU startup. Eight system-tool hashes also changed. The v110 receiver remains unused and inadmissible; do not execute its historical commands. Follow the new source correction and current-OS control evidence in `/Users/mitch/dev/llms-explorer/docs/research/egpu-cold-capture-2026-10-06/README.md`. The original model, capture binaries and 0.05 limit are preserved.

Two CPU requests matched each other exactly at all 21 emitted selected-token logprobs. Two CUDA requests also matched each other exactly. Both CPU/CUDA comparisons reproduced the maximum absolute error 0.08756500482559204 at output index 0. The unchanged limit is 0.05, so numerical qualification remains failed. All 21 token IDs, strings, bytes and final JSON matched.

| Measurement | CPU request 0 | CPU request 1 | CUDA request 0 | CUDA request 1 |
| --- | ---: | ---: | ---: | ---: |
| Uncached prompt tokens | 64 | 64 | 64 | 64 |
| Emitted tokens | 21 | 21 | 21 | 21 |
| Prompt tokens/second | 7.6531 | 7.3472 | 16.2552 | 16.2108 |
| Generation tokens/second | 6.2364 | 6.0539 | 60.9474 | 60.9901 |
| Reused prompt tokens | 0 | 0 | 0 | 0 |

These are reported server timings for the original short arithmetic payload. They do not measure a full coding or research workload. CPU requests ran after CUDA requests, while the retained GPU owner remained resident. Their memory and timing context differs from an exclusive CPU performance benchmark.

The new receiver sent exactly two GPU requests and two CPU requests. It started one CPU-only child, which exited with code 0. It started no GPU process and reset no device. The admitted GPU owner remained unchanged. The original request, context 32768, f16 KV, batch and ubatch 256, one slot and sampler were preserved. The consumed v107/v108 receivers were not replayed.

Root independently recomputed the four pair comparisons from the raw responses. The source hashes and per-token differences are in `/Users/mitch/dev/llms-explorer/docs/research/egpu-precision-repeatability-2026-10-05/REPEAT-COMPARISON.json`. The execution result is `/Users/mitch/dev/llms-explorer/docs/research/egpu-precision-repeatability-2026-10-05/REPEAT-RESULT.json`.

The CPU command was recorded before spawn. A later supplement verified its hash against the original reference manifest; the new helper did not include that command in its pre-execution pin set. It also did not preserve the CPU birth/listener observation during the requests. Preserve these evidence limits. The completed GPU witness is cumulative for the same bound owner, model and build. No before-repeat witness was saved, so it does not isolate either request's kernel interval, tensor phase or physical peak. These limits are recorded in `/Users/mitch/dev/llms-explorer/docs/research/egpu-precision-repeatability-2026-10-05/PROVENANCE-SUPPLEMENT.json`.

Two matching short repeats support repeatability on this payload. They do not identify which operation causes the difference. The retained binary lacks raw tensor capture. A separately built diagnostic will capture the normalized vector entering the output projection and all 248320 raw pre-sampler logits. Its scheduler callback introduces synchronization, so it is a distinct diagnostic arm. Its timings cannot be treated as production throughput.

## Capture preparation and failures

The first offline capture build was rebuilt with 3854 source/header/link/tool pins, including all 1006 compiler dependencies. Independent review verified those pins and both binary hashes. Only the server context archive member changed. This proves the build binding; it does not prove the capture runs correctly.

The first CPU capture preflight refused on the unchanged memory floor before starting a process. A later control started a CPU-only process but sent zero completion requests because the HTTP reader mishandled EOF. A corrected controller sent one completion attempt. The CPU process then aborted with exit -6 and `precision capture unexpected tensor layout`. It saved only the startup capture pair. No successful request capture or numeric result came from these attempts.

The failed capture binary is blocked from GPU admission. The separate v103 successor records actual tensor geometry, handles paired empty checkpoint-prefill outputs, and binds the captured nonempty output to the exact tensor used by sampling. Startup pairs are excluded through observed request boundaries. Preserve all terminal failure receipts; there is no receiver replay.

## Corrected CPU capture

The v103 source records paired empty tensors without reading them. It retains strict one-row capture for nonempty outputs. Immediately before sampling, it compares the captured raw logits bitwise with `llama_get_logits_ith()` for the server's actual batch token index. This binds the captured row to the sampled row. Independent review checked the build and initial helper before execution; final helper hardening was acknowledged five seconds after receiver consumption. The review preserves that ordering.

Both corrected CPU requests completed with exit 0 and no errors. Each had 64 uncached prompt tokens and 21 emitted token entries. Startup pair 0 was excluded. Request 0 used valid pairs 1 through 21; request 1 used pairs 22 through 42. The final entry includes the actual EOS token 248046. Four layout events record two paired zero-row checkpoint outputs. All 42 request sampling receipts show the raw sampled row matched bitwise. Both first-token normalized vectors and full logit vectors repeat bitwise. The captured CPU responses match the uninstrumented CPU reference.

For the first selected token 4754, the raw logit is 23.959152221679688. One host float64 log-softmax calculation over all 248320 raw logits gives a log normalizer of 24.564248838659513 and selected logprob -0.6050966169798251. The server emits -0.6050691604614258, a difference of 0.00002745651839930474. This diagnoses the CPU probability processing; it is not a GPU raw-logit result or a higher-precision model oracle. The GPU side remains uncaptured, so the cause of the 0.087565 backend gap remains unresolved.

The first CPU raw vectors are preserved at `/Users/mitch/dev/llms-explorer/docs/research/egpu-precision-repeatability-2026-10-05/CPU-FIRST-NORM.f32` and `/Users/mitch/dev/llms-explorer/docs/research/egpu-precision-repeatability-2026-10-05/CPU-FIRST-LOGITS.f32`. Root's independent calculation is `/Users/mitch/dev/llms-explorer/docs/research/egpu-precision-repeatability-2026-10-05/CPU-RAW-ANALYSIS.json`. Independent full-vector/sample checks are `/Users/mitch/dev/llms-explorer/docs/research/egpu-precision-repeatability-2026-10-05/CPU-V103-REVIEW.json`.

Total capture files occupy 43625558 bytes, below the 65404928-byte cap. The callback retains a logit vector for sample binding as well as the current transient vector; the source must count both in its lifetime bound. These software bounds do not prove aggregate physical GPU peak. No whole output-weight expansion, model download or GPU reload occurred in this test round.

## Reviewed cold capture receiver

The separate v110 preparation is complete. Independent review verified all 4153 source pins and 323 CPU receipt hashes. Thirty offline controls passed. The source fixes include recognition of competing `gpu-server-capture` processes, absolute HTTP deadlines with redirects refused, and CPU manifest hash checks at each later reference read. These are software controls; they are not coding sessions or physical model acceptance tests.

Root sealed the exact reviewed closure without changing its identity or source pins. The final static review SHA256 is `ed7b7ca45ca73c354cdc08fc8d212bdc13e676b4b6be742758a2be77eac6030d`. The request preparation SHA256 is `dceb3561ea65feec47155e1da46893bd00cc14f32fb368c6a1f4a70d6dc4853d`. Source readiness passed. Physical admission, GPU captures and full qualification remain false. The final verdict is preserved at `/Users/mitch/dev/llms-explorer/docs/research/egpu-precision-repeatability-2026-10-05/COLD-V110-REVIEW.json`.

The next actual test requires a new full Mac shutdown and enclosure power-off/on while the Mac is off. After the user confirms that recovery, the agent must recheck current boot, owners, listeners, Unix socket, owner lock, fault marker, capacity and hashes before the single startup. Consumed boot `1791188232:752319` cannot admit the new binary. No reset, takeover, automatic retry or old receiver replay is allowed.

The cold startup command, run only after that physical confirmation, is:

```sh
/opt/homebrew/bin/python3 -B /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-cold-root-operation-v110/run_actual_cold_once.py --cold-recovery-confirmed --static-review-sha256 ed7b7ca45ca73c354cdc08fc8d212bdc13e676b4b6be742758a2be77eac6030d
```

Only after its exact startup result passes and the admitted owner remains valid, run the two-request capture command:

```sh
/opt/homebrew/bin/python3 -B /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-capture-response-preparation-v110/run_gpu_captures.py --execute --preparation-sha256 dceb3561ea65feec47155e1da46893bd00cc14f32fb368c6a1f4a70d6dc4853d
```

The helper compares all original emitted selected-token logprobs, preserves EOS, matches exact rendered prompt and token/BOS arrays, and analyzes the raw projection inputs and logits under one common host normalization. A successful diagnostic execution can still report a failed numerical gate. Read both outcomes. It does not establish aggregate physical peak, full coding tools, stability or canonical standard `/dr` completion.

The published scripts are exact evidence snapshots with absolute private dependencies. Execute the private originals above. Source bindings are preserved at `/Users/mitch/dev/llms-explorer/docs/research/egpu-precision-repeatability-2026-10-05/COLD-SNAPSHOT-SOURCES.json`. Preserve the original 0.05 limit and all original resource and quality gates. No fully qualified eGPU model has been established.
