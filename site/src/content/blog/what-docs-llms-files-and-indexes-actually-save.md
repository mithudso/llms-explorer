---
title: "What Good Docs, llms Files and Indexes Actually Save: 256 Agent Runs"
description: "A controlled measurement of what documentation, llms files and keyword-plus-semantic indexes save a coding agent. Docs loaded into context cut cost 36–44%; llms files on disk and search indexes saved nothing measurable on two small repos; the agents opened an llms file once in 256 runs; and token counts turned out to be the wrong thing to watch."
date: "2026-09-27"
order: 29
tags: [tokens, cost, documentation, llms-txt, retrieval, measurement]
sources:
  - research/token-cost-2026-09/results.jsonl
  - research/token-cost-2026-09/questions.json
  - research/token-cost-2026-09/run_matrix.py
  - research/token-cost-2026-09/analyze.py
  - research/token-cost-2026-09/retrieval_hits.jsonl
  - research/token-cost-2026-09/gen_results.jsonl
---

*An experiment run end to end on 2026-09-27. Every number below comes from the runs in [`research/token-cost-2026-09/`](https://github.com/mithudso/llms-explorer/tree/main/research/token-cost-2026-09), which holds the harness, the questions, the answer key and the raw results.*

---

## Abstract

I asked a coding agent the same 16 questions about two real repositories under eight setups. Some setups gave it human documentation, some gave it llms files (the `llms.txt` family: an index, a short digest, the full docs in one file, and a list of facts), some gave it a keyword-plus-semantic search index, and one gave it only the code. Each setup ran twice per question in an isolated headless Claude Code session, 256 runs in all, and every answer was graded against a key.

**Bottom line up front.**

- **Documentation saved the most when it was in the agent's context.** With the repository's `CLAUDE.md` loaded, the same questions cost **44% less for lookups and 36% less for comprehension** than with code alone. On disk, the same documents saved 18% on comprehension and nothing measurable on lookups.
- **These agents did not read llms files.** In 256 runs an agent opened an llms file **once**, and that was with a `CLAUDE.md` line telling it to read `llms-small.txt` first. On disk, llms files changed nothing measurable.
- **On two small repositories, a search index did not pay.** Keyword plus semantic search changed lookup cost by −4% (95% CI −20% to +15%), and it was almost never used once `CLAUDE.md` was present: one search in 32 runs.
- **Tokens are the wrong unit.** An agent's prompt cache charges twice the input price for new material and a tenth of it for material it has already seen. In the code-only runs, **60–63% of the cost was cache writes**. On comprehension questions, loading `CLAUDE.md` barely changed the token count (−5%) but cut mean cost by 36%, because it kept tool results out of the conversation.

Everything here holds for two small, unusually well-documented repositories and one model. The last sections cover what that does and does not generalize to, and the three ways this measurement nearly lied to me.

---

## Why "true" savings needs a measurement

Most claims about docs and llms files compare file sizes. My own [inventory post](/blog/every-token-saving-strategy/) reports that `llms-small.txt` runs 13–97× smaller than `llms-full.txt`, and that retrieval answered a docset question in about 1,500 tokens instead of 248,761. Those numbers are true, but they measure the artifacts, not the agent. A ratio of file sizes leaves out four things that decide what a question actually costs:

1. **Whether the agent uses the asset at all.** A file it never opens saves nothing.
2. **Prompt caching.** Context the model has already seen is billed at a tenth of the input price. New context is billed at double.
3. **Correctness.** A cheap wrong answer is not a saving.
4. **The cost of making and keeping the asset.** Documentation, llms files and indexes all cost something to build.

The only way to count all four is to put an agent in front of the same questions with and without each asset, and read the bill.

---

## Setup

**Repositories.** Two of my public repos, chosen because both have unusually thorough docs and a generated llms family:

| Repo | Language | Code + tests | Human docs | llms files |
|---|---|---|---|---|
| [llm-cache-proxy](https://github.com/mithudso/llm-cache-proxy) | JavaScript | 119 KB | 90 KB | 86 KB |
| [llm-memory-pyramid](https://github.com/mithudso/llm-memory-pyramid) | Python | 194 KB | 108 KB | 35 KB |

**Corpora.** From `git archive HEAD` of each repo I built four copies: code only (every `*.md`, `llms*.txt` and `docs/` removed), code plus human docs, code plus docs plus llms files, and that last one with a section appended to `CLAUDE.md`: "Start with `llms-small.txt`… Read them before searching the code."

**The index.** For the index conditions I built two indexes over the same files the agent could see, chunked at 40 lines with 5 lines of overlap: a keyword index (SQLite's FTS5 full-text search, ranked by BM25) and a semantic index (embeddings from a local Ollama model). A small MCP server, the protocol Claude Code uses to call external tools, exposes two tools, `search_keyword` and `search_semantic`. Each returns the top five chunks with paths and line ranges, each chunk cut to 800 characters. The index file lives outside the agent's working directory, so the only way in is the tools.

**Conditions.**

| | On disk | Also in context | Tools |
|---|---|---|---|
| **A** | code | — | Read, Grep, Glob |
| **B** | code + docs | — | Read, Grep, Glob |
| **C** | code + docs + llms files | — | Read, Grep, Glob |
| **D** | code + docs | — | + keyword and semantic search |
| **E** | code | — | + keyword and semantic search |
| **G** | code + docs | the repo's `CLAUDE.md` | Read, Grep, Glob |
| **H** | code + docs | the repo's `CLAUDE.md` | + keyword and semantic search |
| **I** | code + docs + llms files | `CLAUDE.md` with the llms pointer | Read, Grep, Glob |

G, H and I are the realistic ones. A normal Claude Code session always loads the project's `CLAUDE.md`, and that is how most documentation reaches an agent. B, C, D and E keep the documents on disk only, which isolates what the files themselves do. A ninth condition, F, was meant to test the llms pointer but never delivered it to the agent; it is described under "How the measurement nearly lied" and left out of every table.

**Questions.** Sixteen per condition: 12 **lookups** with one specific answer ("What is the default cache TTL and maximum entry count?") and 4 **comprehension** questions ("Walk through the steps a request goes through before any upstream call, naming every cache tier"). Every answer exists in the code. For 14 of the 16 it also appears in the human docs; two (`MAX_INPUT_CHARS = 600_000`, and the Ollama extractor's `num_ctx` and `num_predict`) exist only in code. None of the 12 lookup answers appears in either repo's `llms-small.txt`, which is a map of the repo rather than a store of facts; for the comprehension questions it holds pieces of two answers.

**Runs.** Each (question, condition) pair ran twice, as `claude -p --restricted --strict-mcp-config` with Sonnet (`claude-sonnet-5`). `--restricted` skips my user settings, so no hooks, plugins or skills load, and it confines file tools to the working directory. Every run starts from the same base prompt of about 8k tokens, plus whatever its condition adds. A **turn** below is one model call in the agent's loop. An answer counts as correct when it contains every required fact in the key; I checked each automatic miss by hand.

**Prices.** I did not assume a price list. Claude Code reports each run's cost, and fitting cost against the four token counts over all 256 runs recovers the rates exactly (zero residual): **$2 per million input tokens, $4 per million cache writes, $0.20 per million cache reads, $10 per million output tokens.** Cache writes cost twice the input price, which is the one-hour cache. The runs were billed to a Max subscription; the dollar figures are what the same tokens cost at those API rates.

**Statistics.** "vs A" is the ratio of the condition's mean cost to code-only's mean cost, minus one. The 95% intervals come from a paired bootstrap that resamples questions, so they reflect question-to-question variation. For lookups that means 12 questions; for comprehension only 4, so treat the comprehension intervals as indicative.

---

## Result 1: documentation pays most when it is in context

**Lookup questions** (12 questions × 2 runs = 24 per condition):

| | Setup | Correct | Mean cost | vs A | 95% CI | Turns |
|---|---|---|---|---|---|---|
| A | code only | 24/24 | $0.0293 | — | — | 3.5 |
| B | docs on disk | 24/24 | $0.0278 | −5% | −19% to +12% | 4.0 |
| C | docs + llms on disk | 23/24 | $0.0326 | +11% | −19% to +55% | 3.9 |
| D | docs on disk + index | 24/24 | $0.0321 | +10% | −15% to +43% | 4.0 |
| E | code + index | 24/24 | $0.0280 | −4% | −20% to +15% | 3.8 |
| **G** | **docs + CLAUDE.md** | 24/24 | **$0.0163** | **−44%** | −53% to −35% | 2.5 |
| **H** | **docs + CLAUDE.md + index** | 24/24 | **$0.0186** | **−36%** | −55% to −13% | 2.5 |
| **I** | **llms + CLAUDE.md pointer** | 24/24 | **$0.0185** | **−37%** | −51% to −18% | 2.6 |

**Comprehension questions** (4 questions × 2 runs = 8 per condition):

| | Setup | Correct | Mean cost | vs A | 95% CI | Turns |
|---|---|---|---|---|---|---|
| A | code only | 8/8 | $0.0758 | — | — | 6.4 |
| B | docs on disk | 8/8 | $0.0620 | −18% | −31% to −4% | 3.6 |
| C | docs + llms on disk | 8/8 | $0.0714 | −6% | −30% to +33% | 4.9 |
| D | docs on disk + index | 7/8 | $0.0632 | −17% | −33% to +12% | 4.4 |
| E | code + index | 6/8 | $0.0716 | −6% | −27% to +4% | 5.5 |
| **G** | **docs + CLAUDE.md** | 8/8 | **$0.0482** | **−36%** | −55% to −13% | 5.1 |
| **H** | **docs + CLAUDE.md + index** | 8/8 | **$0.0502** | **−34%** | −44% to −16% | 4.9 |
| **I** | **llms + CLAUDE.md pointer** | 8/8 | **$0.0423** | **−44%** | −59% to −19% | 4.6 |

Only the three conditions with `CLAUDE.md` in context beat code alone on both kinds of question, by 34–44%. Docs on disk helped comprehension (−18%) and did nothing measurable for lookups. The direction held in both repositories: loading `CLAUDE.md` cut lookup cost by 35% in the JavaScript repo and 52% in the Python one.

On lookups, the turn counts show how. A lookup took 3.5 turns with code alone and 2.5 with `CLAUDE.md` loaded. When the answer is already in context, the agent confirms it with one grep and stops; when it is not, the agent searches, reads, and searches again. Both repos' `CLAUDE.md` files are about 6.2 KB, roughly 1,600 tokens, and hold exactly the kind of facts the lookups asked for: defaults, file roles, the cache-key formula.

One anecdote points the same way. On the two questions whose answers exist only in code, and so not in `CLAUDE.md`, loading `CLAUDE.md` still cut mean cost by 54%. That is 4 runs per condition with no interval worth computing. The likely reason is that `CLAUDE.md` names the files involved: the Python repo's mentions both extractor modules, so the agent knew where to look.

---

## Result 2: tokens are the wrong unit

Where the money went, per question, by token type:

| | Setup | Mean cost | Cache writes | Cache reads | Output | Total tokens |
|---|---|---|---|---|---|---|
| Lookup A | code only | $0.0293 | 60% | 20% | 20% | 33,704 |
| Lookup G | docs + CLAUDE.md | $0.0163 | 41% | 33% | 26% | 28,793 |
| Comprehension A | code only | $0.0758 | 63% | 13% | 24% | 63,474 |
| Comprehension B | docs on disk | $0.0620 | 76% | 9% | 15% | 40,000 |
| Comprehension G | docs + CLAUDE.md | $0.0482 | 52% | 22% | 26% | 60,454 |

Two rows make the point. On comprehension questions, docs on disk (B) cut total tokens by 37% but mean cost by only 18%. Loading `CLAUDE.md` (G) cut total tokens by 5% and mean cost by 36%.

The reason is how an agent loop is billed. Each turn re-reads the whole conversation from the cache, which is cheap at $0.20 per million tokens. But every new tool result, whether a grep hit list or a file excerpt, is written to the cache on the following turn at $4 per million, twenty times the read price. In the code-only runs those writes were 60–63% of the bill.

Row B shows that fewer turns alone do not fix this. With docs on disk, comprehension took the fewest turns of any condition (3.6), but the agent spent them reading long documentation files. Those results went into the cache, and its cache-write spend stayed about where code-only's was: $0.047 against $0.048. What `CLAUDE.md` changed was how much new material entered the conversation. The facts were already in the cached prefix, so fewer and smaller tool results had to be written.

A dashboard that counts tokens weights a cache read and a cache write the same, so it points at the wrong thing. The number to watch is cache-write tokens: new material entering the conversation.

---

## Result 3: these agents did not read llms files

Across all 256 runs, an agent opened a file named `llms*` **once**. That single read was in condition I, where `CLAUDE.md` said to start with `llms-small.txt`; the other 31 runs in I ignored the instruction and went to `grep`. With llms files on disk and no pointer (C), no run in 32 opened one.

Condition I still came out cheap (−37% and −44%), but not because of the llms files. I and G both have `CLAUDE.md` in context, and they are close on lookups: $0.0185 against $0.0163. The llms files themselves added nothing I could measure, and on disk without a pointer the point estimate was slightly worse than code alone (+11% on lookups, with an interval spanning zero).

What I read from that: an agent that already has the repository treats `grep` as its index, and it is a good one. `llms-small.txt` held none of the 12 lookup answers, because a digest points at facts rather than holding them. For this kind of agent, a map of the repo competes with a tool that finds the fact directly, and the tool wins. This is one model on two repositories; another model, or a repository too large to grep, could behave differently.

That does not make llms files worthless; it moves where they pay. They are built for readers who do *not* have the repository: an agent fetching a site's docs over HTTP, a chat model given one file, or a search layer like this site's, which serves `llms.txt` families with token counts in the `X-Markdown-Tokens` header. None of that is what this experiment measured.

---

## Result 4: indexes did not pay on small repos

Before the agent runs, I measured retrieval quality on its own. For each of the 12 lookup questions, **hit@5** asks whether the top five results include a chunk containing the answer:

| Retriever | Code only | Code + docs | Build time per corpus |
|---|---|---|---|
| BM25 keyword (question text as the query) | 6/12 | 7/12 | — |
| `nomic-embed-text` | 9/12 | 8/12 | 1–2 s |
| `mxbai-embed-large` | 10/12 | 9/12 | 3–17 s |
| `qwen3-embedding:4b` | 8/12 | 10/12 | 20–32 s |

All three embedding models ran on a laptop through Ollama, so building an index cost no API tokens. The agent runs used `mxbai-embed-large`, the best on average. The keyword scores are a floor: they use the whole question as the query, and an agent writes sharper queries than that.

In the agent runs, the index changed nothing measurable. On lookups, code plus index (E) came out at −4% and docs plus index (D) at +10%, both with intervals spanning zero. Split by repository, E against A was −25% in the Python repo and +21% in the JavaScript one, six questions each. On comprehension, code plus index missed one question in both of its runs (6/8). That question asked how an agent queries the memory pyramid without raw logs. Semantic search surfaced a plausible neighbor, an internal `NapMemRetrievalAgent` class, and the agent answered with that instead of the MCP server that is the real interface. Docs plus index made the same mistake once.

With `CLAUDE.md` loaded, the index went unused: one search call in the 32 runs of condition H.

An index also has standing costs that `grep` does not. Its tool definitions sit in every run's prompt, and each search returns up to about a thousand tokens of chunks whether or not they help. H cost $0.0186 per lookup against G's $0.0163 while searching once in 32 runs; if that gap is not noise, it comes mostly from the tool definitions. On repositories of a few hundred kilobytes, where `grep` reaches every file in one call, those costs were not repaid. The case for an index is a corpus too large to grep or read, such as a docset. For that range, see the [distillers measurement](/blog/every-token-saving-strategy/) (248,761 tokens for the raw mirror against about 1,500 per retrieved answer) and the posts on [keyword plus vector](/blog/keyword-plus-vector/) and [semantic indexing](/blog/semantic-indexing/). This experiment does not test it.

---

## What the assets cost, and when they pay back

I measured creation cost the same way: an isolated session with write access, asked to produce each asset.

| Asset | llm-cache-proxy | llm-memory-pyramid |
|---|---|---|
| `llms.txt` + `llms-small.txt`, from code and docs | $0.31 (16 turns) | $0.24 (18 turns) |
| README + configuration reference, from code alone | $0.48 (23 turns) | $0.65 (32 turns) |
| Keyword + semantic index | $0 in API tokens, 3–17 s locally | $0 in API tokens, 3–4 s |

**Documentation in context.** Loading `CLAUDE.md` saved $0.013 per lookup and $0.028 per comprehension question. At those rates, a documentation set costing $0.48–0.65 to write pays for itself in about **37–50 lookups** or **17–24 comprehension questions**. Its standing cost is small: about 1,600 tokens, which is $0.0003 per turn once cached and $0.006 each time the one-hour cache is rewritten. This estimate joins two measurements: the generated README is not the same document as the repository's existing `CLAUDE.md`, and the savings were measured with the latter.

**llms files, for an agent that has the repo.** They cost $0.24–0.31 to generate and saved nothing measurable, because the agents did not read them. There is no break-even to compute.

**The index.** Building it cost no API tokens, but using it costs a little on every run through its tool definitions, and it saved nothing measurable at this size.

---

## How the measurement nearly lied

Three problems in the harness each changed the answer, and I found them only by reading individual runs.

1. **The directory name leaked the condition.** In the first pass, each sandbox lived in a folder named `code`, `docs` or `llms`, and the agent's system prompt includes its working directory. One agent answered, "I'm restricted to the `docs` directory and can't read `ollama_extractor.py`", believing it was inside a `docs/` subfolder. In that pass, docs on disk looked **45% more expensive** than code alone. After I moved every sandbox to a neutral path shaped like a real checkout, the same condition came out **5% cheaper**, within noise. I discarded the first pass; it is in the research folder as `results_pilot_discarded.jsonl`.
2. **`--restricted` never loads a project's `CLAUDE.md`.** My first design, condition F, put the llms pointer in `CLAUDE.md` and measured nothing, because the agent never saw it. I found out by asking an agent to quote its `CLAUDE.md`; it said it had none. Conditions G, H and I load the file explicitly with `--append-system-prompt-file`, and F is left out of the results.
3. **Two runner bugs.** `--allowedTools` takes a variable number of arguments and swallowed the prompt as a tool name. Later, an empty file path in one run's tool call raised an exception that killed the whole worker pool at run 47. Both are fixed in the published harness, and every run now records a result or an error, never a crash.

The lesson for anyone measuring agents: controlling the files on disk is not enough. You also control what the prompt says about them, and the working directory is part of the prompt.

---

## Limits

- **Two small repositories.** Both are a few hundred kilobytes, well documented, and written by me. On a large codebase, where `grep` returns hundreds of hits, both docs and indexes may be worth more, and this experiment says nothing about that.
- **One model, two runs per cell.** Sonnet only. The comprehension intervals rest on four questions and are indicative at best; the llms and index lookup intervals are wide.
- **Questions from the author.** I wrote the questions and the key, and most answers are also in the docs, which favors documentation. Two code-only questions check the opposite case.
- **A generous `CLAUDE.md`.** Both repositories' `CLAUDE.md` files carry the facts the lookups asked for. A thin `CLAUDE.md` would save less.
- **One index design.** 40-line chunks, top five results, 800-character snippets, `mxbai-embed-large`. Other designs could do better.

---

## What I would do with this

1. **Put the load-bearing facts where the agent already looks.** Defaults, file roles, formulas and commands belong in `CLAUDE.md` or `AGENTS.md`. At about 1,600 tokens it cost $0.0003 per cached turn and cut question cost by 36–44%.
2. **Do not count on agents to discover llms files.** Inside a repository, these agents grepped. Publish llms files for readers who do not have the repository, and serve them where those readers will find them.
3. **Build an index when the corpus outgrows grep**, not by default. On a small repository it adds tool definitions and result payloads and can hand back a confident wrong neighbor.
4. **Measure cost, not tokens.** Split the bill into cache writes, cache reads and output. The cheapest change is usually the one that keeps new material out of the conversation.
5. **Read individual runs before trusting a table.** The directory-name leak moved one condition by 50 percentage points, more than any real effect in the experiment.

---

## Reproduce

Everything is in [`research/token-cost-2026-09/`](https://github.com/mithudso/llms-explorer/tree/main/research/token-cost-2026-09). With Claude Code, the two repositories cloned under `~/dev/`, and a local Ollama that has `mxbai-embed-large`:

```bash
python3 build_sandboxes.py        # corpora in sbx/, run copies at neutral paths w/v1..v4/<repo>
for r in llm-cache-proxy llm-memory-pyramid; do for c in code docs; do
  EMB_MODEL=mxbai-embed-large python3 build_index.py sbx/$r/$c sbx/$r/$c.mxbai-embed-large.idx.sqlite
done; done
EMB_MODEL=mxbai-embed-large python3 retrieval_eval.py   # hit@5 per retriever
python3 run_matrix.py --reps 2 --jobs 6 --only A,B,C,D,E,G,H,I
python3 gen_cost.py               # what the assets cost to create
python3 analyze.py                # the tables above
```

`results.jsonl` holds every run's answer, token counts, cost, turns and tool calls.
