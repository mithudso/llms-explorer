import json
from pathlib import Path
import unittest
from unittest.mock import patch

import parse_framed


class FramingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (Path(__file__).parent / "startup-native.log").read_text()
        cls.normal = "\n".join(parse_framed.PREFIX.sub("", line) for line in cls.raw.splitlines())

    def test_actual_log_retains_all_records_and_original_stages(self):
        result = parse_framed.parse_memory_log(self.raw)
        self.assertEqual([x["line"] for x in result["framing"]["normalized_records"]], [184, 222])
        self.assertEqual(len(result["unassigned_success_records"]), 5)
        self.assertEqual(result["pre_load_guard"]["required_pool_bytes"], 16667408384)
        self.assertTrue(result["same_process_preload_guard_association"])
        self.assertTrue(result["successful_pre_post_association"])
        self.assertFalse(result["graph_peak_or_fit_verified"])

    def test_bare_log_has_identical_semantic_result(self):
        a = parse_framed.parse_memory_log(self.raw)
        b = parse_framed.parse_memory_log(self.normal)
        del a["framing"], b["framing"]
        self.assertEqual(a, b)

    def test_invalid_prefixes_do_not_hide_invalid_records(self):
        record = '{"llmsx_memory_snapshot":{"version":1,"success":true,"free_bytes":1,"total_bytes":2,"capacity_valid":true}}'
        for prefix in ("noise ", "0.02.206.863 I foo ", "0.2.206.863 ", "0.02.206.863 X ", "\x1b[0m", "0.02.206.863  "):
            with self.subTest(prefix=prefix), self.assertRaises(ValueError):
                parse_framed.parse_memory_log(self.normal + "\n" + prefix + record)

    def test_duplicate_stage_is_rejected(self):
        line = '{"llmsx_memory_stage":{"version":1,"stage":"post_load","event":"begin"}}'
        with self.assertRaises(ValueError):
            parse_framed.parse_memory_log(self.normal + "\n0.02.206.863 I " + line)

    def test_duplicate_json_key_is_rejected(self):
        line = '{"llmsx_memory_snapshot":{},"llmsx_memory_snapshot":{}}'
        with self.assertRaises(ValueError):
            parse_framed.parse_memory_log(self.normal + "\n0.02.206.863 " + line)

    def test_suffix_or_second_object_is_rejected(self):
        line = '{"llmsx_memory_snapshot":{"version":1,"success":true,"free_bytes":1,"total_bytes":2,"capacity_valid":true}}'
        for suffix in (" noise", " {}", " NaN"):
            with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                parse_framed.parse_memory_log(self.normal + "\n0.02.206.863 I " + line + suffix)

    def test_nonfinite_record_is_rejected(self):
        line = '{"llmsx_memory_snapshot":{"version":1,"success":true,"free_bytes":NaN,"total_bytes":2,"capacity_valid":true}}'
        with self.assertRaises(ValueError):
            parse_framed.parse_memory_log(self.normal + "\n0.02.206.863 " + line)

    def test_missing_stage_still_rejected(self):
        with self.assertRaises(ValueError):
            parse_framed.parse_memory_log(self.normal.replace('"stage":"post_load","event":"end"', '"stage":"post_load","event":"begin"'))

    def test_budget_floor_is_unchanged(self):
        with self.assertRaises(ValueError):
            parse_framed.parse_memory_log(self.normal.replace('"required_pool_bytes":16667408384', '"required_pool_bytes":16667408383'))

    def test_capacity_snapshot_association_is_unchanged(self):
        lines = self.normal.splitlines()
        guard = json.loads(lines[57])
        guard["llmsx_preload_guard"]["free_bytes"] -= 1
        lines[57] = json.dumps(guard)
        with self.assertRaises(ValueError):
            parse_framed.parse_memory_log("\n".join(lines))

    def test_modified_parser_bytes_are_rejected_before_execution(self):
        with patch.object(Path, "read_bytes", return_value=b"raise SystemExit('must not execute')"), patch("builtins.exec") as execute:
            with self.assertRaisesRegex(ValueError, "Original parser SHA differs"):
                parse_framed.parse_memory_log(self.normal)
            execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
