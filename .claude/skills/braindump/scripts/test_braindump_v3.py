#!/usr/bin/env python3
"""v3 index tests for braindump.py (BRAINDUMP_DIR in a temp dir; no to-do writes)."""
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("braindump.py")


def run(store, *args, stdin=""):
    env = dict(os.environ, BRAINDUMP_DIR=str(store), BRAINDUMP_SKILLS_DIR=str(store / "skills"))
    r = subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout


def seed(store, n_raw=2):
    (store / "raw").mkdir(parents=True)
    for i in range(n_raw):
        (store / "raw" / f"2026-10-{i % 28 + 1:02d}-0900{i:02d}.md").write_text("---\ntype: braindump-raw\n---\nx\n")
    (store / "braindump_career_llms.md").write_text(
        "# braindump — career\n\n## Items\n| item | kind | date | source |\n|---|---|---|---|\n"
        "| secret customer plan | idea | 2026-10-02 | /x/raw/a.md:3 |\n| second | note | 2026-10-05 | /x/raw/a.md:4 |\n")


class V3(unittest.TestCase):
    def test_index_has_three_sections_and_matching_entries(self):
        with tempfile.TemporaryDirectory() as t:
            store = Path(t) / "bd"
            seed(store)
            run(store, "index")
            txt = (store / "llms.txt").read_text()
            for h in ("## Facts", "## Sitemap", "## Resources", "Mode: single-file"):
                self.assertIn(h, txt)
            sm = txt.split("## Sitemap")[1].split("## Resources")[0]
            listed = [l for l in sm.splitlines() if l.startswith("- ")]
            self.assertEqual(int(re.search(r"Entries: (\d+)", txt).group(1)), len(listed))
            self.assertEqual(len(listed), 3)                       # 1 category file + 2 raw dumps
            self.assertIn("career: 2 items, 2026-10-02 to 2026-10-05", txt)
            self.assertNotIn("secret customer plan", txt)           # counts only, never row text
            self.assertIn("(unverified)", txt.split("## Resources")[1])   # skills dir is empty here

    def test_many_raw_dumps_stay_under_caps(self):
        with tempfile.TemporaryDirectory() as t:
            store = Path(t) / "bd"
            seed(store, n_raw=400)
            run(store, "index")
            txt = (store / "llms.txt").read_text()
            self.assertLessEqual(len(txt.encode()), 32000)
            listed = [l for l in txt.split("## Sitemap")[1].split("## Resources")[0].splitlines() if l.startswith("- ")]
            self.assertLessEqual(len(listed), 200)
            self.assertEqual(int(re.search(r"Entries: (\d+)", txt).group(1)), len(listed))


if __name__ == "__main__":
    unittest.main()
