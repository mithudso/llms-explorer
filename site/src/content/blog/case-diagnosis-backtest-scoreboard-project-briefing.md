---
title: "TSE Strategy Backtest Scoreboard — Project Briefing"
description: "A first-person briefing on a git-backed scoreboard that backtests case-diagnosis strategies blind against resolved support cases, with how to read its scores and add a strategy."
date: "2026-10-10"
order: 6
---

**Python 3.11 · git-backed evaluation ledger · Internal Tool**

This briefing is self-contained and written for several audiences. Each section header names its primary one: leadership sections use plain language, and developer and reviewer sections use precise technical terms. Every command, path, count, and code reference comes from the repo's files. I don't name the customers behind the case data. I call the one behind the 244-case dataset "Customer A", drop customer prefixes from panel IDs, and write customer-named scripts and variables as `<customer>` placeholders. The repo is internal, so the paths below are for orientation, not links.

---

## 1. Executive Summary *(leadership)*

The TSE (Technical Services Engineer) Strategy Backtest Scoreboard answers one question: **which way of diagnosing a support case actually predicts the right root cause?** I built it as a TAM (Technical Account Manager). It is a git-backed ledger that backtests competing **diagnosis strategies** (each a prompt plus its knowledge sources) *blind* against frozen panels, also called sample sets, of already-resolved MongoDB/Atlas support cases. It grades every prediction against ground-truth resolutions with a separate versioned judge and rolls the scores into a leaderboard.

Three rules keep the comparison honest. A strategy sees only the case's opening prompt (title plus first customer message), never the resolution. A methodology-blind judge that the strategy never influences scores the predictions. And once a run references an artifact, that artifact is pinned by content hash and frozen, so scores cannot be quietly edited after the fact. A continuous-integration (CI) gate re-validates schemas, immutability, and freshness on every pull request and every push to `main`.

A "run" produces a folder of `predictions.json`, `grades.json`, and a deterministic `scorecard.json`; all scorecards roll up into `scoreboard/leaderboard.{json,md}`, grouped so only comparable runs (same panel, same ground-truth version) are ever ranked together.

As of the leaderboard generated on 2026-05-29, the ledger scores 4 strategies across 2 leaderboard panels drawn from a 244-case dataset of resolved cases from Customer A, with a third panel of 1,000 cases from a second customer evaluated off-ledger. One caveat governs every number below: the current ground truth is **plausibility-grade**, not validated, so read scores accordingly (see §9).

### Standings on 2026-05-29 *(all)*

Full corpus, panel `blind-244-v1` (calibrated rubric), ground truth `r1-autoclose-fallback`:

| Rank | Strategy | n | Defensibility | Acc / gradable | Raw acc |
| ----: | :---- | ----: | ----: | ----: | ----: |
| 1 | Pure MongoDB skill knowledge | 244 | 100% | 90.3% | 72.5% |
| 2 | Documented flowchart corpus | 244 | 86% | 63.5% | 51.0% |
| 3 | A colleague's Customer A flowchart bundle | 244 | 37% | 26.3% | 21.1% |

Here `n` is the case count, and gradable cases are the ones the judge could check. Defensibility is the share of gradable answers that were not flatly wrong. Accuracy on gradable cases gives Correct 1.0 and Partial 0.5 over the gradable cases, and raw accuracy divides the same total by all `n`, so abstaining costs points. Rows sort by accuracy on gradable cases, then defensibility, then lower abstention rate (`harness/leaderboard.py`).

The strategies differ in what they may consult. Pure skill knowledge uses only the `mongodb-*` expert skills. The documented flowchart corpus uses the canonical MongoDB troubleshooting flowcharts. The customer bundle is a colleague's set of incident-remediation flowcharts written for Customer A. The fourth strategy, a hybrid cascade that defers to the most explainable component, has a ledger run only on the 20-case panel.

On the stricter 20-case seed panel (`blind-20-v1`) the documented flowchart corpus leads instead. I attribute that largely to rubric calibration, not a strategy regression (see §9). Source: `scoreboard/leaderboard.md`.

---

## 2. Key Features *(all)*

- **Blind, separated-agent backtest.** Prediction agents see only `case.initial_prompt`. A separate, versioned, methodology-blind judge scores against resolutions the predictor never reads.
- **Parallel multi-agent fan-out.** Competing methodologies are dispatched as parallel agents in one pass, in strict predict → grade → synthesize order (`docs/evaluation-prompt-parallel.md`).
- **Versioned hybrid grading.** Four tiers (Correct 1.0 / Partial 0.5 / Wrong 0.0 / Unverifiable = excluded), an honesty downgrade for autoclose-fallback resolutions (see §9), and an optional human `override` that wins in scoring (`judges/blind-diagnosis-judge-v1/`, `schemas/grade.schema.json`).
- **Deterministic scorecard math.** `defensibility = 1 − Wrong/gradable`, `accuracy_on_gradable = Σweight/gradable`, `raw_accuracy = Σweight/n`, `abstention_rate = U/n` (`harness/score.py`).
- **Efficiency scored alongside accuracy.** The scorecard records compute time, flowchart navigation cost, on-disk strategy size, and human-follow time at 250 words per minute over the decision chain. No run records navigation cost yet.
- **Immutability via content hash and CI gate.** Once a run references an artifact, its `content_hash` is pinned; `harness/validate.py` recomputes and fails on drift.
- **Additive contribution model.** `harness/new_strategy.py` scaffolds a new strategy folder and refuses to overwrite. Improving a method means a new immutable `-v2` folder, never editing a scored one.
- **Provenance seeder and ground-truth ingester.** `harness/seed_<customer>.py` turns a one-time Customer A export into artifacts. `harness/ingest_resolutions.py` appends a new ground-truth version (for example `r2`).
- **Deterministic hybrid composition.** `harness/build_cascade.py` composes the defer-to-explainable `hybrid-cascade-v1` from component runs.
- **Generated leaderboard, grouped by comparable scope.** `harness/leaderboard.py` regenerates `scoreboard/leaderboard.{json,md}` and never mixes panels or ground-truth versions.
- **Optional `/dr` deep-research harness.** `dr-harness/` orchestrates wave-based research to *build* a strategy's knowledge corpus (worklist → runner prompts → merge → coverage report).
- **Contract-first artifacts.** Nine JSON Schema files (`schemas/`) define every artifact, and `jsonschema` validation is the repo's enforced API.

---

## 3. Problems Solved *(leadership + team)*

| Pain point | How the scoreboard addresses it |
| :---- | :---- |
| **"Which diagnosis method is best?" was anecdotal** | Frozen panels + deterministic scorecards + a ranked leaderboard make it measurable |
| **A methodology grading its own exam** | The judge is a separate, versioned, methodology-blind artifact; predictor ≠ judge |
| **Ground-truth leakage into a "blind" test** | Strategies see only `initial_prompt`; resolutions live in a separate file the predictor never opens |
| **Post-hoc tampering to inflate a score** | Content-hash pinning plus a `validate.py` immutability pass reject edits to tested artifacts |
| **Stale or hand-edited scoreboards** | Every scorecard and the leaderboard are generated; CI fails if validation regenerates a tracked file |
| **Non-comparable scores** | Each run pins strategy + panel + judge + ground truth by hash; only same-panel, same-ground-truth runs are ranked together |
| **Accuracy hiding cost** | An efficiency block scores compute, navigation cost, size, and human-follow time |
| **Weak ground truth read as "accuracy"** | A `ground_truth_caveat` is stamped on every scorecard; scores are framed as plausibility until `r2` |
| **Improving a method corrupting old results** | A new version is a new immutable folder; lineage tracked via `forked_from` |
| **Adding a contributor's method touching others' files** | Contribution is purely additive — new folders only; the scaffolder refuses to overwrite |

---

## 4. Scope of Work *(leadership + reviewers)*

I designed and built this project as an internal evaluation tool. It is proprietary and confidential to MongoDB, Inc. (`LICENSE`, which also notes that the licensing posture is not final).

| Component | Path | Approx. lines |
| :---- | :---- | :---- |
| Core harness (11 Python scripts) | `harness/*.py` | ~1,610 |
| `/dr` deep-research runner (8 scripts) | `dr-harness/*.py` | ~650 |
| Artifact contracts | `schemas/*.json` (9 files) | ~360 |
| Scorer tests | `tests/test_score.py` | ~110 |
| Documentation suite | `docs/*.md` (17 files) | ~1,440 |
| Post-run analyses | `evaluations/*.md` (6 files: 5 analyses and an index) | ~590 |

Line counts are raw file lines from `wc -l`, intended as scope indicators rather than source lines of code.

**Engineering quality markers:**

- **CI pipeline.** A single workflow (`.github/workflows/validate.yml`, Python 3.11) runs the scorer tests (`python tests/test_score.py`), then `python harness/validate.py` (schema + immutability + integrity + freshness), and **fails if validation regenerated any tracked file** — that is, if a contributor forgot to commit the rebuilt leaderboard. Enforcement needs GitHub Actions enabled on the repo, which the repo's known-issues list flags as something to confirm (`docs/known-issues.md`).
- **Tests.** 8 scorer-math test functions in `tests/test_score.py`, covering metric computation, override precedence, decision-chain word counts, and efficiency signals. Scope is deliberately the scorer only — the harness has no network or runtime to integration-test.
- **Contract-first.** 9 JSON Schemas define every artifact; nothing enters the ledger without validating against them.
- **Documentation suite.** 17 docs (~1,440 lines), per-directory READMEs for every data folder, a runbook (`docs/runbooks/rebuild-scoreboard.md`), and machine-readable codebase maps.
- **Reproducibility.** Canonical content hashing and 2-space-indent JSON make every artifact byte-stable and every run re-scorable from its pinned inputs.

---

## 5. Data & Integrity Posture *(reviewers + leadership)*

**Summary for reviewers**: Everything is local file I/O inside the git tree. The scored core makes zero in-process external calls, reads no secrets, and never executes case data. Integrity comes from content hashing and a CI gate, not a server.

### Customer-data handling

The cases are real customer support cases (a Customer A export taken through TS Tools). The rule is to treat every case as customer-confidential and to store only the blind inputs and the resolutions grading requires — no fuller exports, PII, or internal URLs beyond that (`docs/SECURITY.md`).

### Blinding

Two-axis separation is built into the data model: blind inputs (`cases.json`) and ground truth (`resolutions-r1.json`) live in different files. During grading, predictions are pooled, shuffled, and stripped of strategy identity into an anonymized queue keyed by an opaque `record_id`; identity is reattached only after scoring. This blinding is procedural, specified in `docs/evaluation-prompt-parallel.md`; CI proves immutability and re-scoring, not blindness. The repo's known-issues list also notes that seed grades were produced per strategy, before the judge became a separate artifact, so a fully independent grader would be more rigorous.

### Secrets and network

The codebase reads no secrets — the only environment variable is `<CUSTOMER>_SRC`, a local filesystem path used solely by the seeder. The scored ledger makes **zero in-process external calls**: no network, no database, no Model Context Protocol (MCP) calls. The one in-repo subprocess spawn is `dr_orchestrate.py` calling its sibling `dr_merge.py` (Python → Python, no network). LLM and web access — for the `/dr` knowledge build and for producing future ground truth — happen in operator-run tools outside this codebase (`docs/external-calls.md`).

### Integrity model

The repo *is* the database. There is no server and no external state; integrity comes from canonical content hashes plus the `validate.py` CI gate, which is the read-back equivalent. The full STRIDE threat-model table is in `docs/SECURITY.md`.

---

## 6. Architecture Overview *(reviewers + team)*

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

`common.py` (canonical hashing + JSON I/O), `new_strategy.py` (scaffold), `freeze.py` (write content hashes), `pin_runs.py` (stamp a run with its input hashes), `score.py` (grades → scorecard), `leaderboard.py` (runs → leaderboard), `validate.py` (the CI gate), and `seed_<customer>.py` (provenance seed). The domain-model table and trade-offs are in `docs/architecture.md`.

---

## 7. Installation & Quick Start *(new users)*

### Prerequisites

- **Python 3.11** (`.python-version`; CI pins 3.11)
- **Node.js ≥ 22** — only for the optional `/dr` deep-research runner (`.nvmrc`, `package.json` engines)
- Git

### Install (core)

```shell
pip install -r requirements.txt      # jsonschema>=4.26.0 — the only core dependency
```

### Reproduce the seed scoreboard from a local Customer A export

```shell
<CUSTOMER>_SRC=/path/to/customer-a-export python harness/seed_<customer>.py
python harness/freeze.py && python harness/pin_runs.py
python harness/score.py && python harness/leaderboard.py
python harness/validate.py            # the exact CI gate
```

The only configuration needed is `<CUSTOMER>_SRC`, a placeholder for the customer-named variable that holds a local path used solely by the seeder. No secrets or API keys are required for the core. Detail in `docs/INSTALLATION.md` and `docs/DEVELOPMENT.md`.

---

## 8. Usage Guide *(team + new users)*

### Add your own strategy and score it

Contributing is additive: a new strategy is a new folder, and nobody edits another contributor's files (`CONTRIBUTING.md`).

1. Scaffold the strategy. The scaffolder refuses to overwrite an existing one.

   ```shell
   python harness/new_strategy.py my-method-v1 --title "My method" --kind hybrid
   ```

2. Write the methodology in `strategies/my-method-v1/prompt.md` and list its sources under `knowledge_sources` in `strategy.json`.
3. Produce blind predictions for a sample set before reading any ground truth. Save them as `predictions.json` in a new `runs/<run_id>/` folder (schema: `schemas/prediction.schema.json`).
4. Grade the predictions with a judge (an LLM draft plus an optional human override) into `grades.json`, then author `run.json` (schemas: `schemas/grade.schema.json`, `schemas/run.schema.json`).
5. Freeze the strategy, pin and score the run, rebuild the leaderboard, and validate:

   ```shell
   python harness/freeze.py strategies/my-method-v1
   python harness/pin_runs.py runs/<run_id>
   python harness/score.py runs/<run_id>
   python harness/leaderboard.py
   python harness/validate.py            # the exact CI gate
   ```

6. Open a pull request. CI repeats `validate.py` and fails on any schema, immutability, integrity, or freshness violation.

To improve a scored strategy, fork it into a new `-v2` folder instead of editing it. The scaffolder's `--forked-from` flag records the lineage.

---

## 9. Reading the Scores *(all)*

The standings rank strategies by plausibility, not verified accuracy. Two things explain why.

**Weak ground truth.** The Customer A dataset's resolutions, version `r1-autoclose-fallback`, include only a handful of cases with a substantive engineer narrative: the dataset record counts 12 strong resolutions, while the repo's docs treat about 8 as substantive. Another 188 are autoclose fallbacks: the stored "resolution" echoes the customer's first message instead of an engineer's finding, so a prediction that matches one has mostly matched the customer's own words. The judge's honesty downgrade grades such a case Unverifiable unless the prediction can be tested against substantive content (`judges/blind-diagnosis-judge-v1/rubric.md`). The remaining 44 are unavailable and cannot be graded. On the roughly 8 strong cases the ranking holds but the margins shrink, and that is too few for high confidence (`docs/ground-truth-workflow.md`).

**Rubric calibration.** The panels were graded under different rubrics. The 20-case seed panel kept its original grades, strict for skill knowledge and lenient for the flowchart corpus, and the skill strategy was Unverifiable on 15 of 20 cases. The 244-case panel re-issued every phase's grades under one calibrated threshold, and the same strategy was Unverifiable on 48 of 244. That is one reason the panels rank strategies differently, and why the leaderboard never mixes them (`docs/methodology.md`). The repo's README adds that the calibrated rubric favors the skill strategy's prompt-mirroring predictions.

The fix is a new resolution version, `r2`, built from engineer comment threads, with each strategy's existing predictions re-graded against it. The leaderboard would then show `r1` and `r2` as separate comparable groups, and a strategy that scores well on `r1` but poorly on `r2` was matching customer phrasing rather than diagnosing. As of this writing the repo has no `r2`: `datasets/<customer>/` holds a single resolutions file, `resolutions-r1.json`. The ingestion tooling (`harness/ingest_resolutions.py`) is ready, and the blocker, per `docs/known-issues.md`, is that re-ingesting the real engineer comment threads needs an internal case-tracker worker to be online.
