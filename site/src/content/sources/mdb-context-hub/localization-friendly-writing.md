---
title: "Localization Friendly Writing"
description: "Reference for writing source-language strings that translate cleanly into 30+ locales."
---

# Localization-Friendly Writing

Reference for writing source-language strings that translate cleanly into 30+ locales.

## The one rule: write so a translator can reorder, expand, and replace

Every translation operation needs three freedoms:
1. **Reorder** — subject-verb-object in English is not subject-verb-object in Japanese or German.
2. **Expand** — German, Russian, Finnish run 30–40% longer than English.
3. **Replace** — Plural forms, gendered forms, formal/informal address.

## Core concept 1 — The translation-friendly English rules

1. **One sentence, one idea.** Compound sentences with subordinate clauses become unparseable in OV languages.
2. **Subject-verb-object, in that order.**
3. **No idioms.** "Hit the ground running" has no German equivalent.
4. **No metaphors.** "Move the needle" requires a needle, which requires a gauge, which requires the metaphor to land.
5. **No cultural references.** No baseball, no Thanksgiving, no Marvel cinematic universe.
6. **Avoid humour and wordplay.** Puns are untranslatable by definition.
7. **No abbreviations the reader must decode.** "Q1," "EOY," "ASAP" — spell them out at first use.
8. **No phrasal verbs where a single verb works.** "Set up the account" becomes "create the account."
9. **No latinate jargon.** "Utilize" → "use." "Initiate" → "start."
10. **Active voice as the default.**

## Core concept 2 — ICU MessageFormat: plural

```icu
{count, plural,
  =0 {No items}
  one {# item}
  other {# items}
}
```

**Common mistake — only English plural categories:**
```icu
{count, plural,
  one {# item}
  other {# items}
}
```
This works for English. It silently breaks Russian, Polish, Arabic.

## Core concept 3 — CLDR plural categories

| Category | Used by | Example values |
|----------|---------|----------------|
| `zero` | Arabic, Welsh, Latvian | 0 (in some languages) |
| `one` | English, Spanish, French | 1 |
| `two` | Arabic, Welsh | 2 |
| `few` | Russian, Polish, Czech | 2–4 (Russian: 2, 3, 4, 22, 23, 24…) |
| `many` | Russian, Polish | 5+ in some languages |
| `other` | every language; required fallback | Everything else |

**`other` is required.** Every plural block must include `other`.

## Core concept 4 — ICU select and selectordinal

**`select`** is a switch over a string variable, typically used for gender:
```icu
{gender, select,
  female {She updated her profile.}
  male {He updated his profile.}
  other {They updated their profile.}
}
```

`other` is required even in `select`.

## Core concept 5 — Placeholders that survive translation

1. **Use named placeholders, not positional.** `{username}` survives word reorder. `%s %s` does not.
2. **Never concatenate.** `"Hello, " + username + "!"` forces English word order.
3. **Always provide a comment describing the placeholder.**

**Concatenation anti-pattern:**
```javascript
// BAD
const msg = t('error.prefix') + ' ' + filename + ' ' + t('error.suffix');

// GOOD
const msg = t('error.full', { filename });
// strings.en.json: { "error.full": "Could not save file {filename}." }
```

## Core concept 6 — Translator comments

Every non-trivial string gets a translator comment answering:
1. **What is this?** UI element type (button, error, tooltip, heading).
2. **What does the placeholder mean?** `{count}` = unread messages, integer ≥ 0.
3. **Where does it appear?**

## Core concept 7 — Pseudo-localization

Pseudo-localization is a smoke test that runs before any human translator sees the strings. It:
- **Expands every string 30–40%** to surface truncation bugs
- **Replaces ASCII characters with accented Latin equivalents**
- **Wraps every string with sentinels** like `[!! … !!]` to surface un-extracted strings

## Core concept 8 — RTL-friendly writing

1. **Avoid baked-in directional assumptions.** "Click the arrow on the right" becomes wrong in Arabic. Prefer "Click the arrow next to the search box."
2. **Numbers stay LTR inside RTL text.** This is automatic in Unicode bidi.

## Core concept 10 — Key naming conventions

```text
GOOD (semantic, namespaced):
  inbox.unread.label
  settings.security.two_factor.toggle
  errors.network.timeout.body

BAD (content-derived, fragile):
  "Save changes"           # key changes every time copy changes
  "msg1", "label2"          # opaque
```

**Three rules:**
1. **The key describes the role, not the content.**
2. **Namespace by feature, then by sub-feature.**
3. **Don't bury locale in the key.**

## Anti-patterns

| Anti-pattern | Why it fails | Fix |
|--------------|--------------|-----|
| Concatenating UI fragments | Word order is fixed by English | Single string with named placeholders |
| Positional `%s %s` | Translator can't reorder | Named `{username}`, `{date}` |
| Only `one` and `other` plural categories | Russian, Arabic, Polish break | Author all CLDR forms |
| No translator comment | Translator guesses; gets it wrong | Comment every non-trivial string |
| Idioms in source | No literal translation | Rewrite to the underlying meaning |
| Text baked into images | Untranslatable without re-rendering | HTML overlay or SVG `<text>` |

## References

- Unicode CLDR: [Plural Rules](https://cldr.unicode.org/index/cldr-spec/plural-rules)
- ICU: [Formatting Messages](https://unicode-org.github.io/icu/userguide/format_parse/messages/)
- Mozilla L10n: [Best practices for developers](https://mozilla-l10n.github.io/documentation/localization/dev_best_practices.html)
