---
title: "Microcopy and UI Writing"
description: "Microcopy is every word in a product that is not body content: the buttons, the field labels, the placeholder hints, the validation messages, the empty states, the toasts, the modal titles, the 404 pa"
---

# Microcopy and UI Writing

Microcopy is every word in a product that is not body content: the buttons, the field labels, the placeholder hints, the validation messages, the empty states, the toasts, the modal titles, the 404 pages. Collectively, microcopy is the voice of the product.

## Core concepts

### 1. The "verb the noun" rule for buttons

Buttons should describe the action they perform. The canonical shape is **verb + noun**.

| Weak | Stronger |
|---|---|
| OK | Save changes |
| Submit | Create account |
| Yes | Delete project |
| Done | Save and close |
| Continue | Continue to payment |

**Echo the action's verb in destructive confirmations.** If the dialog asks "Delete this project?", the destructive button says "Delete project," not "Yes" or "Confirm."

### 2. The "what you can do here" rule for empty states

1. **Name the absence** (one short line).
2. **Tell the user what this surface is for.**
3. **Give them the next action** (with a button when possible).

**Weak:** "No items."
**Stronger:** "No saved designs yet / This is where your saved email designs will live. / [Create your first design]"

### 3. The "be specific" rule for error and validation messages

Nielsen Norman Group's canonical four-part guideline:
1. **State what went wrong** in plain language.
2. **Explain why**, if useful.
3. **Tell the user how to fix it.**
4. **Don't blame the user.**

| Weak | Stronger |
|---|---|
| Invalid input. | Email must include an @ and a domain. |
| Error. | We couldn't reach the server. Check your connection and try again. |
| Password not accepted. | Password must be at least 12 characters and include a number. |

**Never use exclamation points in failure messages.**

### 4. The match-the-verb rule for destructive confirmations

| Part | Pattern | Example |
|---|---|---|
| Title | "Verb this [thing]?" | "Delete project Acme?" |
| Body | What happens, what is irreversible | "This will permanently delete all 47 issues, comments, and attachments. This cannot be undone." |
| Destructive button | The same verb, with the noun | "Delete project" |
| Dismissive button | "Cancel" | "Cancel" |

**Avoid:** "Are you sure?" as a title. "OK" / "Cancel" as button pair. "Yes" / "No" as button pair.

### 5. Tooltips, helper text, placeholders — distinct uses

| Pattern | Lives where | Example |
|---|---|---|
| **Label** | Above or beside the field. Never disappears. | "Project name" |
| **Helper text** | Below the field. Always visible. | "Letters, numbers, and dashes. 3-40 characters." |
| **Placeholder** | Inside the empty field. Disappears on focus. | `e.g., acme-prod-cluster` |
| **Tooltip** | On hover or info-icon click. | "Project name is used in URLs and CLI invocations." |

**Anti-pattern: Placeholder as label.** When the user starts typing, the label vanishes.

### 6. Toasts, banners, modals — match severity to surface

| Surface | When | Example |
|---|---|---|
| **Toast** (transient) | Successful actions, low-stakes info | "Saved" "Copied" "Invitation sent" |
| **Banner** (persistent strip) | Account-wide state, time-bound info | "Your trial ends in 3 days" |
| **Modal dialog** | Action requires confirmation, or blocks workflow | Destructive confirmations |

Toast copy is the shortest writing in the product. **Single word or short verb-noun phrase.** Past-tense for completed actions: "Saved" not "Your changes were saved successfully."

### 7. Consent, opt-in, opt-out — symmetry of choice

**The path to the more privacy-protective choice must not be harder than the path to the less privacy-protective choice.**

| Anti-pattern | Description | Fix |
|---|---|---|
| Confirmshaming | "No thanks, I don't want to save money" | "No thanks" — neutral phrase only |
| Pre-checked opt-in | Marketing-emails box pre-selected | Unchecked by default for non-essential consents |
| Buried "Reject all" | Big "Accept all" button, "Reject" hidden | Same visual weight, same number of clicks |

### 8. Voice and tone

NN/g's four dimensions to calibrate tone:
- **Funny vs Serious** — billing errors are serious; an empty state for a hobby app can be playful.
- **Formal vs Casual** — enterprise tools lean formal, consumer apps lean casual.

**When to drop humor entirely:** anything involving money, security, or privacy; anything destructive or irreversible; anything during an outage or sign-in failure.

## Button label rewrites

| Context | Weak | Strong |
|---|---|---|
| Create-flow primary | Submit | Create project |
| Save-flow primary | OK | Save changes |
| Destructive | Yes / Delete | Delete project |
| Sign-up primary | Sign up | Create free account |
| Multi-step next | Next | Continue to payment |
| Confirm purchase | Confirm | Place order — $42.00 |

## Anti-Patterns

- **"Submit"** — almost never the right word.
- **Placeholder-as-label** — field with no visible, persistent label.
- **Apologetic empty states** — "Oh no, you have no projects yet!"
- **"Are you sure?" as the only confirmation question** — vague.
- **Yes/No buttons on confirmation dialogs** — forces the user to re-read the title.
- **Exclamation points in error messages.**
- **Pre-checked marketing opt-ins.**

## References

- [Mailchimp Content Style Guide — Voice and Tone](https://styleguide.mailchimp.com/voice-and-tone/)
- [Shopify Polaris — Error Messages](https://polaris-react.shopify.com/content/error-messages)
- [Apple Human Interface Guidelines — Writing](https://developer.apple.com/design/human-interface-guidelines/writing)
- [Nielsen Norman Group — Error-Message Guidelines](https://www.nngroup.com/articles/error-message-guidelines/)
- Kinneret Yifrah — *Microcopy: The Complete Guide* (2nd ed.)
