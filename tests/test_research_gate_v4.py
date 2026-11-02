"""Reject source-name matches and cheap structural failures before a paid review."""
import copy
import importlib.util
import json
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location('strict_gate', Path(__file__).resolve().parents[1] / 'scripts/research_gate.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


@pytest.fixture
def case(tmp_path):
    text = 'The `serverStatus.metrics.cursor.open.total` field counts open cursors, including pinned cursors.'
    body = tmp_path / 'source.txt'
    body.write_text(text)
    url = 'https://example.org/serverStatus'
    evidence = {'url':url, 'source_id':'src:one', 'snapshot_sha256':gate.digest(text.encode()),
                'start':0, 'end':len(text), 'quote':text, 'extraction_status':'complete'}
    doc = {'concept':'Cursors', 'claims':[{'text':text, 'sources':[url], 'confidence':'high', 'evidence':[evidence]}]}
    manifest = {'slug':'test', 'gate_contract_version':4, 'depth':'quick',
                'concepts':[{'name':'Cursors', 'slug':'cursors', 'status':'done'}]}
    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)
    shared = SimpleNamespace(load_claims=lambda *args:{'cursors':doc}, atomic_write=write,
        run_dir=lambda slug:tmp_path, source_id=lambda url:'src:one',
        lib_find=lambda url:{'url':url,'id':'src:one','text_path':str(body),'sha256':gate.digest(body.read_bytes())})
    return shared, manifest, doc, tmp_path


def response(packet):
    return {'schema':gate.STRICT_SCHEMA, 'packet_sha256':packet['packet_sha256'],
        'conflict_reviewed_claim_ids':[row['claim_id'] for row in packet['claims']], 'conflicts':[], 'verdicts':[
        {**{k:row[k] for k in ('claim_id','claim_sha256','text')},'verdict':'SUPPORTED',
         'rationale':'The read source establishes the identifier and its entire behavior.',
         'evidence':copy.deepcopy(row['evidence'])} for row in packet['claims']]}


def test_quick_checks_every_ordinary_claim_and_pins_authored_evidence(case):
    shared, manifest, doc, root = case
    doc['claims'].append({**doc['claims'][0], 'text':'Open cursors include pinned cursors.'})
    packet = gate.prepare(shared, manifest, root / 'attempt', 0, 0)
    assert packet['coverage']['selected_claims'] == 2
    assert gate.validate(packet, response(packet), root / 'attempt')['all_supported']
    prior = gate.claim_rows(manifest, {'cursors':doc})[0]['claim_id']
    doc['claims'][0]['evidence'][0]['extraction_status'] = 'incomplete'
    assert gate.claim_rows(manifest, {'cursors':doc})[0]['claim_id'] != prior


@pytest.mark.parametrize('failure', ['no-span','incomplete','wrong-source','wrong-hash','wrong-quote','missing-field','missing-number','conflict','omitted'])
def test_preflight_rejects_before_any_model(case, failure):
    shared, manifest, doc, root = case
    claim = doc['claims'][0]
    span = claim['evidence'][0]
    if failure == 'no-span': claim['evidence'] = []
    elif failure == 'incomplete': span['extraction_status'] = 'unknown'
    elif failure == 'wrong-source': span['url'] = 'https://other.example'
    elif failure == 'wrong-hash': span['snapshot_sha256'] = 'false'
    elif failure == 'wrong-quote': span['quote'] += ' invented'
    elif failure == 'missing-field': claim['text'] = 'The `serverStatus.missing.field` field counts open cursors.'
    elif failure == 'missing-number': claim['text'] = 'The cursor limit is 99.'
    elif failure == 'conflict': claim['conflict'] = {'status':'unresolved'}
    elif failure == 'omitted':
        body = root / 'source.txt'
        body.write_text(body.read_text() + '\n[truncated]')
        span['snapshot_sha256'] = gate.digest(body.read_bytes())
    with pytest.raises(ValueError, match='claim preflight failed'):
        gate.prepare(shared, manifest, root / 'attempt', 0, 0)
    failures = json.loads((root / 'attempt/preflight.json').read_text())['failures']
    assert len(failures) == 1 and failures[0]['claim_id'].startswith('clm:')


def test_semantic_supported_cannot_override_missing_field(case):
    shared, manifest, doc, root = case
    packet = gate.prepare(shared, manifest, root / 'attempt', 0, 0)
    verdicts = response(packet)
    # A model chooses a genuine but irrelevant span which omits the field.
    source = doc['claims'][0]['evidence'][0]['quote']
    span = verdicts['verdicts'][0]['evidence'][0]
    span.update(start=source.index('field counts'), quote=source[source.index('field counts'):])
    with pytest.raises(ValueError, match='omits claim identifiers'):
        gate.validate(packet, verdicts, root / 'attempt')


def test_reuse_requires_unchanged_identity_and_real_snapshot(case):
    shared, manifest, doc, root = case
    old = root / 'gate/attempts/first'
    packet = gate.prepare(shared, manifest, old, 0, 0)
    verdicts = response(packet)
    gate.validate(packet, verdicts, old)
    (old / 'verdicts.json').write_text(json.dumps(verdicts))
    (old / 'validation.json').write_text(json.dumps({'validated':True, 'packet_sha256':packet['packet_sha256']}))
    manifest['gate'] = {'attempt':'gate/attempts/first', 'validated':True, 'is_error':False}
    second = gate.prepare(shared, manifest, root / 'gate/attempts/second', 0, 0)
    assert len(second['reused_verdicts']) == 1
    doc['claims'][0]['text'] = 'Open cursors include pinned cursors.'
    third = gate.prepare(shared, manifest, root / 'gate/attempts/third', 0, 0)
    assert third['reused_verdicts'] == []
    (old / packet['sources'][doc['claims'][0]['sources'][0]]['file']).write_text('tampered')
    assert gate.reusable_judgments(shared, manifest, second, root) == []


@pytest.mark.parametrize('claim', ['The field transactions.totalAborted is present.', 'The numIdleCursors field counts idle cursors.', 'The limit is 5.'])
def test_unquoted_identifiers_and_numeric_substrings_fail(case, claim):
    shared, manifest, doc, root = case
    doc['claims'][0]['text'] = claim
    if claim.endswith('5.'):
        body = root / 'source.txt'
        body.write_text('The limit is 512, with at least 15 entries.')
        doc['claims'][0]['evidence'][0].update(quote=body.read_text(), end=len(body.read_text()), snapshot_sha256=gate.digest(body.read_bytes()))
    with pytest.raises(ValueError, match='identifiers or numbers'):
        gate.prepare(shared, manifest, root / 'attempt', 0, 0)


def test_supported_judgments_survive_dissent_and_later_preflight_failures(case):
    shared, manifest, doc, root = case
    doc['claims'].append({**doc['claims'][0], 'text':'Open cursors include pinned cursors.'})
    old = root / 'gate/attempts/first'
    packet = gate.prepare(shared, manifest, old, 0, 0)
    verdicts = response(packet)
    verdicts['verdicts'][1].update(verdict='UNVERIFIED', evidence=[])
    report = gate.validate(packet, verdicts, old)
    assert not report['all_supported']
    (old / 'verdicts.json').write_text(json.dumps(verdicts))
    (old / 'validation.json').write_text(json.dumps({**report, 'is_error':True}))
    failed = root / 'gate/attempts/later-preflight'
    failed.mkdir()
    (failed / 'validation.json').write_text(json.dumps({'validated':False, 'is_error':True}))
    doc['claims'][1]['text'] = 'Pinned cursors are included in open cursor totals.'
    current = gate.prepare(shared, manifest, root / 'gate/attempts/repaired', 0, 0)
    assert [row['claim_id'] for row in current['reused_verdicts']] == [packet['claims'][0]['claim_id']]


def test_unchanged_failed_gate_refuses_another_paid_call_and_repairs_review_only_changed_claim(case):
    shared, manifest, doc, root = case
    doc['claims'].append({**doc['claims'][0], 'text':'Open cursors include pinned cursors.'})
    shared._create_run = lambda *args, **kwargs: manifest
    shared.load_manifest = lambda slug: manifest
    shared.save_manifest = lambda value: None
    shared.run_lock = lambda slug: nullcontext()
    shared._now = lambda: '2026-11-02T00:00:00Z'
    shared._print = lambda value: None
    shared._probe_claims_path = lambda *args: root / 'absent-probe'
    calls = []
    def judge(*args):
        attempt = max((root / 'gate/attempts').iterdir())
        packet = json.loads((attempt / 'packet.json').read_text())
        result = response(packet)
        reused = {row['claim_id'] for row in packet.get('reused_verdicts', [])}
        result['verdicts'] = [row for row in result['verdicts'] if row['claim_id'] not in reused]
        calls.append([row['claim_id'] for row in result['verdicts']])
        if len(calls) == 1:
            result['verdicts'][1].update(verdict='UNVERIFIED', evidence=[])
        (attempt / 'verdicts.json').write_text(json.dumps(result))
        return {'is_error':False}
    shared.run_agent = judge
    gate.install(shared)
    args = SimpleNamespace(slug='test', sample=None, dry_run=False, refetch_cap=0,
                           model=None, effort=None, max_turns=5, agent_timeout=30)
    assert shared.cmd_gate(args) == 1
    assert len(calls) == 1 and len(calls[0]) == 2
    assert shared.cmd_gate(args) == 1
    assert len(calls) == 1
    doc['claims'][1]['text'] = 'Pinned cursors are included in open cursor totals.'
    assert shared.cmd_gate(args) == 0
    assert len(calls) == 2 and len(calls[1]) == 1
    assert calls[0][0] not in calls[1]


def test_conflict_ledger_blocks_even_when_each_source_supports_its_claim(case):
    shared, manifest, doc, root = case
    packet = gate.prepare(shared, manifest, root / 'attempt', 0, 0)
    verdicts = response(packet)
    verdicts['conflicts'] = [{'claim_ids':[packet['claims'][0]['claim_id']], 'resolution':'unresolved',
                             'rationale':'The cited editions establish incompatible applicability rules.'}]
    assert not gate.validate(packet, verdicts, root / 'attempt')['all_supported']
    verdicts['conflicts'][0]['resolution'] = 'attributed'
    with pytest.raises(ValueError, match='attribution is absent'):
        gate.validate(packet, verdicts, root / 'attempt')
    verdicts.pop('conflict_reviewed_claim_ids')
    with pytest.raises(ValueError, match='conflict review'):
        gate.validate(packet, verdicts, root / 'attempt')


@pytest.mark.parametrize('statement,source,allowed', [
    ('The limit is 5.', 'The limit is 5.', True),
    ('The limit is 5.', 'The limit is 5.1.', False),
    ('The limit is 5.', 'The limit is 15.', False),
    ('The numIdleCursors field counts idle cursors.', 'The numIdleCursorsExtra field counts idle cursors.', False),
])
def test_literal_boundaries_preserve_sentence_punctuation(case, statement, source, allowed):
    shared, manifest, doc, root = case
    body = root / 'source.txt'
    body.write_text(source)
    doc['claims'][0]['text'] = statement
    doc['claims'][0]['evidence'][0].update(quote=source, end=len(source), snapshot_sha256=gate.digest(body.read_bytes()))
    if allowed:
        assert gate.prepare(shared, manifest, root / 'attempt', 0, 0)['schema'] == gate.STRICT_SCHEMA
    else:
        with pytest.raises(ValueError, match='identifiers or numbers'):
            gate.prepare(shared, manifest, root / 'attempt', 0, 0)
