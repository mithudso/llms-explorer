#!/usr/bin/env python3
"""Braindump store: verbatim raw dumps plus one categorical llms file per category.

Usage:
  braindump.py save-raw < dump.txt            # prints the raw file path, with line numbers
  braindump.py file < parsed.json             # appends rows, rebuilds llms.txt, sends tasks to the to-do list
  braindump.py categories                     # canonical categories with what belongs in each
  braindump.py index                          # rebuild llms.txt only

parsed.json shape (the model writes it after reading the numbered raw dump):
  {"raw": "<path from save-raw>",
   "items": [{"category": "career", "kind": "idea", "text": "...", "line": 3}],
   "tasks": [{"text": "...", "line": 5}]}

Store: $BRAINDUMP_DIR (default $HOME/dev/personal/Areas/braindump)
  raw/YYYY-MM-DD-HHMMSS.md         verbatim capture, never edited
  braindump_<category>_llms.md     | item | kind | date | source | rows, source = raw path:line
  llms.txt                         v3 single-file index: ## Facts (counts), ## Sitemap (every category
                                   and raw file), ## Resources (to-do list, scripts, skills, tools)
"""
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "todo", "scripts"))
import todo  # noqa: E402

VERSION = "1.1.0"
SINGLE_FILE_MAX_BYTES = 32000      # llms-family-format.md v3 section 2
SINGLE_FILE_MAX_ENTRIES = 200
SKILLS_DIR = os.environ.get("BRAINDUMP_SKILLS_DIR", os.path.expanduser("~/.claude/skills"))

STORE = os.environ.get("BRAINDUMP_DIR", os.path.expanduser("~/dev/personal/Areas/braindump"))
RAW_DIR = os.path.join(STORE, "raw")

CATEGORIES = {
    "career": "job search, applications, interviews, positioning, long-term career moves",
    "work": "day-job TAM work: accounts, cases, customers, colleagues, process",
    "projects": "side projects and repos: what to build, fix, or change",
    "ideas": "new product, tool, or business ideas not yet tied to a project",
    "learning": "things to learn, read, or understand; insights from reading",
    "tech": "tooling, infrastructure, setup, AI/agent workflow observations",
    "trading": "markets, trading systems, crypto positions and strategy",
    "finance": "personal money: spending, bills, taxes, purchases",
    "health": "physical and mental health, sleep, exercise, energy",
    "relationships": "family, friends, dating, people",
    "personal": "home, errands, life admin, anything personal not above",
    "reflections": "feelings, mood, values, how things are going",
}
KINDS = {"idea", "insight", "decision", "question", "task", "concern", "note"}


def now():
    return dt.datetime.now()


def cell(s):
    return " ".join(str(s).split()).replace("|", "/")


def save_raw(text):
    text = text.strip("\n")
    if not text.strip():
        raise SystemExit("empty braindump")
    os.makedirs(RAW_DIR, exist_ok=True)
    stamp = now().strftime("%Y-%m-%d-%H%M%S")
    path = os.path.join(RAW_DIR, f"{stamp}.md")
    header = f"---\ntype: braindump-raw\ncaptured: {now().isoformat(timespec='seconds')}\n---\n"
    with open(path, "x", encoding="utf-8") as f:
        f.write(header + text + "\n")
    print(path)
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            print(f"{n:4}  {line.rstrip()}")


def category_file(cat):
    return os.path.join(STORE, f"braindump_{cat}_llms.md")


def append_rows(cat, rows):
    path = category_file(cat)
    if not os.path.exists(path):
        desc = CATEGORIES.get(cat, "custom category")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# braindump — {cat}\n\n> {desc}\n\n"
                    "Rows are appended by braindump.py; newest at the bottom. "
                    "source = verbatim raw dump path:line.\n\n"
                    "## Items\n| item | kind | date | source |\n|---|---|---|---|\n")
    with open(path, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(f"| {cell(r['text'])} | {r['kind']} | {r['date']} | {r['source']} |\n")


def count_rows(path):
    with open(path, encoding="utf-8") as f:
        return sum(1 for line in f if line.startswith("| ") and not line.startswith("| item "))


def mark(path):
    return "" if os.path.exists(path) else " (unverified)"


def category_dates(path):
    """Distinct `date` cells of a category file's rows (YYYY-MM-DD)."""
    dates = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("| ") and not line.startswith("| item "):
                m = re.search(r"\|\s*(\d{4}-\d{2}-\d{2})\s*\|", line)
                if m:
                    dates.append(m.group(1))
    return dates


def rebuild_index():
    """Write llms.txt as a v3 single file: ## Facts / ## Sitemap / ## Resources, <= 32,000 bytes.
    Counts only; no row text, so customer names never reach the index."""
    os.makedirs(STORE, exist_ok=True)
    cats = sorted(p for p in os.listdir(STORE) if re.match(r"braindump_[a-z0-9-]+_llms\.md$", p))
    raws = sorted(p for p in os.listdir(RAW_DIR) if p.endswith(".md")) if os.path.isdir(RAW_DIR) else []
    facts, sitemap, all_dates = [], [], []
    for path in cats:
        cat = path[len("braindump_"):-len("_llms.md")]
        full = os.path.join(STORE, path)
        n = count_rows(full)
        dates = category_dates(full)
        all_dates += dates
        span = f", {min(dates)} to {max(dates)}" if dates else ""
        facts.append(f"- {cat}: {n} items{span}. {CATEGORIES.get(cat, 'custom category')}")
        sitemap.append((f"- {full} — {cat}, {n} row{'s' if n != 1 else ''}"))
    total = sum(count_rows(os.path.join(STORE, p)) for p in cats)
    head_fact = (f"- {total} items in {len(cats)} categories, {len(raws)} raw dumps"
                 + (f", dates {min(all_dates)} to {max(all_dates)}" if all_dates else "") + ".")
    raw_lines = [f"- {os.path.join(RAW_DIR, r)} — verbatim capture" for r in raws]

    def render(raw_listing, note=None):
        entries = len(sitemap) + len(raw_listing)
        res = ["### Related files", "",
               f"- {todo.TODO_FILE} — the personal to-do list; tasks found in dumps also land here{mark(todo.TODO_FILE)}",
               f"- {STORE} — the braindump store{mark(STORE)}", "",
               "### Scripts", "",
               f"- `python3 {os.path.abspath(__file__)} categories` — canonical categories and what belongs in each{mark(__file__)}",
               f"- `python3 {os.path.abspath(__file__)} save-raw` — save a dump verbatim (stdin){mark(__file__)}",
               f"- `python3 {os.path.abspath(__file__)} file` — append parsed rows, rebuild this index, send tasks to the to-do list{mark(__file__)}",
               "", "### Skills", ""]
        res += [f"- `{n}` — {why}{mark(os.path.join(SKILLS_DIR, n))}"
                for n, why in (("todo", "read or change the to-do list"),
                               ("note-organizer", "reorganize a pile of notes into a structure"))]
        res += ["", "### Agents and tools", "", "- `hub_search_codebase` — semantic search of these rows through the hub index (unverified)"]
        text = "\n".join(
            ["# Braindump", "",
             "> Personal braindumps parsed into one llms file per category. Every row cites the verbatim raw capture it came from (raw/<stamp>.md:line).",
             f"> Source: {STORE} · Generated: {now().date().isoformat()} by braindump v{VERSION} · Mode: single-file · Entries: {entries}", "",
             "## Facts", "", head_fact] + facts + ([note] if note else []) +
            ["", "## Sitemap", ""] + sitemap + raw_listing + ["", "## Resources", ""] + res) + "\n"
        return text, entries

    text, entries = render(raw_lines)
    if len(text.encode()) > SINGLE_FILE_MAX_BYTES or entries > SINGLE_FILE_MAX_ENTRIES:
        # too many dumps for one file: keep the newest, summarize the rest per month (still one line each)
        keep = max(0, min(100, SINGLE_FILE_MAX_ENTRIES - len(sitemap) - 40))
        older, newer = raws[:len(raws) - keep] if keep else raws, raws[len(raws) - keep:] if keep else []
        months = {}
        for r in older:
            months.setdefault(r[:7], []).append(r)
        listing = [f"- {os.path.join(RAW_DIR, ms[0])} — first of {len(ms)} verbatim captures in {m}" for m, ms in sorted(months.items())]
        listing += [f"- {os.path.join(RAW_DIR, r)} — verbatim capture" for r in newer]
        text, entries = render(listing, f"- {len(older)} older raw dumps are summarized by month in the sitemap.")
    with open(os.path.join(STORE, "llms.txt"), "w", encoding="utf-8") as f:
        f.write(text)


def file_parsed(doc):
    raw = os.path.abspath(doc["raw"])
    if not raw.startswith(os.path.abspath(RAW_DIR) + os.sep) or not os.path.exists(raw):
        raise SystemExit(f"raw path must be an existing file under {RAW_DIR}: {raw}")
    with open(raw, encoding="utf-8") as f:
        n_lines = sum(1 for _ in f)
    date = now().date().isoformat()
    by_cat, warnings = {}, []
    for it in doc.get("items", []):
        cat = str(it.get("category", "")).strip().lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,30}", cat):
            raise SystemExit(f"bad category slug: {cat!r}")
        if cat not in CATEGORIES:
            warnings.append(f"new category '{cat}' (not in the canonical list)")
        kind = it.get("kind", "note")
        if kind not in KINDS:
            warnings.append(f"kind '{kind}' unknown, stored as note")
            kind = "note"
        line = int(it.get("line", 0))
        if not 1 <= line <= n_lines:
            raise SystemExit(f"line {line} outside {raw} (1..{n_lines})")
        if not str(it.get("text", "")).strip():
            continue
        by_cat.setdefault(cat, []).append(
            {"text": it["text"], "kind": kind, "date": date, "source": f"{raw}:{line}"})
    for t in doc.get("tasks", []):
        if not 1 <= int(t.get("line", 0)) <= n_lines or not str(t.get("text", "")).strip():
            raise SystemExit(f"bad task entry (needs text and a line in 1..{n_lines}): {t}")
    for cat, rows in by_cat.items():
        append_rows(cat, rows)
    added_tasks = []
    for t in doc.get("tasks", []):
        line = int(t.get("line", 0))
        item_id = todo.add_item(t["text"], f"braindump:{raw}:{line}")
        added_tasks.append((item_id, t["text"]))
    rebuild_index()
    for w in sorted(set(warnings)):
        print(f"warning: {w}")
    for cat, rows in sorted(by_cat.items()):
        print(f"{cat}: +{len(rows)} -> {category_file(cat)}")
    for item_id, text in added_tasks:
        print(f"todo: {'+' + item_id if item_id else 'already listed'}  {text}")
    print(f"index: {os.path.join(STORE, 'llms.txt')}")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "save-raw":
        save_raw(sys.stdin.read())
    elif cmd == "file":
        file_parsed(json.load(sys.stdin))
    elif cmd == "categories":
        for k, v in CATEGORIES.items():
            print(f"{k:<14} {v}")
    elif cmd == "index":
        rebuild_index()
        print(os.path.join(STORE, "llms.txt"))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
