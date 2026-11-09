# llms file format v3: single file or family, sitemap, resources

Version 3.0.0, 2026-11-06. This is the project’s v3 convention, not an official revision of the llmstxt.org specification. Every skill in the `llms-txt-tooling` hub that writes llms files
follows this page. When a spoke's own reference disagrees with this page, this page wins and the
spoke needs an update.

The bundled linter implements part of this page. Optional Global AI Hub tools implement other parts.
`scripts/llms_lint.py` checks single files, sitemaps and the family index's sitemap link
(pass P16). The `scripts/docset_refine` export writes `llms-sitemap.txt` to section 4. It departs
from this page twice. It never collapses a small family into one file, because that repo's
readers open `llms-full.txt` and `manifest.json` by name. It also budgets `llms-small.txt` at
200,000 characters, not 8,000 bytes.

## 1. Pick the shape: one file or a family

Measure before you write. Count the bytes the output would hold if you wrote it as one file:
facts, condensed sections, sitemap and resources.

| Condition | Shape |
|---|---|
| The input is one document (a page, a PDF, one note, one report) | **single file** |
| The whole output fits in 32,000 bytes (about 8,000 tokens) and the sitemap has at most 200 entries | **single file** |
| Anything larger | **family** |

The 32,000-byte cap in section 2 applies to every single file, including one built from a single
document: condense the output until it fits. `llms_lint.py` reports a larger single file as High.

Why this split:

- A reader with no repo pays one fetch for a single file. A family costs at least two: the index,
  then the page it points at. A first read costs about $4 per million tokens (the cache-write
  rate in `llms-usage-guidance`), so loading an 8,000-token file whole costs about $0.03. This
  page assumes that costs less than the extra round trip a family needs.
- Small families gave nothing to their readers. In the 2026-09-27 measurement (see the
  `llms-usage-guidance` skill) the `llms-small.txt` digests of two small repos were 813 and 838
  bytes and held none of the 12 lookup answers. Splitting small material makes thin files.
- Families pay when the full text is larger than a reader should load at once. Then a cheap
  index, a budgeted `llms-small.txt` and searchable `llms-full.txt` / `llms-facts.txt` let the reader
  load only what the question needs.

A producer that cannot know the size in advance writes the family, then collapses it. If the
family totals at most 32,000 bytes and its sitemap has at most 200 entries, the producer merges
the files into one `llms.txt` and deletes the sibling `llms-*.txt` files. Other files, such as
`manifest.json` or `filemap.json`, stay.

## 2. Single-file format (`llms.txt`, lint kind `single`)

```
# <Name>

> <What this is and who it is for, in one paragraph.>
> Source: <path or URL>[ @ <short commit>] · Generated: <YYYY-MM-DD> by <skill> v<version> · Mode: single-file

## Facts
- Misbelief: <wrong belief>. Actually: <correction>. [src: ...]
- <one atomic claim per line, each with its provenance tag>

## <Topic sections, optional: condensed content, code verbatim>

## Contested
<optional; rules under "The ## Contested section" below>

## Sitemap
- <path or URL> — <title or one-line role>

## Resources
<see section 4>

## Optional
- [<title>](<url>): <links a reader may skip, per llmstxt.org>
```

Rules: at most 32,000 bytes and at most 200 `## Sitemap` entries. `## Facts`, `## Sitemap` and
`## Resources` are required; for a one-document input the sitemap lists that one source.
`Misbelief:` lines come first in Facts.
No sibling `llms-*.txt` files exist next to a single-file `llms.txt`.

### The `## Contested` section (both shapes)

The section holds controversies, open questions and common misbeliefs. Stele `KNOW-326` and
the `llms-txt-tooling` hub's shared contract define it.

- **Where.** In a single file, after the topic sections and before `## Sitemap`. In a family,
  last in `llms-full.txt`. Category layouts use one `<project>_contested_llms.md` file instead.
- **Line format.** Each line starts with its kind tag:
  `Misbelief: <wrong>. Actually: <right>.`,
  `Controversy: <claim>. <side A> (<source>) vs <side B> (<source>).`, or
  `Open question: <unknown>.`
- **Order.** Misbeliefs, then controversies, then open questions.
  `llms-concept-abstractor` puts open questions before its `### c<n>` conflict groups.
- **Evidence.** A line needs a source that states the dispute, the gap or the correction.
  A misbelief also needs evidence that someone holds it.
- **Empty.** If no line qualifies, omit the section. Do not write "None found".
- **Facts copy.** Each `Misbelief:` line also goes to `## Facts` (single file) or
  `llms-facts.txt` (family), first in the list, so Placement can lift it into CLAUDE.md.
  Controversies and open questions never go to Facts or CLAUDE.md.

## 3. Family format

| File | Job | Cap |
|---|---|---|
| `llms.txt` | index: purpose paragraph, one link line per section, a link to every sibling, including `llms-sitemap.txt` and `llms-sitemap.txt#resources` | 2,000 bytes for repo crawls; never more than 10,000 bytes |
| `llms-full.txt` | complete condensed reference, `## Contested` last | uncapped |
| `llms-small.txt` | budgeted digest | 8,000 bytes (`docset_refine` export: 200,000 characters) |
| `llms-facts.txt` | atomic claims, one per line, tagged; every `Misbelief:` line | uncapped |
| `llms-sitemap.txt` | every page or file, then `## Resources` (section 4) | uncapped |
| producer extras (`llms-indexes.txt`, `llms-infra.txt`, `llms-history.txt`, `llms-executable.txt`, `llms-vocabulary.txt`) | as each spoke defines | as defined |

`llms-sitemap.txt` replaces `llms-filemap.txt` and any URL or link list a producer used to write.
The per-file detail cards that `llms-filemap.txt` carried move to `llms-full.txt` under `## Files`
and to `filemap.json`; the sitemap keeps one line per file.

## 4. `llms-sitemap.txt` (lint kind `sitemap`) and the `## Resources` section

```
# <Name> — sitemap

> Source: <root URL, or repo path @ short commit> · Generated: <YYYY-MM-DD> by <skill> v<version>
> Kind: website | repo | store · Entries: <N>

## Pages
- <page URL> — <page title>

## Files
- <path relative to the root> — <one-line role, when known>

## Resources

### Related files
- <absolute path> — <why it helps: sibling repo, config, data dir, generated output>

### Scripts
- `<exact command>` — <what it does for this subject>

### Websites
- <url> — <official docs, spec, dashboard, upstream repo>

### Guides
- <path or url> — <how-to, runbook, wiki page>

### Skills
- `<skill-id>` — <when to load it for this subject>

### Agents and tools
- `<agent name or MCP tool>` — <when to use it>

### Other
- <anything else outside the root that a reader would want>
```

Set `Kind:` to one of the three values. Use `## Pages` for `website` and `## Files` for `repo` or
`store`. Write each heading exactly as shown: the linter matches heading text, so a note on the
heading line hides the section. List each target once. Website targets are http(s) URLs. Write
every `## Resources` entry as `- <target> — <why>`, with a spaced em dash, and put no prose lines
there. `Related files` targets are absolute paths.

Completeness rules:

- **Website:** list every page the crawl or `firecrawl map` (or `sitemap.xml`) found, not a sample.
  Group under `###` headings by path prefix when the site has more than 200 pages.
- **Repo:** list every tracked file (`git ls-files`), or every file `find` returns for a
  non-git directory after the producer's exclusions. Group under `###` headings by top-level
  directory.
- **Entries:** in every sitemap, `Entries:` must equal the number of `- ` lines under
  `## Pages` / `## Files`, including lines under `###` group headings.
- **Resources** point outside the root. Verify each one when you write it: the local path
  exists, the URL resolved during this run, the skill or agent is installed. Mark anything you
  could not verify `(unverified)`. Omit empty subsections. Never write secret values.
  `## Resources` itself is required: if nothing qualifies, write one `### Other` entry, such as
  `- (none) — no related file or tool could be verified`, as the `docset_refine` export does.
- A single-file `llms.txt` lists the same entries under `## Sitemap` and carries `## Resources`
  inline (section 2).

## 5. Readers: look for llms files first, sized

A skill that works on a subject should check for that subject's llms files before reading raw
material, then open them by size (rules in the `llms-usage-guidance` skill):

1. Look for, in order: the subject's `llms.txt` (repo root, `~/.global-ai-hub/skills.llms/<owner>-<repo>.repo/`,
   `~/.global-ai-hub/llms-concepts/<slug>.llms/`, a docs site's `/llms.txt`), memory-central rows
   (`keyword_index.py query … --prefix ~/.llms`), and hub indexes (`hub_query_docset`,
   `hub_search_keyword`, `hub_search_codebase`).
2. Size first (`wc -c`, or `x-markdown-tokens` on a remote). Read a file whole only when it fits;
   otherwise search it.
3. Prefer `llms-facts.txt` and `llms-sitemap.txt` for lookups; `llms-small.txt` is a map, not a fact store.
4. If you have the repo, the code is still the authority: llms files are a shortcut to the right
   file, and every fact you act on gets verified against its `path:line`.

## 6. Migration

- `scripts/llms_lint.py` accepts `llms-filemap.txt` as a legacy alias of `sitemap` and reports
  a Low finding asking for the rename. It runs no other sitemap check on that file, so lint the
  regenerated `llms-sitemap.txt` instead.
- Rewriting an existing family (`--refresh`) writes `llms-sitemap.txt` and removes `llms-filemap.txt`.

## 7. Lint

Run the bundled linter from the installed skill directory:

```
python3 scripts/llms_lint.py check <file or directory>
```

It detects the kind from the file name and shape; `--kind sitemap` or `--kind single` forces one.
A directory argument checks every `llms*.txt` below it. Exit status 1 means a High finding
remains. The linter flags an index above 10,000 bytes and an `llms-small.txt` above 200,000
characters. It does not check the 2,000-byte index cap or the 8,000-byte `llms-small.txt` cap;
measure those with `wc -c`.
