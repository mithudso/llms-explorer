---
title: "Knowledge Graphs and Semantic Analytics"
description: "A knowledge graph (KG) represents entities (nodes) and the typed, meaning-bearing relationships between them (edges), with attributes (properties) on both, plus a schema/ontology that says what the ty"
---

# Knowledge Graphs & Semantic Analytics

## Overview

A **knowledge graph (KG)** represents entities (nodes) and the typed, meaning-bearing relationships between them (edges), with attributes (properties) on both, plus a **schema/ontology** that says what the types *mean*. The point is not just to store connections (that is da-27's graph-algorithms angle) but to encode **semantics** — shared, machine-interpretable meaning — so that data from many sources can be integrated, queried by meaning, validated against a model, and reasoned over to infer new facts.

Reach for a KG when the **connections and their meaning carry the signal and must be queried, integrated, or reasoned about**: multi-hop questions, heterogeneous data integration under one vocabulary, provenance/lineage, regulatory traceability, and grounding LLMs. A KG beats relational/dimensional modeling when traversal depth is variable and deep. If the question is answerable with a `GROUP BY` or a couple of JOINs over a stable schema, you do **not** need a KG — use a warehouse/dimensional model (da-29).

This is the semantic/ontology node of the data-analytics curriculum (da-1 onward).

## Scope boundary
- **da-27-network-graph-analytics** owns graph *algorithms* (centrality, community detection, link prediction, GNNs). This skill owns *meaning*: ontologies, RDF/OWL/SHACL, semantic queries, reasoning, KG construction, GraphRAG.
- **ai-datastores ("Knowledge Graphs for AI")** owns the vector-DB / agent-memory / KG-as-storage angle. This skill owns the analytics/semantic-integration angle.
- **da-18-semantic-layer-headless-bi** owns the *metrics* layer (dbt SL, Cube, MetricFlow). A KG semantic layer is about *entities and their meaning*.
- **da-30-data-governance-catalogs** owns governance/catalog policy generally; this skill covers modeling the catalog itself as a knowledge graph.

## Core Concepts
1. **Two graph data models**: Labeled Property Graph (LPG; Neo4j/TigerGraph/Memgraph; Cypher/GQL) vs RDF triple store (subject-predicate-object with global IRIs; GraphDB/Jena/Stardog/Virtuoso; SPARQL). Plain RDF can't attach properties to one relationship instance — **RDF-star** fixes this. Choose RDF for interoperability/reasoning/standards, LPG for speed/traversal/AI; hybrid (RDF of record + LPG projection) is common.
2. **Semantic web stack (W3C)**: RDF (Turtle/N-Triples/JSON-LD), RDFS (lightweight schema), OWL 2 (Description-Logic ontologies; EL/QL/RL profiles), SPARQL (graph patterns, property paths, federation, CONSTRUCT), SHACL (shapes validation), named graphs (quads for provenance/trust/versioning).
3. **OWL vs SHACL**: OWL = inference (open-world; derives new facts). SHACL = validation (closed-world; checks constraints, reports violations). Modern practice: OWL for modeling + SHACL for validation together.
4. **Ontology & taxonomy engineering**: taxonomy (hierarchy) vs ontology (taxonomy + typed relations + axioms). SKOS for controlled vocabularies; upper ontologies (BFO/DOLCE/SUMO/gist) for alignment; Ontology Design Patterns; schema.org as pragmatic web vocab.
5. **KG construction**: schema-first vs data-first; NER + relation extraction; entity resolution/dedup; entity linking to canonical IDs (Wikidata Q-numbers); R2RML/RML schema mapping; Ontology-Based Data Access (OBDA)/virtual KGs (Ontop rewrites SPARQL→SQL); LLM-assisted construction (2024-2026) validated via OWL/SHACL.
6. **Querying, reasoning & analytics**: SPARQL vs Cypher vs **GQL** (ISO/IEC 39075:2024, first new ISO query standard since SQL); reasoning/materialisation (sound entailment, unlike approximate embedding-based completion); semantic analytics (entity-centric aggregation, multi-hop joins, lineage traversal).
7. **Enterprise KGs**: data fabric (plumbing) + KG (semantic intelligence); metadata knowledge graph as unified queryable catalog; data catalog as a graph (discovery via traversal/semantic search).
8. **GraphRAG & semantic retrieval**: RAG over a KG (hybrid vector+graph); handles multi-hop/global questions with explainable, grounded, entity-centric answers; 2025-2026 pattern is hybrid routing (vector/KG-traversal/SQL by query type); agentic GraphRAG plans multi-hop traversals.

## Tools
Neo4j + neosemantics (n10s), RDFLib, Apache Jena/Fuseki, Ontotext GraphDB, Stardog, Amazon Neptune (RDF+LPG), TigerGraph, Virtuoso, Ontop (virtual RDF/OBDA), Wikidata, schema.org.

## Methodology
1. Decide if you need a KG (variable-depth traversal/integration/reasoning/provenance/LLM grounding — else use da-29).
2. Pick the model (RDF vs LPG vs hybrid/RDF-star).
3. Design the ontology/taxonomy (reuse SKOS/schema.org/upper ontologies/ODPs; keep OWL and SHACL distinct).
4. Construct (extract, resolve, link, map via R2RML/RML or OBDA; validate LLM extraction with SHACL).
5. Validate & reason (SHACL for quality; materialise or query-time reason).
6. Query & serve analytics (SPARQL/Cypher/GQL; layer GraphRAG; route hybrid by query type).

## Anti-Patterns
Using a KG as a slow relational DB; confusing OWL (infers, open-world) and SHACL (validates, closed-world); plain RDF for edge attributes instead of RDF-star/LPG; skipping entity resolution; ontology over-engineering; trusting unvalidated LLM extractions.

(Full skill body with 38 cited references installed at ~/.claude/skills/da-41-knowledge-graphs-and-semantic-analytics/SKILL.md)
