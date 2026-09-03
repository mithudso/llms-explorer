# Markdown Linting & Quality Gates (markdownlint · remark-lint · Vale · link-check)

Enforce **consistent, valid, well-styled markdown** in editors and CI. This reference owns markdown linting/quality tooling. For markdown syntax load `references/markdown-authoring.md`; for remark/unified plumbing load `references/markdown-processing.md`; for docs-as-code CI context load `references/markdown-docs-as-code.md`.

---

## 1. Two different jobs: structural lint vs prose lint

- **Structural/style lint** (markdownlint, remark-lint) — markdown *correctness & consistency*: heading increments, list marker style, blank-line rules, trailing spaces, fenced-code languages, line length.
- **Prose lint** (Vale, write-good, alex, proselint) — *writing quality*: style-guide terms, passive voice, inclusive language, banned words. Complementary, not substitute. Run both in docs CI.

## 2. markdownlint (the de-facto structural linter)

Rules `MD001`–`MD0xx` (e.g. `MD013` line-length, `MD025` single-H1, `MD040` fenced-code language, `MD033` no-inline-HTML). Two main runners:

- **markdownlint-cli2** (preferred CLI) and **markdownlint-cli**; also `markdownlint` library (Node) and VS Code extension (David Anson). Ports: `pymarkdownlnt` (Python), `mdl` (Ruby).

```jsonc
// .markdownlint-cli2.jsonc  (or .markdownlint.json / .yaml)
{
  "config": {
    "default": true,
    "MD013": { "line_length": 100, "code_blocks": false, "tables": false }, // relax line length
    "MD033": { "allowed_elements": ["details", "summary", "br"] },           // allow some inline HTML
    "MD041": false                                                            // first-line-H1 off (frontmatter)
  },
  "globs": ["**/*.md"],
  "ignores": ["node_modules", "CHANGELOG.md"]
}
```

```bash
npx markdownlint-cli2 "**/*.md"            # lint
npx markdownlint-cli2 --fix "**/*.md"      # auto-fix the fixable rules
```

Inline control: `<!-- markdownlint-disable MD013 -->` … `<!-- markdownlint-enable MD013 -->`, or `<!-- markdownlint-disable-next-line MD033 -->`.

## 3. remark-lint (lint inside the unified pipeline)

Already use remark (`references/markdown-processing.md`)? Lint as plugins on mdast:

```js
import { remark } from 'remark'
import remarkPresetLintRecommended from 'remark-preset-lint-recommended'
import remarkPresetLintConsistent from 'remark-preset-lint-consistent'

await remark()
  .use(remarkPresetLintRecommended)
  .use(remarkPresetLintConsistent)        // enforce whatever style the doc uses first
  .process(file)                          // messages attach to file.messages
```

Or via `remark-cli` + `.remarkrc`. Presets: `recommended` (catch real problems), `consistent` (match file's own first choice), or `remark-preset-lint-markdown-style-guide`. Hundreds of individual `remark-lint-*` rules compose. **markdownlint vs remark-lint:** markdownlint simpler/standalone, common choice; remark-lint right when markdown already flows through remark/unified build.

## 4. Link checking & prose linting

```bash
lychee --no-progress "**/*.md"             # fast Rust link checker (internal + external, anchors)
npx markdown-link-check ./README.md        # per-file link check (Node)
vale ./docs                                # prose style-guide linter (Vale + a style like Microsoft/Google)
```

Vale uses `.vale.ini` + style packages (Microsoft, Google, write-good). Standard for enforcing *writing* style guide; pair with markdownlint for full coverage.

## 5. Wire it into the workflow

- **pre-commit** (framework): hooks for `markdownlint-cli2`, `lychee`, `vale` — catch issues before commit.
- **CI** (`references/markdown-docs-as-code.md` §4): run lint + link-check + prose-lint as gates; fail on errors; run `--fix` locally but check (not fix) in CI.
- **Editor**: markdownlint VS Code extension surfaces rules live; format-on-save fixes easy ones.
- **Monorepos/docs**: scope globs to docs dir, ignore generated files (CHANGELOG, vendored content).

## Sources
- [markdownlint (rules)](https://github.com/DavidAnson/markdownlint) · [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2) · [rule reference](https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md)
- [remark-lint](https://github.com/remarkjs/remark-lint) · [remark-preset-lint-recommended](https://github.com/remarkjs/remark-lint/tree/main/packages/remark-preset-lint-recommended)
- [Vale](https://vale.sh/) · [lychee link checker](https://github.com/lycheeverse/lychee) · [pre-commit](https://pre-commit.com/)