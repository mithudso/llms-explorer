---
title: "Diátaxis Tutorial Quadrant"
description: "A tutorial is a lesson. Its only job is to take a complete newcomer through a meaningful, hand-held experience and leave them with two things: a tiny working artifact they built themselves, and the co"
---

# Tutorial Writing — Diátaxis Learning Quadrant

## Overview

A tutorial is **a lesson**. Its only job is to take a complete newcomer through a meaningful, hand-held experience and leave them with two things: a tiny working artifact they built themselves, and the confidence that they can use this tool.

**The single most-violated rule:** the artifact does not matter; the learning does. A tutorial reader is not there to ship the thing they build — they are there to encounter the tool, the vocabulary, and the shape of the workflow under your protection.

If you find yourself optimizing for "they could use this output in production" — stop. You are writing a how-to. Switch quadrants.

## Core Concepts

### 1. The learner's promise

When a learner runs your step, they must see the result you said they would see. This is non-negotiable. Confidence is built layer by layer, and one broken step shakes the whole stack.

**Re-test every step on a clean environment before you ship.**

### 2. Narrator voice — "we" not "you alone"

Tutorials use the first-person plural: *"we'll create a file called `app.py`"*, *"now we'll run it"*. The instructor is present. The learner is not abandoned.

Contrast with how-to voice ("Create a file named `app.py`") which assumes competence.

### 3. No detours

There will be a hundred interesting tangents — "by the way, you could also…", "in production you'd usually…". **Cut all of them.** Every sentence either moves the learner toward the artifact or it leaves the document.

### 4. Exit-with-a-completed-artifact

The learner must finish with **something visible**: a running web server on `localhost:8000`, a printed "Hello, world", a deployed function that responded to a curl.

### 5. Cognitive load budget (7±2)

Human working memory holds roughly 7 ± 2 items. Each step introduces **one** new thing. Earlier-introduced things are reused, not re-explained.

### 6. Backward design (Carpentries)

Start at the end. Write down — in one sentence — what the learner can do after the tutorial that they could not do before. Then work backwards.

### 7. Concrete, particular, robust

Tutorials are built around **specific** actions and **specific** outcomes. Not "create a database" — *"create a database called `tutorial_db`"*. Not "you'll see some output" — *"you'll see exactly this output: `{...}`"*.

### 8. The instructor's safety contract

The reader is a guest in your kitchen; you don't let them touch the hot pan. If the install command on macOS 14 prompts for a password and the learner does not expect it, that is your error, not theirs.

### 9. Inspire confidence, not competence

The goal is *"I can do this"*, not *"I have mastered this"*.

### 10. Tutorials are not the place for "if" or "depending on"

Branching kills tutorials. Pick **one** environment, declare it in step 0, and keep one linear path.

## Template — minimum viable tutorial

```markdown
# Your First <Thing>

In this tutorial we'll build a <small concrete thing>. By the end, you'll have
<artifact> running on <where>.

This tutorial takes about <N> minutes. We assume you have <one prerequisite>
installed.

## What we'll build

<one or two sentences and ideally a screenshot or sample output>

## Step 0 — Set up

<copy-pasteable env setup. Pin versions.>

You should see:
```
<exact expected output>
```

## Step 1 — <one new thing>

<narrator voice: "Let's create a file called …">

```<lang>
<code>
```

Run it:

```
<command>
```

You should see:
```
<exact expected output>
```

<one sentence on what just happened — no theory, no alternatives>

## Step N — <the final visible artifact>

…

Congratulations. You've built <artifact>. You can find the finished code at
<link>.

## What's next

- To do <related task>, see the [How to <verb>](…) guide.
- To understand *why* <concept> works this way, see [<concept> explained](…).
```

## Anti-Patterns

### AP-1 — The "tutorial" that is secretly reference
> "This tutorial covers the `Client` class, which has the following methods…"
Tutorials walk a learner through *doing one thing*; they do not enumerate surface area.

### AP-2 — The "kitchen sink" tutorial
Twelve features, three languages, two installation paths. Pick one concrete artifact, one environment, one path.

### AP-3 — Theory before action
Three paragraphs of background before the first command. Get them to `Hello, world` in the first five minutes.

### AP-4 — Hand-waved steps
*"Now set up your database."* How? Which database? On what port? Every imperative must be **copy-pasteable**.

### AP-5 — Untested steps
Tutorials decay. **Re-run the entire tutorial on a clean VM before each release.**

### AP-6 — "You'll see something like…"
Either it's exact or you've broken the learner's promise. Show the exact output.

## Decision Heuristics

1. **Is the reader a complete newcomer?** If they could already articulate a specific goal, they need a how-to.
2. **Is the artifact small enough that you can guarantee every step?** If not, split it.
3. **Is there exactly one path through?** If you find "if/depending on/optionally", you are drifting toward how-to.
4. **Does the reader end with a visible, working thing they built themselves?**

When the answer points elsewhere:
- Competent reader with a goal → `howto-writing`
- "Why does this exist?" → `explanation-doc-writing`
- "What are the parameters of `foo()`" → `reference-doc-writing`

## References

1. [Tutorials — Diátaxis](https://diataxis.fr/tutorials/)
2. [Collaborative Lesson Development Training — Lesson Design (The Carpentries)](https://carpentries.github.io/lesson-development-training/lesson-design.html)
