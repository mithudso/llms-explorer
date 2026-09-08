---
title: "Personal Income Taxes"
description: "> Educational information, NOT tax advice. This is a practical filer's"
---

# US Personal Income Taxes (+ North Carolina)

> **Educational information, NOT tax advice.** This is a practical filer's
> reference, not a substitute for a CPA, enrolled agent, or tax attorney. Tax
> figures change **every year** with inflation, and the **One Big Beautiful Bill
> Act (OBBBA, signed July 4, 2025)** reshaped several individual provisions —
> so anything here is **"as of 2026"** and must be re-verified at **irs.gov**
> and **ncdor.gov** before you rely on it. Dollar thresholds below are
> **date-stamped by tax year (TY)**: "TY2025" = the return filed in early 2026;
> "TY2026" = the return filed in early 2027.

This skill is a **spoke of the `consumer-finance` hub** (note only — do not
modify the hub). In this installation the consumer-finance family is registered
as **`consumer-credit-and-debt`** — route there for sibling topics. Neighboring
spokes are cross-referenced at the end.

---

## 0. The shape of a 1040 (how the numbers connect)

A US individual return (**Form 1040**) flows top to bottom:

1. **Gross income** — wages (W-2 box 1), self-employment, interest, dividends,
   capital gains, retirement distributions, etc.
2. **− Above-the-line adjustments** (Schedule 1) → **Adjusted Gross Income (AGI)**.
   AGI is the pivotal number; most phase-outs key off AGI or *modified* AGI (MAGI).
3. **− Standard deduction OR itemized deductions** (Schedule A) → **taxable income**.
4. **Apply the tax brackets** to taxable income → **tax before credits**.
5. **− Tax credits** (some refundable, some not) → **tax after credits**.
6. **− Payments** (withholding from W-2/1099, estimated payments) → **refund or balance due**.

> **TCJA note:** Most of the 2017 Tax Cuts and Jobs Act individual structure was
> set to *sunset* after TY2025. **OBBBA made the TCJA rate brackets and the
> larger standard deduction PERMANENT** and added new (some temporary) deductions.
> The "2025→2026 sunset cliff" people feared **did not happen** — but several
> OBBBA add-ons (senior deduction, tips/overtime deductions) are **temporary
> (≈TY2025–2028)**, so a *different* uncertainty now applies. Verify any
> OBBBA-specific figure at irs.gov.

---

## 1. Filing status

| Status | Who | Notes |
|---|---|---|
| **Single** | Unmarried, not HoH | — |
| **Married Filing Jointly (MFJ)** | Married, one combined return | Usually lowest tax; both spouses jointly liable |
| **Married Filing Separately (MFS)** | Married, separate returns | Often higher tax; loses EITC, most education credits, blocks student-loan-interest deduction |
| **Head of Household (HoH)** | Unmarried + paid >½ cost of a home for a qualifying person | Bigger standard deduction & wider brackets than Single |
| **Qualifying Surviving Spouse (QSS)** | Widow(er) w/ dependent child, ≤2 yrs after spouse's death | Uses MFJ brackets/standard deduction |

Status is generally fixed by your situation on **Dec 31**.

---

## 2. Marginal vs effective brackets (date-stamped)

The US uses **7 marginal brackets** (10/12/22/24/32/35/37%). Your **marginal
rate** is the rate on your *last* dollar; your **effective rate** is total tax ÷
taxable income (always lower). A raise into a higher bracket only taxes the
*portion* above the threshold — it never lowers your take-home.

> **Worked example (TY2025, Single, $60,000 taxable income):** 10% on the first
> $11,925 + 12% from $11,925 to $48,475 + 22% on the last $11,525 = **≈$8,114
> tax → marginal rate 22%, effective rate ≈13.5%.**

### TY2025 brackets (taxable income) — IRS Rev. Proc. 2024-40
| Rate | Single | Married Filing Jointly |
|---|---|---|
| 10% | $0 – $11,925 | $0 – $23,850 |
| 12% | $11,926 – $48,475 | $23,851 – $96,950 |
| 22% | $48,476 – $103,350 | $96,951 – $206,700 |
| 24% | $103,351 – $197,300 | $206,701 – $394,600 |
| 32% | $197,301 – $250,525 | $394,601 – $501,050 |
| 35% | $250,526 – $626,350 | $501,051 – $751,600 |
| 37% | over $626,350 | over $751,600 |

### TY2026 brackets (taxable income) — IRS Rev. Proc. 2025-32
| Rate | Single | Married Filing Jointly |
|---|---|---|
| 10% | $0 – $12,400 | $0 – $24,800 |
| 12% | $12,401 – $50,400 | $24,801 – $100,800 |
| 22% | $50,401 – $105,700 | $100,801 – $211,400 |
| 24% | $105,701 – $201,775 | $211,401 – $403,550 |
| 32% | $201,776 – $256,225 | $403,551 – $512,450 |
| 35% | $256,226 – $640,600 | $512,451 – $768,700 |
| 37% | over $640,600 | over $768,700 |

*(HoH, MFS, QSS thresholds differ — see the IRS releases linked below.)*

---

## 3. Standard vs itemized deduction

Take the **larger** of the two. Most filers (since TCJA nearly doubled the
standard deduction) take the **standard**.

### Standard deduction
> ⚠️ **OBBBA retroactively RAISED the TY2025 standard deduction** above the
> originally-announced Oct-2024 figures. The numbers below are the
> **in-effect, OBBBA-revised** amounts (IRS Rev. Proc. 2025-32 supersedes the
> earlier figures). An old TY2025 source showing $15,000/$30,000 is pre-OBBBA.

| Filing status | TY2025 (in effect) | TY2026 |
|---|---|---|
| Single | $15,750 | $16,100 |
| Married Filing Jointly / QSS | $31,500 | $32,200 |
| Head of Household | $23,625 | $24,150 |
| Married Filing Separately | $15,750 | $16,100 |

**Additional standard deduction** for **age 65+ OR blind** (per condition; a
person 65+ *and* blind gets it twice): TY2025 **$1,600** (married, per box) /
**$2,000** (unmarried); TY2026 **$1,650 / $2,050**.

### Itemize instead if your total exceeds the standard deduction
Schedule A buckets: **SALT** (state/local income or sales + property tax — note
OBBBA raised the SALT cap above the old $10,000; verify the current cap and
income phasedown at irs.gov), **mortgage interest**, **charitable gifts**,
**medical expenses over 7.5% of AGI**. Itemizing is common for homeowners in
high-tax areas; renters rarely beat the standard deduction.

---

## 4. Common credits (more valuable than deductions — $-for-$)

A **deduction** lowers taxable income; a **credit** lowers tax dollar-for-dollar.
**Refundable** credits can pay you beyond zero tax; **nonrefundable** only zero
out tax owed. *(Figures TY2025 unless noted.)*

| Credit | Form | Amount / structure | Key limits |
|---|---|---|---|
| **Earned Income Tax Credit (EITC)** — *refundable* | Sch. EIC | Max **$649** (0 kids), **$4,328** (1), **$7,152** (2), **$8,046** (3+) | Low/moderate earned income; investment income ≤ **$11,950**; MFS generally barred. Verify the AGI phase-out limits on the IRS EITC tables. |
| **Child Tax Credit (CTC)** — *partly refundable* | Sch. 8812 | **$2,200 / qualifying child** (OBBBA raised from $2,000 & made permanent); refundable **Additional CTC up to $1,700** | MAGI phase-out **$200k** (Single/HoH) / **$400k** (MFJ); −$50 per $1,000 over. Child must have an SSN. |
| **American Opportunity (AOTC)** — *40% refundable* | 8863 | **$2,500/student** = 100% of first $2,000 + 25% of next $2,000; up to **$1,000 refundable** | First 4 yrs of college; MAGI phase-out **$80k–$90k** Single / **$160k–$180k** MFJ (static) |
| **Lifetime Learning (LLC)** — *nonrefundable* | 8863 | **$2,000/return** (20% of up to $10,000) | Any post-secondary/job-skill course; same MAGI phase-out as AOTC. Can't claim AOTC and LLC for the *same* student. |
| **Saver's Credit** — *nonrefundable* | 8880 | 50/20/10% of up to $2,000 contrib ($4,000 MFJ) → max **$1,000/$2,000** | TY2025 50% tier: AGI ≤ $23,750 Single / ≤ $47,500 MFJ. **Becomes the "Saver's Match" (a direct deposit) starting TY2027** (SECURE 2.0). |
| **Child & Dependent Care** — *nonrefundable* | 2441 | 20–35% of up to **$3,000** (1 dependent) / **$6,000** (2+) | 35% at AGI ≤ $15k, fading to 20% over $43k. **OBBBA raises the top rate toward 50% beginning TY2026.** |

> Don't confuse the **Child Tax Credit** (per child, on Sch. 8812) with the
> **Child & Dependent Care Credit** (for daycare/care costs so you can work, on
> Form 2441) — they're different credits and you can claim both.

---

## 5. Above-the-line adjustments (reduce AGI even if you take the standard deduction)

These come off gross income **before** AGI, so they help everyone and shrink
MAGI-based phase-outs:

| Adjustment | TY2025 | TY2026 | Notes |
|---|---|---|---|
| **HSA contribution** (must have an HDHP) | $4,300 self / $8,550 family | $4,400 / $8,750 | +$1,000 catch-up at 55+. *Triple-tax-advantaged.* |
| **Traditional IRA deduction** | $7,000 (+$1,000 at 50+) | $7,500 (+$1,100) | Deduction phases out if you (or spouse) have a workplace plan — Single covered $79k–$89k (TY2025). |
| **Student-loan interest** | up to **$2,500** | up to $2,500 | MAGI phase-out $85k–$100k Single / $170k–$200k MFJ; **MFS can't claim.** |

> Retirement-account **strategy and contribution mechanics** (Roth vs
> traditional choice, backdoor Roth, employer-match optimization) are **out of
> scope — route to a dedicated retirement/investing skill if one is installed.**
> Briefly, on the *tax* side only: *traditional* = deduct now / taxed at
> withdrawal; *Roth* = no deduction now / tax-free qualified withdrawals. HSA and
> IRA appear here only as the AGI-reducing line items.

---

## 6. W-4 withholding & refund-vs-owe

Your employer withholds tax from each paycheck based on the **Form W-4** you file.

- The **redesigned W-4 (post-2020) eliminated "allowances"** (they were tied to
  personal exemptions, which TCJA zeroed out). It's now a 5-step form: filing
  status (Step 1), multiple-jobs/working-spouse (Step 2), dependents/credits
  (Step 3), other income / deductions / **extra withholding 4(c)** (Step 4),
  sign (Step 5).
- A **big refund ≠ winning** — it means you over-withheld and gave the
  government an interest-free loan all year. **Owing a lot** can trigger an
  underpayment penalty. The goal is to land near **$0**.
- Tune withholding with the **IRS Tax Withholding Estimator**
  (irs.gov/individuals/tax-withholding-estimator), which outputs a pre-filled W-4.

---

## 7. W-2 vs 1099, self-employment tax & quarterly estimated taxes

> **Boundary:** this section is for an **individual filer** with 1099 / gig /
> freelance income filing a personal return. If your question is about owner
> taxes *because you formed an entity* (LLC/S-corp/sole-prop entity choice and
> its self-employment-tax consequences), that's **`venture-nc-business-formation-tax`**.

**W-2 (employee):** employer withholds income tax and pays half of your
Social-Security/Medicare (FICA); you do nothing extra.

**1099-NEC (independent contractor / gig / freelancer):** *no* withholding, *no*
employer FICA match — **you owe self-employment tax and must make your own
quarterly payments.** (Worker status is decided by IRS common-law rules —
behavioral/financial control & relationship; misclassification is a real risk.)

### Self-employment (SE) tax
- **Rate 15.3% = 12.4% Social Security + 2.9% Medicare**, charged on **92.35%**
  of net SE earnings; kicks in at **$400** of net earnings.
- The **12.4% SS portion** applies only up to the SS wage base: **$176,100
  (TY2025) / $184,500 (TY2026)**; the 2.9% Medicare portion has no cap.
- **0.9% Additional Medicare Tax** on wages/SE income over **$200k Single /
  $250k MFJ / $125k MFS** (static — Form 8959).
- You **deduct one-half of SE tax** above the line, easing the sting.

### Quarterly estimated taxes (Form 1040-ES)
- **Who:** anyone expecting to owe **$1,000+** at filing after withholding
  (typical for self-employed, large investment income, or under-withheld W-2).
- **Safe harbor** (avoids the underpayment penalty — pay the *smaller* of):
  **90% of this year's tax**, OR **100% of last year's** (**110% if prior-year
  AGI > $150k**).
- **Four due dates (TY2026 cycle):** Apr 15 2026, Jun 15 2026, Sep 15 2026,
  Jan 15 2027 (next business day if a weekend/holiday). Penalty figured on
  **Form 2210**.

---

## 8. Capital gains (brief — tax treatment only; route strategy to a retirement/investing skill)

When you sell an asset (stock, crypto, property), gain = **amount realized −
basis**. **Basis** = what you paid, adjusted for things like improvements or
reinvested dividends.

- **Short-term** (held **≤ 1 year**): taxed as **ordinary income** at your
  bracket rate.
- **Long-term** (held **> 1 year**): preferential **0% / 15% / 20%** rates.

**TY2025 long-term breakpoints (taxable income):** 0% up to **$48,350** Single /
**$96,700** MFJ; 15% above that to **$533,400** / **$600,050**; 20% beyond.

- **Net Investment Income Tax (NIIT) 3.8%** adds on top once MAGI exceeds
  **$200k Single / $250k MFJ** (static — Form 8960).
- Reported on **Schedule D + Form 8949**. Capital *losses* offset gains and up
  to **$3,000** of ordinary income per year (excess carries forward).

---

## 9. The IRS process: deadlines, extensions, fixes, audits, paying late

| Topic | What to know |
|---|---|
| **Deadline** | **April 15** (TY2025 → Apr 15, 2026); next business day if a weekend/holiday. |
| **Extension (Form 4868)** | Buys time to **file** (to **Oct 15**), **NOT** time to **pay** — estimate and pay by Apr 15 or owe interest + penalty. |
| **Amended return (Form 1040-X)** | Fix a filed return; e-fileable for the current + 2 prior years. **Refund claim window: 3 years** from the original filing (or 2 yrs after paying). |
| **Audits** | Correspondence (mail), office, or field. General **3-year** assessment statute; up to **6 years** for a substantial (>25%) income omission; no limit for fraud/non-filing. Keep records ≥3 yrs. |
| **Payment plans** | **Short-term:** ≤180 days, balance < $100k, $0 setup fee. **Long-term installment agreement:** balance ≤ $50k to apply online; small setup fee (reduced/waived for low income). Apply via the **Online Payment Agreement**. |
| **Offer in Compromise (OIC)** | Settle for **less than you owe** when you genuinely can't pay it all; check the **OIC Pre-Qualifier** first. Not a routine discount — the IRS evaluates ability to pay. |

> A **1099-C (canceled debt)** that shows up as taxable income — and the
> insolvency exclusion / **Form 982** — is **cross-referenced, not covered here
> → `charge-offs-collections-and-debt-resolution`.** Likewise **tax-related
> identity theft** (someone files using your SSN), the **IRS IP PIN**, and
> **Form 14039** → **`identity-theft-and-credit-fraud`.**

---

## 10. Free filing (verify current — status changed in 2025)

- **IRS Free File** — public-private partnership: brand-name guided software
  **free if AGI ≤ $89,000** (FS2026 figure; was ~$84k the prior year).
  **Free File Fillable Forms** are available **at any income**. **Still
  operating.** → irs.gov/freefile
- **IRS Direct File** (the IRS's own free direct-to-government e-file tool) —
  > ⚠️ **As of 2026: NOT available.** The IRS told its 25 partner states in
  > Nov 2025 that **"Direct File will not be available in Filing Season 2026,"**
  > the app/pages are down (directfile.irs.gov refuses connection; the old IRS
  > pages 404), and the Jan 2026 filing-season notice omits it. Note: **OBBBA
  > §70607 funded a *study* of a public-private replacement (a $15M task force,
  > 90-day report) — it did not itself order termination;** the shutdown was a
  > separate IRS/Treasury administrative decision. **Re-verify at irs.gov before
  > relying** — its future is unsettled.
- **Other free options:** **MilTax** (military) and **VITA/TCE** (free
  in-person prep for lower-income, elderly, limited-English filers).

---

## 11. North Carolina individual income tax (flat rate)

NC is a **flat-tax** state — one rate on **NC taxable income**, no brackets.
File **Form D-400** (+ **Schedule S** for additions/deductions). NC deadline
**matches federal (≈April 15)**; NCDOR offers **eFile**.

### NC flat rate (date-stamped) — NCDOR / G.S. 105-153.7
| Tax year | Flat rate |
|---|---|
| 2024 | 4.50% |
| **2025** | **4.25%** |
| **2026 and after** | **3.99%** |

Beyond 2026, **revenue-triggered** cuts can step the rate down further
(by up to 0.50 pt/yr) toward a **statutory floor of 2.49%**, but only if NC
General-Fund revenue clears set thresholds (tax years 2027–2034) — **conditional,
not guaranteed.** Verify at ncdor.gov.

### NC standard deduction (TY2025)
| Filing status | NC standard deduction |
|---|---|
| Married Filing Jointly / QSS | $25,500 |
| Head of Household | $19,125 |
| Single | $12,750 |
| Married Filing Separately | $12,750 |

> NC uses **its own** standard deduction, **not** the federal amount, and has
> **no** age-65/blind add-on. (TY2026 figure not separately published at
> research time — these have been flat since 2022; verify.)

### Where NC differs from federal (filer-facing)
- **Starts from federal AGI**, then applies NC adjustments → NC taxable income ×
  flat rate. **No personal exemptions.**
- **Social Security / Railroad Retirement: NOT taxed by NC** (deduct on D-400
  Sch. S if in federal AGI).
- **Bailey settlement:** certain federal/state/local & military retirement
  benefits are **NC-exempt** if the retiree had **5+ years of creditable service
  as of Aug 12, 1989.**
- **Capital gains: taxed as ordinary income at the flat rate** — NC has **no**
  preferential long-term rate (gains already sit in federal AGI).
- **NC itemized deductions are limited** (mortgage interest + property taxes
  combined **capped at $20,000**; plus charitable, medical, claim-of-right) —
  narrower than federal Schedule A.
- **NC 529 contributions:** **no NC contribution deduction** (earnings/qualified
  withdrawals are still NC-tax-free).

### NC child deduction (a DEDUCTION, not a credit) — TY2025
Per qualifying child (one for whom you get the federal CTC), tiered by filing
status and federal AGI; phases to $0 at higher AGI.

| Filing status | Top tier (per child) | Fully phased out above |
|---|---|---|
| MFJ / QSS | $3,000 (AGI ≤ $40,000) | $140,000 |
| Head of Household | $3,000 (AGI ≤ $30,000) | $105,000 |
| Single / MFS | $3,000 (AGI ≤ $20,000) | $70,000 |

*(Intermediate AGI tiers step down $500 at a time — see the NCDOR child-deduction page.)*

> **NC BUSINESS taxes** — entity income, sales/use, franchise, NC withholding,
> employer payroll — are **out of scope here.** Forming a NC entity / business
> tax → **`venture-nc-business-formation-tax`**; running payroll / NC withholding
> as an employer → **`venture-nc-employer-payroll`.**

---

## Cross-references (consumer-finance family)

- **`consumer-credit-and-debt`** — the installed consumer-finance family hub;
  route here for other consumer-finance/credit spokes.
- **`charge-offs-collections-and-debt-resolution`** — **1099-C canceled-debt
  income**, insolvency exclusion, **Form 982**.
- **`identity-theft-and-credit-fraud`** — **tax-related identity theft**, IRS
  **IP PIN**, Form 14039, 5071C letter.
- **`student-loans`** — student-loan repayment/forgiveness (the **$2,500
  interest deduction** lives here in §5; the *loans* themselves are there).
- **`personal-banking`** — deposit-interest (1099-INT) accounts, HYSA basics.
- *(retirement / investing skill, if installed)* — retirement-account
  **strategy** (Roth vs traditional) and **capital-gains strategy**; this skill
  covers only the tax *treatment* of each.
- **`venture-nc-business-formation-tax`** / **`venture-nc-employer-payroll`** —
  BUSINESS entity tax, sales/use/franchise, and employer payroll/withholding.

---

## References (verify current — figures change yearly; re-check before relying)

**Date-stamped: compiled 2026-06-16. Tax law is volatile post-OBBBA (July 2025).**

### IRS — federal (irs.gov)
- TY2025 inflation adjustments (brackets, EITC, Saver's): https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2025
- TY2026 inflation adjustments (incl. OBBBA amendments): https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026-including-amendments-from-the-one-big-beautiful-bill
- OBBBA individual provisions: https://www.irs.gov/newsroom/one-big-beautiful-bill-provisions
- Standard deduction (Topic 551): https://www.irs.gov/taxtopics/tc551
- EITC tables: https://www.irs.gov/credits-deductions/individuals/earned-income-tax-credit/earned-income-and-earned-income-tax-credit-eitc-tables
- Child Tax Credit / Sch. 8812: https://www.irs.gov/credits-deductions/individuals/child-tax-credit
- Education credits (AOTC/LLC, Pub 970): https://www.irs.gov/publications/p970 · AOTC: https://www.irs.gov/credits-deductions/individuals/aotc
- Saver's Credit (Form 8880): https://www.irs.gov/pub/irs-pdf/f8880.pdf
- Child & Dependent Care (Form 2441): https://www.irs.gov/instructions/i2441
- Retirement-plan & IRA limits: https://www.irs.gov/newsroom/401k-limit-increases-to-24500-for-2026-ira-limit-increases-to-7500
- HSA limits: TY2025 https://www.irs.gov/pub/irs-drop/rp-24-25.pdf · TY2026 https://www.irs.gov/pub/irs-drop/rp-25-19.pdf
- Student-loan interest (Topic 456): https://www.irs.gov/taxtopics/tc456
- Form W-4 / withholding: https://www.irs.gov/forms-pubs/about-form-w-4 · Withholding Estimator: https://www.irs.gov/individuals/tax-withholding-estimator
- Self-employment tax: https://www.irs.gov/businesses/small-businesses-self-employed/self-employment-tax-social-security-and-medicare-taxes
- Estimated taxes / Form 1040-ES: https://www.irs.gov/businesses/small-businesses-self-employed/estimated-taxes
- Capital gains (Topic 409): https://www.irs.gov/taxtopics/tc409 · NIIT: https://www.irs.gov/individuals/net-investment-income-tax
- When to file / extension (Form 4868): https://www.irs.gov/filing/individuals/when-to-file · https://www.irs.gov/forms-pubs/extension-of-time-to-file-your-tax-return
- Amended returns (1040-X): https://www.irs.gov/filing/amended-return-frequently-asked-questions
- Audits: https://www.irs.gov/businesses/small-businesses-self-employed/irs-audits
- Payment plans: https://www.irs.gov/payments/online-payment-agreement-application · OIC: https://www.irs.gov/payments/offer-in-compromise
- Free File: https://www.irs.gov/freefile · Free-file hub: https://www.irs.gov/e-file-do-your-taxes-for-free
- Direct File status (Taxpayer Advocate filing-season page): https://www.taxpayeradvocate.irs.gov/get-help/filing-returns/filing-season-resources/

### NCDOR — North Carolina (ncdor.gov)
- NC tax-rate schedules: https://www.ncdor.gov/taxes-forms/individual-income-tax/tax-rate-schedules
- NC rate statute (G.S. 105-153.7): https://www.ncleg.gov/EnactedLegislation/Statutes/HTML/BySection/Chapter_105/GS_105-153.7.html
- NC standard / itemized deductions: https://www.ncdor.gov/taxes-forms/individual-income-tax/filing-topics/north-carolina-standard-deduction-or-north-carolina-itemized-deductions
- NC child deduction: https://www.ncdor.gov/taxes-forms/individual-income-tax/north-carolina-child-deduction
- NC Social Security / Railroad Retirement: https://www.ncdor.gov/taxes-forms/individual-income-tax/filing-topics/social-security-and-railroad-retirement-benefits
- NC Bailey decision (retirement exemption): https://www.ncdor.gov/taxes-forms/individual-income-tax/filing-topics/bailey-decision-concerning-federal-state-and-local-retirement-benefits
- NC when/where/how to file (D-400): https://www.ncdor.gov/taxes-forms/individual-income-tax/when-where-and-how-file-your-north-carolina-return
- NC forms & instructions (D-400/D-401): https://www.ncdor.gov/taxes-forms/individual-income-tax/individual-income-tax-forms-instructions

### Bracket-table cross-check
- Tax Foundation 2025 brackets: https://taxfoundation.org/data/all/federal/2025-tax-brackets/
- Tax Foundation 2026 brackets: https://taxfoundation.org/data/all/federal/2026-tax-brackets/

> **Items to re-verify (were not lockable to a single primary HTML page at
> research time):** OBBBA **senior deduction** ($6,000, TY2025–2028, MAGI
> phase-out), **no-tax-on-tips / overtime** deductions (caps & years), the new
> **SALT cap** amount and phasedown, and the **$1,700 Additional CTC** refundable
> cap — confirm each on irs.gov before relying. The NC **TY2026 standard
> deduction** and NC **capital-gains** treatment (inferred from the single-rate
> statute) likewise warrant a quick ncdor.gov check.
