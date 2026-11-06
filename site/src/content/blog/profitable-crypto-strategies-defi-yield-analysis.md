---
title: "Profitable Crypto Strategies and DeFi Yield Mechanics: An Unverified Quantitative Analysis"
description: "An unverified quantitative analysis of DeFi yield: real yield versus emissions, loss-versus-rebalancing, a DefiLlama field guide, thirteen DefiLlama pages and a ranked strategy table, with an evidence note on what was not checked."
date: "2026-11-06"
noindex: true
evidenceStatus: "unverified"
evidenceNote: "The dated DefiLlama figures, the strategy APY ranges, the loss-versus-rebalancing formula and the disqualification thresholds come from the author's analysis without matching public run artifacts. The ranked table and thresholds are heuristics, not measurements. Do not treat them as inputs for capital allocation."
tags: ["defi", "yield", "lvr", "defillama", "lending", "basis-trade", "solana"]
sources:
  - https://defillama.com/yields
  - https://defillama.com/earnings
  - https://defillama.com/holders-revenue
  - https://defillama.com/airdrops
  - https://defillama.com/protocols/risk-curators
  - https://kamino.com/docs/products/multiply/concepts
---

> **Evidence notice: unverified analysis.** This post reproduces an analysis document, edited for the site. Its DefiLlama snapshot figures are dated 2026-11-06 and were not re-collected for publication. Its strategy APY ranges, the LVR formula and the hard disqualification rules are the author's heuristics with no cited source. The [evidence notes](#evidence-notes) at the end list what was checked and what was not. This is educational material, not financial advice; leveraged positions can lose more than the stake.

## 1. The structural reality of DeFi yield

Most headline yields in decentralized finance are economic illusions. In a competitive, permissionless market a sustained positive expected value requires one of two things: a counterparty taking the equal and opposite negative expected value, or an entity paying non-dilutive economic rent for a verifiable service such as liquidity, credit, settlement or execution.

DeFi yield falls into three categories:

1. **Non-dilutive economic rent (real yield).** Cash flows from trading fees, borrow interest, protocol tollbooths and consensus validation rewards, paid in hard or native assets such as USDC, USDT, ETH or SOL.
2. **Dilutive capital subsidies (inflationary farming).** Yield paid in newly minted governance tokens such as AERO, RAY or CAKE. This transfers wealth from passive token holders to short-term farmers and tends to end in a liquidity death spiral.
3. **Adverse-selection traps (loss-versus-rebalancing, LVR).** High gross trading-fee yield on volatile automated-market-maker pairs that is exceeded by the divergence loss inflicted by informed arbitrageurs and toxic flow.

The decision tree the analysis uses to sort a quoted APY:

- Is the yield base fee or interest, or reward emission?
  - 100% reward emission: **inflation trap.** The farm token is dumped faster than it accrues, so real PnL is negative.
  - Base fee or organic yield: does the pool incur divergence or LVR risk?
    - No (single asset or correlated pair): **structural real yield** with positive expectancy (lending, staking, stable AMM).
    - Yes (volatile pair): is the edge ratio (income divided by LVR) above 1.2?
      - No: **adverse-selection trap.** A passive LP underperforms holding.
      - Yes: **conditional profitability.** It needs active rebalancing or a delta-neutral hedge.

## 2. Quantitative foundations: LVR and the AMM profitability inequality

The analysis cites market-structure research on loss-versus-rebalancing (Milionis, Moallemi and Roughgarden among others) and states that more than half of passive concentrated-liquidity providers on Uniswap v3, Orca Whirlpools and Aerodrome Slipstream lose money relative to simply holding. See the [evidence notes](#evidence-notes) for what could and could not be traced.

### 2.1 The LVR formulation

Impermanent loss measures only the path-independent divergence between two endpoints. With `k = P_t / P_0`:

```
IL(k) = 2*sqrt(k) / (1 + k) - 1
```

LVR instead measures the continuous cost an LP pays by trading against informed arbitrageurs who rebalance the pool whenever the external price moves.

For a concentrated position centered on price P across a symmetric log-range `[-w, +w]`, the analysis gives:

```
LVR_daily = sigma^2 / (8 * (1 - exp(-w/2))) * V_position
```

- `sigma` is the daily standard deviation of the log-price ratio.
- `w` is the half-width of the liquidity band in natural-log price space.
- As `w` goes to infinity (full range, Uniswap v2 constant product) this reduces to the classical volatility drag `sigma^2 / 8`.

### 2.2 The net LP profitability inequality

A position is profitable if and only if fee growth exceeds LVR plus rebalancing costs:

```
fee_growth_rate  >  LVR + rebalancing_costs

dFeeGrowthGlobal/dt  >  sigma^2 / (8 * (1 - exp(-w/2)))  +  (sigma^2 / w^2) * C_rebalance
```

- `sigma^2 / w^2` is the expected number of barrier crossings (rebalances) per day.
- `C_rebalance` is the all-in transaction cost: gas, the L1 data fee and swap impact on inventory.

### 2.3 The edge ratio

```
Edge Ratio = Daily Organic Fee Income / Daily LVR
```

- **Edge below 1.0:** the analysis says no passive concentrated range can be profitable over the price horizon.
- **Edge at or above 1.2:** a viable candidate for active or delta-hedged liquidity provision.

## 3. DefiLlama API infrastructure: capabilities and missing signals

The analysis inspected the DefiLlama OpenAPI specification and live endpoints to see what the platform tracks and what must be modeled elsewhere.

### 3.1 Dead or deprecated metrics

In the spec under `/yields/v1/pools` (lines 8418 to 8446 of the copy inspected):

- `il7d`: marked "Always null; no longer computed".
- `apyBase7d`: marked "Always null; no longer computed".
- `apyBaseInception`: marked "Always null; no longer computed".

DefiLlama no longer computes impermanent loss across its yield endpoints, so the quoted metrics are gross historical yields.

### 3.2 High-signal tracked fields

1. `apyBase`: organic yield from swap fees, borrow interest or validator consensus rewards.
2. `apyReward`: inflationary token emissions.
3. `ilRisk`: `"yes"` or `"no"`. The analysis treats `"no"` pools as having no divergence-loss risk.
4. `exposure`: `"single"` for single-asset deposits, `"multi"` for multi-asset LP pairs.
5. `stability_30d`: `1 / (1 + CV)`, where CV is the 30-day standard deviation of APY divided by its mean.
6. `predictions`: a machine-learning classification of whether trailing yield will be `Stable/Up` or `Down`, with probability and binned confidence.

## 4. Thirteen DefiLlama pages

Figures in this section were read from the live pages on 2026-11-06 and will have moved.

### 4.1 Top quoted yields (`defillama.com/yields?sortBy=apy&sortDesc=true`)

- Sorting by APY surfaces pools quoting 20,000% to 800,000% (Aerodrome WETH-RSR at 801,039%, OGN-OETHB at 407,134%, Blackhole WAVAX-USDC at 392,344%).
- `apyBase` is 0% or null across the top entries, so all of the quoted yield is `apyReward` (AERO or DEX gauge voting incentives). Pool TVL is small, roughly $15,000 to $380,000.
- Mechanism of ruin: the quoted APY extrapolates one epoch's voter bribe over a tiny pool. Capital inflow compresses it by orders of magnitude, and the secondary token suffers divergence loss against the primary asset, leaving a negative fiat return.

### 4.2 Chain-level app revenue (`/app-revenue/chains`, 24 hours)

- Ethereum about $16.8M, Solana about $9.1M, Hyperliquid L1 about $7.4M, Base about $2.2M, Arbitrum about $1.5M.
- Takeaway: real LP fees require real application revenue. A chain with high TVL but under $100k of daily app fees is subsidized.

### 4.3 Earnings (`/earnings`)

- Earnings = protocol revenue minus token incentives minus operating expenses.
- Structurally profitable: Tether and Circle (net interest on reserves, about $16.7M and $6.7M daily revenue), Hyperliquid (about $3.5M daily), pump.fun (about $1.4M), Lido (about $1.48M gross staking cut) and Morpho Blue (about $1.36M protocol fee capture).
- Takeaway: protocols with positive net operating margin are the only sustainable sources of yield for token-staking strategies.

### 4.4 Holders revenue (`/holders-revenue`, 30 days)

- Hyperliquid perps $66.8M (HYPE buybacks and community vault), Tron $24.9M (TRX burned through fees), Uniswap $8.4M (interface fees and selected fee switches), Aero Slipstream $3.26M (100% of pool swap fees to veAERO lockers), Sky $5.56M (MKR/SKY buyback-and-burn).
- Takeaway: governance tokens without programmatic cash flow trade at a structural discount to cash-flowing protocols.

### 4.5 DEX turnover (`/exchanges`, 24 hours)

- Uniswap V3 $1.72B (7 days: $8.38B), Uniswap V4 $1.29B ($7.70B), PancakeSwap V3 $896M ($4.62B), Aero Slipstream $832M ($4.54B).
- Fee velocity is 24h volume divided by TVL. The analysis reports Aero Slipstream and Uniswap V3 above 0.6 to 1.2 on core pairs, which it argues is enough organic yield to offset volatility drag under tight band management.

### 4.6 Airdrops (`/airdrops`)

- More than 4,300 tracked protocols have no native token.
- Capital locked in zero-yield points programs bears a drag of at least 5.0% to 5.5% a year against Treasury yields. The analysis puts sybil and wash-trading dilution of retail cohorts at 70% to 90%.
- Verdict: negative expected value for unhedged retail capital.

### 4.7 Leveraged recursive lending (`/yields/loop`)

The loop APY:

```
APY_loop = APY_collateral + (APY_collateral - APY_borrow) * LTV / (1 - LTV)
```

Two risk factors:

1. **Utilization kink shock.** Money-market curves are piecewise linear:
   ```
   R_borrow = R0 + (U / U_kink) * R1                          for U <= U_kink
   R_borrow = R0 + R1 + ((U - U_kink) / (1 - U_kink)) * R2    for U >  U_kink
   ```
   Past the kink (roughly 85% to 90% utilization) the analysis says borrow rates jump from about 3% to 25% or more, inverting net yield at once.
2. **Depeg liquidation.** The analysis states that at 90% LTV (10x leverage) a 2.5% depeg triggers liquidation with a 5% to 10% penalty. See the [evidence notes](#evidence-notes): this depends on the market's liquidation threshold.

### 4.8 Chains by TVL (`/chains`)

- Ethereum $43.20B (deepest liquidity, high gas floor, positions above about $10,000), Base $5.84B (sub-$1,000 active LP management), Solana $5.30B, BSC $5.08B, Tron $5.01B (USDT transfers, limited smart-contract LP), Arbitrum $1.44B.

### 4.9 Categories (`/categories`)

- Structural value capturers: DEXes and derivatives (a toll on non-directional volume), liquid staking (a skim on consensus inflation), lending (interest margins backed by programmatic liquidation).
- Value destroyers: cross-chain bridges (exploit exposure, sub-1 bps margins) and yield aggregators (layered smart-contract risk for marginal fee optimization).

### 4.10 Risk curators (`/protocols/risk-curators`)

- 99 curators run isolated credit vaults on Morpho Blue and Euler v2: Steakhouse Financial $2.76B, Sentora $2.66B, Gauntlet $1.49B curated TVL.
- Curators set conservative LLTV thresholds (for example 77% to 86%) on single collateral pairs such as wstETH/USDC and cbBTC/USDC, and adjust parameters to prevent bad-debt accrual.
- The analysis calls this the highest risk-adjusted stablecoin yield in DeFi, at 6.5% to 12.0% organic interest.

### 4.11 Launchpads (`/protocols/launchpad`)

- pump.fun earns about $1.4M a day by charging 1% on bonding-curve swaps with no balance-sheet risk.
- LPs on graduated pairs (Raydium, PumpSwap) face LVR losses the analysis puts above 80% as early buyers sell. It concludes that LPing graduated launchpad pairs is ruinous.

### 4.12 Yield predictions (`/predictions`, 15,698 pools)

- Down: 6,235 pools (39.7%). Stable/Up: 4,596 (29.3%). Unclassified: 4,867 (31.0%).
- More than 70% of active pools are therefore either in yield decay or unpredictable. APY spikes with a Down prediction reflect bribe or volume surges that the analysis expects to revert within 7 to 14 days.

## 5. Taxonomy and ranking of the strategies

The analysis ranks yield strategies by risk-adjusted net return, capital capacity and operational complexity. The APY ranges and capacities are the author's estimates and have no cited source.

| Rank | Strategy | Real net APY | Risk | Directional beta | Capacity | Primary failure modes |
|:---:|---|:---:|:---:|:---:|:---:|---|
| 1 | Delta-neutral basis (cash and carry) | 8% to 25% | Low-Med | Zero | >$100M | Exchange insolvency, liquidation on short-leg wicks, negative funding flip |
| 2 | Risk-curated isolated credit (Morpho) | 6% to 13% | Low | Zero (in USD) | >$50M | Oracle latency, borrower bad-debt socialization, smart-contract bug |
| 3 | Correlated or pegged AMM provision | 7% to 22% | Low-Med | Zero (in asset) | <$25M | Underlying depeg (for example an LST discount), JIT bot fee frontrunning |
| 4 | Cross-exchange funding-rate arbitrage | 12% to 30% | Medium | Zero | <$20M | Margin divergence between legs, exchange API or withdrawal freeze |
| 5 | Delta-neutral CLMM plus perp short | 15% to 38% | Med-High | Zero | <$5M | Range breakout into a decaying asset, rebalancing gas drag |
| 6 | Unleveraged liquid staking plus restaking | 3.5% to 8% | Low | 1.0 (in ETH/SOL) | >$1B | Validator slashing, contract exploit, withdrawal-queue congestion |
| 7 | Programmatic real-yield protocol staking | 8% to 30% | High | 1.0 (in protocol token) | <$25M | Token price collapse, fee contraction, governance exploit |
| 8 | Recursive staking loops (LTV 75% or lower) | 8% to 18% | High | 1.0 (in asset) | <$30M | Money-market borrow-kink spike, oracle liquidation cascade |
| 9 | Atomic MEV and flash-loan liquidations | 35% to 100%+ | High | Zero | <$1M | Gas bribe wars, alpha decay, private order-flow internalization |

## 6. An algorithmic decision framework for yield deployment

The analysis proposes this filter for automated deployment:

1. Is more than 50% of the quoted APY from reward emissions? If yes, **reject** (dilution and farm-token dump risk).
2. Is it single-sided or a pegged asset?
   - Lending: is the vault risk-curated with a fixed LLTV? If yes, **deploy** into institutional isolated credit (Morpho or Euler). If no, reject.
   - Staking: is there slashing protection and a track record? If yes, **deploy** into an LST or native staking. If no, reject.
3. If it is a volatile pair, compute historical volatility and continuous LVR. If the edge ratio is below 1.2, reject. Otherwise, if directional risk can be hedged with a perp short, **deploy** a delta-neutral CLMM position with the short. If it cannot be hedged, reject.

### 6.1 Hard disqualification rules

1. **Emission rule.** Disqualify any pool where `apyBase` is 0.
2. **LVR rule.** Disqualify any volatile LP where daily fee yield divided by LVR is below 1.2.
3. **Borrow-kink rule.** In recursive loops, deleverage automatically when pool utilization passes 80%.
4. **TVL floor.** Require TVL of at least $100,000 to avoid illiquidity traps and gauge-bribe distortions.
5. **Deposit break-even bound.** Position size must exceed all-in gas cost divided by net daily APR. Positions under about $500 on L1 or high-gas L2 pairs bleed to gas.

## Evidence notes

These notes were added when the analysis was prepared for the site. They are a spot check against separate sourced research, not a validation of the whole document.

- **Loop APY formula.** The formula in section 4.7 is algebraically consistent with the standard form: net APY equals collateral yield plus the yield spread times (leverage minus 1), and leverage minus 1 equals LTV divided by (1 minus LTV). [Kamino's Multiply documentation](https://kamino.com/docs/products/multiply/concepts) states the same relation.
- **The 2.5% depeg figure is not generally right.** Whether a 10x loop liquidates at a given depeg depends on the market's liquidation threshold, not only the opening LTV. Kamino lists a JitoSOL/SOL elevation group at 90% LTV, and its documentation says it prices SOL-denominated LSTs at their stake rate rather than their DEX price, so a market discount alone does not raise reported LTV. The liquidation risk is the exchange rate (for example an exploit or slashing event) together with the yield-versus-borrow spread.
- **The strategy ranking in section 5 is unsourced.** No source is cited for the APY ranges or capacities. A separate sourced review found one published net-of-cost result for perpetual-versus-spot basis capture (a simulated Bitcoin Sharpe ratio of 1.80 at Binance maker fees, in [He and Manela](https://arxiv.org/html/2212.06888v5)), and warned that cash-and-carry carries margin-spike and liquidation risk in drawdowns.
- **The LVR formula for concentrated liquidity** reduces correctly to `sigma^2 / 8` at full range. The finite-width form was not independently derived or checked here.
- **The "more than 50% of LPs lose to HODL" statement** is attributed to LVR research and a Bancor v3 post-mortem. It was not traced to a specific source here.
- **The hard rules in 6.1** (the 80% utilization trigger, the $100,000 TVL floor, the edge-ratio threshold of 1.2) are heuristics. No source is cited for the specific values.
- **Dated figures.** Every DefiLlama number in section 4 is a 2026-11-06 snapshot. The deprecation of `il7d`, `apyBase7d` and `apyBaseInception` is a statement about one copy of the OpenAPI spec and should be re-checked against the current spec before building on it.
