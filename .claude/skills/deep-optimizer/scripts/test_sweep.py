"""Tests for sweep.py. Run: python3 -m unittest test_sweep (from this dir)."""
import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import sweep as S

FILES = {
    "a.py": "x=1\n", "b.js": "1\n", "c.sh": "echo\n", "d.sql": "select 1;\n",
    "e/SKILL.md": "---\nname: e\n---\n", "notes.md": "# notes\n", "f.svg": "<svg/>\n",
    "prompts/p.md": "you are\n", "agents/z.md": "---\nname: z\n---\n",
    "llms.txt": "# x\n", "data.bin": "\0\1", "page.html": "<p>\n",
}


def run(*argv, cwd=None):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = S.main(list(argv))
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue(), err.getvalue()


class Folder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for rel, text in FILES.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        self.args = ["--folder", str(self.root)]

    def rows(self):
        return json.loads((self.root / ".sweep" / "ledger.json").read_text())["rows"]

    def test_one_row_per_file_with_the_right_member(self):
        self.assertEqual(run("plan", *self.args)[0], 0)
        rows = self.rows()
        self.assertEqual(len(rows), len(FILES))
        want = {"a.py": "code-deep-optimizer", "b.js": "code-deep-optimizer",
                "e/SKILL.md": "skill-optimizer", "d.sql": "deep-query-optimizer",
                "notes.md": "document-critique", "f.svg": "design-deep-optimizer",
                "prompts/p.md": "prompt-deep-optimizer", "agents/z.md": "agent-deep-optimizer",
                "llms.txt": "llms-deep-optimizer", "page.html": "ui-deep-optimizer"}
        for rel, member in want.items():
            self.assertEqual(rows[rel]["member"], member, rel)
        self.assertEqual(rows["data.bin"]["status"], "skipped")

    def test_interrupted_sweep_resumes_at_the_next_file(self):
        run("plan", *self.args)
        routable = sorted(r for r, v in self.rows().items() if v["status"] == "pending")
        for rel in routable[:6]:
            run("done", rel, "--status", "done", *self.args)
        run("next", "--n", "2", *self.args)  # two in flight when the "crash" happens
        run("reset", *self.args)
        run("plan", *self.args)  # the re-plan must keep finished rows
        rows = self.rows()
        self.assertTrue(all(rows[r]["status"] == "done" for r in routable[:6]))
        code, out, _ = run("next", "--n", "1", *self.args)
        self.assertEqual(json.loads(out)["claimed"][0]["path"], routable[6])

    def test_changed_file_goes_back_to_pending(self):
        run("plan", *self.args)
        run("done", "a.py", "--status", "done", *self.args)
        (self.root / "a.py").write_text("x=2\n")
        run("plan", *self.args)
        self.assertEqual(self.rows()["a.py"]["status"], "pending")

    def test_concurrency_cap_counts_rows_in_flight(self):
        run("plan", *self.args)
        _, out1, _ = run("next", "--n", "3", *self.args)
        _, out2, _ = run("next", "--n", "3", *self.args)
        self.assertEqual(len(json.loads(out1)["claimed"]), 3)
        self.assertEqual(json.loads(out2)["claimed"], [])

    def test_map_override_and_unknown_member(self):
        run("plan", "--map", ".py=skill-optimizer", *self.args)
        self.assertEqual(self.rows()["a.py"]["member"], "skill-optimizer")
        self.assertEqual(run("plan", "--map", ".py=nope", *self.args)[0], 1)

    def test_plan_requires_exactly_one_target_kind(self):
        self.assertEqual(run("plan")[0], 1)


class Session(unittest.TestCase):
    def test_session_lists_dirty_and_branch_commits_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            g = lambda *a: subprocess.run(["git", *a], cwd=root, check=True, capture_output=True,
                                          env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                                               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
                                               "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"})
            g("init", "-q", "-b", "main")
            (root / "old.py").write_text("1\n")
            g("add", "."); g("commit", "-qm", "base")
            g("checkout", "-qb", "feature")
            (root / "new.py").write_text("2\n")
            g("add", "."); g("commit", "-qm", "feature file")
            (root / "old.py").write_text("changed\n")
            (root / "scratch.md").write_text("n\n")
            self.assertEqual(sorted(S.enumerate_session(root, None, None)),
                             ["new.py", "old.py", "scratch.md"])
            self.assertEqual(sorted(S.enumerate_session(root, "HEAD", None)),
                             ["old.py", "scratch.md"])


if __name__ == "__main__":
    unittest.main()
