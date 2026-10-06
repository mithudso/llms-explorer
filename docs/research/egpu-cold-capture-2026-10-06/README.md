# Cold capture after physical recovery

Version: 1.2.0
Date: 2026-10-06

The user confirmed the requested physical cold recovery. The fresh boot is `1791277640:498901`, on macOS 27.2 build 26B5101f. Initial passive checks found no recognized GPU, driver, local adapter or Claude owner. One admitted GPU startup and exactly two capture requests completed without errors or resets. Full model qualification remains false.

The previous short-response CPU/GPU comparison remains a failure: maximum selected-token log-probability error was 0.08756500482559204, against the unchanged 0.05 limit. The two retained GPU repeats reported approximately 60.95 and 60.99 generated tokens per second. Those figures describe a short arithmetic payload; they do not establish coding or research performance.

## A real admission failure before startup

The frozen v110 receiver cannot admit its own reviewed source closure. Its `verify_pins()` function applies private-file rules to system inputs. The closure contains 520 aliases resolving through symlinks and 1,113 system-owned files. The actual consuming validator refuses with `File owner differs`; an isolated Apple SDK alias refuses with `Canonical nonsymlink path required`.

All 4,153 paths still exist. Eight system-tool hashes differ from the reviewed Oct5 bytes. The model and capture binaries still match. The changed inputs are seven `/usr/bin` tool dispatcher paths and `/usr/bin/sandbox-exec`. This records changed bytes without attributing their cause.

The source-only Oct5 audit verified hashes and fixture controls. It did not establish that the real consuming predicates admitted this complete closure. The new refusal corrects that interpretation. Every frozen v110 file and unused receiver is preserved. The new source version is separate.

## Corrective experiment

The v111 successor separates exact source/system alias bindings from strict private authority-file checks. It must exercise its consuming validator against the complete actual closure and reject alias retargeting, byte or owner drift, and private-file violations. It preserves historical build-tool identity separately from current runtime identity. No capture binary is rebuilt.

The old CPU captures did not bind Apple's shared-library cache. Exactly two current-OS CPU capture requests used the unchanged v103 CPU binary in a new receiver. Independent review verified exit0, all 323 manifest entries, 86 finite exact-shape raw vectors bitwise identical to the historical pair, both 21-entry emitted comparisons with maximum error 0, and exact rendered-byte/token/BOS identity. Their manifest is `c1357b03f9a504d7bddde19b247e1f649cb707c95d6aaa9f4f4c0c5691619a53`. These are CPU controls, with no GPU initialization.

The reviewer independently normalized the complete 248320-logit vocabulary at all 42 sampled positions. The maximum difference between emitted log-probability and float64 raw-logit normalization was 0.00002745651839930474. Startup pair 0 was excluded; EOS was included. The current 84 dyld header/stat records match, but this is not a full shared-cache content hash or loaded-image proof. The final independent CPU source hash confirmation followed execution; no prior final independent receipt is claimed.

Independent review passed the real 4509-pin source closure, 1672 external bindings, startup identity/recheck and both source-plan consumers, plus 49 accept/refuse controls. The author separately passed 30 retained and 39 new controls. Root sealed the exact static and request authorities. One transport and one native process started on the confirmed boot. Two uncached GPU captures then completed on that same owner. The original context, f16 KV, batch sizes, memory reserves, tool sets, sampler and 0.05 numerical limit remained in force.

## Continuation and remaining acceptance

The cold-admission repair task, TASK-610, and physical capture task, TASK-609, are complete. The numerical diagnostic parent, TASK-603, and full qualification task, TASK-482, remain active. TASK-613 prepares a bounded checkpoint-tail source correction and offline output-head controls.

The remaining model requirements are the numerical gate, actual placement and aggregate memory evidence, fresh full-tool coding sessions, stability and cache controls, genuine canonical `/dr` with validated artifacts, and verified deployment. A CPU reference, source audit or raw-vector capture is not full acceptance.

Private execution context: `/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-cold-capture-execution-20261006/ROOT-MEMORY.json`.

Private independent audit: `/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-cold-capture-independent-review-20261006/`.

The source refusal did not require a second physical recovery. This boot has now run the one admitted startup and two captures. Preserve native 45967 and transport 45957. No warm stop, reset, retry or additional inference is authorized by the offline preparation.

## Actual GPU results

Independent review verified all 43 response-receipt pins and 304 capture pins, 86 finite full raw vectors, 42 pre-sampler rows including EOS, and the exact 64-token prompt/rendered/BOS binding. All 21 hidden/logit rows repeat bitwise between the two GPU requests. Both emitted responses exactly reproduce the earlier uninstrumented CUDA result.

Both original CPU/GPU comparisons fail at the first output position: maximum selected-token error 0.08756500482559204 against 0.05. Common float64 normalization retains 0.0875266946578428. GPU probability processing differs only 0.00006576668614854952 from that raw normalization. The first normalized hidden vector differs by maximum 2.728110134601593, relative L2 .33220352092066785 and cosine .9450001650703492. The full-vocabulary raw-logit maximum difference is 3.8300201892852783. This establishes upstream state disagreement; it does not identify the faulty operation.

The synchronized diagnostic requests report 56.53087009488707 and56.78 generated tokens/sec. They use capture callbacks that partition/synchronize the graph. These figures do not establish production coding throughput, repeated-session stability, per-tensor placement or aggregate peak memory.

## Next bounded correction

The actual prompt log splits 64 tokens into 60, a recurrent checkpoint at position 59, then 4 tokens. The first sample binds batch_token_index3. Small quantized multiplies can select MMVQ before cuBLAS; the F32 compute setting only affects cuBLAS. Prior F32 prefill therefore does not establish F32 tail routing.

The source-only proposal will bypass MMVQ for the same eligible trunk types at 2–8 columns, preserving one-column decode and the Q5_K output head. It must retain the original 2GiB workspace and all other gates. The largest eligible F32 weight matrix is 356,515,840 bytes; rounded unique-size sums are not aggregate residency proof. A separate offline selected Q5_K row-dot analysis can distinguish inherited hidden-state error from output projection error without another GPU request or whole-head F32 expansion. Neither experiment has yet established a numerical fix.

## Reproduce saved-evidence validation

This command reads the saved snapshots. It does not import the inference helpers or contact the native server.

```sh
python3 -B /Users/mitch/dev/llms-explorer/docs/research/egpu-cold-capture-2026-10-06/verify_evidence.py
```

Expected: evidence_integrity_pass:true, exactly two CPU and GPU responses, both CPU_GPU_max_errors 0.08756500482559204 and candidate_numerical_pair_pass:false. Full qualification remains false. The published startup/request scripts are immutable evidence snapshots with private absolute dependencies. Their one-use receivers are consumed; do not replay them.
