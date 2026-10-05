# One future v107 response

Version: 1.0.0
Delta: Verified standalone first-response helper, separate from the sealed cold receiver.

No GPU test ran during this preparation. The helper has85 offline controls and an independent static final review. The optimizer reached its10-minute budget; all six corroborated Medium findings were corrected, original dissent is retained, and the second final blind gate found no Medium-or-higher findings. This is software review only.

The original physical v105 run returned correct arithmetic JSON at59.098 generation tokens/s. It failed the unchanged selected-token tolerance: maximum absolute logprob difference0.06316304206848145 exceeds0.05 at the first token. All21positions remain required.

The user reported a reboot. The last passive boot was1791188232:752319 and recognized native/transport owners were absent. Full Mac shutdown plus enclosure power-off/on confirmation is still unanswered. The sealed v107 receiver remains unused; its future runtime and this helper's future result directory remain absent.

## Offline verification only

```sh
/opt/homebrew/bin/uv run --offline --no-project --with pytest python -B -m pytest -q -p no:cacheprovider /Users/mitch/dev/llms-explorer/docs/research/egpu-first-response-v107-2026-10-05/test_run_once.py
```

Expected:85 software controls pass using saved responses and temporary synthetic receipts. This command does not send a model request. The fixture source paths are machine-specific frozen inputs.

## Conditional physical continuation

First obtain the exact cold-cycle fact. Then repeat the existing owner/boot preflight and run the independently sealed cold receiver only once:

```sh
/opt/homebrew/bin/python3 -B /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-cold-root-operation-v107/run_actual_cold_once.py --cold-recovery-confirmed --static-review-sha256 ca03acf7b377483824fca73972e929fccd6432b8e655ca0dafc7c00510e4b289
```

Only after that actual operation and runtime both pass, use the retained same native and driver owners:

```sh
/opt/homebrew/bin/python3 -B /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-first-response-preparation-v107/run_once.py --execute --preparation-sha256 ec52d80517cba17647af0669f3efdae887ac73b5cee2c08a24d19e0e8391cfcc
```

The helper verifies sealed cold/root/runtime bindings, current complete model and diagnostic binary, boot and process birth/UID/command, both inference and transport listeners, held lock, fault latch, recognized other workers and idle model/context metadata. It disables environment proxies and redirects. It sends exact original CPU request bytes at most once. It retains bounded success or error bytes, marks truncation, compares all21selected tokens, and reports the original0.05 numerical result separately from functional output. Terminal persistence failure reports the true attempted request count. It never starts or resets a process and never retries.

Success here still leaves actual placement/aggregate peak, the original fresh coding pair, repeated-session stability and a genuine standard /dr with validated artifacts. A failure preserves its consumed marker and evidence. No model cleanup, service action, index resume, new model download, global harness default change or qualification-floor change is part of this preparation.

## Local continuation

Preparation SHA256: ec52d80517cba17647af0669f3efdae887ac73b5cee2c08a24d19e0e8391cfcc

Preparation receipt: /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-first-response-preparation-v107/PREPARATION.json

Future result (currently absent): /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-first-inference-v107/RESULT.json

Parent cold trial task: TASK-576. Helper preparation: TASK-588. Final task status and publication receipt are retained separately; this receipt remains sealed.
