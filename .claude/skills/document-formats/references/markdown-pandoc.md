# Pandoc — Universal Document Conversion (Markdown ↔ everything)

Pandoc: swiss-army converter. **Read one format, write another** through single internal AST. This reference owns Pandoc + format conversion. Plain-markdown syntax/flavors → `references/markdown-authoring.md`; JS remark/unified AST → `references/markdown-processing.md` (Pandoc = Haskell-world counterpart, own AST).

---

## 1. The model: reader → AST → writer

Pandoc parses input into **Pandoc AST** (typed doc tree), renders to output format. Conversion = reader + writer.

```bash
pandoc input.md -o output.docx              # format inferred from extensions
pandoc -f gfm -t html5 input.md -o out.html # explicit -f (from) / -t (to)
pandoc README.md -o readme.pdf              # md → PDF (needs a LaTeX engine, see §4)
```

- **Readers**: `markdown` (pandoc extended), `commonmark`, `commonmark_x`, `gfm`, `html`, `latex`, `docx`, `odt`, `epub`, `rst`, `org`, `mediawiki`, `textile`, `ipynb`, `csv`, `bibtex`.
- **Writers**: all above plus `pdf`, `pptx`, `beamer` (slides), `revealjs`/`s5` (HTML slides), `man`, `asciidoc`, `docbook`, `jats`, `icml`, `typst`.

## 2. Pandoc's Markdown flavor

Richest markdown flavor — CommonMark superset with toggleable extensions via `+ext`/`-ext`:

```bash
pandoc -f markdown+hard_line_breaks-yaml_metadata_block input.md -t html
pandoc -t commonmark_x input.md             # CommonMark + pandoc's extension set
```

Notable extensions: `pipe_tables`, `grid_tables`, `multiline_tables`, `footnotes`, `definition_lists`, `fenced_divs` (`::: warning … :::`), `bracketed_spans` (`[text]{.class}`), `attributes` (`# H {#id .cls}`), `tex_math_dollars` (`$…$`), `citations` (`[@key]`), `yaml_metadata_block`. Run `pandoc --list-extensions` for all + on/off defaults per format.

## 3. Filters, templates, metadata

- **Lua filters** (`--lua-filter=f.lua`) — transform AST in-process (no extra runtime); fast, modern default. **JSON filters** (`--filter=prog`) — any language reading/writing Pandoc JSON AST on stdin/stdout (e.g. `pandoc-crossref`).
- **Templates** (`--template=tpl`, `-V key=val`) — control output skeleton; `pandoc -D html5` dumps default template. Partials + variables drive layout.
- **Metadata** — YAML frontmatter or `--metadata-file`; drives title/author/date + template variables.
- **Citations** — `--citeproc` + `--bibliography=refs.bib` + CSL style (`--csl=style.csl`) renders `[@key]` citations + reference list (replaces old `pandoc-citeproc`).

## 4. Markdown → PDF (the common ask)

PDF goes through intermediate engine — pick with `--pdf-engine`:

| Engine | Path | Use when |
| --- | --- | --- |
| `pdflatex`/`xelatex`/`lualatex` | LaTeX (needs TeX install, e.g. TinyTeX) | best typography; xelatex/lualatex for Unicode/fonts |
| `weasyprint` | HTML/CSS → PDF (Python) | style with CSS, no LaTeX |
| `wkhtmltopdf` | HTML/CSS → PDF (WebKit) | legacy HTML→PDF |
| `typst` | Typst (fast, modern) | newer, fast, no TeX |
| `context` | ConTeXt | advanced layout |

```bash
pandoc doc.md -o doc.pdf --pdf-engine=xelatex -V mainfont="Helvetica"
pandoc doc.md -o doc.pdf --pdf-engine=weasyprint --css=style.css
```

## 5. Handy recipes

```bash
pandoc -s in.md -o out.html                       # -s = standalone (full doc, not a fragment)
pandoc -s --toc --toc-depth=2 in.md -o out.html    # table of contents
pandoc in.md -o slides.pptx                         # markdown → PowerPoint (see references/pptx.md)
pandoc in.md -t revealjs -s -o slides.html          # markdown → HTML slide deck
pandoc in.docx -t gfm -o out.md                     # Word → GitHub markdown (great for migrations)
pandoc in.md --embed-resources --standalone -o self-contained.html   # inline CSS/images/JS
pandoc in.ipynb -o notebook.md                      # Jupyter → markdown
```

## 6. When Pandoc vs the JS ecosystem

- **Pandoc** — cross-format conversion (docx/odt/epub/latex/pptx), academic/publishing pipelines, citations, PDF/print, CLI/CI batch. Heavier dep (Haskell binary + maybe TeX).
- **remark/unified** (`references/markdown-processing.md`) — in-JS transforms, web pipelines, custom plugins, Node toolchain outputting HTML.
- Both have real AST; choose by ecosystem + target formats.

## Sources
- [pandoc.org](https://pandoc.org/) · [MANUAL](https://pandoc.org/MANUAL.html) · [Markdown flavor + extensions](https://pandoc.org/MANUAL.html#pandocs-markdown) · [Lua filters](https://pandoc.org/lua-filters.html) · [Citations / --citeproc](https://pandoc.org/MANUAL.html#citations) · [Creating a PDF](https://pandoc.org/MANUAL.html#creating-a-pdf)