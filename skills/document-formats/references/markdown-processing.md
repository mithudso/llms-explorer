# Markdown Processing & ASTs (parsers · unified/remark/rehype · mdast↔hast · plugins)

Programmatically parse, transform, analyze, re-emit markdown — choose parser, work AST, write transforms. This reference owns *parse/transform-in-code*.
For *writing correct markdown / spec semantics* load `references/markdown-authoring.md`. For *rendering to safe HTML inside browser page or extension* (marked.js + DOMPurify + highlight.js, CSP, shadow DOM) use standalone `markdown-rendering-browser` skill. For *Markdown+JSX* load `references/mdx.md`.

---

## 1. Choosing a parser (the decision that matters most)

| Library | Model | Use when | Notes |
| --- | --- | --- | --- |
| **marked** | md → HTML string (sync, tiny, fast) | "just render markdown to HTML, fast, minimal deps" | No real AST; lexer→renderer. Override `renderer`/`walkTokens`. **Not** safe by default → sanitize. |
| **markdown-it** | md → **token stream** → HTML | configurable rendering + huge plugin ecosystem | Powers VitePress, mkdocs-material-ish tooling. `md.use(plugin)`, `md.renderer.rules`. CommonMark + opt-in GFM bits. |
| **micromark** | low-level **tokenizer**, md → HTML | small/safe/streaming md→HTML with CommonMark/GFM/MDX compliance | Powers remark's parsing. Use directly if no tree needed. Safe by default (escapes raw HTML unless told otherwise). |
| **unified + remark + rehype** | md → **mdast** → (bridge) → **hast** → HTML/other | transform, lint, analyze, or convert across formats | Plugin framework. Slower, but only one with real walkable transformable syntax tree. |
| **goldmark** (Go) | AST | Go services; powers **Hugo** | CommonMark + extensions. |
| **comrak** / **pulldown-cmark** (Rust) | AST / events | Rust; CommonMark 0.31.2 + GFM | comrak mirrors cmark-gfm. |
| **python-markdown**, **markdown-it-py**, **mistune** | varies | Python; markdown-it-py powers MkDocs/Material | markdown-it-py is markdown-it port. |
| **cmark / cmark-gfm** (C) | reference | embedding canonical parser | GitHub uses cmark-gfm. |

**Rule:** *render only* → marked (fast) or markdown-it (pluggable). *Transform / analyze / lint / cross-format* → unified/remark/rehype. *Low-level, safe, no tree* → micromark. *Non-JS* → goldmark/comrak/python-markdown.

---

## 2. The syntax-tree model (unist → mdast / hast)

unified ecosystem standardizes on **unist** (Universal Syntax Tree). Every node:

```js
{ type: 'heading', depth: 2, children: [ { type: 'text', value: 'Hi' } ],
  position: { start: {line,column,offset}, end: {…} } }
```

- **mdast** = Markdown AST. Node types touched most: `root`, `heading`, `paragraph`, `text`,
  `list`/`listItem`, `code` (with `lang`/`meta`), `inlineCode`, `link`, `image`, `emphasis`, `strong`,
  `blockquote`, `thematicBreak`, `table`/`tableRow`/`tableCell` (GFM), `delete` (GFM strikethrough),
  `footnoteReference`/`footnoteDefinition`, `html` (raw), `definition`.
- **hast** = HTML AST (`element`/`text`/`root`, `tagName`, `properties`). Transform target before stringifying HTML.
- Sibling trees: **xast** (XML), **nlcst** (natural language). Utilities span all (`unist-util-*`).

Key utilities: `unist-util-visit` (walk/mutate by node type), `unist-util-visit-parents`,
`unist-util-select` (CSS-like queries), `mdast-util-to-string` (node→plain text), `mdast-util-toc` (build TOC).

---

## 3. The unified pipeline

Mental model: **parser → transformers → compiler.** Each `.use()` adds plugin.

```js
import { unified } from 'unified'
import remarkParse from 'remark-parse'        // md text  → mdast
import remarkGfm from 'remark-gfm'            // tables/strike/tasklists/autolinks/footnotes
import remarkRehype from 'remark-rehype'      // mdast    → hast   (the bridge)
import rehypeSanitize from 'rehype-sanitize'  // hast scrub (XSS-safe)
import rehypeStringify from 'rehype-stringify'// hast     → HTML string

const file = await unified()
  .use(remarkParse)
  .use(remarkGfm)
  .use(remarkRehype, { allowDangerousHtml: false })
  .use(rehypeSanitize)            // ← keep this when input is untrusted
  .use(rehypeStringify)
  .process('# Hello *world*')
console.log(String(file))
```

- `remark()` = shortcut preset (parse + stringify back to **markdown** — use for md→md transforms/formatting).
- `.process()` (async) vs `.processSync()`. Plugins run in order; transformers mutate shared tree.
- Bridge (`remark-rehype`) = where markdown-land (mdast) becomes HTML-land (hast). Cross-format conversion (HTML→md) goes other way via `rehype-remark`.

---

## 4. Writing a transform (plugin)

remark/rehype plugin = function returning transformer `(tree, file) => void`:

```js
import { visit } from 'unist-util-visit'

/** Add rel="nofollow" to every external link. */
export default function remarkExternalLinks() {
  return (tree) => {
    visit(tree, 'link', (node) => {
      if (/^https?:\/\//.test(node.url)) {
        node.data ??= {}
        node.data.hProperties = { ...(node.data.hProperties||{}), rel: 'nofollow', target: '_blank' }
      }
    })
  }
}
```

Common off-the-shelf plugins: `rehype-slug` (+`rehype-autolink-headings`) for anchored headings,
`remark-frontmatter` (parse `---` blocks), `remark-toc` (insert TOC), `rehype-highlight` /
`rehype-pretty-code` / `@shikijs/rehype` (syntax highlighting), `rehype-raw` (re-parse raw HTML
inside markdown — pair with sanitize), `remark-lint-*` (linting; see `references/markdown-linting.md`).

---

## 5. Recipes

```js
// md → sanitized HTML with GFM (the safe default)
unified().use(remarkParse).use(remarkGfm).use(remarkRehype).use(rehypeSanitize).use(rehypeStringify)

// md → markdown (reformat / normalize / programmatic edit)
remark().use(remarkGfm).process(src)            // mdast round-trips back to md

// md → plain text (strip all formatting)
import { toString } from 'mdast-util-to-string'  // toString(tree)

// extract frontmatter
import matter from 'gray-matter'                 // { data, content } — then parse content
// or remark-frontmatter + remark-parse-frontmatter inside the pipeline

// HTML → markdown
unified().use(rehypeParse).use(rehypeRemark).use(remarkStringify).process(html)

// build a table of contents from headings
import { toc } from 'mdast-util-toc'             // toc(tree).map
```

**markdown-it flavor** (token stream, not nested tree):
```js
import MarkdownIt from 'markdown-it'
const md = new MarkdownIt({ html: false, linkify: true, typographer: true }).use(somePlugin)
md.render('# hi')                 // → HTML
md.parse('# hi', {})              // → flat token array (inspect/transform tokens)
md.renderer.rules.heading_open = (tokens, i, opts, env, self) => { /* custom */ }
```

---

## 6. Safety & performance

- **Never trust untrusted markdown.** Raw HTML passes through (CommonMark allows it). For untrusted input either disable HTML (`remarkRehype({ allowDangerousHtml: false })`, micromark default) **or** sanitize HTML output (`rehype-sanitize` server/Node; DOMPurify in browser — see `markdown-rendering-browser`). marked and markdown-it **not** safe by default.
- **`rehype-raw` re-enables raw HTML** — always pair with `rehype-sanitize` downstream.
- **Performance:** marked / markdown-it fastest (single pass to HTML). unified pipeline slower (parse → mdast → hast → stringify) but only one with transformable tree — pay that cost only when actually transforming/analyzing. micromark sits between for plain rendering.
- **Positions** (`node.position`) enable source-mapping for linters and editor tooling; `remark-parse` records by default.

---

## Sources
- [unifiedjs.com](https://unifiedjs.com/) · [Learn: intro to unified](https://unifiedjs.com/learn/) · [remark](https://github.com/remarkjs/remark) · [remark-rehype](https://github.com/remarkjs/remark-rehype)
- [micromark](https://github.com/micromark/micromark) · [mdast spec](https://github.com/syntax-tree/mdast) · [hast spec](https://github.com/syntax-tree/hast) · [unist](https://github.com/syntax-tree/unist) · [unist-util-visit](https://github.com/syntax-tree/unist-util-visit)
- [markdown-it](https://github.com/markdown-it/markdown-it) · [marked](https://github.com/markedjs/marked) · [rehype-sanitize](https://github.com/rehypejs/rehype-sanitize)
- [goldmark (Go)](https://github.com/yuin/goldmark) · [comrak (Rust)](https://github.com/kivikakk/comrak) · [npm-compare: markdown-it/marked/remark/unified](https://npm-compare.com/markdown-it,marked,remark,remark-parse,unified)