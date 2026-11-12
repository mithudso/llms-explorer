### Phase 2: Resolve Drive stubs (the step that makes this skill possible)

Most of the corpus is Google-native and **dataless on disk**:

| Extension | On-disk reality | How to read it |
|---|---|---|
| `.gdoc` `.gsheet` `.gslides` | ~179-byte placeholder; `cat`/`head` fail with `Error reading …` | resolve ID, then Drive |
| `.md` `.txt` `.csv` `.json` `.py` `.sh` `.tf` `.toml` `.mmd` | real bytes | read directly |
| `.pdf` `.docx` `.xlsx` `.pptx` `.ods` | real bytes | Drive by ID if it has one, else `document-conversion` (pdftotext/pandoc) |
| `.png` `.jpg` | real bytes | Drive read (vision) or skip with a card |
| `.zip` `.tgz` | real bytes | card only; never extract |

**A sidecar mirror is not an export.** An account whose folder carries a machine-generated
mirror (`12 Optimized Docs/`, `*.processed.md`, `*.extracted.txt`) looks like it has local
copies of every Google-native doc. It does not — those sidecars are ~1 KB digests, and
reading one instead of resolving the stub silently swaps the document for a summary of it.
Check the sidecar's size and generation date against the stub's `modifiedTime`: a mirror
older than the doc is superseded, and a mirror under a few KB is a digest, not content.

**Getting the Drive ID of a stub** — the file's contents are unreadable, but the ID is in
an extended attribute. **The attribute name ends in `#S`, and that suffix is part of the
name** — `xattr -p com.google.drivefs.item-id` (without it) fails with
`No such xattr: com.google.drivefs.item-id` on every file. Confirm the exact name with a
bare `xattr <file>` first:

```bash
xattr "<path/to/file.gdoc>"                              # lists: com.google.drivefs.item-id#S
xattr -p 'com.google.drivefs.item-id#S' "<path/to/file.gdoc>"
```

`xattr -p` accepts many paths at once and prints `path: value` per line, so resolve the
whole census in batches of a few hundred rather than one subprocess per file. A batch of
one prints the bare value with no `path: ` prefix — handle that case or single-stub
folders silently resolve to nothing.

Then read the content with the Google Drive MCP: `read_file_content(fileId)`. It handles
Docs, Slides, Sheets, PDF, docx, xlsx, pptx and images, and takes `includeComments` —
comments on an account doc are frequently where the real decision was made, so request
them for `context`, `weekly-update`, `rca` and `initiative` roles.

Operational realities to expect and handle:

- **Oversize results.** A large context file can exceed 100k characters and so exceeds the
  MCP result cap; the tool writes the full JSON to a `tool-results/` path and returns the
  path. Read it in sequential chunks until the whole thing is consumed, and record in the
  card whether the read was `full` or `partial`. Never summarize a partial read as if it
  were complete.
- **`gog` fallback.** The `gog` CLI (`gog -a <account> docs cat <docId>`,
  `gog drive get <fileId>`, `gog sheets`, `gog slides`) can substitute for the MCP, but on
  this machine it is installed and unauthenticated: it fails with `OAuth client
  credentials missing (OAuth client ID JSON).` Attempt it only if the MCP is unavailable,
  and report that exact error rather than concluding Drive is unreachable.
- **Cloud-only or missing xattr.** No `com.google.drivefs.item-id` and no readable bytes →
  card the artifact `[unresolved]`, keep it in the census, and count it in the report. An
  unresolved artifact is a known gap, not an absent one.
- `--no-drive-resolve` skips this phase entirely and produces a filename-level pack; say
  so loudly in the header, because such a pack is an index, not a truth pack.
