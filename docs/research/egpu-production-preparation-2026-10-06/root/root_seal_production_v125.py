"""Issue accepted source-only authorities. Never invoke native or GPU operations."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import stat
import sys
import types
import ast

EXP = Path('/Users/mitch/.cache/claude-egpu/experiments')
OUT = EXP / 'qwen36-27b-iq2-cold-capture-execution-20261006'
PREP_ROOT = EXP / 'qwen36-27b-downstream-preparation-v125'
STATIC = PREP_ROOT / 'production/static-inputs'
REQUEST = PREP_ROOT / 'production/capture-response-preparation'
AUDIT = EXP / 'qwen36-27b-iq2-cold-capture-independent-review-20261006/TASK620-PRODUCTION-SOURCE-REVIEW.json'


def held(path, digest):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        assert stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
        assert stat.S_IMODE(before.st_mode) in (0o600, 0o700)
        assert before.st_nlink == 1 and before.st_size <= 8 * 1024 * 1024
        with os.fdopen(os.dup(fd), 'rb') as stream:
            data = stream.read()
        after = os.fstat(fd)
        keys = ('st_dev', 'st_ino', 'st_uid', 'st_gid', 'st_mode', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
        assert all(getattr(before, k) == getattr(after, k) for k in keys)
        assert len(data) == before.st_size and hashlib.sha256(data).hexdigest() == digest
        return data
    finally:
        os.close(fd)


def module(path, digest, name):
    data = held(path, digest)
    result = types.ModuleType(name)
    result.__file__ = str(path)
    sys.modules[name] = result
    exec(compile(data, str(path), 'exec'), result.__dict__)
    return result


def exclusive(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    digest = hashlib.sha256(data).hexdigest()
    assert held(path, digest) == data
    return {'path': str(path), 'sha256': digest, 'bytes': len(data), 'mode': '0600', 'uid': os.getuid()}


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def main():
    audit_sha = '04c06f6622fd98153c31ed7bb67a97a8142cfb7fcd3034840cc3266bf4e87a08'
    held(AUDIT, audit_sha)
    freeze = json.loads(held(PREP_ROOT / 'PRODUCTION-FREEZE.json', 'd90c9a31249a798dcde88f9bb4297185644873bfdda4619ec2faba2adda28f77'))
    assert len(freeze['frozen_sources']) == 20
    for path, digest in freeze['frozen_sources'].items():
        held(Path(path), digest)
    source_sha = '66cc053cf6d08cd3a1f331d13198accd5cf185697fcacb0d7eff1109c8fd1e16'
    request_sha = 'd70b063c0a9e2db5347143f9945bdfb9b438e3250ccc5e5043ca4bce990e209c'
    final = json.loads(held(STATIC / 'REVIEW-DRAFT.json', source_sha))
    preparation = json.loads(held(REQUEST / 'PREPARATION-DRAFT.json', request_sha))
    assert not (STATIC / 'INDEPENDENT-REVIEW.json').exists()
    assert not (REQUEST / 'PREPARATION.json').exists()
    final.update(passed=True, seal_pending=False, independent_static_review=True,
                 independent_review_pending=False, issuer='/root',
                 sealed_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                 independent_audit={'path': str(AUDIT), 'sha256': audit_sha},
                 source_draft={'path': str(STATIC / 'REVIEW-DRAFT.json'), 'sha256': source_sha})
    final['scope'] = 'Source-only fresh capture-disabled cold startup and exactly two original native numerical requests. Fresh physical recovery and actual gates remain pending.'
    final['delta'] = 'Root source-only final production authority after independent exact consuming-prefix review.'
    for key in ('full_qualification', 'candidate_numerics_verified', 'coding_verified',
                'actual_peak_verified', 'standard_research_verified', 'cold_admission_issued', 'physical_launch_ready'):
        assert final[key] is False
    assert final['source_pin_count'] == len(final['source_pins']) == 4752
    assert len(final['external_source_bindings']) == 1748
    assert final['excluded_consumed_boot'] == '1791277640:498901'
    renderer_path = PREP_ROOT / 'production/renderer-preparation/experimental_27b.py'
    cold_path = PREP_ROOT / 'production/cold-root-operation/run_actual_cold_once.py'
    renderer = module(renderer_path, final['source_pins'][str(renderer_path)], 'root_production_v125_renderer')
    cold = module(cold_path, final['source_pins'][str(cold_path)], 'root_production_v125_cold')
    renderer.final_review(final)
    cold.minimal_final_review(final)
    renderer.same_identity(final, 'c1fb382b5557f3dabdb76241f9ee2f9167e87eac208878f23116a34cbf6d19d9')
    abi_path = STATIC / 'BUILD-ABI.json'
    abi = renderer.parse_json(held(abi_path, final['source_pins'][str(abi_path)]))
    renderer.bind_candidate_build(abi, final, {'build_abi': {'path': str(abi_path), 'sha256': final['source_pins'][str(abi_path)]}})
    static_data = encoded(final)
    static_sha = hashlib.sha256(static_data).hexdigest()
    preparation.update(version='1.0.1', source_review_sha256=static_sha, source_review_sha256_pending=False, seal_pending=False, independent_review_pending=False)
    assert preparation['maximum_GPU_requests'] == 2 and preparation['automatic_retry'] is False
    assert preparation['model_requests'] == preparation['GPU_initializations'] == 0
    assert preparation['full_qualification'] is False
    assert preparation['CPU_capture_manifest'] == final['current_CPU_reference']
    for path, digest in preparation['pins'].items():
        assert final['source_pins'][path] == digest
        held(Path(path), digest)
    for alias in ('/opt/homebrew/opt/openssl@3/lib/libssl.3.dylib', '/opt/homebrew/opt/openssl@3/lib/libcrypto.3.dylib'):
        assert final['external_source_bindings'][alias]['sha256'] == final['source_pins'][alias]
    assert final['production_mode']['key_absent_required'] is True
    assert final['production_mode']['production_mode_numerical_acceptance'] is False
    assert preparation['capture_enabled'] is False
    assert preparation['production_mode_numerical_acceptance'] is False
    static_receipt = exclusive(STATIC / 'INDEPENDENT-REVIEW.json', static_data)
    request_receipt = exclusive(REQUEST / 'PREPARATION.json', encoded(preparation))
    guard_path = REQUEST / 'guard_v125.py'
    guard = module(guard_path, preparation['pins'][str(guard_path)], 'root_production_v125_guard')
    tree = ast.parse(held(guard_path, preparation['pins'][str(guard_path)]))
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'verify_admission')
    function.body = function.body[:3] + [ast.Return(value=ast.Name(id='prep', ctx=ast.Load()))]
    prefix = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    scope = dict(guard.__dict__)
    exec(compile(prefix, str(guard_path), 'exec'), scope)
    assert scope['verify_admission'](request_receipt['sha256']) == preparation
    receipt = {'version': '1.0.0', 'delta': 'Exclusive source-only production v125 root seals and exact three-statement consuming-prefix checks. No physical or quality acceptance.',
               'at': dt.datetime.now(dt.timezone.utc).isoformat(), 'static': static_receipt, 'request': request_receipt,
               'pure_final_fixture_passed': True, 'source_pins': 4752, 'external_bindings': 1748,
               'native_executable_invocations': 0, 'GPU_actions': 0, 'physical_confirmation_pending': True,
               'independent_final_readback_pending': True, 'full_qualification': False}
    exclusive(OUT / 'PRODUCTION-V125-ROOT-SEAL-RECEIPT.json', encoded(receipt))
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
