#!/usr/bin/env python3
"""Local estate evaluation inventory. No model calls or repository test execution by default."""
from __future__ import annotations
import argparse
import ast
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

VERSION = '1.0.0'
SKIP = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'dist', 'build', 'target', '.next', '.astro', '.tox', '.cache', 'vendor', 'coverage', '.pnpm-store', 'Xcode.app', '.build'}
HOME = Path.home()
DEFAULT_ROOTS = [HOME/'dev', HOME/'.global-ai-hub', HOME/'.agents/skills', HOME/'.claude/skills', HOME/'.codex/skills', HOME/'.claude/plugins', HOME/'.codex/plugins', HOME/'.codex/.tmp/plugins']

def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2) + '\n')
    tmp.replace(path)

def identity(path):
    return hashlib.sha256(str(path).encode()).hexdigest()[:16]

def discover(roots):
    found = {'skills': {}, 'repos': {}}
    errors, aliases, missing = [], [], []
    visited = set()
    def walk(path):
        try:
            real = path.resolve(strict=True)
            if path.is_symlink():
                aliases.append({'path': str(path), 'canonical': str(real)})
            if not real.is_dir() or real in visited:
                return
            visited.add(real)
            if len(visited) % 10000 == 0:
                print(f'Scanned {len(visited)} directories: {real}', flush=True)
            entries = list(path.iterdir())
            names = {e.name for e in entries}
            for kind, marker in [('skills', 'SKILL.md'), ('repos', '.git')]:
                if marker in names:
                    target = (real/'SKILL.md').resolve() if kind == 'skills' else real
                    if kind == 'skills' and (real/'SKILL.md').is_symlink():
                        aliases.append({'path': str(real/'SKILL.md'), 'canonical': str(target)})
                    found[kind][str(target)] = {'id': identity(target), 'path': str(target)}
            for entry in sorted(entries):
                if entry.name not in SKIP and entry.is_dir():
                    walk(entry)
                elif entry.is_symlink() and not entry.exists():
                    errors.append({'path': str(entry), 'error': 'broken symlink'})
        except (OSError, RuntimeError) as exc:
            errors.append({'path': str(path), 'error': str(exc)})
    for root in roots:
        p = Path(root).expanduser().absolute()
        if p.exists():
            walk(p)
        else:
            missing.append(str(p))
    alias_index = {}
    for alias in aliases:
        alias_index.setdefault(Path(alias['canonical']), []).append(Path(alias['path']))
    for kind in found:
        for item in found[kind].values():
            target = Path(item['path'])
            item['aliases'] = sorted({str(alias / target.relative_to(parent)) for parent in [target, *target.parents] for alias in alias_index.get(parent, [])})
            item['source_class'] = ('plugin_cache_or_staging' if '/plugins/' in str(target) else 'skill_registry' if any(str(target).startswith(str(HOME / x)) for x in ['.agents/skills', '.claude/skills', '.codex/skills']) else 'repository_or_hub')
            item['archive_hint'] = any(re.search(r'archive|backup|deprecated', part, re.I) for part in target.parts)
    content_seen = {}
    for item in found['skills'].values():
        try:
            digest = hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()
            item['content_sha256'] = digest
            item['same_content_as'] = content_seen.get(digest)
            content_seen.setdefault(digest, item['id'])
        except OSError:
            item['content_sha256'] = None
    return {'version': VERSION, 'created_at': time.time(), 'roots': list(map(str, roots)), 'excluded_directory_names': sorted(SKIP), 'archive_policy': 'included and flagged; no archive-name exclusions', 'missing_roots': missing, 'errors': errors, 'directory_aliases': aliases, **{k: sorted(v.values(), key=lambda x: x['path']) for k,v in found.items()}}

def skill_fixture(item):
    try:
        text = Path(item['path']).read_text(errors='replace')
    except OSError as exc:
        return {'skill_id': item['id'], 'skill_path': item['path'], 'status': 'unreadable_skill', 'error': str(exc), 'cases': []}
    match = re.search(r'^description:\s*(.+?)(?=\n[\w-]+:|\n---)', text, re.M | re.S)
    desc = match.group(1).strip() if match else ''
    return {'skill_id': item['id'], 'skill_path': item['path'], 'status': 'generated_unvalidated', 'description': desc,
            'cases': [{'id': 'positive-routing', 'prompt': 'Help me with this task: ' + desc, 'expected_route': item['path']},
                      {'id': 'negative-routing', 'prompt': 'Reply only with the word hello. Do not use any skill.', 'expected_route': None}],
            'content_assertions': [{'kind': 'rubric', 'text': 'The response fulfills the following documented scope: ' + desc, 'validated': False}],
            'blockers': ['Human review of routing prompts and content rubric', 'Domain-specific goldens and a behavioral adapter are required']}

def repo_config(item):
    root = Path(item['path'])
    candidates = []
    # Inspect manifests throughout each repo, excluding nested repos and generated trees.
    for directory, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP and not (Path(directory)/d/'.git').exists() and not (Path(directory)/d).is_symlink()]
        cwd = Path(directory)
        if 'package.json' in files:
            try:
                scripts = json.loads((cwd/'package.json').read_text()).get('scripts', {})
                for name, command in scripts.items():
                    if re.search(r'test|eval|check|lint|verify', name):
                        candidates.append({'cwd': str(cwd), 'argv': ['npm', 'run', name], 'declared_command': command, 'review_required': True})
            except (ValueError, OSError):
                candidates.append({'cwd': str(cwd), 'error': 'Unreadable package.json'})
        if any(f in files for f in ['pytest.ini', 'pyproject.toml', 'setup.cfg']) and ((cwd/'tests').is_dir() or 'pytest.ini' in files):
            candidates.append({'cwd': str(cwd), 'argv': [str(root/'.venv/bin/python') if (root/'.venv/bin/python').exists() else str(HOME/'.codex/evals/runtime/venv/bin/python') if (HOME/'.codex/evals/runtime/venv/bin/python').exists() else 'python3', '-m', 'pytest'], 'review_required': True})
        if any(re.fullmatch(r'test_.*\.py', f) for f in files):
            candidates.append({'cwd': str(cwd), 'argv': ['python3', '-m', 'unittest', 'discover', '-s', '.', '-p', 'test_*.py'], 'review_required': True})
        for marker, argv in [('Cargo.toml', ['cargo','test']), ('go.mod', ['go','test','./...']), ('pom.xml', ['mvn','test'])]:
            if marker in files:
                candidates.append({'cwd': str(cwd), 'argv': argv, 'review_required': True})
    return {'repo_id': item['id'], 'path': str(root), 'baseline_command': ['python3', str(Path(__file__).resolve()), 'repo-static', '--id', item['id']], 'status': 'commands_discovered_not_executed' if candidates else 'missing_test_adapter', 'candidates': candidates, 'approved_command': None}

def execute(argv, cwd=None, timeout=30):
    start = time.monotonic()
    try:
        with subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True) as proc:
            try:
                out, err = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                out, err = proc.communicate()
                return {'status': 'timeout', 'stdout': out, 'stderr': err, 'seconds': time.monotonic()-start}
            return {'status': 'executed' if proc.returncode == 0 else 'failed', 'exit_code': proc.returncode, 'stdout': out, 'stderr': err, 'seconds': time.monotonic()-start}
    except OSError as exc:
        return {'status': 'error', 'error': str(exc)}

def repo_static(item, timeout=30):
    """Parse tracked Python and JSON manifests; check local Markdown file links."""
    root = Path(item['path'])
    listing = execute(['git', '-C', str(root), 'ls-files', '-z'], timeout=timeout)
    if listing['status'] != 'executed':
        return {'status': 'repository_check_failed', 'detail': listing}
    checks, findings = Counter(), []
    tracked = [p for p in listing['stdout'].split('\0') if p]
    repository_type = ('code' if any(Path(p).suffix in {'.py', '.js', '.mjs', '.cjs', '.ts', '.tsx', '.go', '.rs', '.java', '.c', '.cpp', '.swift'} for p in tracked) else 'documentation' if any(Path(p).suffix == '.md' for p in tracked) else 'other' if tracked else 'empty')
    for rel in tracked:
        if not rel or any(p in SKIP for p in Path(rel).parts):
            continue
        path = root / rel
        if not path.is_file():
            continue
        try:
            if path.suffix == '.py':
                checks['python_syntax'] += 1
                ast.parse(path.read_bytes(), filename=rel)
            elif path.name in ('package.json', 'tsconfig.json', 'composer.json'):
                # tsconfig allows JSONC and is deliberately not parsed as strict JSON.
                if path.name != 'tsconfig.json':
                    checks['json_manifest'] += 1
                    json.loads(path.read_text())
            elif path.suffix == '.md':
                checks['markdown_files'] += 1
                for link in re.findall(r'\[[^\]\n]*\]\(([^)\s]+)\)', path.read_text(errors='replace')):
                    if link.startswith(('#', '/', 'http:', 'https:', 'mailto:', 'data:', 'app:', 'file:', 'skill:')) or ':' in link or '{' in link:
                        continue
                    target = link.split('#')[0].split('?')[0]
                    if not target or '%' in target:
                        continue
                    checks['markdown_local_links'] += 1
                    if not (path.parent / target).exists():
                        findings.append({'path': rel, 'check': 'markdown_local_link', 'target': target, 'severity': 'review'})
        except (OSError, SyntaxError, ValueError) as exc:
            findings.append({'path': rel, 'check': 'parse', 'error': str(exc), 'severity': 'error'})
    total = sum(checks.values())
    return {'status': 'static_findings_tests_pending' if findings else 'static_no_findings_tests_pending' if total else 'no_supported_static_files_tests_pending', 'checks': dict(checks), 'repository_type': repository_type, 'tracked_file_count': len(tracked), 'findings': findings, 'test_status': 'not_executed', 'scope': 'Tracked Python syntax, strict JSON manifests, and heuristic local Markdown links; not runtime correctness'}

def analyze_skill(item, plugin, timeout):
    result = execute(['node', str(plugin), 'analyze', item['path'], '--format', 'json'], timeout=timeout)
    if result['status'] == 'executed':
        try:
            report = json.loads(result['stdout'])
            if not isinstance(report.get('checks'), list) or not report['checks'] or 'summary' not in report:
                raise ValueError('Missing or empty checks/summary')
            result['report'] = report
            result.pop('stdout')
            counts = Counter(c.get('status') for c in report['checks'])
            result['check_counts'] = dict(counts)
            result['status'] = 'static_findings' if counts['fail'] or counts['warn'] else 'static_no_findings'
        except (ValueError, TypeError, AttributeError) as exc:
            result['status'] = 'invalid_report'
            result['error'] = str(exc)
    return {'id': item['id'], 'path': item['path'], 'behavioral_status': 'not_executed', **result}

def report(out):
    inventory = json.loads((out/'inventory.json').read_text())
    skill_counts, repo_counts = Counter(), Counter()
    for kind, counts in [('skills', skill_counts), ('repos', repo_counts)]:
        for item in inventory[kind]:
            p = out/'results'/kind/(item['id']+'.json')
            counts[json.loads(p.read_text())['status'] if p.exists() else 'not_executed'] += 1
    summary = {'version': VERSION, 'skills': len(inventory['skills']), 'repos': len(inventory['repos']), 'skill_static_statuses': dict(skill_counts), 'repo_statuses': dict(repo_counts), 'skill_source_classes': dict(Counter(i.get('source_class', 'unclassified') for i in inventory['skills'])), 'archive_hinted_skills': sum(i['archive_hint'] for i in inventory['skills']), 'distinct_skill_content_hashes': len({i.get('content_sha256') for i in inventory['skills'] if i.get('content_sha256')}), 'repo_test_statuses': dict(Counter(json.loads((out/'results/repo-test'/(i['id']+'.json')).read_text())['status'] if (out/'results/repo-test'/(i['id']+'.json')).exists() else 'not_executed' for i in inventory['repos'])), 'skill_behavior_statuses': dict(Counter(json.loads((out/'results/behavior'/(i['id']+'.json')).read_text())['status'] if (out/'results/behavior'/(i['id']+'.json')).exists() else 'not_executed' for i in inventory['skills'])), 'behavioral_evidence': 'Generated fixtures are not passes; separate adapter evidence is required.', 'inventory_errors': len(inventory['errors']), 'missing_roots': inventory['missing_roots']}
    save(out/'summary.json', summary)
    return summary

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['discover','run','repo-static','report','behavior','repo-test'])
    parser.add_argument('--output', type=Path, default=HOME/'.codex/evals')
    parser.add_argument('--root', action='append')
    parser.add_argument('--plugin', type=Path, default=HOME/'.codex/plugins/cache/openai-curated-remote/plugin-eval/0.1.2/scripts/plugin-eval.js')
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--timeout', type=float, default=45)
    parser.add_argument('--id')
    parser.add_argument('--command-json', help='Explicit argv JSON for an adapter or reviewed repo test; never a shell string')
    args = parser.parse_args()
    out = args.output.expanduser()
    out.mkdir(parents=True, exist_ok=True)
    if args.action == 'discover':
        inventory = discover(args.root or DEFAULT_ROOTS)
        if not args.root:
            inventory['repos'] = [i for i in inventory['repos'] if any(Path(i['path']).is_relative_to(r.resolve()) for r in [HOME/'dev', HOME/'.global-ai-hub'])]
        save(out/'inventory.json', inventory)
        for item in inventory['skills']:
            save(out/'fixtures'/(item['id']+'.json'), skill_fixture(item))
        for item in inventory['repos']:
            save(out/'repos'/(item['id']+'.json'), repo_config(item))
        save(out/'checkpoint.json', {'phase': 'discovered', 'skills': len(inventory['skills']), 'repos': len(inventory['repos'])})
    elif args.action == 'run':
        inventory = json.loads((out/'inventory.json').read_text())
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            pending = {pool.submit(analyze_skill, i, args.plugin, args.timeout): i for i in inventory['skills']}
            for n, future in enumerate(as_completed(pending), 1):
                item = pending[future]
                try:
                    result = future.result()
                except Exception as exc:
                    result = {'id': item['id'], 'status': 'error', 'error': str(exc)}
                save(out/'results/skills'/(item['id']+'.json'), result)
                if n % 50 == 0:
                    save(out/'checkpoint.json', {'phase': 'running_static', 'completed': n, 'total': len(pending)})
                    print(f'Skills analyzed: {n}/{len(pending)}', flush=True)
        for item in inventory['repos']:
            config = json.loads((out/'repos'/(item['id']+'.json')).read_text())
            result = repo_static(item, args.timeout)
            result['candidate_count'] = len(config['candidates'])
            save(out/'results/repos'/(item['id']+'.json'), result)
        save(out/'checkpoint.json', {'phase': 'static_complete', 'behavioral': 'requires reviewed fixtures and adapters'})
    elif args.action == 'repo-static':
        inventory = json.loads((out/'inventory.json').read_text())
        if args.id and not any(i['id'] == args.id for i in inventory['repos']):
            parser.error('Unknown repository id')
        for item in inventory['repos']:
            if not args.id or item['id'] == args.id:
                save(out/'results/repos'/(item['id']+'.json'), repo_static(item, args.timeout))
    elif args.action in ('behavior', 'repo-test'):
        if not args.id or not args.command_json:
            parser.error('--id and --command-json are required')
        inventory = json.loads((out/'inventory.json').read_text())
        kind = 'skills' if args.action == 'behavior' else 'repos'
        item = next((i for i in inventory[kind] if i['id'] == args.id), None)
        if item is None:
            parser.error('Unknown target id')
        argv = json.loads(args.command_json)
        if not isinstance(argv, list) or not argv or not all(isinstance(a,str) for a in argv):
            parser.error('--command-json must be a nonempty array of strings')
        # Behavioral adapter receives fixture path and must return machine-readable evidence.
        result = execute(argv + ([str(out/'fixtures'/(args.id+'.json'))] if kind == 'skills' else []), cwd=item['path'] if kind == 'repos' else str(Path(item['path']).parent), timeout=args.timeout)
        if kind == 'skills' and result['status'] == 'executed':
            try:
                evidence = json.loads(result['stdout'])
                cases = evidence['cases']
                fixture = json.loads((out/'fixtures'/(args.id+'.json')).read_text())
                expected = {c['id'] for c in fixture['cases']}
                if not cases or {c['id'] for c in cases} != expected or not all(isinstance(c.get('passed'), bool) and c.get('evidence') for c in cases):
                    raise ValueError('Expected evidence and boolean passed for every fixture case')
                result['status'] = 'behavior_passed' if all(c['passed'] for c in cases) else 'behavior_failed'
            except (ValueError, KeyError, TypeError) as exc:
                result['status'] = 'invalid_behavior_evidence'
                result['error'] = str(exc)
        result['argv'] = argv
        result['target_id'] = args.id
        save(out/'results'/args.action/(args.id+'.json'), result)
        print(json.dumps(result, indent=2))
        return 0 if result['status'] in ('executed', 'behavior_passed') else 1
    print(json.dumps(report(out), indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
