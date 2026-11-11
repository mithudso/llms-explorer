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


@pytest.mark.parametrize('corruption', ['missing-identifier', 'wrong-quote', 'wrong-hash', 'wrong-text'])
def test_valid_sibling_survives_an_invalid_returned_judgment(case, corruption):
    shared, manifest, doc, root = case
    doc['claims'].append({**doc['claims'][0], 'text':'The cursor field includes pinned cursors.'})
    old = root / 'gate/attempts/first'
    packet = gate.prepare(shared, manifest, old, 0, 0)
    verdicts = response(packet)
    bad = verdicts['verdicts'][0]
    if corruption == 'missing-identifier':
        source = bad['evidence'][0]['quote']
        bad['evidence'][0].update(start=source.index('field counts'), quote=source[source.index('field counts'):])
    elif corruption == 'wrong-quote': bad['evidence'][0]['quote'] += ' invented'
    elif corruption == 'wrong-hash': bad['evidence'][0]['snapshot_sha256'] = 'false'
    else: bad['text'] += ' silently substituted'
    with pytest.raises(ValueError):
        gate.validate(packet, verdicts, old)
    partial = gate.validate(packet, verdicts, old, allow_partial=True)
    assert not partial['validated'] and not partial['all_supported']
    assert partial['rejected_judgment_ids'] == [packet['claims'][0]['claim_id']]
    (old / 'verdicts.json').write_text(json.dumps(verdicts))
    (old / 'validation.json').write_text(json.dumps({'validated':False, 'is_error':True,
                                                  'packet_sha256':packet['packet_sha256']}))
    current = gate.prepare(shared, manifest, root / 'gate/attempts/repaired', 0, 0)
    assert [row['claim_id'] for row in current['reused_verdicts']] == [packet['claims'][1]['claim_id']]
    assert 'reused_conflict_review' not in current
    doc['claims'][1]['text'] = 'Changed source claim needs its own review.'
    assert gate.prepare(shared, manifest, root / 'gate/attempts/changed', 0, 0)['reused_verdicts'] == []


@pytest.mark.parametrize('corruption', ['packet-hash', 'response-hash', 'duplicate-id', 'missing-conflict-review'])
def test_partial_reuse_still_rejects_broken_packet_or_response_envelope(case, corruption):
    shared, manifest, doc, root = case
    doc['claims'].append({**doc['claims'][0], 'text':'Open cursors include pinned cursors.'})
    old = root / 'gate/attempts/first'
    packet = gate.prepare(shared, manifest, old, 0, 0)
    verdicts = response(packet)
    if corruption == 'packet-hash': packet['coverage']['total_claims'] += 1
    elif corruption == 'response-hash': verdicts['packet_sha256'] = 'false'
    elif corruption == 'duplicate-id': verdicts['verdicts'][1] = copy.deepcopy(verdicts['verdicts'][0])
    else: verdicts.pop('conflict_reviewed_claim_ids')
    (old / 'packet.json').write_text(json.dumps(packet))
    (old / 'verdicts.json').write_text(json.dumps(verdicts))
    (old / 'validation.json').write_text(json.dumps({'validated':False, 'is_error':True,
                                                  'packet_sha256':packet['packet_sha256']}))
    current = gate.prepare(shared, manifest, root / 'gate/attempts/repaired', 0, 0)
    assert current['reused_verdicts'] == []


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
    shared, manifest, _doc, root = case
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



@pytest.mark.parametrize('statement,source,allowed', [
    ('The dependency v3.18.1 is required.', 'The dependency v3.18.1 is required.', True),
    ('The dependency v3.18.1 is required.', 'The dependency v3.18.2 is required.', False),
    ('The dependency v3.18.1 is required.', 'The dependency suffix 18.1 is required.', False),
    ('The dependency v3.18.1 is required.', 'The dependency 3.18.1 is required.', False),
    ('The dependency v3.18.1 is required.', 'The dependency v3.18.1.4 is required.', False),
    ('The dependency v3.18.1 is required.', 'The dependency v3.18.10 is required.', False),
    ('The dependency v3.18.1 is required.', 'The dependency xv3.18.1 is required.', False),
    ('The dependency v3.18.1 is required.', 'The dependency v3.18.1Extra is required.', False),
    ('The dependency v3.18.1 is required.', 'The dependency x.v3.18.1 is required.', False),
    ('The dependency v3.18.1 is required.', 'The dependency v3.18.1-rc.1 is required.', False),
    ('The dependency v3.18.1 is required.', 'The dependency v3.18.1+build.1 is required.', False),
    ('The dependency v3.18.1-rc.1 is required.', 'The dependency v3.18.1-rc.1 is required.', True),
    ('The dependency v3.18.1-rc.1 is required.', 'The dependency v3.18.1-rc.2 is required.', False),
    ('The dependency v3.18.1-rc.1+build.1 is required.', 'The dependency v3.18.1-rc.1+build.1 is required.', True),
    ('The dependency v3.18.1-rc.1+build.1 is required.', 'The dependency v3.18.1-rc.1+build.2 is required.', False),
    ('The dependency V3.18.1 is required.', 'The dependency V3.18.1 is required.', True),
    ('The dependency v3.18.1 is required.', 'The dependency V3.18.1 is required.', False),
    ('Use v3.18.1 with V4.2 and standalone 18.1.', 'Use v3.18.1 with V4.2 and standalone 18.1.', True),
    ('Use v3.18.1 with V4.2 and standalone 18.1.', 'Use v3.18.1 with V4.3 and standalone 18.1.', False),
    ('Use v3.18.1 with V4.2 and standalone 18.1.', 'Use v3.18.1 with V4.2 and standalone 18.2.', False),
    ('The limit is 18.1.', 'The limit is 18.1.', True),
    ('The limit is 18.1.', 'The dependency v3.18.1 is required.', False),
    ('The limit is 18.1.', 'The limit is 118.1.', False),
    ('Use v3.18.1 with 2.5ms and 25%.', 'Use v3.18.1 with 2.5ms and 25%.', True),
    ('Use v3.18.1 with 2.5ms and 25%.', 'Use v3.18.1 with 2.5s and 25%.', False),
    ('Use v3.18.1 with 2.5ms and 25%.', 'Use v3.18.1 with 2.5ms and 125%.', False),
    ('Use v3.18.1 with numIdleCursors.', 'Use v3.18.1 with numIdleCursorsExtra.', False),
])
def test_prefixed_version_literals_and_ordinary_numbers(case, statement, source, allowed):
    shared, manifest, doc, root = case
    body = root / 'source.txt'
    body.write_text(source)
    doc['claims'][0]['text'] = statement
    doc['claims'][0]['evidence'][0].update(quote=source, end=len(source), snapshot_sha256=gate.digest(body.read_bytes()))
    if allowed:
        packet = gate.prepare(shared, manifest, root / 'attempt', 0, 0)
        assert gate.validate(packet, response(packet), root / 'attempt')['all_supported']
    else:
        with pytest.raises(ValueError, match='identifiers or numbers'):
            gate.prepare(shared, manifest, root / 'attempt', 0, 0)



@pytest.mark.parametrize('reviewer', [False, True], ids=['authored', 'reviewer'])
@pytest.mark.parametrize('source,start,end', [
    ('The dependency v3.18.10 is required.', 0, 22),
    ('The dependency v3.18.1.4 is required.', 0, 22),
    ('The dependency v3.18.1-rc.1 is required.', 0, 22),
    ('The dependency v3.18.1+build.1 is required.', 0, 22),
    ('The dependency v3.18.1Extra is required.', 0, 22),
    ('xv3.18.1 is required with advanced support.', 1, None),
    ('x.v3.18.1 is required with advanced support.', 2, None),
])
def test_quote_edges_cannot_fabricate_complete_version_tokens(case, source, start, end, reviewer):
    shared, manifest, doc, root = case
    end = len(source) if end is None else end
    # The real version elsewhere must not rescue the selected, cropped span.
    source += ' A supported dependency v3.18.1 is required.'
    body = root / 'source.txt'
    body.write_text(source)
    doc['claims'][0]['text'] = 'The dependency v3.18.1 is required.'
    evidence = doc['claims'][0]['evidence'][0]
    evidence.update(quote=source, end=len(source), snapshot_sha256=gate.digest(body.read_bytes()))
    cropped = {**evidence, 'quote': source[start:end], 'start': start, 'end': end}
    if reviewer:
        packet = gate.prepare(shared, manifest, root / 'attempt', 0, 0)
        verdicts = response(packet)
        verdicts['verdicts'][0]['evidence'] = [cropped]
        with pytest.raises(ValueError, match='identifiers or numbers'):
            gate.validate(packet, verdicts, root / 'attempt')
    else:
        doc['claims'][0]['evidence'] = [cropped]
        with pytest.raises(ValueError, match='identifiers or numbers'):
            gate.prepare(shared, manifest, root / 'attempt', 0, 0)


def test_complete_version_inside_a_partial_source_quote_still_passes(case):
    shared, manifest, doc, root = case
    sentence = 'The dependency v3.18.1 is required.'
    source = 'Other context. ' + sentence + ' More context.'
    start = source.index(sentence)
    end = start + len(sentence)
    body = root / 'source.txt'
    body.write_text(source)
    doc['claims'][0]['text'] = sentence
    doc['claims'][0]['evidence'][0].update(quote=source[start:end], start=start, end=end,
                                         snapshot_sha256=gate.digest(body.read_bytes()))
    packet = gate.prepare(shared, manifest, root / 'attempt', 0, 0)
    assert gate.validate(packet, response(packet), root / 'attempt')['all_supported']


def test_supported_judgment_cannot_substitute_a_version_suffix(case):
    shared, manifest, doc, root = case
    source = 'The dependency v3.18.1 is required. The standalone suffix 18.1 is unrelated.'
    body = root / 'source.txt'
    body.write_text(source)
    doc['claims'][0]['text'] = 'The dependency v3.18.1 is required.'
    doc['claims'][0]['evidence'][0].update(quote=source, end=len(source), snapshot_sha256=gate.digest(body.read_bytes()))
    packet = gate.prepare(shared, manifest, root / 'attempt', 0, 0)
    verdicts = response(packet)
    start = source.index('The standalone')
    verdicts['verdicts'][0]['evidence'][0].update(start=start, quote=source[start:])
    with pytest.raises(ValueError, match='identifiers or numbers'):
        gate.validate(packet, verdicts, root / 'attempt')



@pytest.mark.parametrize('verdict', ['CONTRADICTED', 'NOT-IN-SOURCE', 'UNVERIFIED'])
def test_version_literal_coverage_does_not_override_negation_dissent(case, verdict):
    shared, manifest, doc, root = case
    source = 'The dependency v3.18.1 never retries writes.'
    body = root / 'source.txt'
    body.write_text(source)
    doc['claims'][0]['text'] = 'The dependency v3.18.1 retries writes.'
    doc['claims'][0]['evidence'][0].update(quote=source, end=len(source), snapshot_sha256=gate.digest(body.read_bytes()))
    packet = gate.prepare(shared, manifest, root / 'attempt', 0, 0)
    verdicts = response(packet)
    verdicts['verdicts'][0].update(verdict=verdict, rationale='The source negates the claimed retry behavior.')
    report = gate.validate(packet, verdicts, root / 'attempt')
    assert not report['all_supported']
    assert report['counts'] == {verdict: 1}


def test_format_retry_budget_cannot_be_reset_by_repeating_the_command(case):
    shared, manifest, _doc, root = case
    shared._create_run = lambda *args, **kwargs: manifest
    shared.load_manifest = lambda slug: manifest
    shared.save_manifest = lambda value: None
    shared.run_lock = lambda slug: nullcontext()
    shared._now = lambda: '2026-11-02T00:00:00Z'
    shared._print = lambda value: None
    calls = []
    def judge(*args):
        attempts = sorted((root / 'gate/attempts').glob('*'))
        (attempts[-1] / 'verdicts.json').write_text('{broken')
        calls.append(True)
        return {'is_error':False}
    shared.run_agent = judge
    gate.install(shared)
    args = SimpleNamespace(slug='test', sample=None, dry_run=False, refetch_cap=0,
                           model=None, effort=None, max_turns=5, agent_timeout=30)
    assert shared.cmd_gate(args) == 1
    assert len(calls) == 2
    assert shared.cmd_gate(args) == 1
    assert len(calls) == 2


@pytest.mark.parametrize('token', ['$setOnInsert', '$$setOnInsert', '$$ROOT', '$field_name',
                                    '$setOnInsert.field', '$field2', '0x05', '0xDE', '0XAF'])
def test_complete_prefixed_and_hexadecimal_literals_pass(case, token):
    shared, manifest, doc, root = case
    source = f'Pinned source evidence: {token} is the retained token in this source body.'
    body = root / 'source.txt'
    body.write_text(source)
    doc['claims'][0]['text'] = f'The `{token}` token is retained.'
    doc['claims'][0]['evidence'][0].update(quote=source, end=len(source), snapshot_sha256=gate.digest(body.read_bytes()))
    packet = gate.prepare(shared, manifest, root / 'attempt', 'all', 0)
    assert gate.validate(packet, response(packet), root / 'attempt')['all_supported']


@pytest.mark.parametrize('claim_token,source_token', [
    ('$setOnInsert', '$$setOnInsert'), ('$setOnInsert', '$$$setOnInsert'),
    ('$setOnInsert', '$setOnInsertExtra'), ('$setOnInsert', '$setOnInsert_extra'),
    ('$setOnInsert', '$setOnInsert.field'), ('$setOnInsert', '$setOnInserté'),
    ('$setOnInsert', 'é$setOnInsert'), ('$setOnInsert', 'x$setOnInsert'),
    ('setOnInsert', '$setOnInsert'), ('0x05', '0x050'), ('0x05', '0x05F'),
    ('0x05', '0x15'), ('0x05', '0X05'), ('0x05', 'x0x05'), ('0x05', 'é0x05'),
    ('0x05', '$0x05'), ('0x05', 'x.0x05'), ('0x05', '0x05é'),
    ('0x05', '0x05_suffix'), ('0x05', '0x05.value'), ('0x05', '0x05.1'),
    ('5', '0x05'), ('5', '512'), ('numIdleCursors', 'numIdleCursorsExtra'),
])
def test_prefixed_and_hexadecimal_literals_require_exact_full_tokens(case, claim_token, source_token):
    shared, manifest, doc, root = case
    source = f'Pinned source evidence: {source_token} is the retained token in this source body.'
    body = root / 'source.txt'
    body.write_text(source)
    doc['claims'][0]['text'] = f'The `{claim_token}` token is retained.'
    doc['claims'][0]['evidence'][0].update(quote=source, end=len(source), snapshot_sha256=gate.digest(body.read_bytes()))
    with pytest.raises(ValueError, match='identifiers or numbers'):
        gate.prepare(shared, manifest, root / 'attempt', 'all', 0)


@pytest.mark.parametrize('reviewer', [False, True], ids=['authored', 'reviewer'])
@pytest.mark.parametrize('token,source_token,crop_prefix', [
    ('$setOnInsert', '$$setOnInsert', True), ('$setOnInsert', 'é$setOnInsert', True),
    ('$setOnInsert', 'x$setOnInsert', True), ('$setOnInsert', '$setOnInsertExtra', False),
    ('0x05', 'x0x05', True), ('0x05', 'é0x05', True), ('0x05', '$0x05', True),
    ('0x05', '0x050', False), ('0x05', '0x05F', False), ('0x05', '0x05_suffix', False),
])
def test_quote_edges_cannot_create_prefixed_or_hexadecimal_token_boundaries(case, token, source_token, crop_prefix, reviewer):
    shared, manifest, doc, root = case
    selected = f'Pinned source evidence: {source_token} is the retained token in this source body.'
    source = selected + f' Outside the cited span: {token} is also documented.'
    start = selected.index(token) if crop_prefix else 0
    end = len(selected) if crop_prefix else selected.index(token) + len(token)
    body = root / 'source.txt'
    body.write_text(source)
    doc['claims'][0]['text'] = f'The `{token}` token is retained.'
    span = doc['claims'][0]['evidence'][0]
    span.update(quote=source, end=len(source), snapshot_sha256=gate.digest(body.read_bytes()))
    cropped = {**span, 'start': start, 'end': end, 'quote': source[start:end]}
    if reviewer:
        packet = gate.prepare(shared, manifest, root / 'attempt', 'all', 0)
        verdicts = response(packet)
        verdicts['verdicts'][0]['evidence'] = [cropped]
        with pytest.raises(ValueError, match='identifiers or numbers'):
            gate.validate(packet, verdicts, root / 'attempt')
    else:
        doc['claims'][0]['evidence'] = [cropped]
        with pytest.raises(ValueError, match='identifiers or numbers'):
            gate.prepare(shared, manifest, root / 'attempt', 'all', 0)


def test_hex_values_do_not_mask_other_decimal_version_or_identifier_details(case):
    shared, manifest, doc, root = case
    statement = 'Use 0x05 with v3.18.1, 2.5ms, 25% and numIdleCursors field.'
    body = root / 'source.txt'
    doc['claims'][0]['text'] = statement
    for source in [statement, statement.replace('2.5ms', '2.5s'), statement.replace('25%', '125%'),
                   statement.replace('v3.18.1', 'v3.18.10'), statement.replace('numIdleCursors', 'numIdleCursorsExtra')]:
        body.write_text(source)
        doc['claims'][0]['evidence'][0].update(quote=source, end=len(source), snapshot_sha256=gate.digest(body.read_bytes()))
        if source == statement:
            packet = gate.prepare(shared, manifest, root / 'attempt', 'all', 0)
            assert gate.validate(packet, response(packet), root / 'attempt')['all_supported']
        else:
            with pytest.raises(ValueError, match='identifiers or numbers'):
                gate.prepare(shared, manifest, root / 'attempt', 'all', 0)


@pytest.mark.parametrize('reviewer', [False, True], ids=['authored', 'reviewer'])
@pytest.mark.parametrize('statement,token,source_token,crop_prefix', [
    ('The limit is 5.', '5', '512', False),
    ('The field is numIdleCursors.', 'numIdleCursors', 'numIdleCursorsExtra', False),
    ('The field is metrics.idle.', 'metrics.idle', 'metrics.idleExtra', False),
    ('The limit is 5.', '5', 'é5', True),
    ('The limit is 5.', '5', '5é', False),
    ('The field is numIdleCursors.', 'numIdleCursors', 'énumIdleCursors', True),
    ('The field is numIdleCursors.', 'numIdleCursors', 'numIdleCursorsé', False),
    ('The field is metrics.idle.', 'metrics.idle', 'émetrics.idle', True),
    ('The field is metrics.idle.', 'metrics.idle', 'metrics.idleé', False),
    ('The limit is 2.5ms.', '2.5ms', '2.5msExtra', False),
])
def test_ordinary_tokens_use_full_source_boundaries_at_quote_edges(case, statement, token, source_token, crop_prefix, reviewer):
    shared, manifest, doc, root = case
    selected = f'The documented token is {source_token} and remains stable in this source.'
    # A correct occurrence outside the selected citation cannot rescue a crop.
    source = selected + f' Complete correct token: {token} is documented elsewhere.'
    start = selected.index(token) if crop_prefix else 0
    end = len(selected) if crop_prefix else selected.index(token) + len(token)
    body = root / 'source.txt'
    body.write_text(source)
    doc['claims'][0]['text'] = statement
    span = doc['claims'][0]['evidence'][0]
    span.update(quote=source, end=len(source), snapshot_sha256=gate.digest(body.read_bytes()))
    cropped = {**span, 'start': start, 'end': end, 'quote': source[start:end]}
    if reviewer:
        packet = gate.prepare(shared, manifest, root / 'attempt', 'all', 0)
        verdicts = response(packet)
        verdicts['verdicts'][0]['evidence'] = [cropped]
        with pytest.raises(ValueError, match='identifiers or numbers'):
            gate.validate(packet, verdicts, root / 'attempt')
    else:
        doc['claims'][0]['evidence'] = [cropped]
        with pytest.raises(ValueError, match='identifiers or numbers'):
            gate.prepare(shared, manifest, root / 'attempt', 'all', 0)


@pytest.mark.parametrize('reviewer', [False, True], ids=['authored', 'reviewer'])
@pytest.mark.parametrize('cross_source', [False, True], ids=['one-source', 'cross-source'])
def test_one_literal_cannot_be_synthesized_across_evidence_spans(case, reviewer, cross_source):
    shared, manifest, doc, root = case
    # Joining these two exact quotes with a newline would fabricate the backtick literal.
    first = 'First fragment is sufficiently long'
    second = 'Second fragment is also sufficiently long'
    literal = first + '\n' + second
    if cross_source:
        texts = {'https://example.org/first': first + ' original suffix',
                 'https://example.org/second': 'original prefix ' + second,
                 'https://example.org/complete': literal}
    else:
        texts = {'https://example.org/first': first + ' unrelated middle ' + second + '\n' + literal}
    metadata, fragments = {}, []
    for index, (url, text) in enumerate(texts.items()):
        body = root / f'split-source-{index}.txt'
        body.write_text(text)
        metadata[url] = {'id': f'src:split{index}', 'url': url, 'text_path': str(body), 'sha256': gate.digest(body.read_bytes())}
    for url, fragment in [('https://example.org/first', first),
                          ('https://example.org/second' if cross_source else 'https://example.org/first', second)]:
        meta = metadata[url]
        text = Path(meta['text_path']).read_text()
        start = text.index(fragment)
        fragments.append({'url': url, 'source_id': meta['id'], 'snapshot_sha256': meta['sha256'],
                          'start': start, 'end': start + len(fragment), 'quote': fragment, 'extraction_status': 'complete'})
    shared.lib_find = lambda url: metadata[url]
    shared.source_id = lambda url: metadata[url]['id']
    doc['claims'][0].update(text=f'The exact phrase is `{literal}`.', sources=list(metadata))
    doc['claims'][0]['evidence'] = [{**fragment} for fragment in fragments]
    if reviewer:
        # Prepare with a complete real occurrence, then let the reviewer select only fragments.
        url = 'https://example.org/complete' if cross_source else 'https://example.org/first'
        meta = metadata[url]
        text = Path(meta['text_path']).read_text()
        start = text.index(literal)
        doc['claims'][0]['evidence'] = [{'url': url, 'source_id': meta['id'], 'snapshot_sha256': meta['sha256'],
            'start': start, 'end': start + len(literal), 'quote': literal, 'extraction_status': 'complete'}]
        packet = gate.prepare(shared, manifest, root / 'attempt', 'all', 0)
        verdicts = response(packet)
        verdicts['verdicts'][0]['evidence'] = fragments
        with pytest.raises(ValueError, match='identifiers or numbers'):
            gate.validate(packet, verdicts, root / 'attempt')
    else:
        with pytest.raises(ValueError, match='identifiers or numbers'):
            gate.prepare(shared, manifest, root / 'attempt', 'all', 0)


@pytest.mark.parametrize('reviewer', [False, True], ids=['authored', 'reviewer'])
def test_separate_complete_literals_may_use_different_cited_sources(case, reviewer):
    shared, manifest, doc, root = case
    texts = {'https://example.org/first': 'The numIdleCursors field has a limit of 5.',
             'https://example.org/second': 'The metrics.idle field has a latency of 2.5ms and a threshold of 25%.'}
    metadata, spans = {}, []
    for index, (url, text) in enumerate(texts.items()):
        body = root / f'complete-source-{index}.txt'
        body.write_text(text)
        meta = {'id': f'src:complete{index}', 'url': url, 'text_path': str(body), 'sha256': gate.digest(body.read_bytes())}
        metadata[url] = meta
        spans.append({'url': url, 'source_id': meta['id'], 'snapshot_sha256': meta['sha256'],
                      'start': 0, 'end': len(text), 'quote': text, 'extraction_status': 'complete'})
    shared.lib_find = lambda url: metadata[url]
    shared.source_id = lambda url: metadata[url]['id']
    doc['claims'][0].update(text='The numIdleCursors field has a limit of 5; the metrics.idle field has a latency of 2.5ms and a threshold of 25%.',
                            sources=list(metadata), evidence=spans)
    packet = gate.prepare(shared, manifest, root / 'attempt', 'all', 0)
    if reviewer:
        assert gate.validate(packet, response(packet), root / 'attempt')['all_supported']
    else:
        assert gate.preflight(packet, root / 'attempt') == []


@pytest.mark.parametrize('token,source', [
    ('5', 'The numeric limit is 5.'), ('2.5ms', 'The latency is (2.5ms).'),
    ('25%', 'The threshold is 25%; this is documented.'),
    ('numIdleCursors', 'The field is (numIdleCursors), with ordinary punctuation.'),
    ('metrics.idle', 'The field is [metrics.idle]; this is documented.'),
    ('numIdleCursors', 'The field is «numIdleCursors» with Unicode punctuation.'),
    ('metrics.idle', 'The field is metrics.idle—documented with Unicode punctuation.'),
])
def test_complete_ordinary_terms_keep_valid_punctuation(case, token, source):
    shared, manifest, doc, root = case
    body = root / 'source.txt'
    body.write_text(source)
    doc['claims'][0]['text'] = f'The {token} term is documented.'
    doc['claims'][0]['evidence'][0].update(quote=source, end=len(source), snapshot_sha256=gate.digest(body.read_bytes()))
    packet = gate.prepare(shared, manifest, root / 'attempt', 'all', 0)
    assert gate.validate(packet, response(packet), root / 'attempt')['all_supported']


@pytest.mark.parametrize('token', ['1e6', '1E6', '1e+6', '1e-6', '1.5e3', '10_000', '1_000.25', '1e6ms'])
def test_complete_scientific_and_grouped_numeric_literals_pass(case, token):
    shared, manifest, doc, root = case
    source = 'The configured threshold is ' + token + ' operations.'
    body = root / 'source.txt'
    body.write_text(source)
    doc['claims'][0]['text'] = source
    doc['claims'][0]['evidence'][0].update(
        quote=source, end=len(source), snapshot_sha256=gate.digest(body.read_bytes()))
    packet = gate.prepare(shared, manifest, root / 'attempt', 0, 0)
    assert gate.validate(packet, response(packet), root / 'attempt')['all_supported']


@pytest.mark.parametrize('claim_token,source_token', [
    ('1e6', '1e60'), ('1e6', '11e6'), ('1e6', '1e6ms'),
    ('10_000', '10_0000'), ('10_000', '110_000'), ('1', '1e6'),
    ('1e6', '1e+6'), ('10_000', '10000'),
])
def test_numeric_literal_support_still_requires_exact_boundaries(case, claim_token, source_token):
    shared, manifest, doc, root = case
    source = 'The configured threshold is ' + source_token + ' operations.'
    body = root / 'source.txt'
    body.write_text(source)
    doc['claims'][0]['text'] = 'The configured threshold is ' + claim_token + ' operations.'
    doc['claims'][0]['evidence'][0].update(
        quote=source, end=len(source), snapshot_sha256=gate.digest(body.read_bytes()))
    with pytest.raises(ValueError, match='identifiers or numbers'):
        gate.prepare(shared, manifest, root / 'attempt', 0, 0)
