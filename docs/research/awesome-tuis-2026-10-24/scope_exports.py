#!/usr/bin/env python3
"""Keep this research publication separate from concurrently completed hub runs.

Freeze before DR finish. After finish, retain this run's accepted packs and use
its normal site generator against a scoped input view. Never edit the live hub
or another worktree. Preserve broad finish receipts as historical evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

PREFIXES = ('concept-tree', 'outputs/llms-concepts', 'outputs/research-artifacts',
            'site/src/data', 'site/src/content/sources',
            'site/public/downloads/concepts', 'site/public/downloads/research')
SEARCH = ('site/public/search-keywords.json', 'site/public/search-index.bin', '.privacy-allowlist')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files(repo):
    result = set()
    for prefix in PREFIXES:
        result.update(p for p in (repo / prefix).rglob('*') if p.is_file())
    result.update(repo / name for name in SEARCH if (repo / name).is_file())
    return result


def load(path):
    spec = importlib.util.spec_from_file_location('scoped_research_site_sync', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['freeze', 'apply'])
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--hub', type=Path, required=True)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--run', action='append', default=[])
    args = parser.parse_args()
    repo, hub, state = args.repo.resolve(), args.hub.resolve(), args.state.resolve()
    baseline = state / 'baseline'
    index = state / 'baseline.json'
    state.mkdir(parents=True, exist_ok=True)
    if args.action == 'freeze':
        if index.exists():
            raise ValueError('Baseline already frozen; do not overwrite continuation evidence')
        dirty = subprocess.check_output(['git', 'diff', '--name-only', '--', *PREFIXES, *SEARCH], cwd=repo)
        if dirty.strip():
            raise ValueError('Generated files already dirty; preserve them before choosing a baseline')
        hashes = {}
        for path in files(repo):
            rel = path.relative_to(repo)
            dest = baseline / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            hashes[str(rel)] = digest(path)
        index.write_text(json.dumps({'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
                                     'files': hashes}, indent=2) + '\n')
        print(json.dumps({'frozen_files': len(hashes), 'state': str(state)}))
        return
    frozen = json.loads(index.read_text())
    receipts = [json.loads((hub / 'research' / run / 'artifacts/receipt.json').read_text()) for run in args.run]
    slugs = {Path(row['path']).name.removesuffix('.llms') for receipt in receipts
             for row in receipt['packs'] if row['target'] == 'repository'}
    tree_path = repo / 'concept-tree/tree.json'
    own_nodes = [n for n in json.loads(tree_path.read_text()) if n['slug'] in slugs]
    if {n['slug'] for n in own_nodes} != slugs:
        raise ValueError('Accepted export/tree identities differ')

    def own(path):
        rel = path.relative_to(repo)
        return any(part.removesuffix('.llms') in slugs for part in rel.parts) or path.stem in slugs

    restored, removed = [], []
    for path in files(repo):
        if own(path):
            continue
        rel = str(path.relative_to(repo))
        if rel in frozen['files']:
            source = baseline / rel
            if digest(source) != frozen['files'][rel]:
                raise ValueError('Frozen baseline hash mismatch: ' + rel)
            if digest(path) != frozen['files'][rel]:
                shutil.copy2(source, path)
                restored.append(rel)
        else:
            path.unlink()
            removed.append(rel)
    sync = load(repo / 'scripts/research_site_sync.py')
    original_nodes = json.loads((baseline / 'concept-tree/tree.json').read_text())
    nodes = sync.merge_nodes(original_nodes, own_nodes)
    tree_path.write_text(json.dumps(nodes, ensure_ascii=False, indent=2) + '\n')
    view = state / 'hub-view'
    (view / 'concept-tree').mkdir(parents=True, exist_ok=True)
    (view / 'llms-concepts').mkdir(exist_ok=True)
    (view / 'research').mkdir(exist_ok=True)
    shutil.copy2(tree_path, view / 'concept-tree/tree.json')
    cache = hub / 'research/.site-public-references.json'
    if cache.exists():
        shutil.copy2(cache, view / 'research/.site-public-references.json')
    for slug in slugs:
        dest = view / 'llms-concepts' / (slug + '.llms')
        if not dest.exists():
            dest.symlink_to(hub / 'llms-concepts' / (slug + '.llms'), target_is_directory=True)
    result = sync.sync(repo, view, apply=True, merge_tree=False, authoritative_slugs=sorted(slugs))
    # The generator also materializes previously absent downloads for published
    # baseline concepts. Retain this task's downloads and the frozen originals.
    ephemeral_downloads = []
    for prefix in ('site/public/downloads/concepts', 'site/public/downloads/research'):
        for path in (repo / prefix).glob('*'):
            rel = str(path.relative_to(repo))
            if path.is_file() and rel not in frozen['files'] and not own(path):
                path.unlink()
                ephemeral_downloads.append(rel)
    leaf_prefixes = ('outputs/llms-concepts/', 'outputs/research-artifacts/', 'site/src/data/concepts/',
                     'site/public/downloads/concepts/', 'site/public/downloads/research/')
    differences = []
    for rel, sha in frozen['files'].items():
        path = repo / rel
        if rel.startswith(leaf_prefixes) and not own(path) and (not path.is_file() or digest(path) != sha):
            differences.append(rel)
    for path in files(repo):
        rel = str(path.relative_to(repo))
        if rel.startswith(leaf_prefixes) and rel not in frozen['files'] and not own(path):
            differences.append(rel)
    previous = {n['slug']: n for n in original_nodes if n['slug'] not in slugs}
    current = {n['slug']: n for n in json.loads(tree_path.read_text()) if n['slug'] not in slugs}
    if differences or current != previous:
        raise ValueError('Scoped generation altered unrelated leaves/nodes: ' + repr(differences[:20]))
    receipt = {'version': '1.0.0', 'ok': True, 'baseline_head': frozen['head'],
        'baseline_index_sha256': digest(index), 'accepted_slugs': sorted(slugs),
        'scoped_hub': str(view), 'scoped_tree_sha256': digest(view / 'concept-tree/tree.json'),
        'withheld_reference_cache_sha256': digest(view / 'research/.site-public-references.json') if cache.exists() else None,
        'restored_non_tui_generated_files': restored, 'removed_non_tui_generated_files': removed,
        'removed_new_baseline_downloads': ephemeral_downloads,
        'non_tui_leaf_files_match_baseline': True, 'non_tui_tree_nodes_match_baseline': True,
        'final_website': result, 'authority': 'This scoped receipt supersedes the broad finish website receipts for remote publication.'}
    (state / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'ok': True, 'accepted_slugs': sorted(slugs), 'restored': len(restored), 'removed': len(removed),
                      'receipt': str(state / 'receipt.json')}))


if __name__ == '__main__':
    main()
