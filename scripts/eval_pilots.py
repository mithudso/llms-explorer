#!/usr/bin/env python3
"""Bounded real-code behavioral pilots; never call an embedding/model service by default."""
from __future__ import annotations
import argparse
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile

REPO = Path(__file__).resolve().parents[1]
ROOT = Path.home() / '.codex/evals/pilots'
RUNTIME = Path.home() / '.codex/evals/runtime'
VERSION = '1.0.0'
CASES = {
    'missing-category': {'input': [{'concept': 'Replication', 'skillId': 'replication', 'parentConcept': 'Databases', 'childConcepts': []}], 'expected': {'concepts': ['Databases', 'Replication'], 'edges': [['Databases', 'Replication']]}},
    'slug-collision': {'input': [{'concept': 'Vector Search', 'skillId': 'weak', 'sourcesCount': 1}, {'concept': 'Vector-Search', 'skillId': 'strong', 'sourcesCount': 7}], 'expected': {'concepts': ['Vector-Search'], 'edges': []}},
}

def actual(case):
    spec = importlib.util.spec_from_file_location('pilot_merge', REPO / 'scripts/merge_concept_trees.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
        path = Path(tmp) / 'tree.json'
        path.write_text(json.dumps(CASES[case]['input']))
        nodes = module.load_mdb_nodes(path)
    return {'concepts': sorted(n['concept'] for n in nodes), 'edges': sorted([n['parentConcept'], n['concept']] for n in nodes if n.get('parentConcept'))}

def call_api(prompt, options, context):
    """Promptfoo Python provider executes repository code, not a simulated LLM."""
    return {'output': json.dumps(actual(prompt.strip()), sort_keys=True)}

def local(output):
    os.environ.setdefault('DEEPEVAL_TELEMETRY_OPT_OUT', 'YES')
    os.environ.setdefault('CONFIDENT_AI_TELEMETRY_OPT_OUT', 'YES')
    from deepeval.metrics import BaseMetric
    from deepeval.test_case import LLMTestCase
    class ConceptGraphMetric(BaseMetric):
        threshold = 1.0
        async_mode = False
        @property
        def __name__(self):
            return 'Exact concept graph preservation'
        def measure(self, test_case):
            self.score = float(json.loads(test_case.actual_output) == json.loads(test_case.expected_output))
            self.success = self.score == 1
            self.reason = 'Exact graph matches independent expectation' if self.success else 'Concept or relationship mismatch'
            return self.score
        async def a_measure(self, test_case):
            return self.measure(test_case)
        def is_successful(self):
            return self.success
    results = []
    tests = []
    for name, case in CASES.items():
        expected = json.dumps(case['expected'], sort_keys=True)
        observed = json.dumps(actual(name), sort_keys=True)
        metric = ConceptGraphMetric()
        score = metric.measure(LLMTestCase(input=name, actual_output=observed, expected_output=expected))
        results.append({'case': name, 'score': score, 'actual': json.loads(observed), 'expected': case['expected']})
        tests.append({'vars': {'case': name}, 'assert': [{'type': 'equals', 'value': expected}]})
    (output / 'deepeval.json').write_text(json.dumps({'version': VERSION, 'kind': 'deterministic-real-code', 'results': results}, indent=2))
    config = {'description': 'Real concept merge code: missing category and slug collision', 'prompts': ['{{case}}'], 'providers': [f'python:{Path(__file__).resolve()}:call_api'], 'tests': tests}
    config_path = output / 'promptfoo.json'
    config_path.write_text(json.dumps(config, indent=2))
    env = dict(os.environ, PROMPTFOO_PYTHON=str(RUNTIME / 'venv/bin/python'), PROMPTFOO_DISABLE_TELEMETRY='1', PROMPTFOO_DISABLE_UPDATE='1')
    cmd = [str(RUNTIME / 'node/node_modules/.bin/promptfoo'), 'eval', '-c', str(config_path), '-o', str(output / 'promptfoo-results.json'), '--no-cache', '--max-concurrency', '1']
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)
    (output / 'promptfoo.log').write_text(result.stdout + result.stderr)
    return {'deepeval_passed': sum(r['score'] == 1 for r in results), 'deepeval_total': len(results), 'promptfoo_exit_code': result.returncode}

def benchmark(output):
    """One subscription-backed skill execution, with a synthetic fixture only."""
    plugin = Path.home() / '.codex/plugins/cache/openai-curated-remote/plugin-eval/0.1.2'
    target = output / 'caveman'
    target.mkdir(exist_ok=True)
    shutil.copy2(Path.home() / '.agents/skills/caveman/SKILL.md', target / 'SKILL.md')
    source = output / 'synthetic-workspace'
    source.mkdir(exist_ok=True)
    (source / 'input.txt').write_text('The worker retries HTTP 429 responses after 30 seconds. It never retries HTTP 401 responses.\n')
    verifier = "from pathlib import Path; s=Path('answer.txt').read_text(); assert all(x in s for x in ['429','30','401']); assert 'never' in s.lower(); assert len(s.split()) <= 20; assert Path('input.txt').read_text() == " + repr((source / 'input.txt').read_text())
    # The verifier lives outside the model workspace to prevent accidental edits.
    verifier_path = output / 'verify-caveman.py'
    verifier_path.write_text(verifier + '\n')
    config = {'kind': 'plugin-eval-benchmark', 'schemaVersion': 2, 'version': 2,
        'runner': {'type': 'codex-cli', 'model': 'gpt-6-astra', 'sandbox': 'workspace-write', 'approvalPolicy': 'never', 'extraArgs': ['-c', 'model_reasoning_effort="low"']},
        'workspace': {'sourcePath': str(source), 'setupMode': 'copy', 'preserve': 'never'},
        'targetProvisioning': {'mode': 'isolated-skill-home'},
        'verifiers': {'commands': [f'{RUNTIME / "venv/bin/python"} {verifier_path}']},
        'scenarios': [{'id': 'preserve-http-semantics', 'title': 'Compress without losing retry conditions',
          'purpose': 'Verify exact codes, delay, negative condition, and bounded verbosity on synthetic text.',
          'userInput': 'Use $caveman to compress input.txt into answer.txt in at most 20 words. Keep HTTP codes, delay, and the word never. Do not alter input.txt. Use no network or external services.',
          'successChecklist': ['answer.txt preserves 429, 401, 30, and never', 'No more than 20 words', 'Input unchanged']}]}
    config_path = output / 'benchmark.json'
    config_path.write_text(json.dumps(config, indent=2))
    with tempfile.TemporaryDirectory(prefix='eval-auth-') as temp:
        auth_home = Path(temp)
        auth = Path.home() / '.codex/auth.json'
        if auth.exists():
            shutil.copy2(auth, auth_home / 'auth.json')
            (auth_home / 'auth.json').chmod(0o600)
        (auth_home / 'config.toml').write_text('model = "gpt-6-astra"\n')
        run_temp = auth_home / 'runs'
        run_temp.mkdir()
        env = dict(os.environ, PLUGIN_EVAL_CODEX_HOME_SOURCE=temp, TMPDIR=str(run_temp))
        command = ['node', str(plugin / 'scripts/plugin-eval.js'), 'benchmark', str(target), '--config', str(config_path), '--output', str(output / 'benchmark-result.json')]
        with (output / 'benchmark.log').open('w') as log:
            process = subprocess.Popen(command, env=env, stdout=log, stderr=log, start_new_session=True)
            try:
                code = process.wait(timeout=240)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=10)
                code = 124
    report_path = output / 'benchmark-result.json'
    summary = json.loads(report_path.read_text()).get('summary', {}) if code == 0 and report_path.exists() else {}
    passed = code == 0 and summary.get('completedScenarios') == 1 and summary.get('verifierPassCount') == 1 and summary.get('failedScenarios') == 0
    return {'benchmark_exit_code': code if code else (0 if passed else 1), 'benchmark_result': str(report_path), 'benchmark_summary': summary}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark', action='store_true', help='Also run one live Codex skill scenario (may consume subscription usage)')
    parser.add_argument('--output', type=Path, default=ROOT)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True, mode=0o700)
    result = local(args.output)
    if args.benchmark:
        result.update(benchmark(args.output))
    (args.output / 'summary.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return int(result['deepeval_passed'] != result['deepeval_total'] or result['promptfoo_exit_code'] != 0 or result.get('benchmark_exit_code', 0) != 0)

if __name__ == '__main__':
    raise SystemExit(main())
