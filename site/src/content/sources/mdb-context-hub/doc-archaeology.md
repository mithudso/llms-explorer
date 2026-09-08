---
title: "Doc Archaeology"
description: "Excavate aging documents for staleness, dead links, process drift, phantom dependencies, and obsolete examples."
---

# Doc Archaeology

Excavate aging documents for staleness, dead links, process drift, phantom dependencies, and obsolete examples.

## Five categories of doc decay

1. **Stale Facts** — claims about state-of-the-world that have changed
2. **Dead Links** — URLs that 404, redirect to unrelated destinations
3. **Drift from Current Process** — procedures that no longer reflect actual practice
4. **Phantom Dependencies** — scripts, files, tools, people that no longer exist
5. **Obsolete Examples** — code snippets reflecting prior API or UI

## Five-pass workflow

1. **Last-Updated Lens** — estimate age, catalog time-sensitive claims, set decay risk (low/medium/high)
2. **Fact-Check Pass** — verify each claim against current state
3. **Link-Check Pass** — verify every URL; flag auth-gated as "unverified"
4. **Process-Check Pass** — verify procedures against current practice at step level
5. **Dependency-Check Pass** — check scripts, files, tools, channels, people

## Findings table

| # | Category | Location | What the doc says | Current reality | Severity | Action |
|---|---|---|---|---|---|---|

**Severity:** Critical/Misleading → High/Outdated → Medium/Cosmetic → Low/Historical

## Salvage decisions

- **Update in place** — targeted fixes; structure is sound
- **Restructure and refresh** — major rewrites needed
- **Deprecate with pointer** — superseded, add deprecation banner
- **Archive** — historical state; remove from search
- **Delete** — fully phantom, all claims stale

## Anti-patterns

- Noting a doc is old without running any passes (ostrich mode)
- Rewriting when targeted refresh would suffice
- Deleting load-bearing historical context
- Treating unverifiable as confirmed
