import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('checkpoints', Path(__file__).resolve().parents[1] / 'scripts/research_checkpoints.py')
checkpoints = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checkpoints)


def test_resume_skips_only_matching_inputs_and_outputs(tmp_path):
    output, state = tmp_path / 'result', tmp_path / 'stages.json'
    calls = []
    def action():
        calls.append('paid discovery')
        output.write_text('valid')
    assert not checkpoints.run_stage(state, 'research', {'input': 1}, [output], action)['resumed']
    assert checkpoints.run_stage(state, 'research', {'input': 1}, [output], action)['resumed']
    output.write_text('corrupt')
    assert not checkpoints.run_stage(state, 'research', {'input': 1}, [output], action)['resumed']
    assert not checkpoints.run_stage(state, 'research', {'input': 2}, [output], action)['resumed']
    assert len(calls) == 3


def test_failure_resumes_only_failed_stage(tmp_path):
    calls = []
    first, second, state = tmp_path / 'claims', tmp_path / 'export', tmp_path / 'stages.json'
    def research():
        calls.append('research')
        first.write_text('facts')
    def fail():
        raise OSError('disk full')
    checkpoints.run_stage(state, 'research', {}, [first], research)
    with pytest.raises(OSError): checkpoints.run_stage(state, 'export', {}, [second], fail)
    assert checkpoints.run_stage(state, 'research', {}, [first], research)['resumed']
    checkpoints.run_stage(state, 'export', {}, [second], lambda: second.write_text('pack'))
    assert calls == ['research']
    second.unlink()
    with pytest.raises(ValueError, match='required outputs'):
        checkpoints.run_stage(state, 'export', {}, [second], lambda: None)
