---
title: "A third axis for repo dossiers: every command, statically read"
description: "crawl-repo-to-llms gets an operational axis — every entrypoint's options, env vars, and outputs, read from the actual parser code, never from --help. Run for real against a live, twice-weekly automation pipeline: 6 entrypoints, 4 CLI flags, 19 env vars, 9 HTTP routes, 13 quick answers, and three doc/code contradictions caught along the way."
date: "2026-09-04"
tags: [repo-dossier, executables, cli, crawl-repo-to-llms]
sources:
  - skills/crawl-repo-to-llms/SKILL.md
---

<!-- verified-as-of: 2026-09-04 · repo identity and customer specifics anonymized; every
     count below is real, taken from an actual run against a live private repository -->

## Problem

A repo dossier answers "what does this file do" and "what does this codebase mean." It does
not answer "how do I start the server," and that gap shows up constantly: an agent (or a
person six weeks later) reads a per-file card explaining that `api/server.py` is a loopback
HTTP control surface, and still has to go find the one environment variable that makes it
refuse to start, or the exact flag that turns a dry run into a live post.

The knowledge axis (prose, condensed) and the artifact axis (files, cards, an importance
rubric) don't cover this, because the answer isn't in the file's *purpose* — it's in its
*parser*. `crawl-repo-to-llms` v1.2.0 adds a third axis for exactly that: every entrypoint a
repository actually runs, carded with its options, environment variables, config consumed,
and outputs, built by statically reading the argparse/route/Makefile source — never by
running `--help`, which the skill's read-only guard forbids outright.

## Inputs

Run against a live, unattended automation pipeline that posts to a real third-party SaaS
board twice a week — identity anonymized here, but the shape is ordinary: a Python 3.11+
repo, 85 tracked files, a `pyproject.toml`-installed console script, a stdlib HTTP server, a
Makefile, and a vendored standalone script. This was the second pass over the repo — the
first (knowledge + artifact axes) had already run and produced a dossier; this pass added
only the new operational axis on top of it.

## Commands

```bash
# the skill's own status-probe pattern, used verbatim as one of its own Guard-3 exceptions
# (a read-only query against a store the target already built) — this is the kind of
# thing a "how do I ___" quick-answer resolves to, not a command the skill itself runs
<INDEX_ROOT_VAR>=<per-target-index-dir> python3 <indexer-script>.py status --target <id>

# what the skill produces is a file, not a command — the entrypoint enumeration itself is
# a static read of:
#   pyproject.toml [project.scripts]      → the CLI's registration
#   <cli-module>.py's argparse tree       → every subcommand, flag, default
#   <server>.py's route table             → every HTTP method + path
#   Makefile                              → every target and what it wraps
#   scripts/*.sh                          → prerequisite/precondition checks
```

No `--help` was run against anything. The options table below traces to specific
`add_argument()` / route-registration call sites read directly from source.

## Outputs

One new file, `llms-executable.txt`, alongside the six from the first pass. Counted, not
estimated:

| What | Count |
|---|---|
| Entrypoints found | 6 (a CLI, an HTTP server, a standalone script, a Makefile, a shell script, a browser-UI popup) |
| CLI subcommands | 8, on the one console script |
| CLI flags (true options, excluding positional args) | 4 |
| Distinct environment variables read across every entrypoint | 19 |
| HTTP routes | 9 |
| Makefile targets | 12 |
| Quick-answer entries built | 13 |
| Quick-answer intents with no matching command (omitted, not invented) | 4 — `build`, `deploy`, `migrate`, `seed` (this repo has none of the three: nothing to compile, no deploy target, no database) |

The quick-answers index is the part built for the question this post opened with. It maps a
fixed intent vocabulary — start/serve, run, test, lint, build, deploy, migrate, clean,
watch — to the exact card that satisfies it, and only when one actually exists:

```
start the server        → <API_TOKEN_VAR>=$(openssl rand -hex 16) python3 api/server.py
kick off the process    → <cli> run <target> (dry run is the default; a live flag posts)
run everything CI runs  → make check
tail a running job's log → <cli> logs <target> -n 50
```

(Command names above are the real shape, target/token names anonymized.) Every row traces
back to a specific entrypoint card in the same file — an intent with no card behind it is
left out of the table entirely, per the same anti-fabrication rule that governs every other
axis of this skill's output.

## What the audit found

The same crawl that built the executable inventory also re-confirmed three findings from the
first pass, because Phase 4e's static reads cross the same source files the earlier per-file
cards did:

- One entrypoint's own module docstring stated it "never calls" a third-party API directly —
  untrue; one of its subcommands does exactly that, over the network, using a token from the
  environment. The docstring was written before that subcommand existed and never updated.
- A test-strategy doc named 7 test classes as the suite's coverage; the actual test file
  defines 24. Counted by `grep -c '^class Test'`, not estimated — a 17-class gap between
  what the docs claim and what the code has.
- A "legacy, superseded" README described one archived file as "a one-line stub that was
  never written." Reading the file found 222 lines of a fully detailed, working
  configuration — the README's claim about that specific file was simply wrong.

None of these are found by argument-parsing alone; they surface because the crawl reads
source and docs side by side and refuses to let a doc's claim stand in for what the code
actually does. The lesson generalizes: an operational axis built from source is also, for
free, a doc-drift detector — a documented flag that doesn't exist in the parser, or a parser
flag with no documentation anywhere, is the same class of finding as these three.

## Lessons

- **Static, not executed, is the load-bearing constraint.** The temptation to just run
  `--help` and parse its output is strong — it would be far less code. It also cannot be done
  under a read-only guard, and it would silently fail on any entrypoint that needs
  environment setup before it can even print help (this repo's HTTP server refuses to start
  at all without a token set — `--help` never returns for it).
- **A quick-answers index is only trustworthy if empty rows are allowed.** The four omitted
  intents (build/deploy/migrate/seed) were a deliberate design decision, not a gap: inventing
  a plausible-sounding `make deploy` for a repo that has none would be a worse failure mode
  than an honest "no matching command."
- **The operational axis doubles as a drift detector for free.** All three doc/code
  contradictions above were found by the same pass that built the command inventory, because
  reading a parser's actual flags and a doc's claimed flags side by side is nearly the same
  operation as reading a docstring's claim and a function's actual network calls side by
  side.
- **Counting beats estimating, even for a private repo you can't cite by name.** Every number
  in the outputs table came from grepping or reading the actual source, then double-checked
  by a second, independent count (env-var tokens extracted by regex, cross-checked against
  the by-hand card list) before either number was allowed to disagree with the other silently.

## Reproduce

The skill itself — the full Phase 4e specification, the card grammar, the guard about never
running `--help`, and the quick-answers construction rule — is `skills/crawl-repo-to-llms/SKILL.md`
in this repository. Point it at any repository with `/crawl-repo2llms <path>` and it emits
`llms-executable.txt` alongside the rest of the dossier family; `--no-exec-inventory` skips
this axis on a monorepo with too many scripts to be worth cataloguing individually.
