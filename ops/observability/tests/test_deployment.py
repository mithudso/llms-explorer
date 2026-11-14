import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fleet_manage", ROOT / "manage.py")
manage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manage)


class DeploymentChecks(unittest.TestCase):
    def test_generation_is_identical_across_hash_seeds(self):
        digests = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "inventory.json").write_bytes(
                (ROOT / "inventory.json").read_bytes()
            )
            script = "import importlib.util,pathlib,sys; s=importlib.util.spec_from_file_location('g',sys.argv[1]); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); m.ROOT=pathlib.Path(sys.argv[2]); m.generate()"
            for seed in ["1", "2"]:
                subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        script,
                        str(ROOT / "generate.py"),
                        str(root),
                    ],
                    env={**os.environ, "PYTHONHASHSEED": seed},
                    check=True,
                )
                digests.append(
                    {
                        str(p.relative_to(root)): p.read_bytes()
                        for p in root.rglob("*")
                        if p.is_file()
                    }
                )
        self.assertEqual(digests[0], digests[1])

    def test_launchd_retries_async_bootout_and_preserves_unchanged_agents(self):
        loaded = False
        bootstrap_attempts = 0
        calls = []

        def runner(*args, **kwargs):
            nonlocal loaded, bootstrap_attempts
            calls.append(args)
            code = 0
            if args[1] == "print":
                code = 0 if loaded else 113
            elif args[1] == "bootstrap":
                bootstrap_attempts += 1
                code = 5 if bootstrap_attempts == 1 else 0
                loaded = code == 0
            elif args[1] == "bootout":
                loaded = False
            return subprocess.CompletedProcess(args, code)

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(manage.Path, "home", return_value=Path(tmp)),
            patch.object(manage, "RUNTIME", Path(tmp)),
            patch.object(manage, "run", side_effect=runner),
            patch.object(manage.time, "sleep"),
        ):
            manage.launch("com.llmsx.observability.fixture", ["/bin/fixture"])
            self.assertEqual(bootstrap_attempts, 2)
            self.assertTrue(loaded)
            calls.clear()
            manage.launch("com.llmsx.observability.fixture", ["/bin/fixture"])
            self.assertEqual([args[1] for args in calls], ["print"])

    def test_dashboard_health_thresholds_match_failure_meaning(self):
        spec = importlib.util.spec_from_file_location(
            "fleet_generate", ROOT / "generate.py"
        )
        generate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generate)
        with tempfile.TemporaryDirectory() as tmp:
            generate.ROOT = Path(tmp)
            (generate.ROOT / "inventory.json").write_bytes(
                (ROOT / "inventory.json").read_bytes()
            )
            generate.generate()
            panels = json.loads(
                (generate.ROOT / "grafana/dashboards/fleet.json").read_text()
            )["panels"]
        by_title = {p["title"]: p for p in panels}

        def color(title, value):
            result = None
            for step in by_title[title]["fieldConfig"]["defaults"]["thresholds"][
                "steps"
            ]:
                if step["value"] is None or value >= step["value"]:
                    result = step["color"]
            return result

        self.assertEqual(color("Firing alerts", 4), "red")
        self.assertEqual(color("Firing alerts", 0), "green")
        self.assertEqual(color("Public sites responding / 6", 2), "red")
        self.assertEqual(color("Public sites responding / 6", 6), "green")
        self.assertEqual(color("Monitoring scrape failures", 0), "green")


if __name__ == "__main__":
    unittest.main()
