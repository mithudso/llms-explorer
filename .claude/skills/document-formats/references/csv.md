<!-- hub-reference-banner -->
> **Reference file — part of the `document-formats` hub.** Formerly the standalone `csv` skill.
> Sibling topics in this family are now reference files under the hubs (`document-formats`) — **not** standalone
> skills. Ignore any "use the X skill" / `related_skills` / SKIP pointers below that name a bare sibling
> skill; load that topic's `references/<name>.md` from the owning hub (see the hub's "Cross-hub map").

---

---
name: csv
version: "1.1.0"
updated: "2026-05-29"
category: developer
tags: [csv, tsv, parsing, encoding, streaming, data-processing, pandas, polars, duckdb, formula-injection, csvkit, qsv]
description: "CSV/TSV expert — parse, generate, validate, convert, and stream delimited-text files in Python and Node.js. TRIGGER: user wants to parse, generate, transform, validate, or stream CSV/TSV data; handle encoding issues (BOM, UTF-8, Windows-1252); convert between CSV and JSON/Parquet/XLSX/SQL/NDJSON; sanitize CSV exports against formula-injection (CWE-1236); use CLI tools (csvkit, qsv, miller, DuckDB); troubleshoot parse errors (misaligned columns, garbled text, scientific notation, CR-only line endings, ragged rows); performance-sensitive CSV work (chunked pandas reads, Polars lazy scanning, backpressure Node.js pipelines). SKIP: deliverable is an Excel workbook with cell formatting, formulas, or charts (use xlsx skill); CSV is a side-effect of a broader ETL or ORM task where the format itself is not the concern; user needs Word/PDF output and mentions CSV only as a data source."
related_skills: [xlsx, pdf, docx, json-advanced, python-patterns]
whenToUse:
  - "parse a CSV file in Python"
  - "parse a CSV file in Node.js"
  - "handle BOM or encoding issues in CSV"
  - "stream a large CSV without loading it into memory"
  - "convert CSV to JSON, Parquet, or Excel"
  - "sanitize CSV against formula injection"
  - "fix garbled or misaligned CSV"
  - "use DuckDB, qsv, or miller to query a CSV"
  - "write CSV with correct line endings and encoding"
  - "troubleshoot CSV parse errors"
---

# CSV Expert Skill

## When NOT to use

- Deliverable is an Excel workbook with cell formatting, formulas, or charts → use `xlsx`
- CSV is a minor side-effect of a broader ETL, ORM, or database migration task where the format itself is not the concern
- User needs Word/PDF output and mentions CSV only as a data source

## Execution sequence

1. Read `context.md` in this directory before writing any code — it contains authoritative API references, option tables, security patterns, and performance benchmarks.
2. Select the right tool using the Key Decisions table below.
3. Apply all Critical Rules — treat violations as bugs, not style issues.
4. Validate output against the checklist at the bottom of this file before returning.

## Knowledge index (`context.md`)

- RFC 4180 formal grammar and quoting rules (ABNF)
- Node.js parsers: csv-parse, PapaParse, fast-csv, d3-dsv (all options, streaming, workers)
- Python parsers: csv module, pandas.read_csv, Polars scan_csv, DuckDB read_csv
- Browser-side parsing with PapaParse Web Workers
- CLI tools: csvkit, qsv, miller, DuckDB CLI (commands, flags, performance numbers)
- Writing/generation: csv-stringify, fast-csv format, pandas.to_csv, Polars write_csv
- Security: formula/DDE injection attack payloads and sanitization patterns for all languages
- Validation: csvlint, Frictionless Data schema, type inference traps
- Conversion: CSV↔JSON, CSV↔Parquet, CSV↔XLSX, CSV↔SQL (PostgreSQL COPY, MySQL LOAD DATA)
- Performance: backpressure pipelines, async generators, worker threads, chunked processing, memory benchmarks
- Anti-patterns: 10 most common mistakes with fixes
- Troubleshooting: CR-only endings, BOM artifacts, garbled encoding, ragged rows, date corruption

## Key Decisions

| Need | Recommended tool |
|------|-----------------|
| Node.js large file parse | csv-parse + stream.pipeline |
| Node.js browser parse | PapaParse with `worker:true` |
| Python large file analysis | Polars `scan_csv` + `collect(streaming=True)` |
| Python data science | `pandas.read_csv` with explicit `dtype` map |
| Ad-hoc SQL query on CSV | DuckDB `read_csv_auto` |
| CLI filter/transform | qsv or miller |
| CLI stats/SQL | csvkit (`csvsql`, `csvstat`) |
| CSV → Parquet | Polars `sink_parquet` or DuckDB `COPY` |
| CSV → Excel | `pandas.to_excel` or openpyxl |
| Formula-injection-safe output | csv-stringify `escape_formulas:true` |
| Unknown encoding | Python `charset-normalizer`; Node `jschardet` |

## Critical Rules

All 7 rules are hard correctness constraints, not style preferences. When you discover a violation while writing code, stop, fix it, then continue. When the user's existing code violates a rule, flag it as a bug and provide a corrected version.

**Violation protocol:** identify the rule number → explain the specific failure mode → provide corrected code → continue.

### Rule 1 — `newline=''` in Python

Always open CSV files with `newline=''` (both `csv` module and manual reads). Universal newline mode corrupts `\r\n` inside quoted multiline fields, splitting them into separate rows.

**Validation:** every Python CSV `open()` call must include `newline=''`.

### Rule 2 — `encoding='utf-8-sig'` in Python

Always specify `encoding='utf-8-sig'` (not `'utf-8'`) when reading CSV files that may have come from Windows or Excel. `utf-8-sig` strips the BOM silently; `utf-8` leaves an invisible `﻿` on the first column name, breaking header lookups.

**Validation:** grep for `encoding='utf-8'` on CSV reads; replace with `utf-8-sig` unless source is guaranteed non-Windows.

### Rule 3 — BOM handling in Node.js

Pass `bom: true` to csv-parse for any file that may have been generated by Windows tools. For d3-dsv, pre-process with `strip-bom` — d3-dsv does not auto-strip in Node.js (browsers do it automatically).

**Validation:** BOM option present in every Node.js CSV parse call.

### Rule 4 — Use a real RFC 4180 parser

Never parse CSV with `split(',')`, regex, or manual string splitting. These break on: quoted commas (`"Smith, Jr."`), embedded newlines inside quoted fields, and doubled-quote escaping (`""`). Use csv-parse, PapaParse, fast-csv, d3-dsv (Node.js), or `csv.reader`, pandas, Polars (Python).

**Validation:** reject any code containing `.split(',')` applied to a raw CSV line.

### Rule 5 — Sanitize before export (formula/DDE injection, CWE-1236)

Always sanitize user-supplied data before writing CSV: use `escape_formulas: true` in csv-stringify, or prefix any cell value starting with `=`, `+`, `-`, `@`, `\t`, or `\r` with a single quote `'`. Without this, formula/DDE injection is possible when the file is opened in Excel or LibreOffice.

**Validation:** sanitization applied to every field derived from user input, not just top-level fields.

### Rule 6 — ISO 8601 dates

Always write dates as `YYYY-MM-DD` (Python: `%Y-%m-%d` or `.isoformat()[:10]`; Node.js: `.toISOString().split('T')[0]`). Locale-specific formats (`MM/DD/YY`, `DD/MM/YY`) cause silent data corruption when files cross locale boundaries.

**Validation:** reject date format strings containing `%m/%d`, `%d/%m`, or two-digit year `%y`.

### Rule 7 — Stream files > 50 MB

Never load CSV files larger than ~50 MB into a single in-memory array or DataFrame. Use streaming equivalents: `stream.pipeline` + csv-parse (Node.js); `chunksize` (pandas); `scan_csv` + `collect(streaming=True)` (Polars); `read_csv_auto` (DuckDB).

**Validation:** when the task involves a file path and size is unknown or large, default to the streaming pattern.

## Output validation checklist

Before returning CSV-related code or data, confirm:

- [ ] Encoding specified explicitly (not relying on OS default)
- [ ] BOM handled (stripped on read; added only when Excel compatibility required)
- [ ] Line endings consistent (LF for interop; CRLF only if strict RFC 4180 required)
- [ ] All user-supplied fields sanitized against formula injection
- [ ] Dates in ISO 8601
- [ ] Large files streamed, not fully buffered
- [ ] Parser is RFC 4180 compliant (not `split`)
