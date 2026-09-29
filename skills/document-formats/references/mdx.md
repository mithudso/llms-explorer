# MDX — Markdown for the Component Era (Markdown + JSX)

MDX lets you use **JSX components, imports/exports, and `{expressions}` inside markdown** — the
authoring format behind Docusaurus, Astro/Starlight, Next.js docs, and Storybook. This reference owns
MDX specifically. For plain-markdown syntax/spec load `references/markdown-authoring.md`; for the
markdown AST/parser ecosystem (remark/unified, on which MDX is built) load
`references/markdown-processing.md`; for in-browser render+sanitize use `markdown-rendering-browser`.

---

## 1. What MDX is (and isn't)

MDX is a superset of markdown that compiles to a **JavaScript/JSX module**. A `.mdx` file can:

```mdx
---
title: Hello
---
import { Chart } from './Chart.jsx'
export const year = 2026

# Hello {year}

Regular **markdown** prose, then a live component:

<Chart data={[1, 2, 3]} />
```

- Markdown becomes JSX elements; `{…}` are JS expressions; `import`/`export` are real ESM.
- It compiles to a component (e.g. a default export) you render in React/Preact/Vue/Solid (via the
  appropriate JSX runtime). **MDX is not a runtime string format** — it's compiled, like a `.jsx` file.
- Because it compiles to code, **MDX is not safe for untrusted input** — never compile user-submitted
  MDX (arbitrary import/JS execution). For untrusted markdown use a plain parser + sanitizer instead.

## 2. MDX 3 (current major) — what changed

MDX 3 is "a small major release" — modernization, not new syntax:
- **ES2024** in expressions (Acorn parses as ES2024).
- **Top-level `await`** in MDX is allowed (whether it *works* depends on your framework supporting async components/promises).
- **Block expressions** may sit directly next to block JSX (the old "blank line between `>` braces and tags" requirement is gone).
- **Cleaner codegen** — JSX pragma comment removed, object spreads instead of `Object.assign`, `'use strict'` added when needed.
- **Node 16+** required.

## 3. The component scope: `components` prop & `MDXProvider`

MDX maps markdown nodes to components you can override (e.g. render every `<h1>` or `<a>` with your design-system component):

```jsx
import Content from './post.mdx'
const components = { h1: MyH1, a: MyLink, Chart }
<Content components={components} />          // per-render override
// or app-wide via the provider:
import { MDXProvider } from '@mdx-js/react'
<MDXProvider components={components}><App/></MDXProvider>
```

Components referenced in MDX resolve from: in-file `import`s → the `components` prop → `MDXProvider` context.

## 4. How to compile / integrate

- **Core:** `@mdx-js/mdx` — `compile()` / `evaluate()` (the latter runs MDX at runtime against a JSX runtime; still don't feed it untrusted input).
- **Bundlers:** `@mdx-js/loader` (webpack), `@mdx-js/rollup`, `@mdx-js/esbuild`; Vite via `@mdx-js/rollup`.
- **Frameworks:** `@next/mdx` (Next.js), Astro `@astrojs/mdx` (Starlight is MDX-native), Docusaurus (MDX is its default doc format), Gatsby `gatsby-plugin-mdx`, Storybook docs.
- **Pipeline:** MDX is built on **remark** (markdown → mdast) + **rehype** (→ hast) + a JSX/estree stage, so remark/rehype **plugins compose** — `remark-gfm` for tables/footnotes, `remark-math`+`rehype-katex` for math, `rehype-slug`+`rehype-pretty-code` for anchored, highlighted docs.

```js
import { compile } from '@mdx-js/mdx'
import remarkGfm from 'remark-gfm'
const js = String(await compile(mdxSource, { remarkPlugins: [remarkGfm], jsxImportSource: 'react' }))
```

## 5. Authoring gotchas

| Gotcha | Detail |
| --- | --- |
| It's JS, not text | A stray `{` or `<` is parsed as expression/JSX. Escape `\{` or use `` `code` ``. |
| Indentation | 4-space indents can become a markdown code block; keep JSX flush-left. |
| Comments | Use `{/* JSX comments */}`, not `<!-- HTML comments -->` (HTML comments error in MDX 2/3). |
| Components must be in scope | An undefined `<Foo/>` throws at compile/eval — import it or pass via `components`. |
| Closing tags / self-close | JSX rules apply: `<br/>`, not `<br>`. |
| Untrusted input | Never compile/evaluate user MDX. Use plain markdown + `rehype-sanitize` instead. |

## Sources
- [mdxjs.com](https://mdxjs.com/) · [MDX 3 release notes](https://mdxjs.com/blog/v3/) · [mdx-js/mdx (GitHub)](https://github.com/mdx-js/mdx/) · [remark-mdx](https://mdxjs.com/packages/remark-mdx/)
- [Docusaurus: MDX & React](https://docusaurus.io/docs/markdown-features/react) · [Astro MDX integration](https://docs.astro.build/en/guides/integrations-guide/mdx/) · [@next/mdx](https://nextjs.org/docs/app/building-your-application/configuring/mdx)
