# Gemma article full DDO review

This file retains the writer-phase and corrective history. Final integration is complete with explicit evidence and cap limits; all final actionable dissent is resolved. See [README.md](README.md) and [summary.json](summary.json) for current per-post status and independent review lineage. No all-CLEAN certification is claimed.

Version: 1.0.0. Mode: full/write. Result: reviewed with explicit source limits; no eligible edits.

This report records the exact source hash in gemma.json. The article was committed by its author during this run. The audit made no overwrite.

The contract, every selected pass, source inventory and limits are recorded in gemma.json. The first pass reviewed all prose; later source changes require review of the changed spans. The review found no Medium-or-higher change supported by the inspected sources. The article already separates recorded phases, reported inference results and proposed eGPU work.

| Claim group | Verification source | Result |
|---|---|---|
|Agent qualification scope: original five concepts used Qwen; Gemma had one fresh worker, correction, gate and canonical completion.|site/public/downloads/benchmarks/local-research-2026-09-30/measurements.json provenance/research_phases; docs/verification/local-ollama-dr-2026-09-30/gemma31-worker-review.json|confirmed|
|243/293.349/315/41.445-second phase records; six corrected worker facts, ten sampled gate verdicts and eight scrapes.|measurements.json research_phases; worker-review.json; gate-review.json; gemma31-explorer-acceptance.json|confirmed as recorded phases; not a new reproduction|
|Ollama0.34.4,64GB M5Max,19,424,434,468-byte model,65536 requested context, one final endpoint.|measurements.json hardware/runtime; docs/verification/local-ollama-dr-2026-09-30/gemma31-manifest.json|confirmed as saved configuration|
|Gemma31 is dense; Gemma26A4B has3.8B active parameters.|https://ollama.com/library/gemma4:31b-mlx model information|confirmed|
|Ollama connects Claude Code through an Anthropic-compatible local API; tools require compatible models.|https://docs.ollama.com/integrations/claude-code|confirmed|
|Ollama native MLX engine supports NVFP4.|https://ollama.com/blog/mlx-performance|confirmed|
|All five two-tool probes passed; output counts88/81/111/112/102 and rates100.62/54.68/79.91/113.04/54.76.|measurements.json native_probes; scripts/benchmark_local_research_model.py probe; exact sum(eval_count)/sum(eval_duration) recomputation passed for every row|confirmed as saved probes|
|Native probe requested8192context,temperature0,thinkingfalse,512output tokens per response;31wall5.46s.|scripts/benchmark_local_research_model.py probe; measurements.json native_probe_method|confirmed|
|Community Qwen alias identifies35B-A3B NVFP4/MTP weights.|https://ollama.com/Ermzzz999/qwen3.6-35b-a3b-abliterated-nvfp4-mtp; docs/verification/local-ollama-dr-2026-09-30/mlx-manifests.json|confirmed model attribution; no independent speculation-performance claim|
|Follow-up load/prefill/burst/sustained and memory values were supplied in a summary.|site/public/downloads/benchmarks/local-research-2026-09-30/reported-inference-rerun.json|confirmed as attributed report; underlying empirical values remain unverified without raw requests/counters/repetitions|
|stream=false and load_duration+prompt_eval_duration do not measure arrival of the first token at the client.|site/public/downloads/benchmarks/benchmark_suite.py; https://docs.ollama.com/api/generate response counters|confirmed|
|Apple lists460/614GB/s for M5Max variants;400GB/s was not measured here.|https://www.apple.com/macbook-pro/specs/; reported-inference-rerun.json interpretation_limits|confirmed specification and evidence limit|
|7..9215 applies to deletion dataExpirationRule.expireAfterDays; archival criteria.expireAfterDays is a separate field.|https://www.mongodb.com/docs/api/doc/atlas-admin-api-v2/operation/operation-creategroupclusteronlinearchive criteria/dataExpirationRule|confirmed|
|read_source preserves headings/property ancestry and records truncation; record_verdict checks fields, exact footnote mapping and quoted words from retrieved bodies, not semantic entailment.|llmsx/llmsx/retrieval_proxy.py read_source/schema_scopes/record_verdict|confirmed|
|Gate limits fifteen actual scrape attempts incl failures; caches repeat calls and blocks inline search scraping; UNVERIFIED causes completion warning.|llmsx/llmsx/retrieval_proxy.py handle; llmsx/llmsx/ollama_agent.py completion_check/gate_prompt|confirmed|
|Standard/dr requires five concepts, three independent sources per concept, contrary-evidence round and sampled gate.|.agents/skills/dr/SKILL.md Depth contract and Phase1|confirmed|
|Runtime repair passed309tests and final completion check was null,null.|docs/verification/local-ollama-dr-2026-09-30/final-verification.json|confirmed as recorded test run|
|eGPU metadata reached endpoints; bridge drops tools/protocol and fabricates timing; hybrid adapter path is proposed.|site/public/downloads/benchmarks/local-research-2026-09-30/egpu-dr-strategy.md; docs/research/egpu-explorer-dr-strategy-2026-09-30.md|confirmed as attributed inspection and proposal; no inference run independently repeated|
|Model installation/probe examples agree with runtime API and saved standalone harness; host must match daemon.|scripts/benchmark_local_research_model.py main/probe; https://ollama.com/library/gemma4:31b-mlx; llmsx/llmsx/ollama_agent.py environment selection|confirmed by static inspection; commands not executed|
|No power trace,streamedTTFT,eGPUcomparison or universal accuracy score;local inference does not imply offline retrieval.|measurements.json native_probe_method/provenance and reported-inference-rerun.json method gaps|confirmed evidence limits|

Mechanical review found balanced fences/tables, unchanged anchor headings and valid frontmatter. Operational examples were inspected as data. No article commands ran. Word delta:0%. Raw rerun results remain attributed and unverified; this is not a reproduced benchmark. The independent blind review found no eligible changes. Canonical no-op convergence returned CLEAN with edit-distance ratio 0.0000; that narrow result does not reproduce the reported inference reruns. Built-page and link checks passed for the recorded source hash.
