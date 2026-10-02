# Local Ollama /dr findings and continuation

Version: 7.0 — 2026-09-30. Delta: 6.1 to 7.0. Task: Configure and verify local Ollama research model for Explorer /dr, TASK-35, Stele project llms-explorer-9d1wd. This checkpoint replaces stale running-worker and provisional Gemma 12B selection notes. Historical snapshots remain in the private bundle.

## Final selection and evidence

Explorer selects **llmsx-research-gemma31-mlx**, derived from official **gemma4:31b-mlx**, with a requested 65,536-token context. Ollama 0.34.4 runs native safetensors/NVFP4 MLX inference on this M5 Max, 40 GPU cores, 64 GiB unified memory. The model download is 19.424 GB / 1,236 tensors. Coordinator and workers share the scoped endpoint 11435 so only one model copy loads. Original 11434 is untouched. Indexing remains paused.

Gemma 31B completed a fresh standard-contract DATE Criteria research worker in 243 seconds / 16 turns. It generated six claims but initially transferred deletion-retention bounds to archival age. After repairing source extraction, an evidence-directed correction worker completed in 293.349 seconds and corrected all six facts. Independent review confirmed five exact date-format enums, ISODATE default, BSON long epoch values, time-series ISODATE, dataExpirationRule.expireAfterDays deletion 7–9215 days and ObjectId embedded timestamps. See gemma31-worker-review.json.

A fresh Gemma 31B gate completed in 315 seconds / 35 turns. It saved ten SUPPORTED verdicts, two for each of five core headings, with 8 actual scrapes, 0 repeat-cache reads and 0 blocked attempts. Independent full-source review confirmed all ten sampled facts, including clauses missing from short stored excerpts and the full deletion-rule object path. It reused the complete fetched pages and made 0 additional fetches. See gemma31-gate-review.json. A quote match proves occurrence, not full entailment.

The real Explorer job completed in 41.445 seconds / two turns, status=ok / returncode=0. It executed the canonical dr_run.py finish command without --minutes. Manifest=finalized/COMPLETED; completion_check=(None,None). The helper finalized the installed reference, canonical tree, research index and telemetry. This canonical bookkeeping does not perform deferred embeddings. See gemma31-explorer-acceptance.json. Log: ~/.llmsx/jobs/explorer-llmsx-research-gemma31-mlx-acceptance-20260930T094859Z.jsonl; Claude sessionc046cb15-bad6-4c57-bebe-b093bb1dee8a.

The native two-tool probe passed in 5.46 seconds. It correctly rejected applying deletion bounds to criteria.expireAfterDays. Its54.76 generated tokens/second figure describes102 generated tokens across that short probe. It is not /dr throughput, TTFT or a long-context benchmark. See gemma31-tool-benchmark.json.

**Qualification boundary:** the original five DATE concepts used GGUF Qwen27 research. Qwen MLX corrected two false age-limit claims. Gemma 31B separately performed a fresh one-concept worker, correction, fresh gate and actual Explorer completion. This is not a fresh five-worker Gemma-only benchmark. Initial drafts still need verification/correction; this fixture does not establish accuracy for every frontier topic. Claude helper Sonnet labels, generic 200000-token context metadata and costUSD estimates describe the requested client model, not cloud inference or local inference charges. The actual alias requests 65536 context. Retrieval services may have usage charges.

## Original failure and runtime repair

The screenshot mixed ANSI spinner/cursor controls from interactive ollama run with a more fundamental failure: plain chat had no file, shell or retrieval tool loop. The model said it could not execute /dr and simulated research. A model change alone cannot supply those tools.

Explorer routes Ollama research through llmsx.ollama_agent and Claude Code's tool loop against Ollama's local Anthropic-compatible API. Claude supplies tools and the local model supplies inference. The runtime executes Claude directly; the earlier ollama launch wrapper left child inference alive after helper timeouts. Root and child workers inherit the local alias through DR_CLAUDE_BIN. The runtime reads the installed /dr command and resolves DATE Criteria → Archive Rules → Online Archive → MongoDB Atlas ancestry. It excludes unrelated hooks, MCP servers and skill catalogs. Source text remains untrusted data.

Standard research uses five concrete concepts, at least three sources per concept and a negation query. Workers write the complete claims schema and call concept-done until ok=true. Persistent instructions survive compaction. Missing concepts, unresolved findings, malformed gates and success prose cannot bypass Explorer completion checks. UNVERIFIED remains permitted with an explicit completion warning under the standard contract.

The bounded stdio MCP relay exposes Firecrawl search/scrape and local source extraction. Gate scrapes have a hard 15-attempt cap; failures count and identical calls reuse cached results. Search cannot hide extra retrieval in scrapeOptions. The blind gate has no shell tool. Large source bodies stay on disk. read_source confines reads to relay-owned JSON files and returns narrow passages, Markdown headings, API property-list ancestors/purpose and truncation information. Source line numbers and property annotations are metadata, not quoted source words.

The API repeats expireAfterDays under criteria and dataExpirationRule. The previous extractor lost the parent object, causing the concrete7/9215 deletion limit to appear as an archival-age limit. schema_scopes preserves [dataExpirationRule.expireAfterDays] and the deletion-rule purpose even with context_lines=1. A regression test covers this failure. The corrected worker and fresh gate then distinguished these paths.

MCP initialization once failed with Retrieval relay failed: JSONDecodeError because the server emitted empty SSE data keepalives. The decoder now ignores empty events and assembles multiline event payloads. Credentials remain private; relay errors print only exception types.

record_verdict writes valid JSON atomically after each accepted record. It checks nonempty evidence, exact footnote syntax and URL resolution against the installed artifact. SUPPORTED evidence must preserve visible words from an actually fetched cited page; Markdown links/backticks/emphasis may differ. It returns actual saved counts and missing heading samples after success or rejection. A rejected record is not saved. The gate must finish with ten distinct records, two per core heading. Independent review still checks meaning and object ownership.

## Candidate history

| Candidate / attempt | Observed result |
| --- | --- |
| Qwen3.5:27b GGUF, llmsx-research | Original five concepts completed with schema/compaction repairs. Its1102s gate omitted DATE-vs-CUSTOM and confused deletion versus archival age; rejected gate. |
| User Qwen3.6-35b-A3B abliterated NVFP4 MTP MLX | Native/tool and real claim-repair tests passed. First gate exceeded20scrapes. Later369s structured gate omitted a core heading and had wrong citations; rejected. |
| Official Qwen3.5:35b MLX comparison | Short probes passed; comparison model removed to free disk for31B. User Qwen and original GGUF remain installed. |
| Gemma4:26b-mlx | Native and actual Firecrawl smoke passed.376s gate saved ten empty evidence fields and an unfetched API claim; rejected. |
| Gemma4:12b-mlx early |404s malformed JSON with a trailing quote; later361s turn-limited structured gate saved only eight samples. |
| Gemma4:31b-mlx early |478s/48turns; claimed ten samples but only seven saved. Rejected before progress/markup repairs. |
| Gemma4:12b-mlx repaired runtime |290s ten SUPPORTED samples, independently reviewed, then39.887s real Explorer completion. A fresh170s research worker nevertheless asserted wrong format names/counts and partition restrictions. Rejected for fresh research quality; default reverted before31 qualification. |
| Gemma4:31b-mlx final |243s fresh worker,293.349s correction,315s independently reviewed ten-claim gate,41.445s actual Explorer completion. Selected. |

Gemma 12B's fresh worker named only three formats, invented EPOCH_MILLISECONDS, made the default first-position date field mandatory and claimed only two DATE partition fields. Schema validity did not establish factual accuracy. Historical gemma12-explorer-acceptance.json, gemma12-gate-review.json and gemma12-tool-benchmark.json describe the rejected Gemma 12B resumed pass; use the explicit gemma31-* records for the final choice. gemma12-invalid-gate.json intentionally preserves malformed model output.

Model-reported query totals can aggregate several retrieval operations. The corrected 31B worker reported 13 queries; the actual transcript contains 1 search + 4 scrapes + 8 source extractions. Do not call that 13 web searches or infer fabrication by comparing it only with search calls. Its full measured tools also include 2 claim writes and 2 concept-done calls. Report categories separately.

## Installed research and metadata

Run: ~/.global-ai-hub/research/date-criteria. Status=finalized; exit_status=COMPLETED. Installed file: ~/.claude/skills/mongodb-atlas-expert/references/date-criteria.md,39 claims / 16 source URLs. Its DATE Criteria node has parent Archive Rules and six child concepts. The repo gained only this canonical DATE node. Guard passed687→688nodes,3773→3778frontier references with zero loss. Other canonical nodes created by concurrent work were not copied over the repo.

Atlas hub version 1.5.1 has a 279-character description and 33 routing rows. /sko --meta --no-sync returned 0 High / 0 Medium / 0 Low. DATE Criteria and three existing orphan references were added to hub routing and the MongoDB consolidation manifest. New-spoke SKIP destinations were corrected to real Atlas references. Only touched Atlas files were mirrored into ~/.agents/skills/mongodb-atlas-expert; no global migration ran. The reference's provenance banner precedes YAML, so its folded catalog row has empty frontmatter metadata; hub triggers/routing work. Offline catalog checks passed. Registry embeddings and semantic queries remain deferred.

The installed artifact's footnote targets were checked. A source-instruction scan found no matching assistant directives. Use dr_run.py for canonical research/run/tree/index updates. Do not rerun gating or acceptance on this finalized fixture unless deliberately reopening it. Normal next use is another frontier in Explorer.

## Configuration and operation

Private ~/.llmsx/config.json is mode 0600. Other settings/secrets were preserved:

```json
{
  "provider": "ollama",
  "models": {"ollama": "llmsx-research-gemma31-mlx"},
  "ollama_host": "http://127.0.0.1:11435",
  "ollama_worker_host": "http://127.0.0.1:11435",
  "ollama_allow_indexing": false
}
```

Backups: config.before-local-research.json, config.before-gemma12-selection.json and config.before-gemma31-selection.json under ~/.llmsx. Credential-bearing ~/.llmsx/ollama-mcp.json is excluded from the bundle and repo. Never print or copy its URL/headers. Both scoped LaunchAgents remain installed, but 11436 is idle after unloading only the task-owned 31B model. Keep coordinator and workers serial on 11435. Ollama reported about 21–32 GB model allocation during different contexts; those are not peak system-memory measurements. Two 31B copies can exhaust practical 64 GiB headroom.

LaunchAgents: ~/Library/LaunchAgents/com.mitch.llmsx-ollama.plist and com.mitch.llmsx-ollama-worker.plist, KeepAlive/RunAtLoad. Logs: ~/.llmsx/ollama-server.log and ollama-worker.log. The original11434 service and unrelated indexing settings were not restarted.

llmsx version 0.2.3 is installed editable. The console runner is ~/.local/pipx/venvs/pip/bin/llmsx-ollama-agent. Reinstall if needed with:

```bash
uv pip install --python ~/.local/pipx/venvs/pip/bin/python --no-deps -e llmsx
```

Restart an already-open Explorer to load upgraded Python code and saved configuration. Choose another frontier and run /dr. Local research uses standard depth, a 150-minute research budget, serial 30-minute workers and a 90-turn gate. The coordinator waits for long helper commands in the foreground. LLMSX_RESEARCH_TIMEOUT defaults to 10800 seconds for Ollama.

## Scripts and verification

- scripts/resume_local_dr.py: read-only fixture status by default; refuses research/gate on the completed DATE run; explicit --execute and saved local-model/indexing guards.
- scripts/accept_local_dr.py: checks gate hash and independent ten-claim confirmation, then exercises real Explorer finalization of this specific reviewed run. Do not rerun casually on a completed fixture.
- scripts/probe_local_research_worker.py: configurable --model/--slug, DATE Criteria topic, five-concept standard scaffold but only one worker. It never renders/finishes/installs a test skill. Existing fixture directories are refused.
- scripts/benchmark_local_research_model.py: native two-tool evidence/path probe; records actual durations/token counts, excludes model reasoning. No TTFT or sustained-throughput claim.
- llmsx/llmsx/retrieval_proxy.py and tests/test_retrieval_proxy.py: bounded retrieval, SSE, source confinement, heading/object preservation, exact quote/citation checks and saved progress.

Final runtime suite: 309 tests passed. Scoped Ruff passed. This includes malformed/incomplete completion, exact footnote mapping, two samples per heading, source confinement, fetch limits/failures/search-inline bypass, SSE keepalives, visible-word normalization and property-list ownership. No embedding test ran. Tree guard passed with zero permitted loss.

```bash
python3 scripts/resume_local_dr.py
PYTHONPATH=llmsx hub/.venv/bin/python -m pytest llmsx/tests -q
```

System Python needs PYTHONPATH=llmsx from the repo because the outer directory otherwise shadows the installed package. The installed console entrypoint works from research directories.

## Supplied research: verified measurement limits

The user's listed research files guided the MLX selection. Their numerical examples are not measurements of this host. Full supplied paths are recorded in prompts.md v46. The microarchitecture and acceleration manifests are COMPLETED but have no gate record. Their supplied report.md paths do not exist; claims live in claims/*.json rather than the named claims.jsonl paths. No eGPU test/deployment occurred here.

memory_profiler.py hardcodes 4096-byte pages; live vm_stat reports 16384. Its page-based byte totals are understated by 4x, and some counters are cumulative events rather than resident pages. Parse the actual header and select appropriate counters. benchmark_suite.py uses stream=false and estimates TTFT from load_duration+prompt_eval_duration. It does not measure client first-token arrival, inter-token jitter or peak memory despite its docstring.

Apple rates this 40 GPU-core M5 Max at 614 GB/s, versus the article's 400 GB/s example. Rated bandwidth is not measured sustained bandwidth. Qwen35B-A3B activates a subset of weights; total stored weight bytes divided by bandwidth is not a decode-rate bound. Generic architecture repositories do not establish precise eGPU throughput or residency numbers. Those source files were left unchanged in the other session's scope. Stele benchmark measurement lesson: KNOW-53.

## Durable handoff and future work

Private bundle: ~/.llmsx/handoffs/local-dr-20260930T044607Z. It contains this writeup, snapshots, scripts/runtime/tests, selected redacted config, model definition, LaunchAgents, reviewed research, gate source caches, public evidence, pre-edit hub metadata/tree and supplied-reference inventory. Historical handoffs remain under history/. Raw local job logs stay private. MCP credentials/configs are excluded. A Mac reboot at 04:34:45 UTC deleted early /tmp probes; use durable artifacts instead.

The isolated 31B worker fixture is archived in the bundle after review so its four deliberately pending scaffold concepts do not appear as unfinished product research. The isolated rejected 12B fixture is already archived there. Neither is a completed five-worker research run.

No remaining model-selection or runtime-implementation steps. Indexing is still paused by user instruction. A fresh five-worker Gemma-only benchmark is additional evaluation, not a result claimed here. Commit explicit task paths only; no push is authorized by this task. Preserve concurrent website/Analytics history, .codex/agents/ and .skillopt-sleep/. The commit containing this v7.0 checkpoint is the scoped completion commit; use git log to identify it.

Primary references: [Gemma 31B MLX](https://ollama.com/library/gemma4:31b-mlx), [Ollama MLX performance](https://ollama.com/blog/mlx-performance), [Claude Code integration](https://docs.ollama.com/integrations/claude-code), [user Qwen MLX](https://ollama.com/Ermzzz999/qwen3.6-35b-a3b-abliterated-nvfp4-mtp), [Apple hardware specs](https://www.apple.com/macbook-pro/specs/).
