# TSE Strategy Backtest Scoreboard — Project Briefing

**Python 3.11 · git-backed evaluation ledger · Internal Tool**

This document is a self-contained briefing for multiple audiences. Each section header marks its primary audience. Plain language is used in leadership-facing sections; precise technical terminology in developer- and reviewer-facing sections. All facts — commands, paths, counts, code references — are derived from actual repo files.

---

## 1\. Executive Summary *(leadership)*

The TSE Strategy Backtest Scoreboard answers one question rigorously: **which way of diagnosing a support case actually predicts the right root cause?** Built by \[REDACTED\] (TAM), it is a git-backed ledger that backtests competing **diagnosis strategies** — each a prompt plus its knowledge sources — *blind* against frozen panels of already-resolved MongoDB/Atlas support cases, grades every prediction against ground-truth resolutions with a separate versioned judge, and rolls the scores into a leaderboard.

The discipline is what makes the numbers trustworthy: a strategy sees only the case's opening prompt (title \+ first customer message), never the resolution; a **methodology-blind grader** that the strategy never influences scores the predictions; and once a run references an artifact, that artifact is pinned by content hash and frozen, so scores cannot be quietly edited after the fact. A CI gate re-validates schemas, immutability, and freshness on every push.

A "run" produces a folder of `predictions.json`, `grades.json`, and a deterministic `scorecard.json`; all scorecards roll up into `scoreboard/leaderboard.{json,md}`, grouped so only comparable runs (same panel, same ground-truth version) are ever ranked together.

Today the ledger scores **4 strategies** across **2 leaderboard panels** drawn from a **244-case Okta dataset**, with a third 1,000-case panel evaluated off-ledger. One caveat governs every number below: the current ground truth is **plausibility-grade**, not validated — read scores accordingly (see §11).

### Current standings *(all)*

Full corpus, panel `okta-blind-244-v1` (calibrated rubric), ground truth `r1-autoclose-fallback`:

| Rank | Strategy | n | Defensibility | Acc / gradable | Raw acc |
| ----: | :---- | ----: | ----: | ----: | ----: |
| 1 | Pure MongoDB skill knowledge | 244 | 100% | 90.3% | 72.5% |
| 2 | Documented flowchart corpus | 244 | 86% | 63.5% | 51.0% |
| 3 | Chandler's Okta flowchart bundle | 244 | 37% | 26.3% | 21.1% |

On the stricter 20-case seed panel (`okta-blind-20-v1`) the documented flowchart corpus leads instead — a rubric-calibration difference, not a strategy regression (see §11). Source: [`scoreboard/leaderboard.md`](http://scoreboard/leaderboard.md).

---

## 2\. Key Features *(all)*

- **Blind, separated-agent backtest** — prediction agents see only `case.initial_prompt`; a separate, versioned, methodology-blind grader scores against resolutions the predictor never reads.  
- **Parallel multi-agent fan-out** — competing methodologies are dispatched as parallel agents in one pass, in strict predict → grade → synthesize order (`docs/evaluation-prompt-parallel.md`).  
- **Versioned deterministic grading** — four tiers (Correct 1.0 / Partial 0.5 / Wrong 0.0 / Unverifiable \= excluded), with an honesty downgrade for autoclose-fallback resolutions and an optional human `override` (`judges/blind-diagnosis-judge-v1/judge.json`).  
- **Deterministic scorecard math** — `defensibility = 1 − Wrong/gradable`, `accuracy_on_gradable = Σweight/gradable`, `raw_accuracy = Σweight/n`, `abstention_rate = U/n` (`harness/score.py`).  
- **Efficiency scored alongside accuracy** — compute time, flowchart navigation cost, on-disk strategy size, and human-follow time at 250 wpm over the decision chain.  
- **Immutability via content hash \+ CI gate** — once a run references an artifact, its `content_hash` is pinned; `harness/validate.py` recomputes and fails on drift.  
- **Additive contribution model** — `harness/new_strategy.py` scaffolds a new strategy folder and refuses to overwrite; improving a method means a new immutable `-v2` folder, never editing a scored one.  
- **Provenance seeder and ground-truth ingester** — `harness/seed_okta.py` turns a one-time Okta export into artifacts; `harness/ingest_resolutions.py` appends a new ground-truth version (e.g. `r2`).  
- **Deterministic hybrid composition** — `harness/build_cascade.py` composes the defer-to-explainable `hybrid-cascade-v1` from component runs.  
- **Generated leaderboard, grouped by comparable scope** — `harness/leaderboard.py` regenerates `scoreboard/leaderboard.{json,md}` and never mixes panels or ground-truth versions.  
- **Optional `/dr` deep-research harness** — `dr-harness/` orchestrates wave-based research to *build* a strategy's knowledge corpus (worklist → runner prompts → merge → coverage report).  
- **Contract-first artifacts** — 9 JSON Schema files (`schemas/`) define every artifact; `jsonschema` validation is the repo's enforced API.

---

## 3\. Problems Solved *(leadership \+ team)*

| Pain point | How the scoreboard addresses it |
| :---- | :---- |
| **"Which diagnosis method is best?" was anecdotal** | Frozen panels \+ deterministic scorecards \+ a ranked leaderboard make it measurable |
| **A methodology grading its own exam** | The judge is a separate, versioned, methodology-blind artifact; predictor ≠ grader |
| **Ground-truth leakage into a "blind" test** | Strategies see only `initial_prompt`; resolutions live in a separate file the predictor never opens |
| **Post-hoc tampering to inflate a score** | Content-hash pinning plus a `validate.py` immutability pass reject edits to tested artifacts |
| **Stale or hand-edited scoreboards** | Every scorecard and the leaderboard are generated; CI fails if validation regenerates a tracked file |
| **Non-comparable scores** | Each run pins strategy \+ panel \+ judge \+ ground truth by hash; only same-panel, same-ground-truth runs are ranked together |
| **Accuracy hiding cost** | An efficiency block scores compute, navigation cost, size, and human-follow time |
| **Weak ground truth read as "accuracy"** | A `ground_truth_caveat` is stamped on every scorecard; scores are framed as plausibility until `r2` |
| **Improving a method corrupting old results** | A new version is a new immutable folder; lineage tracked via `forked_from` |
| **Adding a contributor's method touching others' files** | Contribution is purely additive — new folders only; the scaffolder refuses to overwrite |

---

## 4\. Scope of Work *(leadership \+ reviewers)*

This project was designed and built by **\[REDACTED\] (TAM)** as an internal evaluation tool. It is proprietary and confidential to MongoDB, Inc. (`LICENSE`).

| Component | Path | Approx. lines |
| :---- | :---- | :---- |
| Core harness (11 Python scripts) | `harness/*.py` | \~1,610 |
| `/dr` deep-research runner (8 scripts) | `dr-harness/*.py` | \~650 |
| Artifact contracts | `schemas/*.json` (9 files) | \~360 |
| Scorer tests | `tests/test_score.py` | \~110 |
| Documentation suite | `docs/*.md` (16 files) | \~1,440 |
| Post-run analyses | `evaluations/*.md` (5 files) | \~590 |

Line counts are raw file lines from `wc -l`, intended as scope indicators rather than SLOC.

**Engineering quality markers:**

- **CI pipeline.** A single workflow (`.github/workflows/validate.yml`, Python 3.11) runs the scorer tests (`python tests/test_score.py`), then `python harness/validate.py` (schema \+ immutability \+ integrity \+ freshness), and **fails if validation regenerated any tracked file** — i.e., if a contributor forgot to commit the rebuilt leaderboard.  
- **Tests.** 8 scorer-math test functions in `tests/test_score.py`, covering metric computation, override precedence, decision-chain word counts, and efficiency signals. Scope is deliberately the scorer only — the harness has no network or runtime to integration-test.  
- **Contract-first.** 9 JSON Schemas define every artifact; nothing enters the ledger without validating against them.  
- **Documentation suite.** 16 docs (\~1,440 lines), per-directory READMEs for every data folder, a runbook (`docs/runbooks/rebuild-scoreboard.md`), and machine-readable codebase maps.  
- **Reproducibility.** Canonical content hashing and 2-space-indent JSON make every artifact byte-stable and every run re-derivable from its pinned inputs.

---

## 5\. Data & Integrity Posture *(reviewers \+ leadership)*

**Summary for reviewers**: Everything is local file I/O inside the git tree. The scored core makes zero in-process external calls, reads no secrets, and never executes case data. Integrity comes from content hashing and a CI gate, not a server.

### Customer-data handling

The cases are real customer support cases (Okta, Inc. export via TS Tools). The rule is to treat every case as customer-confidential and to store only the blind inputs and the resolutions grading requires — no fuller exports, PII, or internal URLs beyond that (`docs/SECURITY.md`).

### Blinding

Two-axis separation is built into the data model: blind inputs (`cases.json`) and ground truth (`resolutions-r1.json`) live in different files. During grading, predictions are pooled, shuffled, and stripped of strategy identity into an anonymized queue keyed by an opaque `record_id`; identity is reattached only after scoring.

### Secrets and network

The codebase reads no secrets — the only environment variable is `OKTA_SRC`, a local filesystem path used solely by the seeder. The scored ledger makes **zero in-process external calls**: no network, no database, no MCP invocations. The one in-repo subprocess spawn is `dr_orchestrate.py` calling its sibling `dr_merge.py` (Python → Python, no network). LLM and web access — for the `/dr` knowledge build and for producing future ground truth — happen in operator-run tools outside this codebase (`docs/external-calls.md`).

### Integrity model

The repo *is* the database. There is no server and no external state; integrity comes from canonical content hashes plus the `validate.py` CI gate, which is the read-back equivalent. The full STRIDE table is in [`docs/SECURITY.md`](http://docs/SECURITY.md).

---

## 6\. Architecture Overview *(reviewers \+ team)*

The scoreboard is a model-agnostic ledger: it ingests and verifies prediction and grade artifacts but does not ship the agent runtime that produces predictions.

### End-to-end run flow

```
datasets/<id>/cases.json        (blind input: title + first message only)
        │
        ▼
strategies/<id>/                (prompt.md + strategy.json + knowledge_sources)
        │   produces predictions for a frozen sample set
        ▼
runs/<run_id>/predictions.json
        │
        ▼
judges/<id>/                    (versioned, methodology-blind)
        │   grades vs resolutions-rN.json  → grades.json (+ optional human override)
        ▼
harness/score.py                (deterministic) → runs/<run_id>/scorecard.json
        │
        ▼
harness/leaderboard.py          → scoreboard/leaderboard.{json,md}
                                  (grouped by sample set + ground-truth version)
```

### Run identity

`run_id = <strategy_id>__<sample_set_id>__<judge_id>__<UTC timestamp>`. Every input is pinned by content hash, so a run is reproducible — and comparable to another run *only if* both share the same sample set **and** the same resolution version.

### Storage

Plain JSON files in the git working tree — no SQLite, MongoDB, or server. JSON is written with 2-space indent and a trailing newline (`harness/common.py`).

### Key modules

`common.py` (canonical hashing \+ JSON I/O), `new_strategy.py` (scaffold), `freeze.py` (write content hashes), `pin_runs.py` (stamp a run with its input hashes), `score.py` (grades → scorecard), `leaderboard.py` (runs → leaderboard), `validate.py` (the CI gate), and `seed_okta.py` (provenance seed). The domain-model table and trade-offs are in [`docs/architecture.md`](http://docs/architecture.md).

---

## 7\. Installation & Quick Start *(new users)*

### Prerequisites

- **Python 3.11** (`.python-version`; CI pins 3.11)  
- **Node.js ≥ 22** — only for the optional `/dr` deep-research runner (`.nvmrc`, `package.json` engines)  
- Git

### Install (core)

```shell
pip install -r requirements.txt      # jsonschema>=4.26.0 — the only core dependency
```

### Reproduce the seed scoreboard from a local Okta export

```shell
OKTA_SRC=/path/to/customer-files/Okta python harness/seed_okta.py
python harness/freeze.py && python harness/pin_runs.py
python harness/score.py && python harness/leaderboard.py
python harness/validate.py            # the exact CI gate
```

The only configuration needed is `OKTA_SRC` (a local path used solely by the seeder). No secrets or API keys are required for the core. Detail in [`docs/INSTALLATION.md`](http://docs/INSTALLATION.md) and [`docs/DEVELOPMENT.md`](http://docs/DEVELOPMENT.md).

---

## 8\. Usage Guide *(team \+ new users)*

### Add your own strategy and score it

```shell