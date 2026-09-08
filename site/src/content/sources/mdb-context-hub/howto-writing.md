---
title: "Diátaxis How-To Quadrant"
description: "A how-to guide is a recipe. It serves a competent user who has arrived at the page with a specific goal already formed — 'How do I add OAuth to my app?' — and who needs an efficient series of steps to"
---

# How-To Writing — Diátaxis How-To Quadrant

## Overview

A how-to guide is **a recipe**. It serves a competent user who has arrived at the page with a specific goal already formed — *"How do I add OAuth to my app?"* — and who needs an efficient series of steps to get there.

**The single most-violated rule: how-tos answer a question only a competent user could ask.** If your reader cannot even formulate the goal, they need a tutorial.

## Core Concepts

### 1. Title starts with "How to <verb>"

*"How to rotate the signing key"*. *"How to add a custom domain"*. If you cannot fit your doc's purpose into that pattern, you do not have a how-to.

### 2. One goal per document

A how-to with three goals is three how-tos that have not yet been separated. Each goal gets its own URL, its own title, its own search hit.

### 3. Prerequisite block up front

The first block under the title says what the reader must already have, know, or have done. If the reader can't tick every box, they bounce — which is correct, because the doc is not for them yet.

### 4. Numbered, imperative steps

Steps are numbered. Each step begins with an imperative verb. *"Create…"*, *"Run…"*, *"Set…"*, *"Verify…"*. Not *"Now you might want to…"*, not *"Let's…"*.

### 5. Assume competence, omit teaching

A how-to does **not** explain what a Kubernetes namespace is. Link out to an explanation or reference doc if useful; do not inline the lesson.

### 6. Branches are allowed (unlike tutorials)

How-tos can branch: *"If you use Atlas, run X; if you self-host, run Y."* Keep branches shallow (1–2 levels) and label them clearly.

### 7. Verifications, not promises

Tutorials promise *"you'll see exactly this"*. How-tos verify: *"Confirm that `kubectl get pods` shows the new pod in `Running` state."*

### 8. Failure modes are part of the recipe

When a step can plausibly fail, name the failure inline: *"If you see `Permission denied`, your role does not have `clusterAdmin` — see [granting roles](…)."*

### 9. End at the goal, not past it

When the reader has done the thing, stop. Optional follow-up belongs in a **See also** block, not in the numbered list.

## Template — minimum viable how-to

```markdown
# How to <verb> <noun>

<One sentence stating the outcome and when you'd want this.>

## Before you start

- You have <prerequisite 1>.
- You have <prerequisite 2>.
- You have <permission / role / credential>.

## Steps

1. <Imperative verb>… <action>.
   ```
   <command>
   ```

2. <Imperative verb>… <action>.

3. Verify the result:
   ```
   <verification command>
   ```
   You should see <observable indicator>.

## If something goes wrong

- **<Error 1>** — <cause and fix or link>.
- **<Error 2>** — <cause and fix or link>.

## See also

- [Related how-to]
- [Background / explanation doc]
- [API reference for <X>]
```

## Anti-Patterns

### AP-1 — Teaching inside the how-to
> "Before we deploy, let's understand what a deployment is…"

The reader knows what a deployment is. If they don't, link an explanation doc.

### AP-2 — Multi-goal mega-guide
> "How to configure, deploy, and monitor your service"

That is three guides. Split them.

### AP-3 — Tutorial drift
Narrator voice ("we'll now create…"), promise language ("you'll see exactly…"). Either commit to the tutorial form or trust the reader.

### AP-4 — Missing prerequisites
The reader hits step 3 and discovers they needed `kubectl` configured. The prerequisite block is the contract.

### AP-5 — No verification
Twelve steps, no checks. Insert verification at every decision point and at the end.

## Decision Heuristics

1. **Could the reader phrase their question as "How do I <verb>?" before reading?** If they couldn't even ask, they need a tutorial.
2. **Is there exactly one goal?** If not, split.
3. **Does the reader already own the vocabulary?** If you need to define basic terms, you are drifting into tutorial or explanation.
4. **Is the goal a daily task, or a once-ever production-critical event?** Once-ever production-critical events with rollback procedures are **runbooks**, not how-tos.

## References

1. [How-to guides — Diátaxis](https://diataxis.fr/how-to-guides/)
2. [Documentation Quadrants — Dunn](https://dunnhq.com/posts/2023/documentation-quadrants/)
