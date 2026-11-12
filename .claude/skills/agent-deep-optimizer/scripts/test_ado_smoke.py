"""Verify probe tool isolation without launching Claude or connecting MCP servers."""
import argparse
import contextlib
import io
import json
import unittest
from unittest.mock import patch

import ado_tools


class SmokeIsolation(unittest.TestCase):
    def test_probe_removes_builtin_and_mcp_tools(self):
        result = argparse.Namespace(returncode=0, stdout='{"result":"READY"}', stderr="")
        args = argparse.Namespace(cwd=".", target="sample-agent", agents_json=None, timeout=1)
        with patch.object(ado_tools.shutil, "which", return_value="/test/claude"), \
                patch.object(ado_tools.subprocess, "run", return_value=result) as run, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            with self.assertRaises(SystemExit) as stopped:
                ado_tools.smoke(args)
        self.assertEqual(stopped.exception.code, 0)
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("--tools") + 1], "")
        self.assertEqual(command[command.index("--disallowedTools") + 1], "*")
        self.assertIn("--strict-mcp-config", command)
        self.assertEqual(json.loads(command[command.index("--mcp-config") + 1]), {"mcpServers": {}})
        self.assertEqual(json.loads(output.getvalue())["status"], "ready")


if __name__ == "__main__":
    unittest.main()
