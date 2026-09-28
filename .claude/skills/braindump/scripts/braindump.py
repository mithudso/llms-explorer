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

Store: $BRAINDUMP_DIR (default ~/dev/personal/Areas/braindump)
  raw/YYYY-MM-DD-HHMMSS.md         verbatim capture, never edited
  braindump_<category>_llms.md     | item | kind | date | source | rows, source = raw path:line
  llms.txt                         index of category files with counts
"""
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "todo", "scripts"))
import todo  # noqa: E402

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


def rebuild_index():
    os.makedirs(STORE, exist_ok=True)
    lines = ["# Braindump", "",
             "> Personal braindumps parsed into one llms file per category. Every row cites the verbatim",
             "> raw capture it came from (raw/<stamp>.md:line). Tasks found in dumps also land in",
             f"> {todo.TODO_FILE}.", "",
             f"<!-- generator: braindump.py · generated: {now().date().isoformat()} -->", "",
             "## Categories"]
    for path in sorted(p for p in os.listdir(STORE) if re.match(r"braindump_[a-z0-9-]+_llms\.md$", p)):
        cat = path[len("braindump_"):-len("_llms.md")]
        desc = CATEGORIES.get(cat, "custom category")
        lines.append(f"- [{cat}]({path}): {count_rows(os.path.join(STORE, path))} items. {desc}")
    raws = sorted(os.listdir(RAW_DIR)) if os.path.isdir(RAW_DIR) else []
    lines += ["", "## Raw captures", f"- {len(raws)} dumps in raw/"
              + (f", latest {raws[-1]}" if raws else "")]
    with open(os.path.join(STORE, "llms.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


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
