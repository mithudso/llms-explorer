#!/usr/bin/env python3
"""Validate declared optimizer acceptance evidence offline; never manufacture observations."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprint(artifacts, base):
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError('artifacts must be a nonempty list')
    records = []
    for row in artifacts:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id']:
            raise ValueError('each artifact needs a nonempty string id')
        digest = file_hash(base / row['path'])
        if row.get('sha256') != digest:
            raise ValueError(f'artifact {row["id"]}: stale file hash')
        records.append((row['id'], digest))
    if len({key for key, _ in records}) != len(records):
        raise ValueError('duplicate artifact id')
    return hashlib.sha256(json.dumps(sorted(records), separators=(',', ':')).encode()).hexdigest()


def validate(manifest, base):
    """Return consistency/freshness failures, not proof that the author told the truth."""
    errors = []
    base = Path(base)

    def need(condition, message):
        if not condition:
            errors.append(message)

    def proof(value, label):
        if not isinstance(value, dict):
            errors.append(label + ': missing proof')
            return
        try:
            need(file_hash(base / value['path']) == value.get('sha256'), label + ': proof hash mismatch')
        except (KeyError, OSError, TypeError):
            errors.append(label + ': proof file unavailable')

    def receipt(row, label, kind, revision, exit_success=None):
        if not isinstance(row, dict):
            errors.append(label + ': missing receipt')
            return
        need(row.get('kind') == kind, label + ': requires ' + kind)
        need(row.get('completed') is True, label + ': result incomplete')
        need(row.get('artifact_sha256') == revision, label + ': stale artifact binding')
        proof(row.get('proof'), label)
        if kind == 'EXECUTED':
            command = isinstance(row.get('command'), str) and bool(row['command'].strip())
            tool = isinstance(row.get('tool'), str) and bool(row['tool'].strip())
            need(command != tool, label + ': declare one command or tool')
            if command:
                code = row.get('exit_code')
                need(type(code) is int, label + ': missing integer exit code')
                if exit_success is not None:
                    need(type(code) is int and (code == 0) == exit_success, label + ': unexpected exit code')
            elif tool:
                need(exit_success is not False, label + ': regression failure needs a command exit code')
                need(row.get('success') is True, label + ': tool did not succeed')

    if not isinstance(manifest, dict):
        return ['acceptance must be an object']
    try:
        need(manifest.get('schema_version') == 1, 'unsupported acceptance schema')
        current = fingerprint(manifest.get('artifacts'), base)
        need(manifest.get('artifact_sha256') == current, 'acceptance artifact fingerprint mismatch')
        checks = manifest.get('checks')
        need(isinstance(checks, list) and bool(checks), 'missing required executed checks')
        for i, check in enumerate(checks if isinstance(checks, list) else []):
            receipt(check, f'check {i}', 'EXECUTED', current, True)
        review = manifest.get('review')
        receipt(review, 'final review', 'ISOLATED', current)
        if isinstance(review, dict):
            need(isinstance(review.get('reviewer'), str) and bool(review['reviewer'].strip()), 'missing independent reviewer')
            need(review.get('verdict') == 'PASS', 'final review did not pass')
        findings = manifest.get('correctness_findings')
        need(isinstance(findings, list) and all(isinstance(x, str) and x for x in findings),
             'declare correctness_findings as string IDs, or an empty list')
        if not isinstance(findings, list) or not all(isinstance(x, str) for x in findings):
            findings = []
        need(len(findings) == len(set(findings)), 'duplicate correctness finding')
        regressions = manifest.get('regressions', [])
        need(isinstance(regressions, list), 'regressions must be a list')
        regressions = regressions if isinstance(regressions, list) else []
        ids = [r.get('finding_id') for r in regressions if isinstance(r, dict)]
        need(len(ids) == len(regressions) and len(ids) == len(set(ids)) and set(ids) == set(findings),
             'each correctness finding needs exactly one regression')
        baseline = fingerprint(manifest.get('baseline_artifacts'), base) if findings else None
        if findings:
            need({row['id'] for row in manifest['baseline_artifacts']} == {row['id'] for row in manifest['artifacts']},
                 'regression baseline and final artifact IDs must match')
            need(baseline != current, 'regression baseline equals the final artifact')
            need(sorted(row['sha256'] for row in manifest['baseline_artifacts']) != sorted(row['sha256'] for row in manifest['artifacts']),
                 'regression needs changed file content, not relabeled identities')
        for row in regressions:
            if not isinstance(row, dict):
                continue
            label = 'regression ' + str(row.get('finding_id'))
            before, after = row.get('before'), row.get('after')
            receipt(before, label + ' before', 'EXECUTED', baseline, False)
            receipt(after, label + ' after', 'EXECUTED', current, True)
            proof(row.get('test'), label + ' test')
            if isinstance(before, dict) and isinstance(after, dict):
                need(bool(before.get('command')) and before.get('command') == after.get('command'),
                     label + ': must run the same regression command')
                expected = row.get('test', {}).get('sha256')
                need(bool(expected) and before.get('test_sha256') == expected and after.get('test_sha256') == expected,
                     label + ': regression test changed between runs')
        installation = manifest.get('installation')
        need(isinstance(installation, dict) and type(installation.get('required')) is bool,
             'declare whether installation is required')
        if isinstance(installation, dict) and installation.get('required') is True:
            observation = installation.get('observation')
            receipt(observation, 'installed observation', 'OBSERVED', current)
            need(isinstance(installation.get('identity'), str) and bool(installation['identity'].strip()),
                 'missing loaded runtime identity')
            need(installation.get('loaded_artifact_sha256') == current, 'loaded source differs from reviewed source')
            receipt(installation.get('entrypoint'), 'installed entrypoint', 'EXECUTED', current, True)
    except (KeyError, OSError, TypeError, ValueError, AttributeError) as exc:
        errors.append('invalid acceptance evidence: ' + str(exc))
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--fingerprint', action='store_true', help='compute binding from artifacts only')
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.manifest.read_text())
        if args.fingerprint:
            print(json.dumps({'artifact_sha256': fingerprint(data['artifacts'], args.manifest.parent)}))
            return 0
        errors = validate(data, args.manifest.parent)
        print(json.dumps({'valid': not errors, 'errors': errors, 'evidence': 'EXECUTED'}, indent=2))
        return 1 if errors else 0
    except (KeyError, OSError, ValueError, TypeError) as exc:
        print(json.dumps({'valid': False, 'errors': [str(exc)]}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
