# Bounded F32 checkpoint-tail host build

Version: 1.1.0
Delta: add the independently accepted actual compiled artifact and current dependency review.

The Qwen3.6-27B IQ2_XXS numerical gate remains failed at 0.08756500482559204 against the original 0.05 limit. The raw hidden-state and selected CPU projection controls are published separately in /Users/mitch/dev/llms-explorer/docs/research/egpu-cold-capture-2026-10-06/ and /Users/mitch/dev/llms-explorer/docs/research/egpu-selected-projection-2026-10-06/. This bundle prepares the next physical numerical experiment. It reports no new GPU request, repair, full coding pass, standard /dr completion or model deployment.

## Why this build exists

The measured 64-token prompt splits into 60 tokens, then a four-token checkpoint tail. In the inspected CUDA dispatcher, MMVQ precedes cuBLAS. The previous F32 cuBLAS setting therefore does not establish F32 computation for that small tail. The new host dispatcher bypasses MMVQ for 2–8-column multiplies of Q2_K, Q4_K and IQ2_XXS weights. It retains one-column decode and the Q5_K output projection. The original context32768, f16KV, batch256 and 0.05 numerical limit remain required.

The old per-pool scratch ceiling did not bound eight stream pools plus separate cuBLAS workspaces. The new process-wide atomic ledger charges cached and checked-out legacy scratch and prepays 256MiB per context for cuBLAS capacity under the unchanged 2GiB workspace ceiling. It refuses an allocation before attempting a reset or eviction retry. The exact compiled CPU header passed 27 accounting and concurrency controls in one 0.1003-second run. These CPU controls do not measure CUDA lifecycle or total physical peak. Model weights, graph and KV allocations, driver reserves and safety margins retain their separate acceptance requirements.

## Actual build results

The first arm materialized its inputs, then the host compiler failed with `Operation not permitted`. The sandbox still allowed the v116 directory while the commands targeted v117. Both author and reviewer missed that correspondence. Its receiver, terminal failure and exact policy are preserved. No object, second compile, archive replacement, link or GPU action followed that failure.

A separate v121 successor corrected the literal output path. Actual allowed and forbidden write probes passed. The v122 wrapper changed six literal mappings from the accepted controller, and independent review confirmed byte-for-byte normalized equality. It then executed one materialization, two host-only compiles, one archive replacement and one link, each with exit0 and no retry. Host compiles took 1.212s and 1.429s; the archive replacement took 0.073s and the link 0.136s. These are build timings, not inference benchmarks.

The build produced the ARM64 executable /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-small-prefill-global-scratch-build-v121/gpu-server-capture-small-prefill-global-scratch, SHA256c1fb382b5557f3dabdb76241f9ee2f9167e87eac208878f23116a34cbf6d19d9. It preserved the original40208-byte and5708600-byte device payloads, wrapper bytes and normalized registration identities. The archive contains188members, with186unchanged. The executable has never been invoked, including --help. Independent compiled artifact review passed. It verified all 188 members, both complete registration routes, the seven-import ARM64 binary and 899 unique current dependency paths. Its exact receipt and audit source are saved in this bundle.

The successful compiler depfiles expose881and779 lexical inputs. Current dependency hashes are recorded after compilation. Newly discovered dependencies do not become proof of historical archive provenance or a precompile hash binding merely because their current files match. The next startup seal must bind these actual current dependencies.

## Verify saved evidence

```sh
python3 -B /Users/mitch/dev/llms-explorer/docs/research/egpu-tail-build-2026-10-06/verify_evidence.py
```

The verifier checks every saved snapshot hash, all40 frozen source mappings, original limits, actual five-stage terminal results, recorded archive/object/payload bindings and the original refusal and CPU control results. It never compiles, contacts a service, opens a device or loads a model. It validates saved evidence integrity, not current private artifact bytes, numerical repair or full qualification. Original private-path scripts are preserved as historical source; do not run them as new authorities.

The complete publication inventory will be written to /Users/mitch/dev/llms-explorer/docs/research/egpu-tail-build-2026-10-06/SESSION-FILES.txt. Source mappings retain each original absolute private path. Model weights, objects, native executables and archives are deliberately absent from this Git publication.
