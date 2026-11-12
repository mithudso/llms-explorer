"""Synthetic customer-pack checks; never reads an engagement drive or calls a service."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(os.environ.get("SKO_TEST_SOURCE_ROOT", Path(__file__).parent))


class JsonRedaction(unittest.TestCase):
    def check_pack(self, credential=False, *, shape="family", sitemap=True, padding=0, sibling=False):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "Fixture Account" / "llms"
            out.mkdir(parents=True)
            header = ("# Fixture Account — role\n> Sources: 1 local artifact · 0 Glean documents\n"
                      "> Generated: 2026-11-11 by fixture\n"
                      "> Census: 1 enumerated / 1 deep-read / 0 shallow / 0 unresolved\n"
                      "> Freshness: newest source 2026-11-11 · stale-after 90d · 0 claims tagged stale\n")
            if shape == "single":
                single_header = header.replace("by fixture\n", "by fixture · Mode: single-file\n")
                (out / "llms.txt").write_text(single_header +
                    "## Facts\n- Canonical context fixture-context [asserted]\n" + "x" * padding +
                    "\n## Sitemap\n- context.md — original fixture source\n" +
                    "\n## Resources\n### Other\n- (none) — no external resource was checked\n")
                if sibling:
                    (out / "llms-small.txt").write_text(header)
            else:
                for name in ["llms.txt", "llms-full.txt", "llms-small.txt", "llms-facts.txt"]:
                    (out / name).write_text(header + "- Canonical context fixture-context [asserted]\n")
                if sitemap:
                    (out / "llms-sitemap.txt").write_text(header +
                        "> Kind: store · Entries: 1\n\n## Files\n- context.md — original fixture source\n" +
                        "\n## Resources\n### Other\n- (none) — no external resource was checked\n")
            card = {"path": "context.md", "purpose": "source fixture", "read-status": "full"}
            if credential:
                card["purpose"] = "sk-" + "Q" * 32  # synthetic, nonfunctional token shape
            (out / "artifacts.json").write_text(json.dumps([card]))
            (out / "manifest.json").write_text(json.dumps({"census": {"enumerated": 1},
                "canonical_context_file": {"drive_id": "fixture-context", "modified": "2026-11-11", "in_folder": True}}))
            return subprocess.run([sys.executable, str(SOURCE / "selfcheck.py"), "Fixture Account",
                                   "--root", str(root)], capture_output=True, text=True)

    def test_clean_synthetic_pack_passes(self):
        result = self.check_pack()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_credential_in_json_sidecar_fails(self):
        result = self.check_pack(credential=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("credentials", result.stdout)

    def test_single_file_shape_passes_without_family_siblings(self):
        result = self.check_pack(shape="single", padding=2500)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_family_requires_current_sitemap(self):
        result = self.check_pack(sitemap=False)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("missing:llms-sitemap.txt", result.stdout)

    def test_single_file_rejects_family_siblings(self):
        result = self.check_pack(shape="single", sibling=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("single-siblings", result.stdout)


if __name__ == "__main__":
    unittest.main()
