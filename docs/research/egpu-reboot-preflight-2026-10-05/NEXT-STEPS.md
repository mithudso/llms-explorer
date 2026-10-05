Version: 1.0.0
Delta: New v107 receiver is statically sealed; explicit physical cold-cycle confirmation remains missing.

Do not execute until the user explicitly confirms full Mac shutdown and enclosure power-off/on while the Mac was off. Reboot alone does not establish that fact. Recheck all recognized owners and live boot immediately before execution. Preserve any unrelated active work.

After the fact is confirmed and no owners conflict, the root agent may execute exactly once:

/opt/homebrew/bin/python3 -B /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-cold-root-operation-v107/run_actual_cold_once.py --cold-recovery-confirmed --static-review-sha256 ca03acf7b377483824fca73972e929fccd6432b8e655ca0dafc7c00510e4b289

If startup is admitted, prepare a same-new-owner request helper from its actual fresh startup receipts. Do not reuse the consumed v100 request helper. Use unchanged original CPU REQUEST and RESPONSE and pinned PREFLIGHT tolerance0.05. Keep all21 selected-token positions. No rerun of the accepted CPU baseline, tolerance relaxation, first-token omission or reset retry is allowed. Numerics, actual operator/placement/peak, two full-tool coding sessions, genuine standard /dr and activation remain unverified.
