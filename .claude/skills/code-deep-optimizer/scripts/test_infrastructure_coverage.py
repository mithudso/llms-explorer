"""Supported infrastructure surfaces stay in the per-file review plan."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

HELPER = Path(os.environ.get('SKO_HELPER_PATH', str(Path(__file__).with_name('cdo_ledger.py'))))


class InfrastructureCoverage(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        spec = importlib.util.spec_from_file_location('cdo_infra_subject', HELPER)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.supported = {
            'main.py': 'print(1)\n', 'Dockerfile': 'FROM scratch\n',
            'Dockerfile.release': 'FROM scratch\n', 'docker-compose.yml': 'services: {}\n',
            'deployment.yaml': 'apiVersion: v1\nkind: Service\n',
            'network.tf': 'resource "sample" "network" {}\n',
            '.github/workflows/check.yml': 'jobs: {}\n', '.gitlab-ci.yml': 'stages: [test]\n',
            'Jenkinsfile': 'pipeline {}\n', 'manifest.json': '{"manifest_version": 3}\n',
        }
        for name, text in self.supported.items():
            path = self.root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)

    def plan(self, *extra):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = self.module.main(['plan', '--repo', str(self.root), '--json', *extra])
        self.assertEqual(code, 0)
        return json.loads(output.getvalue())

    def test_non_git_walk_includes_every_documented_surface(self):
        self.assertEqual(set(self.module.enumerate_sources(self.root)), set(self.supported))

    def test_git_plan_includes_supported_files_and_keeps_ignores(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True, capture_output=True)
        (self.root/'.gitignore').write_text('ignored.yaml\n')
        for name in ['ignored.yaml', 'vendor/network.tf', '.cdo/generated.yaml', 'assets/data.bin']:
            path = self.root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('apiVersion: v1\nkind: Service\n')
        self.assertEqual({row['path'] for row in self.plan()['review']}, set(self.supported))

    def test_unchanged_infrastructure_can_be_recorded_then_replanned(self):
        with contextlib.redirect_stdout(io.StringIO()):
            code = self.module.main(['record', '--repo', str(self.root), '--passes',
                                     ','.join(self.module.PASSES), '--verdict', 'CLEAN', 'network.tf'])
        self.assertEqual(code, 0)
        plan = self.plan()
        self.assertEqual(plan['unchanged_skipped'], 1)
        self.assertNotIn('network.tf', {row['path'] for row in plan['review']})
        (self.root/'network.tf').write_text('resource "sample" "changed" {}\n')
        self.assertIn({'path': 'network.tf', 'reason': 'changed'}, self.plan()['review'])


if __name__ == '__main__':
    unittest.main()
