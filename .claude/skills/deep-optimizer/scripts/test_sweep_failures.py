"""Failure preservation and explicit MongoDB route regressions."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import sweep as S


class SweepFailures(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "a.sql").write_text("select 1;\n")
        (self.root / "pipeline.json").write_text('[{"$match":{"active":true}}]\n')

    def call(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = S.main([*args, "--folder", str(self.root)])
        return code, output.getvalue()

    def rows(self):
        return json.loads((self.root / ".sweep/ledger.json").read_text())["rows"]

    def fail_row(self):
        self.call("plan")
        self.call("done", "a.sql", "--status", "failed", "--note", "permission denied")

    def test_replan_retains_failed_status_and_note(self):
        self.fail_row()
        self.call("reset")
        self.call("plan")
        row = self.rows()["a.sql"]
        self.assertEqual(row["status"], "failed")
        self.assertEqual(row["note"], "permission denied")
        _, out = self.call("next", "--n", "4")
        self.assertFalse(any(r["path"] == "a.sql" for r in json.loads(out)["claimed"]))

    def test_retry_is_explicit_and_keeps_failure_history(self):
        self.fail_row()
        code, _ = self.call("retry", "a.sql")
        self.assertEqual(code, 0)
        row = self.rows()["a.sql"]
        self.assertEqual(row["status"], "pending")
        self.assertEqual(row["failures"][-1]["note"], "permission denied")

    def test_mql_override_invalidates_old_ambiguous_json_skip(self):
        self.call("plan")
        self.assertEqual(self.rows()["pipeline.json"]["status"], "skipped")
        code, _ = self.call("plan", "--map", ".json=deep-mongodb-mql-query-optimizer")
        self.assertEqual(code, 0)
        row = self.rows()["pipeline.json"]
        self.assertEqual(row["member"], "deep-mongodb-mql-query-optimizer")
        self.assertEqual(row["alias"], "/dmqo")
        self.assertEqual(row["status"], "pending")


if __name__ == "__main__":
    unittest.main()
