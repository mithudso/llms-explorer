---
description: >-
  Guide used-car and salvage-auction buying: Copart, IAAI, AutoBidMaster and brokers; title/damage/odometer fields; bidding, fees, valuation, repair budgets, reliable choices and buying alternatives.
  TRIGGER: "buy a car at Copart/IAAI", "what does Run and Drive mean", "how much should I bid", "estimate this salvage repair", "best-value used car".
  SKIP: new-car financing, loans, leases and maintenance procedures after purchase are outside this hub; use a separate specialist; this hub does not provide one.
name: used-car-buying
category: custom
tags:
  - used-cars
  - salvage-auctions
  - copart
  - iaai
  - autobidmaster
  - car-buying
  - vehicle-valuation
  - repair-cost-estimation
  - auto-auctions
keywords:
  - Copart
  - IAAI
  - Insurance Auto Auctions
  - AutoBidMaster
  - salvage title
  - rebuilt title
  - Run and Drive
  - actual cash value
  - total loss
  - VIN history
  - buyer premium
  - proxy bidding
  - dealer wholesale auction
  - Manheim
  - ADESA
whenToUse:
  - "How do I buy a car at Copart or IAAI without a dealer license?"
  - "Read this auction listing and explain its title, odometer and damage fields."
  - "Estimate a bid ceiling including repairs, fees and transport."
  - "Compare reliable used-car choices and alternatives to salvage auctions."
whenNotToUse:
  - "New-car financing, loans, or leasing — not covered here"
  - "General auto repair/maintenance procedures for a car you already own — use a repair-specific reference"
related_skills: []
version: "1.1.1"
updated: "2026-11-11"
model: claude-opus-5-5
effort: high
metadata:
  changelog_ref: references/CHANGELOG.md
---

# Used Car Buying

Reference hub for buying a used car through salvage/insurance auctions (Copart, IAAI) or
through the cheaper alternatives to them. Compiled from source-cited `/rabbithole` research
(SEC filings, regulatory records, official auction-site documentation, and independent
industry reporting). The references retain source citations for verification.
Start from the routing table, then read the listed `references/…md` file before answering
a deep question.

## Look for llms files first

Before reading the relevant auction, vehicle and title/registration sources raw, locate its llms files. If the repo is available, step 4 sets the order.
1. Check the subject's `llms.txt`, its docs site's `/llms.txt`, or matching packs under `~/.global-ai-hub/skills.llms/` and `~/.global-ai-hub/llms-concepts/`; use available hub keyword/search tools as discovery leads.
2. Run `wc -c` first (or inspect a remote size header). Read a file whole only when it fits; otherwise search it.
3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map, not a fact store.
4. If you have the repo, search its code before opening llms files. Verify each fact you act on against the authoritative file and line.
5. Index and llms hits are leads. Confirm them against readable source text before acting.

## Sub-skill routing table

| Sub-topic | When to load | Reference file |
| --- | --- | --- |
| `copart-salvage-auctions` | Copart-specific mechanics: VB3 bidding, condition tags, fees, title processing, market position | `references/copart-salvage-auctions.md` |
| `iaai-salvage-auctions` | IAAI (Insurance Auto Auctions, part of RB Global) as Copart's main competitor | `references/iaai-salvage-auctions.md` |
| `autobidmaster-international-bidding` | Broker access to Copart/IAAI for buyers without a dealer license, incl. overseas buyers | `references/autobidmaster-international-bidding.md` |
| `reading-a-salvage-auction-listing` | Title-status codes, damage fields, odometer/actual-mileage flags, condition reports | `references/reading-a-salvage-auction-listing.md` |
| `salvage-auction-bidding-strategy` | Proxy/live bidding mechanics, buyer premium and fees, reserve lots, when to walk away | `references/salvage-auction-bidding-strategy.md` |
| `individual-buyer-best-practices-at-salvage-auctions` | Pre-bid inspection limits, VIN/title history, total-cost budgeting, registration/insurance implications | `references/individual-buyer-best-practices-at-salvage-auctions.md` |
| `salvage-and-clean-title-vehicle-valuation` | Actual cash value, total-loss threshold, salvage/rebuilt title discount vs. clean-title comps | `references/salvage-and-clean-title-vehicle-valuation.md` |
| `auction-vehicle-repair-cost-estimation` | Estimating repair cost from listing photos/damage codes, parts sourcing, labor benchmarks | `references/auction-vehicle-repair-cost-estimation.md` |
| `newbie-mistakes-in-used-car-buying` | Recurring first-time-buyer mistakes across auction and general used-car buying | `references/newbie-mistakes-in-used-car-buying.md` |
| `best-value-used-car-selection` | Reliability data, depreciation curves, total-cost-of-ownership selection, independent of channel | `references/best-value-used-car-selection.md` |
| `low-cost-alternative-car-buying-channels` | Dealer wholesale auctions, private-party, CPO, credit-union buying programs as auction alternatives | `references/low-cost-alternative-car-buying-channels.md` |

## Notes on this research

- Reference files retain their source citations. Read the relevant source before relying on a claim; this routing table is not an evidence verdict.
- A handful of source citations in the underlying compiled packs were truncated mid-URL by
  the research pipeline (a known pipeline issue, not something fixed by rewriting the
  source) — those specific broken citations were filtered out rather than published as if
  valid. Treat any claim left without a usable supporting citation as unverified until you reacquire its source.
- Verify current auction fees, access rules, title/registration law, insurance eligibility and vehicle-specific costs against primary sources before a buying recommendation. State the jurisdiction and date; a dated research snapshot cannot establish current eligibility or a guaranteed repair estimate.
