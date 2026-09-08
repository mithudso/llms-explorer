---
title: "Error Message Craft"
description: "Error messages are the most-read text most software ever produces. They are also the worst-edited. The goal: tell the user what went wrong, why it went wrong, and what to do next."
---

# Error Message Craft

## Overview

Error messages are the most-read text most software ever produces. They are also the worst-edited. The goal: tell the user **what** went wrong, **why** it went wrong, and **what to do next**.

## Core Concepts

### 1. The "what / why / what to do next" triple

1. **What went wrong** — the observable failure, stated in user terms.
2. **Why it went wrong** — only when the cause helps the user decide what to do.
3. **What to do next** — a concrete action.

The triple does not have to be three separate sentences. For a short field validation:
> "Email must include an @ symbol."

For an API 5xx:
> "We couldn't save your changes (database unreachable). Wait 30 seconds and retry; if this persists, contact support with request ID `req_abc123`."

### 2. No-blame language — the system owns the failure

Three substitutions do most of the no-blame work:

- **"You [did wrong thing]" → "[Field] requires [thing]"**
- **"You failed to..." → "[Action] needs..."**
- **"Invalid input" → "[Field name] must be [format]"**

Test: replace "you" with "the system" in the draft. If the sentence now reads as the system admitting a defect, the original was probably user-friendly. If it reads as nonsense, the original was blame language.

### 3. State the problem in user terms, not internal terms

The user sees:
> "Couldn't connect to the database. Try again in 30 seconds."

The log sees:
> `ERROR svc=auth method=login userId=12345 cause=ECONNREFUSED host=db-primary:5432`

### 4. Error codes — naming conventions

- **UPPER_SNAKE_CASE** for the identifier (`INVALID_API_KEY`, not `invalid-api-key`).
- **Stable across versions** — once published, never rename.
- **Categorized by prefix** — `AUTH_*`, `RATE_*`, `VALIDATION_*`.
- **Documented** — every code has a docs page explaining what triggers it.

### 5. Provide a concrete next action, or admit you cannot

A complete next-action clause names one of:
- **A retry hint with a time bound**: "Try again in 30 seconds." Not "try again later."
- **A specific input fix**: "Add an @ symbol to your email."
- **An escalation path with diagnostic info**: "Contact support and include request ID `req_abc123`."

### 6. Conservative punctuation

The Google Developer Documentation Style Guide is explicit: avoid exclamation points in error messages. They read as shouting, performative panic, or sarcasm.

Also avoid:
- **ALL CAPS for emphasis**: reads as shouting.
- **Ellipses for trailing-off**: reads as passive-aggressive.

### 7. i18n considerations

- **Avoid contractions** where translation may be awkward ("can't" → "cannot").
- **Avoid idioms** ("hit a snag", "ran into a wall"). They do not translate.
- **Avoid concatenation in code** ("Error: " + fieldName + " is invalid"). Breaks grammatical agreement in gendered languages.
- **Plan for pluralization complexity**. Use ICU MessageFormat or equivalent.

### 8. NN/g hostile patterns — what never to ship

- **Mockery**: "Oops! Something went terribly wrong! 😱"
- **Self-deprecation**: "Our bad! We messed up."
- **Vague hedging**: "An unexpected error occurred."
- **Exposed internals**: stack traces, internal class names, raw DB errors.
- **Marketing voice in failure**: "Thanks for your patience as we work to deliver an amazing experience!"

### 9. Form-validation errors — inline, contextual, specific

- **Inline, near the field**, not at the top of the form.
- **Specific to the field's actual requirement**. "Password must be at least 12 characters" not "Invalid password."
- **Suggest the fix when possible.**
- **Validate on blur, not on each keystroke.**

## Templates

### API error response body

```json
{
  "error": {
    "code": "INVALID_API_KEY",
    "message": "The API key you provided is not valid. Check that your key is set correctly in the Authorization header.",
    "status": 401,
    "request_id": "req_abc123",
    "docs": "https://docs.example.com/errors/INVALID_API_KEY"
  }
}
```

### Rewriting a blame-language error

| Before (blamey, internal-leaking) | After (user-voiced, specific, actionable) |
|---|---|
| "You entered an invalid email." | "Email must include an @ symbol (for example, alice@example.com)." |
| "Error: ECONNREFUSED" | "Couldn't connect to the database. Try again in 30 seconds. If this persists, contact support with request ID `req_abc123`." |
| "Invalid input." | "First name must be 1-50 characters and cannot contain digits." |
| "Please try again later." | "Try again in 30 seconds. If this persists for more than 5 minutes, see [status.example.com]." |

## References

- [Microsoft Writing Style Guide — Error Message Guidelines](https://learn.microsoft.com/en-us/windows/win32/debug/error-message-guidelines)
- [Google Developer Documentation Style Guide](https://developers.google.com/style)
- [NN/g — Error-Message Guidelines](https://www.nngroup.com/articles/error-message-guidelines/)
- [NN/g — Hostile Patterns in Error Messages](https://www.nngroup.com/articles/hostile-error-messages/)
