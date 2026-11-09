"""Tests for cdo_ledger.py. Run: python3 -m unittest test_cdo_ledger (from this dir)."""
import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import cdo_ledger as L


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = L.main(list(argv))
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue(), err.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        for name in ("a.py", "b.py", "c.js"):
            (self.repo / name).write_text(f"print('{name}')\n")
        (self.repo / "README.md").write_text("docs\n")
        (self.repo / "node_modules").mkdir()
        (self.repo / "node_modules" / "x.js").write_text("x\n")

    def plan(self, *extra):
        code, out, _ = run("plan", "--repo", str(self.repo), "--json", *extra)
        self.assertEqual(code, 0)
        return json.loads(out)


class Plan(Base):
    def test_first_run_reviews_every_source_and_skips_vendored(self):
        got = self.plan()
        self.assertEqual({r["path"] for r in got["review"]}, {"a.py", "b.py", "c.js"})
        self.assertEqual({r["reason"] for r in got["review"]}, {"new"})

    def test_rerun_reviews_only_changed_and_new(self):
        run("begin", "--repo", str(self.repo))
        run("record", "--repo", str(self.repo), "--passes", "C1,S1", "a.py", "b.py", "c.js")
        self.assertEqual(self.plan()["review"], [])
        (self.repo / "b.py").write_text("print('edited')\n")
        (self.repo / "d.py").write_text("print('d')\n")
        got = self.plan()
        self.assertEqual({(r["path"], r["reason"]) for r in got["review"]},
                         {("b.py", "changed"), ("d.py", "new")})
        self.assertEqual(got["unchanged_skipped"], 2)

    def test_full_flag_ignores_the_ledger(self):
        run("record", "--repo", str(self.repo), "--passes", "C1", "a.py", "b.py", "c.js")
        got = self.plan("--full")
        self.assertEqual(len(got["review"]), 3)
        self.assertEqual({r["reason"] for r in got["review"]}, {"full"})

    def test_quick_triage_is_not_coverage(self):
        run("begin", "--repo", str(self.repo), "--quick")
        run("record", "--repo", str(self.repo), "--passes", "C1,C3,S1", "a.py")
        reasons = {r["path"]: r["reason"] for r in self.plan()["review"]}
        self.assertEqual(reasons["a.py"], "quick-only")

    def test_max_files_defers_without_recording(self):
        got = self.plan("--max-files", "2")
        self.assertEqual((len(got["review"]), len(got["deferred"])), (2, 1))
        self.assertEqual(len(self.plan()["review"]), 3)

    def test_prune_drops_deleted_files(self):
        run("record", "--repo", str(self.repo), "--passes", "C1", "a.py")
        (self.repo / "a.py").unlink()
        self.assertEqual(self.plan()["removed_from_disk"], ["a.py"])
        run("prune", "--repo", str(self.repo))
        self.assertEqual(self.plan()["removed_from_disk"], [])


class Receipt(Base):
    def test_silently_dropped_pass_fails_the_receipt(self):
        run("begin", "--repo", str(self.repo))
        run("record", "--repo", str(self.repo), "--passes", "C1", "a.py")
        code, out, _ = run("receipt", "--repo", str(self.repo))
        self.assertEqual(code, 2)
        self.assertIn("Silently dropped", out)

    def test_complete_receipt_lists_every_pass(self):
        run("begin", "--repo", str(self.repo))
        run("record", "--repo", str(self.repo), "--passes", ",".join(L.PASSES), "a.py")
        code, out, _ = run("receipt", "--repo", str(self.repo), "--status", "CLEAN")
        self.assertEqual(code, 0)
        self.assertIn("Fix-track passes that ran: 18 of 18", out)
        self.assertIn("covered by the ledger now: 1 of 3", out)

    def test_na_pass_needs_a_reason(self):
        code, _, err = run("pass", "--repo", str(self.repo), "M3", "--state", "na")
        self.assertEqual(code, 1)
        self.assertIn("--reason", err)

    def test_unknown_pass_is_rejected(self):
        code, _, _ = run("record", "--repo", str(self.repo), "--passes", "ZZ", "a.py")
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
