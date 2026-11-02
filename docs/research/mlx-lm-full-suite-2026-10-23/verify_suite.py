#!/usr/bin/env python3
"""Verify the delivered MLX-LM suite without private research state or models."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

PACK_FILES = {
    'llms.txt', 'llms-full.txt', 'llms-small.txt', 'llms-facts.txt',
    'llms-vocabulary.txt', 'units.jsonl', 'concept-graph.json', 'manifest.json',
}


def read(path: Path):
    return json.loads(path.read_text())


def verify(repo: Path) -> dict:
    report_dir = Path(__file__).resolve().parent
    members = read(report_dir / 'members.json')
    assert len({m['slug'] for m in members}) == len(members), 'Duplicate family member'
    tree = {n['slug']: n for n in read(repo / 'concept-tree/tree.json')}
    unique_claims = set()
    for member in members:
        slug = member['slug']
        directory = repo / f'outputs/llms-concepts/{slug}.llms'
        assert PACK_FILES <= {p.name for p in directory.iterdir()}, f'{slug}: missing pack file'
        manifest = read(directory / 'manifest.json')
        assert manifest['research_status'] == 'COMPLETED', slug
        units = [json.loads(line) for line in (directory / 'units.jsonl').read_text().splitlines()]
        assert len(units) == manifest['kept_units'], f'{slug}: count mismatch'
        public = read(repo / f'outputs/research-artifacts/{slug}.json')
        assert public['canonical_artifact_sha256'] == manifest['canonical_artifact_sha256'], slug
        claims = {c['id']: c for c in public['claims']}
        assert len(claims) == len(units), f'{slug}: duplicate or missing canonical claims'
        full = (directory / 'llms-full.txt').read_text()
        for unit in units:
            claim = claims[unit['id']]
            assert unit['validation_status'] == claim['validation_status'] == 'SUPPORTED', slug
            assert unit['evidence_ids'], f'{slug}: missing bound evidence'
            assert unit['text'] == claim['text'], f'{slug}: changed public statement'
            assert re.sub(r'\s+', ' ', unit['text']).strip() in full, f'{slug}: clipped statement'
            assert unit['source_url'].startswith(('https://', 'http://')), slug
            unique_claims.add(unit['id'])
        for filename, stats in manifest['files'].items():
            path = directory / filename
            assert len(path.read_bytes()) == stats['bytes'], f'{slug}: stale {filename} byte count'
        site = read(repo / f'site/src/data/concepts/{slug}.json')
        assert site['canonicalArtifactSha256'] == manifest['canonical_artifact_sha256'], slug
        assert slug in tree, f'{slug}: unregistered reader'
    family = repo / 'outputs/llms-concepts/mlx-lm-family.llms'
    family_manifest = read(family / 'manifest.json')
    assert family_manifest['members'] == members, 'Family membership drift'
    content = (family / 'llms.txt').read_bytes()
    assert hashlib.sha256(content).hexdigest() == family_manifest['index_sha256'], 'Family hash drift'
    allowed = {(repo / f'outputs/llms-concepts/{m["slug"]}.llms' / filename).resolve()
               for m in members for filename in ['llms.txt', 'llms-facts.txt']}
    targets = {(family / target).resolve()
               for target in re.findall(r'\]\(([^)]+)\)', content.decode())}
    assert targets == allowed, 'Family targets differ from the authorized member set'
    assert all(target.is_file() for target in targets), 'Broken family target'
    checks = read(report_dir / 'checks.json')
    for item in checks['skill_audit']['artifacts']:
        path = repo / '.agents/skills/mlx-lm-expert' / item['file']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], 'Stale skill audit'
    verification = read(report_dir / 'verification.json')
    for path, expected in verification['frozen_semantic_files'].items():
        assert hashlib.sha256((repo / path).read_bytes()).hexdigest() == expected, path
    for row in verification['pack_answer_tests']:
        slug, phase = row['slug'], row['phase']
        file = repo / f'outputs/llms-concepts/{slug}.llms/llms-{phase}.txt'
        assert hashlib.sha256(file.read_bytes()).hexdigest() == row['pack_sha256'], f'{slug}: stale QA'
        bank = report_dir / 'questions' / f'{slug}.jsonl'
        assert hashlib.sha256(bank.read_bytes()).hexdigest() == row['bank_sha256'], f'{slug}: changed bank'
        assert row['supported'] >= (8 if phase == 'small' else 9), f'{slug}: answer coverage gap'
    assert len(verification['pack_answer_tests']) == 2 * len(members), 'Incomplete pack QA'
    return {'members': len(members), 'unique_supported_claims': len(unique_claims),
            'pack_answer_tests': len(verification['pack_answer_tests']), 'new_embeddings': 0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    print(json.dumps(verify(args.repo.resolve()), indent=2))


if __name__ == '__main__':
    main()
