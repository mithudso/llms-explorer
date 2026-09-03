# Docs-as-Code & Static-Site Generators (markdown as the content layer)

Docs treated like source code — **markdown files in git, built into site by SSG, reviewed via PR, deployed by CI**. Reference owns docs-as-code workflow and SSG selection. For markdown syntax load `references/markdown-authoring.md`; MDX specifics load `references/mdx.md`; prose/structure quality defer to `technical-writing-craft` hub (Diátaxis, heading discipline) — this reference: *plumbing*, not writing.

---

## 1. The docs-as-code workflow

1. **Author** markdown (+ frontmatter) alongside or near code.
2. **Review** via pull request (diffs, comments, approvals — same as code).
3. **Build** with SSG (markdown → static HTML/CSS/JS).
4. **Deploy** via CI to static hosting (GitHub/GitLab Pages, Netlify, Vercel, Cloudflare Pages, S3+CDN).
5. **Quality-gate** in CI: markdown lint (`references/markdown-linting.md`), link-check, spell/Vale prose lint, broken-anchor check.

Benefits: versioned with product, single source of truth, contributor-friendly, preview deploys per PR.
Content layer almost always **markdown/MDX + frontmatter**; SSG supplies nav, search, versioning, theming.

## 2. SSG landscape (2025–2026) — pick by ecosystem & need

| SSG | Stack | Sweet spot | Notes |
| --- | --- | --- | --- |
| **Starlight** (Astro) | Astro / JS | New OSS docs default in 2026 | Sidebars, search (Pagefind), i18n, versioning built in; MDX-native; islands for interactivity |
| **Docusaurus** | React / MDX | Feature-rich product docs | Meta-backed; versioning, i18n, search (Algolia), blog; tens of thousands of sites |
| **MkDocs + Material** | Python | Fast, beautiful, low-friction docs | Material theme redefined category; rich extensions (admonitions, tabs); great search |
| **VitePress** | Vue / Vite | JS-camp docs, fast dev | MkDocs-Material-like for Vite world; Vue components in markdown |
| **Hugo** | Go | Huge sites, speed-critical | Millisecond builds; templating power; steeper templating curve |
| **Eleventy (11ty)** | JS | Flexible, un-opinionated sites | Bring-your-own structure; many template languages |
| **Jekyll** | Ruby | GitHub Pages default, blogs | Native GH Pages support; mature; slower on large sites |
| **Sphinx** | Python | API/scientific docs (reST-first) | reStructuredText native; MyST adds markdown; autodoc; see `references/lightweight-markup-languages.md` |
| **Nextra / Mintlify** | React / hosted | Next.js docs / polished hosted docs | Nextra = Next.js+MDX; Mintlify = hosted, opinionated |

**Selection heuristic:** React shop → Docusaurus or Nextra. Best-in-class OSS docs, little config → Starlight or MkDocs Material. Vue/Vite → VitePress. Massive site, speed paramount → Hugo. Python/API docs from docstrings → Sphinx (+MyST). Hosted, zero-ops → Mintlify.

## 3. The content layer details

- **Frontmatter** drives per-page metadata (title, sidebar order, slug, tags, draft) — YAML near-universal; Hugo also takes TOML/JSON. See `references/markdown-authoring.md` §4.
- **MDX** (Docusaurus, Astro, Nextra, VitePress-via-Vue) lets docs embed live components — see `references/mdx.md`.
- **Cross-references & anchors** — SSGs slugify headings; prefer relative links to source `.md` files (many SSGs rewrite them) so links survive both in-repo and on built site.
- **Admonitions/callouts** — most doc SSGs support `:::note` / `> [!NOTE]` style callouts (syntax varies; Material uses `!!! note`, Docusaurus/Starlight use `:::note`).

## 4. CI quality gates (wire these once)

```yaml
# illustrative CI steps
- markdownlint '**/*.md'                 # style/consistency (references/markdown-linting.md)
- lychee --no-progress ./**/*.md         # link checker (or markdown-link-check)
- vale ./docs                            # prose linter (style guide enforcement)
- <ssg> build                            # fail the build on broken refs / missing pages
```

Per-PR **preview deploys** (Netlify/Vercel/Cloudflare Pages) let reviewers see rendered docs before merge — highest-leverage docs-as-code practice.

## Sources
- [Astro Starlight](https://starlight.astro.build/) · [Docusaurus](https://docusaurus.io/) · [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) · [VitePress](https://vitepress.dev/) · [Hugo](https://gohugo.io/) · [Eleventy](https://www.11ty.dev/) · [Jekyll](https://jekyllrb.com/) · [Sphinx](https://www.sphinx-doc.org/) / [MyST](https://myst-parser.readthedocs.io/)
- [Starlight vs Docusaurus (LogRocket)](https://blog.logrocket.com/starlight-vs-docusaurus-building-documentation/) · [Write the Docs: docs-as-code](https://www.writethedocs.org/guide/docs-as-code/)