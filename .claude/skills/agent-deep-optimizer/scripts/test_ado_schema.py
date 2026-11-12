"""Synthetic permission/parser counterexamples; no provider or target execution."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import ado_tools as A


class EffectiveGrant(unittest.TestCase):
    def schema(self, frontmatter):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "auditor.md"
            path.write_text("---\nname: auditor\ndescription: Review local files\n" + frontmatter +
                            "\n---\nThis is read-only. Never delegate. Return a final report.\n")
            with contextlib.redirect_stdout(io.StringIO()) as output:
                with self.assertRaises(SystemExit) as stopped:
                    A.schema(argparse.Namespace(target=str(path), project_dir=directory))
            return stopped.exception.code, json.loads(output.getvalue())

    def test_partial_disallow_does_not_hide_write(self):
        code, report = self.schema("tools: Read, Write, Edit\ndisallowedTools: Edit")
        self.assertNotEqual(code, 0)
        self.assertTrue(any(r["check"] == "read-only-with-write-tools" for r in report["findings"]))
        self.assertEqual(report["effective_write_tools"], ["Write"])

    def test_full_disallow_removes_each_write_tool(self):
        code, report = self.schema("tools: Read, Write, Edit, NotebookEdit\ndisallowedTools: Write, Edit, NotebookEdit")
        self.assertEqual(code, 0)
        self.assertEqual(report["effective_write_tools"], [])

    def test_wildcard_disallow_removes_write_tools(self):
        code, report = self.schema('tools: Read, Write, Edit\ndisallowedTools: "*"')
        self.assertEqual(code, 0)
        self.assertEqual(report["effective_write_tools"], [])

    def test_missing_strict_parser_never_certifies_even_simple_input(self):
        with patch.object(A, "yaml", None):
            code, report = self.schema("tools: Read")
        self.assertNotEqual(code, 0)
        self.assertEqual(report["yaml_parser"], "fallback")
        self.assertTrue(any(r["check"] == "yaml-parser-unavailable" for r in report["findings"]))

    def test_malformed_yaml_cannot_pass_fallback(self):
        with patch.object(A, "yaml", None):
            code, report = self.schema("tools: Read\ninitialPrompt: invalid: nested colon")
        self.assertNotEqual(code, 0)
        self.assertTrue(any(r["check"] == "yaml-parser-unavailable" for r in report["findings"]))


if __name__ == "__main__":
    unittest.main()
