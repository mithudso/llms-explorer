"""Regression tests for malformed suites and fixture integrity; no skill execution."""
import json
from pathlib import Path
import tempfile
import unittest

from suite_validator import validate_suite


class SuiteValidation(unittest.TestCase):
    def check_data(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evals.json"
            path.write_text(json.dumps(data))
            return validate_suite(str(path))

    def test_missing_fixture_is_a_high_finding(self):
        report = self.check_data({"skill_name": "sample", "evals": [{
            "id": 1, "name": "missing-input", "prompt": "Summarize this fixture",
            "expected_output": "A summary of the supplied input", "files": ["inputs/missing.txt"],
            "assertions": [{"name": "coverage", "check": "includes every row", "type": "structural"}],
        }]})
        self.assertTrue(any(r["pass"] == "Pass G" and r["severity"] == "High"
                            for r in report["findings"]))

    def test_non_object_trigger_row_reports_schema_failure(self):
        report = self.check_data(["not a query object"])
        self.assertGreater(report["high_findings"], 0)

    def test_invalid_top_level_reports_schema_failure(self):
        report = self.check_data(42)
        self.assertGreater(report["high_findings"], 0)

    def test_missing_required_case_fields_report_schema_failure(self):
        report = self.check_data({"skill_name": "sample", "evals": [{"prompt": "hello"}]})
        self.assertTrue(any(r["pass"] == "Pass L" and r["severity"] == "High"
                            for r in report["findings"]))

    def test_trigger_labels_must_be_booleans_and_queries_nonempty(self):
        report = self.check_data([{"query": "", "should_trigger": "false"}])
        self.assertTrue(any(r["pass"] == "Pass L" and r["severity"] == "High"
                            for r in report["findings"]))

    def test_valid_trigger_projection_has_no_schema_findings(self):
        rows = [{"query": f"Optimize code module {i}", "should_trigger": i < 10} for i in range(20)]
        report = self.check_data(rows)
        self.assertFalse(any(r["pass"] == "Pass L" for r in report["findings"]))


if __name__ == "__main__":
    unittest.main()
