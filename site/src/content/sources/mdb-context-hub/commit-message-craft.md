---
title: "Commit Message Craft"
description: "Subject line: hard limit 50 characters. Body: wrap at 72."
---

# Commit Message Craft

## Core Concepts

### 1. The 50/72 rule (Tim Pope, 2008)

Subject line: hard limit 50 characters. Body: wrap at 72.

**Mechanical rules:**
- Subject line ≤ 50 chars. Hard ceiling is 72, but cross 50 only when truly unavoidable.
- Blank line between subject and body — required.
- Body wrap at 72.
- No trailing period on the subject.

### 2. Imperative mood for the subject

Write the subject as a command the commit gives the codebase, not as a past-tense report.

Test: prepend "If applied, this commit will ___". The result must be a grammatical English sentence.

- `Add retry logic to S3 uploader` — passes
- `Added retry logic to S3 uploader` — fails

### 3. Conventional Commits: structure beyond the basics

```
<type>[optional scope][!]: <description>

[optional body]

[optional footer(s)]
```

**Types:** feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert

### 4. Breaking changes: `!` and `BREAKING CHANGE:` footer

**Method 1 — exclamation mark in the header:**
```
feat(api)!: remove deprecated /v1/users endpoint
```

**Method 2 — footer token:**
```
feat(api): drop XML response format

BREAKING CHANGE: Clients sending Accept: application/xml now receive
406 Not Acceptable.
```

### 5. The "why not what" rule for the body

The diff already shows *what* changed. The body must explain *why*.

**Body content checklist:**
- What problem did this commit solve?
- Why this approach and not an alternative?
- Any non-obvious side effect or trade-off?
- Links to tickets, design docs, or incident reports.

**Body anti-content:**
- Don't restate the subject line.
- Don't narrate the diff line by line.

### 6. Multi-commit storytelling for PR reviewers

1. **Prep commits first** — refactors, renames, type-only changes with no behavior change.
2. **The substantive commit** — the one that does the actual feature/fix.
3. **Test commit(s)** — if tests are separated.
4. **Cleanup commits last** — docs, changelog, version bumps.

### 7. Fixup / squash / autosquash discipline

`git commit --fixup=<sha>` writes a commit message starting with `fixup! <original-subject>`.

- `--fixup` discards the fixup's commit message; only the original is kept. Use for typo fixes.
- `--squash` keeps both messages joined. Use when the "fix" adds meaningful nuance.

**Never push fixup commits to a shared branch as-is.**

### 8. Signed-off-by and the Developer Certificate of Origin

```
fix(net): handle ECONNRESET during initial TLS handshake

The current code path treats a reset before the ServerHello as a
generic IO error, masking the actual TLS issue.

Signed-off-by: Mitchell Hudson <mitch.hudson@mongodb.com>
```

Use `git commit -s` (or `--signoff`) to add automatically.

### 9. Other trailers

- `Co-authored-by: Name <email>` — GitHub credits both authors
- `Closes #123`, `Fixes #123`, `Resolves #123` — GitHub auto-closes the issue

## Templates

### Template — Conventional Commit with body and footers

```
<type>(<scope>): <imperative description>

<Why this change exists. What problem it solves or what behavior it
enables. Wrap at 72 columns.>

Closes #1234
Co-authored-by: Pat Reviewer <pat@example.com>
Signed-off-by: Mitchell Hudson <mitch.hudson@mongodb.com>
```

## Anti-Patterns

- **"Fixed bug" / "Updates" / "WIP"** — useless.
- **Past-tense subjects** — `Added`, `Fixed`, `Refactored`.
- **Restating the diff in the body.**
- **Stacking unrelated changes in one commit.**
- **Burying breaking changes without `!` or `BREAKING CHANGE:`.**

## References

- [Conventional Commits v1.0.0 specification](https://www.conventionalcommits.org/en/v1.0.0/)
- [Tim Pope — A Note About Git Commit Messages](https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html)
- [Chris Beams — How to Write a Git Commit Message](https://cbea.ms/git-commit/)
