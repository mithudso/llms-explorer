# Research Report: Structured Output Constraints and LLM Hallucination Mitigation

## Executive Summary
Structured output constraints (e.g., JSON Schema enforcement) provide a reliable method to force Large Language Models (LLMs) to output machine-readable data structures. By using techniques like constrained decoding and guided generation, developers can guarantee 100% syntactical compliance, effectively eliminating "structural hallucinations" (e.g., malformed JSON, incorrect data types, or unwanted commentary). However, these constraints do *not* solve "content/semantic hallucinations" where the model generates factually incorrect data within a valid schema. To build robust data extraction pipelines, structured output must be combined with Retrieval-Augmented Generation (RAG), programmatic validation loops, and semantic verification.

## 1. Introduction to Structured Output Constraints
Standard LLM generation is autoregressive and probabilistic. When prompted to "output only JSON," models often fail by including conversational filler, violating schema requirements, or introducing syntax errors. Structured output constraints address this by enforcing a strict "data contract" that guarantees the model's output adheres to a predefined schema.

## 2. The Mechanics of Constrained Decoding
Constrained decoding intervenes directly during the generation process to restrict the model's token selection.

### 2.1 Finite State Machines (FSM) and Logit Masking
Libraries like **Outlines**, **SGLang**, and **Guidance** implement constrained decoding by compiling the target JSON Schema or regular expression into a Finite State Machine (FSM). 
During generation, the FSM determines which tokens are valid next steps based on the current state. The logits (probabilities) for all invalid tokens are masked or set to negative infinity. This ensures the model can only select tokens that progress toward a syntactically valid output.

### 2.2 Native Provider Features
Major API providers have integrated these concepts natively:
- **OpenAI:** "Structured Outputs" mode guarantees adherence to provided JSON schemas.
- **Google Gemini:** Supports schema-constrained generation via the `response_schema` API parameter.
- **Anthropic Claude:** Uses tool use (function calling) to enforce structured data returns.

## 3. Impact on LLM Hallucinations
It is critical to distinguish between the two primary types of extraction errors to understand the boundaries of schema enforcement.

### 3.1 Structural Hallucinations (Solved)
Structural hallucinations involve format violations, unexpected fields, incorrect types, or un-parseable syntax. Constrained decoding completely solves this class of hallucination. By forcing the model down valid token paths, it is mathematically prevented from generating invalid syntax.

### 3.2 Content and Semantic Hallucinations (Unsolved but Mitigated)
Content hallucinations occur when the model outputs factually incorrect, fabricated, or contextually inconsistent data, despite the format being perfect. For example, a model might correctly generate `{ "name": "John Doe", "age": 45 }`, but the age 45 is fabricated.

**Limitations of Schema Enforcement:**
A schema can ensure that `age` is an integer, but it cannot verify if the integer is true. Forcing a model to conform to a schema can sometimes *increase* confident-sounding content hallucinations if the model is forced to fill a required field for which it has no knowledge.

## 4. Complementary Strategies for Complete Mitigation
Because structured outputs only solve half of the hallucination problem, production systems require layered mitigation strategies:

### 4.1 Grounded Generation and RAG
Retrieval-Augmented Generation (RAG) grounds the LLM in verified external data. When combined with schema enforcement, RAG ensures the model has the factual basis required to populate the fields accurately.

### 4.2 Programmatic Validation Validation Loops
Tools like Pydantic or Zod are used post-generation to validate business logic (e.g., `age > 0`). If validation fails, the error can be fed back into the LLM in a retry loop, allowing the model to self-correct.

### 4.3 Semantic Scoring and Citation Checks
Secondary evaluation layers can be implemented to score the generated JSON against the source text to ensure fidelity. Requiring the model to extract a "quote_citation" alongside the target data can anchor the extraction and reduce the likelihood of fabrication.

## 5. Conclusion
Structured output constraints are a prerequisite for using LLMs as reliable data extraction engines, effectively eradicating structural hallucinations. However, treating schema enforcement as a complete solution to hallucinations is a dangerous anti-pattern. True reliability requires pairing strict structural constraints with robust grounding and post-generation validation.
