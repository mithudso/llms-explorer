# Bounded CPU projection control and next GPU source proposal

Version: 1.1.0

Delta: Preserve the rejected direct-dot v112 control and the separately accepted explicit CPU_REPACK v113 control. No GPU correction has been compiled or run.

The sole selected-row CPU helper compiled successfully and executed once in 0.122 seconds. It exited 2 because all three reconstructed CPU raw logits differ from the recorded CPU logits. The helper correctly refused residual interpretation. Its data buffers occupy 76,664 bytes; it read 10,560 model-row bytes, 40,960 saved norm bytes and 24 saved raw-logit bytes. It made no GPU initialization or request.

| Token ID | Recorded CPU raw logit | Direct CPU helper raw logit | Signed F32 ULP difference |
| --- | ---: | ---: | ---: |
| 4754 | 23.959152221679688 | 23.959157943725586 | +3 |
| 90 | 23.76719856262207 | 23.767196655273438 | -1 |
| 71093 | 17.973369598388672 | 17.973373413085938 | +2 |

These tiny oracle differences are a limitation of this reconstruction. They neither replace nor relax the model's original 0.05 selected-logprob gate. Both actual v111 GPU requests still fail that gate at 0.08756500482559204. The raw hidden-state discrepancy already precedes output projection. The complete physical capture evidence is recorded at /Users/mitch/dev/llms-explorer/docs/research/egpu-cold-capture-2026-10-06/README.md.

## What was independently verified

The source review checked all 18 frozen proposal pins, exact row offsets/hashes, two finite norm vectors, six bound raw logits, ABI sizes, unchanged CPU/base archive hashes, and absence of GPU/backend/model-init calls. The actual build review checked ARM64 Mach-O identity, 153 compiler dependencies (134 previously bound and 19 current headers), exact compile arguments/environment, and only libc++,libSystem and Accelerate imports. A separate binary-symbol review confirmed that the exact executable defines the three intended CPU quantization/dot functions. Actual loaded compiler/linker handles and full dyld-cache content were not sampled during the short compile.

The execution review checked the one terminal exit2, no retry or timeout, saved output identity and the three F32 bit comparisons. All three strict comparisons failed. No attribution from the gated residual fields is accepted.

## Source proposal and its limits

The actual GPU prompt splits into 60 tokens followed by 4 tokens at recurrent checkpoint 59. The existing CUDA dispatcher selects MMVQ before MMQ/cuBLAS for the small tail. Setting F32 cuBLAS computation alone does not establish that the four-token MMVQ route uses F32 activation math.

The frozen v112 diagnostic patch bypasses MMVQ only for 2–8 columns of Q2_K,Q4_K and IQ2_XXS. Its macro-off source is byte-identical to the original. The separate diagnostic allocator patch refuses an allocation failure before synchronization, eviction or retry. Its 2 GiB cap covers cached plus checked-out bytes in one legacy scratch pool. It does not prove aggregate scratch allocation across pools, model/graph/driver residency or physical peak. The 388 target trunk matrices and 1,012,924,416-byte one-each rounded-cache sum are source/arithmetic observations. They are not placement or peak measurements.

Independent source simulation passed 84 dispatch and 7 allocator controls. Those controls did not compile or exercise a GPU consumer. A future MMVQ replacement must also preserve its embedded device binary; the old MMQ host-only replacement command cannot be replayed indiscriminately.

After the oracle refusal, source investigation ruled out an invented two-column Q5_K dot path: Q5_K's CPU trait requires one row and its ARM routine asserts nrc=1. The captured norm/output tensors themselves have one column. CPU_REPACK has a separate eight-row Q5_K path. The separate explicit control below reproduces selected values; the historical full-reference operator remains unidentified.

## Safe verification and continuation

Verify the saved snapshots without compiling, loading a model or contacting a backend:

```sh
python3 -B /Users/mitch/dev/llms-explorer/docs/research/egpu-selected-projection-2026-10-06/verify_evidence.py
```

Expected result: evidence_integrity_pass=true, v112_direct_CPU_bitwise_oracle_pass=false, v113_explicit_repack_CPU_bitwise_oracle_pass=true, full_qualification=false.

TASK-613 tracks the remaining source preparation and exact CPU projection oracle. The current transport 45957/native 45967 owners remain retained. Do not replay any consumed startup or request receiver. Preserve the original context 32768, f16 KV, batch/ubatch 256, single slot, all workspace/driver/output/safety reserves, full coding tools and canonical standardDR contract. Numerical, aggregate physical peak/placement, fresh coding/stability, standardDR artifacts and deployment acceptance remain incomplete.

## Corrected explicit CPU_REPACK control

The separate v113 control explicitly initializes the CPU backend and selects its CPU_REPACK Q5_K 8×8/Q8_K buffer trait. It checks actual NEON/i8mm support and the exact RTTI identity. It reads three eight-row groups, one saved norm column at a time, and performs six bounded CPU graph calls with eight threads. The graph arena is 1 MiB, actual planned workspace is 6,352 bytes, and the original 32 MiB logical data limit remains unchanged.

One compilation succeeded in 0.405 seconds. The reporting wrapper then rejected an incorrect unmangled-C expectation for the existing C++ repack symbol. That refusal is preserved. Passive Mach-O symbol analysis corrected the reporting expectation; no recompile occurred. Independent review accepted all 827 compiler dependencies and CPU-only imports. The first comment in the frozen source retains an inaccurate no-backend-init claim; the actual, authorized behavior is explicit CPU-only initialization.

The helper executed once in 0.130 seconds. All three saved CPU raw logits reproduced bitwise. Independent review verified the execution binding, features, exact trait, workspace and arithmetic. An independent Q5_K decoder plus compensated float64 dot also reproduced all six mathematical controls exactly.

| Token ID | Recorded CPU | Same explicit CPU graph with GPU norm | Recorded CUDA | Shared-route hidden contribution | Remaining projection difference |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4754 | 23.959152221679688 | 22.746320724487305 | 22.767013549804688 | -1.2128314971923828 | +0.020692825317382812 |
| 90 | 23.76719856262207 | 22.33134651184082 | 22.354034423828125 | -1.43585205078125 | +0.022687911987304688 |
| 71093 | 17.973369598388672 | 17.313894271850586 | 17.2977352142334 | -0.6594753265380859 | -0.0161590576171875 |

Each row decomposes the recorded raw-logit difference exactly. Under this shared explicit projection, changed hidden input accounts for the larger absolute contribution in these three selected rows. This is selected-value evidence. It does not identify a unique historical operator, compute a full-vocabulary normalizer or establish an all-position logprob fix. The original all21 0.05 GPU gate still fails. No model inference or GPU request ran in either projection helper.

The next source proposal must bound scratch across up to eight per-stream pools and preserve the exact embedded device binaries in both host objects. The old per-pool bound and fatbin-free MMQ replacement recipe are insufficient admission for that new build.
