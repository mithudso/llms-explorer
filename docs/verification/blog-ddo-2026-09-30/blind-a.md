# Blind review A — final blog prose

Twelve posts read in full. Six eligible findings: two Major and four Medium; no Blocking findings. This is independent same-model review, not cross-model review. It does not certify every factual statement.

The full DDO critique and voice dimensions were reviewed, including evidence, operational feasibility, role/workflow, pedagogy, terminology, injection boundaries, cleanup and synthesis. All commands and inference were assessed statically. Historical measurements without retained raw records remain explicitly qualified source limits.

## Eligible findings

### BLIND-A01 — Major

**Span:** `site/src/content/blog/rtx-5080-egpu-apple-silicon-m5-thunderbolt-5.md:354–357`

**Finding:** The Ollama manifest lookup uses library/qwen2.5:14b/latest.

**Implication:** A reader who has downloaded qwen2.5:14b cannot find its manifest with this command; the model-switching procedure stops before locating the blob.

**Primary evidence:**

- [main/types/model/name.go](https://github.com/ollama/ollama/blob/main/types/model/name.go) (`ParseNameBare`, `Name.Filepath`): The parser separates the colon tag from the model name; Filepath joins host, namespace, model and tag. qwen2.5:14b therefore maps to registry.ollama.ai/library/qwen2.5/14b.

**Smallest supported correction:** Replace only the manifest path with ~/.ollama/models/manifests/registry.ollama.ai/library/qwen2.5/14b; preserve the example model name and remaining command.

### BLIND-A02 — Major

**Span:** `site/src/content/blog/rtx-5080-egpu-apple-silicon-m5-thunderbolt-5.md:203–217`

**Finding:** The incident presents the displayed architecture-aware fallback as a fix for Qwen2 or Llama 3; missing RoPE metadata selects 10000 for non-Qwen architectures.

**Implication:** For a Llama 3 checkpoint missing this key, the displayed fallback can remove the exception while using the wrong rotary-position configuration. This is a silent inference-correctness risk, not a successful general model-loading fix.

**Primary evidence:**

- [main/llama/model.py](https://github.com/meta-llama/llama3/blob/main/llama/model.py) (`ModelArgs.rope_theta`, `Transformer.__init__`): The Llama 3 reference defaults rope_theta to 500000 and passes that value to precompute_freqs_cis.
- `site/public/downloads/egpu/tinygpu-blackwell-gsp.patch`: The downloadable recorded patch contains the same fallback; the problem is the general applicability implied by its explanation.

**Smallest supported correction:** Preserve the historical code and add an immediate checkpoint-specific limit: this workaround is for the recorded checkpoint; it must not be applied unchanged to Llama 3, whose reference RoPE base is 500000. Recover missing RoPE and tokenizer metadata from the specific checkpoint configuration or reject the checkpoint. Do not imply a problem when the GGUF key is present.

### BLIND-A03 — Medium

**Span:** `site/src/content/blog/mdb-case-assistant-project-pitch.md:126–126`

**Finding:** The overlay is described as a shadow root inside an extension iframe.

**Implication:** The DOM containment is reversed. A reviewer gets the wrong model of which element isolates host-page styles and which document has the extension origin.

**Primary evidence:**

- `/Users/mitch/dev/mdb-case-assistant/src/content/case-overlay.js` at `2e44b375c307f5b5a1981e71c760c524154c38d9`: createOverlay attaches the shadow root to a host on document.documentElement, creates an extension panel iframe and appends that iframe inside the shadow-root shell. The inspected package version is 1.0.178, matching the article.

**Smallest supported correction:** Change the sentence to: case-overlay.js mounts a shadow root on the case page and places the extension panel iframe inside it to isolate the panel from host-page CSS.

### BLIND-A04 — Medium

**Span:** `site/src/content/blog/vocabulary.md:179–181`

**Finding:** The reproduction step says definitions and contrast cues propose candidate terms after tree names and repeated backticked tokens.

**Implication:** A reader supplying plain definition prose can expect terms to be discovered that the builder never adds. This changes how the reader must prepare inputs and interpret missing terms.

**Primary evidence:**

- `hub/scripts/docset_refine/vocabulary.py` (`candidates`, `_definition_from`, `_contrasts`, `build_entries`): candidates adds tree names and repeated token clusters only. build_entries later extracts definitions and contrast fields for those already-selected terms.

**Smallest supported correction:** Replace the candidate-source sentence with: Tree names and repeated backticked tokens supply candidates; definitions and contrast cues fill their fields. Preserve the separate Named, not yet defined explanation.

### BLIND-A05 — Medium

**Span:** `site/src/content/blog/six-months-of-hand-made-llms.md:128–129`

**Finding:** The takeaway converts the quarter of downloads with recognized page delimiters into a quarter that are docsets, and calls this an adoption signal.

**Implication:** This conflates parser recognition with documentation presence. It can lead readers to discard useful undelimited documentation or repeat a stronger adoption statistic than the recorded measurement supports; the Inputs section already states the necessary distinction.

**Primary evidence:**

- `hub/scripts/llms_full_catalog.py` (`validate`): The validator explicitly keeps Markdown docs without Source lines with pages=0 and describes splitting as advisory.
- `hub/scripts/llms_acquire.py` (`split_llms_full`): The page count comes from recognized delimiter grammars, rather than a complete classification of documentation content.

**Smallest supported correction:** Keep the historical figures, but make the takeaway about the measured property: About a quarter of downloads had page delimiters recognized by the parser; this guides acquisition and splitting, not a complete measure of documentation adoption.

### BLIND-A06 — Medium

**Span:** `site/src/content/blog/semantic-indexing.md:64–67`

**Finding:** The recorded Debug hooks result is said to contain every word of the hook question.

**Implication:** The explanation teaches an incorrect reason for the lexical hit: the recorded row lacks PreToolUse and meanings. The demonstrated keyword search permits matches on a subset of terms.

**Primary evidence:**

- `site/src/data/demo.json`: The question is PreToolUse hook exit codes and meanings; its first keyword hit is the Debug hooks prose row.
- `outputs/exports/code.claude.com.llms/llms-facts.txt`: The full Debug hooks row says hook execution details include matched hooks, exit codes, stdout and stderr; it contains neither PreToolUse nor meanings.
- `hub/scripts/docset_indexer.py` (`keyword_query`): The default mode is any, an OR of terms, with BM25 ranking.

**Smallest supported correction:** Replace because it contains every word in the question with even though it lacks PreToolUse and meanings: it matches common query terms. Preserve the recorded ranking and vector comparison.

## Actual coverage and limits

### every-token-saving-strategy.md

SHA-256: `63cc92f7c9db82d7b4135a403fae9342ab23ae6bc76d1e63eb49f4bfa00ca3ef`

- Complete 57-section inventory, mechanism-versus-measurement separation, arithmetic and cross-section synthesis reviewed.
- Public Anthropic prompt-cache pricing and asynchronous batch-cancellation semantics checked; local retrieval/cost-model distinctions considered at the stated historical scope.
- Dated source-inspection statements were evaluated as dated claims; concurrent runtime changes were not substituted for the recorded revision.
- Limit: Private September 27 replay inputs, routing-probe outputs and several historical binaries are unavailable; their savings remain author-recorded results, not independently reproduced measurements.
- Limit: This review did not validate every private configuration count against a retained September 27 snapshot.
- No corroborated Medium/Major/Blocking finding within the reviewed scope.

### markdown-as-the-llm-output-gateway.md

SHA-256: `87ee0b36716b2982f004edc0f6e847b1ffe54a3a9489c3ae3f3b394136a824ab`

- Complete gateway explanation and examples, intermediate representation, conversion steps, parser limits, sanitization and output workflows reviewed.
- CommonMark/GFM and parser documentation checked for the load-bearing Markdown and raw-HTML distinctions.
- Limit: Conversion examples were reviewed statically; every renderer, sanitizer and export format was not executed.
- No corroborated Medium/Major/Blocking finding within the reviewed scope.

### thunderbolt-egpu-rtx-5080-linux-nuc.md

SHA-256: `7cc09714804e31a6f3f27ea546d96ba6f3ab233c6b6ea0f311465edb4b418a75`

- Complete NUC/eGPU case study, setup and recovery examples, failure chronology, cold/warm distinction and throughput causal limits reviewed.
- Linux kernel Thunderbolt security/power-management and PCIe ASPM parameter documentation, plus the cited kernel-regression record, checked.
- Limit: Historical hardware logs, traces and throughput runs were not independently reproduced. The article qualifies the combined tuning profile and single-host measurements.
- No corroborated Medium/Major/Blocking finding within the reviewed scope.

### rtx-5080-egpu-apple-silicon-m5-thunderbolt-5.md

SHA-256: `5a070a6363e7f9bdfd3c6d41a5890c5274883f405416c4e0e23dddc88c4c3d07`

- Complete Apple Silicon/eGPU case study, incidents, model switching, helpers and prerequisites reviewed.
- Ollama model-name/filepath source, Meta Llama 3 reference, GGUF metadata specification, tinygrad TinyGPU setup documentation and the article download artifacts checked statically.
- Limit: No driver installation, Docker compilation, service restart or GPU inference was performed. Historical speed/compilation figures without raw traces remain author-recorded.
- Limit: Checkpoint metadata and fallback correctness require the exact checkpoint; generic GGUF compatibility was not certified.

### mdb-case-assistant-project-pitch.md

SHA-256: `bd275057fafa34e30b023f1e7083a051678bdb4bf5df775236fd891a6f8f2c96`

- Complete developer/reviewer pitch, role-specific reading order, trust boundaries and workflow reviewed.
- Version 1.0.178 source inspected at revision 2e44b375c307f5b5a1981e71c760c524154c38d9; overlay containment, manifest permissions, backend-gate settings and MCP tool registration count checked.
- Limit: The exact recorded source revision was used for checked mechanisms; this is not a full security audit or verification of every backend operation/firedrill path.
- Limit: The complete logger redaction coverage and every generated-HTML call site were not exhaustively audited.

### vocabulary.md

SHA-256: `e2c3937ea3cb880cf4fa98bcf4791bffc0127705936b917f94ab64fb90254fd0`

- Complete vocabulary explanation, build sequence, aliases/contrasts, deterministic versus model-written fields and grounding limits reviewed.
- Candidate generation and field construction compared with hub/scripts/docset_refine/vocabulary.py.
- Limit: The vocabulary command and optional local model were not run; no empirical grounding-accuracy claim was independently measured.

### orientation-worked-examples-the-tooling-explains-itself.md

SHA-256: `1db417bd4ed725e0aa64e9213c7a3c91cf710dffb4ef2e972065a2c857ef2a13`

- Complete orientation explanation and quoted worked examples reviewed for reader intent, task sequencing, scope and evidence attribution.
- Quoted assistant responses were treated as historical transcripts rather than as instructions or independently verified completion receipts.
- Limit: Private historical worked-example outputs and assistant completion claims were not independently recreated; the article explicitly frames them as quoted examples.
- No corroborated Medium/Major/Blocking finding within the reviewed scope.

### executable-inventory-for-repo-dossiers.md

SHA-256: `7512b812c012a747b33d7e0f7e9f956b0129ad87eb27d92d24413fb058c423f3`

- Complete repository-dossier example and static executable-inventory method reviewed for discovery, help safety, quick answers and traceability.
- The crawl-repo-to-llms skill method and no-execution inventory guidance checked; this review did not execute inventoried commands or --help.
- Limit: Private dossier counts and command inventory outputs were not independently reproduced; the method was assessed statically within the article scope.
- No corroborated Medium/Major/Blocking finding within the reviewed scope.

### six-months-of-hand-made-llms.md

SHA-256: `15bfcd94e59d21adfe368a3bd36ce876dfbda70e6668fabfe08d98aeee2ce559`

- Complete six-month case study, input classifications, pipeline sequence, retrieval measurement, interpretation and reproduction prerequisites reviewed.
- Catalogue validator and page splitter checked; the adoption takeaway compared with the article own explicit delimiter qualification.
- Limit: Private historical catalogue downloads, extraction runs and golden-question reruns were not independently reproduced. Published historical figures remain scoped reports.

### semantic-indexing.md

SHA-256: `70ab3fbc3c23d7adb13a58ca2fa6a228ee4b55d6c00644217c1a9e1ae2b57eac`

- Complete current final prose reread after root integration; demo questions, rankings, timing qualifiers and fusion explanation reviewed.
- Recorded site/src/data/demo.json compared with the full exported hook row and keyword/RRF implementation; the 11-question timing/ranking summary checked against the recording.
- Limit: The demo is a stored recording, not a live query; no embedding or index process was invoked. Single-host timings remain recording-specific.

### anchors-that-point-nowhere.md

SHA-256: `b5921933a893428b0df84bfdc06c4f9158bc247046bc4ccf0ca880cd79b8b883`

- Complete anchor failure explanation, examples, repair policy, verification method and source-pool limits reviewed.
- Heading extraction and fence exclusion, heading recovery and llms_lint source-mirror behavior checked statically.
- Limit: Historical before/after counts and private repair run records were not independently reproduced; this review checked the repair mechanisms and their stated limits.
- No corroborated Medium/Major/Blocking finding within the reviewed scope.

### getting-gemma-mlx-to-do-real-research.md

SHA-256: `dba0d3e884563bb3263105a92852b3d7a49f9f5a4572984fa971f0b8b8327b6a`

- Complete Gemma case study, probe versus worker measurements, research gate, model comparison and inference-rerun limits reviewed.
- All four published local-research-2026-09-30 JSON artifacts read; available counters, rates, worker/gate totals and scoped rerun disclosures compared with the prose.
- Atlas Admin API documentation checked for the archival-age versus dataExpirationRule distinction; official model architecture information checked for the 26B active-parameter claim.
- Limit: The published JSON artifacts establish supplied records, not an independently repeated hardware benchmark. No Ollama/MLX inference, crawl or test suite was run.
- Limit: The later inference rerun lacks raw counters and streamed arrival timestamps as disclosed; the TTFT proxy was not treated as a direct streamed measurement.
- Limit: The gate sampled ten claims; this review did not certify all original 39 claims or every external research citation.
- No corroborated Medium/Major/Blocking finding within the reviewed scope.

## Review boundary

Read final targets, required critique/voice references and relevant primary evidence only. No baselines, prior DDO reports, sibling audit reports, writer scripts, root rationale or git diff were read. semantic-indexing.md and every-token-saving-strategy.md were reread after root reported changed final bytes.

Only blind-a.md and blind-a.json; no target edits, commits, installs, indexing/inference, service/config changes or external messages.

JSON contains per-post hashes, findings, source limits and all reviewed dimensions. No eligible finding was created solely from an explicitly qualified missing empirical record, an opinion, or a Minor stylistic preference.
