import importlib.util
import pathlib
import tomllib
import unittest

spec = importlib.util.spec_from_file_location("repair", pathlib.Path(__file__).parents[1] / "repair_codex_plugin_hooks.py")
repair = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repair)


class HookRepairTests(unittest.TestCase):
    def test_arguments_are_in_command_and_other_hooks_unchanged(self):
        original = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
            {"command": "${CLAUDE_PLUGIN_ROOT}/scripts/hook", "args": ["claude", "PreToolUse"]},
            {"command": "another-hook", "args": ["keep"]},
        ]}]}}
        result = repair.repair_semgrep(original)
        hooks = result["hooks"]["PreToolUse"][0]["hooks"]
        self.assertEqual(hooks[0], {"command": '"${CLAUDE_PLUGIN_ROOT}/scripts/hook" claude PreToolUse'})
        self.assertEqual(hooks[1], original["hooks"]["PreToolUse"][0]["hooks"][1])
        self.assertIn("args", original["hooks"]["PreToolUse"][0]["hooks"][0])
        self.assertEqual(repair.repair_semgrep(result), result)

    def test_disable_is_scoped_and_idempotent(self):
        key = "ai-software-architect@openai-curated-remote:hooks/hooks.json:stop:0:0"
        original = f'[hooks.state."{key}"]\nenabled = true\ntrusted_hash = "keep"\n\n[plugins.other]\nenabled = true\n'
        result = repair.disable_windows_hooks(original)
        parsed = tomllib.loads(result)
        self.assertFalse(parsed["hooks"]["state"][key]["enabled"])
        self.assertEqual(parsed["hooks"]["state"][key]["trusted_hash"], "keep")
        self.assertTrue(parsed["plugins"]["other"]["enabled"])
        self.assertEqual(len(parsed["hooks"]["state"]), 5)
        self.assertEqual(repair.disable_windows_hooks(result), result)


if __name__ == "__main__":
    unittest.main()
