# Physical F32 prefill trial, 2026-10-05

Version 1.0.0. Delta: the prepared F32 trial now has actual hardware results. The user confirmed full Mac shutdown and enclosure power-off/on while the Mac was off. All 306 sealed input hashes matched before consumption. One cold startup passed on boot 1791188232:752319. TinyGPU 2592 and native 2602 remained the same owners through one original model request.

| Metric | Earlier non-F32 trial | F32 prefill trial |
|---|---:|---:|
| Uncached prompt tokens |64|64|
| Generated tokens |21|21|
| Prompt evaluation, tokens/s |289.9273|16.0930|
| Generation, tokens/s |59.0978|59.8011|
| Complete request, seconds |0.561855|4.317361|
| Maximum selected-token absolute error |0.063163|0.087565|
| Original numerical tolerance |0.05|0.05|
| Correct JSON and identical token sequence |yes|yes|
| Numerical acceptance |failed|failed|

These trials ran on different user-confirmed cold boots. This is not a matched same-boot on/off causal benchmark. The new trial used F32 prefill on eligible Q2_K, Q4_K and IQ2_XXS matrices. It retained quantized decoding and Q5_K output. Completed witness data includes 484 tinyblas_gemm_f32 stamps. Those stamps prove that F32 kernels executed; they do not attribute each tensor or prove aggregate physical peak memory.

The first request helper refused before creating its output directory or sending a POST. It expected TinyGPU on legacy TCP 14013. The admitted startup uses a private Unix socket. A separate v108 helper binds the actual socket path, device/inode, UID, permissions and admitted driver PID/birth. It also retains native TCP 8000, boot, lock, other-owner, fault, idle-slot, model/context and immediate pre/post request checks. All 95 offline controls passed. An initial CPU fixture used an overly long macOS AF_UNIX path; shorter canonical temporary paths fixed that fixture. No hardware restart occurred for this fix. The sealed v107 cold receiver and original helper were not edited.

The one real request returned {"sum": 42, "product": 56, "gcd": 6}. All 21 selected token IDs, text and bytes matched the CPU reference. The maximum error remains at first token. F32 prefill did not fix the original numerical failure. No numerical tolerance, token position, full tool schema or research contract was relaxed.

The measured one-shot startup and request are complete. The broader qualification remains incomplete: numerical diagnosis, actual placement and aggregate physical peak, fresh full Claude Code coding pair, repeated-session stability, genuine standard /dr with canonical artifacts, and final launcher deployment. The current native owner remained healthy and was retained. Do not consume either one-shot receiver again or use these results as production qualification.

## Reproduce software controls only

```sh
PYTHONDONTWRITEBYTECODE=1 uv run --directory /Users/mitch/dev/llms-explorer/hub --no-sync pytest -q /Users/mitch/dev/llms-explorer/docs/research/egpu-f32-trial-2026-10-05/test_run_once.py -p no:cacheprovider
```

Expected: 95 passed. These tests do not perform GPU inference. The operational source contains machine-local evidence paths and is a preserved experiment, not a production launcher.

## Evidence and continuation

The exact commands, startup/request results, complete comparison, response, witness snapshot, software checks, preserved guard refusal, prompt and continuation memory accompany this document. Private runtime evidence remains at:

/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-cold-root-operation-v107

/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-cold-runtime-v107

/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-first-inference-v108

/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-confirmed-execution-v100

Future precision work must separate changed output-projection/activation quantization from prefill and recurrent-state differences. This run alone does not establish a cause. Source changes must use a separate candidate and preserve current receipts and all original acceptance floors. No new hardware trial is prepared or authorized by this document alone.
