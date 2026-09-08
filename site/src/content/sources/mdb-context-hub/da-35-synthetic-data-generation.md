---
title: "Synthetic Data Generation"
description: "Synthetic data is artificial data produced by a model fit to real data, designed to reproduce the real data's statistical properties (marginals, correlations, joint structure) without being a copy of"
---

# Synthetic Data Generation

Synthetic data is artificial data produced by a model fit to real data, designed to reproduce the real data's statistical properties (marginals, correlations, joint structure) without being a copy of any real record. The goal is to make synthetic records *useful* for a downstream task while breaking the one-to-one link to real individuals.

This skill treats synthetic data generation as a discipline: when to use it, which generator to reach for, how to make it private, and most importantly how to prove it is good enough on the three axes that always compete: fidelity, utility, privacy.

## When to use this skill

Use it when the task is to *create* data rather than analyze existing data: share data you cannot share in raw form, augment a too-small or imbalanced training set, populate a test/dev/CI environment without production PII, or release a public benchmark from a sensitive source.

Do **not** use it for plain class-rebalancing with off-the-shelf SMOTE (data-prep step, see da-4), abstract differential-privacy/k-anonymity theory (da-11), or feature encoding (da-17). Those skills are adjacent; this one owns the generation pipeline and its evaluation.

## Core concepts

### 1. Why synthetic data
- **Privacy / data sharing.** Replace a protected dataset with a synthetic surrogate. Gartner projected synthetic data would let organizations avoid 70% of privacy-violation sanctions by 2025, and estimated ~60% of AI/analytics data in 2024 would be synthetic (Gartner 2024; MIT Sloan 2023).
- **Augmentation.** Fill gaps, enlarge small datasets, balance rare classes, simulate scarce scenarios (fraud, failure).
- **Testing / dev / CI.** Populate non-prod at scale with realistic-but-fake records (Gartner 2024 Data Masking Market Guide).
- **Class rebalancing.** Generate minority-class examples to de-skew a classifier.

Inference, not fact: "synthetic surpasses real by 2030" is a vendor/analyst projection. Treat market-size and adoption numbers as directional.

### 2. Tabular synthesis methods
Tabular is the hard case: mixed types, non-Gaussian/multimodal continuous columns, imbalanced categoricals.
- **Gaussian copula.** Transform each column to standard-normal via its CDF, fit a multivariate Gaussian for correlation structure, sample, invert to original margins. Fast, transparent, stable on small data; weak on highly non-linear dependencies (SDV docs).
- **CTGAN (Conditional Tabular GAN).** Mode-specific normalization for multimodal continuous columns + conditional generator + training-by-sampling for imbalanced categoricals. Beat Bayesian-network and prior GAN baselines on >=87% of test datasets (Xu et al., NeurIPS 2019).
- **TVAE (Tabular VAE).** VAE from the same NeurIPS 2019 paper; strong on smaller datasets, trains more stably than a GAN.
- **CopulaGAN.** Hybrid applying the copula transform before GAN modeling (experimental in SDV).
- **CART / sequential synthesis.** Non-deep classical approach (R synthpop): synthesize one column at a time conditioned on already-synthesized columns via CART trees. Interpretable, fast, official-statistics default.

### 3. Deep generative methods
- **GANs.** Adversarial generator vs discriminator; high fidelity but training instability and mode collapse. CTGAN is the tabular workhorse.
- **VAEs.** Encoder/decoder with latent prior; smoother, more stable, good diversity. TVAE is the tabular instance.
- **Diffusion.** Iterative denoising from a Gaussian prior. TabDDPM (ICML 2023) handles numerical + categorical features and beat prior SOTA on several benchmarks; concurrent STaSy, CoDi; later TabSyn, TabDiff (Kotelnikov et al., ICML 2023).

### 4. Class imbalance: resampling vs generative
- **SMOTE** interpolates minority points along segments to k nearest minority neighbors (local info only).
- **ADASYN** adapts the number of synthetic points per minority sample by density, generating more in harder-to-learn regions.
- **Generative (GAN/VAE/diffusion)** captures complex non-linear joint structure SMOTE/ADASYN miss; hybrids like SMOTE->GAN refine unrealistic SMOTE points (MDPI Mathematics 2023; SMOTified-GAN 2021).
- **Rule of thumb.** Low-dim numeric, small budget -> SMOTE/ADASYN. High-cardinality categoricals, non-linear interactions, or privacy need -> generative. SMOTE before the train/test split leaks information; resample inside the CV fold only.

### 5. Differentially private synthesis
Plain synthetic data is **not** automatically private; formal guarantees require DP built into training.
- **DP-GAN / DP-SGD GANs.** Calibrated noise + gradient clipping on the discriminator; post-processing theorem makes the generator DP.
- **PATE-GAN.** PATE ensemble of teacher discriminators trains a student via noisy aggregated votes; DP by post-processing, often better utility than DP-GAN at equal epsilon (Jordon, Yoon, van der Schaar, ICLR 2019).
- **Marginal-based (PrivBayes, MST).** Privately measure low-order marginals (Laplace/Gaussian mechanism), then reconstruct a distribution: a Bayesian network (PrivBayes, Zhang et al. 2017) or a graphical model over a maximum-spanning-tree of marginals (MST). MST won the 2018 NIST DP Synthetic Data Challenge; both strong against membership inference with high utility (McKenna, Miklau, Sheldon 2021; NIST).
- **SmartNoise (OpenDP).** Microsoft + Harvard toolkit; smartnoise-synth exposes DP synthesizers (MST, PrivBayes, AIM) with a uniform fit()/sample() API (Microsoft 2021).

Caveat: high epsilon hollows out the guarantee. MST/PrivBayes at high epsilon still leak (arXiv 2402.06699, 2024). DP is only as strong as the epsilon you actually set.

### 6. Tools & frameworks
- **SDV (Synthetic Data Vault)** Python one-stop: single-table (GaussianCopula, CTGAN, TVAE, CopulaGAN), multi-table (HMA), sequential (PAR); metadata-driven fit()/sample().
- **SDMetrics** SDV evaluation: Quality Report (column shapes, column-pair trends), Diagnostic Report (validity/structure), privacy metrics.
- **CTGAN (sdv-dev/ctgan)** standalone CTGAN + TVAE.
- **synthcity** van der Schaar lab; tabular/time-series/survival + privacy benchmarks.
- **SmartNoise-synth (OpenDP)** DP synthesizers with formal guarantees.
- **imbalanced-learn** SMOTE/ADASYN variants.
- **synthpop (R)** CART/sequential synthesis.

### 7. Evaluation: fidelity vs utility vs privacy
The three axes trade off (especially privacy vs fidelity/utility under DP). Measure all three.
- **Fidelity** (looks like real): per-column shape (KS continuous, total-variation/chi-sq categorical), pairwise correlation/contingency similarity, validity/structure (SDMetrics).
- **Utility** (works like real): TSTR (Train on Synthetic, Test on Real) vs TRTR (train-real-test-real); TSTR ~= TRTR means high utility (AWS ML blog 2023).
- **Privacy** (attacker recovery): Distance to Closest Record (DCR) flags near-copies; Membership Inference Attack (MIA) tests whether an adversary can tell a record was in training (Frontiers Digital Health 2025).

### 8. Text & image synthesis (overview)
- **Text.** Instruction-tuned LLMs generate synthetic text/labels (DataGen, MagPie); quality/diversity and label noise are limits; DP-via-API (Aug-PE/Private Evolution) exists (2023-24).
- **Images.** GANs gave limited augmentation benefit; diffusion era (Stable Diffusion, DALL-E, Imagen) sharply improved fidelity and dropped per-image cost (2024-25 reviews).

### 9. Regulatory context
Synthetic data is **not automatically anonymous** or out of GDPR scope. Fully synthetic data meeting the anonymisation bar escapes GDPR; partially synthetic data usually remains personal data. ICO's March 2025 anonymisation guidance: effective anonymisation is a high bar requiring a documented re-identification-risk assessment (GDPR Local; RPC 2025; NIST). Treat a privacy claim as something you must *measure* (DCR + MIA, ideally under a DP budget), not something the word "synthetic" grants.

## Methodology (end-to-end pipeline)
1. **Define the goal first** (privacy share / augmentation / test data / rebalancing) — sets which axis you optimize and which gates you must pass.
2. **Profile and build metadata** (types, keys, datetime formats, constraints). Bad metadata is the #1 cause of bad output.
3. **Split before you fit** — hold out a real test set before training so TSTR and MIA are honest.
4. **Pick a generator by data + constraint** — copula baseline; escalate to CTGAN/TVAE; diffusion (TabDDPM) for highest fidelity; switch to a DP synthesizer (PATE-GAN, MST/PrivBayes via SmartNoise) the moment a formal privacy guarantee is required.
5. **Fit, then enforce constraints** — apply business rules / valid ranges; reject or post-process invalid rows.
6. **Evaluate on all three axes** — fidelity, utility (TSTR vs TRTR), privacy (DCR + MIA). For DP, report epsilon.
7. **Iterate against the binding constraint** — privacy fails: lower epsilon/regularize; utility fails: more capacity/epochs or change family. Expect to trade.
8. **Document** generator, hyperparameters, epsilon, seed, metrics, and the re-identification-risk assessment (required for any GDPR/anonymisation claim).

## Practical patterns
- Copula-first ladder; don't start with a GAN.
- Resample inside the fold (never before the split).
- DP by construction, not post-hoc filtering.
- Conditional sampling (CTGAN/SDV) for rare classes.
- Report TSTR next to TRTR; the gap is the signal.
- Keep metadata in version control; regenerate from it.

## Anti-patterns
- Calling synthetic data "anonymous" with no DCR + MIA test.
- Evaluating fidelity only (a perfect KS can still memorize records or be useless downstream).
- SMOTE before the split / on test data (leakage).
- Treating high epsilon as "private" (MST/PrivBayes leak at high epsilon).
- GAN by default on small/simple data (mode collapse; copula or TVAE is faster/better).
- Ignoring constraints/keys (synthesizers emit out-of-range values and broken keys unless constrained).
- One synthetic draw as ground truth (sample multiple; metrics vary, especially for GANs).

## Troubleshooting
- **Mode collapse / low diversity (GAN):** switch to TVAE/diffusion; add conditional generator; tune batch size / PacGAN packing.
- **Categorical cardinality blows up training:** group rare categories or use copula/CART.
- **DP output useless (utility floor):** epsilon too small or marginals too high-order; raise epsilon within policy, lower marginal order (MST), or swap PATE-GAN <-> marginal-based.
- **TSTR far worse than TRTR:** fidelity gap in relied-on columns; inspect per-column shape + correlation reports.
- **Synthetic rows duplicate real rows (DCR ~0):** overfitting; reduce epochs/capacity, add DP, or add training data.
- **Invalid rows (out of range, broken keys):** add SDV constraints/metadata; post-process and re-validate.

## References
- Xu et al. — Modeling Tabular Data using Conditional GAN (CTGAN), NeurIPS 2019. https://proceedings.neurips.cc/paper_files/paper/2019/file/254ed7d2de3b23ab10936522dd547b78-Paper.pdf
- Jordon, Yoon, van der Schaar — PATE-GAN, ICLR 2019. https://openreview.net/pdf?id=S1zk9iRqF7
- Kotelnikov et al. — TabDDPM, ICML 2023. https://proceedings.mlr.press/v202/kotelnikov23a/kotelnikov23a.pdf
- McKenna, Miklau, Sheldon — Winning the NIST Contest: MST, 2021. https://arxiv.org/pdf/2301.08844
- Zhang et al. — PrivBayes, ACM TODS 2017. https://dl.acm.org/doi/10.1145/3134428
- SDV docs & synthesizers. https://docs.sdv.dev/sdv | https://github.com/sdv-dev/SDV | https://github.com/sdv-dev/CTGAN
- SmartNoise / OpenDP. https://opensource.microsoft.com/blog/2021/02/18/create-privacy-preserving-synthetic-data-for-machine-learning-with-smartnoise/ | https://docs.smartnoise.org/synth/index.html
- NIST Privacy Collaborative Research Cycle. https://pages.nist.gov/privacy_collaborative_research_cycle/pages/techniques.html
- AWS ML Blog — fidelity/utility/privacy. https://aws.amazon.com/blogs/machine-learning/how-to-evaluate-the-quality-of-the-synthetic-data-measuring-from-the-perspective-of-fidelity-utility-and-privacy/
- Frontiers Digital Health — synthetic tabular health eval, 2025. https://www.frontiersin.org/journals/digital-health/articles/10.3389/fdgth.2025.1576290/full
- High Epsilon Vulnerabilities in MST and PrivBayes, 2024. https://arxiv.org/html/2402.06699v1
- MDPI Mathematics — GANs vs SMOTE, 2023. https://www.mdpi.com/2227-7390/11/16/3605 | SMOTified-GAN 2021. https://arxiv.org/pdf/2108.03235
- imbalanced-learn SMOTE & ADASYN. https://machinelearningmastery.com/smote-oversampling-for-imbalanced-classification/
- Gartner — Safeguarding Privacy with Synthetic Data, 2024. https://www.gartner.com/en/newsroom/press-releases/2024-06-27-safeguarding-privacy-with-synthetic-data
- ICO anonymisation guidance, RPC 2025. https://www.rpclegal.com/snapshots/data-protection/summer-2025/ico-publishes-new-guidance-on-anonymisation-and-pseudonymisation/
- GDPR Local — Synthetic Data Under GDPR. https://gdprlocal.com/synthetic-data-under-gdpr/
- Synthetic Data in 2024 review. https://www.timlrx.com/blog/synthetic-data-in-2024-progress-opportunities-challenges/
- synthcity. https://arxiv.org/pdf/2301.07573
