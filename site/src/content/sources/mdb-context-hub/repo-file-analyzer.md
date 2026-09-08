---
title: "Repo File Analyzer"
description: "A lightweight, incremental repo intelligence skill. Walks a repository, analyzes each file, and stores the results in the mdb-context-hub file-analysis library via MCP tools. Does not write any files"
---

# Repo File Analyzer

A lightweight, incremental repo intelligence skill. Walks a repository, analyzes each file, and stores the results in the mdb-context-hub `file-analysis` library via MCP tools. Does **not** write any files to the analyzed repo.

## When to use this skill

- You want a quick, searchable per-file index of any repo without running the full repo-bootstrapper
- You want to understand what a specific file does without reading the whole codebase
- You want to find which files handle authentication, routing, database access, etc. across a repo
- You want to re-run the analysis after changing some files and only re-process what changed

## Required MCP

`mdb_context_hub` must be running (HTTP on `127.0.0.1:3939`). The skill uses these tools:
- `tam_get_file_analysis_state` — load previous file hashes for the repo
- `tam_save_file_analysis` — save a single file's analysis entry
- `tam_save_file_analysis_state` — persist updated hashes after the run
- `tam_list_file_analyses` — browse results after analysis
- `tam_search_file_analyses` — find files by keyword across all summaries
- `tam_delete_repo_file_analyses` — wipe a repo's data and start fresh

---

## File categories

Before analyzing anything, classify every file into one of four buckets. Process them in order: **skip → meta → high-signal → standard**.

### SKIP — never analyze

Do not call `tam_save_file_analysis` for any file matching these patterns:

| Category | Patterns |
|---|---|
| Lock files | `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `poetry.lock`, `Gemfile.lock`, `go.sum`, `cargo.lock` |
| Compiled/minified output | `*.min.js`, `*.min.css`, `*.bundle.js`, `*.js.map`, `*.css.map` |
| Auto-generated | `*.generated.*`, `*-generated.*`, `*.auto.*`, `*-auto.*`, any file with `// @generated` or `# @generated` header |
| Snapshots / fixtures | `*.snap`, files inside `__snapshots__/`, `__fixtures__/`, `test/fixtures/` |
| Binary assets | images (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.ico`, `.svg`), fonts (`.woff`, `.woff2`, `.ttf`, `.eot`), audio/video, PDFs |
| Version history | `CHANGELOG*`, `HISTORY*`, `RELEASES*`, `CHANGES*` |
| Dotfile boilerplate | `.gitignore`, `.gitattributes`, `.gitmodules`, `.editorconfig`, `.prettierrc*`, `.eslintrc*`, `.stylelintrc*`, `.babelrc*`, `.nvmrc`, `.tool-versions` |
| Environment | `.env`, `.env.*`, `.envrc` |
| IDE/OS noise | `.DS_Store`, `Thumbs.db`, `.idea/**`, `.vscode/**` |

### META — store content verbatim

These files contain high-value prose that should be preserved largely intact as the `summary`. Truncate at ~8 KB if the file is very long.

Patterns (matched against filename or relative path):
- `README*` (README.md, README.rst, README.txt, etc.)
- `CONTRIBUTING*`
- `ARCHITECTURE*`, `DESIGN*`, `OVERVIEW*`
- `CLAUDE.md`
- `LICENSE*` (store as-is; mark purpose `"docs"`)
- `docs/*.md` and `docs/**/*.md` (top-level docs folder)
- Any `.md` file in the **repo root** that is not in the SKIP list

Use these field values:
- `purpose: "docs"`
- `summary`: full file content (up to 8 KB; if longer, include first 4 KB + `"... [truncated]"`)
- `tags`: `["meta", "documentation"]` plus one of `["readme"]`, `["license"]`, `["contributing"]`, `["architecture"]` as appropriate
- `exports`: `[]`
- `dependencies`: `[]`

### HIGH-SIGNAL — deep analysis

These files justify 3–5 sentence summaries and complete export/dependency lists.

Patterns:
- Entry points: `index.*`, `main.*`, `app.*`, `server.*`, `__main__.py`, `cli.*`, `run.*`
- Service/business logic: `*.service.*`, `*.controller.*`, `*.handler.*`, `*.router.*`, `*.middleware.*`, `*.resolver.*`, `*.provider.*`
- Core models/schemas: `*.model.*`, `*.schema.*`, `*.entity.*`, `*.domain.*`
- Any file **over 200 lines** of non-test source code
- Files referenced by 3+ other files (if you can tell from imports)

For high-signal files:
- Write 3–5 sentence summaries covering: what it does, the key algorithm or pattern used, and any important side-effects or invariants
- List all named and default exports
- List all significant dependencies (external packages + key internal imports)
- Add a `"high-signal"` tag

### STANDARD — concise analysis

All remaining source files. Write 1–3 sentence summaries. List key exports and dependencies only.

---

## Workflow (execute exactly in this order)

### Step 1 — Identify the repo

Accept the repo path from the user or infer it from the working directory. Resolve to an absolute path. This becomes `repoPath` for all tool calls.

```bash
repoPath=$(pwd)   # or take from user
```

### Step 1.5 — Check if the repo is archived

**Do not proceed with a full analysis on an archived repo** — it wastes time and pollutes the library with stale data.

Check for archival using any available signal:

```bash
# Via GitHub CLI — pass OWNER/REPO slug, not a filesystem path
gh repo view "$(git -C "$repoPath" remote get-url origin 2>/dev/null | sed 's|.*github.com[:/]\(.*\)\.git|\1|;s|.*github.com[:/]\(.*\)|\1|')" \
  --json isArchived --jq '.isArchived' 2>/dev/null
# => prints "true" or "false"; silently fails if not a GitHub repo

# Fallback: look for common archive markers in the repo root
ls "$repoPath/ARCHIVED" "$repoPath/.archived" "$repoPath/DEPRECATED" 2>/dev/null
grep -i "archived\|deprecated\|no longer maintained" "$repoPath/README.md" 2>/dev/null | head -3
```

If the repo is determined to be archived:
1. Print: `⚠️  Repo appears to be archived. Skipping analysis to avoid storing stale data.`
2. Offer the user two options: **(a)** abort, or **(b)** continue anyway with a `"archived"` tag appended to all stored entries.
3. If the user chooses (b), proceed with all steps and add `"archived"` to every file's `tags` array.
4. If the user chooses (a) or gives no response, stop here.

### Step 2 — Load previous state

Call `tam_get_file_analysis_state` with `repoPath`. The response is:
```json
{ "repoPath": "...", "lastRun": "<ISO or null>", "files": { "src/foo.ts": { "hash": "...", "analyzedAt": "..." } } }
```

Store this as `previousState`. If `lastRun` is null, this is a first run.

### Step 3 — Walk the repo

Enumerate all files using:
```bash
find "$repoPath" -type f \
  -not -path "*/.git/*" \
  -not -path "*/node_modules/*" \
  -not -path "*/.next/*" \
  -not -path "*/dist/*" \
  -not -path "*/build/*" \
  -not -path "*/__pycache__/*" \
  -not -path "*/.venv/*" \
  -not -path "*/vendor/*" \
  -not -path "*/.idea/*" \
  -not -path "*/.vscode/*" \
  | sort
```

For each file, compute its SHA-256 hash:
```bash
shasum -a 256 "$filePath" | cut -d' ' -f1  # macOS
sha256sum "$filePath" | cut -d' ' -f1       # Linux
```

### Step 3.5 — Categorize every file

Before doing any analysis, classify each file into one of:
- `skip` — matches any SKIP pattern (see table above)
- `meta` — matches any META pattern
- `high-signal` — matches any HIGH-SIGNAL pattern
- `standard` — everything else that isn't skipped

Print the category counts before starting analysis:
```
Category breakdown:
  skip:        N files  (not stored)
  meta:        N files  (stored verbatim)
  high-signal: N files  (deep analysis)
  standard:    N files  (concise analysis)
```

### Step 4 — Determine which files need (re-)analysis

For each file in the `meta`, `high-signal`, and `standard` buckets, compare its hash against `previousState.files[relPath]?.hash`.

- **New file** (not in state): analyze
- **Changed file** (hash differs): analyze
- **Unchanged file** (hash matches): skip — do NOT call `tam_save_file_analysis` for it

Report the delta counts at the end.

### Step 5A — Store meta files

For each meta file that is new or changed:

1. Read the full file content
2. Truncate to 8 KB if needed (keep first 4 KB + `"\n... [truncated — full file is N lines]"`)
3. Call `tam_save_file_analysis`:

```json
{
  "repoPath": "<abs path>",
  "repoId": "<slug>",
  "filePath": "<relative path>",
  "language": "markdown",
  "summary": "<full file content, up to 8 KB>",
  "purpose": "docs",
  "exports": [],
  "dependencies": [],
  "tags": ["meta", "documentation", "<readme|license|contributing|architecture>"],
  "hash": "<sha256>"
}
```

### Step 5B — Analyze high-signal files

For each high-signal file that is new or changed:

1. Read the file content (skip if binary — check by extension or failed UTF-8 decode)
2. Generate a **deep** analysis:
   - **summary**: 3–5 sentences covering what it does, the primary pattern/algorithm, key side-effects or invariants, and any notable constraints
   - **purpose**: one of `entry-point`, `service`, `utility`, `config`, `test`, `type-definition`, `schema`, `migration`, `script`, `component`, `hook`, `middleware`, `model`, `controller`, `router`, `view`, `store`, `fixture`, `build`, `docs`
   - **exports**: all named and default exports
   - **dependencies**: all significant external packages and key internal imports
   - **tags**: 3–6 domain tags + `"high-signal"`
3. Call `tam_save_file_analysis` with this analysis.

### Step 5C — Analyze standard files

For each standard file that is new or changed:

1. Read the file content (skip binaries)
2. Generate a concise analysis:
   - **summary**: 1–3 sentences on what this file does
   - **purpose**: same label set as above
   - **exports**: key exports only
   - **dependencies**: notable imports only
   - **tags**: 2–5 domain tags
3. Call `tam_save_file_analysis`.

**Batch size**: Process in batches of 5–10 files to avoid context overflow. After each batch, continue immediately without pausing.

### Step 6 — Save updated state

After all files are processed, call `tam_save_file_analysis_state` with:
```json
{
  "repoPath": "<abs path>",
  "files": {
    "<relPath>": { "hash": "<sha256>", "analyzedAt": "<ISO timestamp>" },
    ...
  }
}
```

Include **all** files in the repo (not just the newly analyzed ones) — carry forward the hashes of unchanged files from `previousState.files`. Do **not** include SKIP-category files in the state (they are never stored and never need re-checking).

### Step 7 — Report

Output a summary:
```
Repo: <repoPath>
Files this run:
  meta (verbatim):     N (new: X, changed: Y, skipped-unchanged: Z)
  high-signal (deep):  N (new: X, changed: Y, skipped-unchanged: Z)
  standard (concise):  N (new: X, changed: Y, skipped-unchanged: Z)
  skipped (low-signal): N
Total in library: T
Languages: <comma-separated list>
```

Offer to let the user query with `tam_search_file_analyses` or `tam_list_file_analyses`.

---

## Tips for good analysis

- **Config files** (`package.json`, `pyproject.toml`, `tsconfig.json`): summarize key scripts and dependencies, not the full content; mark `purpose: "config"`
- **Test files**: note what is being tested and what mocking strategy is used
- **Type-definition files** (`.d.ts`, `types.ts`): list the main exported types/interfaces
- **Entry points** (`index.ts`, `main.py`, `app.js`): describe what the file bootstraps and which modules it composes — these are high-signal, treat accordingly
- **Middleware/handlers**: describe what request/response transformation it performs
- **Models/schemas**: list the fields and any validation rules

---

## Incremental re-run behavior

On subsequent invocations, the skill automatically:
1. Checks the repo for archival signals before doing any work
2. Loads the previous state via `tam_get_file_analysis_state`
3. Re-categorizes every current file (category can change if the file was renamed)
4. Only re-analyzes files whose hash changed or that are new
5. Skips files that were deleted from the repo (they remain in the library until `tam_delete_repo_file_analyses` is called)

To force a full re-analysis, call `tam_delete_repo_file_analyses` first, then re-invoke the skill.

---

## Example queries after analysis

```
# Find all authentication-related files
tam_search_file_analyses: { "query": "authentication auth login", "repoPath": "..." }

# Read the README content stored in the library
tam_search_file_analyses: { "query": "meta readme", "repoPath": "..." }

# List all high-signal files
tam_search_file_analyses: { "query": "high-signal", "repoPath": "..." }

# List all TypeScript files in the repo
tam_list_file_analyses: { "repoPath": "...", "language": "typescript" }

# Find entry points
tam_search_file_analyses: { "query": "entry-point bootstrap", "repoPath": "..." }

# See all repos with analysis data
tam_list_analyzed_repos: {}
```
