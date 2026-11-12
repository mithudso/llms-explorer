"""Portable history tests use synthetic judgments, never research acceptance."""
import copy
import importlib.util
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location('history_gate', Path(__file__).resolve().parents[1] / 'scripts/research_gate.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


@pytest.fixture
def history(tmp_path):
    text = 'The fieldA value is 4. The fieldB value is 8.'
    body = tmp_path / 'source.txt'
    body.write_text(text)
    url = 'https://example.org/fields'
    span = {'url': url, 'source_id': 'src:test', 'snapshot_sha256': gate.digest(text.encode()),
            'start': 0, 'end': len(text), 'quote': text, 'extraction_status': 'complete'}
    doc = {'concept': 'Fields', 'claims': [
        {'text': 'The fieldA value is 4.', 'sources': [url], 'confidence': 'low', 'evidence': [copy.deepcopy(span)]},
        {'text': 'The fieldB value is 8.', 'sources': [url], 'confidence': 'low', 'evidence': [copy.deepcopy(span)]}]}
    manifest = {'slug': 'history', 'depth': 'quick', 'gate_contract_version': 4,
                'concepts': [{'name': 'Fields', 'slug': 'fields', 'status': 'done'}]}

    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)

    shared = SimpleNamespace(load_claims=lambda *args: {'fields': doc}, atomic_write=write,
        run_dir=lambda slug: tmp_path, source_id=lambda source: 'src:test',
        lib_find=lambda source: {'url': url, 'id': 'src:test', 'text_path': str(body),
                                 'sha256': gate.digest(body.read_bytes())},
        _create_run=lambda *args, **kwargs: manifest, load_manifest=lambda slug: manifest,
        save_manifest=lambda value: manifest.update(value), run_lock=lambda slug: nullcontext(),
        _now=lambda: '2026-11-02T00:00:00Z', _print=lambda value: None,
        _probe_claims_path=lambda *args: tmp_path / 'absent')
    return shared, manifest, doc, tmp_path


def response(packet, verdict='SUPPORTED'):
    return {'schema': packet['schema'], 'packet_sha256': packet['packet_sha256'],
        'conflict_reviewed_claim_ids': [row['claim_id'] for row in packet['claims']], 'conflicts': [],
        'verdicts': [{**{key: row[key] for key in ('claim_id', 'claim_sha256', 'text')},
            'verdict': verdict, 'rationale': 'Synthetic evidence judgment for offline history regression.',
            'evidence': copy.deepcopy(row['evidence'])} for row in packet['claims']]}


def save_review(shared, manifest, root, name, verdict='SUPPORTED', conflict=False):
    out = root / 'gate/attempts' / name
    packet = gate.prepare(shared, manifest, out, 'all', 0)
    result = response(packet, verdict)
    if conflict:
        result['conflicts'] = [{'claim_ids': [row['claim_id'] for row in packet['claims']],
            'resolution': 'unresolved', 'rationale': 'The synthetic assertions have incompatible applicability.'}]
    report = gate.validate(packet, result, out)
    (out / 'verdicts.json').write_text(json.dumps(result))
    (out / 'validation.json').write_text(json.dumps({**report, 'is_error': not report['all_supported']}))
    return packet, result


def install_judge(history, verdict='SUPPORTED'):
    shared, manifest, _doc, root = history
    calls = []

    def judge(*args):
        attempt = max((root / 'gate/attempts').iterdir())
        packet = json.loads((attempt / 'packet.json').read_text())
        result = response(packet, verdict)
        reused = {row['claim_id'] for row in packet.get('reused_verdicts', [])}
        result['verdicts'] = [row for row in result['verdicts'] if row['claim_id'] not in reused]
        calls.append([row['claim_id'] for row in result['verdicts']])
        (attempt / 'verdicts.json').write_text(json.dumps(result))
        return {'is_error': False}

    shared.run_agent = judge
    gate.install(shared)
    args = SimpleNamespace(slug=manifest['slug'], sample='all', dry_run=False, refetch_cap=0,
                           model=None, effort=None, max_turns=1, agent_timeout=1)
    return args, calls


def missing_binary_history(history):
    """Reproduce the archived Codex branch before run_worker was called."""
    shared, manifest, _doc, root = history
    previous = root / 'gate/attempts/0000-startup'
    packet = gate.prepare(shared, manifest, previous, 'all', 0)
    summary = {'transport': 'codex-exec', 'result': gate.MISSING_CODEX_BINARY,
               'is_error': True, 'usage': {}, 'tools': [], 'num_turns': 0,
               'tokens': 0, 'seconds': 0, 'model': 'gpt-6.1-sol', 'effort': 'medium'}
    worker = root / 'agents/attempts/gate/missing-binary'
    worker.mkdir(parents=True)
    for name in ('worker.json', 'validated-summary.json'):
        (worker / name).write_text(json.dumps(summary))
    for name in ('worker.events.jsonl', 'worker.log', 'worker.last-message.txt'):
        (worker / name).write_text('')
    (worker / 'brief.md').write_text(gate.brief(packet, previous))
    prior = {'schema': packet['schema'], 'validated': False, 'is_error': True,
             'attempt': str(previous.relative_to(root)), 'packet_sha256': packet['packet_sha256'],
             'review_binding': packet['review_binding'], 'finished': shared._now(),
             'error': gate.MISSING_CODEX_BINARY, 'model': summary['model'], 'effort': summary['effort'],
             'tokens': 0, 'seconds': 0}
    (previous / 'validation.json').write_text(json.dumps(prior))
    manifest['gate'] = prior
    manifest['agents'] = {'gate': {**summary, 'counts': {}, 'attempts': [
        {'path': str(worker.relative_to(root)), 'tokens': 0, 'seconds': 0, 'is_error': True}]}}
    shared.claude_binary = lambda: sys.executable
    return previous, worker, packet


@pytest.mark.parametrize('binary', [None, 'missing', 'not-executable'])
def test_missing_executor_never_overwrites_semantic_receipt_or_invokes_worker(history, binary):
    shared, manifest, _doc, root = history
    args, calls = install_judge(history)
    prior = {'accepted_previous_receipt': 'preserve exactly'}
    manifest['gate'] = copy.deepcopy(prior)
    unavailable = root / 'worker'
    if binary == 'not-executable':
        unavailable.write_text('not executable')
        unavailable.chmod(0o600)
    shared.claude_binary = lambda: None if binary is None else str(unavailable)
    assert shared.cmd_gate(args) == 1
    assert calls == [] and manifest['gate'] == prior
    attempts = list((root / 'gate/attempts').iterdir())
    assert len(attempts) == 1 and not (attempts[0] / 'validation.json').exists()
    startup = json.loads((attempts[0] / 'startup.json').read_text())
    assert startup['worker_invoked'] is False and startup['failure_stage'] == 'pre-model-startup'
    shared.claude_binary = lambda: sys.executable
    assert shared.cmd_gate(args) == 0
    assert len(calls) == 1
    shared.claude_binary = lambda: None
    assert shared.cmd_gate(args) == 0  # Exact successful judgments need no executor.
    assert len(calls) == 1


def test_exact_archived_missing_binary_recovers_once_without_rewriting_history(history):
    shared, manifest, _doc, root = history
    previous, worker, _packet = missing_binary_history(history)
    preserved = {path: path.read_bytes() for directory in (previous, worker)
                 for path in directory.rglob('*') if path.is_file()}
    prior = copy.deepcopy(manifest['gate'])
    args, calls = install_judge(history)
    assert shared.cmd_gate(args) == 0
    assert len(calls) == 1 and gate.verify_current(shared, manifest)['all_supported']
    assert all(path.read_bytes() == body for path, body in preserved.items())
    markers = list((root / 'gate/startup-recoveries').glob('*.json'))
    assert len(markers) == 1
    assert manifest['gate']['startup_recovery']['prior_attempt'] == prior['attempt']
    manifest['gate'] = prior  # Restoring a pointer cannot reset the consumed allowance.
    assert shared.cmd_gate(args) == 0  # It can still reuse the completed supported proof.
    assert len(calls) == 1


@pytest.mark.parametrize('corruption', ['generic-error', 'turn', 'usage', 'event', 'log', 'output',
                                      'verdict', 'response', 'brief', 'worker-summary', 'missing-record'])
def test_zero_tokens_or_matching_error_alone_cannot_authorize_recovery(history, corruption):
    shared, manifest, _doc, _root = history
    previous, worker, packet = missing_binary_history(history)
    if corruption == 'generic-error':
        manifest['gate']['error'] = 'timed out after 30s'
        (previous / 'validation.json').write_text(json.dumps(manifest['gate']))
    elif corruption in ('turn', 'usage'):
        summary = json.loads((worker / 'worker.json').read_text())
        summary.update({'num_turns': 1} if corruption == 'turn' else {'usage': {'input_tokens': 1}})
        for name in ('worker.json', 'validated-summary.json'):
            (worker / name).write_text(json.dumps(summary))
        manifest['agents']['gate'].update(summary)
    elif corruption in ('event', 'log', 'output'):
        name = {'event': 'worker.events.jsonl', 'log': 'worker.log', 'output': 'worker.last-message.txt'}[corruption]
        (worker / name).write_text('reviewer execution evidence')
    elif corruption == 'verdict':
        (previous / 'verdicts.json').write_text(json.dumps(response(packet, 'UNVERIFIED')))
    elif corruption == 'response':
        (previous / 'response.json').write_text('{}')
    elif corruption == 'brief':
        (worker / 'brief.md').write_text('Another packet had the same startup error.')
    elif corruption == 'worker-summary':
        (worker / 'validated-summary.json').write_text('{}')
    else:
        (worker / 'worker.events.jsonl').unlink()
    args, calls = install_judge(history)
    assert shared.cmd_gate(args) == 1
    assert calls == []


def test_startup_recovery_is_consumed_atomically_before_unknown_dispatch(history):
    shared, manifest, doc, root = history
    _previous, _worker, packet = missing_binary_history(history)
    recovery = gate.unstarted_codex_recovery(shared, manifest, packet)
    assert recovery is not None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda n: gate.reserve_startup_recovery(
            shared, manifest, recovery, root / f'gate/attempts/concurrent-{n}'), range(2)))
    assert sorted(results) == [False, True]
    assert gate.unstarted_codex_recovery(shared, manifest, packet) is None
    # A new receipt or confidence annotation cannot mint another allowance.
    doc['claims'][0]['confidence'] = 'high'
    annotated = gate.prepare(shared, manifest, root / 'annotation', 'all', 0)
    assert annotated['review_binding'] == packet['review_binding']
    replacement_receipt = {**recovery, 'prior_validation_sha256': 'different-receipt'}
    assert not gate.reserve_startup_recovery(shared, manifest, replacement_receipt, root / 'gate/attempts/again')


def test_real_dissent_after_startup_recovery_cannot_be_reviewed_again(history):
    shared, manifest, _doc, _root = history
    missing_binary_history(history)
    args, calls = install_judge(history, 'UNVERIFIED')
    assert shared.cmd_gate(args) == 1
    assert manifest['gate']['startup_recovery']
    assert manifest['gate']['counts'] == {'UNVERIFIED': 2}
    assert shared.cmd_gate(args) == 1
    assert len(calls) == 1


def test_interrupted_recovery_cannot_dispatch_again(history):
    shared, _manifest, _doc, _root = history
    missing_binary_history(history)
    args, calls = install_judge(history)
    def interrupted(*args):
        calls.append('unknown worker execution')
        raise RuntimeError('interrupted after durable dispatch claim')
    shared.run_agent = interrupted
    with pytest.raises(RuntimeError, match='interrupted'):
        shared.cmd_gate(args)
    assert shared.cmd_gate(args) == 1
    assert calls == ['unknown worker execution']


def archived_history(history):
    """Use the real immutable archive writer with a hermetic shared library."""
    shared, _manifest, doc, root = history
    spec = importlib.util.spec_from_file_location(
        'snapshot_history_provenance', Path(__file__).resolve().parents[1] / 'scripts/research_provenance.py')
    provenance = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(provenance)
    shared.RESEARCH_DIR = root / 'research'
    shared.evidence_provenance = provenance
    url = doc['claims'][0]['sources'][0]
    record = provenance.archive(shared.RESEARCH_DIR / '.library', shared.lib_find(url))
    return record


def test_authored_snapshot_survives_latest_cache_replacement_without_another_model_call(history):
    shared, manifest, doc, root = history
    snapshot = archived_history(history)
    args, calls = install_judge(history, 'SUPPORTED')
    assert shared.cmd_gate(args) == 0
    first = root / manifest['gate']['attempt']
    original_packet = json.loads((first / 'packet.json').read_text())
    original_body = Path(snapshot['snapshot_path']).read_bytes()
    replacement = 'A later extract describes another version, with fieldA equal to 40.'
    (root / 'source.txt').write_text(replacement)

    assert shared.cmd_gate(args) == 0
    assert len(calls) == 1
    current = root / manifest['gate']['attempt']
    packet = json.loads((current / 'packet.json').read_text())
    url = doc['claims'][0]['sources'][0]
    assert packet['sources'][url]['snapshot_sha256'] == snapshot['snapshot_sha256']
    assert gate.evidence_text(packet, current, packet['sources'][url]).encode() == original_body
    assert len(packet['reused_verdicts']) == 2
    assert [gate.assertion_review_binding(packet, row) for row in packet['claims']] == [
        gate.assertion_review_binding(original_packet, row) for row in original_packet['claims']]
    assert (root / 'source.txt').read_text() == replacement
    assert Path(snapshot['snapshot_path']).read_bytes() == original_body
    assert (first / original_packet['sources'][url]['file']).read_bytes() == original_body


def test_pinned_archive_remains_usable_when_latest_cache_entry_is_missing(history):
    shared, manifest, doc, root = history
    snapshot = archived_history(history)
    shared.lib_find = lambda _url: None
    shared.lib_snapshot = lambda *args, **kwargs: pytest.fail('explicit pins must not fetch latest')
    packet = gate.prepare(shared, manifest, root / 'attempt', 'all', 10)
    assert packet['sources'][doc['claims'][0]['sources'][0]]['snapshot_id'] == snapshot['snapshot_id']
    assert gate.validate(packet, response(packet), root / 'attempt')['all_supported']


@pytest.mark.parametrize('contract', [2, 3])
def test_legacy_packets_keep_their_existing_latest_source_resolution(history, contract):
    shared, manifest, doc, root = history
    snapshot = archived_history(history)
    manifest['gate_contract_version'] = contract
    (root / 'source.txt').write_text('The later fieldA value is 40.')
    packet = gate.prepare(shared, manifest, root / 'attempt', 'all', 0)
    source = packet['sources'][doc['claims'][0]['sources'][0]]
    assert source['snapshot_sha256'] != snapshot['snapshot_sha256']
    assert gate.evidence_text(packet, root / 'attempt', source) == 'The later fieldA value is 40.'


@pytest.mark.parametrize('corruption', [
    'missing-receipt', 'missing-body', 'tampered-body', 'wrong-source', 'wrong-hash',
    'wrong-snapshot-id', 'wrong-url', 'escaped-body-path', 'escaped-receipt', 'escaped-body',
])
def test_invalid_pinned_archive_cannot_fall_back_to_latest_or_trigger_a_model(history, corruption):
    shared, manifest, _doc, root = history
    snapshot = archived_history(history)
    archive = shared.RESEARCH_DIR / '.library/provenance'
    receipt = archive / 'versions' / (snapshot['snapshot_id'][5:] + '.json')
    body = Path(snapshot['snapshot_path'])
    if corruption == 'missing-receipt':
        receipt.unlink()
    elif corruption == 'missing-body':
        body.unlink()
    elif corruption == 'tampered-body':
        body.write_text('A tampered archive is not evidence.')
    elif corruption == 'escaped-receipt':
        outside = root / 'outside.json'
        outside.write_bytes(receipt.read_bytes())
        receipt.unlink()
        receipt.symlink_to(outside)
    elif corruption == 'escaped-body':
        outside = root / 'outside.txt'
        outside.write_bytes(body.read_bytes())
        body.unlink()
        body.symlink_to(outside)
    else:
        record = json.loads(receipt.read_text())
        if corruption == 'wrong-source':
            record['source_id'] = 'src:another'
        elif corruption == 'wrong-hash':
            record['snapshot_sha256'] = '0' * 64
        elif corruption == 'wrong-snapshot-id':
            record['snapshot_id'] = 'snap:' + '0' * 64
        elif corruption == 'wrong-url':
            record['url'] = 'https://other.example/fields'
        else:
            outside = root / 'outside.txt'
            outside.write_bytes(body.read_bytes())
            record['snapshot_path'] = str(outside)
        receipt.write_text(json.dumps(record))
    (root / 'source.txt').write_text('A later available extract is not the authored snapshot.')
    shared.lib_snapshot = lambda *args, **kwargs: pytest.fail('explicit pins must not fetch latest')
    args, calls = install_judge(history, 'SUPPORTED')
    assert shared.cmd_gate(args) == 1
    assert calls == []
    preflight = json.loads((root / manifest['gate']['attempt'] / 'preflight.json').read_text())
    assert len(preflight['failures']) == 2
    assert all('pinned source' in row['error'] for row in preflight['failures'])


@pytest.mark.parametrize('location', ['claim', 'disagreement', 'conflict-position'])
def test_one_url_cannot_merge_incompatible_authored_versions(history, location):
    shared, manifest, doc, root = history
    snapshot = archived_history(history)
    old = copy.deepcopy(doc['claims'][0]['evidence'][0])
    new = {**old, 'snapshot_sha256': '1' * 64}
    if location == 'claim':
        doc['claims'][1]['evidence'] = [new]
    elif location == 'conflict-position':
        doc['claims'][0]['conflict'] = {'status': 'attributed', 'positions': [
            {'text': doc['claims'][0]['text'], 'evidence': [old]},
            {'text': doc['claims'][1]['text'], 'evidence': [new]}]}
    else:
        doc['disagreements'] = [{'text': 'The attributed documents describe different field values.',
            'sources': [old['url']], 'evidence': [new],
            'conflict': {'status': 'attributed', 'positions': [
                {'text': doc['claims'][0]['text'], 'evidence': [new]},
                {'text': doc['claims'][1]['text'], 'evidence': [new]}]}}]
    with pytest.raises(ValueError, match='incompatible authored source snapshots'):
        gate.prepare(shared, manifest, root / 'attempt', 'all', 0)
    failures = json.loads((root / 'attempt/preflight.json').read_text())['failures']
    assert len(failures) == 1 and failures[0]['claim_id']
    assert Path(snapshot['snapshot_path']).is_file()
    assert not (root / 'attempt/evidence').exists()


@pytest.mark.parametrize('contract', [2, 3, 4])
def test_exact_same_contract_support_skips_all_repeat_model_calls(history, contract):
    shared, manifest, _doc, _root = history
    manifest['gate_contract_version'] = contract
    args, calls = install_judge(history, 'SUPPORTED')
    assert shared.cmd_gate(args) == 0
    assert shared.cmd_gate(args) == 0
    assert len(calls) == 1
    assert manifest['gate']['counts'] == {'SUPPORTED': 2}


@pytest.mark.parametrize('old_contract,new_contract', [(2, 3), (2, 4), (3, 4), (4, 3), (3, 2)])
def test_support_never_migrates_between_gate_contracts(history, old_contract, new_contract):
    shared, manifest, _doc, root = history
    manifest['gate_contract_version'] = old_contract
    save_review(shared, manifest, root, '01-old')
    manifest['gate_contract_version'] = new_contract
    packet = gate.prepare(shared, manifest, root / 'gate/attempts/02-current', 'all', 0)
    assert packet['reused_verdicts'] == []
    assert 'reused_conflict_review' not in packet


@pytest.mark.parametrize('contract', [2, 3, 4])
@pytest.mark.parametrize('change', ['metadata', 'confidence', 'observation', 'mixed'])
def test_bookkeeping_or_sibling_repairs_cannot_retry_unchanged_dissent(history, contract, change):
    shared, manifest, doc, root = history
    manifest['gate_contract_version'] = contract
    args, calls = install_judge(history, 'NOT-IN-SOURCE')
    assert shared.cmd_gate(args) == 1
    assert shared.cmd_gate(args) == 1
    if change == 'metadata':
        doc['telemetry'] = {'queries': 999}
    elif change == 'confidence':
        doc['claims'][0]['confidence'] = 'high'
    elif change == 'observation':
        doc['claims'][0]['temporal'] = {'recorded_at': '2026-11-02T00:00:00Z'}
    else:
        doc['claims'][0]['text'] = 'The documented fieldA value is 4.'
    assert shared.cmd_gate(args) == 1
    assert len(calls) == 1
    receipt = json.loads((root / manifest['gate']['attempt'] / 'validation.json').read_text())
    assert receipt['blocked_prior_dissent']
    repair = json.loads((root / manifest['gate']['attempt'] / 'repair.json').read_text())
    assert calls[0][1] in repair['failed_claim_ids']


@pytest.mark.parametrize('contract', [2, 3, 4])
def test_newest_valid_dissent_shadows_old_support_and_rejects_forged_support(history, contract):
    shared, manifest, _doc, root = history
    manifest['gate_contract_version'] = contract
    old, _ = save_review(shared, manifest, root, '01-support')
    save_review(shared, manifest, root, '02-dissent', verdict='NOT-IN-SOURCE')
    current = root / 'gate/attempts/03-current'
    packet = gate.prepare(shared, manifest, current, 'all', 0)
    assert packet['reused_verdicts'] == []
    assert {row['claim_id'] for row in packet['blocked_prior_dissent']} == {row['claim_id'] for row in old['claims']}
    with pytest.raises(ValueError, match='unchanged prior dissent/conflict'):
        gate.validate(packet, response(packet), current)


def test_unresolved_conflicts_survive_document_metadata_edits(history):
    shared, manifest, doc, root = history
    save_review(shared, manifest, root, '01-support')
    save_review(shared, manifest, root, '02-conflict', conflict=True)
    doc['telemetry'] = {'changed': 'Only document metadata changed.'}
    current = root / 'gate/attempts/03-current'
    packet = gate.prepare(shared, manifest, current, 'all', 0)
    assert packet['blocked_prior_conflicts']
    assert 'reused_conflict_review' not in packet
    with pytest.raises(ValueError, match='unchanged prior dissent/conflict'):
        gate.validate(packet, response(packet), current)


@pytest.mark.parametrize('contract', [2, 4])
def test_refusal_receipts_do_not_age_paid_dissent_out_of_history(history, contract):
    shared, manifest, _doc, root = history
    manifest['gate_contract_version'] = contract
    save_review(shared, manifest, root, '01-paid-dissent', verdict='NOT-IN-SOURCE')
    for index in range(130):
        attempt = root / 'gate/attempts' / f'02-refused-{index:03d}'
        attempt.mkdir()
        (attempt / 'validation.json').write_text(json.dumps({'validated': False, 'is_error': True}))
    packet = gate.prepare(shared, manifest, root / 'gate/attempts/03-current', 'all', 0)
    assert len(packet['blocked_prior_dissent']) == 2
    assert packet['reused_verdicts'] == []


def test_failure_binding_ignores_bookkeeping_but_retains_applicability_and_evidence(history):
    shared, manifest, _doc, root = history
    packet = gate.prepare(shared, manifest, root / 'attempt', 'all', 0)
    original = packet['claims'][0]
    changed = copy.deepcopy(original)
    changed.update(confidence='high', claim_id='different-id', claim_sha256='different-hash',
                   temporal={'recorded_at': '2026-11-02T00:00:00Z'}, verified_as_of='2026-11-02')
    changed['evidence'].append(copy.deepcopy(changed['evidence'][0]))
    changed['evidence'].reverse()
    changed['evidence'][0]['evidence_id'] = 'unrelated-bookkeeping'
    assert gate.assertion_review_binding(packet, original) == gate.assertion_review_binding(packet, changed)
    assert gate.assertion_binding(packet, original) != gate.assertion_binding(packet, changed)
    for key, value in [('valid_from', '2026-01-01'), ('valid_to', '2027-01-01'), ('applicability_version', 'v2.0.0')]:
        applicable = copy.deepcopy(changed)
        applicable['temporal'][key] = value
        assert gate.assertion_review_binding(packet, original) != gate.assertion_review_binding(packet, applicable)
    for mutation in ['text', 'quote', 'source']:
        repaired = copy.deepcopy(original)
        if mutation == 'text': repaired['text'] += ' A qualified change.'
        elif mutation == 'quote':
            repaired['evidence'][0]['end'] -= 1
            repaired['evidence'][0]['quote'] = repaired['evidence'][0]['quote'][:-1]
        else: repaired['sources'].append('https://example.org/new-evidence')
        assert gate.assertion_review_binding(packet, original) != gate.assertion_review_binding(packet, repaired)


def test_unresolved_conflict_survives_invalid_supporting_quote_on_one_participant(history):
    shared, manifest, _doc, root = history
    old, result = save_review(shared, manifest, root, '01-conflict', conflict=True)
    result['verdicts'][0]['evidence'][0]['quote'] += ' forged'
    (root / 'gate/attempts/01-conflict/verdicts.json').write_text(json.dumps(result))
    current = root / 'gate/attempts/02-current'
    packet = gate.prepare(shared, manifest, current, 'all', 0)
    assert len(packet['reused_verdicts']) == 1
    assert packet['blocked_prior_conflicts']
    assert set(packet['blocked_prior_conflicts'][0]['claim_ids']) == {row['claim_id'] for row in old['claims']}
    assert 'reused_conflict_review' not in packet
    with pytest.raises(ValueError, match='unchanged prior dissent/conflict'):
        gate.validate(packet, response(packet), current)
