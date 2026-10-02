# Frontier research batching prompt

Version: 1.0.0
Updated: 2026-10-01
Delta: +1 user prompt; +1 documentation task; no research execution.

## User prompt

```text
My concept family explorer, /dr, and /rabbithole skills rely on online research and website pulling and scraping, would it be better if the concepts inherited the parent's facts and the children added details, and also batching the research into groups that likely share concepts and facts to utilize firecrawl's batch scraping? Look at the frontier concepts in ~/dev/llms-explorer and group them into concepts that could be researched together to save tokens and save that to a markdown file.
```

## Authorized outcome

Inspect the frontier in /Users/mitch/dev/llms-explorer. Recommend bounded parent-fact reuse and shared-source retrieval groups. Save the full grouping and a compact explanation as Markdown. Store versioned continuation records and commit the documentation. Research execution and workflow implementation are future work.
