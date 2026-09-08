---
title: "Machine Learning"
description: "Machine learning is the curriculum step where the analyst stops merely describing a sample and starts building a function that generalizes from data to unseen inputs. Section 6 (da-6-statistical-model"
---

# Machine Learning (Data Analysis Curriculum, Section 7)

Machine learning is the curriculum step where the analyst stops merely describing a sample and starts building a function that generalizes from data to unseen inputs. Section 6 (`da-6-statistical-modeling`) covered parametric statistical models grounded in explicit probabilistic assumptions. This section widens the lens to algorithms that learn flexible, often non-parametric mappings from data — and to the engineering scaffolding (tuning, evaluation, deployment, monitoring) that turns a trained model into a system that keeps working.

This skill is the curriculum reference for the seventh section of the data analysis path. It is intentionally broad: it sketches the territory and points to the deeper skills you should pull in for any specific build.

## Part 1 — Machine Learning Taxonomy

### 1.1 Three (now four) classical paradigms

- **Supervised learning.** Input–output pairs `(x, y)`. Sub-shapes: classification (discrete `y`) and regression (continuous `y`).
- **Unsupervised learning.** No labels. Discovers clusters (k-means, DBSCAN, HDBSCAN), topics (LDA, NMF), manifolds (PCA, t-SNE, UMAP, autoencoders), density (KDE, GMM), or anomalies (isolation forest, one-class SVM).
- **Reinforcement learning.** Agent → environment → reward; optimizes policy `pi(a | s)`. Modern flavors: PPO, GRPO, DQN. RLHF/RLAIF align LLMs.
- **Self-supervised learning.** Labels constructed from the data: next-token prediction (GPT/Claude/Gemini), masked LM (BERT), masked patch (DINO/MAE), contrastive (CLIP). The engine behind every foundation model.

Edge shapes: semi-supervised (small labeled + large unlabeled), active learning (model picks next labels).

### 1.2 Bias-variance tradeoff

`E[(y - f_hat(x))^2] = Bias[f_hat(x)]^2 + Var[f_hat(x)] + sigma^2`

Bias (underfitting) drops with capacity; variance (overfitting) rises. Regularization, more data, and ensembling trade variance for some bias. The classical U-curve is an idealization — in over-parameterized regimes (most modern DL) test error follows "double descent": rises near the interpolation threshold, then falls again as capacity grows.

### 1.3 Regularization toolbox

L1 (Lasso, feature selection), L2 (Ridge / weight decay, default in DL), ElasticNet, Dropout (ensemble averaging), early stopping, data augmentation (often the strongest), label smoothing, normalization layers.

### 1.4 Classical model zoo

Linear/logistic regression, decision trees, random forests, gradient-boosted trees (XGBoost/LightGBM/CatBoost still win most tabular competitions in 2026), SVM, kNN, Naive Bayes. On tabular: start with a GBT.

## Part 2 — Deep Learning Fundamentals

### 2.1 CNNs

Grid-structured data. Convolution (weight sharing, translation equivariance), pooling, hierarchical feature learning. LeNet → AlexNet → VGG → ResNet (residual connections) → EfficientNet → ConvNeXt. Still competitive on edge devices, limited-data medical imaging, and as hybrid backbones.

### 2.2 RNNs

Sequential state `h_t = f(x_t, h_{t-1})`. Vanilla RNNs (vanishing gradients), LSTM (gated cell, workhorse 2014–2018), GRU (simpler, comparable), bidirectional. Mostly displaced by Transformers; still useful for streaming inference, tiny edge time-series, and as the conceptual ancestor of state-space models (Mamba, S4, S6) that scale linearly in sequence length.

### 2.3 Architecture choice

Transformer is the 2026 default, but consider inductive bias (CNNs encode locality), sequence length (attention is quadratic — sliding window/sparse/linear/SSMs win on long contexts), and latency budget (a 7B Transformer is overkill for keyword-spotting on a watch).

## Part 3 — Transformers and Foundation Models

### 3.1 The Transformer

*Attention Is All You Need* (Vaswani et al., 2017). Per token: query `Q`, key `K`, value `V`. Attention = `softmax(QK^T / sqrt(d_k)) V`. Multi-head runs several attention ops in parallel. Parallelizable training, one-hop long-range dependencies, modality-agnostic (text, images via ViT, audio via Whisper, proteins via AlphaFold).

### 3.2 Foundation model paradigm

Pretrain large on broad data with self-supervision, adapt via: zero-shot prompting, few-shot in-context learning, fine-tuning (full, LoRA/QLoRA, DPO/KTO, RLHF/RLAIF), RAG, tool use / function calling. 2024–2026 era is agent-shaped systems built around pretrained foundations.

## Part 4 — Frontier LLM Landscape (May 2026)

| Model | Provider | Strength |
| --- | --- | --- |
| Claude Opus 4.7 | Anthropic | Agentic coding, SWE-bench Verified 87.6%, 3.75MP image input |
| GPT-5.5 | OpenAI | Top overall Intelligence Index; first ground-up rebuild since GPT-4.5 |
| Gemini 3.1 Pro | Google DeepMind | Scientific reasoning; multimodal (image/audio/video) |
| Llama 4 Scout | Meta | Open weights; 10M-token context |
| Llama 4 / Muse Spark | Meta | Intelligence Index ~52 |
| DeepSeek V3.2 | DeepSeek | Best value-per-dollar at frontier |
| Grok 4 | xAI | Leads raw SWE-bench |
| GLM-5.1 | Zhipu | Open-source coding |

Selection heuristics: agentic coding → Claude Opus 4.7; general reasoning → GPT-5.5; multimodal → Gemini 3.1 Pro; self-hosted → Llama 4; budget/high-volume → DeepSeek V3.2 or smaller specialists. Use LiteLLM/OpenRouter for per-request routing. Treat the LLM as replaceable, not a vendor commitment.

## Part 5 — Hyperparameter Tuning

### 5.1 Search strategies

Manual, grid (only ≤3 hyperparams), random (dominates grid when few hyperparams matter), Bayesian optimization (GP or TPE + EI/UCB acquisition, default for 10–100 trials), HyperBand (successive halving), BOHB (BO + HyperBand, production default for DL), PBT (population-based, learns schedules).

### 5.2 Tooling (2026)

Optuna (Python-native, TPE + pruning, individual default), Ray Tune (distributed, all algorithms above), Weights & Biases Sweeps (if W&B is your tracker), KerasTuner/AutoGluon/FLAML (AutoML), Vizier/SigOpt (hosted).

### 5.3 Cheatsheet

Tune on validation, never on test. Nested CV when small. Log-uniform LR/weight decay. Tune learning rate first. Cap wall-clock per trial. Re-tune on dataset/architecture/optimizer change. Save trial history for `get_param_importances`.

## Part 6 — Evaluation Methodology

### 6.1 Splits

Train/val/test (test touched once). k-fold CV, stratified k-fold (imbalanced), group k-fold (leakage by group ID), time-series splits (never shuffle), nested CV (small data + many hyperparams).

### 6.2 Classification metrics

Accuracy (misleading on imbalance). Precision `TP/(TP+FP)` — optimize when false positives expensive. Recall `TP/(TP+FN)` — optimize when false negatives expensive. F1 harmonic mean. F-beta. ROC-AUC (insensitive to class balance). PR-AUC (preferred when positive class rare). Log-loss / cross-entropy (proper scoring rule). Calibration plots + Brier score. Macro/weighted/micro F1 for multi-class.

### 6.3 Regression metrics

MAE (robust), RMSE (penalizes outliers), MAPE / sMAPE, R^2, quantile / pinball loss.

### 6.4 Ranking metrics

MAP@k, NDCG@k, MRR, Hit-rate@k.

### 6.5 LLM evaluation

MMLU (saturated — frontier >90%), MT-Bench (multi-turn, LLM-as-judge), HELM (Stanford CRFM; accuracy, calibration, robustness, fairness, bias, toxicity, efficiency), Chatbot Arena (Elo from pairwise preference), SWE-bench / SWE-bench Verified / SWE-bench Pro (real GitHub issues; Claude Opus 4.7 leads Verified at 87.6%), HumanEval / MBPP / LiveCodeBench, GPQA / ARC-AGI / FrontierMath (not yet saturated), domain-specific (MedQA, LegalBench, FinanceBench, MMMU).

### 6.6 LLM-as-judge

Pros: fast, scalable. Cons: position bias, self-preference, verbosity bias, rubric drift. Mitigations: randomize position; use different judge family than model under test; calibrate against small human-labeled gold set; prefer pairwise to absolute scoring. Tools: G-Eval, DeepEval, Patronus, Braintrust.

## Part 7 — MLOps

### 7.1 Experiment tracking

MLflow (OSS default), Weights & Biases (commercial), Neptune.ai / Comet, DVC + Git (small teams). Log: code hash, dataset hash, hyperparams, environment, train/val metrics, artifact, evaluation report.

### 7.2 Drift

Covariate shift `P(x)` changes, concept drift `P(y|x)` changes, label drift `P(y)` changes. Detection: PSI, JS divergence, KL divergence, KS test, chi-squared, Wasserstein. When labels arrive late, monitor proxies (prediction distribution, confidence). Tools: Evidently AI (best OSS), WhyLabs, Arize, Fiddler. W&B 2023 data: 62% of orgs see meaningful degradation within 12 months without monitoring.

### 7.3 Train-serve skew

Distinct from drift (drift = world changes; skew = code inconsistency). Feature parity (use a feature store: Feast, Tecton, Hopsworks). Schema parity (TFX SchemaGen, Great Expectations, Pandera). Lookup parity. Time-leakage (use as-of timestamps).

### 7.4 Deployment

Shadow, canary, A/B (tied to business metric), multi-armed bandit, champion/challenger.

### 7.5 Retraining triggers

Scheduled, drift-triggered, performance-triggered, continuous.

### 7.6 Reproducibility

Pinned deps (uv.lock/poetry.lock/conda-lock), hashed datasets (DVC, LakeFS, Delta), fixed seeds (not bit-identical on GPU), containerized training, MLflow run recording.

## Anti-Patterns

- Tuning on the test set
- Mean accuracy on imbalanced data
- Different splits across compared models
- Shuffling a time series
- Ignoring calibration
- Validating the model in isolation rather than the pipeline
- Vibes-only LLM eval
- Treating the LLM as a fixed dependency
- Skipping monitoring because "it works in dev"

## Related Skills

`da-1-foundations-theory`, `da-1-3-probability-theory`, `da-1-4-statistical-inference-foundations`, `da-1-5-information-theory`, `da-1-6-epistemology-of-data`, `da-4-data-cleaning-preparation`, `da-6-statistical-modeling`, `da-8-data-visualization`, `da-9-reporting-communication`, `prompt-engineering`, `llm-context-engineering`, `rag-architecture`, `mongodb-atlas-vector-search`, `mongodb-search-ai`, `ai-datastores`, `ai-languages`, `llm-models`, `mongodb-atlas-stream-processing`.

## References

- Bergstra & Bengio (2012). Random Search for Hyperparameter Optimization. JMLR.
- Vaswani et al. (2017). Attention Is All You Need. NeurIPS.
- Liang et al. (2022). HELM. Stanford CRFM.
- Chiang et al. (2023). Chatbot Arena.
- Belkin et al. (2019). Double descent. PNAS.
- Hendrycks et al. (2021). MMLU. ICLR.
- Jimenez et al. (2024). SWE-bench. ICLR.
- LM Council, Vellum, Artificial Analysis — live LLM leaderboards (May 2026).
- Anthropic / OpenAI / Google DeepMind / Meta / DeepSeek / xAI / Zhipu — model release notes, April–May 2026.
- Evidently AI, Weights & Biases — MLOps drift industry reports (2023–2026).
