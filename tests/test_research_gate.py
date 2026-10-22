"""Adversarial contract checks independent of paid models and shared state."""
import copy
import importlib.util
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location('bound_gate', Path(__file__).resolve().parents[1] / 'scripts/research_gate.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


@pytest.fixture
def pinned():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        text = 'Café evidence: The atomic rename retains the directory entry after a crash.'
        body = root / 'body.txt'
        body.write_text(text)
        doc = {'concept': 'Durability', 'claims': [{'text': text[15:], 'confidence': 'high', 'sources': ['https://example.org/docs']}]}
        manifest = {'slug': 'test', 'depth': 'standard', 'concepts': [{'name': 'Durability', 'slug': 'durability', 'status': 'done'}]}
        def write(path, content):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        shared = SimpleNamespace(load_claims=lambda slug, errors: {'durability': doc},
            lib_find=lambda url: {'id': 'src:abc', 'url': url, 'text_path': str(body), 'sha256': gate.digest(text.encode())},
            source_id=lambda url: 'src:abc', atomic_write=write)
        packet = gate.prepare(shared, manifest, root / 'attempt', 'all', 0)
        row = packet['claims'][0]
        response = {'schema': gate.SCHEMA, 'packet_sha256': packet['packet_sha256'], 'verdicts': [
            {**{k: row[k] for k in ('claim_id', 'claim_sha256', 'text')}, 'verdict': 'SUPPORTED',
             'rationale': 'The pinned evidence establishes the entire statement.',
             'evidence': [{'url': row['sources'][0], 'source_id': 'src:abc',
                          'snapshot_sha256': gate.digest(text.encode()), 'start': 15, 'end': len(text), 'quote': text[15:]}]}]}
        yield shared, manifest, doc, root / 'attempt', packet, response


def test_exact_unicode_span_and_deterministic_risk_coverage(pinned):
    *_, root, packet, response = pinned
    assert gate.validate(packet, response, root)['all_supported']
    rows = [{'claim_id': str(i), 'risk': ['numeric'] if i < 8 else []} for i in range(20)]
    selected = gate.select_claims(rows, 3, 'fixed')
    assert len(selected) == 11
    assert selected == gate.select_claims(rows, 3, 'fixed')
    assert len(gate.select_claims(rows, 0, 'fixed')) == 8
    for text in ('The default is enabled.', 'The limit is 64.', 'Use GET /v1/jobs.', 'Authentication requires a role.'):
        assert gate.risks({'text': text})


@pytest.mark.parametrize('mutation', ['missing', 'extra', 'duplicate', 'identity', 'hash', 'text', 'packet', 'quote', 'offset', 'source', 'snapshot', 'empty', 'rationale'])
def test_rejects_unbound_or_fabricated_judgments(pinned, mutation):
    *_, root, packet, response = pinned
    verdict = response['verdicts'][0]
    if mutation == 'missing': response['verdicts'] = []
    elif mutation in ('extra', 'duplicate'): response['verdicts'].append(copy.deepcopy(verdict))
    elif mutation == 'identity': verdict['claim_id'] = 'other'
    elif mutation == 'hash': verdict['claim_sha256'] = 'wrong'
    elif mutation == 'text': verdict['text'] += ' without a caveat'
    elif mutation == 'packet': response['packet_sha256'] = 'old'
    elif mutation == 'quote': verdict['evidence'][0]['quote'] = 'fabricated'
    elif mutation == 'offset': verdict['evidence'][0]['start'] = True
    elif mutation == 'source': verdict['evidence'][0]['url'] = 'https://other.example/'
    elif mutation == 'snapshot': verdict['evidence'][0]['snapshot_sha256'] = 'old'
    elif mutation == 'empty': verdict['evidence'] = []
    elif mutation == 'rationale': verdict['rationale'] = 'yes'
    with pytest.raises(ValueError): gate.validate(packet, response, root)


def test_duplicate_claims_and_mutated_snapshots_fail(pinned):
    _shared, manifest, doc, root, packet, response = pinned
    doc['claims'].append(copy.deepcopy(doc['claims'][0]))
    with pytest.raises(ValueError, match='duplicate'): gate.claim_rows(manifest, {'durability': doc})
    source = next(iter(packet['sources'].values()))
    (root / source['file']).write_text('changed')
    with pytest.raises(ValueError, match='snapshot changed'): gate.validate(packet, response, root)


def test_dissent_is_never_rewritten_as_support(pinned):
    *_, root, packet, response = pinned
    response['verdicts'][0]['verdict'] = 'CONTRADICTED'
    assert not gate.validate(packet, response, root)['all_supported']


def test_completion_rejects_changed_claims_and_selection(pinned):
    shared, manifest, doc, root, packet, response = pinned
    run = root.parent
    destination = run / 'gate/attempts/one'
    destination.parent.mkdir(parents=True)
    root.rename(destination)
    (destination / 'verdicts.json').write_text(json.dumps(response))
    shared.run_dir = lambda slug: run
    manifest['gate'] = {**gate.validate(packet, response, destination), 'attempt': 'gate/attempts/one'}
    assert gate.verify_current(shared, manifest)['all_supported']
    doc['claims'][0]['text'] += ' corrected'
    with pytest.raises(ValueError, match='claims changed'): gate.verify_current(shared, manifest)
    doc['claims'][0]['text'] = packet['claims'][0]['text']
    manifest['depth'] = 'quick'
    with pytest.raises(ValueError, match='selection or depth'): gate.verify_current(shared, manifest)
    manifest['gate']['is_error'] = True
    with pytest.raises(ValueError, match='validated'): gate.verify_current(shared, manifest)
