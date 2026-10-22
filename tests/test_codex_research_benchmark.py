"""Independent checks for the quality and depth metrics used in the live study."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("research_benchmark", Path(__file__).parents[1] / "scripts/codex_research_benchmark.py")
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.evidence = {"sources": [{"id": "S1", "text": "PASSIVE never invokes the busy handler. It may leave the checkpoint unfinished."}],
                         "gold": {"passive": "PASSIVE never invokes the busy handler."}}
        self.output = {"concepts": [{"id": "c1", "name": "PASSIVE"}],
                       "claims": [{"id": "f1", "concept_id": "c1", "source_id": "S1",
                                   "text": "PASSIVE does not invoke the busy handler.",
                                   "quote": "PASSIVE never invokes the busy handler."}]}
        self.judge = {"claims": [{"id": "f1", "supported": True, "atomic": True, "depth": 2,
                                  "gold_ids": ["passive"]}],
                      "concepts": [{"id": "c1", "canonical_name": "PASSIVE", "meaningful": True, "in_scope": True}]}

    def test_grounded_specific_claim_counts_without_self_reported_depth(self):
        self.output["claims"][0]["pass"] = 99
        result = bench.metrics(self.output, self.judge, self.evidence)
        self.assertEqual((result["supported_atomic_claims"], result["reference_coverage"], result["grounded_unique_concepts"]), (1, 1, 1))
        self.assertEqual(result["mean_depth"], 2)

    def test_quote_present_but_claim_not_entailed_receives_no_credit(self):
        self.judge["claims"][0]["supported"] = False
        result = bench.metrics(self.output, self.judge, self.evidence)
        self.assertEqual(result["exact_quotes"], 1)
        self.assertEqual(result["source_support_percent"], 0)
        self.assertEqual(result["quality_percent"], 0)
        self.assertEqual(result["grounded_unique_concepts"], 0)

    def test_fabricated_quote_or_wrong_source_receives_no_credit(self):
        for change in ({"quote": "PASSIVE always shrinks WAL."}, {"source_id": "S999"}):
            self.output["claims"][0].update(change)
            result = bench.metrics(self.output, self.judge, self.evidence)
            self.assertEqual(result["supported_atomic_claims"], 0)
            self.assertEqual(result["source_support_percent"], 100)
            self.assertEqual(result["exact_quote_percent"], 0)

    def test_duplicate_concepts_and_unknown_rubric_keys_do_not_inflate_score(self):
        self.judge["concepts"].append({"id": "c1", "canonical_name": "passive", "meaningful": True, "in_scope": True})
        self.judge["claims"][0]["gold_ids"].extend(["passive", "invented"])
        result = bench.metrics(self.output, self.judge, self.evidence)
        self.assertEqual(result["grounded_unique_concepts"], 1)
        self.assertEqual(result["reference_coverage"], 1)

    def test_missing_judgment_is_reported_and_never_assumed_supported(self):
        self.judge["claims"] = []
        result = bench.metrics(self.output, self.judge, self.evidence)
        self.assertEqual(result["missing_judgments"], 1)
        self.assertEqual(result["supported_atomic_claims"], 0)

    def test_repeated_claim_is_not_new_information(self):
        self.output["claims"].append({**self.output["claims"][0], "id": "f2"})
        self.judge["claims"].append({**self.judge["claims"][0], "id": "f2", "duplicate_of": "f1"})
        result = bench.metrics(self.output, self.judge, self.evidence)
        self.assertEqual(result["claims"], 2)
        self.assertEqual(result["supported_atomic_claims"], 1)

    def test_saturation_requires_two_low_information_deepening_passes(self):
        self.output["verdict"] = "SATURATED-DEPTH"
        self.output["passes"] = [{"pass": 0, "new_claims": 1, "total_claims": 1, "new_information_rate": 1}]
        self.assertTrue(bench.metrics(self.output, self.judge, self.evidence)["saturation_rule_error"])
        self.output["passes"].extend({"pass": n, "new_claims": 0, "total_claims": 1, "new_information_rate": 0} for n in (1, 2))
        result = bench.metrics(self.output, self.judge, self.evidence)
        self.assertFalse(result["saturation_rule_error"])
        self.assertEqual(result["pass_accounting_errors"], 0)

    def test_timeout_is_visible_in_report_without_invented_quality_score(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            bench.write(out / "evidence.json", self.evidence)
            bench.write(out / "cells/dr__gpt-6-luna__max__r1/generation/run.json", {"is_error": True, "seconds": 900, "returncode": -9})
            bench.report(out)
            self.assertEqual(json.loads((out / "results.json").read_text()), [])
            self.assertEqual(len(json.loads((out / "failures.json").read_text())), 1)
            self.assertIn("timeout/error", (out / "results.md").read_text())


class HierarchyTests(unittest.TestCase):
    def test_ids_and_exact_names_describe_the_same_three_levels(self):
        nodes = [{"id": "a", "name": "Checkpoint", "parent": "SQLite"},
                 {"id": "b", "name": "Mode", "parent": "a"},
                 {"id": "c", "name": "Busy fallback", "parent": "Mode"}]
        self.assertEqual(bench.hierarchy(nodes)["returned_hierarchy_max_depth"], 3)

    def test_parent_cycle_does_not_create_unbounded_depth(self):
        nodes = [{"id": "c", "name": "C", "parent": "a"},
                 {"id": "a", "name": "A", "parent": "b"},
                 {"id": "b", "name": "B", "parent": "a"}]
        result = bench.hierarchy(nodes)
        self.assertEqual(result["returned_hierarchy_max_depth"], 0)
        self.assertEqual(result["hierarchy_cycle_nodes"], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
