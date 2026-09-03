# Markdown Authoring & the Spec (CommonMark · GFM · flavors · frontmatter)

How to **write correct, portable markdown** and reason about which syntax renders where.
This reference owns *authoring + specification semantics*. For programmatic parsing /
AST transformation (remark, unified, markdown-it, mdast↔hast) load
`references/markdown-processing.md`. For rendering markdown to safe HTML *in a browser
page or extension* (marked.js + DOMPurify + highlight.js) use the standalone
`markdown-rendering-browser` skill. For Markdown+JSX components load `references/mdx.md`.

---

## 1. The spec landscape — why "markdown" is ambiguous

There is no single markdown. Authoring well means knowing **which flavor your target renders**.

| Flavor | What it is | Spec status |
| --- | --- | --- |
| **Original Markdown** (Gruber, 2004) | The Daring Fireball syntax + `Markdown.pl`. Deliberately under-specified; "looks like what you mean." | Prose description only; many ambiguities (the reason CommonMark exists). |
| **CommonMark** | The rigorous standardization. **Current spec 0.31.2** (Jan 2024). Defines exact parsing for every edge case + a reference test suite (~650 examples). | The portable baseline. Implementations: cmark (C ref), markdown-it, comrak, commonmark.js, etc. |
| **GFM (GitHub Flavored Markdown)** | A **strict, optional superset of CommonMark** — everything CommonMark does, plus 5 spec'd extensions. | Formal spec at github.github.com/gfm (based on CommonMark 0.29). Engine: `cmark-gfm`. |
| **Pandoc Markdown** | The richest flavor — citations, footnotes, definition lists, fenced divs, attributes, many extensions toggled with `+ext/-ext`. | Defined by Pandoc's manual. See `references/markdown-pandoc.md` (planned). |
| **MultiMarkdown / Markdown Extra / kramdown** | Older extension sets (tables, footnotes, attribute lists). kramdown powers Jekyll. | Per-implementation. |
| **Obsidian / wiki flavors** | CommonMark + `[[wikilinks]]`, `==highlight==`, callouts, embeds, block refs. | Per-app. |
| **MDX** | Markdown where you can import and render JSX components. | mdxjs.com; see `references/mdx.md`. |

**Authoring rule of thumb:** write to **CommonMark core** for maximum portability; reach for GFM
extensions only when your target is GitHub or a GFM-compatible renderer; treat everything beyond
GFM (Pandoc/Obsidian/MDX features) as renderer-specific and verify before relying on it.

---

## 2. CommonMark core syntax (the portable baseline)

### Block-level

```markdown
# ATX heading H1   …   ###### H6      (space after # required; optional closing #'s)
Setext H1
========
Setext H2
--------

A paragraph is one or more lines of text separated from the next block by a blank line.

> Blockquote. Lazy continuation works;
> add `>` on each line to be safe. Blockquotes nest >>.

- Unordered list (-, +, or * — pick one and stay consistent)
  - Nested item: indent the marker under the start of the parent's text
1. Ordered list. The first number sets the start (`5.` starts at 5); the rest can all be `1.`.
1) Ordered lists can use `)` instead of `.`.

    Indented code block — 4 spaces (or 1 tab) of indentation.

```` ```lang ````  Fenced code block. The word after the fence is the **info string**
(used for syntax highlighting). Fences are ``` or ~~~ (3+). Use 4 backticks to wrap code
that itself contains a triple backtick.

---  ***  ___    Thematic break (horizontal rule): 3+ of -, *, or _ on their own line.
```

**Lists — the #1 source of "why did it render wrong":**
- **Tight vs loose.** No blank lines between items → *tight* (no `<p>` wrapping). Any blank line
  between items → *loose* (each item wrapped in `<p>`, more vertical space). This is intentional, not a bug.
- **Nesting** is by indentation aligned to the **start of the parent item's content**, not a fixed
  2/4 spaces. Under `1. ` (3 chars) a nested block indents 3 spaces; under `- ` it's 2.
- **A blank line + indentation** continues an item with a new paragraph, code block, or sub-list.

### Inline

```markdown
*emphasis* or _emphasis_      **strong** or __strong__      ***both***
`inline code`  ``code with a ` backtick``                  ~~deleted~~ (GFM)
[inline link](https://x.com "optional title")
[reference link][ref]      …      [ref]: https://x.com "title"   (defined anywhere)
[shortcut ref]             …      [shortcut ref]: https://x.com
<https://autolink.com>     <user@host.com>                   (CommonMark autolinks: angle brackets)
![alt text](image.png "title")
Hard line break: end a line with two trailing spaces␠␠ or a backslash\
Escape any punctuation with a backslash: \* \_ \# \` \[ \]
```

**Emphasis flanking rules (the intraword gotcha):** `_` will **not** create emphasis inside a word
(`snake_case_var` stays literal — by design), but `*` will (`a*b*c` → a<em>b</em>c). Prefer `**`/`*`
for inline emphasis inside identifiers; prefer `_` when you want literal underscores to survive.

**Raw HTML** is allowed inline and as blocks (CommonMark defines 7 HTML-block types). It passes through
verbatim — which is exactly why any renderer that accepts untrusted markdown **must sanitize the HTML
output** (see `markdown-rendering-browser` for the DOMPurify pattern; this is a real XSS vector).

---

## 3. GFM extensions (the 5 spec'd + GitHub platform features)

GFM adds exactly **five extensions** to CommonMark, all spec'd as a strict superset:

```markdown
| Column A | Column B | Right |      ← Tables: pipe-delimited; the divider row's
| :------- | :------: | ----: |        colons set alignment (left / center / right).
| cell     | cell     |  42   |        Escape a literal pipe in a cell with \|.

- [x] done task        - [ ] open task          ← Task lists (checkboxes).

~~struck through~~                              ← Strikethrough.

Bare URLs autolink: https://example.com         ← Extended autolinks (no angle brackets).

<title> and other disallowed raw HTML tags are filtered  ← Disallowed raw HTML (security).
```

**GitHub-platform features** (render on GitHub.com; *not* all part of the GFM spec proper — verify on other renderers):

- **Alerts / callouts** (shipped late 2023) — a blockquote whose first line is `[!TYPE]`. Five types,
  case-insensitive: `NOTE` (blue), `TIP` (green), `IMPORTANT` (purple), `WARNING` (yellow), `CAUTION` (red).
  ```markdown
  > [!WARNING]
  > Destructive action — cannot be undone.
  ```
- **Math** (shipped May 2022; new inline delimiters May 2023) — MathJax engine. Inline `$…$` or `` $`…`$ ``;
  block `$$…$$` or a ```` ```math ```` fenced block. Escape a literal `$` outside math.
- **Footnotes** — `text[^1]` … `[^1]: definition`.
- **Mentions / references** — `@user`, `#123`, `owner/repo#123`, commit SHAs (GitHub content only).
- **Emoji shortcodes** — `:rocket:` → 🚀 (GitHub content; not GFM spec).
- **Collapsible sections** — raw `<details><summary>…</summary> … </details>` HTML.
- **Auto-generated heading anchors** — GitHub slugifies headings (lowercase, spaces→`-`, punctuation
  dropped); link with `[jump](#my-heading)`.

---

## 4. Frontmatter (metadata blocks)

Not part of CommonMark — a convention consumed by static-site generators, Obsidian, Pandoc, and
doc tooling. Must be the **very first bytes** of the file.

```markdown
---
title: My Post          # YAML frontmatter (most common; --- delimiters)
date: 2026-06-02
tags: [markdown, docs]
draft: false
---
```

- **YAML** (`---`) — Jekyll, Hugo, Eleventy, Astro, Obsidian, Docusaurus, MkDocs.
- **TOML** (`+++`) — Hugo (and others) also accept TOML.
- **JSON** (`{ … }` or `;;;`) — some SSGs.

A bare markdown renderer (GitHub, marked, markdown-it) does **not** strip frontmatter — it renders the
`---` as a thematic break + text. Strip it with a frontmatter parser (`gray-matter` in JS,
`python-frontmatter` in Python) before rendering, or use an SSG that handles it. See
`references/markdown-processing.md` for the parse step.

---

## 5. Flavor compatibility cheat-sheet

| Feature | CommonMark | GFM | Pandoc | Obsidian | MDX |
| --- | :--: | :--: | :--: | :--: | :--: |
| Headings, lists, emphasis, links, code | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tables | ❌ | ✅ | ✅ (+ grid/multiline) | ✅ | ✅ |
| Task lists | ❌ | ✅ | ✅ | ✅ | ✅ |
| Strikethrough `~~` | ❌ | ✅ | ✅ | ✅ | ✅ |
| Footnotes `[^1]` | ❌ | ✅ (GitHub) | ✅ | ✅ | plugin |
| Alerts `> [!NOTE]` | ❌ | GitHub-only | ❌ | callouts `> [!note]` | plugin |
| Math `$…$` | ❌ | ✅ (GitHub) | ✅ | ✅ | plugin (remark-math) |
| Frontmatter | ❌ | ❌ (passthrough) | ✅ (YAML) | ✅ | ✅ |
| Wikilinks `[[…]]` | ❌ | ❌ | ❌ | ✅ | ❌ |
| JSX components | ❌ | ❌ | ❌ | ❌ | ✅ |
| Raw HTML | ✅ (passthrough) | ✅ (filtered) | ✅ | ✅ | JSX |

**Portability ladder:** CommonMark core → +GFM table/task/strike (very widely supported) → footnotes/math
(GitHub + Pandoc + plugins) → alerts/wikilinks/JSX (single-renderer). The further down, the more you must
verify on the actual target.

---

## 6. Authoring best practices

- **Pick a target, then a flavor.** "Renders on GitHub" ≠ "renders in npm README" (npmjs.com uses a
  different sanitizer) ≠ "renders in VS Code preview." When in doubt, stay on CommonMark core.
- **Reference-style links** keep prose readable and let you reuse/centralize URLs: `[text][id]` … `[id]: url`.
- **One blank line** between blocks; be deliberate about list tight-vs-loose.
- **Fence every code block with an info string** (` ```js `) so highlighters work and the language is explicit.
- **Escape table pipes** (`\|`) and **leading characters** that would start a block (`\#`, `1\.`) when you mean them literally.
- **Headings are anchors** — keep them unique and human (GitHub slugifies them for `#fragment` links).
- **Don't rely on trailing-whitespace hard breaks** (invisible, stripped by formatters); use a trailing `\` or restructure.
- **Lint for consistency** (markdownlint / remark-lint) — see `references/markdown-linting.md` (planned).

## 7. Common pitfalls

| Symptom | Cause | Fix |
| --- | --- | --- |
| `snake_case` renders as snake<em>case</em> | `_` intraword emphasis on a non-GFM renderer | use `` `code` `` or `\_`; GFM already ignores intraword `_` |
| List items collapse / extra gaps appear | tight-vs-loose flipped by a stray blank line | remove/add the blank line deliberately |
| Nested list flattens | indentation not aligned to parent content start | align to the parent marker width (e.g. 3 under `1. `) |
| Frontmatter shows as `---` + text | renderer doesn't strip frontmatter | parse with gray-matter / python-frontmatter first |
| Table doesn't render | missing the `|---|` divider row, or CommonMark (no tables) | add the divider; confirm a GFM renderer |
| Raw `<script>` survives | renderer didn't sanitize | sanitize output (DOMPurify) — never trust untrusted markdown |
| `$x$` shows literally | renderer has no math extension | GitHub/Pandoc render it; others need remark-math/KaTeX |

---

## Sources
- [CommonMark Spec 0.31.2](https://spec.commonmark.org/0.31.2/) · [commonmark.org](https://commonmark.org/)
- [GitHub Flavored Markdown Spec](https://github.github.com/gfm/) · [A formal spec for GFM (GitHub Blog)](https://github.blog/engineering/user-experience/a-formal-spec-for-github-markdown/)
- [Basic writing & formatting syntax — GitHub Docs](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax)
- [Alerts (GitHub Docs)](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#alerts) · [Writing mathematical expressions — GitHub Docs](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/writing-mathematical-expressions) · [Render math in Markdown (GitHub Changelog, 2022-05-19)](https://github.blog/changelog/2022-05-19-render-mathematical-expressions-in-markdown/)
- [cmark-gfm](https://github.com/github/cmark-gfm) · [comrak (CommonMark 0.31.2 + GFM)](https://github.com/kivikakk/comrak)
