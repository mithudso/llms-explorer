Version: 1.0.0
Delta: Final independently reviewed source and root-bound receivers; no physical action performed.

These commands are conditional. A new full Mac shutdown and enclosure off/on while the host is off must occur first. The current consumed boot1791188232:752319 cannot admit this receiver. Preserve the current owner until physical recovery. No automatic restart, reset or retry.

After the new physical recovery is explicitly confirmed, run this exact one-use startup command:

```sh
/opt/homebrew/bin/python3 -B /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-cold-root-operation-v110/run_actual_cold_once.py --cold-recovery-confirmed --static-review-sha256 ed7b7ca45ca73c354cdc08fc8d212bdc13e676b4b6be742758a2be77eac6030d
```

Only after that command exits zero with a bound successful startup and current guards pass, run exactly two capture requests:

```sh
/opt/homebrew/bin/python3 -B /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-capture-response-preparation-v110/run_gpu_captures.py --execute --preparation-sha256 dceb3561ea65feec47155e1da46893bd00cc14f32fb368c6a1f4a70d6dc4853d
```

The capture arm is diagnostic. It does not prove speed, aggregate memory peak, full coding tools, long stability, or standard /dr completion. Preserve the original0.05 selected-logprob gate.
