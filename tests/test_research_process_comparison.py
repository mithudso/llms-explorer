"""Adversarial checks for process-comparison identity and fair scoring."""
import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('process_comparison', Path(__file__).resolve().parents[1] / 'scripts/research_process_comparison.py')
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)


class BoundComparisonTests(unittest.TestCase):
    def setUp(self):
        self.output = {'concepts': [{'id': 'c1', 'name': 'PASSIVE'}],
                       'claims': [{'id': 'f1', 'concept_id': 'c1', 'text': 'PASSIVE does not invoke the busy handler.'}]}
        self.judge = {'output_sha256': comparison.digest(self.output),
                      'claims': [{'id': 'f1', 'text': self.output['claims'][0]['text'], 'supported': True,
                                  'verdict': 'SUPPORTED', 'atomic': True, 'depth': 2, 'mechanism': False,
                                  'duplicate_of': None, 'gold_ids': []}],
                      'concepts': [{'id': 'c1', 'canonical_name': 'PASSIVE', 'meaningful': True, 'in_scope': True}]}

    def test_stale_hash_and_substituted_full_statement_fail(self):
        for field, value in [('output_sha256', 'stale'), ('text', 'PASSIVE always finishes.')]:
            judge = copy.deepcopy(self.judge)
            (judge if field == 'output_sha256' else judge['claims'][0])[field] = value
            with self.assertRaises(ValueError):
                comparison.validate_judgment(self.output, judge)

    def test_missing_extra_duplicate_and_ill_typed_judgments_fail(self):
        mutations = [lambda j: j['claims'].clear(),
                     lambda j: j['claims'].append(copy.deepcopy(j['claims'][0])),
                     lambda j: j['concepts'].append({'id': 'unknown'}),
                     lambda j: j['claims'][0].update(depth=True),
                     lambda j: j['claims'][0].update(supported='true'),
                     lambda j: j['claims'][0].update(verdict='CONTRADICTED'),
                     lambda j: j['claims'][0].update(duplicate_of='unknown')]
        for mutate in mutations:
            judge = copy.deepcopy(self.judge)
            mutate(judge)
            with self.assertRaises(ValueError):
                comparison.validate_judgment(self.output, judge)

    def test_all_verdicts_preserve_dissent(self):
        for verdict in ('SUPPORTED', 'NOT-IN-SOURCE', 'CONTRADICTED', 'UNVERIFIED'):
            self.judge['claims'][0].update(verdict=verdict, supported=verdict == 'SUPPORTED')
            comparison.validate_judgment(self.output, self.judge)

    def test_duplicate_generation_ids_and_orphan_claims_fail(self):
        for mutate in (lambda o: o['claims'].append(copy.deepcopy(o['claims'][0])),
                       lambda o: o['claims'][0].update(concept_id='unknown')):
            output = copy.deepcopy(self.output)
            mutate(output)
            with self.assertRaises(ValueError):
                comparison.validate_generation(output)

    def test_cached_call_rejects_changed_prompt_model_or_effort(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            record = {'is_error': False, 'output': self.output,
                      'input_sha256': comparison.digest({'prompt': 'original', 'model': 'gpt-6-luna', 'effort': 'max'}),
                      'output_sha256': comparison.digest(self.output)}
            comparison.write(folder / 'run.json', record)
            for prompt, model, effort in [('new', 'gpt-6-luna', 'max'), ('original', 'gpt-6-astra', 'max'), ('original', 'gpt-6-luna', 'medium')]:
                with self.assertRaisesRegex(ValueError, 'input mismatch'):
                    comparison.stage(folder, prompt, model, effort, 10, comparison.validate_generation)
            with patch.object(comparison, 'call', side_effect=AssertionError('unexpected paid call')):
                comparison.stage(folder, 'original', 'gpt-6-luna', 'max', 10, comparison.validate_generation)
            record['output']['claims'][0]['text'] = 'Changed after scoring.'
            comparison.write(folder / 'run.json', record)
            with self.assertRaisesRegex(ValueError, 'output mismatch'):
                comparison.stage(folder, 'original', 'gpt-6-luna', 'max', 10, comparison.validate_generation)

    def test_fresh_judges_are_blind_to_arm_model_effort_and_runtime(self):
        prompt = comparison.judge_prompt(self.output, 'dr', {'sources': [], 'gold': {}})
        for secret in ('gpt-6-luna', 'gpt-6.1-sol', 'gpt-6-astra', 'updated', 'seconds'):
            self.assertNotIn(secret, prompt)
        self.assertIn(comparison.digest(self.output), prompt)

    def test_resuming_a_live_batch_cannot_start_duplicate_calls(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            def already_running(*args):
                with patch.object(comparison, 'run_locked', side_effect=AssertionError('duplicate model calls')):
                    self.assertEqual(comparison.run(out, 4, 900), 1)
                return 0
            with patch.object(comparison, 'run_locked', side_effect=already_running):
                self.assertEqual(comparison.run(out, 4, 900), 0)

    def test_recovery_selects_first_valid_attempt_instead_of_best_score(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for number, error, score in [('001', True, 100), ('002', False, 20), ('003', False, 100)]:
                comparison.write(folder / 'attempts' / number / 'run.json', {
                    'is_error': error, 'input_sha256': 'same', 'output_sha256': comparison.digest(self.output),
                    'output': self.output, 'score': score})
            result, number = comparison.earliest_valid(folder, 'same', comparison.validate_generation)
            self.assertEqual((number, result['score']), ('002', 20))


if __name__ == '__main__':
    unittest.main()
