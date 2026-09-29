#!/usr/bin/env python3
"""Import a provenance-preserving concept-tree union through Zotero's RDF connector.

No database writes, fabricated publications, remote requests, or attachment imports.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import html
import json
import re
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

VERSION = '1.0.0'
COLLECTION = 'Global AI Concept Tree'
TAG = 'global-ai-concept-tree'
NS = {'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
      'z': 'http://www.zotero.org/namespaces/export#',
      'dc': 'http://purl.org/dc/elements/1.1/',
      'dcterms': 'http://purl.org/dc/terms/', 'bib': 'http://purl.org/net/biblio#'}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def merge_trees(sources):
    """First source wins scalar conflicts; retain every input record and union lists."""
    nodes, names, conflicts = {}, {}, []
    for source, records in sources:
        for record in records:
            slug = record.get('slug')
            name = record.get('concept')
            if not slug or not name:
                raise ValueError(f'Missing stable slug/concept in {source}')
            normalized = name.casefold().strip()
            canonical = names.get(normalized, slug)
            if slug in nodes and nodes[slug]['concept'].casefold().strip() != normalized:
                raise ValueError(f'Slug collision: {slug}')
            if canonical not in nodes:
                nodes[canonical] = {**record, 'provenance': [], 'stableSlugs': []}
            node = nodes[canonical]
            node['provenance'].append({'source': str(source), 'record': record})
            node['stableSlugs'] = sorted(set(node['stableSlugs'] + [slug]))
            for key, value in record.items():
                if key in ('aliases', 'slugAliases', 'childConcepts'):
                    node[key] = sorted(set(node.get(key, [])) | set(value))
                elif key not in node:
                    node[key] = value
                elif node[key] != value:
                    conflicts.append({'slug': canonical, 'field': key,
                                      'kept': node[key], 'alternative': value, 'source': str(source)})
            names[normalized] = canonical
    for slug, node in nodes.items():
        parent = node.get('parentConcept')
        node['parentSlug'] = names.get(parent.casefold().strip()) if parent else None
        if parent and not node['parentSlug']:
            raise ValueError(f'Missing parent {parent!r} for {slug}')
        seen = {slug}
        cursor = node['parentSlug']
        while cursor:
            if cursor in seen:
                raise ValueError(f'Parent cycle at {slug}')
            seen.add(cursor)
            parent_name = nodes[cursor].get('parentConcept')
            cursor = names.get(parent_name.casefold().strip()) if parent_name else None
    return nodes, conflicts


def enrich(nodes, repo, hub, skills):
    """Link locally present packs and skills; extract cited URLs without inventing sources."""
    for slug, node in nodes.items():
        files = set()
        for root in (repo / 'outputs', hub / 'outputs'):
            for stable in node['stableSlugs']:
                pack = root / 'llms-concepts' / f'{stable}.llms' / 'llms.txt'
                if pack.is_file():
                    files.add(pack.resolve())
            llms = node.get('llmsFile', '')
            if llms and not llms.startswith('/'):
                candidate = (root / llms).resolve()
                if candidate.is_relative_to(root.resolve()) and candidate.is_file():
                    files.add(candidate)
        for key in ('skillId', 'skillIdWanted'):
            skill = node.get(key)
            if skill:
                candidate = (skills / skill).resolve()
                if candidate.is_dir():
                    candidate = candidate / 'SKILL.md'
                if candidate.is_file() and candidate.is_relative_to(skills.resolve()):
                    files.add(candidate)
        urls = set()
        for path in files:
            text = path.read_text(errors='replace')
            urls.update(re.findall(r'https?://[^\s<>"\]\)]+', text))
        node['contentFiles'] = [str(p) for p in sorted(files)]
        node['citedURLs'] = sorted(u.rstrip('.,;') for u in urls)
        llms = node.get('llmsFile', '')
        node['declaredPackURL'] = ('https://llms-explorer.com' + llms
                                   if llms.startswith('/t/') else None)


def note_html(slug, node):
    esc = html.escape
    sections = [f'<h1>{esc(node["concept"])}</h1>',
                '<p>Concept/index note. This is not a paper or a verified bibliographic record.</p>',
                f'<p>Stable concept identifier: {esc(slug)}</p>',
                f'<p>Aliases: {esc(", ".join(node.get("aliases", []))) or "None recorded"}</p>',
                f'<p>Parent concept: {esc(node.get("parentConcept") or "Root")}</p>',
                f'<p>Declared children: {esc(", ".join(node.get("childConcepts", []))) or "None recorded"}</p>',
                '<p>sourcesCount is source metadata, not a count of imported publications. '
                'Linked URLs are citations extracted from local content; their availability and '
                'bibliographic metadata were not independently verified.</p>']
    if node.get('summary'):
        sections.append(f'<p>{esc(node["summary"])}</p>')
    links = [(Path(p).as_uri(), p) for p in node.get('contentFiles', [])]
    if node.get('declaredPackURL'):
        links.append((node['declaredPackURL'], 'Declared published concept pack'))
    sections.append('<h2>Content and concept packs</h2><ul>' + ''.join(
        f'<li><a href="{esc(url, quote=True)}">{esc(label)}</a></li>' for url, label in links) + '</ul>')
    sections.append('<h2>Cited source URLs</h2><ul>' + ''.join(
        f'<li><a href="{esc(url, quote=True)}">{esc(url)}</a></li>' for url in node.get('citedURLs', [])) + '</ul>')
    sections.append('<h2>Exact tree provenance</h2>')
    for provenance in node['provenance']:
        sections.append(f'<p>{esc(provenance["source"])}</p><pre>' +
                        esc(json.dumps(provenance['record'], indent=2, ensure_ascii=False)) + '</pre>')
    return '\n'.join(sections)


def rdf_document(nodes):
    def tag(prefix, name):
        return '{' + NS[prefix] + '}' + name
    root = ET.Element(tag('rdf', 'RDF'), {'{http://www.w3.org/XML/1998/namespace}base': 'https://llms-explorer.com/concept-tree/zotero/'})
    collections = {}
    for slug, name in [('ROOT', COLLECTION)] + [(s, n['concept']) for s, n in sorted(nodes.items())]:
        collection = ET.SubElement(root, tag('z', 'Collection'), {tag('rdf', 'about'): '#collection_' + slug})
        ET.SubElement(collection, tag('dc', 'title')).text = name
        collections[slug] = collection
    for slug, node in sorted(nodes.items()):
        ET.SubElement(collections[node['parentSlug'] or 'ROOT'], tag('dcterms', 'hasPart'),
                      {tag('rdf', 'resource'): '#collection_' + slug})
        ET.SubElement(collections[slug], tag('dcterms', 'hasPart'), {tag('rdf', 'resource'): '#note_' + slug})
        item = ET.SubElement(root, tag('bib', 'Memo'), {tag('rdf', 'about'): '#note_' + slug})
        ET.SubElement(item, tag('rdf', 'value')).text = note_html(slug, node)
        ET.SubElement(item, tag('dc', 'subject')).text = TAG
        ET.SubElement(item, tag('dc', 'subject')).text = 'concept-slug:' + slug
        ET.SubElement(item, tag('dc', 'subject')).text = 'concept-digest:' + digest(node)
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


class Client:
    base = 'http://127.0.0.1:23119'

    def request(self, path, data=None, content_type='application/json'):
        headers = {'Zotero-API-Version': '3', 'X-Zotero-Connector-API-Version': '3'}
        if data is not None:
            headers['Content-Type'] = content_type
            if not isinstance(data, bytes):
                data = json.dumps(data).encode()
        req = urllib.request.Request(self.base + path, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=600) as response:
            body = response.read()
            return json.loads(body) if body else None

    def listing(self, resource):
        result = []
        for start in range(0, 1_000_000, 100):
            batch = self.request(f'/api/users/0/{resource}?limit=100&start={start}')
            result.extend(batch)
            if len(batch) < 100:
                return result
        raise RuntimeError('Pagination exceeded safety limit')


def verify(nodes, collections, items):
    """Verify unique keys, hierarchy, note types, membership, and source digests."""
    roots = [c for c in collections if c['data']['name'] == COLLECTION and not c['data'].get('parentCollection')]
    tagged = {}
    for item in items:
        tags = {t['tag'] for t in item['data'].get('tags', [])}
        if TAG not in tags:
            continue
        for value in tags:
            if value.startswith('concept-slug:'):
                slug = value.removeprefix('concept-slug:')
                if slug in tagged:
                    raise ValueError(f'Duplicate imported concept: {slug}')
                tagged[slug] = (item, tags)
    if not roots and not tagged:
        return {'status': 'absent', 'mapping': {}, 'missing': sorted(nodes)}
    if len(roots) != 1:
        raise ValueError(f'Expected one root collection, found {len(roots)}')
    root_key = roots[0]['key']
    mapping, missing, pending = {}, [], dict(nodes)
    while pending:
        ready = [(s, n) for s, n in pending.items() if not n['parentSlug'] or n['parentSlug'] in mapping]
        if not ready:
            raise ValueError('Incomplete collection hierarchy; refusing duplicate import')
        for slug, node in ready:
            parent = mapping[node['parentSlug']]['collection_key'] if node['parentSlug'] else root_key
            matches = [c for c in collections if c['data']['name'] == node['concept'] and c['data'].get('parentCollection') == parent]
            if len(matches) != 1:
                raise ValueError(f'Expected one collection for {slug}, found {len(matches)}; refusing duplicate import')
            entry = {'collection_key': matches[0]['key'], 'item_key': None}
            if slug not in tagged:
                missing.append(slug)
            else:
                item, tags = tagged[slug]
                data = item['data']
                if data['itemType'] != 'note' or entry['collection_key'] not in data.get('collections', []):
                    raise ValueError(f'Wrong note type or collection membership: {slug}')
                if 'concept-digest:' + digest(node) not in tags:
                    raise ValueError(f'Source content changed for {slug}; refusing silent duplicate or overwrite')
                if f'Stable concept identifier: {html.escape(slug)}' not in data.get('note', ''):
                    raise ValueError(f'Note content missing identifier: {slug}')
                entry['item_key'] = item['key']
            mapping[slug] = entry
            del pending[slug]
    return {'status': 'complete' if not missing else 'partial', 'root_key': root_key,
            'mapping': mapping, 'missing': missing, 'concept_count': len(nodes),
            'collection_count': len(mapping) + 1, 'item_count': len(nodes) - len(missing)}


def write_json(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    temp.replace(path)


def run(args):
    args.state.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (args.state / 'import.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        sources = [(p.resolve(), json.loads(p.read_text())) for p in args.tree]
        nodes, conflicts = merge_trees(sources)
        enrich(nodes, args.repo, args.hub, args.skills)
        manifest = {'version': VERSION, 'source_counts': {str(p): len(r) for p, r in sources},
                    'concept_count': len(nodes), 'conflicts': conflicts, 'nodes': nodes}
        write_json(args.state / 'manifest.json', manifest)
        (args.state / 'concept-tree.rdf').write_bytes(rdf_document(nodes))
        if not args.execute and not args.verify_only:
            print(json.dumps({'status': 'prepared', 'concept_count': len(nodes), 'state': str(args.state)}))
            return
        client = Client()
        before_collections, before_items = client.listing('collections'), client.listing('items')
        result = verify(nodes, before_collections, before_items)
        if result['status'] == 'complete':
            write_json(args.state / 'verification.json', result)
            print(json.dumps({'status': 'already-complete', 'concept_count': len(nodes), 'root_key': result['root_key']}))
            return
        if args.verify_only:
            write_json(args.state / 'verification.json', result)
            print(json.dumps({k: v for k, v in result.items() if k not in ('mapping', 'missing')}))
            if result['status'] != 'complete':
                raise RuntimeError('Import not complete')
            return
        target = client.request('/connector/getSelectedCollection', {})
        if target.get('libraryID') != 1 or target.get('id') is not None:
            raise RuntimeError('Select personal My Library root in Zotero before importing')
        if result['status'] != 'absent':
            write_json(args.state / 'verification.json', result)
            raise RuntimeError('Partial import detected; checkpoint preserved. Refusing to create duplicate notes.')
        session = str(uuid.uuid4())
        write_json(args.state / 'checkpoint.json', {'status': 'importing', 'session': session,
                   'source_digest': digest(manifest), 'before_item_keys': [i['key'] for i in before_items],
                   'before_collection_keys': [c['key'] for c in before_collections]})
        try:
            response = client.request('/connector/import?session=' + session,
                                      (args.state / 'concept-tree.rdf').read_bytes(), 'application/rdf+xml')
        except Exception as exc:
            checkpoint = json.loads((args.state / 'checkpoint.json').read_text())
            checkpoint.update(status='connector-error', error=str(exc),
                              next_step='Run --verify-only before retrying or native File > Import')
            write_json(args.state / 'checkpoint.json', checkpoint)
            raise
        write_json(args.state / 'connector-response.json', response)
        after_collections, after_items = client.listing('collections'), client.listing('items')
        result = verify(nodes, after_collections, after_items)
        if not {i['key'] for i in before_items} <= {i['key'] for i in after_items}:
            raise RuntimeError('Pre-existing item keys missing from readback')
        result['preexisting_items_preserved'] = len(before_items)
        result['source_urls'] = len({u for n in nodes.values() for u in n['citedURLs']})
        result['concepts_with_content_links'] = sum(bool(n['contentFiles'] or n['declaredPackURL']) for n in nodes.values())
        write_json(args.state / 'verification.json', result)
        write_json(args.state / 'checkpoint.json', {'status': result['status'], 'session': session,
                   'root_key': result.get('root_key'), 'source_digest': digest(manifest)})
        if result['status'] != 'complete':
            raise RuntimeError('Import did not verify completely; inspect verification.json')
        print(json.dumps({k: v for k, v in result.items() if k not in ('mapping', 'missing')}))


def main():
    repo = Path(__file__).resolve().parents[1]
    hub = Path.home() / '.global-ai-hub'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tree', type=Path, action='append')
    parser.add_argument('--repo', type=Path, default=repo)
    parser.add_argument('--hub', type=Path, default=hub)
    parser.add_argument('--skills', type=Path, default=Path.home() / '.agents/skills')
    parser.add_argument('--state', type=Path, default=Path.home() / '.codex/evals/zotero/concept-tree')
    parser.add_argument('--verify-only', action='store_true', help='Read back an existing import without library writes')
    parser.add_argument('--execute', action='store_true', help='Import into Zotero; otherwise prepare local artifacts only')
    args = parser.parse_args()
    args.tree = args.tree or [hub / 'concept-tree/tree.json', repo / 'concept-tree/tree.json']
    run(args)


if __name__ == '__main__':
    main()
