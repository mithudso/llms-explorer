import importlib.util
import json
from pathlib import Path
import unittest
from unittest import mock
import copy
import test_experimental_27b as baseline

BASE = Path('/Users/mitch/.cache/claude-egpu/experiments')
spec = importlib.util.spec_from_file_location('f32_starter', BASE / 'qwen36-27b-iq2-startup-preparation-v106/start_once.py')
starter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(starter)


class F32ColdDelta(unittest.TestCase):
    def test_scalar_precision_environment_is_exact(self):
        expected = {'GGML_CUDA_CUBLAS_COMPUTE_TYPE': 'f32', 'TINYCUBLAS_TC': '0'}
        self.assertEqual(starter.diagnostic_environment({'diagnostic_environment': expected}), expected)
        for value in (None, {}, {**expected, 'EXTRA': 'x'}, {**expected, 'TINYCUBLAS_TC': 0}, {**expected, 'TINYCUBLAS_TC': '1'}, {**expected, 'GGML_CUDA_CUBLAS_COMPUTE_TYPE': 'f16'}):
            with self.subTest(value=value), self.assertRaises(starter.Refusal):
                starter.diagnostic_environment({'diagnostic_environment': value})

    def test_inherited_precision_overrides_are_rejected(self):
        for key in ('TINYCUBLAS_TC', 'GGML_CUDA_CUBLAS_COMPUTE_TYPE'):
            with self.subTest(key=key), self.assertRaises(starter.Refusal):
                starter.refuse_overrides({key: '0'})

    def test_both_consumed_candidate_boots_rejected(self):
        for boot in ('1791115301:4730', '1791136050:203826'):
            proofs, bindings, plan, now = baseline.BoundaryControls().fixture()
            proofs['cold_admission']['boot_id'] = boot
            with self.subTest(boot=boot), self.assertRaisesRegex(baseline.e.Refusal, 'Old/malformed boot'):
                baseline.e.experimental_admission(proofs, bindings, plan, now)

    def test_consumed_boot_numeric_alias_cannot_admit_cold_trial(self):
        for boot in ('01791136050:203826', '1791136050:0203826', '', 'x:y', '1:01'):
            proofs, bindings, plan, now = baseline.BoundaryControls().fixture()
            proofs['cold_admission']['boot_id'] = boot
            proofs['root_activation']['boot_id'] = boot
            with self.subTest(boot=boot), self.assertRaisesRegex(baseline.e.Refusal, 'Old/malformed boot'):
                baseline.e.experimental_admission(proofs, bindings, plan, now)

    def test_first_trial_owner_boot_is_rejected_before_remaining_admission(self):
        for boot in ('', 'x:y', '01:2', '1:02', '1791136050:203826'):
            owner = {'native_pid': 3, 'transport_pid': 4, 'native_uid': 501, 'transport_uid': 501,
                     'binary_sha256': 'd' * 64, 'model_sha256': baseline.e.MODEL_SHA,
                     'boot_id': boot, 'native_birth': 'fixture', 'transport_birth': 'fixture'}
            outcomes = {'schema': 'qwen35-27b-first-trial-outcomes-v1',
                        'identity': baseline.e.identity('d' * 64), 'actual': True, 'owner': owner}
            with self.subTest(boot=boot), self.assertRaisesRegex(baseline.e.Refusal, 'Old/malformed owner boot'):
                baseline.e.first_trial_quality_admission(outcomes, owner, {}, {})

    def test_runtime_library_aliases_and_hashes_are_bound(self):
        cfg = json.loads((BASE / 'qwen36-27b-iq2-static-inputs-v106/ROOT-CONFIG.json').read_text())
        starter.verify_runtime_library_aliases(cfg)
        with mock.patch.object(starter.Path, 'resolve', return_value=Path('/different/version')), mock.patch.object(starter, 'read_bound') as read:
            with self.assertRaisesRegex(starter.Refusal, 'alias retargeted'):
                starter.verify_runtime_library_aliases(cfg)
            read.assert_not_called()
        broken = copy.deepcopy(cfg)
        alias = next(iter(broken['runtime_library_aliases']))
        broken['runtime_library_aliases'][alias]['sha256'] = '0' * 64
        with self.assertRaisesRegex(starter.Refusal, 'Bound file SHA differs'):
            starter.verify_runtime_library_aliases(broken)

    def test_runtime_library_declaration_rejects_missing_extra_path_or_digest(self):
        cfg = json.loads((BASE / 'qwen36-27b-iq2-static-inputs-v106/ROOT-CONFIG.json').read_text())
        for change in ('missing', 'extra', 'path', 'nullhash', 'boolhash'):
            broken = copy.deepcopy(cfg)
            alias = next(iter(broken['runtime_library_aliases']))
            if change == 'missing':
                broken.pop('runtime_library_aliases')
            elif change == 'extra':
                broken['runtime_library_aliases']['/unexpected'] = {'path': '/extra', 'sha256': 'a' * 64}
            elif change == 'path':
                broken['runtime_library_aliases'][alias]['path'] = '/different/version'
            else:
                broken['runtime_library_aliases'][alias]['sha256'] = None if change == 'nullhash' else True
            with self.subTest(change=change), self.assertRaises(starter.Refusal):
                starter.verify_runtime_library_aliases(broken)

    def test_actual_prefixed_log_preserves_original_guard(self):
        raw = (BASE / 'qwen36-27b-iq2-log-framing-v100/startup-native.log').read_text()
        parsed = baseline.e.validate_preload_guard_records(raw)
        self.assertEqual(parsed['pre_load_guard']['required_pool_bytes'], 16667408384)
        self.assertTrue(parsed['successful_pre_post_association'])
        self.assertEqual([x['line'] for x in parsed['framing']['normalized_records']], [184, 222])
        self.assertEqual(parsed['framing']['event_records_removed'], 0)
        self.assertFalse(parsed['graph_peak_or_fit_verified'])

    def test_new_receiver_remains_unconsumed_with_original_launch_controls(self):
        static = BASE / 'qwen36-27b-iq2-static-inputs-v106'
        abi = json.loads((static / 'BUILD-ABI.json').read_text())
        self.assertEqual(abi['identity'], baseline.e.identity(abi['identity']['binary_sha256']))
        self.assertEqual(abi['binary_path'], baseline.e.BINARY)
        self.assertEqual(abi['preload_envelope_bytes'], 16667408384)
        self.assertEqual(abi['preused_driver_allowance_bytes'], 2147483648)
        self.assertFalse((BASE / 'qwen36-27b-iq2-cold-root-operation-v106/OPERATION-CONSUMED.json').exists())
        self.assertFalse((BASE / 'qwen36-27b-iq2-cold-runtime-v106').exists())


if __name__ == '__main__':
    unittest.main()
