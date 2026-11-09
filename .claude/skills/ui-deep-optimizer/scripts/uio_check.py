#!/usr/bin/env python3
"""Offline catalogue and evidence-ledger checks. Does not execute a UI audit."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {'CLEAN', 'REPORT_ONLY', 'NEEDS_EVIDENCE', 'BLOCKED', 'VERIFY_FAILED',
            'STALLED', 'CYCLING', 'CAPPED', 'BUDGET_EXHAUSTED'}
PASS_STATUSES = {'PASS', 'N_A', 'PARTIAL', 'UNAVAILABLE', 'OUT_OF_SCOPE'}
KINDS = {'EXECUTED', 'OBSERVED', 'EXPERT', 'PARTICIPANT', 'ISOLATED', 'SIMULATED'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprint(files):
    """Bind exact file names and bytes; fail on absent/non-file inputs."""
    if not files:
        raise ValueError('fingerprint requires at least one owned file')
    records = [(str(Path(p).resolve()), sha(p)) for p in files]
    if len({p for p, _ in records}) != len(records):
        raise ValueError('duplicate fingerprint path')
    return hashlib.sha256(json.dumps(sorted(records), separators=(',', ':')).encode()).hexdigest()


def catalogue():
    data = json.loads((ROOT / 'references/methods.json').read_text())
    methods = data['methods']
    seen = set()
    names = set()
    for m in methods:
        for field in ('id', 'method', 'family', 'mode', 'prerequisites', 'inspect',
                      'evidence', 'medium_trigger', 'fix', 'verify', 'source_ids'):
            if not m.get(field):
                raise ValueError(f'{m.get("id")}: missing {field}')
        if m['id'] in seen or m['method'].casefold() in names:
            raise ValueError('duplicate method ID or name')
        if m['mode'] not in {'core', 'conditional', 'research'}:
            raise ValueError('invalid method mode')
        seen.add(m['id'])
        names.add(m['method'].casefold())
    return methods


def validate(report, files, base):
    """Return guard failures. Passing only establishes a consistent supplied ledger."""
    errors = []
    methods = {m['id']: m for m in catalogue()}
    current = fingerprint(files)
    clean = report.get('status') == 'CLEAN'

    def need(ok, message):
        if not ok:
            errors.append(message)

    def receipts(rows, label, research=False, required_kind=None):
        need(isinstance(rows, list) and bool(rows), f'{label}: missing evidence')
        if not isinstance(rows, list):
            return
        for e in rows:
            if not isinstance(e, dict):
                errors.append(f'{label}: invalid receipt')
                continue
            path = base / e.get('path', '')
            need(path.is_file(), f'{label}: evidence file missing')
            if path.is_file():
                need(e.get('sha256') == sha(path), f'{label}: evidence hash mismatch')
            need(e.get('captured_for') == current, f'{label}: stale evidence binding')
            need(e.get('kind') in KINDS - {'SIMULATED'}, f'{label}: unsupported evidence kind')
            if required_kind:
                need(e.get('kind') == required_kind, f'{label}: requires {required_kind} evidence')
            if research:
                need(e.get('kind') in {'PARTICIPANT', 'EXECUTED', 'OBSERVED'},
                     f'{label}: research cannot use simulated participants or expert predictions')

    need(report.get('schema_version') == 1, 'unsupported schema version')
    need(bool(report.get('version')) and bool(report.get('delta')), 'missing version/delta')
    need(report.get('status') in STATUSES, 'invalid exit status')
    need(report.get('artifact_sha256') == current, 'report source fingerprint is stale')
    selected = report.get('selected', [])
    need(isinstance(selected, list), 'selected must be a list')
    selected = selected if isinstance(selected, list) else []
    need(len(selected) == len(set(selected)), 'duplicate selected method')
    need(set(selected) <= methods.keys(), 'unknown selected method')
    need({k for k, m in methods.items() if m['mode'] == 'core'} <= set(selected),
         'cannot drop core methods')
    matrix = report.get('scope', {}).get('matrix', [])
    cells = [c.get('id') for c in matrix]
    need(all(all(c.get(k) for k in ('route', 'state', 'viewport', 'role')) for c in matrix),
         'coverage matrix needs route/state/viewport/role')
    need(bool(cells) and all(cells) and len(cells) == len(set(cells)), 'invalid coverage matrix')
    rows = report.get('passes', [])
    ids = [p.get('id') for p in rows]
    need(len(ids) == len(set(ids)) and set(ids) == methods.keys(),
         'every catalogue method needs exactly one pass row')
    for p in rows:
        key = p.get('id')
        status = p.get('status')
        need(status in PASS_STATUSES, f'{key}: invalid pass status')
        if key not in selected:
            need(status == 'OUT_OF_SCOPE' and bool(p.get('reason')),
                 f'{key}: unselected method needs OUT_OF_SCOPE reason')
            continue
        need(status != 'OUT_OF_SCOPE', f'{key}: selected method cannot be dropped')
        if status != 'PASS':
            need(bool(p.get('reason')), f'{key}: missing applicability/evidence reason')
        if clean:
            need(status in {'PASS', 'N_A'}, f'{key}: selected pass incomplete')
            need(p.get('artifact_sha256') == current, f'{key}: stale pass revision')
            receipts(p.get('evidence'), key, research=methods.get(key, {}).get('mode') == 'research' and status == 'PASS')
            if status == 'PASS':
                applicable = p.get('applicable_cells', [])
                checked = p.get('checked_cells', [])
                need(bool(applicable) and set(applicable) <= set(cells), f'{key}: invalid applicable cells')
                need(len(checked) == len(set(checked)) and set(checked) == set(applicable),
                     f'{key}: incomplete matrix coverage')
    findings = report.get('findings', [])
    finding_ids = [f.get('id') for f in findings]
    need(all(finding_ids) and len(finding_ids) == len(set(finding_ids)), 'invalid finding IDs')
    for f in findings:
        key = f.get('id')
        need(f.get('severity') in {'Critical', 'High', 'Medium', 'Low', 'Nit'}, f'{key}: invalid severity')
        need(f.get('status') in {'OPEN', 'BLOCKED', 'FIXED'}, f'{key}: invalid finding status')
        need(bool(f.get('methods')) and set(f.get('methods', [])) <= set(selected), f'{key}: invalid method links')
        for field in ('locator', 'impact', 'evidence', 'fix'):
            need(bool(f.get(field)), f'{key}: missing {field}')
        if f.get('status') == 'FIXED':
            receipts(f.get('verification'), key + ' verification')
        if clean and f.get('severity') in {'Critical', 'High', 'Medium'}:
            need(f.get('status') == 'FIXED', f'{key}: unresolved Medium+')
    if clean:
        need(report.get('editable') is True, 'read-only input cannot be CLEAN')
        need(report.get('final_sweep_no_edits') is True, 'CLEAN needs a complete no-edit sweep')
        checks = [c for c in report.get('checks', []) if c.get('required') is True]
        need(bool(checks), 'CLEAN needs required completed checks')
        for c in checks:
            need(c.get('completed') is True and type(c.get('exit_code')) is int and c['exit_code'] == 0,
                 'required check incomplete or failed')
            need(c.get('artifact_sha256') == current, 'required check is stale')
            receipts(c.get('evidence'), 'required check', required_kind='EXECUTED')
        runtime = report.get('runtime', {})
        need(bool(runtime.get('identity')) and runtime.get('artifact_sha256') == current,
             'missing current loaded runtime identity')
        receipts(runtime.get('evidence'), 'runtime', required_kind='OBSERVED')
        review = report.get('final_review', {})
        need(review.get('grade') == 'ISOLATED' and bool(review.get('reviewer')),
             'CLEAN needs an independent final review')
        need(review.get('artifact_sha256') == current, 'final review is stale')
        receipts(review.get('evidence'), 'final review', required_kind='ISOLATED')
    return errors


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='command', required=True)
    sub.add_parser('catalog')
    method = sub.add_parser('method')
    method.add_argument('id')
    fp = sub.add_parser('fingerprint')
    fp.add_argument('files', nargs='+')
    val = sub.add_parser('validate')
    val.add_argument('report', type=Path)
    val.add_argument('--files', nargs='+', required=True)
    a = ap.parse_args(argv)
    try:
        if a.command == 'catalog':
            print(json.dumps([{'id': m['id'], 'method': m['method'], 'mode': m['mode']} for m in catalogue()], indent=2))
        elif a.command == 'method':
            print(json.dumps(next(m for m in catalogue() if m['id'] == a.id), indent=2))
        elif a.command == 'fingerprint':
            print(json.dumps({'artifact_sha256': fingerprint(a.files)}, indent=2))
        else:
            errors = validate(json.loads(a.report.read_text()), a.files, a.report.parent)
            print(json.dumps({'valid': not errors, 'errors': errors, 'evidence': 'EXECUTED'}, indent=2))
            return 1 if errors else 0
    except (OSError, ValueError, TypeError, KeyError, StopIteration, AttributeError) as exc:
        print(json.dumps({'valid': False, 'error': str(exc) or 'unknown method'}, indent=2))
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
