---
title: "Pull Request Description Craft"
description: "```markdown"
---

# Pull Request Description Craft

## Core Concepts

### 1. The WWHT template — What, Why, How, Test

```markdown
## What
One or two sentences naming the change at a high level.

## Why
The problem this PR solves. Link to the issue, the incident, the
customer ticket.

## How
The approach. Name the modules touched, the design decision made,
and the alternative considered-and-rejected (one sentence).

## Test
What you ran. What a reviewer should run to verify. Screenshots,
recordings, or perf numbers attached below.
```

The order matters: reviewers read top-down and decide whether to keep reading after each section.

### 2. The two-tier reader pattern — skimmers above, nit-pickers below

A PR has two audiences:
- **Skimmers** — the manager, the on-call, the eventual archaeologist running `git log` six months from now.
- **Nit-pickers** — the assigned reviewer.

```markdown
## TL;DR
Adds retry-with-backoff to the S3 uploader so 3% of uploads that
fail on NLB resets now succeed. No API change. Behind no flag.

<details>
<summary>Details</summary>

## Why
Incident #4821 (May 12) showed 3% of uploads failing...

## How
Wraps the existing `putObject` call in a `withRetry` helper...

## Test
- `npm run test:integration -- s3-uploader.retry`
- Replayed the captured NLB-reset trace; all 200 sessions succeed.

</details>
```

### 3. Before/After evidence — screenshots, recordings, numbers

**Screenshot discipline:**
- Two screenshots side by side: `Before` and `After`.
- Crop tight to the changed region.
- For dark-mode features, include both light- and dark-mode screenshots.

**Recording discipline:**
- Use recordings for interaction flows, animation, or anything that can't be captured in one frame.
- Trim to ≤ 30 seconds.

### 4. The "how to test" section — concrete, copy-pasteable

```markdown
## How to test
1. `git checkout this-branch && npm install`
2. `npm run test:unit -- s3-uploader.retry`
3. In Chrome with the extension loaded, click an attachment in any
   case page. Confirm the upload succeeds without a console error.
4. Open DevTools → Network. Throttle to "Slow 3G". Re-upload.
   Confirm two retry attempts in the network log before success.
```

### 5. Link-out vs inline detail

**Inline:** The rationale for the design decision; the error message or log line; the before/after screenshots; a 3-line code snippet.

**Link out:** The full incident report; the original RFC; the customer ticket; the benchmark methodology; stack traces longer than 10 lines.

### 6. Draft, blocked, and stacked signaling

**Title prefixes:**
- `[Draft]` or use GitHub's native "Draft PR" toggle
- `[Do not merge]` — for PRs that exist for discussion only
- `[Stacked on #1234]` — depends on another PR

```markdown
> [!IMPORTANT]
> Stacked on #1234. Review #1234 first.

> [!WARNING]
> Do not merge until the security review in #1235 is approved.
```

### 7. Stacked PRs

When a feature can't reasonably fit in one reviewable PR (~400 lines is the soft ceiling):
1. **PR #1: refactor / scaffolding** — no behavior change.
2. **PR #2: the substantive change** — depends on #1.
3. **PR #3: tests / docs / migration** — depends on #2.

Mark each stacked PR's body with its position:
```markdown
This is PR 2 of 3 in the auth-overhaul stack:
- #1234 — refactor auth module (merged)
- **#1235 — add OIDC flow** ← you are here
- #1236 — migration & docs
```

### 8. Checklists that get verified, not skipped

**Bad:**
- [ ] Code follows best practices
- [ ] Tests are good

**Good:**
- [ ] `npm run lint` passes locally
- [ ] `npm run test` passes locally
- [ ] Manifest version bumped in `manifest.json` and `package.json`
- [ ] Screenshot added for any UI change

## GitHub PR template (`.github/PULL_REQUEST_TEMPLATE.md`)

```markdown
## TL;DR
<!-- One sentence. What changed and what now works that didn't. -->

## Why
<!-- Link the issue / incident / ticket. Restate the problem in 1-3 sentences. -->
Closes #

## How
<!-- The approach. Modules touched. One sentence on the rejected alternative. -->

## How to test
<!-- Numbered, copy-pasteable steps with expected observations. -->
1.
2.
3.

## Screenshots / recordings
<!-- Before / After for UI. Trim recordings to ≤ 30s. -->

## Checklist
- [ ] Tests pass locally (`npm test`)
- [ ] Lint passes (`npm run lint`)
- [ ] CHANGELOG entry added (if user-facing)
- [ ] Screenshots attached (if UI changed)
- [ ] Breaking change noted in body (if any)
```

## Anti-Patterns

- **Empty PR descriptions** ("see commits")
- **Bullet list of every changed file** — the diff already shows this
- **Screenshots without before/after**
- **"Tested locally"** with no steps
- **40-item checklist of every conceivable concern**
- **Massive PRs (1,000+ lines)** — split into a stack
- **Hiding the breaking-change disclosure** — put `**BREAKING**` in the TL;DR

## References

- [Graphite — Best practices for GitHub pull request descriptions](https://graphite.com/guides/github-pr-description-best-practices)
- [GitHub Docs — Creating a pull request template](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository)
- [Conventional Comments specification](https://conventionalcomments.org/)
