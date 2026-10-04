# Actual full coding payload on the Qwen3.6 candidate

Version: 1.0.0

Delta: Replace unrelated heavy-profile proxy counts with actual full23 coding request measurements.

## Result

Both pinned Claude Code clients send all 23 coding schemas when their actual cached feature data is retained. The installed LiteLLM 1.103.1 pure Anthropic adapter preserves their names and order. Qwen3.6's actual candidate vocabulary and an offline rendering of the server template give these first-request counts:

| Client | Original descriptions | Existing compact-v1 descriptions | Spare after 4096 output tokens with compact-v1 |
|---|---:|---:|---:|
| 2.1.286 | 20,093 tokens | 7,862 tokens | 20,810 tokens |
| 2.1.289 | 20,130 tokens | 7,899 tokens | 20,773 tokens |

The context remains 32,768. Compaction saves 12,231 tokens in each captured request. All schema validation fields, names and order remain unchanged. The full general user profile's earlier 66k–96k cl100k counts do not describe this qualification profile.

These are context and protocol measurements. The mock client endpoint returned canned text. The counter linked CPU-only archives, loaded vocabulary only, created no model context and performed no inference. No GPU initializer, reset, service restart or model-quality trial ran. The actual candidate-native rendering, cache reuse, growing coding sessions, numerical error, peak memory and standard /dr still need live evidence.

## Two prerequisites discovered

The old qualification-pinned executable at /Users/mitch/.local/share/claude/versions/2.1.286 had disappeared. The installed versions are 2.1.287, 2.1.288 and 2.1.289. The official Darwin-arm64 2.1.286 release was restored privately at /Users/mitch/.cache/claude-egpu/experiments/egpu-pinned-client-2.1.286-v100/claude. Its SHA-256 matches the original accepted client hash and the official release manifest. The normal client symlink remains pointed to 2.1.289. A future launcher must retain its pinned executable outside automatic update cleanup or qualify the updated version.

An empty isolated Claude config exposed only 21 schemas and omitted Monitor and PushNotification. Copying only the user's actual cachedGrowthBookFeatures, cachedGrowthBookFeaturesAt, cachedExperimentFeatures and cachedExperimentData restored all 23 schemas. No credentials, arbitrary settings or invented feature values were copied. Claude's Task builtin appears as Agent in the actual API request; both clients emitted the same complete wire-name set. Request capture is stronger evidence of advertisement than the init-event list.

## Reproducibility and fidelity

The exact pinned original profile and fixed-protocol argument preparer were used. The original coding prompt and reviewed summary instruction were retained. The transport-only changes were a private config directory, a loopback mock endpoint, dummy credentials, a candidate alias and an empty test directory before any tools ran. This experiment supplies no coding-success credit.

The OS network guard allowed the capture endpoint and denied another local port. The installed LiteLLM adapter then translated the request under an OS network-deny profile. The counter linked existing CPU archives whose accelerator build flags were verified OFF. The candidate GPU binary and sealed 288-pin startup preparation were untouched. The original-model SHA was checked before vocabulary counting.

For 2.1.286, native Anthropic conversion and installed LiteLLM conversion yielded identical offline rendered prompt hashes and counts. Current 2.1.289 was also translated by the installed LiteLLM adapter and counted. A live deployed gateway/native byte comparison remains pending.

Raw requests, feature-cache snapshots, generated SDK state, rendered prompts, binaries and model data remain private. /Users/mitch/dev/llms-explorer/docs/research/egpu-profile-context-2026-10-04/measurements.json contains publication-safe metadata and exact source pointers. /Users/mitch/dev/llms-explorer/docs/research/egpu-profile-context-2026-10-04/files.txt lists every retained artifact's full path.

## Failures retained

| Preparation | Actual failure | Consequence |
|---|---|---|
| Capture v100 | FileNotFoundError for the old client executable | No client or model started. Restore accepted bytes privately. |
| Capture v101 | Only 21 actual API schemas | Failed full-tool fidelity. Preserve actual cached feature data. |
| Counter build v100 | common_json does not accept stream extraction | Build failed; use json::parse on exact file bytes. |
| Count preparation v100 | NameError: SCHEMA_MAPS is not defined | Converter ran; compactor preparation failed before vocabulary counting. |
| Count preparation v101 | NameError: SCHEMA_SINGLE is not defined | Preserve all referenced pure schema constants. |

The two failed Python preparation sources were reconstructed from the recorded edits. They are marked as reconstructed; they are not asserted to be independently hashed runtime snapshots. Later executions preserve source snapshots. These preparation errors are not model failures.

## Physical continuation

Current observed boot is 1791136050:203826. No native inference listener or TinyGPU owner was found in the last passive observation. The original stale fault record belongs to boot 1790879561:56304 and remains untouched. Apple Ollama embedding runners observed earlier naturally exited; this experiment did not stop them.

The user's enclosure cold-power recovery fact for this boot is pending. Do not assert it or consume the one-shot root on that assumption. The concrete prepared operation remains /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-cold-root-operation-v105/run_actual_cold_once.py. The sealed source review remains /Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-static-inputs-v105/INDEPENDENT-REVIEW.json. All its input paths existed in the latest check. Its actual pin map has 288 entries; the stale descriptive count field remains 254. Preserve both facts and the immutable receipt.

After physical admission, run the actual candidate startup and original first-inference/numerical/peak gates. Then use the original full coding pair and genuine standard /dr with validated canonical artifacts. Keep context32768, f16 KV, original reserves, numerical0.05, full tools and all research quality requirements. This experiment qualifies none of those live gates.
