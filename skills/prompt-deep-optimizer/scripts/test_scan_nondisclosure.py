"""The scan CLI reports static metadata, never synthetic matched values or input lines."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(os.environ.get('PDO_TOOL_PATH', str(Path(__file__).with_name('pdo_tools.py'))))
SAMPLES = [
    ('aws_access_key', 'AKIA' + 'Q' * 16),
    ('openai_key', 'sk-' + 'Q' * 24),
    ('anthropic_key', 'sk-ant-' + 'Q' * 24),
    ('github_token', 'ghp_' + 'Q' * 24),
    ('github_pat_finegrained', 'github_pat_' + 'Q' * 24),
    ('openai_project_key', 'sk-proj-' + 'Q' * 24),
    ('google_api_key', 'AIza' + 'Q' * 35),
    ('stripe_live_key', 'sk_live_' + 'Q' * 24),
    ('npm_token', 'npm_' + 'Q' * 36),
    ('huggingface_token', 'hf_' + 'Q' * 34),
    ('pypi_token', 'pypi-' + 'Q' * 32),
    ('gitlab_pat', 'glpat-' + 'Q' * 24),
    ('slack_token', 'xoxb-' + 'Q' * 12),
    ('jwt', 'eyJ' + 'Q' * 12 + '.' + 'R' * 12 + '.' + 'S' * 12),
    ('private_key_block', '-----BEGIN ' + 'PRIVATE KEY-----'),
    ('bearer_literal', 'Bearer ' + 'Q' * 24),
    ('password_assign', "password = '" + 'non-production-fixture' + "'"),
    ('email', 'fixture' + '@' + 'example.invalid'),
    ('ssn', '000' + '-00-' + '0000'),
    ('phone_us', '202' + '-555-' + '0100'),
]


class ScanNondisclosure(unittest.TestCase):
    def scan(self, payload, use_stdin):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'input.txt'
            path.write_text(payload)
            command = [sys.executable, str(TOOL), 'scan', '-' if use_stdin else str(path)]
            return subprocess.run(command, input=payload if use_stdin else None,
                                  capture_output=True, text=True, check=False)

    def metadata(self, result, payload, expected):
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, '')
        report = json.loads(result.stdout)
        self.assertEqual(set(report), {'findings', 'count', 'redaction_required', 'note', 'evidence'})
        self.assertEqual(report['findings'], expected)
        self.assertEqual(report['count'], len(expected))
        self.assertEqual(report['redaction_required'], bool(expected))
        self.assertEqual(report['evidence'], 'EXECUTED')
        for finding in report['findings']:
            self.assertEqual(set(finding), {'type', 'line'})
            self.assertIs(type(finding['line']), int)
        output = result.stdout + result.stderr
        for _, value in SAMPLES:
            self.assertNotIn(value, output)
        for line in payload.splitlines():
            if line.strip():
                self.assertNotIn(line, output)
        return report

    def test_file_all_detection_types_emit_only_type_line_and_counts(self):
        payload = '\n' + '\n'.join(f'fixture {n}: {value}' for n, (_, value) in enumerate(SAMPLES, 1)) + '\n'
        expected = [{'line': n + 1, 'type': kind} for n, (kind, _) in enumerate(SAMPLES, 1)]
        self.metadata(self.scan(payload, False), payload, expected)

    def test_stdin_all_detection_types_emit_only_type_line_and_counts(self):
        payload = '\n'.join(f'fixture {n}: {value}' for n, (_, value) in enumerate(SAMPLES, 1))
        expected = [{'line': n, 'type': kind} for n, (kind, _) in enumerate(SAMPLES, 1)]
        self.metadata(self.scan(payload, True), payload, expected)

    def test_multiple_matches_on_one_line_do_not_emit_the_input_line(self):
        payload = 'combined fixture: ' + SAMPLES[0][1] + ' and ' + SAMPLES[17][1]
        expected = [{'line': 1, 'type': 'aws_access_key'}, {'line': 1, 'type': 'email'}]
        for stdin in [False, True]:
            with self.subTest(stdin=stdin):
                self.metadata(self.scan(payload, stdin), payload, expected)

    def test_clean_input_keeps_empty_findings_and_existing_schema(self):
        payload = 'Summarize the attached architecture notes without making changes.\n'
        for stdin in [False, True]:
            with self.subTest(stdin=stdin):
                self.metadata(self.scan(payload, stdin), payload, [])


if __name__ == '__main__':
    unittest.main()
