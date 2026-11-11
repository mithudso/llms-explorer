# Research publication plan — November 11, 2026

The blog is the parent publication. Research papers appear under `/blog/research/`; `/research/` remains the task-oriented reference finder. The detailed implementation paper, **Queryable expertise: research memory, private skills and checked optimization**, is the November 11 release.

## Editorial and evidence rules

Each queued paper retains its complete historical study body, tables, dates, negative findings and evidence limits. Full-depth document optimization checks claims against retained sources. A separate reviewer reads the complete manuscript and reports disagreements. An approval binds the final Markdown and review report to exact SHA-256 values; changing either blocks publication. Editorial approval does not reproduce an experiment, certify trading performance, or qualify unreviewed research.

Source records were discovered across the accessible shared project memories and resolved against retained files. Account and employer material is excluded. Two existing public papers were deduplicated. One copied archival study, the nine-coin strategy sweep, remains on hold because the original evidence files needed to verify its retention claim are unavailable. Other incomplete or missing-source leads remain outside this queue. This is an inventory of available eligible papers, not a claim to have recovered every paper ever written.

## Daily queue

The workflow runs at 14:00 UTC (09:00 EST or 10:00 EDT). It publishes at most one article per America/New_York day, after 09:00. A missed day delays the queue; it never releases a backlog in a burst. Existing same-day articles and persisted receipts consume that day's slot. There are no subscriber messages.

Dates below are planned earliest publication dates. The scheduler requires current full-depth approvals. Papers and reviewed figures remain outside the public content/build until release. Figures move with the paper, and repeat builds preserve released evidence and figures. Forward companion references are marked forthcoming; the held study has no public destination.

| Planned date | Paper | Repository manuscript |
| --- | --- | --- |
| 2026-11-12 | Concept knowledge architecture strategies | `site/scheduled-posts/research/concept-knowledge-architecture.md` |
| 2026-11-13 | A model and effort matrix for bounded research | `site/scheduled-posts/research/research-model-effort-matrix.md` |
| 2026-11-14 | Comparing two evidence-bound research processes | `site/scheduled-posts/research/research-process-comparison.md` |
| 2026-11-15 | A dated vLLM and MLX comparison on Apple Silicon | `site/scheduled-posts/research/vllm-mlx-apple-silicon.md` |
| 2026-11-16 | Candle data gaps and the limits of historical tests | `site/scheduled-posts/research/candle-data-gap-audit.md` |
| 2026-11-17 | An archival reference for SOL strategies and signals | `site/scheduled-posts/research/sol-strategy-reference.md` |
| 2026-11-18 | Historical SOL strategy rankings and robustness checks | `site/scheduled-posts/research/sol-strategy-rankings.md` |
| 2026-11-19 | How an archival SOL study chose its top five candidates | `site/scheduled-posts/research/sol-robustness-top-five.md` |
| 2026-11-20 | Testing whether SOL findings transferred across assets | `site/scheduled-posts/research/cross-asset-strategy-transfer.md` |
| 2026-11-21 | Historical leverage and perpetual-futures cost economics | `site/scheduled-posts/research/leveraged-perpetuals-economics.md` |
| 2026-11-22 | A historical test of ratio rotation | `site/scheduled-posts/research/ratio-rotation-study.md` |
| 2026-11-23 | A compound five-minute direction scorecard | `site/scheduled-posts/research/compound-five-minute-scorecard.md` |
| 2026-11-24 | The historical frontier of a five-minute compound signal | `site/scheduled-posts/research/compound-five-minute-frontier.md` |
| 2026-11-25 | What five-minute perpetuals research establishes | `site/scheduled-posts/research/five-minute-perpetuals-evidence.md` |
| 2026-11-26 | Did the historical grid make money? | `site/scheduled-posts/research/grid-replay-review.md` |
| 2026-11-27 | A historical ZEC Volty Expan Close study | `site/scheduled-posts/research/zec-volty-study.md` |
| 2026-11-28 | ZEC ensemble hypotheses and their evidence limits | `site/scheduled-posts/research/zec-ensemble-study.md` |
| 2026-11-29 | Does ZEC show a recurring chart frequency? | `site/scheduled-posts/research/zec-cycle-validation.md` |
| 2026-11-30 | An exploratory shape-aware spot study | `site/scheduled-posts/research/shape-aware-spot-study.md` |
| 2026-12-01 | Grid cycles and chart shapes across a Coinbase top-50 sample | `site/scheduled-posts/research/coinbase-top50-grid-cycles.md` |
| 2026-12-02 | Market graph geometry and the limits of strategy evidence | `site/scheduled-posts/research/market-graph-geometry-evidence.md` |

## Operating the queue

From the repository root:

```sh
python3 site/tools/promote_scheduled_posts.py --dry-run
```

This inspects the current daily slot without moving files. The GitHub workflow invokes the same publisher, commits one reviewed article and its receipt, then explicitly dispatches site validation. The existing Pages Git integration deploys the default branch. GitHub scheduling can run late; release dates are not guaranteed delivery times.

Review records live in `site/research-reviews/`; full editorial reports live beside this plan. `site/src/data/publication-ledger.json` records actual scheduled releases. Reports preserve the author review and independent dissent/closure rather than claiming a new experiment.

## Concept family

Queryable Research Expertise is a zero-source domain under Research & Knowledge Tooling. Its five child topics remain unresolved frontier work: the Neo4j projection, provenance-aware hybrid retrieval, claim-to-source provenance, private skill distribution, and research-guided artifact optimization. The implementation report is a related reading, not a fabricated accepted concept pack.
