import importlib.util
import json
from pathlib import Path
import sys
spec = importlib.util.spec_from_file_location('estate_evals', Path(__file__).parents[1]/'scripts/estate_evals.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)

def test_nested_and_aliases(tmp_path):
    root = tmp_path/'repo'
    (root/'.git').mkdir(parents=True)
    (root/'nested/.git').mkdir(parents=True)
    skill = root/'skills/family/references/spoke'
    skill.mkdir(parents=True)
    (skill/'SKILL.md').write_text('---\nname: spoke\ndescription: Test routing\n---\nBody')
    (tmp_path/'alias').symlink_to(root, target_is_directory=True)
    (root/'node_modules/ignored/.git').mkdir(parents=True)
    (root/'loop').symlink_to(root, target_is_directory=True)
    result = e.discover([root, tmp_path/'alias'])
    assert len(result['repos']) == 2
    assert len(result['skills']) == 1
    assert any('/alias/' in a for a in result['skills'][0]['aliases'])

def test_missing_and_broken(tmp_path):
    (tmp_path/'broken').symlink_to(tmp_path/'absent')
    result = e.discover([tmp_path, tmp_path/'missing'])
    assert result['missing_roots']
    assert result['errors'][0]['error'] == 'broken symlink'

def test_timeout_and_command_errors():
    assert e.execute([sys.executable, '-c', 'import time; time.sleep(30)'], timeout=.05)['status'] == 'timeout'
    assert e.execute(['/no/such/executable'])['status'] == 'error'
    assert e.execute([sys.executable, '-c', 'raise SystemExit(4)'])['status'] == 'failed'

def test_empty_analyzer_not_pass(monkeypatch):
    monkeypatch.setattr(e, 'execute', lambda *a, **k: {'status':'executed','stdout':'{"summary":{},"checks":[]}'})
    assert e.analyze_skill({'id':'a','path':'/tmp/SKILL.md'}, '/tmp/plugin', 1)['status'] == 'invalid_report'

def test_findings_not_pass(monkeypatch):
    monkeypatch.setattr(e, 'execute', lambda *a, **k: {'status':'executed','stdout':json.dumps({'summary':{},'checks':[{'status':'fail'}]})})
    result = e.analyze_skill({'id':'a','path':'/tmp/SKILL.md'}, '/tmp/plugin', 1)
    assert result['status'] == 'static_findings'
    assert result['behavioral_status'] == 'not_executed'

def test_repo_discovery_does_not_execute(tmp_path):
    (tmp_path/'package.json').write_text(json.dumps({'scripts': {'test':'rm -rf something', 'start':'node app.js'}}))
    result = e.repo_config({'id':'a','path':str(tmp_path)})
    assert len(result['candidates']) == 1
    assert result['candidates'][0]['review_required']
    assert result['approved_command'] is None

def test_fixtures_are_unvalidated(tmp_path):
    skill = tmp_path/'SKILL.md'
    skill.write_text('---\nname: sample\ndescription: Summarize documents\n---\nText')
    result = e.skill_fixture({'id':'a','path':str(skill)})
    assert result['status'] == 'generated_unvalidated'
    assert result['description'] == 'Summarize documents'
    assert len(result['cases']) == 2

def test_repo_static_detects_real_parse_error(tmp_path, monkeypatch):
    (tmp_path/'broken.py').write_text('def nope(:\n')
    (tmp_path/'README.md').write_text('[missing](absent.md)')
    monkeypatch.setattr(e, 'execute', lambda *a, **k: {'status':'executed', 'stdout':'broken.py\0README.md\0'})
    result = e.repo_static({'path':str(tmp_path)})
    assert result['status'] == 'static_findings_tests_pending'
    assert result['checks']['python_syntax'] == 1
    assert len(result['findings']) == 2

def test_repo_static_empty_is_not_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(e, 'execute', lambda *a, **k: {'status':'executed', 'stdout':''})
    assert e.repo_static({'path':str(tmp_path)})['status'] == 'no_supported_static_files_tests_pending'

def test_skill_file_symlinks_deduplicate(tmp_path):
    (tmp_path/'one').mkdir()
    (tmp_path/'two').mkdir()
    (tmp_path/'one/SKILL.md').write_text('body')
    (tmp_path/'two/SKILL.md').symlink_to(tmp_path/'one/SKILL.md')
    result = e.discover([tmp_path])
    assert len(result['skills']) == 1
    assert str(tmp_path/'two/SKILL.md') in result['skills'][0]['aliases']
