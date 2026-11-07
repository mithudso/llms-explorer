---
title: 'Concept facts files'
description: 'Load the preserved concept tree as source-cited Markdown facts.'
section: reference
order: 9
---

The [context index](/context/) lists concept facts under the roots of the
[concept tree](/tree/). The source directory and scraped reports are no longer published.

## Read a concept

Fetch `/context.md` to choose a concept, then fetch its
`/downloads/concepts/<slug>.md` file. Each file includes its summary, facets,
facts and related concepts. Facts retain their original source identifiers.
Archived report identifiers appear as text because those reports are no longer hosted here.
External primary sources remain links.

The files use `text/markdown`. Each banner records the pack date and an estimated
token count. Publication does not certify independent review or factual accuracy.

## Portable public packs

Download `/downloads/context-packs/<slug>.llms.zip`, or use LLMSX0.2.8+:

```sh
llmsx context list
llmsx context get prompt-caching
llmsx concepts --data . serve prompt-caching --file llms-facts.txt
```

The ZIP contains `<slug>.llms/manifest.json`, `concept-graph.json`, `llms.txt`,
`llms-full.txt`, `llms-small.txt`, `llms-facts.txt` and `llms-vocabulary.txt`.
The five-file ladder is a project convention, not a universal llms.txt requirement.
The public graph has one node; no private graph, raw reports or unpublished claim
ledgers are included. The vocabulary file explicitly states that this export does
not supply an independently curated vocabulary. The short file is a labeled
opening extract. The full and facts layers retain the public Markdown reference.

The catalog at `/downloads/context-packs/index.json` records sizes and archive
hashes. The CLI validates the catalog hash, exact member list and every member's
manifest hash before writing a new directory. Existing output paths are refused.
These checks prove transfer integrity; they do not certify factual accuracy.
Use the pack date, original sources and task-specific checks to judge suitability.
