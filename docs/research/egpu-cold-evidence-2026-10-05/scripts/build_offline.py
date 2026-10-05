#!/usr/bin/env python3
"""v1.0.2: bind declared offline source/header/link/tool inputs; never run server."""
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import time

ROOT = Path(__file__).resolve().parent
BASE = Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-preload-guard-build-v100')
MACUDA = Path('/Users/mitch/dev/macuda')
SOURCE = MACUDA / 'llama.cpp/ggml/src/ggml-cuda/mmq.cu'
ARCHIVE = MACUDA / 'cuda-shim/build/libggml-cuda.sm_120a.a'
HEADER = Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-renderer-preparation-v105/expected-inventory.json')
SDK = '/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk'
EXPECTED_HEADER_SHA = '7d82bc33dfbcbcfeb9796525640aa73d108ccf34a7b251561f57915db41eea19'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda: f.read(4 * 1024**2), b''):
            h.update(data)
    return h.hexdigest()


def write(name, value):
    raw = value if isinstance(value, bytes) else (json.dumps(value, indent=2, allow_nan=False) + '\n').encode()
    fd = os.open(ROOT / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)


def run(name, argv):
    command = ['/usr/bin/sandbox-exec', '-f', str(ROOT / 'deny-live.sb'), *argv]
    write(name + '-COMMAND.json', {'argv': command, 'GPU_initializations': 0, 'server_execution': False})
    env = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'TMPDIR': str(ROOT / 'tmp') + '/', 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1'}
    started = time.monotonic()
    with (ROOT / (name + '.stdout')).open('xb') as out, (ROOT / (name + '.stderr')).open('xb') as err:
        try:
            p = subprocess.run(command, cwd=ROOT, env=env, stdout=out, stderr=err, timeout=120)
        except (subprocess.TimeoutExpired, OSError) as error:
            write(name + '-RESULT.json', {'exit_code': None, 'seconds': time.monotonic() - started, 'exception_type': type(error).__name__, 'error': str(error), 'GPU_initializations': 0, 'CPU_build_child_only': True})
            raise
    write(name + '-RESULT.json', {'exit_code': p.returncode, 'seconds': time.monotonic() - started, 'GPU_initializations': 0})
    require(p.returncode == 0, name + ' failed; inspect saved stderr')


def bind_pin(pins, path, digest=None):
    require(path.is_absolute() and path.is_file(), 'Required input missing: ' + str(path))
    actual = sha(path)
    require(digest is None or actual == digest, 'Bound input differs: ' + str(path))
    require(str(path) not in pins or pins[str(path)] == actual, 'Conflicting input: ' + str(path))
    pins[str(path)] = actual


def reconcile_historical(pins, nested, allowed):
    require(set(allowed) <= set(nested), 'Historical exception not in manifest')
    report = []
    for value, expected in nested.items():
        path = Path(value)
        if value in allowed:
            exists = path.is_file()
            actual = sha(path) if exists else None
            require(actual != expected, 'Listed historical exception has no drift: ' + value)
            report.append({'path': value, 'historical_sha256': expected,
                           'current_sha256': actual, 'current_resolved_path': str(path.resolve()),
                           'exists': exists, 'included_in_new_build': False})
        else:
            bind_pin(pins, path, expected)
    return report


def link_arguments(inputs):
    original = json.loads((BASE / 'LINK-COMMAND.json').read_bytes())['arguments'][3:]
    overrides = inputs['link_overrides']
    expected = {'/opt/homebrew/lib/libssl.dylib': '/opt/homebrew/Cellar/openssl@3/3.6.5/lib/libssl.3.dylib',
                '/opt/homebrew/lib/libcrypto.dylib': '/opt/homebrew/Cellar/openssl@3/3.6.5/lib/libcrypto.3.dylib'}
    require(overrides == expected, 'Explicit OpenSSL3 link operands differ')
    require(all(original.count(alias) == 1 for alias in overrides), 'Original OpenSSL aliases differ')
    return [overrides.get(value, value) for value in original]


def capture_closure(inputs, compiled_source):
    """Reconcile historical drift and bind every declared current build input."""
    pins = dict(inputs['pins'])
    nested = json.loads((BASE / 'SOURCE-PINS.json').read_bytes())
    expected_drift = {'/opt/homebrew/Cellar/openssl@3/3.6.4/lib/libssl.3.dylib',
                      '/opt/homebrew/Cellar/openssl@3/3.6.4/lib/libcrypto.3.dylib',
                      '/opt/homebrew/lib/libssl.dylib', '/opt/homebrew/lib/libcrypto.dylib'}
    require(set(inputs['historical_drift_paths']) == expected_drift, 'Historical drift exceptions differ')
    drift = reconcile_historical(pins, nested, expected_drift)
    link = link_arguments(inputs)
    values = [*inputs['compile_dependency_paths'], *link,
              '/opt/homebrew/opt/llvm/bin/clang++', '/opt/homebrew/opt/llvm/bin/llvm-ar',
              '/usr/bin/c++', '/usr/bin/ld', '/usr/bin/sandbox-exec', '/usr/bin/otool', '/usr/bin/nm',
              '/Library/Developer/CommandLineTools/usr/bin/clang',
              '/Library/Developer/CommandLineTools/usr/bin/ld',
              str(HEADER), str(ROOT / 'deny-live.sb'), str(ROOT / 'build_offline.py'),
              str(ROOT / 'INPUTS.json')]
    skipped_output = str(BASE / 'llama-server-27b-preload-guard')
    for value in values:
        path = Path(value)
        if not path.is_absolute() or value == skipped_output or value == SDK:
            continue
        bind_pin(pins, path)
    require(sha(ROOT / 'mmq.cu') == hashlib.sha256(compiled_source).hexdigest(), 'Patched source differs')
    for framework in ('Accelerate', 'CoreFoundation', 'Security'):
        path = Path(SDK) / 'System/Library/Frameworks' / (framework + '.framework') / (framework + '.tbd')
        bind_pin(pins, path)
    for lib in ('libSystem.tbd', 'libc++.tbd'):
        bind_pin(pins, Path(SDK) / 'usr/lib' / lib)
    identities = {p: identity(Path(p)) for p in pins}
    return pins, identities, drift


def identity(path):
    item = path.stat()
    return [item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns, item.st_ctime_ns]


def verify_closure(pins, identities):
    for p, digest in pins.items():
        require(identity(Path(p)) == identities[p] and sha(Path(p)) == digest, 'Build closure changed: ' + p)


def verify_archive(original, replacement):
    ar = '/opt/homebrew/opt/llvm/bin/llvm-ar'
    old = subprocess.check_output([ar, 't', str(original)], text=True).splitlines()
    new = subprocess.check_output([ar, 't', str(replacement)], text=True).splitlines()
    require(old == new and len(old) == len(set(old)) and old.count('mmq.o') == 1, 'Archive member order/count/duplicates differ')
    hashes = {}
    for member in old:
        a = subprocess.check_output([ar, 'p', str(original), member])
        b = subprocess.check_output([ar, 'p', str(replacement), member])
        if member == 'mmq.o':
            require(b == (ROOT / 'mmq.o').read_bytes(), 'Replacement dispatcher member differs')
        else:
            require(a == b, 'Original device/host archive member changed: ' + member)
        hashes[member] = hashlib.sha256(b).hexdigest()
    return {'member_count_excluding_regenerated_archive_symbol_table': len(old), 'one_dispatcher_replacement': True, 'all_other_members_unchanged': True, 'member_hashes': hashes}


def main():
    os.umask(0o077)
    require(not (ROOT / 'CONSUMED.json').exists(), 'Offline build already consumed')
    inputs = json.loads((ROOT / 'INPUTS.json').read_bytes())
    for path, digest in inputs['pins'].items():
        require(sha(Path(path)) == digest, 'Bound build input differs: ' + path)
    require(sha(HEADER) == EXPECTED_HEADER_SHA, 'Model inventory differs')
    model = json.loads(HEADER.read_bytes())
    targets = [t for t in model['tensors'] if t['type_id'] in (10, 12, 16) and t['name'] != 'token_embd.weight' and not t['name'].startswith('blk.64.')]
    output = next(t for t in model['tensors'] if t['name'] == 'output.weight')
    require(output['type_id'] == 13, 'Output type no longer excluded from F32 conversion')
    maximum = max(math.prod(t['shape']) * 4 for t in targets)
    require(maximum < 2**29, 'Individual targeted F32 weight matrix exceeds512MiB')
    source = SOURCE.read_bytes()
    needle = b'bool ggml_cuda_should_use_mmq(enum ggml_type type, int cc, int64_t ne11, int64_t n_experts) {\n'
    require(source.count(needle) == 1, 'Exact host dispatcher signature differs')
    patch = b'''#ifdef LLMSX_QWEN36_F32_PREFILL_DIAGNOSTIC
    // Keep Q5_K output and all decode MMVQ paths unchanged. No activation Q8 here.
    if (type == GGML_TYPE_Q2_K || type == GGML_TYPE_Q4_K || type == GGML_TYPE_IQ2_XXS) {
        return false;
    }
#endif
'''
    patched_source = source.replace(needle, needle + patch)
    write('mmq.cu', patched_source)
    write('MEMORY-PLAN.json', {'target_type_ids': [10, 12, 16], 'target_cuda_tensor_count': len(targets), 'maximum_individual_F32_weight_bytes': maximum, 'output_type_id': 13, 'output_F32_conversion_enabled': False, 'host_embedding_excluded': True, 'workspace_reserve_bytes': 2147483648, 'allocator_reserve_bytes': 268435456, 'driver_reserve_bytes': 2147483648, 'safety_reserve_bytes': 1073741824, 'measured_peak_verified': False, 'notice': 'Individual matrix bound only; no claim about total simultaneous pool residency or runtime peak.'})
    pins, identities, drift = capture_closure(inputs, patched_source)
    write('BUILD-INPUT-CLOSURE.json', {'version': '1.0.2', 'pins': pins, 'identities': identities, 'historical_manifest_entries': len(json.loads((BASE / 'SOURCE-PINS.json').read_bytes())), 'historical_matching_entries_verified': len(json.loads((BASE / 'SOURCE-PINS.json').read_bytes())) - len(drift), 'explicit_historical_drift': drift, 'coverage': 'Declared source/header/link operands and tool executables. This is not a claim that every dynamic library or shared-cache page of the compiler process is pinned.', 'known_compile_dependencies': len(inputs['compile_dependency_paths']), 'verified_before_compile': True})
    write('CONSUMED.json', {'GPU_initializations': 0, 'server_execution': False, 'automatic_runtime_launch': False})
    ggml = MACUDA / 'llama.cpp/ggml'
    shim = MACUDA / 'cuda-shim'
    flags = ['-std=c++17', '-O2', '-DNDEBUG', '-isysroot', SDK, '-x', 'cuda', '--cuda-host-only', '--offload-arch=sm_120a', '--cuda-path=' + str(shim / 'cuda-13'), '-nocudalib', '-Wno-unknown-cuda-version', '-include', str(shim / 'spike/tinycudart_compat.h'), '-I' + str(shim / 'cuda-13/include/cccl'), '-I' + str(ggml / 'include'), '-I' + str(ggml / 'src'), '-I' + str(ggml / 'src/ggml-cuda'), '-DGGML_CUDA_FORCE_MMQ', '-DGGML_CUDA_NO_VMM', '-DGGML_CUDA_USE_GRAPHS', '-DLLMSX_QWEN36_F32_PREFILL_DIAGNOSTIC']
    for k in ('F16', 'Q4_0', 'Q4_1', 'Q5_0', 'Q5_1', 'Q8_0', 'BF16'):
        for v in ('F16', 'Q4_0', 'Q4_1', 'Q5_0', 'Q5_1', 'Q8_0', 'BF16'):
            flags.append('-DGGML_CUDA_FA_' + k + '_' + v + '=1')
    run('COMPILE-HOST-DISPATCH', ['/opt/homebrew/opt/llvm/bin/clang++', *flags, '-MD', '-MF', str(ROOT / 'mmq.d'), '-c', str(ROOT / 'mmq.cu'), '-o', str(ROOT / 'mmq.o')])
    dependency_text = (ROOT / 'mmq.d').read_text().replace('\\\n', ' ')
    dependencies = shlex.split(dependency_text.split(':', 1)[1])
    require(set(dependencies) <= set(pins), 'Compilation discovered an unbound dependency')
    verify_closure(pins, identities)
    shutil.copyfile(ARCHIVE, ROOT / 'libggml-cuda-f32-prefill.a')
    run('REPLACE-HOST-OBJECT', ['/opt/homebrew/opt/llvm/bin/llvm-ar', 'rcs', str(ROOT / 'libggml-cuda-f32-prefill.a'), str(ROOT / 'mmq.o')])
    write('ARCHIVE-INTEGRITY.json', verify_archive(ARCHIVE, ROOT / 'libggml-cuda-f32-prefill.a'))
    argv = link_arguments(inputs)
    archive_alias = str(MACUDA / 'cuda-shim/build/libggml-cuda.a')
    mapped = [str(ROOT / 'llama-server-f32-prefill-diagnostic') if a == str(BASE / 'llama-server-27b-preload-guard') else str(ROOT / 'libggml-cuda-f32-prefill.a') if a == archive_alias else a for a in argv]
    require(archive_alias not in mapped and str(ROOT / 'libggml-cuda-f32-prefill.a') in mapped, 'Exact archive mapping failed')
    run('LINK', mapped)
    run('OBJECT-SECTIONS', ['/usr/bin/otool', '-l', str(ROOT / 'mmq.o')])
    sections = (ROOT / 'OBJECT-SECTIONS.stdout').read_text()
    require('fatbin' not in sections and '__nv' not in sections, 'Unexpected CUDA device payload in host dispatcher')
    run('STATIC-SYMBOLS', ['/usr/bin/nm', '-g', str(ROOT / 'llama-server-f32-prefill-diagnostic')])
    symbols = (ROOT / 'STATIC-SYMBOLS.stdout').read_text()
    require(sum(' T __Z24ggml_cuda_should_use_mmq9ggml_typeixx' in line for line in symbols.splitlines()) == 1, 'Exactly one linked dispatcher definition required')
    for path, digest in inputs['pins'].items():
        require(sha(Path(path)) == digest, 'Original input changed during build: ' + path)
    verify_closure(pins, identities)
    write('BUILD-READY.json', {'version': '1.0.2', 'offline_build_passed': True, 'GPU_initializations': 0, 'server_execution': False, 'physical_admission_ready': False, 'independent_review_pending': True, 'historical_unchanged_entries_verified': len(json.loads((BASE / 'SOURCE-PINS.json').read_bytes())) - len(drift), 'explicit_historical_dependency_changes': drift, 'declared_build_inputs_before_and_after_verified': True, 'all_historical_inputs_unchanged': False, 'closure_pin_count': len(pins), 'original_numerical_atol': 0.05, 'diagnostic_binary': str(ROOT / 'llama-server-f32-prefill-diagnostic'), 'diagnostic_binary_sha256': sha(ROOT / 'llama-server-f32-prefill-diagnostic'), 'runtime_environment_for_future_trial': {'GGML_CUDA_CUBLAS_COMPUTE_TYPE': 'f32', 'TINYCUBLAS_TC': '0'}, 'target_types': ['Q2_K', 'Q4_K', 'IQ2_XXS'], 'full_qualification': False, 'remaining': 'Independent CPU audit, allocation and actual cold-owner authority, actual numerical/peak controls; coding and standard /dr.'})
    print((ROOT / 'BUILD-READY.json').read_text(), flush=True)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        if not (ROOT / 'BUILD-FAILURE.json').exists():
            write('BUILD-FAILURE.json', {'version': '1.0.2', 'exception_type': type(error).__name__, 'error': str(error), 'GPU_initializations': 0, 'server_execution': False, 'consumed': (ROOT / 'CONSUMED.json').exists()})
        raise
