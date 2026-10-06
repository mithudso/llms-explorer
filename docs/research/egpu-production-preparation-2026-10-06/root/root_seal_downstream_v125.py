#!/usr/bin/env python3
"""Issue one source-only authority; never activate a runtime or request."""
import hashlib
import json
import os
import stat
import types
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-downstream-preparation-v125')
RECEIVER = Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-cold-capture-execution-20261006')
DRAFT = ROOT / 'DOWNSTREAM-REVIEW-DRAFT.json'
DRAFT_SHA = '71d7fda85e639bc99562aa0213bcf92a35cb5b704706e1c1596c8acf389f2f5e'
AUDIT = Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-cold-capture-independent-review-20261006/TASK620-DOWNSTREAM-SOURCE-REVIEW.json')
AUDIT_SHA = 'f4bbd0019eb0a83b28082e6887d5b8c0ad63374811b94f5348d616aa4a86d74b'
COMMON = ROOT / 'downstream_common.py'
COMMON_SHA = 'bb144de159e83520305a37528697a70273a2fdbbcac539e55e612f6dd4ac1d6b'
FINAL = ROOT / 'INDEPENDENT-DOWNSTREAM-REVIEW.json'


def held(path, expected):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        assert stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
        assert stat.S_IMODE(before.st_mode) == 0o600 and before.st_size < 64 * 1024**2
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read()
        after = os.fstat(fd)
        assert (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
        assert hashlib.sha256(raw).hexdigest() == expected
        return raw
    finally:
        os.close(fd)


def create(path, value):
    raw = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    digest = hashlib.sha256(raw).hexdigest()
    assert held(path, digest) == raw
    return digest


def main():
    assert not FINAL.exists()
    draft = json.loads(held(DRAFT, DRAFT_SHA))
    audit = json.loads(held(AUDIT, AUDIT_SHA))
    assert audit['passed'] is True and audit['status'] == 'complete'
    final = dict(draft)
    final.update(passed=True, seal_pending=False, independent_review_pending=False,
                 issuer='root-independent-source-seal',
                 independent_audit={'path': str(AUDIT), 'sha256': AUDIT_SHA},
                 source_draft={'path': str(DRAFT), 'sha256': DRAFT_SHA},
                 sealed_at=datetime.now(timezone.utc).isoformat())
    assert final['actual_session_identity'] is None
    for key in ('actual_numerical_acceptance', 'full_qualification', 'physical_launch_ready', 'cold_admission_issued', 'coding_verified', 'standard_research_verified', 'actual_peak_verified'):
        assert final[key] is False
    common = types.ModuleType('root_held_downstream_common')
    common.__file__ = str(COMMON)
    exec(compile(held(COMMON, COMMON_SHA), str(COMMON), 'exec'), common.__dict__)
    renderer = common.renderer()
    renderer.final_review(final)
    final_sha = create(FINAL, final)
    consumed = common.bound_document({'path': str(FINAL), 'sha256': final_sha})
    renderer.final_review(consumed)
    common.load_source(ROOT / 'claude_candidate.py', consumed, renderer, 'root_definitions_only_candidate')
    receipt = {
        'version': '1.0.0', 'issued_at': final['sealed_at'], 'source_only': True,
        'final': {'path': str(FINAL), 'sha256': final_sha},
        'independent_audit': final['independent_audit'], 'source_draft': final['source_draft'],
        'actual_pure_consumer_readback_passed': True,
        'independent_final_readback_pending': True,
        'conditions': audit['operational_conditions'],
        'actual_activation_issued': False, 'actual_session_identity': None,
        'actual_numerical_acceptance': False, 'full_qualification': False,
        'native_starts': 0, 'HTTP_calls': 0, 'model_calls': 0,
    }
    receipt_sha = create(RECEIVER / 'DOWNSTREAM-V125-ROOT-SEAL-RECEIPT.json', receipt)
    print(json.dumps({'final_path': str(FINAL), 'final_sha256': final_sha, 'receipt_sha256': receipt_sha, 'pure_readback_passed': True, 'actual_activation_issued': False}))


if __name__ == '__main__':
    main()
