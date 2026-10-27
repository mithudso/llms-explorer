<!-- hub-reference-banner -->
> **Reference file — part of the `mlx-lm-expert` hub.** Created by `/dr` deep research 2026-10-23; research dir `~/.global-ai-hub/research/mlx-lm-python-evaluation-20261023`.

---
name: mlx-lm-python-evaluation
description: "Explain MLX-LM Python generation sampling and evaluation contracts. TRIGGER: generate and stream_generate response objects; custom samplers and logits processors; standalone and rolling perplexity; lm-evaluation harness inputs. SKIP: model loading and HTTP requests -> mlx-lm-expert native-contracts reference."
version: "1.0.0"
updated: "2026-10-23"
category: "research"
whenToUse:
  - "Use Python generation and streaming"
  - "Write a custom sampler or logits processor"
  - "Compare perplexity and lm-eval measurements"
keywords: ["mlx-lm", "generate", "stream_generate", "GenerationResponse", "sampler", "logits processors", "perplexity", "lm-eval", "loglikelihood_rolling"]
tags: ["mlx-lm", "inference", "evaluation", "api"]
provenance: "/dr · ~/.global-ai-hub/research/mlx-lm-python-evaluation-20261023"
---

# MLX-LM Python generation sampling and evaluation

## Overview

MLX-LM exposes a one-shot Python call and an incremental streaming generator. `generate` consumes the stream and assembles visible text; `stream_generate` yields structured `GenerationResponse` objects with text fragments and token or timing metadata. Callers should read `.text`, inspect the final response for `finish_reason`, and account for edge behavior such as `max_tokens=0`, empty output, mutable prompt caches, and thread-local MLX streams. Current third-party examples sometimes confuse response objects with strings or retain an outdated edge-case description, so pin behavioral claims to the installed version.

MLX-LM exposes generation customization through callable samplers and ordered logits processors. A processor receives token history and current model logits and returns changed logits; MLX-LM runs processors before normalizing logits to log-probabilities for the sampler. Built-in factories cover greedy and temperature-based sampling, top-p/min-p/top-k/XTC filters, logit bias, and repetition/presence/frequency penalties. Independent MLX projects show how to combine the factories with custom token bans or biases. April 2026 reports on mlx-lm 0.31.2 caution that stateful processors can depend on accurate token history and rollback during speculative decoding.

MLX-LM exposes two complementary evaluation paths. `mlx_lm.perplexity` estimates next-token perplexity over sampled fixed-length token sequences. `mlx_lm.evaluate` registers an MLX model with EleutherAI's `lm-evaluation-harness` for task benchmarks and rolling likelihood scoring. These paths use different data and context protocols, so their scores are not interchangeable. Perplexity measures predictive fit on a text distribution; task scores measure performance on selected benchmarks and prompts. Reproducible comparisons should pin the model and tokenizer, corpus and split, context policy, task and prompt settings, random seed, and package versions. For adapters, `mlx_lm.lora --test` scores a held-out `test.jsonl`; prompt masking changes which tokens contribute to that score.

## Core Concepts

### MLX-LM Python generation and streaming contracts

- At revision 0d4d3d04, `generate(model, tokenizer, prompt, ...)` concatenates streamed `.text` values and normally returns a Python string. If the assembled text is empty, `verbose=True` prints `No text generated for this prompt` and returns `None`; the default `verbose=False` path returns the empty string. (two sources) verified-as-of: 2026-10-23[^c1-1][^c1-2][^c1-11]
- `stream_generate` is a generator of `GenerationResponse` objects, not strings. Callers read each response's `.text`; that field may be empty. Ordinary per-token responses have `finish_reason=None`, and the final response reports `stop` for EOS or `length` when generation ends at the token cap. verified-as-of: 2026-10-23[^c1-1][^c1-2][^c1-3]
- The current mlx_lm package exports load, generate, and stream_generate at package top level; load returns the (model, tokenizer) pair used by the generation helpers. verified-as-of: 2026-10-23[^c1-9][^c1-10][^c1-2]
- generate is the whole-response helper: it iterates stream_generate, concatenates each response.text segment, and returns the generated continuation when text exists; verbose=True prints the generated text and final token, speed, and memory statistics. verified-as-of: 2026-10-23[^c1-1][^c1-2][^c1-3]
- stream_generate returns a Python generator and accepts a prompt as str, mx.array, or List[int]; it tokenizes string prompts internally and yields GenerationResponse objects. verified-as-of: 2026-10-23[^c1-1][^c1-10][^c1-2][^c1-3]
- GenerationResponse.text is the next decoded text segment and may be empty; each response also carries the token, log probabilities, draft-model flag, prompt and generation token counts and rates, peak memory, and optional finish_reason. verified-as-of: 2026-10-23[^c1-1][^c1-2][^c1-3]
- Tentative: In current upstream main, stream_generate yields intermediate responses with finish_reason=None, then finalizes the detokenizer and yields a terminal response marked stop for EOS or length when the token limit ends generation. If EOS ends generation, the terminal response's token field still contains the EOS token, although that token is not appended to decoded text. verified-as-of: 2026-10-23[^c1-1]

### MLX-LM custom sampling and logits processors

- MLX-LM's Python generate and stream_generate functions accept separate sampler and logits_processors callables. Each processor receives token history and current logits; processors run in list order before normalization, and current generate.py passes normalized log-probabilities to the sampler. verified-as-of: 2026-10-23[^c2-1][^c2-2][^c2-3]
- The current generate_step API accepts optional sampler and logits_processors arguments, and stream_generate forwards its extra keyword arguments to generate_step. Each processor receives (tokens, logits) and returns revised logits; generation applies processors before normalizing logits and sampling. This lets callers pass custom callables as well as the supplied factories. verified-as-of: 2026-10-23[^c2-2][^c2-3][^c2-4]
- make_sampler returns greedy argmax immediately when temp == 0, so the filtering chain is bypassed at zero temperature. At nonzero temperature, the factory applies enabled top-p, min-p, XTC, then top-k filters to log probabilities before categorical sampling. verified-as-of: 2026-10-23[^c2-3][^c2-4]
- make_logits_processors can build processors for additive logit_bias, sign-aware repetition penalty, presence penalty, and frequency penalty. Its three penalty context-size defaults are 20 tokens; presence subtracts once for tokens in the context, while frequency subtracts per occurrence. verified-as-of: 2026-10-23[^c2-3][^c2-5]

### MLX-LM perplexity and lm-evaluation

_(no core claims)_

## Tools & Frameworks

- sample_utils.make_sampler returns greedy argmax for temp=0; otherwise it applies enabled top-p, min-p, XTC, and top-k filters before categorical sampling at the requested temperature. make_logits_processors builds optional additive logit bias followed by enabled repetition, presence, and frequency penalties. The independent csm-mlx README demonstrates make_sampler(temp=0.8, top_k=50) and logit-bias use. verified-as-of: 2026-10-23[^c2-3][^c2-4][^c2-2] _(MLX-LM custom sampling and logits processors)_
- As of the inspected source, `mlx_lm.perplexity` computes next-token cross-entropy, reports `exp(mean(token_loss))`, and estimates perplexity standard error with a delta approximation. Its CLI defaults are `allenai/tulu-3-sft-mixture`, 256 examples, sequence length 512, batch size 8, and seed 123; it randomly permutes dataset rows, concatenates tokenized contents, and reshapes the stream into fixed-length sequences. verified-as-of: 2026-10-23[^c3-1][^c3-12][^c3-3] _(MLX-LM perplexity and lm-evaluation)_
- `mlx_lm.evaluate` registers the `mlxlm` backend with lm-evaluation-harness and implements `loglikelihood` and `loglikelihood_rolling`. The current `mlx-lm[evaluate]` extra installs `lm-eval` and `tqdm`, and the package registers the `mlx_lm.evaluate` command entry point. verified-as-of: 2026-10-23[^c3-2][^c3-3][^c3-6] _(MLX-LM perplexity and lm-evaluation)_
- The standalone `mlx_lm.perplexity` CLI has no `--adapter-path` option in its current parser. To score an adapter, use `mlx_lm.lora --test` on the held-out dataset or fuse the adapter before using the standalone perplexity command. verified-as-of: 2026-10-23[^c3-1][^c3-4][^c3-11] _(MLX-LM perplexity and lm-evaluation)_
- `mlx_lm.evaluate` registers an MLX model with EleutherAI's `lm-evaluation-harness` and implements continuation log-likelihood, rolling log-likelihood, and generation. The harness model guide defines rolling log-likelihood as the interface used to evaluate perplexity on a data distribution. verified-as-of: 2026-10-23[^c3-2][^c3-6] _(MLX-LM perplexity and lm-evaluation)_
- The current `mlx-lm` package declares `lm-eval` and `tqdm` in the optional `evaluate` extra, so the harness dependency is not part of the base dependency list. verified-as-of: 2026-10-23[^c3-3][^c3-2] _(MLX-LM perplexity and lm-evaluation)_

## Methodology

- The harness uses `loglikelihood_rolling` for perplexity over a text distribution. MLX-LM scores documents separately. At revision 0d4d3d04, its docstring promises context-bounded windows with maximal context, but the implementation calls `_score_fn`, which processes default 2048-token steps with a continuing cache rather than constructing those windows. Compare implementations as well as documented context policies. verified-as-of: 2026-10-23[^c3-2][^c3-6][^c3-16] _(MLX-LM perplexity and lm-evaluation)_
- `mlx_lm.lora --test` computes test-set perplexity using `test.jsonl` from the dataset named by `--data`. The `--mask-prompt` option changes the scored span from every token to the completion, so compare test perplexities only when both runs use the same masking policy. verified-as-of: 2026-10-23[^c3-4][^c3-11] _(MLX-LM perplexity and lm-evaluation)_
- Token-level perplexity depends on tokenization. A 2026 EACL study reports word-level perplexity through lm-evaluation-harness to enable cross-tokenizer comparisons; a 2025 NeurIPS study cautions that vocabulary-size and likelihood-bound differences made validation perplexity an unsuitable effectiveness comparison in its diffusion-language-model setting. For cross-tokenizer comparisons, state the normalization and pair perplexity with task results. (two sources)[^c3-10][^c3-9] _(MLX-LM perplexity and lm-evaluation)_
- Perplexity measures next-token fit on the scored text; it does not by itself establish downstream task performance. MLX-LM exposes text perplexity and named benchmark tasks through separate commands, while research on benchmark leaderboards shows that task scores can shift under benchmark perturbations. Report both metrics when both text fit and task capability matter. (two sources)[^c3-1][^c3-5][^c3-8] _(MLX-LM perplexity and lm-evaluation)_
- For repeatable comparisons, record model and tokenizer, corpus and split, sample count, context policy, random seed, tasks, few-shot count, prompt-template setting, limit, and package versions. These are reporting requirements, not a claim that every MLX-LM CLI exposes every control: the inspected standalone perplexity loader hardcodes its dataset splits and loads the tokenizer with the model. The project benchmark notes request MLX and MLX-LM versions, and the cited ACL study documents benchmark sensitivity. (two sources) verified-as-of: 2026-10-23[^c3-1][^c3-2][^c3-5][^c3-8][^c3-16][^c3-17] _(MLX-LM perplexity and lm-evaluation)_
- Treat `--limit` runs as smoke tests rather than published benchmark scores: the harness CLI documents `--limit` as testing-only, and the MLX evaluation guide makes the same distinction for limited task runs. verified-as-of: 2026-10-23[^c3-7][^c3-11] _(MLX-LM perplexity and lm-evaluation)_
- At revision 0d4d3d04, standalone `mlx_lm.perplexity` concatenates tokenized dataset rows and reshapes them into disjoint fixed-length sequences. `MLXLM.loglikelihood_rolling` scores documents separately; `_score_fn` shifts encoded inputs and next-token targets, so the first encoded token serves as context rather than a scored target. Its identity depends on tokenizer special-token and template settings. The rolling method does not explicitly prepend EOT, despite its docstring example. Align these protocols before comparing perplexity.[^c3-1][^c3-2][^c3-12][^c3-16][^c3-17] _(MLX-LM perplexity and lm-evaluation)_
- Perplexity depends on tokenization and context-window protocol: Hugging Face's documentation says tokenization directly affects PPL and demonstrates a score change between disjoint windows and a strided sliding window. Compare PPL only after matching tokenizer, corpus preprocessing, scored tokens, and context/scoring protocol.[^c3-12][^c3-1] _(MLX-LM perplexity and lm-evaluation)_
- Harness task results depend on task and prompt protocol: its CLI exposes task selection, few-shot count, chat-template use, generation arguments, and example limits, while an ACL 2024 study found that small changes such as multiple-choice option order or answer-selection method shifted MMLU leaderboard rankings by as many as eight places. Record the exact task version and scoring configuration when reporting a score.[^c3-7][^c3-8] _(MLX-LM perplexity and lm-evaluation)_

## Practical Patterns

- A supplied `prompt_cache` is updated in place. An open MLX-LM issue still reports that direct calls with extending prompts lack first-class prefix-aware reuse, so callers using that pattern must track which tokens the cache represents and trim it themselves. (two sources) verified-as-of: 2026-10-23[^c1-1][^c1-6] _(MLX-LM Python generation and streaming contracts)_
- Tentative: Pass revision="<branch, tag, or commit hash>" to load(path_or_hf_repo, revision=...) to select the Hugging Face model revision. The loader forwards revision to its download helper; pin an immutable commit for reproducible remote model selection. verified-as-of: 2026-10-23[^c1-12] _(MLX-LM Python generation and streaming contracts)_
- Tentative: With an existing prompt_cache, generate_step forwards the supplied prompt tokens to the model with that cache; it does not detect an already cached prefix or strip duplicate tokens. Callers must pass only the uncached suffix and ensure that the cache matches the preceding token history. The supplied cache is mutated in place. verified-as-of: 2026-10-23[^c1-11] _(MLX-LM Python generation and streaming contracts)_
- The independent Exo MLX wrapper composes an application-defined ban_token_ids(eos_ids) processor ahead of built-in penalties and passes the processor list per sequence to MLX-LM's BatchGenerator.insert, providing a concrete pattern for combining custom filters with make_logits_processors in a batched path. verified-as-of: 2026-10-23[^c2-5][^c2-2][^c2-3] _(MLX-LM custom sampling and logits processors)_
- Independent consumers demonstrate the intended integration pattern: csm-mlx passes MLX-LM's sampler to its generator and documents logit bias through logits_processors; Exo's MLX backend imports both factories and builds sampler and processor callables for batched generation. verified-as-of: 2026-10-23[^c2-4][^c2-5] _(MLX-LM custom sampling and logits processors)_
- A Sampler callable receives log-probabilities and returns token indices as an MLX array. In generate_step, logits processors first modify raw logits in list order; the code then subtracts mx.logsumexp(logits, keepdims=True) and passes the resulting log-probabilities to sampler. verified-as-of: 2026-10-23[^c2-11][^c2-12] _(MLX-LM custom sampling and logits processors)_
- Tentative: min_p removes candidates whose probability is below min_p times the most probable token probability. top_p instead filters by cumulative probability mass. min_tokens_to_keep protects a minimum number of the highest-probability candidates from min_p filtering and must be a positive integer. verified-as-of: 2026-10-23[^c2-11] _(MLX-LM custom sampling and logits processors)_
- Tentative: make_logits_processors takes logit_bias as a dictionary mapping integer token IDs to additive bias values. It constructs index and value arrays from the dictionary keys and values, then adds those values to the corresponding logits. verified-as-of: 2026-10-23[^c2-11] _(MLX-LM custom sampling and logits processors)_
- Tentative: For tokens in its selected context, repetition_penalty multiplies negative logits by the penalty and divides nonnegative logits by the penalty. presence_penalty subtracts its penalty once for a token present in context, while frequency_penalty subtracts a penalty scaled by that token's occurrence count. verified-as-of: 2026-10-23[^c2-11] _(MLX-LM custom sampling and logits processors)_
- Tentative: Adapter test evaluation computes test_ppl=math.exp(test_loss). Run mlx_lm.lora --model <base> --adapter-path <adapter_directory> --data <dataset_directory> --test; with --test and no --train, the entry point loads that adapter before evaluating test.jsonl. An empty --adapter-path explicitly skips adapter loading for base-model testing. verified-as-of: 2026-10-23[^c3-18] _(MLX-LM perplexity and lm-evaluation)_
- Tentative: mlx_lm.evaluate requires --model <model> and --tasks <task...>. --num-shots selects the few-shot example count; --limit caps examples per task; --output-dir selects the directory for result files and defaults to the current directory. These CLI options are forwarded to the harness or used for writing its results. verified-as-of: 2026-10-23[^c3-16] _(MLX-LM perplexity and lm-evaluation)_
- Tentative: Use --apply-chat-template or --no-apply-chat-template to explicitly enable or disable evaluation chat templating; argparse.BooleanOptionalAction provides both forms. --confirm-run-unsafe-code explicitly permits harness tasks that execute untrusted code and defaults to false. It is separate from --trust-remote-code for tokenizer loading. verified-as-of: 2026-10-23[^c3-16] _(MLX-LM perplexity and lm-evaluation)_

## Anti-Patterns

- Tentative: stream_generate requires a draft_model to use the same tokenizer as the main model. The native CLI checks draft_tokenizer.vocab_size against tokenizer.vocab_size and raises ValueError("Draft model tokenizer does not match model tokenizer.") on a mismatch; equal vocabulary sizes alone do not prove identical token mappings. verified-as-of: 2026-10-23[^c1-11] _(MLX-LM Python generation and streaming contracts)_

## Troubleshooting

- Advancing `stream_generate(..., max_tokens=0)` raises `ValueError` in the current `main` implementation. A third-party guide still says this path raises `UnboundLocalError`; that note is stale relative to the current source. (two sources) verified-as-of: 2026-10-23[^c1-1][^c1-3] _(MLX-LM Python generation and streaming contracts)_
- The documented `stream_generate` prompt types are `str`, `mx.array`, and `List[int]`. A Transformers `BatchEncoding` returned by `apply_chat_template` can violate that input shape: an MLX-LM issue traced a server crash on Transformers 5.0+ to a chat-template call that omitted `return_dict=False`. (two sources) verified-as-of: 2026-10-23[^c1-1][^c1-4] _(MLX-LM Python generation and streaming contracts)_
- The current implementation creates its default generation stream with `mx.new_thread_local_stream`. A third-party reproduction on MLX-LM 0.31.3 reported `RuntimeError: There is no Stream(gpu, N) in current thread` when a sliding-window model was loaded on one thread and generated on another; keep load and generation on the same thread for affected model and runtime combinations until verified locally. (two sources) verified-as-of: 2026-10-23[^c1-1][^c1-5] _(MLX-LM Python generation and streaming contracts)_
- The inspected `generate` function is annotated to return `str`, but its empty-output path returns `None` when `verbose=True`. With the default `verbose=False`, the same empty-output case returns an empty string. This control-flow distinction requires indentation-preserving source evidence. (two sources) verified-as-of: 2026-10-23[^c1-1][^c1-3][^c1-11] _(MLX-LM Python generation and streaming contracts)_
- Tentative: Current upstream main rejects stream_generate(max_tokens=0) with ValueError and directs callers to use -1 for no token limit. verified-as-of: 2026-10-23[^c1-1] _(MLX-LM Python generation and streaming contracts)_
- April 2026 reports for mlx-lm 0.31.2 describe stateful processors seeing stale token history in stream or MTP paths: one report attributes the observation to lazy token arrays, and another says MTP draft calls omitted the backbone's just-sampled token. The MTP report author later described a vendored fix that snapshots token context and restores it after a rejected draft; the earlier report says stateless repetition penalties were unaffected. Verify this version-specific behavior against the release in use. (two sources) verified-as-of: 2026-04-28[^c2-6][^c2-7][^c2-2] _(MLX-LM custom sampling and logits processors)_
- A Xinference issue opened on 2025-04-09 records that importing make_logits_processors and make_sampler from mlx_lm.utils failed; a follow-up shows the integration importing them from mlx_lm.sample_utils. Current MLX-LM source defines the factories in sample_utils.py, so integrations should check the installed package's module path. (two sources) verified-as-of: 2026-10-23[^c2-8][^c2-3] _(MLX-LM custom sampling and logits processors)_
- A report against mlx-lm 0.31.3 described TypeError: 'NoneType' object is not iterable when continuous batches mixed requests with and without logits processors. Upstream PR #1826 merged on 2026-09-04, normalizing per-sequence samplers and processors and closing the report. verified-as-of: 2026-10-23[^c2-9][^c2-10] _(MLX-LM custom sampling and logits processors)_
- Tentative: An open MLX-LM issue reports that mtp_generate_step in mlx-lm 0.31.2 passed stale prev_tokens to stateful processors on speculative draft calls. The author says the current main MTP path had since been restructured, so this version-specific report does not establish a defect in ordinary serial generate_step. verified-as-of: 2026-10-23[^c2-7] _(MLX-LM custom sampling and logits processors)_
- Tentative: apply_top_k rejects top_k unless it is an integer strictly greater than zero and strictly less than logprobs.shape[-1] (the vocabulary size), raising ValueError otherwise. make_sampler separately treats top_k=0 as disabling its top-k filter. verified-as-of: 2026-10-23[^c2-11] _(MLX-LM custom sampling and logits processors)_
- The current MLX-LM `BENCHMARKS.md` example spells the task option `--task`, while `mlx_lm.evaluate` declares the required option as `--tasks`. Use the plural spelling declared by the parser; whether argparse accepts the singular spelling as an abbreviation was not verified. (two sources) verified-as-of: 2026-10-23[^c3-5][^c3-2] _(MLX-LM perplexity and lm-evaluation)_
- A July 2025 import failure report traced `mlx_lm.evaluate` to access of `lm_eval.models.huggingface.HFLM.tokenizer_name`; the issue was closed as fixed in PR #275. Current `evaluate.py` instead imports `LM` and `register_model` from `lm_eval.api` and derives the tokenizer name from the loaded tokenizer, so that specific internal-attribute access is absent in the inspected source. This does not verify every current version combination. (two sources) verified-as-of: 2026-10-23[^c3-13][^c3-2] _(MLX-LM perplexity and lm-evaluation)_
- Tentative: A January 2024 upstream harness report recorded NaN perplexity and sharply lower LAMBADA accuracy for Pythia-70M with automatic dtype; setting `dtype=float32` restored the earlier reported score, and a maintainer noted small Pythia models were sensitive to 16-bit precision. This is a historical numeric-precision example, not evidence of a current MLX-LM failure.[^c3-14] _(MLX-LM perplexity and lm-evaluation)_
- Tentative: A January 2026 MLX-LM issue reported that `mlx_lm.evaluate` failed while compiling a Metal kernel with `unknown type name 'bfloat16_t'` on `mlx-lm 0.30.4`, `mlx 0.30.4.dev`, and macOS 26.2. The reporter said deleting `build/` and rebuilding resolved that installation; the thread did not establish a general root cause or current status.[^c3-15] _(MLX-LM perplexity and lm-evaluation)_

## Disagreements & Open Questions

- Disagreement (MLX-LM Python generation and streaming contracts): The Microsoft tutorial loops over `stream_generate` as if each item were a string token, but the current implementation yields `GenerationResponse` objects and other examples read `.text`.[^c1-7][^c1-1][^c1-2]
- Disagreement (MLX-LM Python generation and streaming contracts): The HB Martin guide says `max_tokens=0` raises `UnboundLocalError`, while current `main` explicitly raises `ValueError`; its example is tested against an earlier `e5baded` snapshot.[^c1-3][^c1-1]
- Disagreement (MLX-LM Python generation and streaming contracts): A downstream `vllm-mlx` issue recorded `finish_reason=null` in its HTTP stream on natural stop, then closed after a wrapper fix. This was a wrapper conversion problem and does not contradict the direct Python `GenerationResponse.finish_reason` behavior.[^c1-8][^c1-1]
- Disagreement (MLX-LM Python generation and streaming contracts): The H.B. Martin guide says an EOS token is not visible in GenerationResponse.token. Current upstream main skips appending EOS to decoded text but includes the EOS value in the terminal response's token field.[^c1-3][^c1-1]
- Disagreement (MLX-LM Python generation and streaming contracts): The H.B. Martin guide describes max_tokens=0 as causing UnboundLocalError in its source snapshot. Current upstream main checks zero before iteration and raises ValueError instead, so this edge case is version-dependent.[^c1-3][^c1-1]
- Disagreement (MLX-LM Python generation and streaming contracts): A vllm-mlx issue reported missing natural-stop finish_reason in that wrapper's HTTP stream when testing mlx-lm 0.31.3; the issue was closed as completed after wrapper fixes in August 2026. This scopes the report to that wrapper and version, rather than the direct Python stream_generate contract.[^c1-8][^c1-1]
- Open (MLX-LM Python generation and streaming contracts): The thread-affinity reproduction used MLX-LM 0.31.3; the same sliding-window model and worker-thread setup have not been verified against the current release.
- Open (MLX-LM Python generation and streaming contracts): A university lecture-note PDF surfaced with a `stream_generate` example, but source.put skipped it because its response content type was application/pdf; it was not used in the claims.
- Open (MLX-LM Python generation and streaming contracts): Which installed mlx-lm versions still differ from current upstream main on zero-token requests and terminal EOS metadata?
- Disagreement (MLX-LM custom sampling and logits processors): The pinned README describes the sampler input as a possibly batched logits array, while current generate.py normalizes processed logits to log-probabilities before calling the sampler; sample_utils also documents its helper sampler as receiving log-probabilities.[^c2-1][^c2-2][^c2-3]
- Disagreement (MLX-LM custom sampling and logits processors): Issue #1156 initially attributed stale tokens in serial generation to lazy evaluation, but a maintainer disputed that mechanism and closed the report. Issue #1175 separately reports stale context on an older MTP draft path; it does not establish that the ordinary serial path is broken.[^c2-6][^c2-7]
- Open (MLX-LM custom sampling and logits processors): Does the current speculative or MTP path preserve external processor state and restore it after rejected draft tokens? The April 2026 report says the callable interface has no save/restore protocol.
- Open (MLX-LM custom sampling and logits processors): What array shapes and dtypes are guaranteed for user-defined samplers and processors across serial, streaming, and per-sequence batched entrypoints?
- Open (MLX-LM custom sampling and logits processors): Does the mlx-lm 0.31.2 MTP stale-context report apply to the newer, restructured main-branch draft path?
- Disagreement (MLX-LM perplexity and lm-evaluation): MLX-LM's benchmark documentation uses `--task`, but the current `evaluate.py` parser declares required `--tasks`; the docs and parser spellings differ. The actual behavior of argparse abbreviation was not tested.[^c3-5][^c3-2]
- Open (MLX-LM perplexity and lm-evaluation): The repository does not establish numeric equivalence between standalone fixed-length sampled perplexity and harness rolling perplexity; comparisons should align corpus, tokenization, document boundaries, and context policy.
- Open (MLX-LM perplexity and lm-evaluation): Argparse abbreviation behavior for the documented `--task` spelling was not executed; the parser-declared `--tasks` spelling is the verified option.
- Open (MLX-LM perplexity and lm-evaluation): No current runtime matrix was run across `mlx-lm`, MLX, `lm-eval`, Python, macOS, and hardware; the historical reports do not establish present-day compatibility.
- Open (MLX-LM perplexity and lm-evaluation): The standalone PPL default uses an SFT-mixture dataset and the loader is configured for its training data. Select an explicit held-out corpus and split when the evaluation question requires held-out perplexity.

## References

### MLX-LM Python generation and streaming contracts

[^c1-1]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/generate.py — mlx-lm generate.py current Python API implementation (repo)
[^c1-2]: https://brianpfeil.com/courses/mlx-lm/lessons/0002-the-python-surface.html — MLX-LM course: the Python surface and chat templates (blog)
[^c1-3]: https://hbmartin.github.io/Foundation-Models-and-Core-AI-and-MLX-skills/part-12-mlx-python/references/04-mlx-lm-cli-generation-and-caching/ — mlx-lm: the CLI surface, the generation API, and KV caching (blog)
[^c1-4]: https://github.com/ml-explore/mlx-lm/issues/897 — server.py chat completions crash with transformers >= 5.0 (forum)
[^c1-5]: https://github.com/cubist38/mlx-openai-server/issues/312 — Sliding-window models fail across generation threads (forum)
[^c1-6]: https://github.com/ml-explore/mlx-lm/issues/1194 — Library-level helper for prefix-aware prompt cache reuse with stream_generate (forum)
[^c1-7]: https://github.com/microsoft/edgeai-for-beginners/blob/main/translations/pcm/Module04/05.AppleMLX.md — Apple MLX and MLX-LM tutorial (repo)
[^c1-8]: https://github.com/waybarrios/vllm-mlx/issues/628 — Streaming chat completions never emit finish_reason stop on natural stops (forum)
[^c1-9]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/__init__.py — mlx-lm package exports (repo)
[^c1-10]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/README.md — MLX-LM README at pinned commit (repo)
[^c1-11]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/generate.py — MLX-LM generate.py at 0d4d3d04 (repo)
[^c1-12]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/utils.py — Pinned primary source (repo)

### MLX-LM custom sampling and logits processors

[^c2-1]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/README.md — MLX-LM README at pinned commit (repo)
[^c2-2]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/generate.py — MLX-LM generate.py at main (repo)
[^c2-3]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/sample_utils.py — MLX-LM sample_utils.py at main (repo)
[^c2-4]: https://github.com/senstella/csm-mlx — csm-mlx README (repo)
[^c2-5]: https://github.com/exo-explore/exo/blob/main/src/exo/worker/engines/mlx/generator/batch_generate.py — exo MLX batch_generate.py (repo)
[^c2-6]: https://github.com/ml-explore/mlx-lm/issues/1156 — Stateful logits processors see stale tokens due to lazy evaluation in stream context (forum)
[^c2-7]: https://github.com/ml-explore/mlx-lm/issues/1175 — mtp_generate_step logits processors see stale prev_tokens on draft calls (forum)
[^c2-8]: https://github.com/xorbitsai/inference/issues/3210 — Xinference MLX import path issue #3210 (forum)
[^c2-9]: https://github.com/ml-explore/mlx-lm/issues/1472 — MLX-LM mixed logits processors batching issue #1472 (forum)
[^c2-10]: https://github.com/ml-explore/mlx-lm/pull/1826 — MLX-LM normalize per-sequence samplers and logits processors #1826 (repo)
[^c2-11]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/sample_utils.py — Pinned primary source (repo)
[^c2-12]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/generate.py — Pinned primary source (repo)

### MLX-LM perplexity and lm-evaluation

[^c3-1]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/perplexity.py — mlx-lm perplexity.py (repo)
[^c3-2]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/evaluate.py — mlx-lm evaluate.py (repo)
[^c3-3]: https://github.com/ml-explore/mlx-lm/blob/main/pyproject.toml — mlx-lm pyproject.toml (repo)
[^c3-4]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md — MLX-LM LoRA guide on GitHub main (docs)
[^c3-5]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/BENCHMARKS.md — mlx-lm benchmark notes (repo)
[^c3-6]: https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/model_guide.md — lm-evaluation-harness model guide (repo)
[^c3-7]: https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/interface.md — lm-evaluation-harness CLI interface (repo)
[^c3-8]: https://aclanthology.org/2024.acl-long.744/ — When Benchmarks are Targets: Revealing the Sensitivity of Large Language Model Leaderboards (paper)
[^c3-9]: https://proceedings.neurips.cc/paper_files/paper/2025/file/3b3d7aafe5f36995a8320059a858e4b9-Paper-Conference.pdf — Next Semantic Scale Prediction via (paper)
[^c3-10]: https://aclanthology.org/2026.eacl-long.119.pdf — EACL 2026 paper on word-level perplexity (paper)
[^c3-11]: https://hbmartin.github.io/Foundation-Models-and-Core-AI-and-MLX-skills/part-12-mlx-python/references/06-finetuning-and-porting-models/ — Apple AI Guides: LoRA and DoRA fine tuning (blog)
[^c3-12]: https://huggingface.co/buckets/hf-doc-build/doc/tree/transformers/v5.12.1/en/perplexity.md?code=true — Perplexity of fixed-length models, Transformers v5.12.1 (docs)
[^c3-13]: https://github.com/ml-explore/mlx-lm/issues/274 — mlx-lm issue 274: lm_eval.models import error (forum)
[^c3-14]: https://github.com/EleutherAI/lm-evaluation-harness/issues/1269 — lm-evaluation-harness issue 1269: divergent benchmark results (forum)
[^c3-15]: https://github.com/ml-explore/mlx-lm/issues/784 — mlx-lm issue 784: Metal bfloat16 error (forum)
[^c3-16]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/evaluate.py — MLX-LM evaluate.py at 0d4d3d04 (repo)
[^c3-17]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/perplexity.py — MLX-LM perplexity.py at 0d4d3d04 (repo)
[^c3-18]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/lora.py — Pinned primary source (repo)
