---
title: "ZEC ensemble hypotheses and their evidence limits"
description: "ZEC ensemble hypotheses and their evidence limits. An edited historical research report with its original evidence limits retained."
date: "2026-11-28"
category: research
tags: [research, historical-study]
evidenceStatus: unverified
evidenceNote: "Editorial review does not independently reproduce the original experiment. Results retain the source study’s dates, assumptions and limitations."
---

# ZEC ensemble study and paper forward tests

Study and installation snapshot: **2026-11-10–11**. Service status, first-candle waiting and package versions below are author-recorded historical observations. This publication did not poll or restart the service and reports no later prospective performance.

Status: historical study complete; ten paper accounts started. The Oracle page publishes the frozen top configuration and may use historical warmup for a current reference independently of paper activation.

The owner requested ZEC backtests at **1m and 1h**, guided by
`Strategy Ensembles.md`, more historical data where available,
ten selected paper forward tests, and Oracle publication of the top configuration.

## Research contract

The guide is a source of hypotheses. Its headline Sharpe of 6.04 comes from 848
hourly candles and 11 trades. The guide does not provide a reproducible dataset
fingerprint or exact complete configuration, so this study does not treat that
number as a validated baseline or an expected result.

The market is Binance spot **ZEC/USDT**. USDT is not USD. The study does not model
short selling or leverage. Initial capital, assumed fees, slippage, windows,
configuration IDs, source hashes, and code hashes are recorded with each run.
No synthetic candles repair missing history. Accounts restart across data gaps.

The primary windows are fixed before ranking: latest 180 days for 1m and up to
four years for 1h. The oldest 40% is training data, the next 40% supplies three
chronological validation blocks, and the newest 20% is reserved for the final
historical test in this run. These historical dates may have appeared in earlier
research; they are not claimed to be globally unseen.

Selection uses validation evidence only. The selected configurations are frozen
before opening the reserved test. Test results never change their rank. Older
history and doubled costs provide separate stress tests of the frozen selection.
Cash and buy-and-hold provide benchmarks. Zero-trade and insufficient candidates
remain visible and cannot become selected winners.

A large search creates selection bias. The ten selected configurations are
experimental paper candidates, not proof of a profitable edge. Their prospective
paper evidence starts only when the forward service starts observing new closed
candles. Historical warmup never creates prospective profit.

## Artifacts

Large datasets, original ZIP archives, publisher checksums, the source guide,
raw API receipts, configuration/result ledgers and runtime receipts live outside Git:

`RESEARCH_ARCHIVE/zec-ensembles-20261110`

The data fetcher uses public Binance spot archive files and the read-only public
market-data API. It verifies SHA-256 and ZIP CRC, normalizes the archive's
millisecond/microsecond timestamp transition, rejects conflicting duplicates,
and records gaps and unavailable archive files explicitly.

## Downloaded history

The acquisition contains **3,606,401 native 1m candles** and **60,114 native 1h
candles**, from 2020-01-01 through 2026-11-11 01:26UTC (last hourly open 00:00UTC).
It preserves 182 verified archives and observed API tail responses. Both intervals
have 15 documented gaps: 2,326 missing minute bars and 31 missing hourly bars.
The longest continuous span begins 2023-03-24 14:00UTC and contains 1,911,567
minutes / 31,859 hours. Source hashes and a separate validation receipt bind the
CSV files to the final data validator.

The executable catalog has **1,652 configurations**, 826 per interval. It includes
60 canonical single-strategy baselines, 38 parameter sensitivities, 840 pair/trio
voting cases, 60 family committees, 28 turnover deadbands, 42 persistence cases,
14 training-correlation weightings, 180 hierarchical permission cases, 300 gated
soft votes, and 90 trend/reversion routing cases. Three leverage wrappers and
the conditional trigger policy are outside this spot exposure experiment.

## Hypotheses and reproducibility

See `research/ZEC-ENSEMBLE-HYPOTHESES.md` for the executable hypothesis catalog.
The sweep and the forward service share `backtester/core/zec_ensemble.py`.
The simulator schedules a close-derived decision at a later bar's open and charges
costs on fills. An optimized batch recurrence must agree with the canonical
engine before its results can select configurations.

## Measured results

The validated run evaluated **1,652 unique configurations**, with 1,592 eligible
and 1,084 distinct validation behaviors. The frozen top ten all use **1h** bars.
The best minute validation score was −4.9496; the best hourly score was only
+0.0945. The combined ranking compares different market periods (180 days of
minute history versus approximately 3.6 years hourly), so it does not establish
that one timeframe is generally superior. A separate common-calendar diagnostic
is retained for each selected configuration.

The leader is the single strategy `bb_breakout(window=40, num_std=2.5)`.
The guide’s preferred ensemble architecture did not win this fixed search.
On the reserved hourly test, **2026-02-18 13:00UTC through 2026-11-11 01:00UTC**,
the leader returned **+282.64%** with **−21.64%** maximum drawdown, versus
buy-and-hold **+266.52% / −56.02%**. Its 48 closing/downsizing outcomes are
not necessarily 48 independent round trips. Doubling assumed costs reduced
the leader’s return to **+241.00%**, with −23.04% maximum drawdown.

**None of the ten selections establishes a statistically validated edge.**
Their validation deflated-Sharpe probabilities round to zero under the stated
1,652-trial IID-daily-return heuristic. That test has assumptions and is a
selection-bias warning, not a forecast. The saved common-calendar diagnostic
is weaker: the leader lost **7.63%**, versus buy-and-hold losing **23.21%**.
Its three older fixed stress windows returned **+0.99%, +4.34%, and −9.00%**.

| Frozen rank | Candidate ID | Policy | Reserved-test return | Max drawdown |
| --- | --- | --- | ---: | ---: |
| 1 | `0b5f50401a87b47b82f29119` | single(bb_breakout) | +282.64% | -21.64% |
| 2 | `019c293dc46c5d8e84b8894c` | gate(bb_breakout) gate=vol_regime persist=2 | +20.69% | -16.99% |
| 3 | `5cebaf1b01cfd69d4412877c` | mean(rsi,voltarget) | +20.44% | -33.31% |
| 4 | `0aa353146b7c6461422307fb` | mean(macd,swing_confluence,vol_regime,rsi) threshold=0.25 | +93.28% | -16.94% |
| 5 | `9ea0fb281c45c6f33d611fdc` | mean(swing_confluence,rsi) | +72.41% | -33.25% |
| 6 | `5ffb15720963de746562ba94` | switch(ts_momentum) gate=adx_trend fallback=rsi | +68.97% | -56.99% |
| 7 | `a13e07e99b8f7f92ff916193` | gate(swing_confluence) gate=adx_trend persist=2 | +144.80% | -29.03% |
| 8 | `a0e065f66366b921a4558860` | mean(ts_momentum,rsi) | +76.40% | -36.30% |
| 9 | `4849be02d874c82f29a8150d` | switch(swing_confluence) gate=adx_trend fallback=rsi | +80.12% | -57.09% |
| 10 | `28a045cab9e1048fd7cb27bf` | gate(bb_breakout) gate=vol_regime persist=3 | +19.60% | -11.31% |

After selection was frozen, a separate diagnostic opened the reserved minute
test for the best minute validation candidate, `all(ppo,rsi,voltarget)`.
It returned **-0.81%**, versus minute-window buy-and-hold
**-24.74%**. This diagnostic did not rerank the top ten or change
deployment. Cash returned zero before inflation/opportunity cost in both tests.

The final study ID is
`b68d46c7c105f3230dc0cdad8584df517f81c0054676c50f250c1f17e92d318e`.
An independent audit recomputed every validation score and eligibility check,
reconstructed the frozen rank without reading test metrics, checked unique IDs
and behavior deduplication, and verified source, code, selection and result hashes.

## Reproduce the study

From the repository root with its existing NumPy/Pandas Python environment:

```sh
"$STUDY_PYTHON" -m research.fetch_zec_history --start 2020-01-01 --workers 4 --output RESEARCH_ARCHIVE/zec-ensembles-20261110/reproduction-data
"$STUDY_PYTHON" -m research.zec_ensembles --data-dir RESEARCH_ARCHIVE/zec-ensembles-20261110/reproduction-data --output RESEARCH_ARCHIVE/zec-ensembles-20261110/reproduction --workers 6
```

A new download changes the data fingerprint. Keep the validated files and run
directory immutable when reproducing the accepted result. The preliminary
`study/` directory is a preserved computation checkpoint; `study-validated/`
is the authoritative result. Cache reuse has its own verified receipt.

## Installed service at historical acceptance

The study used a dedicated, version-pinned environment.
The durable home is `SERVICE_HOME/zec-forward-20261110`.
A dedicated LaunchAgent has `RunAtLoad` and
`KeepAlive`. Ten separate virtual accounts begin with 10,000 USDT each; their
capital is not a shared portfolio allocation.

All ten hourly tests started waiting for the first fully post-start candle. Its
first decision close is **2026-11-11 03:00UTC** (22:00 America/New_York on
November 10). Warmup receives no historical paper profit. A prospective paper decision remains
unavailable until that observation arrives; the next observed candle's open
then supplies the modeled reference fill. At acceptance time, the Oracle page displayed the
frozen rank-one configuration and all ten account identities.

The existing managed environment was upgraded coherently to manager 0.7.2,
Oracle 0.2.3, research runtime 0.4.0, backtester 0.2.0 and ecosystem 0.4.4.
The managed supervisor restarted gracefully; the old stopped/disarmed demo-grid
retains its intent and account journal. Other external owners remain separate.
The service pins installed implementation hashes and refuses changed policy
code, missing source cadence or stale observations.

Open the actual managed UI through `solbot ui open` and choose **Oracle**.
The selected publication is **ZEC/USDT**, never a silently converted USD quote.
Runtime identities, loaded-source hashes, wheel checksums, actual HTTP/browser
checks and preserved prior-owner state are recorded in:

`RESEARCH_ARCHIVE/zec-ensembles-20261110/independent-acceptance.json`

Check the installed paper owner directly:

```sh
"$STUDY_PYTHON" -I -m ecosystem.zec_forward --home SERVICE_HOME/zec-forward-20261110 status
```

Healthy waiting accounts have a fresh heartbeat and `first_post_start_closed_bar`.
A fresh running account has a new closed-candle decision. `available: false` during
startup or an outage is a withheld signal, not a synthetic flat forecast.


The final live health gate found and corrected a recovery latch after a temporary
feed error: successful polls with no new hourly candle now recover waiting or
running state when the stored candle is fresh. The scientific policy and every
original account/activation remain unchanged. The separate correction acceptance
receipt is `independent-recovery-acceptance.json` in the same external directory.

Publication note: `RESEARCH_ARCHIVE`, `SERVICE_HOME` and `COMPOUND_STATE` denote the original retained study archives or state directories. `$STUDY_REPO`, `$STUDY_PYTHON` and `$MARKET_DATA_DIR`, where shown, must point to the matching study checkout, environment and data. These private artifacts are not bundled with this article. Historical acceptance statements above describe the original study; publication review did not rerun experiments or operate services.
