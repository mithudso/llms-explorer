#!/usr/bin/env python3
"""Record bounded, attributed catalog observations through the existing DR runtime.

Private source snapshots remain outside the repository. Catalog acquisition is
separate from independent claim verification and from project depth saturation.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import io
import json
import re
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace


def load_runtime(repo):
    path = repo / 'scripts/codex_dr_run.py'
    spec = importlib.util.spec_from_file_location('catalog_codex_adapter', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.load_shared()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--evidence-index', type=Path, required=True)
    parser.add_argument('--run', default='awesome-tuis-catalog-2026-10-24')
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text())
    spec = importlib.util.spec_from_file_location('acquired_catalog', args.catalog.with_name('catalog.py'))
    acquisition = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(acquisition)
    evidence = {row['entry_id']: row for row in json.loads(args.evidence_index.read_text())}
    shared = load_runtime(args.repo.resolve())
    paths = shared.paths(args.run)
    private = Path(paths['dir'])
    prepared = private / 'catalog-evidence'
    prepared.mkdir(exist_ok=True)
    concept = 'Awesome TUIs project catalog'
    sources, snapshots, claims, gaps, mapping = {}, [], [], [], []
    seen = {}

    def keep(url, body, title, owner):
        if url in sources:
            return
        path = prepared / (hashlib.sha256(url.encode()).hexdigest() + '.txt')
        path.write_text(body)
        output = io.StringIO()
        with redirect_stdout(output):
            shared.cmd_source_put(SimpleNamespace(slug=args.run, url=url, title=title,
                tier='repo', concept=concept, text_file=str(path), no_snapshot=False))
        result = json.loads(output.getvalue())
        if result.get('warnings'):
            raise ValueError(f"Source snapshot failed for {url}: {result['warnings']}")
        shared.evidence_provenance.annotate(shared.RESEARCH_DIR / '.library',
            result['library_id'], owner or 'unknown-origin',
            version=hashlib.sha256(body.encode()).hexdigest())
        sources[url] = {'url': url, 'title': title, 'tier': 'repo'}
        snapshots.append({'url': url, 'sha256': hashlib.sha256(body.encode()).hexdigest(),
                          'source_id': result.get('library_id')})

    pinned = catalog['inventory']['pinned_readme_url']
    inventory_body = (args.evidence_index.parent / 'inventory.md').read_text()
    for row in catalog['entries']:
        proof = evidence[row['entry_id']]
        quote = row.get('first_party_description_quote', '').removesuffix(' …').strip()
        readme_quote = (proof.get('readme_text') and
                       proof['description_source_url'] == proof.get('readme_url'))
        raw_path = Path(proof['readme_text'] if readme_quote else proof['metadata_or_site_body'])
        if quote and raw_path.is_file() and row.get('acquisition_status') != 'SOURCE-GAP':
            raw = raw_path.read_bytes()
            expected_hash = proof['readme_sha256'] if readme_quote else proof['metadata_or_site_sha256']
            if hashlib.sha256(raw).hexdigest() != expected_hash:
                raise ValueError('Acquisition body hash mismatch: ' + row['entry_id'])
            body = raw.decode('utf-8', 'replace')
            # A readable representation preserves the exact description field while
            # retaining the acquired response. This is a documented text projection.
            if readme_quote:
                normalized = acquisition.clean(body)
                if quote not in normalized:
                    raise ValueError('Description does not match README: ' + row['entry_id'])
                body = 'README text (markup and whitespace normalized): ' + normalized + '\n\n' + body
            elif row.get('metadata_url'):
                metadata = json.loads(body)
                field = 'name' if proof.get('description_kind') == 'repository title' else 'description'
                description = acquisition.clean(metadata.get(field) or '')
                if quote not in description:
                    raise ValueError('Description does not match metadata: ' + row['entry_id'])
                body = 'Project description (whitespace normalized): ' + description + '\n\n' + body
            else:
                if quote not in html.unescape(re.sub(r'\s+', ' ', body)):
                    raise ValueError('Description does not match acquired site: ' + row['entry_id'])
                body = 'Official page description (decoded HTML text): ' + quote + '\n\n' + body
            url = proof['description_source_url']
            keep(url, body, row['name'] + ' first-party description or title', proof.get('source_owner'))
            text = ('The captured project source for ' + row['name']
                    + ' contains this description or title: “' + quote + '”.')
        else:
            url = pinned
            keep(url, inventory_body, 'Pinned Awesome TUIs inventory', 'github-owner:rothgar')
            text = ('The pinned Awesome TUIs list includes ' + row['name'] + ' in its '
                    + row['category'] + ' section and links to ' + row['listed_url'] + '.')
            gaps.append(row['entry_id'] + ': first-party purpose description unavailable; only list inclusion is recorded.')
        if text not in seen:
            seen[text] = len(claims)
            claims.append({'text': text, 'confidence': 'low', 'section': 'tools',
                           'sources': [url], 'volatile': False})
        mapping.append({'entry_id': row['entry_id'], 'claim_ordinal': seen[text],
                        'source_url': url, 'primary_description': url != pinned})
    document = {'concept': concept,
        'summary': 'A source-pinned survey of every application and library row in Awesome TUIs. Purpose descriptions are attributed observations from project metadata or official pages. Missing primary descriptions retain an explicit inventory-only record. This catalog does not establish installation success, platform compatibility, project safety, active maintenance, or depth saturation. Public profiles preserve documentation observations and acquisition gaps separately from these purpose claims.',
        'claims': claims, 'sources': list(sources.values()), 'disagreements': [],
        'open_questions': gaps + ['Independent project-level depth investigations remain a separate frontier; catalog acquisition does not establish depth saturation.'],
        'child_concepts': [],
        'telemetry': {'queries': 0, 'negation_queries': 0, 'sources_deep_read': 0}}
    claim_path = private / 'catalog-import.json'
    claim_path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n')
    errors = shared.validate_claims(document)
    if errors:
        raise ValueError(errors)
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = shared.cmd_concept_done(SimpleNamespace(slug=args.run, claims_file=str(claim_path), as_concept=concept))
    recorded = json.loads(output.getvalue())
    if exit_code != 0 or not recorded.get('ok'):
        raise ValueError('Canonical catalog recording failed: ' + output.getvalue())
    receipt = {'schema_version': '1.0.0', 'inventory_rows': len(mapping), 'unique_claims': len(claims),
               'sources': len(sources), 'gaps': gaps, 'entry_claim_mapping': mapping,
               'source_snapshots': snapshots, 'record_result': recorded,
               'method': 'Deterministic attributed description extraction; no model synthesis or project depth saturation is claimed.'}
    (private / 'catalog-import-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ('inventory_rows', 'unique_claims', 'sources', 'gaps')}, indent=2))


if __name__ == '__main__':
    main()
