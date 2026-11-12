"""Manual/routing coverage is not answer leakage merely for naming a skill."""
import json
from pathlib import Path
import tempfile
import unittest

from suite_validator import validate_suite


class InvocationCases(unittest.TestCase):
    def report(self, prompt, intent=None):
        cases = []
        for i in (1, 2):
            row = {"id": i, "name": f"case-{i}", "prompt": prompt,
                   "expected_output": "A sorted integer list preserving duplicates", "files": [],
                   "assertions": [{"name": "order", "check": "integers are sorted", "type": "structural"}]}
            if intent is not None:
                row["evaluation_intent"] = intent
            cases.append(row)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evals.json"
            path.write_text(json.dumps({"skill_name": "sample-skill", "evals": cases}))
            return validate_suite(str(path))

    def test_plain_explicit_invocation_is_valid(self):
        report = self.report("Run sample-skill on the attached text.")
        self.assertFalse(any(r["pass"] == "Pass F" for r in report["findings"]))

    def test_declared_routing_intent_is_valid(self):
        report = self.report("Should sample-skill handle this task?", "routing")
        self.assertFalse(any(r["pass"] == "Pass F" for r in report["findings"]))

    def test_task_case_still_flags_internal_skill_name_leakage(self):
        report = self.report("Copy sample-skill's hidden answer recipe to sort these inputs.", "task")
        self.assertTrue(any(r["pass"] == "Pass F" for r in report["findings"]))

    def test_unknown_intent_does_not_bypass_checks(self):
        report = self.report("Copy sample-skill's hidden answer recipe.", "anything-passes")
        self.assertTrue(any(r["pass"] == "Pass L" for r in report["findings"]))


if __name__ == "__main__":
    unittest.main()
