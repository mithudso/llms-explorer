"""Source-fidelity and cache-preservation regressions; no model or network calls."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from argparse import Namespace
from array import array
from unittest.mock import Mock, patch

SOURCE = Path(os.environ.get("SKO_TEST_SOURCE_ROOT", Path(__file__).parent))
spec = importlib.util.spec_from_file_location("concept_under_test", SOURCE / "concept_abstract.py")
lca = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lca)


def row():
    return {"id": "s01u000001", "text": "The cache retains a prefix for five minutes.",
            "facet": "definition", "relation": "about", "keep": True}


class SourceFidelity(unittest.TestCase):
    def test_rejects_rewritten_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            classified = Path(tmp) / "classified.jsonl"
            classified.write_text(json.dumps({"id": row()["id"],
                                              "text_fix": "The cache retains every request forever."}) + "\n")
            with self.assertRaisesRegex(ValueError, "contiguous source substring"):
                lca._apply_classified([row()], classified)

    def test_accepts_an_exact_contiguous_trim(self):
        with tempfile.TemporaryDirectory() as tmp:
            classified = Path(tmp) / "classified.jsonl"
            classified.write_text(json.dumps({"id": row()["id"], "text_fix": "five minutes"}) + "\n")
            kept, _ = lca._apply_classified([row()], classified)
            self.assertEqual(kept[0]["text"], "five minutes")


class CachePreservation(unittest.TestCase):
    def cache_files(self, root, keys):
        folder = root / "fixture-model"
        folder.mkdir()
        (folder / "meta.json").write_text(json.dumps({"model": "fixture-model", "dim": 2}))
        (folder / "keys.txt").write_text("\n".join(keys) + "\n")
        (folder / "vectors.f32").write_bytes(array("f", [1.0, 0.0]).tobytes())
        return folder

    def test_misaligned_cache_is_rejected_without_truncation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = self.cache_files(root, ["a", "b"])
            before = {p.name: p.read_bytes() for p in folder.iterdir()}
            with self.assertRaisesRegex(RuntimeError, "misaligned"):
                lca.VecCache(root, "fixture-model")
            self.assertEqual(before, {p.name: p.read_bytes() for p in folder.iterdir()})

    def test_dimension_change_does_not_append(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = self.cache_files(root, [lca.VecCache.key("old text")])
            cache = lca.VecCache(root, "fixture-model")
            before = {p.name: p.read_bytes() for p in folder.iterdir() if p.name != ".lock"}
            with patch.object(lca, "_embed_call", return_value=[[1.0, 0.0, 0.0]]):
                with self.assertRaisesRegex(RuntimeError, "dimension"):
                    cache.get_many(["new text"], "fixture-model", "http://unused.invalid", log=lambda *_: None)
            self.assertEqual(before, {p.name: p.read_bytes() for p in folder.iterdir() if p.name != ".lock"})


class PublicationBoundary(unittest.TestCase):
    def compile_with_binding(self, private):
        with tempfile.TemporaryDirectory() as tmp:
            hub = Path(tmp) / "hub"
            (hub / "research").mkdir(parents=True)
            (hub / "research/.site-sync.json").write_text("{}")
            out = hub / "llms-concepts/cache.llms"
            out.mkdir(parents=True)
            unit = lca._unit("s01u000001", "statement", "A cache is a store for repeated reads.",
                             "https://source.fixture.invalid/cache", "#definition")
            unit.update(matched=["cache"], relation="about", score=1.0, facet="definition", keep=True)
            (out / "pool.jsonl").write_text(json.dumps(unit) + "\n")
            hook = types.ModuleType("research_site_hook")
            hook.refresh = Mock()
            args = Namespace(out=str(out), concept="Cache", lexicon=None, classified=None,
                             budget_tokens=8000, summary=None, rights="extractive", base_url=None,
                             keep_lead_ins=True, max_related=20, private=private)
            with patch.dict(os.environ, {"HUB_DIR": str(hub)}), patch.dict("sys.modules", {"research_site_hook": hook}):
                lca.compile_pack(args)
            return hook.refresh.call_count

    def test_private_canonical_compile_does_not_refresh_site(self):
        self.assertEqual(self.compile_with_binding(private=True), 0)

    def test_existing_public_completion_hook_is_preserved(self):
        self.assertEqual(self.compile_with_binding(private=False), 1)


if __name__ == "__main__":
    unittest.main()
