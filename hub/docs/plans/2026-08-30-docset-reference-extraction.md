# Docset Reference Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn each mirrored docset into a source-anchored fact layer (snippets, tables, definitions, LLM-extracted units) that the hub indexes and surfaces beside the raw text, piloted on `code.claude.com`.

**Architecture:** Acquisition prefers a site's `llms-full.txt` / `llms.txt` + per-page `.md` and writes the existing banner-format mirror; a new `scripts/docset_refine/` package cleans and triages pages deterministically, extracts snippets/tables/definitions without an LLM, extracts prose units on the local Ollama pool, optionally polishes them with `claude -p`, and renders `reference.md`; `docset_indexer` gains a `--units` path producing a `<key>__facts` docset that `hub_query_docset` prefers. The pipeline stage `distill` becomes `refine`.

**Tech Stack:** Python 3.12 (hub venv), stdlib + `embed_core` (Ollama pool), `semantic_ops.llm.generate` (`qwen3:8b` default), `claude -p` for polish, ChromaDB/SQLite via `docset_indexer`, Textual TUI, pytest.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-08-30-docset-reference-extraction-design.md`. Decisions (all approved): local Ollama for bulk unit extraction, Claude (`claude -p`) for a polish pass; `hub_query_docset` defaults to `layer="facts"` with raw fallback; `marketing`/`index` pages are excluded from the fact layer; `distill_offline.py bulk` leaves the pipeline path; Phase 1 acquisition rolls out estate-wide in parallel with the pilot.
- Mirror banner format is a fixed contract: `=` × ≥10 / `URL: <url>` / `=` × ≥10, then page text. Every artifact this plan writes that other tools read as a mirror uses it.
- Provenance is sacred: every unit carries `source_url`; nothing drops it.
- One writer per store: only this box (M5) indexes. Runtime artifacts (`<stem>.reference/`, state files) are gitignored — never commit them.
- Config via env, never hardcoded: `HUB_LLM_MODEL`, `HUB_OLLAMA_URLS`, `HUB_EMBED_MODEL`, new `HUB_REFINE_POLISH_MODEL` (default `claude-sonnet-5`).
- The live mirror script is `~/.claude/skills/web-text-mirror/scripts/text_mirror.py` (`core.MIRROR_SKILL_DIR`); the hub repo's `skills/` is a NESTED git repo — commit skill changes there separately.
- Tests: `.venv/bin/python -m pytest tests/ -q` (hermetic, `hub_tmp` fixture redirects every runtime path); lint: `.venv/bin/python -m ruff check .` (100-col). Both must pass before every commit.
- Commit messages end with the Co-Authored-By / Claude-Session trailer used by prior commits on `main`.

---

## File map

| Path | Responsibility |
|---|---|
| `scripts/llms_acquire.py` (new, stdlib-only) | Probe a host for `llms-full.txt` / `llms.txt`; split `llms-full.txt` into pages; fetch per-page `.md`; write banner-format mirror. Imported by `text_mirror.py` with a guarded import. |
| `~/.claude/skills/web-text-mirror/scripts/text_mirror.py` | `--prefer-llms` (default on) tries `llms_acquire` before crawling; `include_formatting=True` on trafilatura extract. |
| `scripts/docset_refine/__init__.py` | package; `reference_dir(mirror)`; unit record helpers. |
| `scripts/docset_refine/mirror_io.py` | parse banner mirror → pages (reuses `docset_indexer.parse_mirror`), write banner mirror, read/write `pages.json`. |
| `scripts/docset_refine/clean.py` | cross-page boilerplate strip, link-only/nav drop, page triage (`reference/guide/changelog/marketing/index`), changelog entry parser. |
| `scripts/docset_refine/extract.py` | deterministic units: fenced snippets, tables, heading definitions, special parsers (env vars, CLI flags, slash commands, error codes). |
| `scripts/docset_refine/units.py` | LLM prose units: prompt constant, page splitting, JSON parsing, resumable state, embedding dedup. |
| `scripts/docset_refine/polish.py` | `claude -p` polish pass over `units.jsonl` in batches. |
| `scripts/docset_refine/render.py` | `reference.md` grouped by page then type; counts summary. |
| `scripts/docset_refine/__main__.py` | CLI: `clean | extract | units | polish | render | all | probe` on a mirror path. |
| `scripts/docset_indexer.py` | `index --units FILE --name KEY`; `query --layer facts|raw`; `list` carries `facts`/`units` counts. |
| `mcp-server/hub_mcp_server.py` | `hub_query_docset(layer="facts")` with raw fallback; `hub_list_docsets` shows facts. |
| `scripts/pipeline_manager.py` | `STAGES = ("mirror", "refine", "index")`; `stage_refine`; `stage_index` indexes raw (`<stem>.clean.md`) + facts. |
| `scripts/hub_manager/queue_model.py`, `docsets.py`, `app.py` | item report shows refine artifacts; Docsets detail shows facts + `reference.md` link; `e` refresh runs refine + index. |
| `tests/test_llms_acquire.py`, `tests/test_docset_refine.py`, `tests/test_docset_search.py`, `tests/test_queue_model.py`, `tests/test_app_smoke.py` | hermetic tests per task. |
| `docs/superpowers/specs/2026-08-30-docset-golden-baseline.md` | Phase 0 golden questions + before/after answers. |

---

### Task 1: Baseline — golden questions for the pilot

**Files:**
- Create: `docs/superpowers/specs/2026-08-30-docset-golden-baseline.md`

**Interfaces:**
- Produces: a scored table re-run in Task 12.

- [ ] **Step 1: Write the 10 questions and run them against today's index**

```bash
cd ~/.global-ai-hub
for q in "How do I install Claude Code on Windows with PowerShell?" \
 "What exit codes can a PreToolUse hook return and what do they mean?" \
 "What does CLAUDE_CODE_SYNC_SKILLS control?" \
 "What happens when allowUnsandboxedCommands is enabled?" \
 "Which hook events fire once per turn?" \
 "How do I run Claude Code headless in CI and get JSON output?" \
 "What does the --append-system-prompt flag do?" \
 "How do I add a plugin marketplace that is not the official one?" \
 "What is the difference between SessionStart and UserPromptSubmit hooks?" \
 "How do I check which version of Claude Code is installed and update it?"; do
  echo "### $q"; scripts/ask "$q" --corpora docsets --top 5 | head -40; echo; done > /tmp/golden-before.txt
```

- [ ] **Step 2: Record answers and scores (0 = wrong/none, 1 = partial, 2 = correct with a usable command/value) in the doc, plus baseline numbers**

```markdown
# Golden baseline — code.claude.com (2026-08-30)
| # | Question | Before (score) | After (score) |
|---|---|---|---|
| 1 | Install on Windows PowerShell | … | |
…
Baseline: mirror 4,744,720 B · 228 pages · 37,033 non-blank / 28,740 unique lines · 122 fences · raw chunks: <from docset_indexer list>
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-08-30-docset-golden-baseline.md && git commit -m "docs: golden-question baseline for the code.claude.com pilot"
```

---

### Task 2: `llms_acquire` — fetch clean markdown where a site publishes it

**Files:**
- Create: `scripts/llms_acquire.py`
- Test: `tests/test_llms_acquire.py`

**Interfaces:**
- Produces:
  - `probe(base_url: str, fetch=_fetch) -> dict` → `{"llms_full": url|None, "llms": url|None}`; candidate roots tried in order: the seed's own directory (`https://host/docs/`), then `https://host/`.
  - `split_llms_full(text: str) -> list[dict]` → `[{"url": str, "title": str, "text": str}]`; a page starts at a line matching `^# ` whose next non-blank line matches `^Source: (\S+)`.
  - `parse_llms_index(text: str) -> list[str]` → page URLs from `- [title](url)` lines (`.md` links kept as-is).
  - `write_mirror(pages: list[dict], out_path: str, max_pages: int = 0) -> int` → writes the banner format (`=`×90 / `URL:` / `=`×90 / text), returns pages written.
  - `acquire(seed: str, out_path: str, max_pages: int = 0, fetch=_fetch, log=print) -> dict` → `{"method": "llms-full"|"llms"|None, "pages": int}`; `llms-full.txt` under 1,024 bytes counts as absent; per-page `.md` failures fall back per page (skipped, counted in `"failed"`), never per site.
- Stdlib only (`urllib.request`), 30 s timeout, UA `trafilatura-text-mirror/1.0 (+public-archive)`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_llms_acquire.py
"""llms.txt / llms-full.txt acquisition: the clean path around trafilatura."""
import llms_acquire as la

FULL = """# Hooks reference
Source: https://code.claude.com/docs/en/hooks

Hooks are user-defined shell commands.

```bash
claude --version
```

# Overview
Source: https://code.claude.com/docs/en/overview

## Not a page start
Claude Code is a tool.
"""

INDEX = """# Claude Code Docs
## Getting started
- [Overview](https://code.claude.com/docs/en/overview.md): Claude Code is…
- [Quickstart](https://code.claude.com/docs/en/quickstart.md): Welcome
"""


def test_split_llms_full_starts_pages_at_title_plus_source():
    pages = la.split_llms_full(FULL)
    assert [p["url"] for p in pages] == ["https://code.claude.com/docs/en/hooks",
                                         "https://code.claude.com/docs/en/overview"]
    assert pages[0]["title"] == "Hooks reference"
    assert "```bash\nclaude --version\n```" in pages[0]["text"]   # code survives
    assert "## Not a page start" in pages[1]["text"]               # inner H2 is not a page


def test_parse_llms_index_keeps_md_links():
    assert la.parse_llms_index(INDEX) == ["https://code.claude.com/docs/en/overview.md",
                                          "https://code.claude.com/docs/en/quickstart.md"]


def test_write_mirror_uses_the_banner_contract(tmp_path):
    out = tmp_path / "m.md"
    n = la.write_mirror([{"url": "https://h/a", "title": "A", "text": "body"}], str(out))
    text = out.read_text()
    assert n == 1
    assert "\n" + "=" * 90 + "\nURL: https://h/a\n" + "=" * 90 + "\n\n# A\n\nbody\n" in text


def test_acquire_prefers_llms_full_then_index_then_none(tmp_path):
    served = {"https://h/docs/llms-full.txt": FULL,
              "https://h/docs/llms.txt": INDEX,
              "https://h/docs/en/overview.md": "# Overview\n\ntext",
              "https://h/docs/en/quickstart.md": None}  # None = fetch failure

    def fetch(url):
        return served.get(url)

    r = la.acquire("https://h/docs", str(tmp_path / "a.md"), fetch=fetch, log=lambda m: None)
    assert r == {"method": "llms-full", "pages": 2, "failed": 0}

    served["https://h/docs/llms-full.txt"] = "tiny"  # < 1 KB counts as absent
    r = la.acquire("https://h/docs", str(tmp_path / "b.md"), fetch=fetch, log=lambda m: None)
    assert r["method"] == "llms" and r["pages"] == 1 and r["failed"] == 1
    assert "URL: https://h/docs/en/overview" in (tmp_path / "b.md").read_text()  # .md stripped

    served["https://h/docs/llms.txt"] = None
    served["https://h/llms.txt"] = None
    r = la.acquire("https://h/docs", str(tmp_path / "c.md"), fetch=fetch, log=lambda m: None)
    assert r["method"] is None and not (tmp_path / "c.md").exists()


def test_acquire_respects_max_pages(tmp_path):
    fetch = lambda url: FULL if url.endswith("llms-full.txt") else None  # noqa: E731
    r = la.acquire("https://h/docs", str(tmp_path / "a.md"), max_pages=1, fetch=fetch,
                   log=lambda m: None)
    assert r["pages"] == 1
```

- [ ] **Step 2: Run to verify failure** — `.venv/bin/python -m pytest tests/test_llms_acquire.py -q` → `ModuleNotFoundError: llms_acquire`

- [ ] **Step 3: Implement `scripts/llms_acquire.py`**

```python
#!/usr/bin/env python3
"""llms_acquire.py — fetch a docset as the clean markdown a site already publishes.

Many docs hosts (Mintlify, Fern, Docusaurus, GitBook) serve `llms-full.txt`
(the whole docset, one file), `llms.txt` (an index) and a `.md` twin of every
page. Those keep code blocks, tables and admonitions that trafilatura drops.
This module writes them in the web-text-mirror banner format so every
downstream tool is unchanged. Stdlib only: it is imported by text_mirror.py,
which runs on boxes without the hub venv.
"""
from __future__ import annotations

import re
import urllib.error
import urllib.request
from urllib.parse import urljoin, urlparse

UA = "trafilatura-text-mirror/1.0 (+public-archive)"
MIN_FULL_BYTES = 1024
BANNER = "=" * 90
_SOURCE_RE = re.compile(r"^Source:\s*(\S+)\s*$")
_LINK_RE = re.compile(r"^\s*[-*]\s*\[[^\]]*\]\((https?://[^)\s]+)\)")


def _fetch(url: str, timeout: int = 30) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ctype = r.headers.get("Content-Type", "")
            if "html" in ctype:
                return None  # a 200 HTML page is a soft-404 for these files
            return r.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError, ValueError):
        return None


def _roots(seed: str) -> list[str]:
    p = urlparse(seed)
    origin = f"{p.scheme}://{p.netloc}"
    path = p.path if p.path.endswith("/") else p.path.rsplit("/", 1)[0] + "/"
    roots = [origin + path]
    if path != "/":
        roots.append(origin + "/")
    return roots


def probe(seed: str, fetch=_fetch) -> dict:
    out = {"llms_full": None, "llms": None}
    for root in _roots(seed):
        for key, name in (("llms_full", "llms-full.txt"), ("llms", "llms.txt")):
            if out[key]:
                continue
            url = urljoin(root, name)
            text = fetch(url)
            if text and (key != "llms_full" or len(text.encode()) >= MIN_FULL_BYTES):
                out[key] = url
        if out["llms_full"] or out["llms"]:
            break
    return out


def split_llms_full(text: str) -> list[dict]:
    lines = text.splitlines()
    pages: list[dict] = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("# "):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            m = _SOURCE_RE.match(lines[j]) if j < len(lines) else None
            if m:
                pages.append({"title": lines[i][2:].strip(), "url": m.group(1), "lines": []})
                i = j + 1
                continue
        if pages:
            pages[-1]["lines"].append(lines[i])
        i += 1
    for p in pages:
        p["text"] = "\n".join(p.pop("lines")).strip("\n")
    return pages


def parse_llms_index(text: str) -> list[str]:
    urls = []
    for line in text.splitlines():
        m = _LINK_RE.match(line)
        if m and m.group(1) not in urls:
            urls.append(m.group(1))
    return urls


def write_mirror(pages: list[dict], out_path: str, max_pages: int = 0) -> int:
    import os
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    n = 0
    with open(out_path, "w", encoding="utf-8") as fh:
        for pg in pages:
            if max_pages and n >= max_pages:
                break
            body = pg["text"] or "[no extractable text]"
            title = pg.get("title") or ""
            if title and not body.lstrip().startswith("# "):
                body = f"# {title}\n\n{body}"
            fh.write(f"\n\n{BANNER}\nURL: {pg['url']}\n{BANNER}\n\n{body}\n")
            n += 1
    return n


def _page_url(md_url: str) -> str:
    return md_url[:-3] if md_url.endswith(".md") else md_url


def acquire(seed: str, out_path: str, max_pages: int = 0, fetch=_fetch, log=print) -> dict:
    found = probe(seed, fetch)
    if found["llms_full"]:
        pages = split_llms_full(fetch(found["llms_full"]) or "")
        if pages:
            n = write_mirror(pages, out_path, max_pages)
            log(f"llms-full: {n} pages from {found['llms_full']}")
            return {"method": "llms-full", "pages": n, "failed": 0}
    if found["llms"]:
        urls = parse_llms_index(fetch(found["llms"]) or "")
        pages, failed = [], 0
        for u in urls:
            if max_pages and len(pages) >= max_pages:
                break
            text = fetch(u)
            if text is None:
                failed += 1
                log(f"llms page failed: {u}")
                continue
            pages.append({"url": _page_url(u), "title": "", "text": text})
        if pages:
            n = write_mirror(pages, out_path, max_pages)
            log(f"llms index: {n} pages, {failed} failed, from {found['llms']}")
            return {"method": "llms", "pages": n, "failed": failed}
    log("no llms.txt / llms-full.txt — falling back to crawl")
    return {"method": None, "pages": 0, "failed": 0}


if __name__ == "__main__":
    import json
    import sys
    seed, out = sys.argv[1], sys.argv[2]
    cap = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    print(json.dumps(acquire(seed, out, cap)))
```

- [ ] **Step 4: Run tests** — `.venv/bin/python -m pytest tests/test_llms_acquire.py -q` → 5 passed
- [ ] **Step 5: Commit** — `git add scripts/llms_acquire.py tests/test_llms_acquire.py && git commit -m "feat: llms_acquire — fetch docsets from llms-full.txt / llms.txt + page .md"`

---

### Task 3: `text_mirror.py --prefer-llms` + structure-preserving fallback; re-mirror the pilot

**Files:**
- Modify: `~/.claude/skills/web-text-mirror/scripts/text_mirror.py` (imports ~line 37, `process_single_url` ~line 360, `crawl` ~line 619, `main` ~line 766)
- Modify: `scripts/pipeline_manager.py` `stage_mirror` (local branch) — pass `--prefer-llms` (already the default; nothing to add) and record `acquire` method in the item.

**Interfaces:**
- Consumes: `llms_acquire.acquire(seed, out_path, max_pages, log=...)`.
- Produces: `crawl(...)` returns page count as before; when the llms path succeeds it writes the mirror, saves state `{"crawled": {url: 1…}, "discovered": [...], "queue": [], "acquire": "llms-full"|"llms"}` and returns without crawling.

- [ ] **Step 1: Guarded import at the top of `text_mirror.py`** (after `import site_clone`)

```python
try:
    sys.path.insert(0, os.path.expanduser("~/.global-ai-hub/scripts"))
    import llms_acquire  # stdlib-only; absent on a box without the hub checkout
except Exception:  # noqa: BLE001
    llms_acquire = None
```

- [ ] **Step 2: `include_formatting=True` on both `trafilatura.extract(...)` calls** (lines ~360 and ~387) so headings/code/lists keep their markdown when the crawl path is used.

- [ ] **Step 3: In `crawl()`, before the robots/state setup, try the llms path when enabled**

```python
    if PREFER_LLMS and llms_acquire is not None and seed_html is None and not force_refresh:
        out_path = get_out_file(host, out_file)
        if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
            r = llms_acquire.acquire(seed, out_path, max_pages=max_pages, log=log)
            if r["method"]:
                urls = [ln[5:].strip() for ln in open(out_path, encoding="utf-8")
                        if ln.startswith("URL: ")]
                save_state(host, out_file, {u: 1 for u in urls}, urls, [])
                _write_acquire_marker(out_path, r["method"])
                return r["pages"]
```

with `PREFER_LLMS = True` module global, `--prefer-llms/--no-prefer-llms` argparse (`argparse.BooleanOptionalAction`, default True) setting it in `main()`, and

```python
def _write_acquire_marker(out_path, method):
    with open(os.path.splitext(out_path)[0] + "_state.json", "r+") as f:  # state saved just above
        st = json.load(f); st["acquire"] = method; f.seek(0); json.dump(st, f); f.truncate()
```

(existing-mirror rule: an existing non-empty mirror keeps the crawl path so resumed crawls are not clobbered; `c`/recrawl on the Queue tab deletes nothing, so to switch an existing docset to the llms path move the old mirror aside first — Task 12 does this for the rollout.)

- [ ] **Step 4: Verify on the pilot (local, no boxes)**

```bash
cd ~/.claude/skills/web-text-mirror/text-mirror && mv code.claude.com.md _oversized_backup/code.claude.com.trafilatura.md && mv code.claude.com_state.json _oversized_backup/
python3 ../scripts/text_mirror.py https://code.claude.com/docs --out code.claude.com.md --max-pages 2000
grep -c '^URL: ' code.claude.com.md; grep -c '```' code.claude.com.md; python3 -c "import json;print(json.load(open('code.claude.com_state.json'))['acquire'])"
```
Expected: ~191 pages, > 1,000 fences, `llms-full`. Then `cd ~/.global-ai-hub && .venv/bin/python scripts/docset_indexer.py index ~/.claude/skills/web-text-mirror/text-mirror/code.claude.com.md --name codeclaudecom__code-claude-com` still parses it (pages == URL count).

- [ ] **Step 5: Commit in the skills repo** (nested git; `~/.claude/skills/web-text-mirror` — check `git -C ~/.claude/skills/web-text-mirror rev-parse --show-toplevel` and commit there) — `git commit -am "feat(text-mirror): prefer llms-full.txt / llms.txt; keep formatting on the crawl path"`.

---

### Task 4: `docset_refine` package — mirror I/O, boilerplate strip, page triage, changelog

**Files:**
- Create: `scripts/docset_refine/__init__.py`, `mirror_io.py`, `clean.py`, `__main__.py`
- Test: `tests/test_docset_refine.py`

**Interfaces:**
- `docset_refine.reference_dir(mirror: Path) -> Path` → `<mirror.parent>/<stem>.reference/` (created on demand).
- `mirror_io.read_pages(path: Path) -> list[dict]` → `[{"url", "text"}]` via `docset_indexer.parse_mirror` (bannerless file → one synthetic page `file://…`).
- `mirror_io.write_pages(pages, path)` banner format; `mirror_io.save_json(obj, path)` / `load_json(path)` (tmp + `os.replace`).
- `clean.boilerplate_lines(pages, min_share=0.05) -> set[str]` → normalized lines present in ≥ `min_share` of pages (and in ≥ 3 pages).
- `clean.is_link_only(line) -> bool`; `clean.strip_page(text, boiler) -> str` (drops boilerplate, link-only lines, and runs of ≥ 4 consecutive short `- Word` bullets; never touches lines inside a fenced block).
- `clean.classify(url, text) -> str` in `("reference", "guide", "changelog", "marketing", "index")`:
  - `changelog` if the path's last segment ∈ {changelog, release-notes, releases, whats-new};
  - `marketing` if any path segment ∈ {blog, customers, pricing, contact-sales, community, careers, about, press, enterprise, solutions} or the path is `/`;
  - `index` if the page has < 400 chars of non-heading, non-link text or > 60% of non-blank lines are links;
  - `reference` if the path contains one of {reference, api, cli, env, errors, settings, hooks, sdk, schema, commands, options, flags} or ≥ 3 tables / ≥ 5 fences;
  - else `guide`.
- `clean.changelog_entries(text) -> list[dict]` → `[{"date": "YYYY-MM-DD"|None, "version": str|None, "text": str}]` split at lines matching `^#{1,4}\s*(v?\d+\.\d+[\w.\-]*)` or a date heading (`Month D, YYYY` / ISO).
- `clean.run(mirror: Path) -> dict` → writes `<stem>.clean.md` (banner mirror of stripped pages, `marketing`/`index` pages omitted) and `<stem>.reference/pages.json` (`[{"url","class","title","text","headings":[…]}]`), returns `{"pages": n, "kept": n, "dropped_lines": n, "classes": {…}}`.
- CLI: `python -m docset_refine clean <mirror.md>` prints that dict as JSON.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_docset_refine.py
"""docset_refine: strip/triage, deterministic extraction, LLM units, render."""
import json
from pathlib import Path

from docset_refine import clean, extract, mirror_io, render, units  # noqa: F401 (units used later)

FOOTER = "You can access Claude Code with a Claude Pro or Max plan."
PAGE = lambda url, body: f"\n\n{'=' * 90}\nURL: {url}\n{'=' * 90}\n\n{body}\n"  # noqa: E731
HOOKS = """# Hooks reference

Hooks are user-defined shell commands that run at specific points.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | allow |
| 2 | block |

```bash
claude --version
```

- Terminal
- VS Code
- Desktop app
- Web

[Configuration](https://code.claude.com#configuration)
""" + FOOTER


def _mirror(tmp_path):
    p = tmp_path / "code.claude.com.md"
    p.write_text(PAGE("https://code.claude.com/docs/en/hooks", HOOKS)
                 + PAGE("https://code.claude.com/docs/en/quickstart", "# Quickstart\n\nRun `claude`.\n\n" + FOOTER)
                 + PAGE("https://code.claude.com/customers/ramp", "# Ramp\n\nRamp loves it.\n\n" + FOOTER)
                 + PAGE("https://code.claude.com/docs/en/changelog",
                        "# Changelog\n\n## 2.1.0\n\n- Added hooks\n\n## 2.0.0\n\n- Initial\n\n" + FOOTER))
    return p


def test_boilerplate_is_lines_shared_across_pages(tmp_path):
    pages = mirror_io.read_pages(_mirror(tmp_path))
    boiler = clean.boilerplate_lines(pages, min_share=0.05)
    assert FOOTER in boiler
    assert "Hooks are user-defined shell commands that run at specific points." not in boiler


def test_strip_page_drops_chrome_but_never_fence_contents():
    text = clean.strip_page(HOOKS, {FOOTER})
    assert FOOTER not in text
    assert "[Configuration](https://code.claude.com#configuration)" not in text  # link-only
    assert "- Terminal" not in text                                              # nav run
    assert "```bash\nclaude --version\n```" in text
    assert "| 0 | allow |" in text


def test_classify_by_url_and_shape():
    assert clean.classify("https://h/docs/en/hooks", HOOKS) == "reference"
    assert clean.classify("https://h/docs/en/quickstart", "# Q\n\n" + "prose. " * 80) == "guide"
    assert clean.classify("https://h/customers/ramp", "# R\n\ntext") == "marketing"
    assert clean.classify("https://h/docs/en/changelog", "# C") == "changelog"
    assert clean.classify("https://h/docs", "- [a](https://h/a)\n- [b](https://h/b)\n") == "index"


def test_changelog_entries_split_on_version_headings():
    entries = clean.changelog_entries("# Changelog\n\n## 2.1.0\n\n- Added hooks\n\n## 2.0.0\n\n- Initial")
    assert [e["version"] for e in entries] == ["2.1.0", "2.0.0"]
    assert "Added hooks" in entries[0]["text"]


def test_clean_run_writes_clean_mirror_and_pages_json(tmp_path):
    m = _mirror(tmp_path)
    r = clean.run(m)
    assert r["pages"] == 4 and r["kept"] == 3          # marketing page dropped
    clean_pages = mirror_io.read_pages(tmp_path / "code.claude.com.clean.md")
    assert [p["url"].rsplit("/", 1)[1] for p in clean_pages] == ["hooks", "quickstart", "changelog"]
    assert FOOTER not in (tmp_path / "code.claude.com.clean.md").read_text()
    meta = json.loads((tmp_path / "code.claude.com.reference" / "pages.json").read_text())
    assert {p["class"] for p in meta} == {"reference", "guide", "changelog"}
    assert meta[0]["headings"][:2] == ["Hooks reference", "Exit codes"]
```

- [ ] **Step 2: Run to verify failure** — `ModuleNotFoundError: docset_refine`
- [ ] **Step 3: Implement** `__init__.py` (`reference_dir`, `UNIT_TYPES`, `new_unit(...)`), `mirror_io.py`, `clean.py` per the interfaces above; `__main__.py` with argparse subcommands dispatching to `clean.run` (later tasks add the rest). Fence-awareness: iterate lines toggling `in_fence` on lines starting with ```` ``` ````; only non-fence lines are candidates for stripping.
- [ ] **Step 4: Run tests** → 5 passed; run on the pilot: `PYTHONPATH=scripts .venv/bin/python -m docset_refine clean ~/.claude/skills/web-text-mirror/text-mirror/code.claude.com.md` → JSON with `classes` counts; `grep -c . *.clean.md` vs unique lines ≥ 95%.
- [ ] **Step 5: Commit** — `feat: docset_refine clean — boilerplate strip, page triage, changelog entries`

---

### Task 5: Deterministic extraction + render

**Files:**
- Create: `scripts/docset_refine/extract.py`, `scripts/docset_refine/render.py`
- Modify: `scripts/docset_refine/__main__.py` (add `extract`, `render`)
- Test: `tests/test_docset_refine.py` (append)

**Interfaces:**
- Unit record (shared by Tasks 5–8): `{"id": "u000412", "type": str, "text": str, "source_url": str, "anchor": str, "page_class": str, "keywords": [str], "code": {"lang": str, "body": str}|None, "origin": "code"|"table"|"heading"|"llm"|"changelog"}`; `docset_refine.new_unit(seq, **fields)` builds it and validates `type ∈ UNIT_TYPES = ("concept","fact","actionable","question","problem","statement","quote","idea","snippet","parameter","definition","change")`.
- `extract.snippets(page) -> list[dict]`: every fenced block → `type="snippet"`, `text=f"{nearest heading}: {first line of code}"`, `code={"lang","body"}`, `anchor="#"+slug(nearest heading)`.
- `extract.tables(page) -> list[dict]`: each markdown table row → `type="parameter"`, `text="<col0>: <col1> (…remaining cols as k=v)"`, header row kept as `keywords`.
- `extract.definitions(page) -> list[dict]`: each `##`/`###` heading with a following paragraph ≥ 40 chars → `type="definition"`, `text=f"{heading} — {first sentence(s) ≤ 300 chars}"`.
- `extract.changes(page) -> list[dict]` for `changelog` pages via `clean.changelog_entries` → `type="change"`, `keywords=[version, date]`.
- `extract.run(mirror: Path) -> dict` → reads `pages.json`, writes `<stem>.reference/structured.jsonl`, returns counts by origin.
- `render.run(mirror: Path) -> dict` → merges `structured.jsonl` + `units.jsonl` (if present) → `<stem>.reference/reference.md` (H1 docset, H2 per page in pages.json order, H3 per type, one bullet per unit ending in `— <source_url><anchor>`; snippets rendered as fences) and `summary.json` `{"pages", "units_by_origin", "units_by_type"}`.

- [ ] **Step 1: Failing tests**

```python
def test_snippets_carry_heading_and_language():
    page = {"url": "https://h/docs/en/hooks", "class": "reference", "text": HOOKS,
            "headings": ["Hooks reference", "Exit codes"]}
    snips = extract.snippets(page)
    assert len(snips) == 1
    s = snips[0]
    assert s["type"] == "snippet" and s["origin"] == "code"
    assert s["code"] == {"lang": "bash", "body": "claude --version"}
    assert s["anchor"] == "#exit-codes" and s["text"].startswith("Exit codes: claude --version")


def test_tables_become_parameter_units():
    page = {"url": "https://h/docs/en/hooks", "class": "reference", "text": HOOKS, "headings": []}
    rows = extract.tables(page)
    assert [r["text"] for r in rows] == ["0: allow", "2: block"]
    assert rows[0]["keywords"] == ["Code", "Meaning"] and rows[0]["origin"] == "table"


def test_definitions_pair_heading_with_first_paragraph():
    page = {"url": "https://h/docs/en/hooks", "class": "reference", "text": HOOKS, "headings": []}
    defs = extract.definitions(page)
    assert defs and defs[0]["text"].startswith("Hooks reference — Hooks are user-defined shell commands")


def test_extract_and_render_end_to_end(tmp_path):
    m = _mirror(tmp_path)
    clean.run(m)
    counts = extract.run(m)
    assert counts["code"] == 1 and counts["table"] == 2 and counts["change"] == 2
    out = render.run(m)
    ref = (tmp_path / "code.claude.com.reference" / "reference.md").read_text()
    assert "## https://code.claude.com/docs/en/hooks" in ref
    assert "```bash\nclaude --version\n```" in ref
    assert "— https://code.claude.com/docs/en/hooks#exit-codes" in ref
    assert out["units_by_origin"]["table"] == 2
```

- [ ] **Step 2–5:** run (fail) → implement → run (pass) → verify on the pilot (`extract` then `render`; expect snippet count ≈ fence count of the clean mirror, and every row of `/docs/en/env-vars` as a `parameter`) → commit `feat: docset_refine extract/render — snippets, tables, definitions, changes`.

---

### Task 6: LLM prose units on the Ollama pool

**Files:**
- Create: `scripts/docset_refine/units.py`
- Modify: `scripts/docset_refine/__main__.py` (add `units`)
- Test: `tests/test_docset_refine.py` (append)

**Interfaces:**
- Consumes: `semantic_ops.llm.generate(prompt, model=None, timeout=None) -> str`; `embed_core.embed_texts(list[str], model=None) -> list[list[float]]`.
- `units.PROMPT: str` (module constant, `{url}` / `{types}` / `{page}` placeholders) — the `/pdo` target.
- `units.sections(page, max_chars=18000) -> list[dict]` → split at H2 when the page exceeds `max_chars`; each `{"anchor", "text"}`.
- `units.parse_reply(text) -> list[dict]` → tolerant: finds the first `[` … last `]`, `json.loads`, keeps dicts with `type ∈ UNIT_TYPES` and `text` ≥ 20 chars; returns `[]` on any failure.
- `units.extract_page(page, generate=llm.generate, model=None) -> list[dict]` → units with `origin="llm"`, `anchor` from the section.
- `units.dedup(units, embed=embed_core.embed_texts, threshold=0.9) -> list[dict]` → exact-normalized dedup first, then cosine over embeddings in insertion order (keep first).
- `units.run(mirror, model=None, classes=("reference","guide"), generate=…, embed=…, log=print) -> dict` → resumable via `<stem>.reference/units.state.json` (`{url: {"hash": sha1(text), "n": int, "ok": bool}}`); writes `units.jsonl` (appends per page, rewrites after dedup at the end); returns `{"pages", "done", "failed", "units", "deduped"}`; exits non-zero (returns `failed_pct > 5`) so the pipeline stage fails loudly.
- CLI: `python -m docset_refine units <mirror> [--model M] [--limit N] [--no-dedup]`.

- [ ] **Step 1: Failing tests**

```python
def test_parse_reply_is_tolerant_of_prose_and_bad_items():
    reply = 'Sure! Here you go:\n[{"type":"fact","text":"Hooks run before every tool call in the loop."},' \
            '{"type":"bogus","text":"x"},{"type":"actionable","text":"short"}]\nDone.'
    got = units.parse_reply(reply)
    assert [u["type"] for u in got] == ["fact"]
    assert units.parse_reply("not json") == []


def test_extract_page_uses_prompt_and_tags_origin():
    seen = {}

    def fake_generate(prompt, model=None, timeout=None):
        seen["prompt"] = prompt
        return '[{"type":"actionable","text":"Run claude --version to check the version.","keywords":["version"]}]'

    page = {"url": "https://h/docs/en/hooks", "class": "reference", "text": HOOKS, "headings": []}
    got = units.extract_page(page, generate=fake_generate)
    assert "https://h/docs/en/hooks" in seen["prompt"] and "claude --version" in seen["prompt"]
    assert got[0]["origin"] == "llm" and got[0]["source_url"] == "https://h/docs/en/hooks"


def test_dedup_drops_near_duplicates_by_embedding():
    us = [{"id": "a", "text": "Hooks run before tool calls."},
          {"id": "b", "text": "Hooks run before tool calls!"},   # exact after normalization
          {"id": "c", "text": "Hooks execute prior to each tool call."},  # semantic dup
          {"id": "d", "text": "Skills sync across sessions."}]
    vecs = {"Hooks run before tool calls.": [1, 0], "Hooks execute prior to each tool call.": [0.99, 0.1],
            "Skills sync across sessions.": [0, 1]}
    kept = units.dedup(us, embed=lambda texts, model=None: [vecs[t] for t in texts], threshold=0.9)
    assert [u["id"] for u in kept] == ["a", "d"]


def test_units_run_is_resumable_and_skips_excluded_classes(tmp_path):
    m = _mirror(tmp_path)
    clean.run(m)
    calls = []

    def gen(prompt, model=None, timeout=None):
        calls.append(prompt)
        return '[{"type":"fact","text":"Hooks are user-defined shell commands that run at points."}]'

    r = units.run(m, generate=gen, embed=lambda t, model=None: [[1.0] for _ in t], log=lambda s: None)
    assert r["pages"] == 2 and r["done"] == 2 and r["units"] >= 1   # hooks + quickstart; changelog skipped
    n = len(calls)
    r2 = units.run(m, generate=gen, embed=lambda t, model=None: [[1.0] for _ in t], log=lambda s: None)
    assert len(calls) == n and r2["done"] == 2                       # nothing re-generated
```

- [ ] **Step 2–5:** run (fail) → implement (the prompt: system framing + rules from spec §4.4; sections split; per-page `generate` with `timeout=300`; `failed` pages recorded in state; dedup at the end) → run (pass) → pilot smoke with `--limit 5` on `qwen3:8b`: `HUB_OLLAMA_URLS=http://192.168.4.75:11434=1 PYTHONPATH=scripts .venv/bin/python -m docset_refine units <mirror> --limit 5` and eyeball `units.jsonl` → commit `feat: docset_refine units — LLM prose extraction on the Ollama pool, resumable, embedding dedup`.

---

### Task 7: Claude polish pass

**Files:**
- Create: `scripts/docset_refine/polish.py`
- Modify: `scripts/docset_refine/__main__.py` (add `polish`, `all --polish`)
- Test: `tests/test_docset_refine.py` (append)

**Interfaces:**
- `polish.POLISH_PROMPT: str`; batches of `batch=40` units, each unit sent as `{id, type, text}`; the model returns the same ids with `text` fixed (grammar, truncation, spelling of commands preserved), `drop: true` for marketing/duplicate/untrue-to-source units, optional `type` correction. Anchors and `source_url` are never sent for editing and are re-attached by id.
- `polish.run_claude(prompt: str, model: str, run=subprocess.run) -> str` → `claude -p --model <model> --output-format text` with the prompt on stdin, 600 s timeout; env `HUB_REFINE_POLISH_MODEL` default `claude-sonnet-5`.
- `polish.apply(units, reply) -> tuple[list[dict], int]` → (polished units, dropped count); unknown ids ignored; a malformed reply leaves the batch untouched.
- `polish.run(mirror, model=None, run_claude=run_claude, log=print) -> dict` → reads `units.jsonl`, writes `units.polished.jsonl` + `polish.state.json` (batch index → done), returns `{"units", "polished", "dropped", "batches", "failed_batches"}`. `render` prefers `units.polished.jsonl` when present.

- [ ] **Step 1: Failing tests**

```python
def test_polish_apply_edits_by_id_and_drops():
    us = [{"id": "u1", "type": "fact", "text": "Hooks runs before tool call", "source_url": "https://h/x", "anchor": "#a"},
          {"id": "u2", "type": "statement", "text": "Claude Code is loved by teams everywhere.", "source_url": "https://h/x", "anchor": ""}]
    reply = '[{"id":"u1","text":"Hooks run before every tool call."},{"id":"u2","drop":true},{"id":"zz","text":"ignored"}]'
    out, dropped = polish.apply(us, reply)
    assert [u["id"] for u in out] == ["u1"] and dropped == 1
    assert out[0]["text"] == "Hooks run before every tool call." and out[0]["anchor"] == "#a"
    assert polish.apply(us, "garbage")[0] == us


def test_polish_run_calls_claude_per_batch_and_resumes(tmp_path):
    ref = tmp_path / "code.claude.com.reference"; ref.mkdir()
    (tmp_path / "code.claude.com.md").write_text("")
    (ref / "units.jsonl").write_text("\n".join(json.dumps(
        {"id": f"u{i}", "type": "fact", "text": f"fact number {i} about hooks", "source_url": "https://h", "anchor": ""})
        for i in range(3)) + "\n")
    calls = []

    def fake_claude(prompt, model):
        calls.append(model)
        return json.dumps([{"id": "u0", "text": "Fact zero about hooks."}, {"id": "u1", "drop": True}])

    r = polish.run(tmp_path / "code.claude.com.md", model="claude-sonnet-5", run_claude=fake_claude, log=lambda s: None)
    assert r == {"units": 3, "polished": 1, "dropped": 1, "batches": 1, "failed_batches": 0} and calls == ["claude-sonnet-5"]
    lines = (ref / "units.polished.jsonl").read_text().splitlines()
    assert len(lines) == 2 and json.loads(lines[0])["text"] == "Fact zero about hooks."
    polish.run(tmp_path / "code.claude.com.md", model="claude-sonnet-5", run_claude=fake_claude, log=lambda s: None)
    assert len(calls) == 1  # state file says batch 0 is done
```

- [ ] **Step 2–5:** fail → implement → pass → live smoke on 1 batch of the pilot (`--limit 1`) and read the diff → commit `feat: docset_refine polish — claude -p pass over extracted units`.

---

### Task 8: `docset_indexer index --units` and `query --layer`

**Files:**
- Modify: `scripts/docset_indexer.py` (`cmd_index` ~line 399, `cmd_query` ~463, `cmd_list` ~526, parser ~535; `SqliteStore.list_docsets`)
- Test: `tests/test_docset_search.py` (append)

**Interfaces:**
- `index --units FILE --name KEY`: one row per unit; `text` = unit text (snippets: `text + "\n" + code body`); metadata `url=source_url+anchor`, `seq=n`, plus `unit_type`, `origin` carried in the sqlite `chunks` table via two new nullable columns (`ALTER TABLE … ADD COLUMN` guarded) and in chroma `metadatas`; `pages` stored as `[]` (facts have no raw pages); meta `source_path` = the jsonl path.
- `facts_key(key) -> f"{key}__facts"`; `cmd_index` derives it when `--units` is given without `--name`? No — `--name` is required with `--units` (explicit keys only).
- `query --layer facts|raw|auto` (default `auto`): `auto` queries `<key>__facts` if it exists else `<key>`; output JSON gains `"layer"`. Result rows carry `unit_type`/`origin` when present.
- `list`: each entry gains `"facts": int|None` (chunk count of `<key>__facts`) and `__facts` docsets are folded into their parent (not listed separately) unless `--all`.

- [ ] **Step 1: Failing tests**

```python
def test_index_units_writes_a_facts_docset_with_unit_metadata(tmp_path, monkeypatch, capsys):
    import docset_indexer, embed_core
    monkeypatch.setattr(docset_indexer, "SQLITE_PATH", tmp_path / "docsets.db")
    monkeypatch.setenv("HUB_DOCSET_BACKEND", "sqlite")
    monkeypatch.setattr(embed_core, "embed_texts", lambda texts, model=None: [[1.0, 0.0] for _ in texts])
    monkeypatch.setattr(embed_core, "embed_model", lambda: "m")
    uf = tmp_path / "units.jsonl"
    uf.write_text(json.dumps({"id": "u1", "type": "snippet", "text": "Exit codes: claude --version",
                              "code": {"lang": "bash", "body": "claude --version"}, "origin": "code",
                              "source_url": "https://h/hooks", "anchor": "#exit-codes"}) + "\n")
    assert docset_indexer.main(["index", str(uf), "--units", "--name", "h__hooks__facts"]) == 0
    store = docset_indexer.SqliteStore()
    rows = list(store.dump_chunks("h__hooks__facts"))
    assert rows[0]["url"] == "https://h/hooks#exit-codes" and "claude --version" in rows[0]["text"]
    assert store.list_docsets(include_facts=True)[0]["docset"] == "h__hooks__facts"


def test_query_layer_auto_prefers_facts_and_list_folds_them(tmp_path, monkeypatch, capsys):
    import docset_indexer, embed_core
    monkeypatch.setattr(docset_indexer, "SQLITE_PATH", tmp_path / "docsets.db")
    monkeypatch.setenv("HUB_DOCSET_BACKEND", "sqlite")
    monkeypatch.setattr(embed_core, "embed_texts", lambda texts, model=None: [[1.0, 0.0] for _ in texts])
    store = docset_indexer.SqliteStore()
    row = lambda t: {"id": t, "url": "https://h/p", "seq": 0, "text": t, "vector": [1.0, 0.0], "model": "m"}  # noqa: E731
    store.replace_docset("h__d", [row("raw chunk text here")], {"source_path": "/m.md", "pages": 1, "model": "m"})
    store.replace_docset("h__d__facts", [row("fact text here")], {"source_path": "/u.jsonl", "pages": 0, "model": "m"})
    store.close()
    assert docset_indexer.main(["query", "h__d", "anything"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["layer"] == "facts" and out["results"][0]["text"] == "fact text here"
    assert docset_indexer.main(["query", "h__d", "anything", "--layer", "raw"]) == 0
    assert json.loads(capsys.readouterr().out)["layer"] == "raw"
    assert docset_indexer.main(["list"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert [e["docset"] for e in listed] == ["h__d"] and listed[0]["facts"] == 1
```

- [ ] **Step 2–5:** fail → implement → pass (existing `test_docset_search.py` tests must still pass: `list_docsets()` default keeps folding; `delete` of a parent also deletes its `__facts`) → commit `feat: docset_indexer — index unit files as <key>__facts; query --layer; list folds facts`.

---

### Task 9: MCP surface — `hub_query_docset(layer=)`, facts in `hub_list_docsets`

**Files:**
- Modify: `mcp-server/hub_mcp_server.py` (`hub_query_docset` ~line 272, `hub_list_docsets`, `hub_delete_docset`), `docs/MCP.md`, `libraries/mcp-library/registry.json` (no new tool; descriptions)
- Test: `tests/test_docset_search.py` (append)

**Interfaces:**
- `hub_query_docset(docset, question, top=5, layer="auto")` → `auto`: facts if `<docset>__facts` exists else raw; reply JSON `{"docset", "layer", "results"}`; passing an explicit `__facts` key works too.
- `hub_list_docsets()` → folded list with `facts` counts (Task 8's `list_docsets()` default).
- `hub_delete_docset` deletes the `__facts` twin as well and reports both.

- [ ] **Step 1: Failing test** — reuse the two-docset sqlite setup from Task 8 and assert `json.loads(hub_mcp_server.hub_query_docset("h__d", "q"))["layer"] == "facts"`, `layer="raw"` returns raw, and `hub_delete_docset("h__d", confirm=True)` leaves `list_docsets(include_facts=True) == []`.
- [ ] **Step 2–5:** fail → implement → pass → commit `feat(mcp): hub_query_docset layer=facts by default; delete removes the facts twin`.

---

### Task 10: Pipeline stage `refine`; index both layers

**Files:**
- Modify: `scripts/pipeline_manager.py` (`STAGES`/`STAGE_TIMEOUT` ~79, `distill_timeout_for` ~99, `stage_distill`/`_remote_distill` ~668–700 → `stage_refine`, `stage_index` ~702, `process_item` ~712–790, docstring ~7–24), `scripts/hub_manager/queue_model.py` (`build_item_report` ~175–225), `scripts/hub_manager/docsets.py` (`index_argv` → also facts), `~/dev/distillers/CLAUDE.md` (note: `bulk` no longer on the pipeline path)
- Test: `tests/test_queue_model.py` (append), `tests/test_box_pool.py` if it names `distill`

**Interfaces:**
- `STAGES = ("mirror", "refine", "index")`; `STAGE_TIMEOUT["refine"] = 6 * 60 * 60` (LLM pass is page-count scaled: `refine_timeout_for(mirror)` = `max(floor, pages * 40 s)`).
- `stage_refine(url, host, box)` → local: `VENV_PY -m docset_refine all <mirror> --no-polish` with `PYTHONPATH=scripts`, `HUB_OLLAMA_URLS=f"{host}=1"`; remote: rsync mirror to box, run the same via `~/.global-ai-hub/scripts` if present on the box, else run locally (the box needs the hub venv for `embed_core`; `remote_safe()` gains that check). Polish is NOT run in the pipeline (cost); it is a manual/`e`-refresh option.
- `stage_index(url, host)` → indexes `<stem>.clean.md` as `<key>` (falls back to `<stem>.md` if no clean file) and `<stem>.reference/units.polished.jsonl` or `units.jsonl` merged with `structured.jsonl` (render writes `all_units.jsonl`) as `<key>__facts`.
- Legacy items with `stage_done=["distill","index","mirror"]`: `remaining_stages` yields `refine` automatically; `queue_model.retry`/`recrawl` unchanged. `build_item_report` lists `clean mirror`, `reference/`, `summary.json` counts instead of the distill index.

- [ ] **Step 1: Failing tests** — `test_queue_model.py`: `QueueItem(stage_done=["mirror","distill","index"]).remaining_stages == ["refine"]`; `build_item_report` on an item whose `<stem>.reference/summary.json` exists mentions `units` counts; `pipeline_manager.refine_argv(mirror)` returns the `-m docset_refine all … --no-polish` argv.
- [ ] **Step 2–5:** fail → implement → pass (full suite; `test_box_pool.py` / `test_site_clone.py` may assert stage names — update fixtures) → commit `feat(pipeline): distill stage becomes refine; index raw + facts layers`.

---

### Task 11: Docsets tab — fact layer surfaced; `e` refresh runs refine + index

**Files:**
- Modify: `scripts/hub_manager/docsets.py` (`docset_detail`, `index_argv` → `refresh_argv(mirror, key, polish=False)` returning a shell-free argv list run via `runner.ProcJob` sequence), `scripts/hub_manager/app.py` (`_reindex_docset`, detail pane, hint text, `_flush_jobs` chaining: when the `refine` slot exits 0 start the `index` slot), `docs/HUB-MANAGER.md`
- Test: `tests/test_docset_search.py`, `tests/test_app_smoke.py` (adjust the existing `e` assertion to the new argv)

**Interfaces:**
- `docsets.docset_detail(entry)` adds lines `facts    <n> units (snippets X · parameters Y · llm Z)` from `summary.json` when present and `reference [link=file://…/reference.md]…[/link]`; entries carry `facts` from Task 8's `list`.
- `docsets.refresh_argv(mirror_path, docset) -> list[list[str]]` → `[[py, "-m", "docset_refine", "all", mirror, "--no-polish"], [py, INDEXER, "index", clean_mirror, "--name", docset], [py, INDEXER, "index", all_units, "--units", "--name", docset + "__facts"]]`; `app._reindex_docset` runs them as a chain in slot `index` (next starts when the previous exits 0, via `_flush_jobs`).
- New key on the Docsets tab: `p` polish (runs `docset_refine polish` then the facts index) — confirm modal because it spends Claude usage.

- [ ] **Step 1: Failing tests** — `docset_detail` renders the facts line and the reference link from a temp `summary.json`; `refresh_argv` shape; the smoke test's `e` expectation becomes the 3-command chain's first argv.
- [ ] **Step 2–5:** fail → implement → pass → commit `feat(tui): Docsets tab shows the fact layer; e refresh = refine + index; p polish`.

---

### Task 12: Pilot end-to-end, golden re-run, rollout, cleanup

**Files:**
- Modify: `docs/superpowers/specs/2026-08-30-docset-golden-baseline.md` (after column), `~/dev/distillers/CLAUDE.md`, `docs/HUB-MANAGER.md`, `CLAUDE.md` (commands), `.gitignore` (no change needed — mirrors live outside the repo)
- Create: `scripts/docset_rollout.py` (probe every queue host for llms.txt; print the rollout order; `--apply` moves each trafilatura mirror aside and recrawls the item)

**Steps:**
- [ ] Run the pilot chain: `PYTHONPATH=scripts .venv/bin/python -m docset_refine all <code.claude.com.md>` (bulk on `qwen3:8b` via .75), then `polish --limit 5` and compare 5 batches of `units.jsonl` vs `units.polished.jsonl` by eye; then the two `index` commands. Gate: `summary.json` units ≤ 15% of clean prose bytes; `failed` pages < 5%.
- [ ] Compare `qwen3:8b` vs `qwen3.5:35b` on the first 20 pages (`--limit 20 --model qwen3.5:35b` into a scratch reference dir): unit count + a 30-unit spot check each; record in the baseline doc; set `HUB_LLM_MODEL` for refine accordingly in `hub-manager.json` settings (`refine_model`, new setting).
- [ ] Re-run the 10 golden questions (`scripts/ask … --corpora docsets`) and fill the After column. Gate: mean score improves and no question scores lower.
- [ ] `docset_rollout.py` (dry run) → order: `llms-full` hosts, `llms` hosts, crawl-only hosts. `--apply` for the first group; the Queue tab's `C`/`c` handles the rest as boxes free up; watch `refine` on the Queue tab.
- [ ] Cleanup: delete `*_master.md` / `*_live_preview.md` / `.*_distill_index.json` under `text-mirror/*.pages/` once each docset has a `summary.json` (`find … -name '*_master.md' -delete` guarded by that check in `docset_rollout.py --cleanup`); note in `~/dev/distillers/CLAUDE.md` that `bulk` is no longer on the pipeline path.
- [ ] Docs + logs: `docs/HUB-MANAGER.md` Docsets row and keys, `CLAUDE.md` command line for `docset_refine`, `prompts-hub.md` / `memory-hub.md`; commit `feat: docset reference layer rolled out; retire the bulk distill funnel`.

---

## Self-review

- **Spec coverage:** A → T2/T3; B → T3; C, D → T4; E → T5; F, G → T6; polish (decision 1) → T7; H → T8/T9/T11; I → T1/T12; J → T10/T12; K/L/M → out of scope (Later). Decisions 2–5 → T9 default `auto→facts`, T4 drops marketing/index from the clean mirror, T10 removes `bulk`, T12 runs the acquisition rollout in parallel with the pilot gate.
- **Placeholders:** none — every task has test code and interfaces; Tasks 5–11 reference "implement per the interfaces" with the algorithms stated in the interface block.
- **Type consistency:** unit record fields (`id,type,text,source_url,anchor,page_class,keywords,code,origin`) are used identically in T5–T9 and T11; `reference_dir` / `<stem>.reference/` naming is consistent; `<key>__facts` naming is consistent across T8–T11.
