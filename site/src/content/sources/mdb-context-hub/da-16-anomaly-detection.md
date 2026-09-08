---
title: "anomaly detection"
description: "The discipline of separating 'normal' from 'not normal' when you mostly only have examples of normal. This skill covers the working methods, when each fits, and the gotchas that bite teams in producti"
---

# Anomaly Detection

The discipline of separating "normal" from "not normal" when you mostly only have examples of normal. This skill covers the working methods, when each fits, and the gotchas that bite teams in production.

## When to use this skill

Activate when the user:
- is looking for unusual rows / events / time points
- is setting up monitoring with alerting on a metric stream
- is building fraud / fault / intrusion detection
- needs to compare methods (Isolation Forest vs LOF vs autoencoder)
- needs streaming anomaly detection
- needs to distinguish data drift from anomalies

## When NOT to use this skill

- Forecasting → `da-analytical-methods` (references/da-15-forecasting.md)
- Supervised classification on labeled fraud → `da-analytical-methods` (references/da-7-machine-learning.md)
- Outlier spot-check during cleaning → `da-analytical-methods` (references/da-4-data-cleaning-preparation.md or references/da-5-exploratory-data-analysis.md)
- Causal investigation → `da-analytical-methods` (references/da-12-ab-testing-causal-inference.md)

---

## Framing: three problem types

Before picking a method, name the problem type.

| Type | Question | Example |
|---|---|---|
| **Point anomaly** | Is this single record unusual? | One transaction far above the user's history |
| **Contextual anomaly** | Is this normal value unusual in this context? | 30°C is normal in summer, an anomaly in January |
| **Collective anomaly** | Is this group of records unusual together? | A burst of small transactions that individually look normal |

Methods don't transfer cleanly between types. A z-score finds point anomalies but misses contextual and collective ones. STL-residual analysis handles contextual time-series anomalies. Sequence models or windowed statistics handle collective.

---

## Statistical methods (univariate, fast, interpretable)

### z-score

`z = (x - μ) / σ`. Flag if `|z| > 3`. Assumes approximately normal; sensitive to the very outliers you're trying to find (μ and σ get pulled).

### Modified z-score (MAD-based)

`z_mod = 0.6745 × (x - median) / MAD`. Flag if `|z_mod| > 3.5` (Iglewicz & Hoaglin 1993). Robust to outliers because median and MAD don't move much. **Use this instead of plain z-score.**

### Grubbs's test

Tests whether the single most extreme point is an outlier under a normality assumption. Tests one at a time; for multiple outliers use ESD.

### Generalized ESD (Rosner 1983)

Iteratively tests up to k suspected outliers in a normal sample. Computes test statistic for the most extreme point, removes it, repeats.

### IQR / Tukey fences

`lower = Q1 - 1.5·IQR`, `upper = Q3 + 1.5·IQR`. Used by boxplots. Robust to outliers, no distribution assumption, but not statistically calibrated.

**When to reach for each:** modified z-score for clean tabular numerical data, IQR for a quick exploratory boxplot, ESD for the formal "are there k outliers in this sample" answer, Grubbs only for the single-outlier case.

---

## Time-series methods

### Control charts: CUSUM and EWMA

- **CUSUM** (Cumulative Sum) — accumulates deviations from the target. Triggers when the cumulative sum exceeds a threshold. Best for small persistent shifts.
- **EWMA** (Exponentially Weighted Moving Average) — exponentially-weighted average crosses control limits. Smoother than CUSUM; good for medium drifts.
- **Shewhart 3σ** — the classic; sensitive to single large jumps but slow on small persistent shifts.

These come from manufacturing SPC (statistical process control) but transfer to any monitored stream.

### Change-point detection

When the *distribution* changes, not just one point.

| Method | Type | Notes |
|---|---|---|
| **PELT** (Pruned Exact Linear Time) | Offline | Finds optimal partition in O(n) under assumptions |
| **Binary Segmentation** | Offline | Greedy; fast but approximate |
| **Bayesian Online CPD** (BOCPD) | Online | Maintains posterior over run length |
| **`ruptures`** (Python) | Library | Implements PELT, BinSeg, Window, Dynp |

Use change-point detection when "anomaly" really means "this segment is from a different distribution than the previous segment."

### STL residual analysis

Decompose the series via STL (`statsmodels.tsa.seasonal.STL`) into trend + seasonality + residual. Apply a point-anomaly method to the residual. This automatically handles seasonality, so you don't false-alarm on every December spike.

---

## Distance and density methods (multivariate)

### k-NN distance

Distance to the k-th nearest neighbor. Big distance = anomaly. Simple, works in low dimensions, scales badly past ~50 features.

### LOF — Local Outlier Factor (Breunig 2000)

A point's anomaly score is the ratio of its local density to the local density of its neighbors. Catches anomalies in non-uniform-density data where global thresholds fail. Implemented in scikit-learn.

### DBSCAN as outlier detector

Density-based clustering — anything not in a dense region is a "noise" point. Outlier detection is a free side-effect. Sensitive to `eps` and `min_samples`.

---

## Tree-based methods

### Isolation Forest (Liu, Ting, Zhou 2008)

Build random trees by randomly picking a feature and a random split until each point is isolated. Anomalies have shorter average path lengths because random splits separate them quickly. Linear time, constant memory, **the default for tabular numerical data above a few features**.

Hyperparameters: `n_estimators=100` (default fine), `max_samples=256` (canonical), `contamination` (your guess at anomaly rate; affects threshold).

### Extended Isolation Forest (Hariri et al 2019)

Fixes a known IF flaw: standard IF only splits on axes, biasing it on rotated data. EIF allows arbitrary hyperplane splits.

---

## One-class methods

### One-Class SVM

Fits a boundary that encloses most of the training data. Anomalies fall outside the boundary. Sensitive to the `nu` parameter and kernel choice. Slow on > ~10k samples.

### Mahalanobis distance / elliptic envelope

Assumes Gaussian distribution; fits a covariance matrix; distance from the center weighted by the inverse covariance. Works on roughly elliptical data. `EllipticEnvelope` in scikit-learn uses robust covariance estimation (MCD — Minimum Covariance Determinant) so it isn't pulled by the very outliers you're trying to find.

---

## Deep learning methods

### Autoencoder reconstruction error

Train an autoencoder on normal data. At inference, reconstruction error = anomaly score. Works because the model never learned to reconstruct rare patterns.

### VAE (Variational Autoencoder)

Same idea but with a probabilistic latent space. The likelihood of the data under the model is the anomaly score.

### GAN-based (AnoGAN, GANomaly, f-AnoGAN)

Train a GAN on normal data. Anomaly score from the difference between the input and the closest sample the generator can produce.

### Transformer-based and time-series foundation models

2024-2026 frontier. Models like Anomaly-Transformer, TranAD, and time-series foundation models (Chronos, Moirai, TimesFM) can be adapted for anomaly detection by computing prediction error or likelihood under the model.

**When deep learning is overkill:** if your data is < 10 features and < 100k rows, Isolation Forest or LOF will outperform a neural net while running in seconds. Reach for deep methods when you have images, audio, dense time series with structure, or millions of features.

---

## Streaming and real-time

In production you rarely batch-score; you score one event at a time.

| Tool | Strength |
|---|---|
| **River** (Python) | Online ML library; streaming anomaly detectors (Half-Space Trees, KMeans-based, GMM-based) |
| **PySAD** | Streaming anomaly detection focused library |
| **Spark / Flink** | Apply batch detectors to micro-batches |
| **Adaptive ESD** | Streaming Grubbs / ESD variants |

Production constraints:
- **Memory** — streaming detectors must bound state (e.g., reservoir sampling)
- **Latency** — score in microseconds for fraud, milliseconds for monitoring
- **Concept drift** — distribution shifts over time; the detector must adapt

---

## Drift vs anomaly — the critical distinction

These look similar but require different responses.

| | Anomaly | Drift |
|---|---|---|
| What it is | A point or window unusual under the current distribution | The distribution itself has changed |
| Time scale | Spike (seconds-hours) | Gradual or step change (days-months) |
| Right response | Investigate the event | Retrain the model / update the baseline |
| Detection method | Anomaly methods above | Statistical tests on distributions (KS, χ², PSI), or specialized drift detectors |
| Failure mode if confused | Spend resources investigating a baseline shift | Miss a real anomaly because the baseline is wrong |

Production ML systems need **both**. Most monitoring failures come from confusing them. For full drift tooling (PSI, KS, NannyML, Evidently), see `da-analytical-methods` (references/da-42-ml-model-monitoring.md).

---

## Choosing a method — decision matrix

| Situation | Recommended method |
|---|---|
| Single numerical column, < 100k rows | Modified z-score (MAD) |
| Boxplot in a notebook | IQR / Tukey fences |
| Tabular, 5-50 features, < 1M rows | **Isolation Forest** (default) |
| Tabular with non-uniform density | LOF |
| Roughly Gaussian features | EllipticEnvelope (MCD) |
| Time series with seasonality | STL decomposition + anomaly on residuals |
| Time series, small persistent shifts | CUSUM |
| Time series, distribution change | PELT / BOCPD change-point |
| Streaming with bounded memory | River / PySAD (Half-Space Trees) |
| High-dim images, audio, dense series | Autoencoder or transformer-based |
| Labeled fraud data available | Supervised classifier (da-analytical-methods, references/da-7-machine-learning.md), not unsupervised AD |

---

## Evaluating anomaly detectors

The hard part: by definition, anomalies are rare, so you usually don't have labeled validation data.

When you do have labels (post-hoc): use precision-recall, F1, PR-AUC. Accuracy is meaningless because the class is imbalanced.

When you don't have labels: use known synthetic anomalies, or use the time-shifted holdout where you assume the holdout had a similar anomaly rate. Or measure proxy metrics like "% of incidents the system caught."

**The threshold choice** is usually the hardest decision. The model emits a score; you choose where to cut. Tune for the cost-benefit ratio: if a false positive costs 1 minute of investigation and a false negative costs $10k, the threshold should be aggressive.

---

## Anti-patterns

1. **Z-score on data full of outliers** — μ and σ are dragged; use modified z (MAD).
2. **Single threshold on a seasonal series** — false-alarms on every Monday or every December.
3. **Confusing drift with anomaly** — retraining on the anomaly, or investigating drift as if it were an event.
4. **Autoencoder for 5-feature tabular** — overkill; IF will outperform with seconds of compute.
5. **No baseline period** — declaring everything new "anomalous" when you simply lack history.
6. **Treating anomaly score as a probability** — most methods produce uncalibrated scores; pick a threshold from PR data, not "p > 0.05".
7. **Alert fatigue** — a noisy detector trains the on-call to ignore it. Tune precision before deploying.
8. **Forgetting concept drift** — the model that worked last quarter no longer represents "normal."

---

## References

1. Chandola, V., Banerjee, A., & Kumar, V. (2009). "Anomaly Detection: A Survey." *ACM Computing Surveys*. The canonical survey.
2. Iglewicz, B. & Hoaglin, D. (1993). *How to Detect and Handle Outliers*.
3. Rosner, B. (1983). "Percentage Points for a Generalized ESD Many-Outlier Procedure." *Technometrics*.
4. Breunig, M. M. et al. (2000). "LOF: Identifying Density-Based Local Outliers." *SIGMOD*.
5. Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008). "Isolation Forest." *ICDM*.
6. Hariri, S., Carrasco Kind, M., Brunner, R. J. (2019). "Extended Isolation Forest." *IEEE TKDE*.
7. Truong, C., Oudre, L., & Vayatis, N. (2020). "Selective review of offline change point detection methods." *Signal Processing*. (PELT survey.)
8. Adams, R. P. & MacKay, D. J. C. (2007). "Bayesian Online Changepoint Detection." arXiv:0710.3742.
9. River (online ML) — https://riverml.xyz/
10. PySAD — https://github.com/selimfirat/pysad
11. Xu, J. et al. (2021). "Anomaly Transformer." ICLR.
12. Schölkopf, B. et al. (2001). "Estimating the Support of a High-Dimensional Distribution." (One-Class SVM.)
13. scikit-learn outlier detection — https://scikit-learn.org/stable/modules/outlier_detection.html
14. Evidently AI drift detection guide — https://docs.evidentlyai.com/ (drift-vs-anomaly framing).
