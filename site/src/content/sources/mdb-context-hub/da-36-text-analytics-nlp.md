---
title: "Text Analytics and NLP for Analysts"
description: "Applied NLP for turning unstructured text into measurable signal. The audience is an analyst, not an ML engineer: the goal is defensible insight from reviews, support tickets, survey open-ends, call t"
---

# Text Analytics & NLP for Analysts

Applied NLP for turning **unstructured text into measurable signal**. The audience is an analyst, not an ML engineer: the goal is defensible insight from reviews, support tickets, survey open-ends, call transcripts, social posts, and documents — not training novel models. Prefer the simplest method that answers the question; escalate to embeddings/transformers/LLMs only when classical methods fall short.

## Decision guide (start here)

| Question | First reach for | Escalate to |
| --- | --- | --- |
| What words/phrases distinguish these docs? | TF-IDF, c-TF-IDF, KeyBERT | — |
| What themes exist (unlabeled)? | BERTopic (default), LDA/NMF for short/clean corpora | LLM clustering of summaries |
| Are these positive/negative? | VADER (social/short), fine-tuned transformer | aspect-based sentiment |
| Which docs are similar / dedupe / near-search? | sentence-transformers + cosine | cross-encoder rerank |
| Pull people/orgs/dates/products | spaCy NER | spacy-llm / LLM extraction |
| Classify into known labels | TF-IDF + linear model (baseline) → transformer | LLM zero/few-shot |
| Code open-ends against a codebook | deductive: LLM + human validation | embeddings + cluster first |

**Rule of thumb:** establish a cheap, interpretable baseline (TF-IDF + linear model, or VADER) before any transformer or LLM. Report the baseline number even when you ship the fancier model — it is your sanity check and your cost/latency benchmark.

## Core concepts

### 1. Preprocessing, tokenization, normalization
The decisions here silently determine every downstream result.
- **Tokenization**: splitting into tokens (words, subwords, sentences). spaCy and NLTK do linguistic word/sentence tokenization; transformers use subword tokenizers (WordPiece/BPE/SentencePiece) — never lowercase or strip punctuation before a transformer tokenizer, it expects raw text.
- **Normalization**: lowercasing, Unicode normalization (NFC/NFKC), accent folding, contraction expansion, whitespace cleanup.
- **Stopword removal & stemming/lemmatization**: helps bag-of-words / topic models; *harmful* for embeddings and transformers, which need full context. Lemmatization (spaCy) is preferred over crude stemming (Porter/Snowball) when you keep tokens human-readable.
- **What to keep**: for sentiment, keep negations, emojis, intensifiers, ALL-CAPS — VADER and good models use them as signal.
- **Pitfall**: applying the bag-of-words preprocessing recipe (lowercase, de-punct, stem, strip stopwords) before embedding/transformer steps destroys signal.

### 2. Bag-of-words, TF-IDF, n-grams
- **BoW / Count**: document = vector of token counts. Simple, sparse, ignores order.
- **TF-IDF**: down-weights terms common across the corpus, up-weights distinctive terms. `TfidfVectorizer` in scikit-learn is the analyst's workhorse for distinctive-term and baseline-classifier work.
- **n-grams**: capture short phrases ("not good", "customer service") that unigrams miss. Set `ngram_range=(1,2)` (sometimes `(1,3)`); watch dimensionality blow-up — use `min_df`/`max_df` and `max_features`.
- **Still relevant in 2026**: cheap, transparent, fast, and a strong classification baseline. Use it before anything heavier.

### 3. Topic modeling: LDA, NMF, BERTopic
- **LDA** (Latent Dirichlet Allocation, Gensim/scikit-learn): probabilistic, each doc = mixture of topics; needs `num_topics` chosen up front; works best on longer, cleaned text; tune with coherence (c_v / u_mass).
- **NMF** (scikit-learn, on TF-IDF): deterministic-ish matrix factorization; often crisper topics than LDA on short text; also needs k.
- **BERTopic** (MaartenGr): modular pipeline — **embeddings (sentence-transformers) → UMAP (dim reduction) → HDBSCAN (density clustering, auto-detects topic count + outliers) → c-TF-IDF (per-cluster distinctive terms) → optional representation tuning (KeyBERT/MMR/LLM labels)**. Each stage is swappable. Default choice for modern, especially short/noisy, text because it does not force a topic count and handles outliers. Use `reduce_outliers`, `nr_topics` to merge, and pass a fixed `random_state` to UMAP for reproducibility.
- **Choosing**: short/messy/lots of docs → BERTopic; small clean corpus or need probabilistic doc-topic mixtures → LDA/NMF; need speed/transparency → NMF on TF-IDF.

### 4. Sentiment: lexicon (VADER) vs transformer
- **VADER** (Hutto & Gilbert, 2014): lexicon + rule-based, tuned for social media; handles negation, intensifiers, punctuation, emoji, caps. Returns `compound` in [-1, 1] (thresholds ≈ ±0.05). No training, instant, fully transparent, free — ideal first pass on tweets/reviews/short informal text.
- **Transformer** (e.g. fine-tuned BERT/RoBERTa via Hugging Face `pipeline("sentiment-analysis")`): context-aware, handles sarcasm/domain nuance better, but heavier, slower, and can carry positivity/domain bias. Studies consistently rank transformer/Flair > BERT > VADER on correlation with human ratings, with VADER competitive on short informal text and far cheaper.
- **Aspect-based sentiment (ABSA)**: sentiment *per aspect* ("battery good, screen bad") — use when one polarity per doc is too coarse.
- **Analyst guidance**: VADER for fast directional reads and big volumes; transformer when domain/sarcasm matters and you can validate on a labeled sample. Always sanity-check both against a hand-labeled set — domain mismatch (finance, clinical) breaks generic models.

### 5. Named-entity recognition (NER)
- **spaCy**: statistical transition-based NER labeling non-overlapping spans (PERSON, ORG, GPE, DATE, PRODUCT, MONEY, …). `en_core_web_sm/md/lg` for speed, `en_core_web_trf` for accuracy. Add an `EntityRuler` for deterministic patterns (SKUs, ticket IDs) before/after the statistical NER.
- **LLM / spacy-llm**: zero/few-shot extraction of custom entity types without training data; good for niche schemas, but validate and watch for hallucinated spans.
- **Analyst uses**: aggregate mentions of competitors/products/locations, redact PII, link entities for rollups.

### 6. Text classification
- **Baseline**: TF-IDF + linear model (LogisticRegression / LinearSVC) or Naive Bayes. Fast, interpretable, hard to beat on small/medium labeled data.
- **spaCy textcat** (`textcat` mutually-exclusive, `textcat_multilabel` for overlapping labels) for an integrated trainable pipeline.
- **Transformers** (Hugging Face): fine-tune or use zero-shot (`facebook/bart-large-mnli`) when labels are scarce or semantics are subtle.
- **LLM zero/few-shot**: fastest path to a working classifier with no training data; pin the label set, give examples, and measure against a gold sample.
- Mind **class imbalance** (use class weights, stratified splits, macro-F1) and **label leakage**.

### 7. Keyword & keyphrase extraction
- **RAKE**: fast, unsupervised, co-occurrence based; great for speed, weak on stopword handling and precision.
- **YAKE**: statistical, single-document, language-agnostic, no corpus needed; can emit near-duplicates.
- **KeyBERT** (MaartenGr): embeds doc and candidate phrases (sentence-transformers) and ranks by cosine similarity; most accurate/contextual; use **MMR / `diversity`** to reduce redundancy. Slower (needs a model).
- **Choose**: RAKE/YAKE for speed and no dependencies; KeyBERT for quality and contextual relevance. Combine with c-TF-IDF for per-cluster keywords inside BERTopic.

### 8. Embeddings & semantic clustering
- **word2vec / GloVe / fastText** (Gensim): static word vectors; useful for analogy, vocabulary exploration, lightweight similarity; no context sensitivity.
- **sentence-transformers (SBERT)**: contextual *sentence/paragraph* embeddings — `all-MiniLM-L6-v2` (fast, 384-d, default) vs `all-mpnet-base-v2` (best quality, slower); 2024+ multilingual & matryoshka/`gte`/`bge` options. Compute with `model.encode()`; compare with `model.similarity()` (cosine).
- **Semantic clustering**: embed → reduce (UMAP/PCA) → cluster (HDBSCAN for variable density + outliers, KMeans when you want fixed k). This is the engine under BERTopic and the analyst's go-to for "group these open-ends by meaning."
- **Document similarity / dedup / near-search**: cosine over embeddings; paraphrase mining for dedup; add a **cross-encoder reranker** when top-k precision matters.

### 9. LLM-assisted qualitative coding & extraction
- **Deductive coding** (codebook exists): prompt the LLM with the codebook + definitions + few-shot examples; LLMs give a systematic, reliable platform for code identification at scale — but **human validation is mandatory**; measure agreement (Cohen's/Krippendorff's) against human coders on a sample.
- **Inductive/exploratory**: embed + cluster first, then have the LLM label/summarize clusters (reflexive thematic analysis); multi-agent (coder/aggregator/reviewer) roles can improve rigor.
- **Structured extraction**: constrain output to JSON schema; extract fields, entities, ratings from free text reliably.
- **Risks**: hallucination, prompt-injection from the text itself (treat corpus content as untrusted data, not instructions), drift across runs (pin model + temperature=0), cost/latency at corpus scale. Performance varies by construct — validate per code.

### 10. Evaluation
- **Classification/sentiment**: accuracy, precision/recall, **macro-F1** (for imbalance), confusion matrix; always hold out a labeled test set.
- **Topic models**: coherence (c_v, NPMI), topic diversity, and **human inspection of top terms/exemplars** — coherence alone is not enough.
- **Clustering**: silhouette, but mostly qualitative inspection of exemplars; report % outliers (HDBSCAN -1).
- **Retrieval/similarity**: precision@k, recall@k, MRR, nDCG.
- **Coding/extraction**: inter-rater agreement vs human gold (Cohen's κ, Krippendorff's α).
- **Always**: a labeled sample (even 100–300 items) is the cheapest insurance against shipping a wrong conclusion.

## Tools / frameworks

- **spaCy** — production NLP: tokenization, lemmatization, POS, NER, `textcat`, `EntityRuler`, transformer pipelines, spacy-llm. Analyst default for linguistic preprocessing + entities.
- **NLTK** — teaching/classic toolkit: tokenizers, stopwords, stemmers, and **VADER** (`nltk.sentiment.vader`).
- **scikit-learn** — `TfidfVectorizer`/`CountVectorizer`, LDA, NMF, LogisticRegression/SVM, metrics, pipelines. The classical-NLP backbone.
- **Gensim** — LDA, word2vec/fastText, phrase detection, similarity indexes; good for large streaming corpora.
- **Hugging Face Transformers / Hub** — fine-tuned/zero-shot sentiment, classification, NER, embeddings; `pipeline()` API.
- **sentence-transformers (SBERT)** — embeddings for similarity, clustering, semantic search, paraphrase mining; cross-encoder rerankers.
- **BERTopic** — modular transformer topic modeling (embeddings → UMAP → HDBSCAN → c-TF-IDF → representation).
- **KeyBERT / YAKE / RAKE** — keyphrase extraction across the speed↔accuracy spectrum.

## Methodology (analyst workflow)

1. **Frame the question** in measurable terms ("what share of tickets mention billing AND are negative?").
2. **Profile the corpus**: length distribution, language(s), duplicates, source noise (HTML, emoji, boilerplate).
3. **Preprocess deliberately** — match the recipe to the method (heavy for BoW/LDA, light for embeddings/transformers).
4. **Baseline first**: TF-IDF distinctive terms, VADER, or TF-IDF + linear classifier. Record the number.
5. **Escalate only if needed**: embeddings/BERTopic/transformer/LLM, justified by a baseline gap.
6. **Validate on a labeled sample** before trusting aggregates.
7. **Aggregate and visualize** with uncertainty (counts, %, CIs); never report a single sentiment number without volume + a sample of exemplars.
8. **Document** preprocessing, model versions, thresholds, and seeds for reproducibility.

## Practical patterns

- **Distinctive-terms report**: TF-IDF with `ngram_range=(1,2)`, top terms per segment — cheap, persuasive, interpretable.
- **Open-end theming**: SBERT `all-MiniLM-L6-v2` → BERTopic with fixed UMAP `random_state` → label topics with KeyBERT/LLM → reduce outliers.
- **Directional sentiment at scale**: VADER pass for volume; transformer on a sampled/uncertain subset; reconcile.
- **PII scrub / entity rollup**: spaCy NER + EntityRuler; aggregate ORG/PRODUCT mentions.
- **Codebook coding**: LLM deductive pass with few-shot codebook → human reviews a random 10–20% → report κ.
- **Dedup near-identical feedback**: SBERT embeddings + cosine threshold or paraphrase mining.

## Anti-patterns

- Reporting one global sentiment score with no volume, no time trend, no exemplars.
- Stemming/stopword-stripping before embeddings or transformer tokenizers (destroys signal).
- Picking LDA `num_topics` by gut and never checking coherence or exemplars.
- Trusting LLM/transformer output on a new domain without a labeled validation sample.
- Treating corpus text as trusted instructions to the LLM (prompt-injection exposure).
- Using accuracy on imbalanced labels instead of macro-F1.
- Jumping to transformers/LLMs before a TF-IDF/VADER baseline (cost, latency, and no benchmark).
- Non-reproducible runs: unpinned model versions, no seeds, non-zero temperature for extraction.

## Troubleshooting

- **Topics are garbage / one giant topic** → too few/noisy docs, bad preprocessing, or HDBSCAN merging; tune `min_topic_size`, embeddings, or use NMF; check % outliers.
- **Everything looks "neutral" in VADER** → wrong domain (formal/clinical/financial), translation needed, or compound thresholds wrong; try a domain transformer.
- **Embeddings cluster by length/language not meaning** → mixed languages or huge length variance; segment by language, chunk long docs.
- **KeyBERT returns near-duplicates** → enable MMR / raise `diversity`.
- **Classifier great in CV, bad live** → leakage, distribution shift, or imbalance; re-check splits and macro-F1.
- **LLM coding disagrees with humans** → tighten codebook definitions, add few-shot exemplars, lower temperature, measure κ per code.
- **Slow at corpus scale** → batch `encode()`, use MiniLM not mpnet, cache embeddings, sample for exploration.

## References

- BERTopic docs & algorithm — modular embeddings/UMAP/HDBSCAN/c-TF-IDF pipeline (MaartenGr, 2022–2025): https://maartengr.github.io/BERTopic/ , https://maartengr.github.io/BERTopic/algorithm/algorithm.html , https://github.com/MaartenGr/BERTopic
- Sentence-Transformers (SBERT) docs — semantic similarity, pretrained models, computing embeddings (2024–2025): https://www.sbert.net/docs/quickstart.html , https://www.sbert.net/docs/sentence_transformer/pretrained_models.html , https://www.sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html
- VADER: Hutto & Gilbert, "A Parsimonious Rule-Based Model for Sentiment Analysis of Social Media Text," ICWSM 2014: https://ojs.aaai.org/index.php/ICWSM/article/view/14550 ; repo: https://github.com/cjhutto/vaderSentiment ; docs: https://vadersentiment.readthedocs.io/
- Transformer vs lexicon sentiment comparisons (2024–2025): https://link.springer.com/article/10.1007/s10115-024-02214-3 ; healthcare VADER/BERT/Flair: https://pmc.ncbi.nlm.nih.gov/articles/PMC12382424/
- spaCy docs — NER, textcat, training pipelines, LLM integration (v3, 2024–2025): https://spacy.io/usage/spacy-101 , https://spacy.io/api/entityrecognizer , https://spacy.io/usage/training , https://spacy.io/usage/large-language-models , https://github.com/explosion/spacy-llm
- KeyBERT (MaartenGr) + keyword-extraction benchmarks (RAKE/YAKE/KeyBERT, 2024): https://github.com/MaartenGr/KeyBERT , https://arxiv.org/pdf/2409.10640 , https://towardsdatascience.com/keyword-extraction-a-benchmark-of-7-algorithms-in-python-8a905326d93f/
- scikit-learn text feature extraction (TF-IDF, n-grams) & decomposition (LDA/NMF): https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction , https://scikit-learn.org/stable/modules/decomposition.html
- Gensim — LDA, word2vec, similarity: https://radimrehurek.com/gensim/
- Hugging Face Transformers — pipelines (sentiment, zero-shot classification, NER): https://huggingface.co/docs/transformers/main_classes/pipelines
- LLM-assisted qualitative coding / thematic analysis (2024–2026): https://journals.sagepub.com/doi/10.1177/16094069241231168 , https://journals.sagepub.com/doi/10.1177/16094069261426100 , https://arxiv.org/html/2510.18456v1
