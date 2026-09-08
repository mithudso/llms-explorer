---
title: "Diátaxis Reference Quadrant"
description: "Reference documentation is a description. It tells the reader what something is, what its parts are, and what each part does. It does not teach, it does not advocate, and it does not narrate."
---

# Reference Doc Writing — Diátaxis Reference Quadrant

## Overview

Reference documentation is **a description**. It tells the reader what something **is**, what its parts **are**, and what each part **does**. It does not teach, it does not advocate, and it does not narrate.

**The single most-violated rule: reference does not interpret.** It states facts. Discussion belongs in explanation docs; storytelling belongs in tutorials; opinions belong nowhere in reference.

## Core Concepts

### 1. Architecture mirrors the thing described

If the product has modules, the reference has modules. If a class has methods, the doc has a section per method. The doc topology is **isomorphic** to the API topology.

### 2. Exhaustive coverage beats narrative

Every parameter is listed. Every return value is documented. Every error code is enumerated. There is no "for brevity we omit…" — reference is the *only* place where the reader can be sure they have not missed an option. Omissions are bugs.

### 3. Strict consistency

Every function reference has the same sections in the same order. Every parameter table has the same columns. Consistency lets a reader who has read one page **skim** the next page at 10× speed.

### 4. Neutrality

Reference does not say *"you'll usually want…"*, *"the recommended approach is…"*. Reference states: *"`timeout`: integer, milliseconds, default `30000`, minimum `0`, maximum `600000`"*.

### 5. Examples illustrate, never teach

Reference examples are **specimens**, not lessons. A canonical-call example shows the shape — argument positions, return shape, a representative success and a representative failure.

### 6. The no-surprises rule

Anything that could surprise a working reader must be stated explicitly: default values, units (ms vs seconds), whether a field is nullable, whether the method mutates input, whether order matters.

### 7. Search-discoverability

Reference is read by **search**, not by table-of-contents traversal. The page title and the first sentence must contain the term the reader will type. Headings must be the names of the things they describe (`POST /v1/users`, `createSession(opts)`, `--max-retries`).

### 8. Stable ordering

- **Alphabetical** for catalogs (CLI flags, config keys, error codes).
- **Logical / call-order** for function references (constructor, then lifecycle methods, then utility methods).
- **Signature-order** for parameter tables (positional first in their declared order; keyword/optional after).

## Templates

### Template — function/method reference

```markdown
# `<functionName>(<params>) → <return>`

<One-sentence factual statement of what the function does.>

**Since:** v1.4
**Stability:** stable

## Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `opts.timeout` | `number` (ms) | no | `30000` | Maximum time before the call rejects with `TimeoutError`. Must be ≥ 0. |

## Returns

`Promise<Result>` — resolves with `Result` on success. Rejects with one of the errors below.

## Errors

| Code | Class | Thrown when |
|---|---|---|
| `TIMEOUT` | `TimeoutError` | `opts.timeout` elapsed before the call resolved. |

## Example

```js
const r = await client.fetchThing(id, { timeout: 5000 });
```

## See also

- `<relatedFunction>` — for the streaming variant.
```

### Template — CLI flag reference

```markdown
# `mytool deploy`

Deploy the current project to the configured target.

## Synopsis

```
mytool deploy [--target <name>] [--dry-run] [--force]
```

## Flags

| Flag | Type | Default | Description |
|---|---|---|---|
| `--target <name>` | string | `production` | Named target from `config.yaml`. |
| `--dry-run` | bool | `false` | Print planned actions; make no changes. |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success. |
| 2 | Configuration error. |
```

## Anti-Patterns

### AP-1 — Examples that teach instead of describe
> "Imagine you have a user signup form. You'd call `createUser` like this…"

That's a tutorial example. Strip the narrative.

### AP-2 — "Recommended" / "preferred" / "you should"
These are advice. Move them to a how-to.

### AP-3 — Missing defaults, units, or nullability
Every parameter without a documented default is a footgun.

### AP-4 — Incomplete error tables
> "Throws on failure." — What failures? Under what conditions? With what code?

### AP-5 — Mixed ordering
Parameters listed alphabetically on one page, by signature on another. The reader's skim speed collapses.

## Decision Heuristics

1. **Will the reader arrive via search, looking for a specific name?** If yes → reference.
2. **Is the content exhaustive coverage of a surface area?** If you can plausibly omit items "for brevity", you are not writing reference.
3. **Is the voice neutral and factual?** If you find *"you'll want…"* — that's a how-to hiding inside.

When it's not reference, switch quadrants:
- Newcomer onboarding → `tutorial-writing`
- Goal-directed recipe → `howto-writing`
- Background / why / discussion → `explanation-doc-writing`
- REST/SDK endpoint authoring → `api-docs-craft`

## References

1. [Reference — Diátaxis](https://diataxis.fr/reference/)
2. [Reference guides — Divio Documentation](https://docs.divio.com/documentation-system/reference/)
