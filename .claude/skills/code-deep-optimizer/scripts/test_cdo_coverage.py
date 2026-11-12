"""Coverage/resume regressions; all files live in a temporary directory."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import cdo_ledger as L


class Coverage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        (self.repo / "a.py").write_text("value = 1\n")

    def run_cli(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = L.main([*args, "--repo", str(self.repo)])
        return code, output.getvalue()

    def plan(self):
        code, out = self.run_cli("plan", "--json")
        self.assertEqual(code, 0)
        return json.loads(out)

    def test_blocked_partial_review_is_requeued(self):
        self.run_cli("record", "--passes", "C1", "--verdict", "BLOCKED", "a.py")
        plan = self.plan()
        self.assertEqual([r["path"] for r in plan["review"]], ["a.py"])
        self.assertEqual(plan["unchanged_skipped"], 0)

    def test_clean_label_without_required_passes_is_not_coverage(self):
        self.run_cli("record", "--passes", "C1", "--verdict", "CLEAN", "a.py")
        self.assertEqual(len(self.plan()["review"]), 1)

    def test_complete_current_contract_review_can_be_skipped(self):
        self.run_cli("record", "--passes", ",".join(L.PASSES), "--verdict", "CLEAN", "a.py")
        self.assertEqual(self.plan()["review"], [])
        self.assertEqual(self.plan()["unchanged_skipped"], 1)

    def test_old_contract_is_requeued(self):
        self.run_cli("record", "--passes", ",".join(L.PASSES), "--verdict", "CLEAN", "a.py")
        data = L.load(self.repo)
        data["files"]["a.py"].pop("review_contract", None)
        L.save(self.repo, data)
        self.assertEqual(len(self.plan()["review"]), 1)

    def test_explicit_na_with_reason_completes_applicable_coverage(self):
        passes = ",".join(p for p in L.PASSES if p != "T4")
        code, _ = self.run_cli("record", "--passes", passes, "--na-passes", "T4",
                               "--na-reason", "not a test file", "--verdict", "CLEAN", "a.py")
        self.assertEqual(code, 0)
        self.assertEqual(self.plan()["review"], [])


if __name__ == "__main__":
    unittest.main()
