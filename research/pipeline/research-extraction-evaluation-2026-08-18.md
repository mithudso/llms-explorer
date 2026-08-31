# Research Report: Extraction Evaluation Frameworks

## Executive Summary

The transition from traditional Optical Character Recognition (OCR) to Large Language Model (LLM)-driven document extraction has fundamentally altered the landscape of automated data extraction. While LLMs offer unprecedented capabilities in understanding context and unstructured data, they introduce novel failure modes such as hallucinations, subtle omissions, and structural collapse on long documents. To rigorously evaluate these systems, a new generation of evaluation frameworks has emerged. Two prominent examples are **ExtractBench** and **ParseBench**, which move beyond legacy surface-level string-matching metrics (e.g., BLEU, ROUGE) to assess semantic correctness, structural integrity, layout awareness, and schema compliance. 

ExtractBench focuses on schema-guided extraction from long enterprise documents, penalizing systems that fail to trace extracted values to source texts or collapse when processing multi-page files. ParseBench focuses on the reliability of document parsing for AI agents, measuring the semantic correctness of elements like tables, charts, and reading orders to prevent downstream reasoning errors. Alongside other frameworks like SCORE, these benchmarks are standardizing "LLM-as-a-judge" methodologies and establishing rigorous performance baselines for modern text extraction systems.

## 1. Introduction: The Generative Era of Text Extraction

Historically, text extraction relied heavily on template-based parsing, regular expressions, and layout-specific rules. If a document's layout shifted, the extraction pipeline broke. The advent of vision-language models (VLMs) and LLMs introduced zero-shot and few-shot extraction capabilities, allowing systems to ingest raw text, PDFs, or images and output structured JSON based on natural language prompts.

However, this generative approach introduced new complexities:
- **Hallucinations:** Models fabricating data that structurally fits the requested schema but does not exist in the source document.
- **Omissions:** Models silently dropping fields or skipping rows in complex tables.
- **Structural Variability:** Models producing valid JSON that violates the requested schema (e.g., nesting arrays incorrectly or altering key names).
- **Context Loss:** Degraded performance on long-context documents where the model forgets instructions or loses track of document state across dozens of pages.

Legacy evaluation metrics like exact match, F1 score, BLEU, and ROUGE are insufficient because they penalize valid semantic variations while failing to detect critical structural and reasoning errors. Consequently, the industry has pivoted toward comprehensive, multi-dimensional benchmarking frameworks.

## 2. ExtractBench: Schema-Guided Enterprise Extraction

**ExtractBench** is an open-source framework and dataset specifically engineered to evaluate AI systems on real-world enterprise extraction tasks. It addresses the reality that modern extraction is fundamentally agentic and increasingly operates with minimal human oversight.

### 2.1 Core Philosophy
Instead of evaluating models against fixed templates, ExtractBench utilizes a **schema-guided** approach. Models receive both the raw document and a user-defined JSON schema, testing their ability to adapt to unseen document types and complex, arbitrary data structures. 

### 2.2 Dataset Composition
The benchmark comprises 370 enterprise documents spanning over 4,869 pages. This dataset represents 8 distinct business domains and 67 document types, offering a highly diverse and challenging corpus that mirrors the variability found in corporate environments.

### 2.3 Key Evaluation Dimensions
ExtractBench is unique in its joint evaluation of several critical axes:
- **Long-Record Completeness:** Traditional benchmarks often evaluate single-page extractions. ExtractBench tests whether a model can sustain high accuracy across documents spanning dozens or hundreds of pages without collapsing or truncating outputs.
- **Perception Robustness:** The framework evaluates performance on low-quality inputs, including noisy scans, handwritten text, and rotated pages, simulating the imperfect nature of real-world physical documents.
- **Traceability and Grounding:** ExtractBench penalizes models that cannot provide source evidence. An extracted value must be traceable back to its origin in the text, allowing for verifiable audit trails.
- **Schema as Executable Specification:** Each field in the JSON schema declares its own scoring metric. For instance, an identifier field might require an exact match, whereas a quantity or date field might allow for tolerance or format variations.
- **Omission vs. Hallucination Tracking:** The framework explicitly tracks and scores omissions (missing values) separately from hallucinations (invented values), offering deeper diagnostic insights.

## 3. ParseBench: Semantic Correctness for AI Agents

While ExtractBench focuses on schema-driven JSON extraction, **ParseBench** is designed to evaluate the underlying parsing and text extraction systems that feed data into AI agents. Developed and hosted as an open-source dataset (`llamaindex/ParseBench`), it tests whether a parser preserves the structural and semantic meaning required for autonomous decision-making.

### 3.1 The "Silent Error" Problem
ParseBench addresses the critical issue of silent parsing errors. When an AI agent processes a financial report, a misaligned table header, a dropped decimal point, or corrupted reading order will not throw a software exception. Instead, it leads to catastrophic reasoning failures downstream. ParseBench measures a parser's ability to avoid these semantic corruptions.

### 3.2 Evaluation Dimensions
ParseBench tests extraction across five primary capability dimensions using approximately 2,000 human-verified pages from real enterprise documents:
- **Tables and Structural Fidelity:** Evaluates the handling of complex structures like merged cells and hierarchical headers, ensuring data accurately maps to the correct columns and rows.
- **Charts and Visual Elements:** Measures the ability to extract precise numerical values and correct labels from charts (bar, line, pie), moving beyond mere natural language summarization to precise data extraction.
- **Content Faithfulness:** Tests for omissions, hallucinations, and reading-order violations. If a multi-column layout is parsed out of order, the context is corrupted.
- **Semantic Formatting:** Ensures that formatting with inherent semantic meaning—such as strikethroughs (superseded text), superscripts (footnotes), and bold emphasis—is correctly preserved and interpreted.
- **Visual Grounding:** Evaluates how well the parser identifies and interprets visual layout elements, such as bounding boxes and spatial relationships.

## 4. Other Notable Frameworks and Methodologies

Beyond ExtractBench and ParseBench, the ecosystem includes several other notable frameworks:

### 4.1 SCORE (Structural and Content Robust Evaluation)
Developed for the generative era of document parsing, SCORE is an interpretation-agnostic framework. It separates legitimate representational diversity (e.g., representing a table as Markdown vs. HTML vs. JSON) from actual extraction errors. This prevents models from being penalized simply for formatting choices if the underlying semantic data is correct.

### 4.2 CaseReportBench
A domain-specific benchmark focused on dense information extraction from clinical case reports. It highlights the necessity of specialized evaluation in high-stakes environments like healthcare, where entity extraction (symptoms, diagnoses, treatments) must be perfectly accurate and context-aware.

### 4.3 LlamaIndex / LlamaParse Ecosystem
Tools like LlamaParse provide layout-aware evaluation workflows. They emphasize that text extraction must be evaluated at two layers: the raw parsing/OCR layer (how well the document is digitized) and the reasoning layer (how well the LLM extracts the requested schema from the digitized text).

## 5. Methodological Shifts: LLM-as-a-Judge

A unifying trend across these modern frameworks is the adoption of the **LLM-as-a-judge** methodology. Given the limitations of deterministic string matching, advanced models (like GPT-4 or Claude 3.5 Sonnet) are used to evaluate the outputs of other models. 

This process typically involves:
1. **Natural Language Rubrics:** The judging LLM is given strict guidelines on how to grade the extraction (e.g., "Award 1 point if the total amount matches the invoice, even if the currency symbol is omitted").
2. **Pydantic Validation:** The output is first passed through a Pydantic model to ensure strict schema adherence and type safety. If it fails structural validation, it scores a zero.
3. **Ground Truth Comparison:** The judge compares the structurally valid output against a human-verified ground truth, assessing semantic equivalence rather than exact character matching.

## 6. Conclusion

The evaluation of text extraction has matured rapidly. Frameworks like ExtractBench and ParseBench illustrate a shift from evaluating simple OCR accuracy to evaluating agentic reliability, structural comprehension, and semantic fidelity. As enterprise workflows increasingly rely on LLMs to ingest and process unstructured data, these benchmarks provide the rigorous, multi-dimensional scoring necessary to ensure models are production-ready, traceable, and robust against the complexities of real-world documents.
