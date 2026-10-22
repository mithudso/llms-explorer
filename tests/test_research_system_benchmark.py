import copy
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('system_benchmark', Path(__file__).resolve().parents[1] / 'scripts/research_system_benchmark.py')
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


@pytest.fixture
def trial():
    text = 'A long reader prevents checkpoint completion until its snapshot is released.'
    packet = {'sources': [{'id': 'S1', 'text': text}], 'reference': {'reader': text}, 'reference_review_status': 'pending-human-review'}
    output = {'concepts': [{'id': 'c1', 'name': 'Reader boundary'}], 'claims': [
        {'id': 'f1', 'concept_id': 'c1', 'text': text, 'source_id': 'S1', 'quote': text}]}
    judged = {'output_sha256': bench.fingerprint(output), 'claims': [
        {'id': 'f1', 'text': text, 'verdict': 'SUPPORTED', 'atomic': True, 'duplicate_of': None, 'depth': 3, 'mechanism': True, 'reference_ids': ['reader']}],
        'concepts': [{'id': 'c1', 'canonical_name': 'Reader boundary', 'meaningful': True, 'in_scope': True}]}
    return packet, output, judged


def test_metrics_require_bound_full_statements_and_exact_quotes(trial):
    packet, output, judged = trial
    result = bench.metrics(output, judged, packet)
    assert (result['unique_supported_facts'], result['mechanisms'], result['mean_claim_depth']) == (1, 1, 3)
    assert result['reference_review_status'] == 'pending-human-review'
    judged['claims'][0]['text'] += ' extra unsupported scope'
    with pytest.raises(ValueError, match='substituted'): bench.metrics(output, judged, packet)


@pytest.mark.parametrize('change', ['duplicate', 'missing', 'stale', 'quote', 'contradiction'])
def test_failed_or_unsupported_judgments_never_inflate_quality(trial, change):
    packet, output, judged = trial
    if change == 'duplicate': judged['claims'].append(copy.deepcopy(judged['claims'][0]))
    elif change == 'missing': judged['claims'] = []
    elif change == 'stale': judged['output_sha256'] = 'old'
    elif change == 'quote':
        output['claims'][0]['quote'] = 'invented quote that is long enough'
        judged['output_sha256'] = bench.fingerprint(output)
    elif change == 'contradiction': judged['claims'][0]['verdict'] = 'CONTRADICTED'
    if change in ('duplicate', 'missing', 'stale'):
        with pytest.raises(ValueError): bench.metrics(output, judged, packet)
    else:
        assert bench.metrics(output, judged, packet)['unique_supported_facts'] == 0


def test_cost_estimates_do_not_double_count_cached_input():
    rates = {'input_per_million': 2, 'cached_input_per_million': 0.2, 'output_per_million': 8}
    assert bench.estimate_cost({'input_tokens': 1000000, 'cached_input_tokens': 500000, 'output_tokens': 100000}, rates) == 1.9
    assert bench.estimate_cost({}, None) is None
    with pytest.raises(ValueError): bench.estimate_cost({'input_tokens': 1, 'cached_input_tokens': 2}, rates)


@pytest.mark.parametrize('failed_stage', ['generation', 'judge', 'truncated-generation', 'invalid-judge'])
def test_resume_retries_only_failed_stages_and_preserves_attempts(tmp_path, monkeypatch, trial, failed_stage):
    packet, output, judged = trial
    bench.write(tmp_path / 'storage/packet.json', packet)
    destination = tmp_path / 'cells/storage__dr__gpt-6-luna__max__fixed'
    def success(value):
        return {'is_error': False, 'output': value, 'seconds': 1, 'usage': {}, 'tools': []}
    generation, judge = success(output), success(judged)
    if failed_stage in ('judge', 'invalid-judge'):
        bench.write(destination / 'generation/run.json', generation)
        failed = (success({**judged, 'output_sha256': 'stale'}) if failed_stage == 'invalid-judge'
                  else {'is_error': True, 'reason': 'capacity'})
        bench.write(destination / 'judge/run.json', failed)
        stage = 'judge'
    else:
        stage = 'generation'
        bench.write(destination / stage / 'run.json', {'is_error': True, 'reason': 'timeout'})
        if failed_stage == 'truncated-generation':
            (destination / stage / 'run.json').write_text('{interrupted')
    raw = destination / stage / 'events.jsonl'
    raw.write_text('original failed attempt')
    calls = []
    def invoke(prompt, model, effort, target, timeout, live=False):
        calls.append(target.name)
        record = generation if target.name == 'generation' else judge
        bench.write(target / 'run.json', record)
        return record
    monkeypatch.setattr(bench, 'generation_prompt', lambda *args: 'generation')
    monkeypatch.setattr(bench, 'call', invoke)
    result = bench.cell(tmp_path, 'storage', 'gpt-6-luna', 'max', 'dr', False, 1)
    assert result['unique_supported_facts'] == 1
    assert calls == (['judge'] if stage == 'judge' else ['generation', 'judge'])
    preserved = list((destination / 'attempts' / stage).glob('*/events.jsonl'))
    assert len(preserved) == 1 and preserved[0].read_text() == 'original failed attempt'
    calls.clear()
    bench.cell(tmp_path, 'storage', 'gpt-6-luna', 'max', 'dr', False, 1)
    assert calls == [], 'valid successful stages must remain reusable'
