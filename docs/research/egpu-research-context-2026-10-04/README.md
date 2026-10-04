# Standard research context on the candidate vocabulary

Version: 1.0.0

Delta: Measure actual historical research requests separately from coding requests.

## Result

All ten selected research requests fit a 32,768-token window with 4,096 tokens reserved for output. The five initial requests use 7,599–7,625 tokens. Selected longer histories use 14,798–16,731 tokens. The largest leaves 11,941 tokens after the output reserve.

These are CPU vocabulary and template projections onto Qwen3.6-27B IQ2. They are not live new-candidate research results.

| Standard concept | First request tokens | Largest serialized snapshot tokens | Snapshot messages | Spare after output reserve |
|---|---:|---:|---:|---:|
| Cache freshness | 7,599 | 16,516 | 29 | 12,156 |
| 304 Not Modified responses | 7,625 | 16,160 | 27 | 12,512 |
| ETag validators | 7,602 | 16,449 | 29 | 12,223 |
| Last-Modified validators | 7,611 | 14,798 | 25 | 13,874 |
| Conditional request precedence | 7,608 | 16,731 | 29 | 11,941 |

## Fidelity and source evidence

The selector streamed the unchanged 1,403,319,847-byte native log and parsed 1,994 converted request records without malformed JSON. It matched each of the five terminal v125 worker prompts as one exact complete user text block. Each initial user message contains six text blocks; all blocks remain present. The selector retained the first matching request and the matching request with the largest serialized bytes for each worker. This byte selector is not asserted to select the maximum token count across every turn.

All selected requests retain `Read` and the five original firecrawl MCP tools: `firecrawl_scrape`, `firecrawl_search`, `observed_research`, `publish_claims` and `read_source`. Full schemas, message histories and request controls remain unchanged. They retain `tool_choice=required`, temperature 0.6, top_p 0.95, top_k 20, min_p 0, presence_penalty 0, enable_thinking=true and max_tokens 4096. This experiment adds no description compaction.

Separate inspection verifies the exact final `XML_RULE` and `EVIDENCE_RULE` strings from the consumed v125 client source in every selected system prompt. Each system prompt contains 14,720 characters and lacks the obsolete omit-quotes instruction. Each first request has two messages; the selected longer histories have 25–29 messages.

The existing CPU-only counter loaded the SHA-verified candidate vocabulary, created no model context, executed no weights and ran under an OS network-deny profile. Private raw requests, rendered prompts and logs remain outside the repository. Public metadata preserves source pointers, hashes, line numbers and commands.

Source log: /Users/mitch/.cache/claude-egpu/experiments/qwen35-27b-cold-first-runtime-v101/native.log

Source log SHA: f5821d0a5bf5d1bccd1e9d9b376db925a01c1a6e4ab2b0e14fb36b9fdd4b20bd

The executed selection and counting scripts are retained as private source snapshots. The published selector adds a fixed source-log hash check after the first successful measurement. No accepted measurement was rerun for that guard or formatting change.

## Consequence for the physical trial

The coding and research context measurements support testing the existing 32k profile with its required tools and instructions. None of these selected research snapshots demonstrates context overflow. The terminal Qwen3.5 v125 trial remains rejected 0/5. This experiment supplies no replacement facts or research acceptance.

After confirmed physical recovery, the prepared Qwen3.6 candidate still needs actual startup, first inference, the unchanged selected-token numerical limit of 0.05, and peak/reserve admission. Then run a fresh candidate-bound full coding pair and genuine standard research with the original source, semantic, blind, quality, render, install, finish and tree gates. Actual new-candidate rendering, context growth, caching and throughput remain unmeasured.

Current boot is 1791136050:203826. Enclosure recovery is unconfirmed. The sealed v105 cold receiver remains unconsumed. No GPU initializer, service restart, indexing or canonical research mutation ran.

## Preparation corrections

The first metadata verifier assumed string user content and raised `AssertionError`. The actual content is a list of six text blocks. The corrected verifier checks the one exact prompt block and retains every other block. The original extraction and token counts were already correct. The failed verification receipt is retained privately. Ruff's initial `EXE001` finding was corrected by marking the public helpers executable. Neither preparation issue is a model failure.

## Inspect without inference

```sh
/opt/homebrew/bin/python3 -B /Users/mitch/dev/llms-explorer/docs/research/egpu-research-context-2026-10-04/publish_report.py --verify-only
```

Expected: ten preserved payloads verified, zero model inference calls and zero GPU actions. The actual selection and count commands remain in the retained source snapshots and measurement metadata. Every measurement output directory must be new.
