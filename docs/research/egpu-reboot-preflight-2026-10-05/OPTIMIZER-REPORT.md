# v107 successor preparation review
Version: 1.0.2
Delta: Record two repair iterations. Second final blind audit passed. Scope is offline successor preparation, not physical model qualification.

## Per-iteration severity
| Iteration | Critical | High | Medium | Low | Nit |
|---|---:|---:|---:|---:|---:|
| 1 | 0 | 1 | 2 | 0 | 0 |
| 2 | 0 | 0 | 1 | 0 | 0 |

## Findings
| Pass | File and trigger | Severity | Fix | Status |
|---|---|---|---|---|
| C1/C2/C3/T1 | /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-renderer-preparation-v107/expected-inventory.json:8400 added delta to the exact parsed inventory | High | Restore the complete exact inventory bytes; keep provenance in the source plan | Fixed, red-to-green regression |
| C3/S3/S4 | /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-reboot-preflight-v100/prepare_pin_successor.py.iteration1:44 used assert for integrity gates | Medium | Use explicit RuntimeError conditions under optimized Python | Fixed, red-to-green regression |
| C3/S3/P2 | /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-reboot-preflight-v100/prepare_pin_successor.py.iteration1:74 reread transformed bytes after hashing | Medium | Verify and retain the same input bytes before transformations | Fixed, red-to-green regression |
| C3/P2 | /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-reboot-preflight-v100/prepare_pin_successor.py.iteration2:94 silently rebound changed external digests | Medium | Require each unchanged external digest to match its sealed predecessor digest | Fixed, red-to-green regression |

## Verification gate
| Command and working directory | Baseline | After repair | Verdict |
|---|---|---|---|
| /opt/homebrew/bin/python3 -B -m unittest -v test_experimental_27b test_f32_cold_delta in /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-renderer-preparation-v107 | 21 pass | 21 pass; executable controls unchanged | PASS |
| /opt/homebrew/bin/python3 -B -m unittest -v test_successor_preparation in /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-reboot-preflight-v100 | All four changed-condition regressions reproduced before their corresponding repairs | 4 pass | PASS |
| /opt/homebrew/bin/python3 -B scripts/check_publish_privacy.py in /Users/mitch/dev/worktrees/llms-explorer-egpu-reboot-preflight-v107-20261005 | No new publication bundle | Covered tree4033 clean; explicit final17 publication files clean | PASS for final explicit bundle |

## Activated reviewers
Python source/runtime and tests: /Users/mitch/.agents/skills/lang-python/SKILL.md
Security and trust boundaries: /Users/mitch/.agents/skills/security-review/SKILL.md
Baseline code and standards: /Users/mitch/.agents/skills/software-engineering-patterns/references/code-reviewer.md and /Users/mitch/.agents/skills/software-engineering-patterns/references/coding-standards.md
Optimizer rubric: /Users/mitch/.agents/skills/code-deep-optimizer/SKILL.md
Empirical evaluation is disabled. Index synchronization is disabled. No native executable, GPU, model, embedding or service operation ran.

## Diffs
Complete scoped helper/root/starter diff: /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-reboot-preflight-v100/SUCCESSOR.diff
The exact inventory is identical to its accepted predecessor. Source-plan hashes now bind that exact inventory and the explicitly changed canonical skill snapshot. Existing product renderer logic and test controls are unchanged. The root and starter change namespace literals only.

## Blind audit
The first fresh audit independently checked 305 direct pins, 281 nested bindings, exact model header inventory and 24 tests. It applies to its exact historical helper and draft hashes. The parent then reproduced the additional external-pin race. The second and final fresh-context gate passed for the corrected helper and four regressions. It checked305 direct pins,272 nested pin occurrences,10 nested path/SHA bindings, and the additional exact0.05 normative reference for306 final pins. All25 CPU controls pass. No physical qualification is issued by either static gate.

## Summary
2 repair iterations · 18 passes · explicit changed scope · Final C/H/M/L 0/0/0/0 · Verify PASS (25 CPU controls) · Status CLEAN within static successor preparation scope only

## Snapshot and offline rollback
Preserved original helper: /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-reboot-preflight-v100/prepare_pin_successor.py.iteration1
Offline restore command:
```sh
cp /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-reboot-preflight-v100/prepare_pin_successor.py.iteration1 /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-reboot-preflight-v100/prepare_pin_successor.py
rm /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-reboot-preflight-v100/test_successor_preparation.py
```
This invalidates a final successor review. Do not launch any sealed receiver after rollback. Frozen v106, model weights, native build, global skills, service settings and unrelated project changes are untouched.

index: skipped (--no-sync)
memory-central: directly verified prior hub/Ollama pause source; no target-matching convention changed this repair. Lessons: the exact inventory defect and unchanged external pin race are recorded in Stele with file/symbol anchors.
