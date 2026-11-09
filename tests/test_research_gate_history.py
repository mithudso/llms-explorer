"""Portable history tests use synthetic judgments, never research acceptance."""
import copy
import importlib.util
import json
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


def install_judge(history, verdict):
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
