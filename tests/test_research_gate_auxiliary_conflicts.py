"""Explicit prose attribution survives the native gate without changing legacy identities."""
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = _load('auxiliary_conflict_gate', 'research_gate.py')
artifact = _load('auxiliary_conflict_artifact', 'research_artifact.py')
URL = 'https://example.org/ledger'
BODY = (
    'The ledger publishes completed entries after the durable marker.\n'
    'Design notes require the marker before publication.\n'
    'Implementation checks the completed batch boundary.\n'
    'Fixture assertions require publication after the durable marker.\n'
)


def _span(text):
    start = BODY.index(text)
    return {
        'url': URL, 'source_id': 'src:ledger',
        'snapshot_sha256': gate.digest(BODY.encode()), 'start': start,
        'end': start + len(text), 'quote': text, 'extraction_status': 'complete',
    }


def _document():
    positions = [
        {'text': line, 'evidence': [_span(line)]}
        for line in BODY.splitlines()[1:]
    ]
    return {
        'concept': 'Ledger', 'summary': 'The ledger has source-defined publication conditions.',
        'sources': [{'url': URL}],
        'claims': [{
            'text': BODY.splitlines()[0], 'sources': [URL], 'confidence': 'high',
            'evidence': [_span(BODY.splitlines()[0])],
        }],
        'disagreements': [
            {
                'text': 'Publication conditions differ across the source positions.',
                'sources': [URL], 'evidence': [_span(BODY.splitlines()[1])],
            },
            {
                'text': 'Design notes, implementation and fixture assertions retain '
                        'their different publication conditions.',
                'sources': [URL], 'evidence': [copy.deepcopy(p['evidence'][0]) for p in positions],
                'conflict': {'status': 'attributed', 'positions': positions},
            },
        ],
        'open_questions': ['Which environment should be tested next?'],
    }


@pytest.fixture
def case(tmp_path):
    body = tmp_path / 'source.txt'
    body.write_text(BODY)
    document = _document()
    manifest = {
        'slug': 'test', 'topic': 'Ledger', 'gate_contract_version': 4, 'depth': 'quick',
        'concepts': [{'name': 'Ledger', 'slug': 'ledger', 'status': 'done'}],
    }

    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)

    shared = SimpleNamespace(
        HUB_DIR=tmp_path, concept_tree=SimpleNamespace(load_nodes=lambda path: []),
        slugify=lambda name: name.lower(), run_dir=lambda slug: tmp_path,
        load_claims=lambda *args: {'ledger': document}, atomic_write=write,
        source_id=lambda url: 'src:ledger',
        lib_find=lambda url: {
            'url': URL, 'id': 'src:ledger', 'text_path': str(body),
            'sha256': gate.digest(BODY.encode()),
        },
    )
    return shared, manifest, document, tmp_path


def _attribution(packet):
    return next(row for row in packet['claims'] if row.get('conflict') is not None)


def _response(packet):
    verdicts = []
    for row in packet['claims']:
        question = row.get('assertion_kind') == 'open_question'
        verdicts.append({
            **{key: row[key] for key in ('claim_id', 'claim_sha256', 'text')},
            'verdict': gate.NO_ASSERTION if question else 'SUPPORTED',
            'rationale': 'The synthetic evidence supports the complete attributed statement.'
                         if not question else 'This is a pure question without a factual premise.',
            'evidence': [] if question else copy.deepcopy(row.get('evidence') or [_span(BODY)]),
        })
    return {
        'schema': gate.STRICT_SCHEMA, 'packet_sha256': packet['packet_sha256'],
        'conflict_reviewed_claim_ids': [row['claim_id'] for row in packet['claims']],
        'conflicts': [{
            'claim_ids': [_attribution(packet)['claim_id']], 'resolution': 'attributed',
            'rationale': 'The canonical prose explicitly preserves all three attributed positions.',
        }],
        'verdicts': verdicts,
    }


def _save_review(shared, manifest, root):
    packet = gate.prepare(shared, manifest, root, 0, 0)
    response = _response(packet)
    report = gate.validate(packet, response, root)
    receipt = {
        **report, 'attempt': str(root.relative_to(shared.run_dir(manifest['slug']))),
        'is_error': False,
    }
    (root / 'verdicts.json').write_text(json.dumps(response))
    (root / 'validation.json').write_text(json.dumps(receipt))
    manifest['gate'] = receipt
    return packet, response, report


def test_prepare_transports_all_three_positions_and_independent_evidence(case):
    shared, manifest, document, base = case
    root = base / 'gate/attempts/first'
    packet = gate.prepare(shared, manifest, root, 0, 0)
    row = _attribution(packet)
    authored = document['disagreements'][1]
    assert len(row['conflict']['positions']) == 3
    assert row['conflict'] == authored['conflict']
    assert row['evidence'] == authored['evidence']
    assert json.loads((root / 'packet.json').read_text()) == packet
    assert gate.preflight(packet, root) == []
    assert gate.validate(packet, _response(packet), root)['all_supported']
    authored['conflict']['positions'][2]['evidence'][0]['quote'] = 'mutated author object'
    authored['evidence'][0]['quote'] = 'another author mutation'
    assert row['conflict']['positions'][2]['evidence'][0]['quote'] == BODY.splitlines()[3]
    assert row['evidence'][0]['quote'] == BODY.splitlines()[1]


@pytest.mark.parametrize('position', [0, 1, 2, None])
@pytest.mark.parametrize('failure', ['missing', 'wrong-quote', 'wrong-hash', 'incomplete'])
def test_each_position_and_top_assertion_require_exact_complete_evidence(case, position, failure):
    shared, manifest, document, base = case
    attributed = document['disagreements'][1]
    target = attributed if position is None else attributed['conflict']['positions'][position]
    if failure == 'missing':
        target.pop('evidence')
    elif failure == 'wrong-quote':
        target['evidence'][0]['quote'] += ' invented'
    elif failure == 'wrong-hash':
        target['evidence'][0]['snapshot_sha256'] = '0' * 64
    else:
        target['evidence'][0]['extraction_status'] = 'incomplete'
    root = base / 'gate/attempts/rejected'
    with pytest.raises(ValueError, match='claim preflight failed'):
        gate.prepare(shared, manifest, root, 0, 0)
    failures = json.loads((root / 'preflight.json').read_text())['failures']
    assert len(failures) == 1 and failures[0]['claim_id'].startswith('prose:')
    assert not (root / 'packet.json').exists()


@pytest.mark.parametrize('failure', [
    'malformed', 'unresolved', 'missing-status', 'missing-positions', 'one-position',
    'positions-not-list', 'missing-third-text',
])
def test_malformed_attribution_cannot_reach_review(case, failure):
    shared, manifest, document, base = case
    authored = document['disagreements'][1]
    conflict = authored['conflict']
    if failure == 'malformed':
        authored['conflict'] = 'attributed'
    elif failure == 'unresolved':
        conflict['status'] = 'unresolved'
    elif failure == 'missing-status':
        conflict.pop('status')
    elif failure == 'missing-positions':
        conflict.pop('positions')
    elif failure == 'one-position':
        conflict['positions'] = conflict['positions'][:1]
    elif failure == 'positions-not-list':
        conflict['positions'] = {}
    else:
        conflict['positions'][2].pop('text')
    with pytest.raises(ValueError, match='claim preflight failed'):
        gate.prepare(shared, manifest, base / 'gate/attempts/rejected', 0, 0)


def test_ordinary_and_evidence_only_legacy_ids_keep_the_prepatch_contract(case):
    _, manifest, document, _ = case
    rows = gate.claim_rows(manifest, {'ledger': document})
    unchanged = [row['claim_id'] for row in rows if row.get('conflict') is None]
    # Golden values were produced by the pre-patch native helper, not this implementation.
    assert unchanged == [
        'clm:50eeb3068ddd82f383e56ea438cf877b9fedcabc811b799b0791db063d98e458',
        'prose:42f108971c370f9d700f30e0cd5056ce08a2292ebbb156a092e8e142b7141061',
        'prose:9e88dd37aa9b64ac48865cd0755b7b60235451971e61793dce7e7ecc02ed77d3',
        'prose:9f283021f53efc1dc41aa12a40734e503e362d6183ad69904e72a2eaf5bf5103',
    ]
    document['summary_evidence'] = [{'quote': 'Ignored legacy bookkeeping.'}]
    document['disagreements'][0]['evidence'] = [{'quote': 'Other legacy bookkeeping.'}]
    document['disagreements'][0]['conflict'] = None
    assert [
        row['claim_id'] for row in gate.claim_rows(manifest, {'ledger': document})
        if row.get('conflict') is None
    ] == unchanged


@pytest.mark.parametrize('change', ['attribution', 'span'])
def test_changed_attribution_reuses_only_unchanged_judgments(case, change):
    shared, manifest, document, base = case
    before, old_response, _ = _save_review(shared, manifest, base / 'gate/attempts/first')
    authored = document['disagreements'][1]
    if change == 'attribution':
        authored['conflict']['positions'][2]['attribution'] = 'The source fixture.'
    else:
        authored['evidence'][0] = _span(BODY)
    root = base / 'gate/attempts/second'
    after = gate.prepare(shared, manifest, root, 0, 0)
    old, new = _attribution(before), _attribution(after)
    assert old['text'] == new['text']
    assert old['claim_id'] != new['claim_id']
    assert gate.assertion_review_binding(before, old) != gate.assertion_review_binding(after, new)
    unchanged_ids = {row['claim_id'] for row in before['claims']} - {old['claim_id']}
    assert {row['claim_id'] for row in after['claims']} - {new['claim_id']} == unchanged_ids
    assert {row['claim_id'] for row in after['reused_verdicts']} == unchanged_ids
    assert 'reused_conflict_review' not in after
    stale_response = copy.deepcopy(old_response)
    stale_response['packet_sha256'] = after['packet_sha256']
    stale_response['conflict_reviewed_claim_ids'] = [row['claim_id'] for row in after['claims']]
    stale_response['conflicts'][0]['claim_ids'] = [new['claim_id']]
    with pytest.raises(ValueError, match='unknown or duplicate claim ID'):
        gate.validate(after, stale_response, root)
    assert gate.validate(after, _response(after), root)['all_supported']


def test_attributed_artifact_roundtrip_rejects_resealed_metadata_tampering(case):
    shared, manifest, document, base = case
    _save_review(shared, manifest, base / 'gate/attempts/first')
    value, destination = artifact.build(shared, manifest, {'ledger': document}, 'COMPLETED')
    frozen = json.loads(destination.read_text())
    assert artifact.verify(frozen) == value
    assert frozen['documents']['ledger']['auxiliary_assertions'][2]['conflict'] == (
        document['disagreements'][1]['conflict']
    )
    frozen['documents']['ledger']['disagreements'][1]['conflict']['positions'][2][
        'attribution'
    ] = 'A different attribution.'
    frozen['artifact_sha256'] = artifact.digest({
        key: value for key, value in frozen.items() if key != 'artifact_sha256'
    })
    with pytest.raises(ValueError, match='auxiliary prose judgment'):
        artifact.verify(frozen)


def test_public_projection_keeps_approved_text_and_ids_without_private_evidence():
    authored = _document()['disagreements'][1]
    unit = {
        'id': 'prose:approved', 'text': authored['text'], 'source_url': URL,
        'validation_status': 'SUPPORTED', 'evidence_ids': ['ev:approved'],
        'conflict': authored['conflict'], 'evidence': authored['evidence'],
    }
    public = artifact.public_projection({
        'manifest.json': json.dumps({'concept': 'Ledger', 'slug': 'ledger'}),
        'units.jsonl': json.dumps(unit),
    })
    assert public['claims'] == [{
        key: unit[key] for key in ('id', 'text', 'source_url', 'validation_status', 'evidence_ids')
    }]
    serialized = json.dumps(public)
    assert 'positions' not in serialized and 'snapshot_sha256' not in serialized
    assert all(span['quote'] not in serialized for span in authored['evidence'])
