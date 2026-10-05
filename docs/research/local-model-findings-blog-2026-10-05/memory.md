# Comprehensive local model findings publication

Version: 1.0.1

Delta: Complete overview, source map and local verification. Preserve historical and reported scopes.

## Intent and constraints

The user requests all findings to date in a site blog. Create a coherent overview while keeping the earlier detailed articles unchanged. Preserve recorded MLX phases, reported-only MLX throughput, actual historical coding passes, terminal research failures and the latest original numerical failure. Do not transfer acceptance between models or lower any qualification requirement.

No model requests, GPU operations, indexing, service changes, launcher promotion or weight downloads are part of this publication. The primary checkout contains unrelated staged and untracked work. Publish from a separate branch based on the latest main revision.

## Evidence gathered

- Gemma31 MLX performed one fresh research worker and correction, followed by a gate and completion over existing Qwen-origin research. It was not a fresh five-worker Gemma-only benchmark.
- Reported MLX rerun figures lack complete raw counters and streamed first-token timestamps.
- Earlier physical 4B, 9B and 27B coding results have bounded fixture acceptance. Physical standard research remains unaccepted.
- Terminal Qwen3.5 27B research attempted all five concepts and finished BLOCKED with zero accepted concepts.
- Full coding and selected research payloads fit the projected Qwen3.6 32k window. This is CPU vocabulary/template evidence, not live task success.
- Qwen3.6 F32 cold startup passed. One correct response measured 59.8011 generated tokens/s, 16.0930 prompt tokens/s and 4.31736 seconds. Numerical difference 0.087565 failed the unchanged 0.05 limit.
- Whole F32 output expansion requires 5,085,593,600 bytes against a 2 GiB workspace allowance. The mismatch cause remains unproven.
- Existing publication decisions require evidence links and forbid promoting partial results into full qualification.

## Progress

1. Evidence collection: complete.
2. Overview and source map: complete.
3. Local site verification: complete. Merge and production verification follow this frozen pre-publication snapshot; TASK-596 holds their final receipts.

The overview connects the earlier articles rather than overwriting their dated narratives. A downloadable JSON record accompanies ten immutable published-source SHA256 bindings. The actual 9B original coding suite and the SHA-verified 27B terminal archive were also examined directly. The current original 21-token numerical threshold remains 0.05 and failed at 0.087565.

## Verification

Astro check returned zero errors, zero warnings and 26 existing hints. The site built 1,865 pages. HTML, Markdown twin and downloadable JSON contain the final measured markers. Site tests passed 263 in the existing hub environment plus two API-import tests in the existing API environment. Initial missing PyYAML/FastAPI environment errors are recorded; no product code or dependencies changed. The llms lint gate returned zero High findings. Privacy and whitespace checks passed.

Two source-inspection snippets initially assumed the wrong manifest/token-comparison JSON shape. Corrected inspection used the actual fields and completed before the findings record was written. These were publication preparation errors, not model trials.

## Remaining model work

Precision diagnosis/remediation, aggregate physical memory and placement, fresh candidate-bound coding, repeated stability, genuine standard research and final launcher deployment remain outside this publication's completion.

## Tracking

The comprehensive publication is TASK-596. The physical candidate qualification remains TASK-482. Publication decisions KNOW-57 and KNOW-213 govern the evidence claims.
