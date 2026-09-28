# Lightweight Markup Languages (the markdown siblings: reST · AsciiDoc · Org · Textile · wiki)

Markdown siblings — other plain-text markup languages — and **when to choose one over markdown**.
Reference owns comparison/selection of markup *languages*. For markdown syntax load
`references/markdown-authoring.md`; for converting load `references/markdown-pandoc.md`
(Pandoc reads/writes most).

---

## 1. Why markdown isn't always the answer

Markdown optimizes for *easy writing* and *web rendering*, but **deliberately minimal** — no
native cross-references, includes, attributes, rich semantic model. Large technical manuals,
single-source publishing, structured authoring → heavier lightweight-markup often better.

## 2. The siblings

| Language | Origin / ecosystem | Strengths | Weaknesses | Choose when |
| --- | --- | --- | --- | --- |
| **reStructuredText (reST)** | Python/Docutils, **Sphinx** | Rich directives & roles (`.. note::`, `:ref:`), cross-refs, includes, extensible; Python-docs standard | Stricter/fiddlier syntax (indentation, underline-length for headings) | Python projects; API docs via Sphinx autodoc; large cross-referenced manuals |
| **AsciiDoc** | AsciiDoctor (Ruby/JVM/JS) | Powerful yet readable; includes, attributes, conditionals, admonitions, tables; great for books/manuals (DocBook/PDF) | Smaller ecosystem than markdown; another syntax to learn | Technical books, O'Reilly-style manuals, single-source to PDF/HTML/EPUB |
| **Org-mode** | Emacs | Outliner + docs + literate programming + agenda/tasks; babel code execution | Tied to Emacs for full power | Emacs users; literate programming; notes+tasks+docs in one |
| **Textile** | Older web CMSs | Compact inline syntax | Largely superseded by markdown | Maintaining legacy Textile content |
| **Wiki markups** (MediaWiki, Creole) | Wikis | Templates/transclusion; familiar to wiki editors | Per-engine dialects | Wiki platforms (MediaWiki etc.) |
| **MyST Markdown** | Sphinx/Jupyter | **Markdown with reST's power** — directives/roles in markdown syntax | Sphinx-centric | Want Sphinx/reST features but markdown ergonomics |
| **Typst** | Newer typesetting | Markup + programmable typesetting; fast; LaTeX alternative | Young ecosystem | Modern print/PDF typesetting without LaTeX |

## 3. Quick syntax contrasts

```rst
.. reStructuredText
Section Title
=============
.. note::
   An admonition with a directive.
See :ref:`other-section` for cross-reference.
```

```asciidoc
// AsciiDoc
= Document Title
== Section
[NOTE]
====
An admonition block.
====
<<other-section,See here>> for cross-reference.
:attribute: reusable value
```

```org
# Org-mode
* Top heading
** Sub heading
#+BEGIN_SRC python :results output
print("literate code that can execute")
#+END_SRC
```

Markdown equivalents (admonitions, cross-refs) renderer-specific extensions, not core — exactly gap reST/AsciiDoc fill natively.

## 4. Selection heuristics

- **Default to markdown/GFM** for READMEs, web content, chat, LLM context, most project docs.
- **reST + Sphinx** for Python API docs and big cross-referenced manuals (or **MyST** to keep markdown ergonomics with Sphinx power).
- **AsciiDoc** for books/manuals and serious single-source → PDF/EPUB/HTML.
- **Org-mode** if live in Emacs, want notes + tasks + literate docs unified.
- **Typst** for modern, programmable print/PDF without LaTeX.
- **Converting** between any → Pandoc (`references/markdown-pandoc.md`): e.g. `pandoc -f rst -t gfm`, `pandoc -f docbook -t asciidoc`.

## Sources
- [reStructuredText / Docutils](https://docutils.sourceforge.io/rst.html) · [Sphinx](https://www.sphinx-doc.org/) · [MyST Markdown](https://myst-parser.readthedocs.io/)
- [AsciiDoc / Asciidoctor](https://asciidoc.org/) · [Org mode](https://orgmode.org/) · [Typst](https://typst.app/docs/) · [Pandoc format support](https://pandoc.org/MANUAL.html#general-options)